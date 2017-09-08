import numpy as np
from read_data import *
from filter import *
from analysis import *
# %matplotlib inline
import matplotlib.pyplot as plt
import copy, os
cwd = os.getcwd()

class Episode(object):    
    def __init__(
        self, names, time, currentTrace, nthEpisode = 0, piezo = None, 
        commandVoltage = None, filter = None, fc = None):
        """
        Episode objects hold all the information about an epoch and should be 
        used to store raw and manipulated data
        
        Parameters:
            time [1D array of floats] - containing time (in seconds)
            currentTrace [1D array of floats] - containing the current trace
            piezo [1D array of floats] - the voltage applied to the Piezo device
            commandVoltage [1D array of floats] - voltage applied to cell
            nthEp [int] - the number of measurements on this cell that came 
                            before this one
            filter [string] - type of filter used
            fc [int] - cutoff frequency of the filter in Hz
        """
        self.time = time*1000 #convert from seconds to milliseconds
        self.currentTrace = currentTrace
        self.piezo = piezo
        self.commandVoltage = commandVoltage
        self.nthEpisode = int(nthEpisode)
        self.names = names
        self.filterMethod = filter
        self.cutoffFrequency = fc
        self.baselineCorrected = False
        self.idealized = 'Note idealized'
    def plot_trace(self):
        fig = plt.figure(figsize = (20,5))
        plt.plot(self.time,self.currentTrace)
        plt.xlabel('time [ms]')
        plt.ylabel(self.names[0])
        plt.show()#not needed with matplotlib inline
    def plot_episode(self, mode='full'):
        if mode == 'full':
            n = 3
            toPlot = [self.currentTrace, self.piezo, self.commandVoltage]
        elif mode == 'current':
            print("This does not work yet!")
#             n = 1
#             toPlot = [self.currentTrace]
            pass
        fig, ax = plt.subplots(n,1,figsize=(20,10),sharex=True)
        fig.suptitle('episode #%.d'%(self.nthEp+1))
        end = np.min([len(self.currentTrace),len(self.time)])
        for i in range(n):
            ax[i].plot(self.time[:end],toPlot[i][:end])
            ax[i].set_ylabel(self.names[i])
        plt.setp(ax,xlabel='time [ms]')
        plt.show() #not needed with matplotlib inline

class Recording(object):
    """
    Recording objects contain all the information and data of a single patch 
    recording as well as the the processed data.
    
    parameters:
    filename [string] - name of the file containing the data
    filepath [string] - path containing the data file
    samplingrate [int] - sampling rate of the recording (samples/second)
    filetype [string] - specify which kind of file is being loaded, takes 'axo' 
    for axograph files and 'bin' for binary files
    headerlength [int] - in case of binary files with a header preceeding the 
    data in the file
    bindtype [numpy type] - in case of binary the data type, should be 
    somemthing like 'np.int16'
    
    Recording objects load the data into Episode objects which can later be 
    filtered or manipulated in other ways. Presently after each manipulation the 
    newly
    processed data as well as the original data are stored.
    """
    def __init__(self, 
                 filename=cwd+'/data/170404 015.axgd',
                 samplingrate=4e4,
                 filetype = 'axo',
                 headerlength = None,
                 bindtype = None,
                 *args,**kwargs):
        
        self.filename = filename
        self.samplingRate = int(float(samplingrate))
        self.filetype = filetype
        self.headerlength = int(float(headerlength))
        self.bindtype = bindtype

        self.data = {'raw':[]}
        ### The raw data and all the result of any manipulations will be stored 
        ###in this dictionary with a key determined by the operations

        #self.load_data()
        
#     def lookup_deco(f):
#         def do_lookup(dataKey, *args, **kwargs):
#             try:
#                 data = self.data[dataKey]
#             except KeyError:
#                 print("The data you're looking for does not exist")
#             f(data, *args, **kwargs)
#         return do_lookup(dataKey, *args, **kwargs)
        
    def load_data(self):
        """Load the raw data from binary of axograph file. All parameters are 
        specified in the initialization of th Recording instance."""
        if self.filetype == 'axo':
            names, time, current, piezo, voltage = load_axo(self.filename)   
            self.data['raw'] = self.store_rawdata(
                                 names, time, current, piezo=piezo, 
                                 commandVoltage = voltage)
        elif self.filetype == 'bin':
            names, time, current = load_binary(
                                    self.filename,self.bindtype,
                                    self.headerlength, self.samplingRate)
            self.data['raw'] = self.store_rawdata(
                                    names, time, current[np.newaxis])
        else:
            print("Filetype not supported.")
            
    def store_rawdata(
        self, names, time, current, piezo = None, commandVoltage = None):
        """
        Store the raw data in epoch objects
        """
        rawData = []
        for i in range(len(current)):
            if piezo is not None:
                ep = Episode(
                    names, time, current[i], nthEpisode=i, piezo=piezo[i], 
                    commandVoltage=commandVoltage[i])
            else:
                ep = Episode(names, time, current[i], nthEpisode=i)
            rawData.append(ep)
        return rawData
            
    def filter_data(self, fc = 1e3, filter = 'Gaussian'):
        if filter == 'Gaussian':
            name = "G"
            fcs = fc/self.samplingRate #cutoff frequency in 1/samples
            filterWindow = Gaussian(fcs)
            filter_lag = 0 #int(1/(2*fcs))
            fData = []
            for episode in self.data['raw']:
                filteredTrace = apply_filter(episode.currentTrace, filterWindow)
                filteredEpisode = copy.deepcopy(episode)
                filteredEpisode.currentTrace = filteredTrace[filter_lag:] 
                filteredEpisode.filterMethod = 'Gaussian'
                filteredEpisode.cutoffFrequency = fc
                fData.append(filteredEpisode)
            name = name+str(int(fc))+'Hz'
            self.data[name] = fData
            
    def baseline_correction(
        self, dataKey, intervals, method='offset', degree=1):
        """
        Do baseline correction on each epoch.
        Parameters:
            interval - list containing the beginning and end points of the 
                       interval from the baseline is to be estimated 
                       (in milliseconds)
            dataKey - string that contains the dictionary key of the data
            method [string] - specify the method, currently supports 
                'offset' - subtract the average value of the signal over the 
                           intervals from the signal
                'poly' - fit a polynomial of given degree to the selected 
                         intervals and subtract it from the signal
            degree [int] - needed for the 'poly' method, degree of polynomial 
                           fitted, default is 1 (linear regression)
                
        """
        try: ###should write a decorator that does this
            data = self.data[dataKey]
        except KeyError:
            print("These data don't exist.")
            pass
        if "_BC" in dataKey:
            print("Baseline correction has already "
                  "been performed on these data.")
            pass
        corrected = []
        if method is 'offset':
            for episode in data:
                correctedEpisode = copy.deepcopy(episode)
                correctedEpisode.currentTrace = baseline(
                    episode.currentTrace, 
                    self.samplingRate, 
                    intervals)
                correctedEpisode.baselineCorrected = True
                corrected.append(correctedEpisode)
        elif method is 'poly':
            for episode in data:
                correctedEpisode = copy.deepcopy(episode)
                correctedEpisode.currentTrace = poly_baseline(
                    episode.time, episode.currentTrace, 
                    self.samplingRate, intervals, 
                    degree=degree)
                correctedEpisode.baselineCorrected = True
                corrected.append(correctedEpisode)
        name = dataKey+"_BC"
        self.data[name] = corrected
    
    def idealization(self, dataKey, threshold = .5):
        if self.filetype is not 'bin':
            print("Can only idealize single level "
                  "channels so far. (That means bin files)")
            pass
        try:
            data = self.data[dataKey]
        except KeyError:
            print("These data don't exist.")
            pass
        idealized = []
        for episode in data:
            idealizedEpisode = copy.deepcopy(episode)
            activity, signalmax = threshold_crossing(
                                    idealizedEpisode.currentTrace,threshold)
            idealizedEpisode.currentTrace = activity*signalmax
            idealizedEpisode.idealized = (
            'Idealized with simple threshold crossing')
            idealized.append(idealizedEpisode)
        name = dataKey + '_TC'
        self.data[name] = idealized