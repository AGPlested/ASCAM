import logging
import numpy as np

from .analysis import Idealizer
from ascam.constants import (
    CURRENT_UNIT_FACTORS,
    TIME_UNIT_FACTORS,
)


debug_logger = logging.getLogger("ascam.debug")


class IdealizationCache:
    def __init__(self, data, amplitudes, thresholds=None, resolution=None,
                 interpolation_factor=None):
        self.data = data

        self.amplitudes = amplitudes
        self.thresholds = thresholds
        self.resolution = resolution
        self.interpolation_factor = interpolation_factor

        self.episodes = []

    @property
    def ind_idealized(self):
        return {i.n_episode for i in self.episodes}

    def idealization(self, n_episode=None):
        if n_episode is None:
            n_episode = self.data.current_ep_ind
        out = [i.idealization for i in self.episodes if i.n_episode == n_episode]
        if out:
            return out[0]
        else:
            self.idealize_episode(n_episode)
            self.idealization(n_episode)

    def time(self, n_episode=None):
        if n_episode is None:
            n_episode = self.data.current_ep_ind
        out = [i.time for i in self.episodes if i.n_episode == n_episode]
        if out:
            return out[0]
        else:
            self.idealize_episode(n_episode)
            self.time(n_episode)

    @property
    def all_ep_inds(self):
        return {e.n_episode for e in self.data.series}

    def idealize_episode(self, n_episode=None):
        if n_episode is None:
            n_episode = self.data.current_ep_ind
        if n_episode not in self.ind_idealized:
            debug_logger.debug(f'idealizing episode {n_episode} of '
                               f'series {self.data.current_datakey}')
            idealization, trace, time = Idealizer.idealize_episode(
                                    self.data.series[n_episode].trace,
                                    self.data.episode.time,
                                    self.amplitudes,
                                    self.thresholds,
                                    self.resolution,
                                    self.interpolation_factor)
            self.episodes.append(Idealization(idealization, time, n_episode))
            self.ind_idealized.add(n_episode)
        else:
            debug_logger.debug("episode already idealized")

    def idealize_series(self):
        debug_logger.debug(f'idealizing series {self.data.current_datakey}')
        to_idealize = self.all_ep_inds - self.ind_idealized
        for i in to_idealize:
            self.idealize_episode(i)

    def get_events(self, time_unit='us', current_unit='pA'):
        if self.all_ep_inds != self.ind_idealized:
            self.idealize_series()
        export_array = np.zeros((0, 5)).astype(object)
        for episode in self.data.series:
            # create a column containing the episode number
            ep_events = Idealizer.extract_events(self.idealization(), self.time())
            # ep_events = episode.get_events()
            episode_number = episode.n_episode * np.ones(len(ep_events[:, 0]))
            # glue that column to the event
            ep_events = np.concatenate(
                (episode_number[:, np.newaxis], ep_events), axis=1
            )
            export_array = np.concatenate((export_array, ep_events), axis=0)
        export_array[:, 1] *= CURRENT_UNIT_FACTORS[current_unit]
        export_array[:, 2:] *= TIME_UNIT_FACTORS[time_unit]
        return export_array

    def export_idealization(self, filepath, time_unit, trace_unit):
        debug_logger.debug(f"export_idealization")

        if not filepath.endswith(".csv"):
            filepath += ".csv"
        export_array = np.zeros(
            shape=(len(self.episodes) + 1, self.idealization().size)
        )
        export_array[0] = self.time() * TIME_UNIT_FACTORS[time_unit]
        for k, episode in enumerate(self.episodes):
            export_array[k + 1] = (
                episode.idealization * CURRENT_UNIT_FACTORS[trace_unit]
            )
        # note that we transpose the export array to export the matrix
        np.savetxt(filepath, export_array.T, delimiter=",", 
                    header=f"amplitudes = {self.amplitudes};"
                           f"thresholds = {self.thresholds};"
                           f"resolution = {self.resolution};"
                           f"interpolation_factor = {self.interpolation_factor}"
                            )


    def export_events(self, filepath, time_unit='us', current_unit='pA'):
        """Export a table of events in the current (idealized) series and
        duration to a csv file."""
        debug_logger.debug(f"export_events")

        import pandas as pd

        if not filepath.endswith(".csv"):
            filepath += ".csv"
        header = [
            "Episode Number",
            f"Amplitude [{current_unit}]",
            f"Duration [{time_unit}]",
            f"t_start [{time_unit}]",
            f"t_stop [{time_unit}]",
        ]
        params=f"amplitudes = {self.amplitudes};" \
               +f"thresholds = {self.thresholds};" \
               +f"resolution = {self.resolution};" \
               +f"interpolation_factor = {self.interpolation_factor}\n"
        export_array = self.get_events(time_unit, current_unit)
        export_array = pd.DataFrame(export_array, columns=header)
        # truncate floats for duration and timestamps to 3 decimals (standard 1 micro s)
        if time_unit == 'us':
            for i in header:
                export_array[i] = export_array[i].map(lambda x: f"{x:.0f}")
        if time_unit == 'ms':
            for i in header:
                export_array[i] = export_array[i].map(lambda x: f"{x:.3f}")
        if time_unit == 's':
            for i in header:
                export_array[i] = export_array[i].map(lambda x: f"{x:.6f}")
        with open(filepath, 'w') as f:
            f.write(params)
        export_array.to_csv(filepath,mode='a')


class Idealization:
    def __init__(self, idealization, time, n_episode):
        self.idealization = idealization
        self.time = time
        self.n_episode = n_episode
