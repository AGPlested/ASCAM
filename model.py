import numpy as np
import readdata
import filtering
import analysis
import matplotlib.pyplot as plt
import copy
import os
from tools import piezo_selection
cwd = os.getcwd()

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
        self['trace'] = filtering.gaussian_filter(self['trace'], 
                                                  filterFrequency,
                                                  samplingRate,
                                                  method)[filterLag:]
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

class Series(list):
    def __init__(self, data = [], samplingRate = 4e4, filterFrequency = False,         
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
        self.samplingRate = samplingRate
        self.filterFrequency = filterFrequency
        self.baselineCorrected = baselineCorrected
        self.baselineIntervals = baselineIntervals
        self.baselineMethod = baselineMethod
        self.baselineDegree = baselineDegree
        self.idealized = idealized

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
            episode.filter_episode(filterFrequency, self.samplingRate)
        return output

    def baseline_correct_all(self, intervals, method = 'poly', degree = 1,
                                 timeUnit = 'ms', intervalSelection = False,
                                 piezoSelection = False, active = False,
                                 deviation = 0.05):
        """
        Return a `Series` object in which the episodes stored in `self` are
        baseline corrected with the given parameters
        """
        output = copy.deepcopy(self)
        for episode in output:
            episode.baseline_correct_episode(degree = degree,
                                             intervals = intervals, 
                                             method = method,
                                             timeUnit = timeUnit,
                                             intervalSelection = (
                                                   intervalSelection),
                                             piezoSelection = (
                                                      piezoSelection),
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

class Recording(dict):
    def __init__(self, filename = '', 
                 samplingRate = 0, filetype = '', headerlength = 0,
                 bindtype = None, timeUnit = 'ms', piezoUnit = 'V',
                 commandUnit = 'V', currentUnit = 'A'):
        ### parameters for loading the data
        self.filename = filename
        self.filetype = filetype
        self.headerlength = int(float(headerlength))
        self.bindtype = bindtype

        ### attributes of the data
        self.samplingRate = int(float(samplingRate))
        self.timeUnit = timeUnit
        self.commandUnit = commandUnit
        self.currentUnit = currentUnit
        self.piezoUnit = piezoUnit

        ### attributes for storing and managing the data
        self['raw_'] = Series()
        self.currentDatakey = 'raw_'
        self.currentEpisode = 0

        ### if a file is specified load it
        if filename: self.load_data()

        ### variables for user created lists of episodes
        ### `lists` stores the indices of the episodes in the list and their 
        ### color under their name
        self.lists = {'all': [range(len(self['raw_'])), 'white']}
        self.current_lists = ['all']

    def load_data(self):
        """
        Load the data in the file at `self.filename`.
        Accepts `.mat`, `.axgd` and `.bin` files.
        (`.bin` files are for simulated data only at the moment.)
        """
        names, *loaded_data = readdata.load(self.filetype, self.filename,
                               self.bindtype, self.headerlength,
                               self.samplingRate)
        ### The `if` accounts for the presence or absence of
        ### piezo and command voltage in the data being loaded

        if 'Piezo [V]' in names and 'Command Voltage [V]' in names:
            time = loaded_data[0]
            self['raw_'] = Series([Episode(time, trace, nthEpisode=i, 
                                            piezo=pTrace, 
                                            command=cVtrace, 
                                            samplingRate = self.samplingRate)
                                    for i, (trace, pTrace, cVtrace) 
                                    in enumerate(zip(*loaded_data[1:]))])

        elif 'Piezo [V]' in names:
            time, current, piezo, _ = loaded_data
            self['raw_'] = Series([Episode(time, current[i], nthEpisode=i, 
                                            piezo=piezo[i], 
                                            samplingRate = self.samplingRate)
                                    for i in range(len(current))])

        elif 'Command Voltage [V]' in names:
            time, current, _, command = loaded_data
            self['raw_'] = Series([Episode(time, current[i], nthEpisode=i, 
                                            command=command[i], 
                                            samplingRate = self.samplingRate)
                                    for i in range(len(current))])

        else:
            time, current, _, _ = loaded_data
            self['raw_'] = Series([Episode(time, current[i], nthEpisode=i, 
                                            samplingRate = self.samplingRate)
                                    for i in range(len(current))])

    def call_operation(self, operation, *args, **kwargs):
        """
        Calls an operation to be performed on the data.
        Valid operations:
        'BC_' - baseline correction
        'FILTER_' - filter
        'TC_' - threshold crossing

        returns TRUE if the operation was called FALSE if not
        """
        valid = self.check_operation(operation)
        if valid:
            newDatakey = operation+str(*args)+'_'
            if operation == 'FILTER_':
                self[newDatakey] = self[self.currentDatakey].filter_all(*args)
            elif operation == 'BC_':
                self[newDatakey] = (
                        self[self.currentDatakey].baseline_correct_all(*args,
                                                                    **kwargs))
            elif operation == 'TC_':
                self[newDatakey]=self[self.currentDatakey].idealize_all(*args)
            else:
                print("Uknown operation!")
            self.currentDatakey = newDatakey
        return valid

    def check_operation(self, operation):
        """
        Check if the requested operatioin is valid, i.e. if it has not already
        been applied to the current series.
        The check is to see if the series has been filter or baselined. It
        does not compare the filter frequency so filtering twice at different
        frequencies is currently forbidden.
        """
        if operation in self.currentDatakey:
            print(operation+" has already been performed on this series.")
            print('Current series is '+self.currentDatakey)
            return False
        else:
            return True

            
