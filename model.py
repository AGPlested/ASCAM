import numpy as np
import readdata
import filtering
import analysis
import matplotlib.pyplot as plt
import copy
import os
cwd = os.getcwd()

class Episode(dict):    
    def __init__(self, time, trace, nthEpisode = 0, 
                 piezo = None, commandVoltage = None, 
                 filterType = None, fc = None, 
                 samplingRate = 4e4,
                 timeInputUnit = 'seconds'):
        """
        Episode objects hold all the information about an epoch and 
        should be used to store raw and manipulated data
        
        Parameters:
            time [1D array of floats] - containing time (in seconds)
            trace [1D array of floats] - containing the current 
                                                trace
            piezo [1D array of floats] - the voltage applied to the 
                                         Piezo device
            commandVoltage [1D array of floats] - voltage applied to 
                                                  cell
            nthEp [int] - the number of measurements on this cell that 
                          came before this one
            filterType [string] - type of filter used
            fc [int] - cutoff frequency of the filter in Hz
        """
        if timeInputUnit is 'seconds':
          timeUnitMultiplier = 1000
        else:
          timeUnitMultiplier = 1

        self.filterFrequency = np.inf
        self.baselineCorrected = False
        self.idealized = False

        self['time'] = time*timeUnitMultiplier
        self['trace'] = trace
        self['piezo'] = piezo
        self['commandVoltage'] = commandVoltage
        self.nthEpisode = int(nthEpisode)
        self.samplingRate = samplingRate
        self.suspiciousSTD = False

    def filter_episode(self, filterFrequency = 1e3, 
                       samplingRate = None, 
                       method = 'convolution'):
        if samplingRate is None:
            samplingRate = self.samplingRate
        filterLag = 0 #int(1/(2*frequencyOnSamples))
        self['trace'] = filtering.gaussian_filter(self['trace'], 
                                                  filterFrequency, 
                                                  samplingRate, 
                                                  method)[filterLag:]
        self.filterFrequency = filterFrequency

    def baseline_correct_episode(self, intervals, method='poly', degree=1):
        self['trace'] = analysis.baseline_correction(self['time'], 
                                            self['trace'], self.samplingRate, 
                                            intervals, degree = degree, 
                                            method = method)
        self.baselineCorrected = True

    def idealize(self, thresholds):
        activity, signalmax = threshold_crossing(self['trace'], thresholds)
        episode['trace'] = activity*signalmax
        self.idealized = True

    def check_standarddeviation_all(self, stdthreshold = 5e-13):
        piezomax = np.max(np.abs(self['piezo']))
        times = self['piezo']<piezomax/100
        tracestd = np.std(self['trace'][times])
        if tracestd>stdthreshold:
            self.suspiciousSTD = True


class Series(list):
    def __init__(self, 
                 samplingRate = 4e4,
                 filterFrequency = False, 
                 filterMethod = 'convolution',
                 baselineCorrected = False,
                 baselineIntervals = False,
                 baselineMethod = 'poly',
                 baselineDegree = 1, 
                 idealized = False):
        self.samplingRate = samplingRate
        self.filterFrequency = filterFrequency
        self.baselineCorrected = baselineCorrected
        self.idealized = idealized

        if baselineCorrected and intervalsBaseline:
            self.baseline_correct_all(baselineIntervals, baselineMethod,
                                      baselineDegree)
        if filterFrequency:
            self.filter_all(filterFrequency, samplingRate, method)
    
    def filter_all(self, filterFrequency = 1e3, 
                   samplingRate = None, method = 'convolution'):
        if samplingRate is None:
            samplingRate = self.samplingRate
        for episode in self:
            episode.filter_episode(filterFrequency, samplingRate, method)
            
    def baseline_correct_all(self, intervals, method='poly', degree=1):
        for episode in self:
            episode.baseline_correct_episode(intervals, method, degree)

    def idealize_all(self, thresholds):
        for episode in self:
            episode.idealize(thresholds)

    def check_standarddeviation_all(self, stdthreshold = 5e-13):
        for episode in self:
            episode.check_standarddeviation(stdthreshold)


class Model(dict):
    def __init__(self, 
                 filename = cwd+'/data/170404 015.axgd',
                 samplingRate = 4e4,
                 filetype = 'axo',
                 headerlength = 0,
                 bindtype = None):

        self.filename = filename
        self.samplingRate = int(float(samplingRate))
        self.filetype = filetype
        self.headerlength = int(float(headerlength))
        self.bindtype = bindtype
        self['raw_'] = Series()
        self.load_data()
        self.currentDatakey = 'raw_'
        self.currentEpisode = 0

    def load_data(self):
        loadedfile = readdata.load(self.filetype, self.filename, 
                               self.bindtype, self.headerlength, 
                               self.samplingRate)
        if self.filetype == 'axo':
            names, time, current, piezo, voltage = loadedfile
            for i in range(len(current)):
                self['raw_'].append(Episode(time, current[i], nthEpisode=i, 
                             piezo=piezo[i], commandVoltage=voltage[i], 
                             samplingRate = self.samplingRate))
        elif self.filetype == 'bin': #this here because the data we simulate is in binary format
            names, time, current = loadedfile
            for i in range(len(current)):
                self['raw_'].append(Episode(time, current[i], nthEpisode=i,
                                            samplingRate = self.samplingRate))
    
    def call_operation(self, operation, *args):
        """
        Valid operations:
        BC_ - baseline correction
        FILTER_ - filter
        TC_ - threshold crossing
        """
        if self.currentDatakey == 'raw_':
            newDatakey = operation
        else:
            newDatakey = self.currentDatakey+operation
        if self.check_operation(newDatakey, operation, *args):
            self.apply_operation(newDatakey, operation, *args)

    def check_operation(self, newDatakey, operation, *args):
        # if operation in self.keys():
        #     print("This operation has already been performed")
        #     return False
        # else:
        return True

    def apply_operation(self, newDatakey, operation, *args):
        newData = copy.deepcopy(self[self.currentDatakey])
        if operation == 'BC_':
            newData.baseline_correct_all(*args)
        elif operation == 'FILTER_':
            newData.filter_all(*args)
        elif operation == 'TC_':
            newData.idealization(*args)
        else:
            print("Uknown operation!")
        self[newDatakey] = newData
        self.currentDatakey = newDatakey