import logging as log

import numpy as np
import matplotlib.pyplot as plt

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
    log.debug(""" histogram will use {} bins
    normalize histogram to a density is {}
    the data are of type {},
    the data are {}
    """.format(n_bins,density,type(data),data))
    hist, bins = np.histogram(data, n_bins, density=density)
    log.debug("""`np.histogram` returned
                hist = {}
                bins={} """.format(hist,bins))
    return hist, bins

def histogram(time, piezos, traces, active = True, select_piezo=True,
              deviation=.05, n_bins = 200, density=False, time_unit ='ms',
              intervals=False, sampling_rate=None, **kwargs):
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
        select_piezo [boolean] - If true the points to be included in the
                                    histogram are selected based on the piezo
                                    voltage
        deviation [float] - Deviation, as a percentage, from the maximum
                            piezo voltage or threshold below which voltage
                            should be.
        density [boolean] - if true the histogram is scaled to sum to one
        n_bins [int] - number of bins to be used for the histogram
        time_unit [string] - unit of time in the interval specification
        intervals [list or list of of lists] - intervals from which to draw
        sampling_rate [float] - sampling rate of the data
        **kwargs - Keyword arguments for the `pyplot.bar` function.
    Returns:
        plot - Object containing the plot, can be shows by pyplot.`show()`
        time [1D array of floats] - The timestamps of the selected points.
        piezo_list [2D array of floats] - Each row contains the piezo values
                                         at the selected times for an episode.
        trace_list [2D array of floats] - Each row contains the current values
                                         at the selected times for an episode.
    """
    log.debug("""`histogram` called with parameters:
                time: {}
                piezos: {}
                traces: {}
                active: {}, select_piezo:{}, deviation: {}
                n_bins: {}, density:{}, time_unit: {}, sampling_rate: {}
                intervals: {}
                and kwargs: {}
                """.format(time,piezos,traces,active,select_piezo,deviation,
                      n_bins,density,time_unit,sampling_rate,intervals,kwargs))
    trace_list = []
    if select_piezo:
        for piezo, trace in zip(piezos, traces):
            _, _, trace_points = piezo_selection(time, piezo, trace, active,
                                                 deviation)
            trace_list.extend(trace_points)
    elif intervals:
        for trace in traces:
            _, trace_points = interval_selection(time, trace, intervals,
                                                 sampling_rate, time_unit)
            trace_list.extend(trace_points)
    else:
        trace_list = traces

    trace_list = np.asarray(trace_list)
    hist, bins = create_histogram(trace_list, n_bins, density)
    # get centers of all the bins
    centers = (bins[:-1]+bins[1:])/2
    # get the width of a(ll) bin(s)
    width = (bins[1]-bins[0])
    log.debug("""return width: {}, centers: {}""".format(width,centers))
    return hist, bins, centers, width

def plot_histogram(fig, pgs, episode, series, n_bins=50, density=False, select_piezo=False,
                   active=True, deviation=0.05, fs=4e4, intervals=[], single_hist=True,
                   indices=[], allpoint_hist=True, current_unit='A', axis=None, episode_inds = [],
                   **kwargs):
    """
    this method will draw the histogram next to the current trace
    """
    log.info("drawing histogram")
    log.debug("""number of bins = {}
        density = {}
        select_piezo = {}
        active = {}
        deviation = {}""".format(n_bins,density,select_piezo,
                                 active,deviation))
    # create the plot object so we can delete it later
    ax = fig.add_subplot(pgs[:,2])
    #move the axis label and ticks to the right so they dont lie over
    #the other plots
    ax.yaxis.set_label_position('right')
    ax.yaxis.tick_right()
    # get data
    time = episode.time
    # get current episode values and put them in a list
    # because the histogram function expects a list
    single_piezo = [episode.piezo]
    single_trace = [episode.trace]
    # get the bins and their values or the current episode
    hist_single = histogram(time, single_piezo, single_trace,
                                     active=active, n_bins=n_bins,
                                     select_piezo=select_piezo,
                                     deviation=deviation,
                                     density=density, sampling_rate=fs,
                                     intervals=intervals, **kwargs)
    heights_single, bins_single, center_single, width_single\
    = hist_single
    if allpoint_hist:
        log.info("""will create allpoint histogram""")
        # get a list of all the currents and all the traces
        if episode_inds.size==0: episode_inds = list(range(len(series)))
        all_piezos = [episode.piezo for episode in series if episode.n_episode in episode_inds]
        all_traces = [episode.trace for episode in series if episode.n_episode in episode_inds]

        # get the bins and their values for all episodes
        hist_all = histogram(time, all_piezos, all_traces,
                                      active=active, n_bins=n_bins,
                                      select_piezo=select_piezo,
                                      deviation=deviation,
                                      density=density, sampling_rate=fs,
                                      intervals=intervals, **kwargs)
        heights_all, bins_all, center_all, width_all = hist_all
        # draw bar graphs of the histogram values over all episodes
        ax.barh(center_all, heights_all, width_all,
                alpha=0.2, color='orange', align='center')
        ax.plot(heights_all, center_all, color='orange', lw=2)
        ax.set_ylabel(f"Current [{current_unit}")
        if density:
            log.info('setting y-label "Relative frequency"')
            ax.set_xlabel("Relative frequency")
        else:
            log.info('setting y-label "Count"')
            ax.set_xlabel("Count")

    # histogram of single episode
    if single_hist:
        log.info("plotting single episode histogram")
        ax.barh(center_single, heights_single, width_single,
                align='center', alpha=1)
    # cursor = PlotCursor(ax, useblit=True, color='black', linewidth=1)

def plotTrace(ax, time, trace, ylabel, ybounds=[]):
    """
    ybounds [tuple or list] (y_min, y_max)
    ax = matplotlib axes object
    """
    ax.plot(time,trace)
    ax.set_ylabel(ylabel)
    if ybounds:
        ax.set_ylim(ybounds)
    pass

def plot_traces(fig, pgs, episode, show_piezo=True, show_command=True,
                t_zero=0, piezo_unit='V', current_unit='A',
                command_unit='V', time_unit='s'):
    """
    This method plots the current, piezo and command voltage traces
    """
    time = episode.time-t_zero
    subplots = list()
    # plot command voltage
    if show_command:
        log.info('will plot command voltage')
        # always plot command voltage on bottom (-1 row)
        command_plot = fig.add_subplot(pgs[-1,:2])
        plotTrace(ax=command_plot, time=time,
                           trace=episode.command,
                           ylabel=f"Command [{command_unit}]")
        command_plot.set_xlabel(f"Time [{time_unit}]")
        if t_zero!=0: plt.axvline(0, c='r', lw=1, ls='--', alpha=.8)
        subplots.append(command_plot)

    #if piezo will be plotted current plot show be in row 1 else in row 0
    trace_pos = 1 if show_piezo else 0
    #sharex with command if its own
    x_share = command_plot if show_command else None
    # plot the current trace
    current_plot = fig.add_subplot(pgs[trace_pos:trace_pos+2,:2], sharex=x_share)
    plotTrace(ax=current_plot, time=time, trace=episode.trace,
                       ylabel=f"Current [{current_unit}]")
    # label only the last axis
    if show_command: current_plot.set_xticklabels([])
    else: current_plot.set_xlabel(f"Time [{time_unit}]")
    if t_zero!=0: plt.axvline(0, c='r', lw=1, ls='--', alpha=.8)
    subplots.append(current_plot)
    #sharex with current or command voltage
    x_share = command_plot if show_command else current_plot
    # plot the piezo
    if show_piezo:
        log.info('will plot piezo voltage')
        #always plots piezo voltage on top
        piezo_plot = fig.add_subplot(pgs[0,:2], sharex=x_share)
        plotTrace(ax=piezo_plot, time=time, trace=episode.piezo,
                           ylabel=f"Piezo [{piezo_unit}]")
        piezo_plot.set_xticklabels([])
        if t_zero!=0: plt.axvline(0, c='r', lw=1, ls='--', alpha=.8)
        subplots.append(piezo_plot)
    return subplots
