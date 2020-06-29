import csv
import pickle
import logging

import numpy as np
import axographio
from scipy.io import loadmat as scipy_loadmat
from scipy.io.matlab.mio5 import varmats_from_mat


from ..utils.tools import parse_filename


def load(filename, filetype=False, dtype=None, headerlength=None, fs=None):
    """
    get data form a file
    if filetype is not given automatically detects it from the
    extension
    """
    if not filetype:
        # the first value returned by parse_filename is the filetype
        filetype = parse_filename(filename)[0]

    if filetype == "axo":
        output = load_axo(filename)
    elif filetype == "mat":
        output = load_matlab(filename)
    elif filetype == "bin":
        output = load_binary(filename, dtype, headerlength, fs)
    elif filetype == "tdt":
        output = load_tdt(filename)
    else:
        print("Filetype not supported.")
        output = False
    return output


def load_pickle(filename):
    """
    read a recording object from a pickle file
    """
    logging.info("""reading pickle""")
    with open(filename, "rb") as file:
        data = pickle.load(file)
    return data


def load_matlab(filename):
    """
    Uses `scipy.io.loadmat` to load data from a `.mat` file.
    Input:
        filename [string] - name (including location) of the file to be loaded
    Output:
        names [list of strings] - names of the different variables
        time [1D numpy array] - times of measurement
        current [list of 1D numpy arrays] - the current recorded from the patch
        piezo [list of 1D numpy arrays] - voltage of the piezo pipette
        command_voltage [list of 1D numpy arrays] - command voltage applied to
                                                    the patch
    Because the data we have comes with strange dictionary keys (i.e.
    including column numbers and hex values) the function loops over the keys
    to extract current, command voltatge, piezo voltage and time.
    """
    current = []
    command_voltage = []
    piezo = []
    names = ["Time [ms]"]
    ep_numbers = []

    # we use varmats to split up the file into seperate mat files, one for
    # each variable this is necessary for files containing a lot of data
    # (i.e. more that 1000 episode) because the variable names are 3-digit
    # column numbers (so they loop back around after 1000))
    varmats = varmats_from_mat(open(filename, "rb"))

    for variable in varmats:
        value = scipy_loadmat(variable[1])[variable[0]]
        # the first possibility is the name in files we get, the second
        # comes from the ASCAM data structure
        if "Ipatch" in variable[0] or "Column" in variable[0]:
            current.append(value.flatten())
            try:
                ep_numbers.append(int(variable[0].split()[-1]))
            except (IndexError, ValueError):
                pass
        if "trace" in variable[0]:
            current.append(value.flatten())
            try:
                ep_numbers.append(int(variable[0].split()[-1]))
            except (IndexError, ValueError):
                pass
        elif "10Vm" in variable[0] or "command" in variable[0]:
            command_voltage.append(value.flatten())
        elif "Piezo" in variable[0] or "piezo" in variable[0]:
            piezo.append(value.flatten())
        elif "Time" in variable[0] or "time" in variable[0]:
            time = value.flatten()
    if current:
        names.append("Current [A]")
    if piezo:
        names.append("Piezo [V]")
    if command_voltage:
        names.append("Command Voltage [V]")
    return names, time, current, piezo, command_voltage, ep_numbers


def load_binary(filename, dtype, headerlength, fs):
    """
    Loads data from binary file using the numpy function fromfile,
    it assumes that the words in the header are of the
    same bit-length as the numbers in the file and removes
    the header
    Input:
        filename - string
        dtype - should be a numpy dtype duch as 'np.int16' but
                without(!) quotes
        header_length - number of words in header (same bitlength as
                        data)
    Output:
        data - 1 x #(samples) numpy array containing the data
    """
    headerlength = int(headerlength)
    current = np.fromfile(filename, dtype=dtype)
    current = current[headerlength:]
    t_end = len(current) / fs * 1000
    time = np.linspace(0, t_end, len(current))
    names = ["Time [ms]", "Current [A]"]
    current = current[np.newaxis]
    piezo = command_voltage = []
    return names, time, current, piezo, command_voltage


def load_axo(filename):
    """Load data from axograph files using the axographio library.

    Arguments:
        filename - string containing the path to the datafile
    Return:
        time [1D numpy array] - times of measurement
        current [list of 1D numpy arrays] - the current recorded from the patch
        piezo [list of 1D numpy arrays] - voltage of the piezo pipette
        command_voltage [list of 1D numpy arrays] - command voltage applied to
                                                    the patch"""

    file = axographio.read(filename)
    current = []
    command_voltage = []
    piezo = []
    ep_numbers = []

    for name, data in zip(file.names, file.data):
        if "Ipatch" in name :
            current.append(np.array(data))
            try:
                ep_numbers.append(int(name.split()[-1]))
            except (IndexError, ValueError):
                pass
        elif "trace" in name:
            current.append(np.array(data))
            try:
                ep_numbers.append(int(name.split()[-1]))
            except (IndexError, ValueError):
                pass
        elif "10Vm" in name or "command" in name:
            command_voltage.append(np.array(data))
        elif "Piezo" in name or "piezo" in name:
            piezo.append(np.array(data))
        elif "Time" in name or "time" in name:
            time = np.array(data)

    return file.names, time, current, piezo, command_voltage, ep_numbers


# unused method to read tab delimited text
# def load_tdt(filename):
#     """
#     Load data from a tab-delimited text file
#     the file must have the data stored in columns with the first line
#     containing the names of each column
#     Input:
#         filename [string] - name (including location) of the file to be loaded
#     Output:
#         names [list of strings] - names of the different variables
#         time [1D numpy array] - times of measurement
#         current [list of 1D numpy arrays] - the current recorded from the patch
#         piezo [list of 1D numpy arrays] - voltage of the piezo pipette
#         command_voltage [list of 1D numpy arrays] - command voltage applied to
#                                                     the patch
#     """
#     current = []
#     command_voltage = []
#     piezo = []

#     with open(filename) as datafile:
#         datafile = open(filename)
#         reader = csv.reader(datafile, delimiter="\t")
#         names = next(reader)
#         n_lists = len(names)

#         # create a 'list-array' to hold the data, we need to create a list for
#         # each timeseries we get before populating them
#         # and they need to be lists because the length is unknown
#         listlist = list()
#         for i in range(n_lists):
#             listlist.append(list())

#         # sort the data from the csv reader into the seperate lists
#         for line in reader:
#             for i in range(n_lists):
#                 listlist[i].append(line[i])

#         # assign the lists with data
#         for i in range(n_lists):
#             if "Ipatch" in names[i] or "trace" in names[i]:
#                 current.append(np.array(listlist[i], dtype=np.float))
#             elif "10Vm" in names[i] or "command" in names[i]:
#                 command_voltage.append(np.array(listlist[i], dtype=np.float))
#             elif "Piezo" in names[i] or "piezo" in names[i]:
#                 piezo.append(np.array(listlist[i], dtype=np.float))
#             elif "Time" in names[i] or "time" in names[i]:
#                 time = np.array(listlist[i], dtype=np.float)

#     names = ["Time [ms]"]
#     if current:
#         names.append("Current [A]")
#     if piezo:
#         names.append("Piezo [V]")
#     if command_voltage:
#         names.append("Command Voltage [V]")
#     return names, time, current, piezo, command_voltage

