import os

import numpy as np

from ascam.constants import PRECISIONS

def parse_filename(filename):
    """
    detect the type of file from the extension
    works by walking through the filename in reverse order and considering
    the filetype to be whatever comes before the first '.' it encounters
    """
    if not filename:
        raise Exception("Cannot parse empty filename")
    N = len(filename)
    period = False
    slash = False
    for i, char in enumerate(filename[::-1]):
        # loop over the full filename (which includes directory) backwards
        # to extract the extension and name of the file
        if (char == ".") and not period:
            period = N - 1 - i
        if (char == "/") and not slash:
            slash = N - 1 - i
            break
    path = filename[:slash]
    filetype = filename[period + 1 :]
    if "axg" in filetype:
        filetype_long = "axograph"
    elif filetype == "bin":
        filetype_long = "binary"
    elif filetype == "mat":
        filetype_long = "matlab"
    elif filetype == "pkl":
        filetype_long = "pickle"
    elif filetype in ("txt", "axgt"):
        filetype = "tdt"
        filetype_long = "tab-delimited-text"
    filename = filename[slash + 1 :]
    return filetype, path, filetype_long, filename


def piezo_selection(time, piezo, trace, active=True, deviation=0.05):
    """
    Selects part of the episode based on the Piezo voltage.
    The selection is done by choosing extracting the data from those time
    points where the value of the piezo voltage is either within a certain
    range (percentage wise) of the maximum or below a certain percentage
    of the maximum.
    Works in relative terms, i.e. it does not matter if piezo voltage is
    positive or negative. Only works for blocks of the same amplitude.
    Parameters:
        time [1D array of floats] - Vector containing the time points.
        piezo [1D array of floats] - Vector of piezo voltages.
        trace [1D array of floats] - Vector of current trace.
        active [boolean] - If true return time points at which piezo
                           voltage is within `deviation` percent of the
                           maximum piezo voltage.
        deviation [float] - Deviation, as a percentage, from the maximum
                            piezo voltage or threshold below which voltage
                            should be.
    Returns:
        time [1D array of floats] - The timestamps of the selected points.
        piezo [1D array of floats] - The piezo voltage at selected points.
        trace [1D array of floats] - The current at selected points.
    """
    maxPiezo = np.max(np.abs(piezo))
    if active:
        indices = np.where((maxPiezo - np.abs(piezo)) / maxPiezo < deviation)
    else:
        indices = np.where(np.abs(piezo) / maxPiezo < deviation)
    time = time[indices]
    piezo = piezo[indices]
    trace = trace[indices]
    return time, trace


def interval_selection(time, signal, intervals, fs):
    """
    return the signal at the times specified in the interval
    the function assumes `time` and `intervals` to have the same units and
    fs to have the reciprocal unit (eg. s, s and hz)
    """
    time_out = []
    signal_out = []
    if isinstance(intervals[0], list):
        for ival in intervals:
            time_out.extend(time[int(ival[0] * fs) : int(ival[-1] * fs)])
            signal_out.extend(signal[int(ival[0] * fs) : int(ival[-1] * fs)])
    elif isinstance(intervals[0], (float, int)):
        time_out = time[int(intervals[0] * fs) : int(intervals[-1] * fs)]
        signal_out = signal[int(intervals[0] * fs) : int(intervals[1] * fs)]
    return time_out, signal_out


def update_number_in_string(new_val, string):
    """Update a list of floats held in a qt widget that can
    hold text so that the value closest to new_val becomes new_val."""
    array = string_to_array(string)
    differences = np.abs(array - new_val)
    i = np.argmin(differences)
    sep = ", " if "," in string else " "
    split_string = string.split(sep)
    split_string[i] = f"{new_val:.2f}"
    return sep.join(split_string)


def string_to_list(list_as_string):
    """
    Parse a string that is an interval or list of intervals (e.g. "[0,5]" or
    "[[0,4],[5,8]]") and returns it as a list
    Parameters:
        list_as_string (string)
    Returns:
        whole_list (list of lists of integers)
    """
    whole_list = []
    current_list = []
    num_string = ""
    for char in list_as_string:
        if char == "[":
            current_list = []
        elif char == ",":
            if len(current_list) == 0:
                current_list.append(float(num_string))
            num_string = ""
        elif char == "]":
            current_list.append(float(num_string))
            whole_list.append(current_list)
        else:
            num_string += char
    return whole_list


def string_to_array(string):
    if "," in string:
        array = np.array(string.split(","), dtype=np.float)
    else:
        array = np.array(string.split(), dtype=np.float)
    return array


def array_to_string(array, seperator=" "):
    return seperator.join(np.char.mod("%.2f", array))


def clear_qt_layout(layout):
    if layout is not None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                clear_qt_layout(child.layout())

def round_off_tables(dataframe, column_units):
    for i, unit in enumerate(column_units):
        dataframe.iloc[:, i] = dataframe.iloc[:, i].map(lambda x: f"{x:.{PRECISIONS[unit]}f}")
    return dataframe    
