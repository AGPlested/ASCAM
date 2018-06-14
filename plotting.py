import numpy as np
import matplotlib.pyplot as plt
import logging as log
from tools import piezo_selection, interval_selection

def create_histogram(data, n_bins, density=False):
    """
    Create a histogram of the values in `traces`. Keyword arguments for
    `np.histogram` can be given as kwargs here.
    Parameters:
        traces [numpy array] - Array containing all the values for the
                               histogram.
        **kwargs - Keyword arguments for the `numpy.histogram` function
    """
    data = data.flatten()
    log.info("called 'create_histogram'")
    log.debug(""" histogram will use {} bins\n
    normalize histogram to a density is {}\n
    the data are of type {},
    the data are {}
    """.format(n_bins,density,type(data),data))
    hist, bins = np.histogram(data, n_bins, density=density)
    log.debug("""`np.histogram` returned
                \n hist = {}
                \n bins={} """.format(hist,bins))
    return hist, bins

def histogram(time, piezos, traces, active = True, piezoSelection=True,
              deviation=.05, n_bins = 200, density=False, timeUnit ='ms',
              intervals=False, samplingRate=None, **kwargs):
    """
    Creates an all-point-histogram of selected values in trace. The values
    are selected based on whether or not the piezo device is active.
    Parameters:
        time [1D array of floats] - Vector containing the time points.
        piezo [array of floats] - Vector of piezo voltages.
        trace [array of floats] - Vector of current trace.
        active [boolean] - If true return time points at which piezo
                           voltage is within `deviation` percent of the
                           maximum piezo voltage.
        piezoSelection [boolean] - If true the points to be included in the
                                    histogram are selected based on the piezo
                                    voltage
        deviation [float] - Deviation, as a percentage, from the maximum
                            piezo voltage or threshold below which voltage
                            should be.
        density [boolean] - if true the histogram is scaled to sum to one
        n_bins [int] - number of bins to be used for the histogram
        timeUnit [string] - unit of time in the interval specification
        intervals [list or list of of lists] - intervals from which to draw
        samplingRate [float] - sampling rate of the data
        **kwargs - Keyword arguments for the `pyplot.bar` function.
    Returns:
        plot - Object containing the plot, can be shows by pyplot.`show()`
        time [1D array of floats] - The timestamps of the selected points.
        piezo_list [2D array of floats] - Each row contains the piezo values
                                         at the selected times for an episode.
        trace_list [2D array of floats] - Each row contains the current values
                                         at the selected times for an episode.
    """
    trace_list = []
    if piezoSelection:
        for piezo, trace in zip(piezos, traces):
            _, _, trace_points = piezo_selection(time, piezo, trace, active,
                                                 deviation)
            trace_list.extend(trace_points)
    elif intervals:
        for trace in traces:
            _, trace_points = interval_selection(time, trace, intervals,
                                                 samplingRate, timeUnit)
            trace_list.extend(trace_points)
    else:
        trace_list = traces

    trace_list = np.asarray(trace_list)
    hist, bins = create_histogram(trace_list, n_bins, density)
    # get centers of all the bins
    centers = (bins[:-1] + bins[1:]) / 2
    # get the width of a(ll) bin(s)
    width = (bins[1] - bins[0])
    return hist, bins, centers, width

def plotTrace(ax, time, trace, ylabel, ybounds = []):
    """
    ybounds [tuple or list] (y_min, y_max)
    ax = matplotlib axes object
    """

    ax.plot(time,trace)
    ax.set_ylabel(ylabel)
    if ybounds:
        ax.set_ylim(ybounds)
    pass
