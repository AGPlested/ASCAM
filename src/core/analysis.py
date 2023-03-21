import logging
from typing import List, Union

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import CubicSpline as spCubicSpline

from ..utils.tools import interval_selection, piezo_selection


ana_logger = logging.getLogger("ascam.analysis")
debug_logger = logging.getLogger("ascam.debug")


def interpolate(
    signal: NDArray[np.floating],
    time: NDArray[np.floating],
    interpolation_factor: float
) -> tuple[np.ndarray, NDArray[np.floating]]:
    """Interpolate the signal with a cubic spline."""

    spline = spCubicSpline(time, signal)
    interpolation_time = np.arange(
        time[0], time[-1], (time[1] - time[0]) / interpolation_factor
    )
    return spline(interpolation_time), interpolation_time


def detect_first_activation(
    time: np.ndarray,
    signal: np.ndarray,
    threshold: float
) -> float:
    """Return the time where a signal first crosses below a threshold."""
    return time[np.argmax(signal < threshold)]


def baseline_correction(
    time: np.ndarray,
    signal: np.ndarray,
    sampling_rate: float,
    intervals: Union[List, List[List]] = [],
    degree: int = 1,
    method: str = "Polynomial",
    piezo: NDArray = np.array([]),
    selection: str = "piezo",
    active: bool = False,
    deviation: float = 0.05,
) -> NDArray[np.floating]:
    """Perform polynomial/offset baseline correction on the given signal.

    Parameters:
        time - 1D array containing times of the measurements in signal
               units of `time_unit`
        signal - time series of measurements
        intervals - interval or list of intervals from which to
                   estimate the baseline (in ms)
        sampling_rate - sampling frequency (in Hz)
        time_unit - units of the time vector, 'ms' or 's'
        method - `baseline` can subtract a fitted polynomial of
                 desired degree OR subtract the mean
        degree - if method is 'poly', the degree of the polynomial
    Returns:
        original signal less the fitted baseline"""

    if selection.lower() == "intervals":
        t, s = interval_selection(time, signal, intervals, sampling_rate)
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
    else:
        raise ValueError("Baseline correction method not recognized.")
    return output
