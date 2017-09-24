import numpy as np
import readdata
import filtering
import analysis
import matplotlib.pyplot as plt
import copy
import os
cwd = os.getcwd()

class Episode(object):    
    def __init__(self, names, time, currentTrace, nthEpisode = 0, 
                 piezo = None, commandVoltage = None, 
                 filtertype = None, fc = None):
        """
        Episode objects hold all the information about an epoch and 
        should be used to store raw and manipulated data
        
        Parameters:
            time [1D array of floats] - containing time (in seconds)
            currentTrace [1D array of floats] - containing the current trace
            piezo [1D array of floats] - the voltage applied to the 
                                         Piezo device
            commandVoltage [1D array of floats] - voltage applied to 
                                                  cell
            nthEp [int] - the number of measurements on this cell that 
                          came before this one
            filtertype [string] - type of filter used
            fc [int] - cutoff frequency of the filter in Hz
        """
        self.time = time*1000 #convert from seconds to milliseconds
        self.currentTrace = currentTrace
        self.piezo = piezo
        self.commandVoltage = commandVoltage
        self.nthEpisode = int(nthEpisode)
        self.names = names
        self.filterMethod = filtertype
        self.cutoffFrequency = fc
        self.baselineCorrected = False
        self.idealized = False
        

class Recording(dict):
    """
    Recording objects contain all the information and data of a single
    patch recording as well as the the processed data.
    
    parameters:
    filename [string] - name of the file containing the data
    filepath [string] - path containing the data file
    samplingrate [int] - sampling rate of the recording 
                         (in units of samples/second)
    filetype [string] - specify which kind of file is being loaded, 
                        takes 'axo' for axograph files and 'bin' for 
                        binary files
    headerlength [int] - in case of binary files with a header 
                         preceeding the data in the file
    bindtype [numpy type] - in case of binary the data type, should be 
                            somemthing like 'np.int16'
    
    Recording objects load the data into Episode objects which can 
    later be filtered or manipulated in other ways. Presently after 
    each manipulation the newly processed data as well as the original 
    data are stored.
    """
    def __init__(self, 
                 filename=cwd+'/data/170404 015.axgd',
                 samplingrate=4e4,
                 filetype = 'axo',
                 headerlength = 0,
                 bindtype = None,):
        
        self.filename = filename
        self.samplingrate = int(float(samplingrate))
        self.filetype = filetype
        self.headerlength = int(float(headerlength))
        self.bindtype = bindtype
        self['raw'] = []

        self.load_data()


    def load_data(self):
        """Load the raw data from binary of axograph file. All 
        parameters are specified in the initialization of the 
        Recording instance."""
        loadedfile = readdata.load(self.filetype, self.filename, 
                                   self.bindtype, self.headerlength, 
                                   self.samplingrate)
        self.store_rawdata(*loadedfile)


    def store_rawdata(self, names, time, current, piezo = None, 
                      commandVoltage = None):
        for i in range(len(current)):
            if piezo is not None: # `piezo not None` differentiates 
                                  #  between axograph and bin data
                ep = Episode(names, time, current[i], nthEpisode=i, 
                             piezo=piezo[i], 
                             commandVoltage=commandVoltage[i])
            else:
                ep = Episode(names, time, current[i], nthEpisode=i)
            self['raw'].append(ep)
            

    def filter_data(self, filterfreq = 1e3, filtertype = 'Gaussian', 
                    datakey='raw'):
        if not self[datakey]:
            print("These data do not exist.")
            pass

        if filtertype == 'Gaussian':
            frequencyinsamples = filterfreq/self.samplingrate 
            filterWindow = filtering.gaussian(frequencyinsamples)
            filter_lag = 0 #int(1/(2*frequencyinsamples))
            newdataKey = 'G'+str(int(filterfreq))+'Hz'
            self[newdataKey] = []
            for episode in self[datakey]:
                filteredTrace = filtering.applyfilter(
                                                episode.currentTrace, 
                                                filterWindow)
                filteredEpisode = copy.deepcopy(episode)
                filteredEpisode.currentTrace = (
                                          filteredTrace[filter_lag:] )
                filteredEpisode.filterMethod = 'Gaussian'
                filteredEpisode.cutoffFrequency = filterfreq
                self[newdataKey].append(filteredEpisode)
        print("actually filterered the stuff")
        return newdataKey

            
    def baseline_correction(self, datakey, intervals, method='poly', 
                            degree=1):
        """
        Do baseline correction on each epoch.
        Parameters:
            interval - list containing the beginning and end points of 
                       the interval from the baseline is to be 
                       estimated (in milliseconds)
            datakey - string that contains the dictionary key of the 
                      data
            method [string] - specify the method, currently supports 
                'offset' - subtract the average value of the signal 
                           over the intervals from the signal
                'poly' - fit a polynomial of given degree to the 
                         selected intervals and subtract it from the 
                         signal
            degree [int] - needed for the 'poly' method, degree of 
                           polynomial fitted, default is 1 (linear 
                           regression)
                
        """
        if not self[datakey]:
            print("These data do not exist.")
            pass
        elif "_BC" in datakey:
            pass

        newdataKey = datakey+"_BC"
        self[newdataKey] = []

        for episode in self[datakey]:
                correctedEpisode = copy.deepcopy(episode)
                correctedEpisode.currentTrace = (
                    analysis.baseline(episode.time,
                                    episode.currentTrace, 
                                    self.samplingrate, intervals, 
                                    degree = degree, method = method))
                correctedEpisode.baselineCorrected = True
                self[newdataKey].append(correctedEpisode)


    def idealization(self, datakey, threshold = 0.5):
        if self.filetype is not 'bin':
            print("Can only idealize single level "
                  "channels so far. (That means .bin files)")
            pass

        if not self[datakey]:
            print("These data do not exist.")
            pass
        elif '_TC' in datakey:
            pass

        newdataKey = datakey + '_TC'
        self[newdataKey] = []
        for episode in self[datakey]:
            idealizedEpisode = copy.deepcopy(episode)
            activity, signalmax = (
                threshold_crossing(idealizedEpisode.currentTrace,
                                   threshold))
            idealizedEpisode.currentTrace = activity*signalmax
            idealizedEpisode.idealized = (
                                'Idealized with threshold crossing')
            self[newdataKey].append(idealizedEpisode)

