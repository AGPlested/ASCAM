import warnings
import copy
import logging

import numpy as np
from scipy.interpolate import CubicSpline as spCubicSpline
from typing import Optional, List, Tuple
from nptyping import Array

from ascam.utils.tools import interval_selection, piezo_selection


ana_logger = logging.getLogger("ascam.analysis")
debug_logger = logging.getLogger("ascam.debug")


def interpolate(
    signal: Array[float, 1, ...], time: Array[float, 1, ...], interpolation_factor: int
) -> Tuple[Array[float, 1, ...], Array[float, 1, ...]]:
    """Interpolate the signal with a cubic spline."""

    spline = spCubicSpline(time, signal)
    interpolation_time = np.arange(
        time[0], time[-1], (time[1] - time[0]) / interpolation_factor
    )
    return spline(interpolation_time), interpolation_time


class Idealizer:
    """Container object for the different idealization functions."""

    @classmethod
    def idealize_episode(
        cls,
        signal: Array[float, 1, ...],
        time: Array[float, 1, ...],
        amplitudes: Array[float, 1, ...],
        thresholds: Optional[Array[float, 1, ...]] = None,
        resolution: Optional[int] = None,
        interpolation_factor: int = 1,
    ) -> Array[float, 1, ...]:
        """Get idealization for single episode."""

        if thresholds is None or thresholds.size != amplitudes.size - 1:
            thresholds = (amplitudes[1:] + amplitudes[:-1]) / 2

        if interpolation_factor != 1:
            signal, time = interpolate(signal, time, interpolation_factor)

        idealization = cls.threshold_crossing(signal, amplitudes, thresholds)

        if resolution is not None:
            events = cls.extract_events(idealization, time)
            idealization = cls.apply_resolution(events, idealization, time, resolution)
        return idealization, signal, time

    @staticmethod
    def threshold_crossing(
        signal: Array[float, 1, ...],
        amplitudes: Array[float, 1, ...],
        thresholds: Optional[Array[float, 1, ...]] = None,
    ) -> Array[float, 1, ...]:
        """Perform a threshold-crossing idealization on the signal.

        Arguments:
            signal - data to be idealized
            amplitudes - amplitudes to which signal will be idealized
            thresholds - the thresholds above/below which signal is mapped
                to an amplitude"""

        amplitudes = copy.copy(np.sort(amplitudes))  # sort amplitudes in descending order
        amplitudes = amplitudes[::-1]

        # if thresholds are not or incorrectly supplied take midpoint between
        # amplitudes as thresholds
        if thresholds is not None and (thresholds.size != amplitudes.size - 1):
            warnings.warn(
                f"Too many or too few thresholds given, there should be "
                f"{amplitudes.size - 1} but there are {thresholds.size}.\n"
                f"Thresholds = {thresholds}."
            )

            thresholds = (amplitudes[1:] + amplitudes[:-1]) / 2

        # for convenience we include the trivial case of only 1 amplitude
        if amplitudes.size == 1:
            idealization = np.ones(signal.size) * amplitudes
        else:
            idealization = np.zeros(len(signal))
            # np.where returns a tuple containing array so we have to get the
            # first element to get the indices
            inds = np.where(signal > thresholds[0])[0]
            idealization[inds] = amplitudes[0]
            for thresh, amp in zip(thresholds, amplitudes[1:]):
                inds = np.where(signal < thresh)[0]
                idealization[inds] = amp

        return idealization

    @staticmethod
    def apply_resolution(
        events: Array[float, ..., 4],
        idealization: Array[float, 1, ...],
        time: Array[float, 1, ...],
        resolution: int,
    ) -> Array[float, 1, ...]:
        """Remove from the idealization any events that are too short.

        Args:
            idealization - an idealized current trace
            time - the corresponding time array
            resolution - the minimum duration for an event"""
        logging.debug(f"Apply resolution={resolution}.")

        while np.any(events[:, 1] < resolution):
            i = 0
            end_ind = len(events[:, 1])
            while i < end_ind:
                if events[i, 1] < resolution:
                    i_start = int(np.where(time == events[i, 2])[0])
                    i_end = int(np.where(time == events[i, 3])[0]) + 1
                    # add the first but not the last event to the next,
                    # otherwise, flip a coin
                    if (np.random.binomial(1, 0.5) or i == 0) and i != end_ind - 1:
                        idealization[i_start:i_end] = events[i + 1, 0]
                        # set amplitude
                        events[i, 0] = events[i + 1, 0]
                        # add duration
                        events[i, 1] += events[i + 1, 1]
                        # set end_time
                        events[i, 3] = events[i + 1, 3]
                        # delete next event
                        events = np.delete(events, i + 1, axis=0)
                    elif events[i - 1, 1] >= resolution:
                        idealization[i_start:i_end] = events[i - 1, 0]
                        # add duration
                        events[i - 1, 1] += events[i, 1]
                        # set end_time
                        events[i - 1, 3] = events[i, 3]
                        # delete current event
                        events = np.delete(events, i, axis=0)
                        i -= 1
                    # now one less event to iterate over
                    end_ind -= 1
                i += 1
        return idealization

    @staticmethod
    def extract_events(
        idealization: Array[float, 1, ...], time: Array[float, 1, ...]
    ) -> Array[float, ..., 4]:
        """Summarize an idealized trace as a list of events.

        Args:
            idealization [1D numpy array] - an idealized current trace
            time [1D numpy array] - the corresponding time array
        Return:
            event_list [4D numpy array] - an array containing the amplitude of
                the event, its duration, the time it starts and the time it
                end in its columns"""

        diff = idealization[1:] - idealization[:-1]
        events = np.where(diff != 0)[0]
        # diff+1 marks the indices of the first time point of a new event
        # starting from 0 to diff[0] is the first event, and from diff[-1] to
        # t_end is the last event, hence
        n_events = events.size + 1
        # init the array that will be final output table, events in rows and
        # amplitude, duration, start and end in columns
        event_list = np.zeros((n_events, 4))
        # fill the array
        if n_events == 1:
            event_list[0][0] = idealization[0]
            event_list[0][2] = time[0]
            event_list[0][3] = time[-1]
        else:
            event_list[0][0] = idealization[0]
            event_list[0][2] = time[0]
            event_list[0][3] = time[int(events[0])]
            for i, t in enumerate(events[:-1]):
                event_list[i + 1][0] = idealization[int(t) + 1]
                event_list[i + 1][2] = time[int(events[i])]
                event_list[i + 1][3] = time[int(events[i + 1])]
            event_list[-1][0] = idealization[int(events[-1]) + 1]
            event_list[-1][2] = time[(int(events[-1]))]
            event_list[-1][3] = time[-1]
        # get the duration column
        event_list[:, 1] = event_list[:, 3] - event_list[:, 2]
        return event_list


def detect_first_activation(
    time: Array[float, 1, ...], signal: Array[float, 1, ...], threshold: float
) -> float:
    """Return the time where a signal first crosses below a threshold."""

    return time[np.argmax(signal < threshold)]


def baseline_correction(
    time: Array[float, 1, ...],
    signal: Array[float, 1, ...],
    fs: float,
    intervals: Optional[List] = None,
    degree: Optional[int] = 1,
    method: Optional[str] = "Polynomial",
    piezo: Optional[Array[float]] = None,
    selection: Optional[str] = "piezo",
    active: Optional[bool] = False,
    deviation: Optional[float] = 0.05,
) -> Array[float, 1, ...]:
    """Perform polynomial/offset baseline correction on the given signal.

    Parameters:
        time - 1D array containing times of the measurements in signal
               units of `time_unit`
        signal - time series of measurements
        intervals - interval or list of intervals from which to
                   estimate the baseline (in ms)
        fs - sampling frequency (in Hz)
        time_unit - units of the time vector, 'ms' or 's'
        method - `baseline` can subtract a fitted polynomial of
                 desired degree OR subtract the mean
        degree - if method is 'poly', the degree of the polynomial
    Returns:
        original signal less the fitted baseline"""

    if selection.lower() == "intervals":
        t, s = interval_selection(time, signal, intervals, fs)
    elif selection.lower() == "piezo":
        t, s = piezo_selection(time, piezo, signal, active, deviation)
    else:
        t = time
        s = signal

    if method.lower() == "offset":
        offset = np.mean(s)
        output = signal - offset
    elif method.lower() == "polynomial":
        coeffs = np.polyfit(t, s, degree)
        baseline = np.zeros_like(time)
        for i in range(degree + 1):
            baseline += coeffs[i] * (time ** (degree - i))
        output = signal - baseline
    return output
