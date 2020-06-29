import logging
import numpy as np

from .analysis import Idealizer
from ..constants import CURRENT_UNIT_FACTORS, TIME_UNIT_FACTORS
from ..utils import round_off_tables


debug_logger = logging.getLogger("ascam.debug")
ana_logger = logging.getLogger("ascam.analysis")


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
        return {episode.n_episode for episode in self.data.series if episode.idealization is not None}

    def idealization(self, n_episode=None):
        """Return the idealization of a given episode or idealize the episode and then return it."""
        if n_episode is None:
            n_episode = self.data.current_ep_ind
        out = [episode.idealization for episode in self.data.series if episode.n_episode == n_episode]
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
        out = [episode.id_time for episode in self.data.series if episode.n_episode == n_episode]
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
            for episode in [episode for episode in series if episode.idealization is not None]:
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
            self.data.series[n_episode].idealize(
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
            np.asarray(events[:, 1], dtype=np.float) * factor, amp * factor
        )
        debug_logger.debug(f"multiplied amps by pA, amp={amp*factor}")
        data = events[:, 2][mask]
        if log_times:
            data = np.log10(data.astype(float))
        debug_logger.debug(f"there are {len(data)} events")
        if n_bins is None:
            n_bins = int(self.get_n_bins(data))
        heights, bins = np.histogram(data, n_bins)
        heights = np.asarray(heights, dtype=np.float)
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
        export_array = round_off_tables(export_array, 
                ['int', trace_unit, time_unit, time_unit, time_unit])
        with open(filepath, "w") as f:
            f.write(params)
        export_array.to_csv(filepath, mode="a")

