import copy
import logging

import numpy as np

from episode import Episode
from tools import piezo_selection, interval_selection


class Series(list):
    def __init__(self, data=[], idealized=False):
        """`Series` are lists of episodes which also store relevant parameters
        about the recording and operations that have been performed on the
        data."""

        list.__init__(self,data)

    @property
    def has_piezo(self):
        try: val = True if self[0]._piezo is not None else False
        except IndexError: val = False
        logging.debug(f"has_piezo returns {val}")
        return val

    @property
    def has_command(self):
        try: val = True if self[0]._command is not None else False
        except IndexError: val = False
        logging.debug(f"has_command returns {val}")
        return val

    @property
    def max_command(self):
        return np.max([np.max(episode.command) for episode in self])

    @property
    def min_command(self):
        return np.min([np.min(episode.command) for episode in self])

    @property
    def max_current(self):
        return np.max([np.max(episode.trace) for episode in self])

    @property
    def min_current(self):
        return np.min([np.min(episode.trace) for episode in self])

    @property
    def max_piezo(self):
        return np.max([np.max(episode.piezo) for episode in self])

    @property
    def min_piezo(self):
        return np.min([np.min(episode.piezo) for episode in self])

    def gaussian_filter(self, filter_frequency=1e3):
        """Return a Series object in which all episodes are the filtered version
        of episodes in `self`."""

        output = copy.deepcopy(self)
        for episode in output:
            episode.gauss_filter_episode(filter_frequency)
        return output

    def CK_filter(self, window_lengths, weight_exponent, weight_window,
				  apriori_f_weights=False, apriori_b_weights=False):
        """Apply the Chung-Kennedy filter to the series."""

        output = copy.deepcopy(self)
        for episode in output:
            episode.CK_filter_episode(window_lengths, weight_exponent,
                            weight_window, apriori_f_weights, apriori_b_weights)
        return output

    def baseline_correct_all(self, intervals=[], method='poly', degree=1,
                             select_intvl=False, select_piezo=False,
                             active=False, deviation=0.05):
        """Return a `Series` object in which the episodes stored in `self` are
        baseline corrected with the given parameters."""

        output = copy.deepcopy(self)
        for episode in output:
            episode.baseline_correct_episode(degree=degree, intervals=intervals,
                                             method=method, deviation=deviation,
                                             select_intvl=select_intvl,
                                             select_piezo=select_piezo,
                                             active=active)
        return output

    def idealize_all(self, amplitudes, thresholds):
        """Return `Series` object containing the idealization of the episodes
        in `self`."""

        logging.debug(f"idealize_all")

        for episode in self:
            episode.idealize(amplitudes, thresholds)

    def check_standarddeviation_all(self, stdthreshold=5e-13):
        """Check the standard deviation of the each episode in `self` against the
        given threshold value."""

        for episode in self:
            episode.check_standarddeviation(stdthreshold)
