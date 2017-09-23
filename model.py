import numpy as np
import readdata
import filtering
import analysis
import matplotlib.pyplot as plt
import copy
import os
cwd = os.getcwd()

class Episode(object):    
    def __init__(self, names, time, currentTrace, nthEpisode = 0, piezo = None, 
                 commandVoltage = None, filtertype = None, fc = None
                 ):
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

#     def plot_trace(self):
#         fig = plt.figure(figsize = (20,5))
#         plt.plot(self.time,self.currentTrace)
#         plt.xlabel('time [ms]')
#         plt.ylabel(self.names[0])
#         plt.show()#not needed with matplotlib inline

#     def plot_episode(self, mode='full'):
#         if mode == 'full':
#             n = 3
#             toPlot = [self.currentTrace, self.piezo, self.commandVoltage]
#         elif mode == 'current':
#             print("This does not work yet!")
# #             n = 1
# #             toPlot = [self.currentTrace]
#             pass
#         fig, ax = plt.subplots(n,1,figsize=(20,10),sharex=True)
#         fig.suptitle('episode #%.d'%(self.nthEp+1))
#         end = np.min([len(self.currentTrace),len(self.time)])
#         for i in range(n):
#             ax[i].plot(self.time[:end],toPlot[i][:end])
#             ax[i].set_ylabel(self.names[i])
#         plt.setp(ax,xlabel='time [ms]')
#         plt.show() #not needed with matplotlib inline

class Recording(dict):
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
                 headerlength = 0,
                 bindtype = None,
                 ):
        
        self.filename = filename
        self.samplingrate = int(float(samplingrate))
        self.filetype = filetype
        self.headerlength = int(float(headerlength))
        self.bindtype = bindtype
        self['raw'] = []

        self.load_data()


    def load_data(self):
        """Load the raw data from binary of axograph file. All parameters are 
        specified in the initialization of th Recording instance."""
        loadedfile = readdata.load(self.filetype, self.filename,
                                    self.bindtype, self.headerlength, 
                                    self.samplingrate
                                    )
        self.store_rawdata(*loadedfile)

    def store_rawdata(self, names, time, current, piezo = None, 
                      commandVoltage = None
                      ):
        rawdata = []
        for i in range(len(current)):
            if piezo is not None: # `piezo not None` differentiates between axograph and bin data
                ep = Episode(names, time, current[i], nthEpisode=i, 
                             piezo=piezo[i], commandVoltage=commandVoltage[i]
                             )
            else:
                ep = Episode(names, time, current[i], nthEpisode=i)
            rawdata.append(ep)
        self['raw'] = rawdata
            
    def filter_data(self, fc = 1e3, filtertype = 'Gaussian', dataKey='raw'):
        if not self[dataKey]:
            print("These data do not exist.")
            pass
        if filtertype == 'Gaussian':
            name = "G"
            fcs = fc/self.samplingrate #cutoff frequency in 1/samples
            filterWindow = filtering.gaussian(fcs)
            filter_lag = 0 #int(1/(2*fcs))
            fData = []
            for episode in self[dataKey]:
                filteredTrace = filtering.applyfilter(episode.currentTrace, 
                                                      filterWindow
                                                      )
                filteredEpisode = copy.deepcopy(episode)
                filteredEpisode.currentTrace = filteredTrace[filter_lag:] 
                filteredEpisode.filterMethod = 'Gaussian'
                filteredEpisode.cutoffFrequency = fc
                fData.append(filteredEpisode)
            name = name+str(int(fc))+'Hz'
            self[name] = fData
            
    def baseline_correction(self, dataKey, intervals, method='poly', 
                            degree=1
                            ):
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
        if not self[dataKey]:
            print("These data do not exist.")
            pass
        elif "_BC" in dataKey:
            pass

        newdataKey = dataKey+"_BC"
        self[newdataKey] = []

        for episode in self[dataKey]:
                correctedEpisode = copy.deepcopy(episode)
                correctedEpisode.currentTrace = analysis.baseline(
                                                        episode.time,
                                                        episode.currentTrace, 
                                                        self.samplingrate, 
                                                        intervals, 
                                                        degree = degree,
                                                        method = method
                                                        )
                correctedEpisode.baselineCorrected = True
                self[newdataKey].append(correctedEpisode)


    
    def idealization(self, dataKey, threshold = 0.5):
        if self.filetype is not 'bin':
            print("Can only idealize single level "
                  "channels so far. (That means .bin files)")
            pass
        if not self[dataKey]:
            print("These data do not exist.")
            pass
        idealized = []
        for episode in data:
            idealizedEpisode = copy.deepcopy(episode)
            activity, signalmax = threshold_crossing(
                                                idealizedEpisode.currentTrace,
                                                threshold
                                                )
            idealizedEpisode.currentTrace = activity*signalmax
            idealizedEpisode.idealized = (
                                    'Idealized with simple threshold crossing'
                                    )
            idealized.append(idealizedEpisode)
        name = dataKey + '_TC'
        self[name] = idealized

if __name__ == '__main__':
    r = Recording()
    r.load_data()