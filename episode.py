import numpy as np
import filtering
import analysis
from tools import piezo_selection, parse_filename

class Episode():
    def __init__(self, time, trace, n_episode = 0, piezo = None,
                 command = None, filterType = None,
                 sampling_rate = 4e4, timeInputUnit = 'ms'):
        """
        Episode objects hold all the information about an epoch and
        should be used to store raw and manipulated data

        Parameters:
            time [1D array of floats] - containing time (in seconds)
            trace [1D array of floats] - containing the current
                                                trace
            piezo [1D array of floats] - the voltage applied to the
                                         Piezo device
            command [1D array of floats] - voltage applied to
                                                  cell
            nthEp [int] - the number of measurements on this cell that
                          came before this one
            filterType [string] - type of filter used
        """
        time_unit_multiplier = 1
        if timeInputUnit == 'ms':
            time_unit_multiplier = 1000

        self.filterFrequency = np.inf
        self.baselineCorrected = False
        self.idealized = False

        self.time = time*time_unit_multiplier
        self.trace = trace
        self.piezo = piezo
        self.command = command
        self.n_episode = int(n_episode)
        self.sampling_rate = sampling_rate
        self.suspiciousSTD = False

    def filter_episode(self, filterFrequency = 1e3, sampling_rate = None,
                       method = 'convolution'):
        if sampling_rate is None:
            sampling_rate = self.sampling_rate
        filterLag = 0 #int(1/(2*frequencyOnSamples))
        self.trace = filtering.gaussian_filter(
                                            signal = self.trace,
                                            filterFrequency = filterFrequency,
                                            sampling_rate = sampling_rate,
                                            method = method
                                            )[filterLag:]
        self.filterFrequency = filterFrequency

    def baseline_correct_episode(self, intervals, method = 'poly', degree = 1,
                                 timeUnit = 'ms', select_intvl = False,
                                 select_piezo = False, active = False,
                                 deviation = 0.05):
        self.trace = analysis.baseline_correction(time = self.time,
                                                     signal = self.trace,
                                                     fs = self.sampling_rate,
                                                     intervals = intervals,
                                                     degree = degree,
                                                     method = method,
                                                     timeUnit = timeUnit,
                                                     select_intvl = (
                                                           select_intvl),
                                                     piezo = self.piezo,
                                                     select_piezo = (
                                                              select_piezo),
                                                     active = active,
                                                     deviation = deviation)
        self.baselineCorrected = True

    def idealize(self, thresholds):
        activity, signalmax = threshold_crossing(self.trace, thresholds)
        episode.trace = activity*signalmax
        self.idealized = True

    def check_standarddeviation_all(self, stdthreshold = 5e-13):
        """
        check the standard deviation of the episode against a reference value
        """
        _, _, trace = piezo_selection(self.time, self.piezo,
                                      self.trace, active = False,
                                      deviation = 0.01)
        tracestd = np.std(trace)
        if tracestd>stdthreshold:
            self.suspiciousSTD = True

    def get_command_stats(self):
        """
        Get the mean and standard deviation of the command voltage of the
        episode
        """
        try:
            mean = np.mean(self.command)
            std = np.std(self.command)
        except: pass
        return mean, std
