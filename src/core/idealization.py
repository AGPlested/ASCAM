import warnings
import copy
import logging
import numpy as np

from .analysis import interpolate
from ..constants import CURRENT_UNIT_FACTORS, TIME_UNIT_FACTORS
from ..utils import round_off_tables


debug_logger = logging.getLogger("ascam.debug")
ana_logger = logging.getLogger("ascam.analysis")


class Idealizer:
    """Container object for the different idealization functions."""

    @classmethod
    def idealize_episode(
        cls,
        signal,
        time,
        amplitudes,
        thresholds = None,
        resolution = None,
        interpolation_factor = 1,
    ):
        """Get idealization for single episode."""

        if thresholds is None or thresholds.size != amplitudes.size - 1:
            thresholds = (amplitudes[1:] + amplitudes[:-1]) / 2

        if interpolation_factor != 1:
            signal, time = interpolate(signal, time, interpolation_factor)

        idealization = cls.threshold_crossing(signal, amplitudes, thresholds)

        if resolution is not None:
            idealization = cls.apply_resolution(idealization, time, resolution)
        return idealization, time

    @staticmethod
    def threshold_crossing(
        signal,
        amplitudes,
        thresholds = None,
    ):
        """Perform a threshold-crossing idealization on the signal.

        Arguments:
            signal - data to be idealized
            amplitudes - amplitudes to which signal will be idealized
            thresholds - the thresholds above/below which signal is mapped
                to an amplitude"""

        amplitudes = copy.copy(
            np.sort(amplitudes)
        )  # sort amplitudes in descending order
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
        idealization, time, resolution
    ):
        """Remove from the idealization any events that are too short.

        Args:
            idealization - an idealized current trace
            time - the corresponding time array
            resolution - the minimum duration for an event"""
        ana_logger.debug(f"Apply resolution={resolution}.")

        events = Idealizer.extract_events(idealization, time)

        i = 0
        end_ind = len(events[:, 1])
        while i < end_ind:
            if events[i, 1] < resolution:
                i_start = int(np.where(time == events[i, 2])[0])
                i_end = int(np.where(time == events[i, 3])[0]) + 1
                # add the first but not the last event to the next,
                # otherwise, flip a coin
                if (np.random.binomial(1, 0.5) or i == 0) and i != end_ind - 1:
                    i_end = int(np.where(time == events[i + 1, 3])[0]) + 1
                    idealization[i_start:i_end] = events[i + 1, 0]
                    # set amplitude
                    events[i, 0] = events[i + 1, 0]
                    # add duration
                    events[i, 1] += events[i + 1, 1]
                    # set end_time
                    events[i, 3] = events[i + 1, 3]
                    # delete next event
                    events = np.delete(events, i + 1, axis=0)
                else:  # add to the previous event
                    i_start = int(np.where(time == events[i - 1, 2])[0])
                    idealization[i_start:i_end] = events[i - 1, 0]
                    # add duration
                    events[i - 1, 1] += events[i, 1]
                    # set end_time
                    events[i - 1, 3] = events[i, 3]
                    # delete current event
                    events = np.delete(events, i, axis=0)
                # now one less event to iterate over
                end_ind -= 1
            else:
                i += 1
        if np.any(Idealizer.extract_events(idealization, time)[:, 1] < resolution):
            ana_logger.warning(
                "Filter events below the resolution failed! Some events are still too short."
            )
        return idealization

    @staticmethod
    def extract_events(
        idealization, time
    ):
        """Summarize an idealized trace as a list of events.

        Args:
            idealization [1D numpy array] - an idealized current trace
            time [1D numpy array] - the corresponding time array
        Return:
            event_list [4D numpy array] - an array containing the amplitude of
                the event, its duration, the time it starts and the time it
                end in its columns"""

        events = np.where(idealization[1:] != idealization[:-1])[0]
        # events = events.astype(int)
        # events+1 marks the indices of the last time point of an event
        # starting from 0 to events[0] is the first event, from events[0]+1
        # to events[1] is the second...  and from events[-1]+1 to
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

            event_list[1:, 0] = idealization[events + 1]
            event_list[1:, 2] = time[events + 1]
            event_list[1:-1, 3] = time[events[1:]]

            event_list[-1][0] = idealization[int(events[-1]) + 1]
            event_list[-1][2] = time[(int(events[-1])) + 1]
            event_list[-1][3] = time[-1]
        # get the duration column
        # because the start and end times of events are inclusive bounds
        # ie [a,b] the length is b-a+1, so we need to add to each event the
        # sampling interval
        sampling_interval = time[1] - time[0]
        event_list[:, 1] = event_list[:, 3] - event_list[:, 2] + sampling_interval
        return event_list


class IdealizationCache:
    def __init__(
        self,
        data,
        amplitudes,
        thresholds=None,
        resolution=None,
        interpolation_factor=None,
    ):
        self.data = data

        self.amplitudes = amplitudes
        self.thresholds = thresholds
        self.resolution = resolution
        self.interpolation_factor = interpolation_factor

    @property
    def ind_idealized(self):
        """Return the set of numbers of the episodes in the currently selected series
        that have been idealized with the current parameters."""
        return {
            episode.n_episode
            for episode in self.data.series
            if episode.idealization is not None
        }

    def idealization(self, n_episode=None):
        """Return the idealization of a given episode or idealize the episode and then return it."""
        if n_episode is None:
            n_episode = self.data.current_ep_ind
        out = [
            episode.idealization
            for episode in self.data.series
            if episode.n_episode == n_episode
        ]
        if out:  # if an idealization exists return it
            return out[0]
        else:  # else idealize the episode and then return
            self.idealize_episode(n_episode)
            self.idealization(n_episode)

    def time(self, n_episode=None):
        """Return the time vector corresponding to the idealization of the given episode,
        if it is not idealized, idealize it first and then return the time."""
        if n_episode is None:
            n_episode = self.data.current_ep_ind
        out = [
            episode.id_time
            for episode in self.data.series
            if episode.n_episode == n_episode
        ]
        if out:
            return out[0]
        else:
            self.idealize_episode(n_episode)
            self.time(n_episode)

    @property
    def all_ep_inds(self):
        return {e.n_episode for e in self.data.series}

    def clear_idealization(self):
        for series in self.data.values():
            for episode in [
                episode for episode in series if episode.idealization is not None
            ]:
                episode.idealization = None
                episode.id_time = None

    def idealize_episode(self, n_episode=None):
        if n_episode is None:
            n_episode = self.data.current_ep_ind
        if n_episode not in self.ind_idealized:
            debug_logger.debug(
                f"idealizing episode {n_episode} of "
                f"series {self.data.current_datakey}"
            )
            self.data.episode(n_episode).idealize(
                self.amplitudes,
                self.thresholds,
                self.resolution,
                self.interpolation_factor,
            )

        else:
            debug_logger.debug(f"episode number {n_episode} already idealized")

    def idealize_series(self):
        debug_logger.debug(f"idealizing series {self.data.current_datakey}")
        to_idealize = self.all_ep_inds - self.ind_idealized
        for i in to_idealize:
            self.idealize_episode(i)

    def get_events(self, time_unit="s", trace_unit="A"):
        if self.all_ep_inds != self.ind_idealized:
            self.idealize_series()
        event_array = np.zeros((0, 5)).astype(object)
        for episode in self.data.series:
            # create a column containing the episode number
            ep_events = Idealizer.extract_events(
                self.idealization(episode.n_episode), self.time()
            )
            episode_number = episode.n_episode * np.ones(len(ep_events[:, 0]))
            # glue that column to the event
            ep_events = np.concatenate(
                (episode_number[:, np.newaxis], ep_events), axis=1
            )
            event_array = np.concatenate((event_array, ep_events), axis=0)
        event_array[:, 1] *= CURRENT_UNIT_FACTORS[trace_unit]
        event_array[:, 2:] *= TIME_UNIT_FACTORS[time_unit]
        return event_array

    def dwell_time_hist(
        self, amp, n_bins=None, time_unit="ms", log_times=True, root_counts=True
    ):
        events = self.get_events(time_unit)
        debug_logger.debug(f"getting events for amplitude {amp}")
        # np.isclose works best on order of unity (with default tolerances
        # rather than figure out tolerances for e-12 multiply the
        # amp values by the expected units pA
        factor = CURRENT_UNIT_FACTORS["pA"]
        mask = np.isclose(
            np.asarray(events[:, 1], dtype=float) * factor, amp * factor
        )
        debug_logger.debug(f"multiplied amps by pA, amp={amp*factor}")
        data = events[:, 2][mask]
        if log_times:
            data = np.log10(data.astype(float))
        debug_logger.debug(f"there are {len(data)} events")
        if n_bins is None:
            n_bins = int(self.get_n_bins(data))
        heights, bins = np.histogram(data, n_bins)
        heights = np.asarray(heights, dtype=float)
        if root_counts:
            heights = np.sqrt(heights)
        return heights, bins

    @staticmethod
    def get_n_bins(data):
        n = len(data)
        std = np.std(data)
        return round(3.49 * std * n ** (1 / 3))

    def export_events(self, filepath, time_unit="us", trace_unit="pA"):
        """Export a table of events in the current (idealized) series and
        duration to a csv file."""
        debug_logger.debug(f"export_events")

        import pandas as pd

        if not filepath.endswith(".csv"):
            filepath += ".csv"
        header = [
            "Episode Number",
            f"Amplitude [{trace_unit}]",
            f"Duration [{time_unit}]",
            f"t_start [{time_unit}]",
            f"t_stop [{time_unit}]",
        ]
        params = (
            f"amplitudes = {self.amplitudes} [A];"
            + f"thresholds = {self.thresholds} [A];"
            + f"resolution = {self.resolution} [s];"
            + f"interpolation_factor = {self.interpolation_factor}\n"
        )
        export_array = self.get_events(time_unit, trace_unit)
        export_array = pd.DataFrame(export_array, columns=header)
        # truncate floats for duration and timestamps to 1 micro second
        export_array = round_off_tables(
            export_array, ["int", trace_unit, time_unit, time_unit, time_unit]
        )
        with open(filepath, "w") as f:
            f.write(params)
        export_array.to_csv(filepath, mode="a")
