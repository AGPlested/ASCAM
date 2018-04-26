import numpy as np
import filtering
import analysis
from tools import piezo_selection, detect_filetype

class Episode(dict):
    def __init__(self, time, trace, nthEpisode = 0, piezo = None,
                 command = None, filterType = None, fc = None,
                 samplingRate = 4e4, timeInputUnit = 'ms'):
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
            fc [int] - cutoff frequency of the filter in Hz
        """
        time_unit_multiplier = 1
        if timeInputUnit == 'ms':
            time_unit_multiplier = 1000

        self.filterFrequency = np.inf
        self.baselineCorrected = False
        self.idealized = False

        self['time'] = time*time_unit_multiplier
        self['trace'] = trace
        self['piezo'] = piezo
        self['command'] = command
        self.nthEpisode = int(nthEpisode)
        self.samplingRate = samplingRate
        self.suspiciousSTD = False

    def filter_episode(self, filterFrequency = 1e3, samplingRate = None,
                       method = 'convolution'):
        if samplingRate is None:
            samplingRate = self.samplingRate
        filterLag = 0 #int(1/(2*frequencyOnSamples))
        self['trace'] = filtering.gaussian_filter(
                                            signal = self['trace'],
                                            filterFrequency = filterFrequency,
                                            samplingRate = samplingRate,
                                            method = method
                                            )[filterLag:]
        self.filterFrequency = filterFrequency

    def baseline_correct_episode(self, intervals, method = 'poly', degree = 1,
                                 timeUnit = 'ms', intervalSelection = False,
                                 piezoSelection = False, active = False,
                                 deviation = 0.05):
        self['trace'] = analysis.baseline_correction(time = self['time'],
                                                     signal = self['trace'],
                                                     fs = self.samplingRate,
                                                     intervals = intervals,
                                                     degree = degree,
                                                     method = method,
                                                     timeUnit = timeUnit,
                                                     intervalSelection = (
                                                           intervalSelection),
                                                     piezo = self['piezo'],
                                                     piezoSelection = (
                                                              piezoSelection),
                                                     active = active,
                                                     deviation = deviation)
        self.baselineCorrected = True

    def idealize(self, thresholds):
        activity, signalmax = threshold_crossing(self['trace'], thresholds)
        episode['trace'] = activity*signalmax
        self.idealized = True

    def check_standarddeviation_all(self, stdthreshold = 5e-13):
        """
        check the standard deviation of the episode against a reference value
        """
        _, _, trace = piezo_selection(self['time'], self['piezo'],
                                      self['trace'], active = False,
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
            mean = np.mean(self['command'])
            std = np.std(self['command'])
        except: pass
        return mean, std
