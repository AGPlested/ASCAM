import logging
from typing import Optional, List, Tuple
from nptyping import Array
import numpy as np

from ascam.utils import piezo_selection
from ascam.constants import (
    CURRENT_UNIT_FACTORS,
    VOLTAGE_UNIT_FACTORS,
    TIME_UNIT_FACTORS,
)
from .filtering import gaussian_filter, ChungKennedyFilter
from .analysis import (
    baseline_correction,
    detect_first_activation,
    Idealizer,
    interpolate,
)


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

        # units when given input
        self.time = time / TIME_UNIT_FACTORS[input_time_unit]
        self.trace = trace / CURRENT_UNIT_FACTORS[input_trace_unit]
        self.id_time = time / TIME_UNIT_FACTORS[input_time_unit]

        if piezo is not None:
            self.piezo = piezo / VOLTAGE_UNIT_FACTORS[input_piezo_unit]
        else:
            self.piezo = None
        if command is not None:
            self.command = command / VOLTAGE_UNIT_FACTORS[input_command_unit]
        else:
            self.command = None

        # results of analyses
        self.first_activation = None
        self.idealization = None
        self._intrp_trace = None
        # metadata about the episode
        self.n_episode = int(n_episode)
        self.sampling_rate = sampling_rate
        self.suspiciousSTD = False

    def gauss_filter_episode(self, filter_frequency=1e3):
        """Replace the current trace of the episode by the gauss filtered
        version of itself."""

        self.trace = gaussian_filter(
            signal=self.trace,
            filter_frequency=filter_frequency,
            sampling_rate=self.sampling_rate,
        )
        # sett idealization to None since the newly created episode has no
        # idealization
        self.idealization = None

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
        self.trace = ck_filter.apply_filter(self.trace)
        # sett idealization to None since the newly created episode has no
        # idealization
        self.idealization = None

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

        self.trace = baseline_correction(
            time=self.time,
            signal=self.trace,
            fs=self.sampling_rate,
            intervals=intervals,
            degree=degree,
            method=method,
            piezo=self.piezo,
            selection=selection,
            active=active,
            deviation=deviation,
        )
        # reset idealization
        self.idealization = None

    def idealize_or_interpolate(
        self,
        amplitudes: Array[float, 1, ...] = np.array([]),
        thresholds: Optional[Array[float, 1, ...]] = None,
        resolution: Optional[int] = None,
        interpolation_factor: int = 1,
    ):
        if amplitudes.size != 0:
            self.idealize(amplitudes, thresholds, resolution, interpolation_factor)
        elif interpolation_factor != 1:
            self.interpolate(interpolation_factor)

    def interpolate(self, interpolation_factor):
        self._intrp_trace, self.id_time = interpolate(
            self.trace, self.time, interpolation_factor
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
        self.idealization, self._intrp_trace, self.id_time = Idealizer.idealize_episode(
            self.trace,
            self.time,
            amplitudes,
            thresholds,
            resolution,
            interpolation_factor,
        )

    def check_standarddeviation_all(self, stdthreshold=5e-13):
        """Check the standard deviation of the episode against a reference
        value."""

        _, trace = piezo_selection(
            self.time, self.piezo, self.trace, active=False, deviation=0.01
        )
        tracestd = np.std(trace)
        if tracestd > stdthreshold:
            self.suspiciousSTD = True

    def get_command_stats(self):
        """Get the mean and standard deviation of the command voltage of the
        episode."""

        if self.command is not None:
            mean = np.mean(self.command)
            std = np.std(self.command)
        else:
            mean = std = np.nan
        return mean, std

    def detectfirst_activation(self, threshold):
        """Detect the first activation in the episode."""

        self.first_activation = detect_first_activation(self.time, self.trace, threshold)

    def get_events(self):
        """Get the events (i.e. states) from the idealized trace.

        Assumes time and trace to be of equal length and time to start not at 0
        Returns:
            a table containing the amplitude of an opening, its start and end
            time and its duration"""

        return Idealizer.extract_events(self.idealization, self.id_time)
