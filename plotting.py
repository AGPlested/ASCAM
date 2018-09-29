import logging as log

import numpy as np
import matplotlib.pyplot as plt

from tools import piezo_selection, interval_selection


def histogram(time, piezos, traces, active = True, select_piezo=True,
              deviation=.05, n_bins = 200, density=False, time_unit ='ms',
              intervals=False, sampling_rate=None, **kwargs):
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

    trace_list = trace_list.flatten()
    hist, bins = np.histogram(trace_list, n_bins, density=density)

    # get centers of all the bins
    centers = (bins[:-1]+bins[1:])/2
    # get the width of a(ll) bin(s)
    width = (bins[1]-bins[0])
    # log.debug("""return width: {}, centers: {}""".format(width,centers))
    return hist, bins, centers, width

def plot_histogram(fig, pgs, episode, series, n_bins=50, density=False, select_piezo=False,
                   active=True, deviation=0.05, fs=4e4, intervals=[], single_hist=True,
                   indices=[], allpoint_hist=True, current_unit='A', axis=None, episode_inds = [],
                   **kwargs):   
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
    return ax, hist_all

def plot_traces(fig, pgs, episode, show_piezo=True, show_command=True,
                t_zero=0, piezo_unit='V', current_unit='A',
                command_unit='V', time_unit='s', show_idealization=True):
    """
    This method plots the current, piezo and command voltage traces
    """
    time = episode.time-t_zero
    subplots = list()
    x_share = None
    # plot command voltage
    if show_command and type(episode.command) is np.ndarray:
        log.info('will plot command voltage')
        # always plot command voltage on bottom (-1 row)
        command_plot = fig.add_subplot(pgs[-1,:2])
        cm_line, = command_plot.plot(time, episode.command)
        command_plot.set_ylabel(ylabel=f"Command [{command_unit}]")
        command_plot.set_xlabel(f"Time [{time_unit}]")
        if t_zero!=0: plt.axvline(0, c='r', lw=1, ls='--', alpha=.8)
        subplots.append(command_plot)
        x_share = command_plot
    #if piezo will be plotted current plot show be in row 1 else in row 0
    trace_pos = 1 if show_piezo else 0

    # plot the current trace
    current_plot = fig.add_subplot(pgs[trace_pos:trace_pos+2,:2], sharex=x_share)
    tr_line, = current_plot.plot(time, episode.trace)
    current_plot.set_ylabel(ylabel=f"Current [{current_unit}]")
    if show_idealization and episode.idealization is not None:
        plotTrace(ax=current_plot, time=time, trace=episode.idealization, alpha=.6)
    # label only the last axis
    if show_command: current_plot.set_xticklabels([])
    else: current_plot.set_xlabel(f"Time [{time_unit}]")
    if t_zero!=0: plt.axvline(0, c='r', lw=1, ls='--', alpha=.8)
    subplots.append(current_plot)
    #sharex with current or command voltage
    x_share = x_share if show_command else current_plot
    # plot the piezo
    if show_piezo and type(episode.piezo) is np.ndarray:
        log.info('will plot piezo voltage')
        #always plots piezo voltage on top
        piezo_plot = fig.add_subplot(pgs[0,:2], sharex=x_share)
        pi_line, = piezo_plot.plot(time, episode.piezo)
        piezo_plot.set_ylabel(f"Piezo [{piezo_unit}]")
        piezo_plot.set_xticklabels([])
        if t_zero!=0: plt.axvline(0, c='r', lw=1, ls='--', alpha=.8)
        subplots.append(piezo_plot)
    return subplots, [cm_line, tr_line, pi_line]
