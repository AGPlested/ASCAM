import copy
import logging
import pickle

import numpy as np
import pandas as pd

from ..constants import CURRENT_UNIT_FACTORS, VOLTAGE_UNIT_FACTORS, TIME_UNIT_FACTORS
from ..utils import (
    parse_filename,
    piezo_selection,
    interval_selection,
    round_off_tables,
)
from .readdata import load_matlab, load_axo
from .episode import Episode


ana_logger = logging.getLogger("ascam.analysis")
debug_logger = logging.getLogger("ascam.debug")


class Recording(dict):
    @classmethod
    def from_file(
        cls,
        filename="data/180426 000 Copy Export.mat",
        sampling_rate=4e4,
        time_input_unit="s",
        trace_input_unit="A",
        piezo_input_unit="V",
        command_input_unit="V",
    ):
        """Load data from a file.

        This method creates a recording objects or reconstructs one from the
        data in the file.
        Args:
            filename - name of the file
            sampling_rate - the frequency at which the recording was sampled
            time_unit - the unit of time in the input
            trace_unit - the unit of electric current in the input
            piezo_unit - the unit of voltage in the piezo data in the input
            command_unit - the units in which the command voltage is given
        Returns:
            recording - instance of the Recording class containing the data"""
        ana_logger.info(
            f"Loading data from file {filename}\n"
            f"sampling_rate = {sampling_rate}\n"
            f"time_input_unit = {time_input_unit}\n"
            f"trace_input_unit = {trace_input_unit}\n"
            f"piezo_input_unit = {piezo_input_unit}\n"
            f"command_input_unit = {command_input_unit}"
        )

        recording = cls(filename, sampling_rate)

        filetype, _, _, _ = parse_filename(filename)
        if filetype == "pkl":
            recording = cls._load_from_pickle(recording)
        elif filetype == "mat":
            recording = cls._load_from_matlab(
                recording,
                trace_input_unit=trace_input_unit,
                piezo_input_unit=piezo_input_unit,
                command_input_unit=command_input_unit,
                time_input_unit=time_input_unit,
            )
        elif "axg" in filetype:
            recording = cls._load_from_axo(
                recording,
                trace_input_unit=trace_input_unit,
                piezo_input_unit=piezo_input_unit,
                command_input_unit=command_input_unit,
                time_input_unit=time_input_unit,
            )
        else:
            raise ValueError(f"Cannot load from filetype {filetype}.")

        recording.lists = {"All": (list(range(len(recording["raw_"]))), None)}

        return recording

    def __init__(self, filename="", sampling_rate=4e4):
        super().__init__()

        # parameters for loading the data
        self.filename = filename

        # attributes of the data
        self.sampling_rate = int(float(sampling_rate))

        # attributes for storing and managing the data
        self["raw_"] = []
        self.current_datakey = "raw_"
        self.current_ep_ind = 0

        # variables for user created lists of episodes
        # `lists` stores the indices of the episodes in the list in the first
        # element and the associated key as the second
        # lists[name] = ([inds], key)
        self.lists = dict()

    def select_episodes(self, datakey=None, lists=None):
        if datakey is None:
            datakey = self.current_datakey
        if lists is None:
            lists = ["All"]
        indices = list()
        for listname in lists:
            indices.extend(self.lists[listname][0])
        indices = np.array(list(set(indices)))
        return np.array(self[datakey])[indices]

    def episodes_in_lists(self, names):
        if isinstance(str, names):
            names = [names]
        indices = list()
        for listname in names:
            indices.extend(self.lists[listname][0])
        # remove duplicate indices
        indices = np.array(list(set(indices)))
        debug_logger.debug(f"Selected episodes: {indices}")
        return np.array(self.series)[indices]

    @property
    def series(self):
        return self[self.current_datakey]

    def episode(self, n_episode=None):
        if n_episode is None:
            n_episode = self.current_ep_ind
        out = [e for e in self.series if e.n_episode == n_episode]
        if out:
            return out[0]
        else:
            debug_logger.warning(
                f"tried to get episode with index {self.current_ep_ind} but it "
                "doesn't exist"
            )

    def next_episode_ind(self):
        inds = [e.n_episode for e in self.series]
        current = np.where(np.array(inds) == self.current_ep_ind)[0]
        if current + 1 == len(inds):
            return 0
        return int(current) + 1

    @property
    def has_command(self):
        if self.series:
            return True if self.episode().command is not None else False
        return False

    @property
    def has_piezo(self):
        if self.series:
            return True if self.episode().piezo is not None else False
        return False

    def baseline_correction(
        self,
        intervals=None,
        method="Polynomial",
        degree=1,
        selection="piezo",
        active=False,
        deviation=0.05,
        time_unit="s",
    ):
        """Apply a baseline correction to the current series."""

        if self.current_datakey == "raw_":
            # if its the first operation drop the 'raw_'
            new_datakey = "BC_"
        else:
            # if operations have been done before combine the names
            new_datakey = self.current_datakey + "BC_"
        logging.info(f"new datakey is {new_datakey}")
        self[new_datakey] = copy.deepcopy(self.series)
        if selection.lower() == "piezo" and not self.has_piezo:
            debug_logger.debug(
                "selection method was set to 'piezo' but"
                "the recording has no piezo data."
            )
            selection = "None"
        ana_logger.info(
            f"baseline_correction on series '{self.current_datakey}',"
            f"using method '{method}' with degree {degree}\n"
            f"selection is {selection}\n"
            f"the selected intervals are {intervals}\n"
            f"with units {time_unit}"
            f"select where piezo is active is {active}; the "
            f"deviation from piezo baseline is {deviation}"
            f"sampling rate of this recording is {self.sampling_rate}"
        )
        if intervals is not None:
            intervals = np.array(intervals) / TIME_UNIT_FACTORS[time_unit]
        for episode in self[new_datakey]:
            episode.baseline_correct_episode(
                degree=degree,
                intervals=intervals,
                method=method,
                deviation=deviation,
                selection=selection,
                active=active,
                sampling_rate=self.sampling_rate,
            )
        self.current_datakey = new_datakey
        debug_logger.debug("keys of the recording are now {}".format(self.keys()))

    def gauss_filter_series(self, filter_freq):
        """Filter the current series using a gaussian filter"""
        ana_logger.info(
            f"gauss filtering series '{self.current_datakey}'\n"
            f"with frequency {filter_freq}"
            f"sampling_rate is {self.sampling_rate}"
        )

        fdatakey = f"GFILTER{filter_freq}_"
        if self.current_datakey == "raw_":
            # if its the first operation drop the 'raw-'
            new_datakey = fdatakey
        else:
            # if operations have been done before combine the names
            new_datakey = self.current_datakey + fdatakey
        self[new_datakey] = copy.deepcopy(self.series)
        for episode in self[new_datakey]:
            episode.gauss_filter_episode(filter_freq, self.sampling_rate)
        self.current_datakey = new_datakey

    def CK_filter_series(
        self,
        window_lengths,
        weight_exponent,
        weight_window,
        apriori_f_weights=False,
        apriori_b_weights=False,
    ):
        """Filter the current series using the Chung-Kennedy filter banks"""
        ana_logger.info(
            f"Chung-Kennedy filtering on series "
            f"'{self.current_datakey}'\n"
            f"window_lengths: {window_lengths}\n"
            f"weight_exponent: {weight_exponent}\n"
            f"weight_window: {weight_window}\n"
            f"apriori_f_weights: {apriori_f_weights}\n"
            f"apriori_b_weights: {apriori_b_weights}"
        )

        n_filters = len(window_lengths)
        fdatakey = f"CKFILTER_K{n_filters}p{weight_exponent}M{weight_window}_"
        if self.current_datakey == "raw_":
            # if its the first operation drop the 'raw-'
            new_datakey = fdatakey
        else:
            # if operations have been done before combine the names
            new_datakey = self.current_datakey + fdatakey

        self[new_datakey] = copy.deepcopy(self.series)
        for episode in self[new_datakey]:
            episode.CK_filter_episode(
                window_lengths,
                weight_exponent,
                weight_window,
                apriori_f_weights,
                apriori_b_weights,
            )
        self.current_datakey = new_datakey

    def detect_fa(self, threshold):
        """Apply first event detection to all episodes in the selected series"""

        [
            episode.detect_first_activation(threshold)
            for episode in self.series
            if not episode.manual_first_activation
        ]

    def get_first_events(self, threshold):
        # Finding all states in the data
        states_in_episodes = [
            np.unique(episode.idealization) for episode in self.series
        ]
        assert not all(states_in_episodes == np.array([None])), "No idealization found"
        states = np.unique(np.hstack(states_in_episodes))
        states.sort()
        states = states[::-1]
        first_events_list = []
        for i, episode in enumerate(self.series):
            first_events = episode.detect_first_events_episode(threshold, states)
            first_events_list.append(first_events)
        return np.hstack(first_events_list)

    def series_hist(
        self,
        active=True,
        select_piezo=True,
        deviation=0.05,
        n_bins=50,
        density=False,
        intervals=False,
    ):
        """Create a histogram of all episodes in the presently selected series
        """
        debug_logger.debug(f"series_hist")
        # put all piezo traces and all current traces in lists
        piezos = [episode.piezo for episode in self.series]
        traces = [episode.trace for episode in self.series]
        trace_list = []
        if select_piezo and not self.has_piezo:
            debug_logger.debug(
                (f"Tried piezo selection even though there is no piezo data!")
            )
            select_piezo = False
        # select the time points that are used for the histogram
        if select_piezo:
            for piezo, trace in zip(piezos, traces):
                time, trace_points = piezo_selection(
                    self.episode().time, piezo, trace, active, deviation
                )
                trace_list.extend(trace_points)
        elif intervals:
            for trace in traces:
                time, trace_points = interval_selection(
                    self.episode().time, trace, intervals, self.sampling_rate
                )
                trace_list.extend(trace_points)
        else:
            trace_list = traces
        # turn the collected traces into a 1D numpy array for the histogram
        # function
        trace_list = np.asarray(trace_list)
        trace_list = trace_list.flatten()

        heights, bins = np.histogram(trace_list, n_bins, density=density)
        # get centers of all the bins
        centers = (bins[:-1] + bins[1:]) / 2
        # get the width of a(ll) bin(s)
        width = bins[1] - bins[0]
        return heights, bins, centers, width

    def episode_hist(
        self,
        active=True,
        select_piezo=True,
        deviation=0.05,
        n_bins=50,
        density=False,
        intervals=False,
    ):
        """Create a histogram of the current in the presently selected episode.
        """
        if not self.has_piezo:
            debug_logger.debug(
                (f"Tried piezo selection even though there is no piezo data!")
            )
            select_piezo = False
        # select time points to include in histogram
        if select_piezo:
            time, trace_points = piezo_selection(
                self.episode().time,
                self.episode().piezo,
                self.episode().trace,
                active,
                deviation,
            )
        elif intervals:
            time, trace_points = interval_selection(
                self.episode().time,
                self.episode().trace,
                intervals,
                self.episode().sampling_rate,
            )
        else:
            trace_points = self.episode().trace
        heights, bins = np.histogram(trace_points, n_bins, density=density)
        # get centers of all the bins
        centers = (bins[:-1] + bins[1:]) / 2
        # get the width of a(ll) bin(s)
        width = bins[1] - bins[0]
        return heights, bins, centers, width

    # exporting and saving methods
    def save_to_pickle(self, filepath):
        """Dump the recording to a pickle."""
        debug_logger.debug(f"save_to_pickle")

        if not filepath.endswith(".pkl"):
            filepath += ".pkl"
        with open(filepath, "wb") as save_file:
            pickle.dump(self, save_file)

    @staticmethod
    def _load_from_pickle(recording):
        """Load a recording from a '.pkl' file.

        Recordings edited in ASCAM can be saved as pickles, this method
        reconstructs such saved recordings.
        Args:
            recording - recording object to be filled with data
        Returns:
            recording the instance of the recording that was stored in the
            pickle."""
        with open(recording.filename, "rb") as file:
            data = pickle.load(file)
            recording.__dict__ = data.__dict__
            for key, value in data.items():
                recording[key] = value
        return recording

    def export_idealization(
        self,
        filepath,
        lists_to_save,
        time_unit,
        trace_unit,
        amplitudes,
        thresholds,
        resolution,
        interpolation_factor,
    ):
        debug_logger.debug(f"export_idealization")

        if not filepath.endswith(".csv"):
            filepath += ".csv"

        episodes = self.select_episodes(lists=lists_to_save)

        export_array = np.zeros(
            shape=(len(episodes) + 1, episodes[0].idealization.size)
        )
        export_array[0] = self.episode().id_time * TIME_UNIT_FACTORS[time_unit]
        for k, episode in enumerate(episodes):
            export_array[k + 1] = (
                episode.idealization * CURRENT_UNIT_FACTORS[trace_unit]
            )
        # note that we transpose the export array to export the matrix
        np.savetxt(
            filepath,
            export_array.T,
            delimiter=",",
            header=f"amplitudes = {amplitudes};"
            f"thresholds = {thresholds};"
            f"resolution = {resolution};"
            f"interpolation_factor = {interpolation_factor}"
            "\n Time, "
            + ", ".join(["Episode number " + str(e.n_episode) for e in episodes]),
        )

    def export_matlab(
        self,
        filepath,
        datakey,
        lists_to_save,
        save_piezo,
        save_command,
        time_unit="s",
        trace_unit="A",
        piezo_unit="V",
        command_unit="V",
    ):
        """Export all the episodes in the givens list(s) from the given series
        (only one) to a matlab file."""
        debug_logger.debug(
            f"export_matlab:\n"
            f"saving the lists: {lists_to_save}\n"
            f"of series {datakey}\n"
            f"save piezo: {save_piezo}; "
            "save command: {save_command}\n"
            f"saving to destination: {filepath}"
        )
        from scipy import io

        if not filepath.endswith(".mat"):
            filepath += ".mat"

        # create dict to write matlab file and add the time vector
        export_dict = dict()
        export_dict["time"] = self["raw_"][0].time * TIME_UNIT_FACTORS[time_unit]
        fill_length = len(str(len(self[datakey])))
        episodes = self.select_episodes(datakey, lists_to_save)
        # # get the episodes we want to save
        # indices = list()
        # for listname in lists_to_save:
        #     indices.extend(self.lists[listname][0])
        # indices = np.array(list(set(indices)))
        # episodes = np.array(self[datakey])[indices]
        for episode in episodes:
            n = str(episode.n_episode).zfill(fill_length)
            export_dict["trace" + n] = episode.trace * CURRENT_UNIT_FACTORS[trace_unit]
            if save_piezo:
                export_dict["piezo" + n] = (
                    episode.piezo * VOLTAGE_UNIT_FACTORS[piezo_unit]
                )
            if save_command:
                export_dict["command" + n] = (
                    episode.command * VOLTAGE_UNIT_FACTORS[command_unit]
                )
        io.savemat(filepath, export_dict)

    def export_axo(self, filepath, datakey, lists_to_save, save_piezo, save_command):
        """Export data to an axograph file.

        Argument:
            filepath - location where the file is to be stored
            datakey - series that should be exported
            lists_to_save - the user-created lists of episodes that should be
                includes
            save_piezo - if true piezo data will be exported
            save_command - if true command voltage data will be exported"""
        debug_logger.debug(
            f"export_axo:\n"
            f"saving the lists: {lists_to_save}\n"
            f"of series {datakey}\n"
            f"save piezo: {save_piezo}; save command: {save_command}\n"
            f"saving to destination: {filepath}"
        )

        import axographio

        if not filepath.endswith(".axgd"):
            filepath += ".axgd"

        column_names = [f"time (s)"]

        # to write to axgd we need a list as the second argument of the 'write'
        # method, this elements in the lists will be the columns in data table
        # the first column in this will be a list of episode numbers
        data_list = [self.episode().time]

        # get the episodes we want to save
        episodes = self.select_episodes(datakey, lists_to_save)

        for episode in episodes:
            data_list.append(np.array(episode.trace))
            column_names.append(f"Ipatch (A) ep# {episode.n_episode}")
            if save_piezo:
                column_names.append(f"piezo voltage (V) ep# {episode.n_episode}")
                data_list.append(np.array(episode.piezo))
            if save_command:
                column_names.append(f"command voltage (V) ep# {episode.n_episode}")
                data_list.append(np.array(episode.command))
        file = axographio.file_contents(column_names, data_list)
        file.write(filepath)

    def create_first_activation_table(
        self, datakey=None, time_unit="ms", lists_to_save=None, trace_unit="pA"
    ):
        if datakey is None:
            datakey = self.current_datakey
        debug_logger.debug(f"export_first_activation for series {datakey}")

        export_array = np.array(
            [
                (
                    episode.n_episode,
                    episode.first_activation * TIME_UNIT_FACTORS[time_unit],
                    episode.first_activation_amplitude
                    * CURRENT_UNIT_FACTORS[trace_unit],
                )
                for episode in self.select_episodes(datakey, lists_to_save)
            ]
        )
        return export_array.astype(object)

    def create_first_event_table(
            self, datakey=None, time_unit="ms", lists_to_save=None
    ):
        if datakey is None:
            datakey = self.current_datakey
        debug_logger.debug(f"first_events for series {datakey}")

        table_rows = []
        for episode in self.select_episodes(datakey, lists_to_save):
            first_events_matrix = episode.first_events
            # Reshaping 2xnstates matrix into an array, column first
            first_events = first_events_matrix.reshape(
                first_events_matrix.size, order="F"
            ) * TIME_UNIT_FACTORS[time_unit]
            data = (episode.n_episode, ) + tuple(first_events)
            table_rows.append(data)
        return np.array(table_rows).astype(object)

    def export_first_activation(
        self,
        filepath,
        datakey=None,
        time_unit="ms",
        lists_to_save=None,
        trace_unit="pA",
    ):
        """Export csv file of first activation times."""
        export_array = self.create_first_activation_table(
            datakey, time_unit, lists_to_save, trace_unit
        )
        header = [
            "Episode Number",
            f"First Activation Time [{time_unit}]",
            f"Current [{trace_unit}]",
        ]
        export_array = pd.DataFrame(export_array, columns=header)
        # truncate floats for duration and timestamps to 1 micro second
        export_array = round_off_tables(export_array, ["int", time_unit, trace_unit])
        if not filepath.endswith(".csv"):
            filepath += ".csv"
        export_array.to_csv(filepath)

    def export_first_events(
        self,
        filepath,
        datakey=None,
        time_unit="ms",
        lists_to_save=None,
        trace_unit="pA",
    ):
        """Export csv file of first event start times and durations at each state."""
        export_array = self.create_first_event_table(
            datakey, time_unit, lists_to_save
        )
        header = ["Episode Number"]
        # per state 2 columns + episode number
        for i in range(int((export_array.shape[1]-1)/2)):
            header.append(f"S{i}-start [{time_unit}]")
            header.append(f"S{i}-duration [{time_unit}]")
        export_array_df = pd.DataFrame(export_array, columns=header)
        # truncate floats for duration and timestamps to 1 micro second
        export_df = round_off_tables(export_array_df, ["int", time_unit, trace_unit])
        if not filepath.endswith(".csv"):
            filepath += ".csv"
        export_df.to_csv(filepath)

    @staticmethod
    def _load_from_axo(
        recording,
        trace_input_unit,
        piezo_input_unit,
        command_input_unit,
        time_input_unit,
    ):
        """Load a recording from an axograph file.

        Recordings edited in ASCAM can be saved as pickles, this method
        reconstructs such saved recordings.
        Args:
            recording - recording object to be filled with data
        Returns:
            recording the instance of the recording that was stored in the
            file."""
        debug_logger.debug(f"from_axo")

        names, time, current, piezo, command, ep_numbers = load_axo(recording.filename)
        n_episodes = len(current)
        if not piezo:
            piezo = [None] * n_episodes
        if not command:
            command = [None] * n_episodes
        if not ep_numbers:
            ep_numbers = range(n_episodes)
        initial_index = ep_numbers[0]
        recording["raw_"] = [
            Episode(
                time,
                current[i],
                n_episode=int(ep_numbers[i]),
                piezo=piezo[i],
                command=command[i],
                sampling_rate=recording.sampling_rate,
                input_time_unit=time_input_unit,
                input_trace_unit=trace_input_unit,
                input_piezo_unit=piezo_input_unit,
                input_command_unit=command_input_unit,
            )
            for i in range(n_episodes)
        ]
        recording.current_ep_ind = int(initial_index)
        return recording

    @staticmethod
    def _load_from_matlab(
        recording,
        trace_input_unit,
        piezo_input_unit,
        command_input_unit,
        time_input_unit,
    ):
        """Load data from a matlab file.

        This method creates a recording objects from the data in the file.
        Args:
            recording - recording object to be filled with data
        Returns:
            recording - instance of the Recording class containing the data"""
        debug_logger.debug(f"from_matlab")

        names, time, current, piezo, command, ep_numbers = load_matlab(
            recording.filename
        )
        n_episodes = len(current)
        if not piezo:
            piezo = [None] * n_episodes
        if not command:
            command = [None] * n_episodes
        if not ep_numbers:
            ep_numbers = range(n_episodes)
        initial_index = ep_numbers[0]
        recording["raw_"] = [
            Episode(
                time,
                current[i],
                n_episode=int(ep_numbers[i]),
                piezo=piezo[i],
                command=command[i],
                sampling_rate=recording.sampling_rate,
                input_time_unit=time_input_unit,
                input_trace_unit=trace_input_unit,
                input_piezo_unit=piezo_input_unit,
                input_command_unit=command_input_unit,
            )
            for i in range(n_episodes)
        ]
        recording.current_ep_ind = int(initial_index)
        return recording
