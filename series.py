import numpy as np
import copy
from episode import Episode

class Series(list):
    def __init__(self, data = [],
                 baselineCorrected = False, baselineIntervals = False,
                 baselineMethod = 'poly', baselineDegree = 1,
                 idealized = False, reconstruct = False):
        """
        `Series` are lists of episodes which also store relevant parameters
        about the recording and operations that have been performed on the
        data.

        The `reconstruct` input is a placeholder
        """
        list.__init__(self,data)

    def get_min(self,name):
        return np.min([np.min(episode[name]) for episode in self])

    def get_max(self,name):
        return np.max([np.max(episode[name]) for episode in self])

    def filter_all(self, filterFrequency = 1e3):
        """
        Return a Series object in which all episodes are the filtered version
        of episodes in `self`
        """
        output = copy.deepcopy(self)
        for episode in output:
            episode.filter_episode(filterFrequency, episode.sampling_rate)
        return output

    def baseline_correct_all(self, intervals = [], method = 'poly',
                             degree = 1, timeUnit = 'ms',
                             intervalSelection = False,
                             piezoSelection = False, active = False,
                             deviation = 0.05):
        """
        Return a `Series` object in which the episodes stored in `self` are
        baseline corrected with the given parameters
        """
        output = copy.deepcopy(self)
        for episode in output:
            episode.baseline_correct_episode(
                                        degree = degree,
                                        intervals = intervals,
                                        method = method,
                                        timeUnit = timeUnit,
                                        intervalSelection = intervalSelection,
                                        piezoSelection = piezoSelection,
                                        active = active,
                                        deviation = deviation)
        return output

    def idealize_all(self, thresholds):
        """
        Return `Series` object containing the idealization of the episodes
        in `self`
        """
        output = copy.deepcopy(self)
        for episode in output:
            episode.idealize(thresholds)
        return output

    def check_standarddeviation_all(self, stdthreshold = 5e-13):
        """
        Check the standard deviation of the each episode in `self` against the
        given threshold value
        """
        for episode in self:
            episode.check_standarddeviation(stdthreshold)
