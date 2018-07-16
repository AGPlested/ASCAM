import os
import logging as log
import pickle

from scipy import io

import readdata
import savedata
from tools import parse_filename
from episode import Episode
from series import Series

class Recording(dict):
    def __init__(self, filename='', sampling_rate=0, filetype='',
                 headerlength=0, dtype=None, time_unit='ms', piezoUnit='V',
                 commandUnit='V', currentUnit='A'):
        log.info("""intializing Recording""")

        # parameters for loading the data
        self.filename = filename
        self.filetype = filetype
        self.headerlength = int(float(headerlength))
        self.dtype = dtype

        # attributes of the data
        self.sampling_rate = int(float(sampling_rate))
        self.time_unit = time_unit
        self.commandUnit = commandUnit
        self.currentUnit = currentUnit
        self.piezoUnit = piezoUnit

        # attributes for storing and managing the data
        self['raw_'] = Series()
        self.currentDatakey = 'raw_'
        self.currentEpisode = 0

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

        #if the lists attribute has not been set while loading the data do it now
        if not self.lists:
            self.lists = {'all':(list(range(len(self['raw_']))), 'white', None)}

    def load_data(self):
        """
        this method is supposed to load data from a file or a directory
        """
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

    def load_series(self, filename, filetype, dtype, headerlength,
                    sampling_rate, datakey):
        """
        Load the data in the file at `self.filename`.
        Accepts `.mat`, `.axgd` and `.bin` files.
        (`.bin` files are for simulated data only at the moment.)
        """
        names, *loaded_data = readdata.load(filename = filename,
                                            filetype = filetype,
                                            dtype = dtype,
                                            headerlength = headerlength,
                                            fs = sampling_rate)
        ### The `if` accounts for the presence or absence of
        ### piezo and command voltage in the data being loaded

        if 'Piezo [V]' in names and 'Command Voltage [V]' in names:
            time = loaded_data[0]
            self[datakey] = Series([Episode(time, trace, n_episode=i,
                                            piezo=pTrace,
                                            command=cVtrace,
                                            sampling_rate = self.sampling_rate)
                                    for i, (trace, pTrace, cVtrace)
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
        if not filepath.endswith('.pkl'):
            filepath+='.pkl'
        with open(filepath, 'wb') as save_file:
            pickle.dump(self, save_file)
        return True

    def export_matlab(self, filepath, datakey, lists, save_piezo, save_command):
        """Export all the episodes in the givens list(s) from the given series
        (only one) to a matlab file."""
        if not filepath.endswith('.mat'):
            filepath+='.mat'

        list_exports = list()
        # combine the episode numbers to be saved in one list
        for list_name in lists:
            list_exports.extend(self.lists[list_name][0])
        # filter out duplicate elements
        list_exports = list(set(list_exports))

        # create dict to write matlab file and add the time vector
        export_dict = dict()
        export_dict['time'] = self['raw_'][0].time
        no_episodes = len(self[datakey])
        fill_length = len(str(no_episodes))
        for i, episode in enumerate(self[datakey]):
            if i in list_exports:
                n = str(episode.n_episode).zfill(fill_length)
                export_dict['trace'+n] = episode.trace
                if save_piezo: export_dict['piezo'+n] = episode.piezo
                if save_command: export_dict['command'+n] = episode.command
        io.savemat(filepath,export_dict)

    def baseline_correction(self, method='poly', poly_degree=1, intval=[],
                            time_unit='ms', select_intvl=False,
                            select_piezo=True, active_piezo=False,
                            piezo_diff=0.05):
        log.info("""calling baseline_correction""")
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
                            time_unit=time_unit, select_intvl=select_intvl,
                            select_piezo=select_piezo, active=active_piezo,
                            deviation=piezo_diff)
        self.currentDatakey = newDatakey
        log.debug("""keys of the recording are now {}""".format(self.keys()))
        return True

    def gauss_filter_series(self, filter_freq):
        """
        Filter the current series using a gaussian filter
        """
        if self.currentDatakey == 'raw_':
            #if its the first operation drop the 'raw-'
            newDatakey = 'GFILTER'+str(filter_freq)+'_'
        else:
            #if operations have been done before combine the names
            newDatakey = self.currentDatakey+'GFILTER'+str(filter_freq)+'_'
        self[newDatakey] = self[self.currentDatakey].gauss_filter(filter_freq)
        self.currentDatakey = newDatakey
        return True

    def filter_series_CK(self, *args, **kwargs):
        """ DOES NOTHING
        Filter the current series using the Chung-Kennedy filter banks
        """
        # if self.currentDatakey == 'raw_':
        #     #if its the first operation drop the 'raw-'
        #     newDatakey = 'CKFILTER_'
        # else:
        #     #if operations have been done before combine the names
        #     newDatakey = self.currentDatakey+'CKFILTER_'
        # self[newDatakey] = self[self.currentDatakey].CK_filter(*args, **kwargs)
        # self.currentDatakey = newDatakey
        return True

    def idealize_series(self, thresholds):
        """
        DOES NOTHING
        """
        # if self.currentDatakey == 'raw_':
        #     #if its the first operation drop the 'raw-'
        #     newDatakey = 'TC_'
        # else:
        #     #if operations have been done before combine the names
        #     newDatakey = self.currentDatakey+'TC_'
        # self[newDatakey] = self[self.currentDatakey].idealize_all(thresholds)
        # self.currentDatakey = newDatakey
        return True
