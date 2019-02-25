import logging
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import gridspec as gs
import matplotlib.ticker as plticker
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import numpy as np

TRACE_COLOR = 'xkcd:french blue'
ID_COLOR = 'xkcd:faded orange'
THETA_COLOR = 'red'
SELECT_COLOR = 'brown'
FA_TC_COLOR = 'red'
FA_LINE_COLOR = 'green'

class PlotFrame(ttk.Frame):
    def __init__(self, parent):
        logging.debug(f"begin PlotFrame.__init__")
        ttk.Frame.__init__(self, parent)
        self.parent = parent #parent is main frame
        #initiliaze figure
        #changing the size of the figure only seems to work
        self.fig = plt.figure(figsize=(10,5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side="top", fill='both', expand=True)
        self.toolbar = PlotToolbar(self.canvas, self)
        self.initiliaze_parameters()
        self.plotted = False
        logging.debug(f"end PlotFrame.__init__")

    def initiliaze_parameters(self):
        #references for the plots
        self.piezo_plot = None
        self.current_plot = None
        self.command_plot = None
        self.histogram = None
        #references for the lines
        self.c_line = None #command voltage
        self.t_line = None #current trace
        self.i_line = None #idealized curren trace
        self.p_line = None #piezo voltage
        self.single_hist_sel = None #histogram of current episode in selected
                                    #interval
        self.single_hist = None #histogram of current episode
        self.all_hist_sel = None #histogram of all episode in selected interval
        self.all_hist = None #histogram of all episode
        self.interval_indicator = None #line showing with times are included in
                                        #selected histograms
        #lists to hold references to the lines indicating TC paramters
        self.theta_plot_lines = list() #thresholds for idealization on plots
        self.theta_hist_lines = list() #thresholds for idealization on histogram
        self.amp_plot_lines = list() #amplitudes for idealization on plots
        self.amp_hist_lines = list() #amplitudes for idealization on histogram
        #lists to hold the references to the lines drawn for first_activation
        #(even though there is only one lines of each type they are stored in a
        #list because calling `.remove` does not work otherwise)
        self.fa_lines = list() #threshold for first activation detection
        self.fa_marks = list() #vertical line to mark first activation

        # parameters for the histogram
        self.show_hist = tk.IntVar() #must be true to show any histogram
        self.show_hist.set(1) #default is to show histograms
        self.hist_n_bins = tk.StringVar()
        self.hist_n_bins.set(50)
        self.hist_density = tk.IntVar()
        #if true area of histograms is normalized
        self.hist_density.set(0) #default is to show histogram as counts
        self.hist_density.trace("w", self.hist_density_cb)

        self.hist_piezo_active = tk.IntVar()
        #if true select points in histogram using piezo
        self.hist_piezo_active.set(1) #default is true
        self.hist_piezo_deviation = tk.StringVar()
        #factor by which piezo voltage at a point must differ from 0 to be
        #included
        self.hist_piezo_deviation.set(0.05)

        self.hist_interval_entry = tk.StringVar()
        #if true select points for histogram from given intervals
        self.hist_interval_entry.set('')
        self.hist_intervals = []
        self.show_hist_single = tk.IntVar()
        #if true plot a histogram of the currently selected episode
        self.show_hist_single.set(1)
        self.show_hist_single.trace("w", self.show_hist_single_cb)
        self.show_hist_all = tk.IntVar() #if true plot a histogram of all points
        self.show_hist_all.set(1)
        self.show_hist_all.trace("w", self.show_hist_all_cb)
        # radio button variable to decide how to select points in histogram
        self.hist_piezo_interval = tk.IntVar()
        self.hist_piezo_interval.set(1)

        # parameters for the plots
        self.show_piezo = tk.IntVar()
        self.show_piezo.trace("w", self.show_piezo_sc)
        self.show_piezo.set(1)
        self.show_piezo.trace("w", self.show_piezo_cb)
        self.show_command = tk.IntVar()
        self.show_command.trace("w", self.show_command_sc)
        self.show_command.set(1)
        self.show_command.trace("w", self.show_command_cb)
        self.plot_t_zero = tk.StringVar()
        self.plot_t_zero.set("0.00")
        self.show_idealization = tk.IntVar()
        self.show_idealization.set(1)
        self.show_idealization.trace("w", self.update_idealization_plot)

        #idealization related params
        self.show_thetas = tk.IntVar()
        self.show_thetas.set(0)
        self.show_thetas.trace('w', lambda *args: self.draw_theta_lines() \
                                                if self.show_thetas.get() \
                                                else self.remove_theta_lines())

        self.show_amp = tk.IntVar()
        self.show_amp.set(0)
        self.show_amp.trace('w', lambda *args: self.draw_amp_lines() \
                                                if self.show_amp.get() \
                                                else self.remove_amp_lines())
        #first activation params
        self.show_fa_line = tk.IntVar()
        self.show_fa_line.set(0)
        self.show_fa_line.trace('w', lambda *args: self.draw_fa_line() \
                                                if self.show_fa_line.get() \
                                                else self.remove_fa_lines())
        self.show_fa_mark = tk.IntVar()
        self.show_fa_mark.set(0)
        self.show_fa_mark.trace('w', lambda *args: self.draw_fa_mark() \
                                                if self.show_fa_mark.get() \
                                                else self.remove_fa_marks())

    def draw_hist_indicator(self, draw=True, *args):
        logging.debug(f"draw_hist_indicator")
        trace_y = self.parent.data.series.max_current\
                  - self.parent.data.series.min_current
        hist_indicator = np.ones(self.parent.data.hist_times.size)\
                         *(self.parent.data.series.min_current-.1*trace_y)
        self.interval_indicator, = self.current_plot.plot(
                                        self.parent.data.hist_times,
                                        hist_indicator,
                                        color=SELECT_COLOR, lw=5, alpha=.5,
                                        linestyle='none', marker='o')
        if draw: self.canvas.draw()

    def update_command_plot(self, draw=True, *args):
        logging.debug(f"update_command_plot")
        self.c_line.set_ydata(self.parent.data.episode.command)
        if draw: self.canvas.draw()

    def update_current_plot(self, draw=True, *args):
        logging.debug(f"update_current_plot")
        self.t_line.set_ydata(self.parent.data.episode.trace)
        if draw: self.canvas.draw()

    def update_idealization_plot(self, draw=True, *args):
        logging.debug(f"update_idealization_plot")
        if self.parent.data.episode.idealization is not None:
            if self.show_idealization.get():
                self.i_line.set_visible(True)
            else:
                self.i_line.set_visible(False)
            self.i_line.set_ydata(self.parent.data.episode.idealization)
            if draw: self.canvas.draw()

    def update_piezo_plot(self, draw=True, *args):
        logging.debug(f"update_piezo_plot")
        self.p_line.set_ydata(self.parent.data.episode.piezo)
        if draw: self.canvas.draw()

    def update_plots(self, draw=True, *args):
        logging.debug(f"plotframe.update_plots")

        self.update_current_plot(draw=False)
        if self.show_command.get(): self.update_command_plot(draw=False)
        if self.show_idealization: self.update_idealization_plot(draw=False)
        if self.show_piezo.get(): self.update_piezo_plot(draw=False)
        if self.show_amp.get(): self.update_theta_lines(draw=False)
        if self.show_thetas.get(): self.update_amp_lines(draw=False)
        if self.show_fa_line.get(): self.update_fa_line(draw=False)
        if self.show_fa_mark.get(): self.update_fa_mark(draw=False)

        if self.show_hist_single.get():
            self.update_single_hist(draw=False)

        self.fig.canvas.flush_events()
        if draw: self.canvas.draw()

    def update_histograms(self, draw=True, *args):
        logging.debug(f"update_histograms")
        if self.show_hist_single.get(): self.update_single_hist(draw=False)
        if self.show_hist_all.get(): self.update_all_hist(draw=False)
        self.draw_hist_indicator(draw=False)
        if draw: self.canvas.draw()

    def update_single_hist(self, draw=True, *args):
        logging.debug(f"update_single_hist")
        heights, bins, centers, width \
        = self.parent.data.episode_hist(
                            active=self.hist_piezo_active.get(),
                            select_piezo=self.hist_piezo_interval.get(),
                            deviation=float(self.hist_piezo_deviation.get()),
                            n_bins=int(self.hist_n_bins.get()),
                            density=self.hist_density.get(),
                            intervals=self.hist_intervals)
        for (rect, h, b) in zip(self.single_hist_sel, heights, bins):
            rect.set_width(h)
            rect.set_y(b)

        heights, bins, centers, width \
        = self.parent.data.episode_hist(select_piezo=False,
                                            n_bins=int(self.hist_n_bins.get()),
                                            density=self.hist_density.get())
        for (rect, h, b) in zip(self.single_hist, heights, bins):
            rect.set_width(h)
            rect.set_y(b)

        if draw: self.canvas.draw()

    def update_all_hist(self, draw=True, *args):
        logging.debug(f"update_all_hist")
        # episode = self.parent.data.episode
        # indices = self.parent.get_episodes_in_lists()
        # piezos = [episode.piezo for episode in self.parent.data.series \
        #                             if episode.n_episode in indices]
        # traces = [episode.trace for episode in self.parent.data.series \
        #                             if episode.n_episode in indices]
        heights, bins, centers, width \
        = self.parent.data.series_hist(
                            active=self.hist_piezo_active.get(),
                            select_piezo=self.hist_piezo_interval.get(),
                            n_bins=int(self.hist_n_bins.get()),
                            deviation=float(self.hist_piezo_deviation.get()),
                            density=self.hist_density.get(),
                            intervals=self.hist_intervals)
        for (rect, h, b) in zip(self.all_hist_sel, heights, bins):
            rect.set_width(h)
            rect.set_y(b)
        self.all_hist_line_sel.set_xdata(heights)
        self.all_hist_line_sel.set_ydata(centers)

        heights, bins, centers, width \
        = self.parent.data.series_hist(select_piezo=False,
                                           n_bins=int(self.hist_n_bins.get()),
                                           density=self.hist_density.get())
        for (rect, h, b) in zip(self.all_hist, heights, bins):
            rect.set_width(h)
            rect.set_y(b)
        self.all_hist_line.set_xdata(heights)
        self.all_hist_line.set_ydata(centers)
        if draw: self.canvas.draw()

    def update_TC_lines(self, draw=True, *args):
        logging.debug(f"update_TC_lines")
        if self.show_amp.get(): self.update_amp_lines(draw=False)
        if self.show_thetas.get(): self.update_theta_lines(draw=False)
        if draw: self.canvas.draw()

    def update_amp_lines(self, draw=True, *args):
        logging.debug(f"update_amp_lines")
        for amp, plot_line, hist_line in zip(self.parent.data.TC_amplitudes,
                                             self.amp_plot_lines,
                                             self.amp_hist_lines):
            plot_line.set_ydata(amp)
            hist_line.set_ydata(amp)
        if draw: self.canvas.draw()

    def update_theta_lines(self, draw=True, *args):
        logging.debug(f"update_theta_lines")
        for theta, plot_line, hist_line in zip(self.parent.data.TC_thresholds,
                                               self.theta_plot_lines,
                                               self.theta_hist_lines):
            plot_line.set_ydata(theta)
            hist_line.set_ydata(theta)
        if draw: self.canvas.draw()

    def draw_fa_line(self, draw=True, *args):
        logging.debug(f"draw_fa_line")
        if self.fa_lines:
            self.remove_fa_lines()
        line = self.current_plot.axhline(self.parent.data.fa_threshold,
                                        ls='--', c=FA_TC_COLOR, alpha=0.5)
        self.fa_lines.append(line)
        if draw: self.canvas.draw()

    def draw_fa_mark(self, draw=True, *args):
        logging.debug(f"draw_fa_mark")
        if self.fa_marks:
            self.remove_fa_marks()
        line = self.current_plot.axvline(
                                      self.parent.data.episode.first_activation,
                                      c=FA_LINE_COLOR, alpha=.8)
        self.fa_marks.append(line)
        if draw: self.canvas.draw()

    def update_fa_line(self, draw=True, *args):
        logging.debug(f"update_fa_line")
        for line in self.fa_lines:
            line.set_ydata(self.parent.data.fa_threshold)
        if draw: self.canvas.draw()

    def update_fa_mark(self, draw=True, *args):
        logging.debug(f"update_fa_mark")
        for line in self.fa_marks:
            line.set_xdata(self.parent.data.episode.first_activation)
        if draw: self.canvas.draw()

    def remove_fa_lines(self, draw=True, *args):
        logging.debug(f"remove_fa_lines")
        if self.fa_lines:
            for line in self.fa_lines:
                line.remove()
        self.fa_lines = list()
        if draw: self.canvas.draw()

    def remove_fa_marks(self, draw=True, *args):
        logging.debug(f"remove_fa_marks")
        if self.fa_marks:
            for line in self.fa_marks:
                line.remove()
        self.fa_marks = list()
        if draw: self.canvas.draw()

    def draw_TC_lines(self, draw=True, *args):
        logging.debug(f"PlotFrame.draw_TC_lines")
        if self.show_thetas.get():
            self.draw_theta_lines(draw=False)
        if self.show_amp.get():
            self.draw_amp_lines(draw=False)
        if draw: self.canvas.draw()

    def draw_theta_lines(self, draw=True, *args):
        logging.debug(f"draw_theta_lines")
        if self.theta_plot_lines:
            self.remove_theta_lines()
        for theta in self.parent.data.TC_thresholds:
            line = self.current_plot.axhline(theta, ls='--', c=THETA_COLOR,
                                             alpha=0.3)
            self.theta_plot_lines.append(line)
            line = self.histogram.axhline(theta, ls='--', c=THETA_COLOR,
                                          alpha=0.3)
            self.theta_hist_lines.append(line)
        if draw: self.canvas.draw()

    def draw_amp_lines(self, draw=True, *args):
        logging.debug(f"PlotFrame.draw_amp_lines")
        if self.amp_plot_lines:
            self.remove_amp_lines()
        for amp in self.parent.data.TC_amplitudes:
            line = self.current_plot.axhline(amp, ls='--', c=ID_COLOR,
                                             alpha=0.3)
            self.amp_plot_lines.append(line)
            line = self.histogram.axhline(amp, ls='--', c=ID_COLOR, alpha=0.3)
            self.amp_hist_lines.append(line)
        if draw: self.canvas.draw()

    def remove_TC_lines(self, draw=True, *args):
        logging.debug(f"PlotFrame.remove_TC_lines")
        self.remove_amp_lines(draw=False)
        self.remove_theta_lines(draw=False)
        if draw: self.canvas.draw()

    def remove_theta_lines(self, draw=True, *args):
        logging.debug(f"PlotFrame.remove_theta_lines")
        if self.theta_plot_lines:
            for line in self.theta_plot_lines:
                line.remove()
        self.theta_plot_lines = list()
        if self.theta_hist_lines:
            for line in self.theta_hist_lines:
                line.remove()
        self.theta_hist_lines = list()
        if draw: self.canvas.draw()

    def remove_amp_lines(self, draw=True, *args):
        logging.debug(f"remove_amp_lines")
        if self.amp_plot_lines:
            for line in self.amp_plot_lines:
                line.remove()
        self.amp_plot_lines = list()
        if self.amp_hist_lines:
            for line in self.amp_hist_lines:
                line.remove()
        self.amp_hist_lines = list()
        if draw: self.canvas.draw()

    def plot(self, new=False, *args):
        """Draw the all the plots.

        If `new` is true everything is drawn from
        scratch, otherwise only the lines in the plots are updated."""

        logging.debug(f"plotframe.plot")
        logging.debug(f"new={new}, plotted={self.plotted}")
        if self.plotted and not new:
            self.update_plots()
        else:
            #check if there is any data to plot
            if len(self.parent.data['raw_']) > 0:
                plt.clf()
                self.setup_plots()
                self.init_plot()

    def init_plot(self):
        logging.debug(f"PlotFrame.init_plot")
        episode = self.parent.data.episode
        if self.command_plot is not None:
            self.c_line, = self.command_plot.plot(episode.time, episode.command,
                                                  color=TRACE_COLOR)
        self.t_line, = self.current_plot.plot(episode.time, episode.trace,
                                              color=TRACE_COLOR)
        if episode.idealization is not None:
            self.i_line,  = self.current_plot.plot(episode.time,
                                    episode.idealization, color=ID_COLOR,
                                    alpha=.6,
                                    visible=bool(self.show_idealization.get()))
        #if idealization not present create invisble plot as placeholder
        else:
            self.i_line,  = self.current_plot.plot(episode.time,
                              np.mean(episode.trace)*np.ones(episode.time.size),
                              visible=False, alpha=.6, color=ID_COLOR)

        if self.piezo_plot is not None:
            self.p_line, = self.piezo_plot.plot(episode.time, episode.piezo,
                                                color=TRACE_COLOR)

        self.amp_plot_lines = list()
        self.theta_plot_lines = list()
        self.theta_hist_lines = list()
        self.amp_hist_lines = list()
        self.draw_TC_lines(draw=False)
        self.fa_lines = list()
        self.fa_marks = list()
        if self.show_fa_mark.get(): self.draw_fa_mark(draw=False)
        if self.show_fa_line.get(): self.draw_fa_line(draw=False)

        if self.histogram is not None:
            logging.debug(f"init_plot: self.histogram is not None")
            if self.show_hist_single.get():
                heights, _, centers, width \
                = self.parent.data.episode_hist(active=self.hist_piezo_active.get(),
                            select_piezo=self.hist_piezo_interval.get(),
                            deviation=float(self.hist_piezo_deviation.get()),
                            n_bins=int(self.hist_n_bins.get()),
                            density=self.hist_density.get(),
                            intervals=self.hist_intervals)
                self.single_hist_sel = self.histogram.barh(centers, heights, width,
                                                align='center', color=SELECT_COLOR)
                heights, _, centers, width \
                = self.parent.data.episode_hist(select_piezo=False,
                                            n_bins=int(self.hist_n_bins.get()),
                                            density=self.hist_density.get())
                self.single_hist = self.histogram.barh(centers, heights, width,
                                                align='center', color=TRACE_COLOR)
            if self.show_hist_all.get():
                heights, _, centers, width \
                = self.parent.data.series_hist(
                               active=self.hist_piezo_active.get(),
                               select_piezo=self.hist_piezo_interval.get(),
                               n_bins=int(self.hist_n_bins.get()),
                               deviation=float(self.hist_piezo_deviation.get()),
                               density=self.hist_density.get(),
                               intervals=self.hist_intervals)
                self.all_hist_sel = self.histogram.barh(centers, heights, width,
                                    alpha=0.2, color=SELECT_COLOR, align='center')
                self.all_hist_line_sel, = self.histogram.plot(heights, centers,
                                                           color=SELECT_COLOR)

                heights, _, centers, width \
                = self.parent.data.series_hist(select_piezo=False,
                                           n_bins=int(self.hist_n_bins.get()),
                                           density=self.hist_density.get())
                self.all_hist = self.histogram.barh(centers, heights, width,
                                    alpha=0.2, color=TRACE_COLOR, align='center')
                self.all_hist_line, = self.histogram.plot(heights, centers,
                                                           color=TRACE_COLOR)
                self.draw_hist_indicator(draw=False)
        self.toolbar.update()
        self.canvas.draw()
        self.plotted = True

    def setup_plots(self):
        """Create all the plot objects"""

        logging.debug(f"plotframe.setup_plots")
        show_command = self.show_command.get() and self.parent.data.has_command
        show_piezo = self.show_piezo.get() and self.parent.data.has_piezo
        # decide how many plots there will be
        num_plots = 1+show_command+show_piezo
        x_share = None
        show_hist = int(self.show_hist_single.get() or self.show_hist_all.get())
        # plot grid to make current plot bigger
        #arguments are nRows by nCols
        pgs = gs.GridSpec(num_plots+1,1+2*show_hist)
        if show_command:
            # always plot command voltage on bottom (-1 row)
            self.command_plot = self.fig.add_subplot(pgs[-1,:1+show_hist])
            c_y = self.parent.data.series.max_command\
                  - self.parent.data.series.min_command
            self.command_plot.set_ylim(
                                    self.parent.data.series.min_command-.1*c_y,
                                    self.parent.data.series.max_command+.1*c_y)
            self.command_plot.set_ylabel(
                            ylabel=f"Command [{self.parent.data.command_unit}]")
            self.command_plot.set_xlabel(f"Time [{self.parent.data.time_unit}]")
            x_share = self.command_plot
        else: self.command_plot = None
        #if piezo will be plotted current plot show be in row 1 else in row 0
        trace_pos = 1 if show_piezo else 0

        self.current_plot = self.fig.add_subplot(
                                        pgs[trace_pos:trace_pos+2,:1+show_hist],
                                        sharex=x_share)
        #set axis limits of current plot so all episodes fit
        trace_y = self.parent.data.series.max_current\
                  - self.parent.data.series.min_current
        self.current_plot.set_ylim(
                                self.parent.data.series.min_current-.1*trace_y,
                                self.parent.data.series.max_current+.1*trace_y)
        self.current_plot.set_ylabel(f"Current [{self.parent.data.trace_unit}]")
        # set axis ticks
        # loc = plticker.MultipleLocator(base=0.5)
        # self.current_plot.yaxis.set_major_locator(loc)
        # loc = plticker.MultipleLocator(base=0.1)
        # self.current_plot.yaxis.set_minor_locator(loc)

        if show_command:
            plt.setp(self.current_plot.get_xticklabels(), visible=False)
        else:
            self.current_plot.set_xlabel(f"Time [{self.parent.data.time_unit}]")
        # sharex with current or command voltage
        x_share = x_share if show_command else self.current_plot
        if show_piezo:
            # always plots piezo voltage on top
            self.piezo_plot = self.fig.add_subplot(pgs[0,:1+show_hist],
                                                   sharex=x_share)
            piezo_y = self.parent.data.series.max_piezo\
                      - self.parent.data.series.min_piezo
            self.piezo_plot.set_ylim(
                                self.parent.data.series.min_piezo-.1*piezo_y,
                                self.parent.data.series.max_piezo+.1*piezo_y)
            self.piezo_plot.set_ylabel(f"Piezo [{self.parent.data.piezo_unit}]")
            plt.setp(self.piezo_plot.get_xticklabels(), visible=False)
        else: self.piezo_plot = None

        if show_hist:
            self.histogram = self.fig.add_subplot(pgs[trace_pos:trace_pos+2,-1],
                                                  sharey=self.current_plot)
            self.histogram.set_ylim(
                                self.parent.data.series.min_current-.1*trace_y,
                                self.parent.data.series.max_current+.1*trace_y)
            self.histogram.set_ylabel(
                                    f"Current [{self.parent.data.trace_unit}]")
            self.histogram.yaxis.set_label_position('right')
            self.histogram.yaxis.tick_right()
        else: self.histogram = None

    def hist_density_cb(self, *args):
        """Redraw plots if histogram as density toggled"""

        logging.debug(f"hist_density_cb")
        self.plot(new=True)

    def show_hist_single_cb(self, *args):
        """Redraw plots if showing of single episode histogram is toggled"""

        logging.debug(f"show_hist_single_cb")
        self.plot(new=True)

    def show_hist_all_cb(self, *args):
        """Redraw plots if showing of histogram of all episodes is toggled"""

        logging.debug(f"show_hist_all_cb")
        self.plot(new=True)

    def show_piezo_cb(self, *args):
        """Redraw plots if showing of piezo votlage is toggled"""

        if self.show_piezo.get():
            logging.debug(f"show_piezo_cb")
            self.plot(new=True)

    def show_command_cb(self, *args):
        """Redraw plots if showing of command votlage is toggled"""

        if self.show_command.get():
            logging.debug(f"show_command_cb")
            self.plot(new=True)

    def show_command_sc(self, *args):
        """Sanity check for show command, prevent show_command being true if
        there is no command voltage data."""

        if not self.parent.data.has_command:
            self.show_command.set(0)

    def show_piezo_sc(self, *args):
        """Sanity check for show piezo, prevent show_command being true if
        there is no piezo voltage data."""

        if not self.parent.data.has_piezo:
            self.show_piezo.set(0)


class PlotToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, parent):
        self.parent = parent # parent is PlotFrame
        self.canvas = canvas
        # this toolbar is just the standard with fewer buttons
        self.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            (None, None, None, None),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
            (None, None, None, None),
            ('Save', 'Save the figure', 'filesave', 'save_figure'),
            )
        NavigationToolbar2Tk.__init__(self, canvas, parent)

    def zoom(self):
        """
        Redefine the zoom method of the toolbar to include zooming out on
        right-click
        """
        # self.parent.parent.tc_frame.track_on = False
        self_zoom_out_cid = self.canvas.mpl_connect('button_press_event',
                                                    self.zoom_out)
        NavigationToolbar2Tk.zoom(self)

    def zoom_out(self, event):
        """
        Zoom out in this case is done by calling `back` on right-click to
        restore the previous view (i.e. undo last zoom)
        """
        if self._active=='ZOOM' and event.button==3:
            NavigationToolbar2Tk.back(self)
