import readdata
import savedata
import os
from tools import parse_filename
from episode import Episode
from series import Series
import pickle
from scipy import io
import logging as log

class Recording(dict):
    def __init__(self, filename = '',
                 sampling_rate = 0, filetype = '', headerlength = 0,
                 dtype = None, timeUnit = 'ms', piezoUnit = 'V',
                 commandUnit = 'V', currentUnit = 'A'):
        log.info("""intializing Recording""")

        # parameters for loading the data
        self.filename = filename
        self.filetype = filetype
        self.headerlength = int(float(headerlength))
        self.dtype = dtype

        # attributes of the data
        self.sampling_rate = int(float(sampling_rate))
        self.timeUnit = timeUnit
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

    def export_matlab(self,filepath,datakey,lists,save_piezo,save_command):
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
        export_dict['time'] = self['raw_'][0]['time']
        no_episodes = len(self[datakey])
        fill_length = len(str(no_episodes))
        for i, episode in enumerate(self[datakey]):
            if i in list_exports:
                for name, value in episode.items():
                    # the if statements skip the items that do not need to be
                    # saved
                    if name == 'time':
                        continue
                    elif name == 'piezo' and not save_piezo:
                        continue
                    elif name == 'command' and not save_command:
                        continue
                    else:
                    # add data to dictionary
                        n = str(episode.n_episode)
                        n = n.zfill(fill_length)
                        export_dict[name+n] = value
        io.savemat(filepath,export_dict)


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
            # create new datakey
            if self.currentDatakey == 'raw_':
                #if its the first operation drop the 'raw-'
                newDatakey = operation+str(*args)+'_'
            else:
                #if operations have been done before combine the names
                newDatakey = self.currentDatakey+operation+str(*args)+'_'

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
