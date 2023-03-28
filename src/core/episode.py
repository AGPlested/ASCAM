import numpy as np
from numpy.typing import NDArray


from ..utils import piezo_selection
from ..constants import AMPERE_UNIT_FACTORS, VOLTAGE_UNIT_FACTORS, TIME_UNIT_FACTORS
from .filtering import gaussian_filter, ChungKennedyFilter
from .analysis import baseline_correction, detect_first_activation
from .idealization import Idealizer


class Episode:
    def __init__(
        self,
        time: NDArray[np.floating],
        trace: NDArray[np.floating],
        n_episode: int=0,
        piezo: NDArray[np.floating]=None,
        command: NDArray[np.floating]=None,
        sampling_rate: float=None,
        input_time_unit: str="s",
        input_trace_unit: str="A",
        input_piezo_unit: str="V",
        input_command_unit: str="V",
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
        self.trace = trace / AMPERE_UNIT_FACTORS[input_trace_unit]
        self._id_time = time / TIME_UNIT_FACTORS[input_time_unit]

        if piezo is not None:
            self.piezo = piezo / VOLTAGE_UNIT_FACTORS[input_piezo_unit]
        else:
            self.piezo = None
        if command is not None:
            self.command = command / VOLTAGE_UNIT_FACTORS[input_command_unit]
        else:
            self.command = None
        if sampling_rate is not None:
            self.sampling_rate = sampling_rate

        # results of analyses
        self.first_activation = None
        self.manual_first_activation = False
        self.idealization = None
        self.id_time = None
        # metadata about the episode
        self.n_episode = int(n_episode)

    @property
    def first_activation_amplitude(self):
        if self.first_activation is None:
            return None
        # return the trace value at the time point closest to the mark,
        # because manual marking can choose points that are not in the time array
        return self.trace[np.argmin(np.abs(self.time - self.first_activation))]

    def idealize(self, method, params):
        self.idealization, self.id_time = Idealizer.idealize_episode(
                self.trace, self.time, method=method, params=params)

    def gauss_filter_episode(self, filter_frequency=1e3, sampling_rate=4e4):
        """Replace the current trace of the episode by the gauss filtered
        version of itself."""

        self.trace = gaussian_filter(
            signal=self.trace,
            filter_frequency=filter_frequency,
            sampling_rate=sampling_rate,
        )

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

    def baseline_correct_episode(
        self,
        intervals=None,
        method="Polynomial",
        degree=1,
        selection="piezo",
        active=False,
        deviation=0.05,
        sampling_rate=4e4,
    ):
        """Apply a baseline correction to the episode."""

        self.trace = baseline_correction(
            time=self.time,
            signal=self.trace,
            sampling_rate=sampling_rate,
            intervals=intervals,
            degree=degree,
            method=method,
            piezo=self.piezo,
            selection=selection,
            active=active,
            deviation=deviation,
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

    def filter_by_piezo(self, deviation=0.05, active=True):
        """Get the active piezo voltage of the episode."""

        if self.piezo is None:
            raise ValueError("No piezo data available")
        return piezo_selection(self.time, self.piezo,
                               self.trace, active=active,
                               deviation=deviation
                               )

    def get_command_stats(self):
        """Get the mean and standard deviation of the command voltage of the
        episode."""

        if self.command is not None:
            mean = np.mean(self.command)
            std = np.std(self.command)
        else:
            mean = std = np.nan
        return mean, std

    def detect_first_activation(self, threshold):
        """Detect the first activation in the episode."""

        self.first_activation = detect_first_activation(
            self.time, self.trace, threshold
        )
