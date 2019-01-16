import os
import logging as log
import pickle

from scipy import io
import numpy as np

import readdata
import savedata
from tools import parse_filename, piezo_selection, interval_selection
from episode import Episode
from series import Series

class Recording(dict):
    def __init__(self, filename='data/180426 000 Copy Export.mat',
                 sampling_rate=4e4, filetype='',
                 headerlength=0, dtype=None):
        log.info("""intializing Recording""")

        # parameters for loading the data
        self.filename = filename
        self.filetype = filetype
        self.headerlength = int(float(headerlength))
        self.dtype = dtype

        # attributes of the data
        self.sampling_rate = int(float(sampling_rate))

        # attributes for storing and managing the data
        self['raw_'] = Series()
        self.currentDatakey = 'raw_'
        self.n_episode = 0

        self.hist_times=0
        #parameters for analysis
        #idealization
        self._TC_thresholds = np.array([])
        self._TC_amplitudes = np.array([])
        self.tc_unit = 'pA'
        self.tc_unit_factors = {'fA':1e15, 'pA':1e12, 'nA':1e9, 'µA':1e6,
                                    'mA':1e3, 'A':1}
        #first activation
        self._fa_threshold = 0.
        # variables for user created lists of episodes
        # `lists` stores the indices of the episodes in the list in the first
        # element, their color in the GUI in the second and the associated key
        # (i.e. for adding selected episodes to the list in the third element
        # of a tuple that is the value under the list's name (as dict key)
        self.lists = dict()
        self.current_lists = ['all']
        # if a file is specified load it
        if filename:
            log.info("""`filename` is not empty, will load data""")
            self.load_data()
        #if the lists attribute has not been set while loading the data do it
        #now
        #lists is a dict with key name_of_list and values (episodes, color, key)
        if not self.lists:
            self.lists = {'all':(list(range(len(self['raw_']))), 'white', None)}

    @property
    def fa_threshold(self):
        return self._fa_threshold*self.tc_unit_factors[self.tc_unit]

    @fa_threshold.setter
    def fa_threshold(self, theta):
        self._fa_threshold = theta/self.tc_unit_factors[self.tc_unit]

    @property
    def TC_amplitudes(self):
        return self._TC_amplitudes*self.tc_unit_factors[self.tc_unit]

    @TC_amplitudes.setter
    def TC_amplitudes(self, amps):
        self._TC_amplitudes = amps/self.tc_unit_factors[self.tc_unit]

    @property
    def TC_thresholds(self):
        return self._TC_thresholds*self.tc_unit_factors[self.tc_unit]

    @TC_thresholds.setter
    def TC_thresholds(self, amps):
        self._TC_thresholds = amps/self.tc_unit_factors[self.tc_unit]

    @property
    def selected_episodes(self):
        indices = list()
        for listname in self.current_lists:
            indices.extend(self.lists[listname][0])
        # remove duplicate indices
        indices = np.array(list(set(indices)))
        return np.array(self.series)[indices]

    @property
    def series(self): return self[self.currentDatakey]

    @property
    def episode(self): return self.series[self.n_episode]

    @property
    def has_piezo(self): return self.series.has_piezo

    @property
    def has_command(self): return self.series.has_command

    @property
    def time_unit(self): return self.episode.time_unit

    @property
    def trace_unit(self): return self.episode.trace_unit

    @property
    def piezo_unit(self): return self.episode.piezo_unit

    @property
    def command_unit(self): return self.episode.command_unit

    def load_data(self):
        """
        this method is supposed to load data from a file or a directory
        """
        log.debug(f"load_data")
        if 'pkl' in parse_filename(self.filename)[0]:
            loaded_data = readdata.load_pickle(self.filename)
            self.__dict__ = loaded_data.__dict__
            for key, value in loaded_data.items():
                self[key] = value
        elif os.path.isfile(self.filename):
            self.load_series(filename = self.filename,
                             filetype = self.filetype,
                             dtype = self.dtype,
                             headerlength = self.headerlength,
                             sampling_rate = self.sampling_rate,
                             datakey = 'raw_')
        elif os.path.isdir(self.filename):
            if not self.filename.endswith('/'):
                self.filename+='/'
            # loop once to find the json file and extract the datakeys
            for file in os.listdir(self.filename):
                if file.endswith('json'):
                    metadata, series_metadata = readdata.read_metadata(
                    self.filename+file)
                    break
                # recreate recording attributes
                self.__dict__ = metadata

            # loop again to find the data and load it
            for file in os.listdir(self.filename):
                for datakey in series_metadata.keys():
                    if datakey in file:
                        self.load_series(
                                    filename = self.filename+file,
                                    filetype = metadata['filetype'],
                                    dtype = metadata['dtype'],
                                    headerlength = metadata['headerlength'],
                                    sampling_rate = metadata['sampling_rate'],
                                    datakey=datakey)
                        for episode, attributes in zip(self[datakey],
                                            series_metadata[datakey].values()):
                            episode.__dict__ = attributes

    def load_series(self, filename, filetype, dtype, headerlength, datakey,
                    sampling_rate):
        """
        Load the data in the file at `self.filename`.
        Accepts `.mat`, `.axgd` and `.bin` files.
        (`.bin` files are for simulated data only at the moment.)
        """
        log.debug(f"load_series")
        names, *loaded_data = readdata.load(filename = filename,
                                            filetype = filetype,
                                            dtype = dtype,
                                            headerlength = headerlength,
                                            fs = sampling_rate)
        # The `if` accounts for the presence or absence of
        # piezo and command voltage in the data being loaded

        if 'Piezo [V]' in names and 'Command Voltage [V]' in names:
            time = loaded_data[0]
            self[datakey] = Series([Episode(time, trace, n_episode=i,
                                            piezo=piezo,
                                            command=command,
                                            sampling_rate = self.sampling_rate)
                                    for i, (trace, piezo, command)
                                    in enumerate(zip(*loaded_data[1:]))])

        elif 'Piezo [V]' in names:
            time, current, piezo, _ = loaded_data
            self[datakey] = Series([Episode(time, current[i], n_episode=i,
                                            piezo=piezo[i],
                                            sampling_rate = self.sampling_rate)
                                    for i in range(len(current))])

        elif 'Command Voltage [V]' in names:
            time, current, _, command = loaded_data
            self[datakey] = Series([Episode(time, current[i], n_episode=i,
                                            command=command[i],
                                            sampling_rate = self.sampling_rate)
                                    for i in range(len(current))])

        else:
            time, current, _, _ = loaded_data
            self[datakey] = Series([Episode(time, current[i], n_episode=i,
                                            sampling_rate = self.sampling_rate)
                                    for i in range(len(current))])

    def save_to_pickle(self, filepath):
        """
        save data using the pickle module
        useful for saving data that is to be used in ASCAM again
        """
        log.debug(f"save_to_pickle")
        if not filepath.endswith('.pkl'):
            filepath+='.pkl'
        with open(filepath, 'wb') as save_file:
            pickle.dump(self, save_file)
        return True

    def export_matlab(self, filepath, datakey, lists_to_save, save_piezo,
                      save_command):
        """Export all the episodes in the givens list(s) from the given series
        (only one) to a matlab file."""
        log.debug(f"export_matlab")
        if not filepath.endswith('.mat'):
            filepath+='.mat'
        # create dict to write matlab file and add the time vector
        export_dict = dict()
        export_dict['time'] = self['raw_'][0].time
        no_episodes = len(self[datakey])
        fill_length = len(str(no_episodes))

        #get the episodes we want to save
        indices = list()
        for listname in lists_to_save:
            indices.extend(self.lists[listname][0])
        indices = np.array(list(set(indices)))
        episodes = np.array(self[datakey])[indices]
        for episode in episodes:
            n = str(episode.n_episode).zfill(fill_length)
            export_dict['trace'+n] = episode._trace
            if save_piezo: export_dict['piezo'+n] = episode._piezo
            if save_command: export_dict['command'+n] = episode._command
        io.savemat(filepath, export_dict)

    def export_idealization(self, filepath):
        log.debug(f"export_idealization")
        if not filepath.endswith('.csv'):
            filepath+='.csv'
        export_array =  np.zeros(shape=(len(self.selected_episodes)+1,
                                        self.episode._idealization.size))
        export_array[0] = self.episode._time
        for k, episode in enumerate(self.selected_episodes):
            export_array[k+1] = episode._idealization
        #note that we transpose the export array to export the matrix
        #as time x episode
        np.savetxt(filepath, export_array.T, delimiter=',')

    def export_first_activation(self, filepath):
        log.debug(f"export_first_activation")
        if not filepath.endswith('.csv'):
            filepath+='.csv'
        export_array = np.array([(episode.n_episode, episode._first_activation)
                                for episode in self.selected_episodes])
        np.savetxt(filepath, export_array, delimiter=',')

    def baseline_correction(self, method='poly', poly_degree=1, intval=[],
                            select_intvl=False, piezo_diff=0.05,
                            select_piezo=True, active_piezo=False):
        log.debug(f"baseline_correction")
        # valid = self.check_operation('BC_')
        if self.currentDatakey=='raw_':
            #if its the first operation drop the 'raw_'
            newDatakey = 'BC_'
        else:
            #if operations have been done before combine the names
            newDatakey = self.currentDatakey+'BC_'
        log.info("""new datakey is {}""".format(newDatakey))
        self[newDatakey] = self[self.currentDatakey].baseline_correct_all(
                            intervals=intval, method=method, degree=poly_degree,
                            select_intvl=select_intvl,
                            select_piezo=select_piezo, active=active_piezo,
                            deviation=piezo_diff)
        self.currentDatakey = newDatakey
        log.debug("""keys of the recording are now {}""".format(self.keys()))
        return True

    def gauss_filter_series(self, filter_freq):
        """
        Filter the current series using a gaussian filter
        """
        log.debug(f"gaussian_filter")
        fdatakey = f'GFILTER{filter_freq}_'
        if self.currentDatakey == 'raw_':
            #if its the first operation drop the 'raw-'
            new_key = fdatakey
        else:
            #if operations have been done before combine the names
            new_key = self.currentDatakey+fdatakey
        self[new_key] = self[self.currentDatakey].gaussian_filter(filter_freq)
        self.currentDatakey = new_key
        return True

    def CK_filter_series(self, window_lengths, weight_exponent, weight_window,
				         apriori_f_weights=False, apriori_b_weights=False):
        """
        Filter the current series using the Chung-Kennedy filter banks
        """
        log.debug(f"CK_filter_series")
        n_filters = len(window_lengths)
        fdatakey = f'CKFILTER_K{n_filters}p{weight_exponent}M{weight_window}_'
        if self.currentDatakey == 'raw_':
            #if its the first operation drop the 'raw-'
            newDatakey = fdatakey
        else:
            #if operations have been done before combine the names
            newDatakey = self.currentDatakey+fdatakey
        self[newDatakey]\
        = self[self.currentDatakey].CK_filter(window_lengths, weight_exponent,
                            weight_window, apriori_f_weights, apriori_b_weights)
        self.currentDatakey = newDatakey
        return True

    def idealize_series(self):
        log.debug(f"idealize_series")
        self.series.idealize_all(self._TC_amplitudes, self._TC_thresholds)

    def idealize_episode(self):
        log.debug(f"idealize_episode")
        self.episode.idealize(self._TC_amplitudes, self._TC_thresholds)

    def detect_fa(self, exclude=[]):
        log.debug(f"detect_fa")
        [episode.detect_first_activation(self._fa_threshold)
         for episode in self.series if episode.n_episode not in exclude]

    def series_hist(self, active=True, select_piezo=True, deviation=0.05,
                    n_bins=50, density=False, intervals=False):
        log.debug(f"series_hist")
        piezos = [episode.piezo for episode in self.series]
        traces = [episode.trace for episode in self.series]
        trace_list = []
        #this is a failsafe, select_piezo should never be true is has_piezo
        #is false
        if not self.has_piezo:
            if select_piezo: log.debug((f"Tried piezo selection even though )",
                                        ",there is no piezo data!"))
            select_piezo = False
        if select_piezo:
            for piezo, trace in zip(piezos, traces):
                time, trace_points = piezo_selection(self.episode.time, piezo,
                                                     trace, active, deviation)
                trace_list.extend(trace_points)
            self.hist_times = np.array(time)
        elif intervals:
            for trace in traces:
                time, trace_points = interval_selection(self.episode.time,
                                        trace, intervals, self.sampling_rate)
                trace_list.extend(trace_points)
            self.hist_times = np.array(time)
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


    def episode_hist(self, active=True, select_piezo=True,
                  deviation=0.05, n_bins=50, density=False,
                  intervals=False):
        log.debug(f"episode_hist")
        if not self.has_piezo: select_piezo = False
        if select_piezo:
            time, trace_points = piezo_selection(self.episode.time,
                    self.episode.piezo, self.episode.trace, active, deviation)
            self.hist_times = np.array(time)

        elif intervals:
            time, trace_points = interval_selection(self.episode.time,
                    self.episode.trace, intervals, self.episode.sampling_rate)
            self.hist_times = np.array(time)
        else:
            trace_points = self.episode.trace
        heights, bins = np.histogram(trace_points, n_bins, density=density)
        # get centers of all the bins
        centers = (bins[:-1]+bins[1:])/2
        # get the width of a(ll) bin(s)
        width = (bins[1]-bins[0])
        self.histogram = heights, bins, centers, width
        return heights, bins, centers, width
