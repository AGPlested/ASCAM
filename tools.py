import logging as log

import numpy as np
import matplotlib
#check mpl version because navigation toolbar name has changed
mpl_ver = (matplotlib.__version__).split('.')
if int(mpl_ver[0])<2 or int(mpl_ver[1])<2 or int(mpl_ver[2])<2:
    from matplotlib.backends.backend_tkagg \
    import NavigationToolbar2TkAgg as NavigationToolbar2Tk
else: from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

def parse_filename(filename):
    """
    detect the type of file from the extension
    works by walking through the filename in reverse order and considering
    the filetype to be whatever comes before the first '.' it encounters
    """
    log.info("""called `parse_filename` on: {}""".format(filename))
    N = len(filename)
    period = False
    slash = False
    for i, char in enumerate(filename[::-1]):
        # loop over the full filename (which includes directory) backwards
        # to extract the extension and name of the file
        if (char == '.') and not period:
            period = N-1-i
        if (char == '/') and not slash:
            slash = N-1-i
            break
    path = filename[:slash]
    filetype = filename[period+1:]
    log.debug("""filename length: {}
                period (.) at position: {}
                slash (/) at position: {}
                path: {}
                filetype: {}""".format(N, period, slash, path, filetype))
    if filetype == 'axgd':
        filetype = 'axo'
        filetype_long = 'axograph'
    elif filetype == 'bin': filetype_long = 'binary'
    elif filetype == 'mat': filetype_long = 'matlab'
    elif filetype == 'pkl': filetype_long = 'pickle'
    elif filetype == 'txt' or filetype == 'axgt':
        filetype = 'tdt'
        filetype_long = 'tab-delimited-text'
    else: log.warning("Could not detect filetype!")
    filename = filename[slash+1:]
    log.debug("""filetype_long : {}"
               filename: {} """.format(filetype_long,filename))
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
    # log.debug("""called `select_piezo` with parameters:
    #           active = {}, deviation = {}, maxPiezo = {}
    #           time: {}
    #           piezo: {}
    #           trace: {}
    #           """.format(active,deviation,maxPiezo,time,piezo,trace))
    if active:
        # log.debug("""selecting for active piezo""")
        indices = np.where((maxPiezo-np.abs(piezo))/maxPiezo<deviation)
    else:
        # log.debug("""selecting for inactive piezo""")
        indices = np.where(np.abs(piezo)/maxPiezo<deviation)
    time = time[indices]
    piezo = piezo[indices]
    trace = trace[indices]
    # log.debug("""found indices: {}
    #           times: {}
    #           piezo: {}
    #           trace: {}""".format(indices, time, piezo, trace))
    return time, piezo, trace

def interval_selection(time, signal, intervals, fs, time_unit):
    """
    return the signal at the times specified in the interval
    """
    log.info("""called `interval_selection`""")
    # log.debug("""parameters are: sampling frequency: {}, time_unit: {}
    #           time: {}
    #           signal: {}
    #           intervals: {}""".format(fs, time_unit, time, signal, intervals))
    if time_unit == 'ms':
        time_unit = 1000
    elif time_unit == 's':
        time_unit = 1
    time_out = []
    signal_out = []
    if type(intervals[0]) is list:
        log.debug("""`intervals` is a list of intervals""")
        for ival in intervals:
            time_out.extend(time[ int(ival[0]*fs/time_unit)
                            : int(ival[-1]*fs/time_unit) ])
            signal_out.extend(signal[ int(ival[0]*fs/time_unit)
                              : int(ival[-1]*fs/time_unit)])
    elif type(intervals[0]) in [int, float]:
        log.debug("""`intervals` is just one interval""")
        time_out = time[ int(intervals[0]*fs/time_unit)
                   : int(intervals[-1]*fs/time_unit)]
        signal_out = signal[int(intervals[0]*fs/time_unit)
                   : int(intervals[1]*fs/time_unit)]
    # log.debug("""selected times: {}
    #              and signal: {}""".format(time_out,signal_out))
    return time_out, signal_out

def stringList_parser(list_as_string):
    """
    Parse a string that is an interval or list of intervals (e.g. "[0,5]" or
    "[[0,4],[5,8]]") and returns it as a list
    Parameters:
        list_as_string (string)
    Returns:
        whole_list (list of lists of integers)
    """
    log.info("""called `stringList_parser`""")
    whole_list = []
    current_list = []
    num_string = ''
    for char in list_as_string:
        if char == '[':
            current_list = []
        elif char == ',':
            if len(current_list) == 0:
                current_list.append(float(num_string))
            num_string = ''
        elif char == ']':
            current_list.append(float(num_string))
            whole_list.append(current_list)
        else:
            num_string += char
    # log.debug("""string was: {}
    #          returning: {}""".format(list_as_string,whole_list))
    return whole_list

class PlotToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, parent):
        self.parent = parent #parent is PlotFrame
        self.canvas = canvas

        # this toolbar is just the standard with fewer buttons
        self.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            # ('Back', 'Back to  previous view', 'back', 'back'),
            # ('Forward', 'Forward to next view', 'forward', 'forward'),
            (None, None, None, None),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
            (None, None, None, None),
            # ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
            ('Save', 'Save the figure', 'filesave', 'save_figure'),
            )
        NavigationToolbar2Tk.__init__(self, canvas, parent)

    def zoom(self):
        """
        Redefine the zoom method of the toolbar to include zooming out on
        right-click
        """
        # self.parent.parent.tc_frame.track_on = False
        self_zoom_out_cid = self.canvas.mpl_connect('button_press_event', self.zoom_out)
        NavigationToolbar2Tk.zoom(self)

    def zoom_out(self, event):
        """
        Zoom out in this case is done by calling `back` on right-click to
        restore the previous view (i.e. undo last zoom)
        """
        if self._active=='ZOOM' and event.button==3:
            NavigationToolbar2Tk.back(self)
