import numpy as np 
import matplotlib.pyplot as plt

def piezo_selection(time, piezo, trace, active = True, deviation = 0.05):
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
        indices = np.where((maxPiezo-np.abs(piezo))/maxPiezo<deviation)
    else:
        indices = np.where(np.abs(piezo)/maxPiezo<deviation)
    time = time[indices]
    piezo = piezo[indices]
    trace = trace[indices] 
    return time, piezo, trace

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
    hist, bins = np.histogram(data, n_bins, density=density)
    return hist, bins

def histogram(time, piezos, traces, active = True, deviation=.05, n_bins = 200, 
              density=False, **kwargs):
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
        deviation [float] - Deviation, as a percentage, from the maximum
                            piezo voltage or threshold below which voltage
                            should be.
        density [boolean] - if true the histogram is scaled to sum to one
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
    piezo_list = []
    for p, t in zip(piezos, traces):
        time_selection, piezo, trace = piezo_selection(time, p, t, active, 
                                                        deviation)
        piezo_list.append(piezo)
        trace_list.append(trace)
    trace_list = np.asarray(trace_list)
    piezo_list = np.asarray(piezo_list)
    hist, bins = create_histogram(trace_list, n_bins, density)
    center = (bins[:-1] + bins[1:]) / 2
    width = (bins[1] - bins[0])
    # plot = plt.bar(center, hist, width=width, **kwargs)
    return hist, bins, center, width