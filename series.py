import copy

import numpy as np

from episode import Episode
from tools import piezo_selection, interval_selection


class Series(list):
    def __init__(self, data=[], idealized=False):
        """
        `Series` are lists of episodes which also store relevant parameters
        about the recording and operations that have been performed on the
        data.
        """
        list.__init__(self,data)

        self.histogram = None

    @property
    def has_piezo(self):
        try: return True if self[0].piezo is not None else False
        except IndexError: return False

    @property
    def has_command(self):
        try: return True if self[0].command is not None else False
        except IndexError: return False

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

    def gaussian_filter(self, filterFrequency=1e3):
        """
        Return a Series object in which all episodes are the filtered version
        of episodes in `self`
        """
        output = copy.deepcopy(self)
        for episode in output:
            episode.gauss_filter_episode(filterFrequency)
        return output

    def CK_filter(self, window_lengths, weight_exponent, weight_window,
				  apriori_f_weights=False, apriori_b_weights=False):
        """
        """
        output = copy.deepcopy(self)
        for episode in output:
            episode.CK_filter_episode(window_lengths, weight_exponent,
                            weight_window, apriori_f_weights, apriori_b_weights)
        return output
    def baseline_correct_all(self, intervals=[], method='poly', degree=1,
                             select_intvl=False,
                             select_piezo=False, active=False, deviation=0.05):
        """
        Return a `Series` object in which the episodes stored in `self` are
        baseline corrected with the given parameters
        """
        output = copy.deepcopy(self)
        for episode in output:
            episode.baseline_correct_episode(degree=degree, intervals=intervals,
                                             method=method,
                                             select_intvl=select_intvl,
                                             select_piezo=select_piezo,
                                             active=active, deviation=deviation)
        return output

    def idealize_all(self, amplitudes, thresholds):
        """
        Return `Series` object containing the idealization of the episodes
        in `self`
        """
        for episode in self:
            episode.idealize(amplitudes, thresholds)

    def check_standarddeviation_all(self, stdthreshold=5e-13):
        """
        Check the standard deviation of the each episode in `self` against the
        given threshold value
        """
        for episode in self:
            episode.check_standarddeviation(stdthreshold)

    def create_histogram(self, active=True, select_piezo=True,
                  deviation=0.05, n_bins=50, density=False,
                  intervals=False):
        time = self[0].time
        piezos = [episode.piezo for episode in self]
        traces = [episode.trace for episode in self]
        trace_list = []
        if select_piezo:
            for piezo, trace in zip(piezos, traces):
                _, _, trace_points = piezo_selection(time, piezo, trace, active,
                                                     deviation)
                trace_list.extend(trace_points)
        elif intervals:
            for trace in traces:
                _, trace_points = interval_selection(time, trace, intervals,
                                                     sampling_rate)
                trace_list.extend(trace_points)
        else:
            trace_list = traces
        trace_list = np.asarray(trace_list)

        trace_list = trace_list.flatten()

        heights, bins = np.histogram(trace_list, n_bins, density=density)

        # get centers of all the bins
        centers = (bins[:-1]+bins[1:])/2
        # get the width of a(ll) bin(s)
        width = (bins[1]-bins[0])
        return heights, bins, centers, width
