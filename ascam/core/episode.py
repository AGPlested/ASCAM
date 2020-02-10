import logging
from typing import Optional, List, Tuple
from nptyping import Array
import numpy as np

from ascam.core.filtering import gaussian_filter, ChungKennedyFilter
from ascam.core.analysis import (
    baseline_correction,
    detect_first_activation,
    Idealizer,
    interpolate,
)
from ascam.utils.tools import piezo_selection
from ascam.constants import CURRENT_UNIT_FACTORS, VOLTAGE_UNIT_FACTORS, TIME_UNIT_FACTORS

class Episode:
    def __init__(
        self,
        time,
        trace,
        n_episode=0,
        piezo=None,
        command=None,
        sampling_rate=4e4,
        # time_unit="ms",
        # piezo_unit="V",
        # command_unit="mV",
        # trace_unit="pA",
        input_time_unit="s",
        input_trace_unit="A",
        input_piezo_unit="V",
        input_command_unit="V",
    ):
        """Episode objects hold all the information about an epoch and
        should be used to store raw and manipulated data

        Parameters:
            time [1D array of floats] - containing time (in seconds)
            trace [1D array of floats] - containing the current
                                                trace
            piezo [1D array of floats] - the voltage applied to the
                                         Piezo device
            command [1D array of floats] - voltage applied to
                                                  cell
            n_episode [int] - the number of measurements on this cell that
                          came before this one
            filterType [string] - type of filter used"""

        # units of the data
        # the units of the private attributes (eg _time) should be SI units
        # ie seconds, ampere etc
        # self.time_unit = time_unit
        # self.trace_unit = trace_unit
        # self.command_unit = command_unit
        # self.piezo_unit = piezo_unit
        # units when given input
        self._time = time / TIME_UNIT_FACTORS[input_time_unit]
        self._trace = trace / CURRENT_UNIT_FACTORS[input_trace_unit]
        self._id_time = time / TIME_UNIT_FACTORS[input_time_unit]        

        if piezo is not None:
            self._piezo = piezo / VOLTAGE_UNIT_FACTORS[input_piezo_unit]
        else:
            self._piezo = None
        if command is not None:
            self._command = command  / VOLTAGE_UNIT_FACTORS[input_command_unit]
        else:
            self._command = None

        # results of analyses
        self._first_activation = None
        self._idealization = None
        self._intrp_trace = None
        # metadata about the episode
        self.n_episode = int(n_episode)
        self.sampling_rate = sampling_rate
        self.suspiciousSTD = False


    @property
    def time_unit_factor(self):
        return self.time_unit_factors[self.time_unit]

    @property
    def trace_unit_factor(self):
        return self.trace_unit_factors[self.trace_unit]

    @property
    def command_unit_factor(self):
        return self.command_unit_factors[self.command_unit]

    @property
    def piezo_unit_factor(self):
        return self.piezo_unit_factors[self.piezo_unit]

    def gauss_filter_episode(self, filter_frequency=1e3, method="convolution"):
        """Replace the current trace of the episode by the gauss filtered
        version of itself."""

        self._trace = gaussian_filter(
            signal=self._trace,
            filter_frequency=filter_frequency,
            sampling_rate=self.sampling_rate,
        )
        # sett idealization to None since the newly created episode has no
        # idealization
        self._idealization = None

    def CK_filter_episode(
        self,
        window_lengths,
        weight_exponent,
        weight_window,
        apriori_f_weights=False,
        apriori_b_weights=False,
    ):
        """Replace the current _trace by the CK fitered version of itself."""

        ck_filter = ChungKennedyFilter(
            window_lengths,
            weight_exponent,
            weight_window,
            apriori_f_weights,
            apriori_b_weights,
        )
        self._trace = ck_filter.apply_filter(self._trace)
        # sett idealization to None since the newly created episode has no
        # idealization
        self._idealization = None

    def baseline_correct_episode(
        self,
        intervals=None,
        method="Polynomial",
        degree=1,
        selection="piezo",
        active=False,
        deviation=0.05,
    ):
        """Apply a baseline correction to the episode."""

        self._trace = baseline_correction(
            time=self._time,
            signal=self._trace,
            fs=self.sampling_rate,
            intervals=intervals,
            degree=degree,
            method=method,
            piezo=self._piezo,
            selection=selection,
            active=active,
            deviation=deviation,
        )
        # reset _idealization
        self._idealization = None

    def idealize_or_interpolate(
        self,
        amplitudes: Array[float, 1, ...]=np.array([]),
        thresholds: Optional[Array[float, 1, ...]]=None,
        resolution: Optional[int]=None,
        interpolation_factor: int=1,
    ):
        if amplitudes.size != 0:
            self.idealize(amplitudes, thresholds, resolution, interpolation_factor)
        elif interpolation_factor != 1:
            self.interpolate(interpolation_factor)

    def interpolate(self, interpolation_factor):
        self._intrp_trace, self._id_time = interpolate(
            self._trace, self._time, interpolation_factor
        )

    def idealize(self, amplitudes, thresholds, resolution, interpolation_factor):
        """Idealize the episode using threshold crossing."""

        logging.debug(
            f"Idealizing episode #{self.n_episode}\n"
            f"amplitudes = {amplitudes}\n"
            f"thresholds = { thresholds } \n"
            f"resolution = { resolution } \n"
            f"interpolation_factor = { interpolation_factor } "
        )
        self._idealization, self._intrp_trace, self._id_time = Idealizer.idealize_episode(
            self._trace,
            self._time,
            amplitudes,
            thresholds,
            resolution,
            interpolation_factor,
        )

    def check_standarddeviation_all(self, stdthreshold=5e-13):
        """Check the standard deviation of the episode against a reference
        value."""

        _, _, trace = piezo_selection(
            self._time, self._piezo, self._trace, active=False, deviation=0.01
        )
        tracestd = np.std(trace)
        if tracestd > stdthreshold:
            self.suspiciousSTD = True

    def get_command_stats(self):
        """Get the mean and standard deviation of the command voltage of the
        episode."""

        if self._command is not None:
            mean = np.mean(self._command)
            std = np.std(self._command)
        else:
            mean = std = np.nan
        return mean, std

    def detect_first_activation(self, threshold):
        """Detect the first activation in the episode."""

        self._first_activation = detect_first_activation(
            self._time, self._trace, threshold
        )

    def get_events(self):
        """Get the events (i.e. states) from the idealized trace.

        Assumes time and trace to be of equal length and time to start not at 0
        Returns:
            a table containing the amplitude of an opening, its start and end
            time and its duration"""

        return Idealizer.extract_events(self.idealization, self.id_time)
