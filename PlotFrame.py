import logging as log
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import gridspec as gs
#check mpl version because navigation toolbar name has changed
mpl_ver = (matplotlib.__version__).split('.')
if int(mpl_ver[0])<2 or int(mpl_ver[1])<2 or int(mpl_ver[2])<2:
    from matplotlib.backends.backend_tkagg \
    import NavigationToolbar2TkAgg as NavigationToolbar2Tk
else: from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import numpy as np

from plotting import create_histogram

class PlotFrame(ttk.Frame):
    def __init__(self, parent):
        log.debug(f"begin PlotFrame.__init__")
        ttk.Frame.__init__(self, parent)
        self.parent = parent #parent is main frame
        #initiliaze figure
        self.fig = plt.figure(figsize=(10,5))

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.toolbar = PlotToolbar(self.canvas, self)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.initiliaze_parameters()

        self.plotted = False

        log.debug(f"end PlotFrame.__init__")

    def initiliaze_parameters(self):
        self.piezo_plot = None
        self.current_plot = None
        self.command_plot = None
        self.histogram = None

        # parameters for the histogram
        self.show_hist = tk.IntVar() #must be true to show any histogram
        self.show_hist.set(1) #default is to show histograms
        self.hist_n_bins = tk.StringVar()
        self.hist_n_bins.set(50)
        self.hist_density = tk.IntVar()
        #if true area of histograms is normalized
        self.hist_density.set(0) #default is to show histogram as counts
        self.hist_density.trace("w", self.plot)

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
        self.show_hist_single.trace("w", self.plot)
        self.show_hist_all = tk.IntVar() #if true plot a histogram of all points
        self.show_hist_all.set(1)
        self.show_hist_all.trace("w", self.plot)
        # radio button variable to decide how to select points in histogram
        self.hist_piezo_interval = tk.IntVar()
        self.hist_piezo_interval.set(1)

        # parameters for the plots
        self.show_piezo = tk.IntVar()
        self.show_piezo.set(1)
        self.show_piezo.trace("w", self.plot)
        self.show_command = tk.IntVar()
        self.show_command.set(1)
        self.show_command.trace("w", self.plot)
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
        #lists to hold references to the lines indicating TC paramters
        self.theta_lines = list()
        self.amp_lines = list()

    def update_command_plot(self, draw=True, *args):
        log.debug(f"update_command_plot")
        self.c_line.set_ydata(self.parent.episode.command)
        if draw: self.canvas.draw()

    def update_current_plot(self, draw=True, *args):
        log.debug(f"update_current_plot")
        self.t_line.set_ydata(self.parent.episode.trace)
        if draw: self.canvas.draw()

    def update_idealization_plot(self, draw=True, *args):
        log.debug(f"update_idealization_plot")
        if self.parent.episode.idealization is not None:
            if self.show_idealization.get():
                self.i_line.set_visible(True)
            else:
                self.i_line.set_visible(False)
            self.i_line.set_ydata(self.parent.episode.idealization)
            if draw: self.canvas.draw()

    def update_piezo_plot(self, draw=True, *args):
        log.debug(f"update_piezo_plot")
        self.p_line.set_ydata(self.parent.episode.piezo)
        if draw: self.canvas.draw()

    def update_plots(self, draw=True, *args):
        log.debug(f"plotframe.update_plots")

        if self.show_command.get(): self.update_command_plot(draw=False)
        self.update_current_plot(draw=False)
        if self.show_idealization: self.update_idealization_plot(draw=False)
        if self.show_piezo.get(): self.update_piezo_plot(draw=False)
        if self.show_amp.get(): self.update_theta_lines(draw=False)
        if self.show_thetas.get(): self.update_amp_lines(draw=False)

        if self.show_hist_single.get():
            self.update_single_hist(draw=False)
            # self.update_histograms(draw=False)

        self.fig.canvas.flush_events()
        if draw: self.canvas.draw()

    def update_histograms(self, draw=True, *args):
        log.debug(f"update_histograms")
        if self.show_hist_single.get(): self.update_single_hist(draw=False)
        if self.show_hist_all.get(): self.update_all_hist(draw=False)
        if draw: self.canvas.draw()

    def update_single_hist(self, draw=True, *args):
        log.debug(f"update_single_hist")
        episode = self.parent.episode
        heights, bins, centers, width \
        = create_histogram(episode.time, [episode.piezo],
                       [episode.trace],
                       active=self.hist_piezo_active.get(),
                       select_piezo=self.hist_piezo_interval.get(),
                       deviation=float(self.hist_piezo_deviation.get()),
                       n_bins=int(self.hist_n_bins.get()),
                       density=self.hist_density.get(),
                       intervals=self.hist_intervals,
                       sampling_rate=self.parent.data.sampling_rate,
                       time_unit=self.parent.data.time_unit)
        for (rect, h, b) in zip(self.single_hist, heights, bins):
            rect.set_width(h)
            rect.set_y(b)
        if draw: self.canvas.draw()

    def update_all_hist(self, draw=True, *args):
        log.debug(f"update_all_hist")
        episode = self.parent.episode
        indices = self.parent.get_episodes_in_lists()
        piezos = [episode.piezo for episode in self.parent.series \
                                    if episode.n_episode in indices]
        traces = [episode.trace for episode in self.parent.series \
                                    if episode.n_episode in indices]
        heights, bins, centers, width \
        = create_histogram(episode.time, piezos, traces,
                       active=self.hist_piezo_active.get(),
                       select_piezo=self.hist_piezo_interval.get(),
                       n_bins=int(self.hist_n_bins.get()),
                       deviation=float(self.hist_piezo_deviation.get()),
                       density=self.hist_density.get(),
                       intervals=self.hist_intervals,
                       sampling_rate=self.parent.data.sampling_rate,
                       time_unit=self.parent.data.time_unit)
        for (rect, h, b) in zip(self.all_hist, heights, bins):
            rect.set_width(h)
            rect.set_y(b)

        self.all_hist_line.set_xdata(heights)
        self.all_hist_line.set_ydata(centers)


        if draw: self.canvas.draw()

    def update_TC_lines(self, draw=True, *args):
        log.debug(f"update_TC_lines")
        if self.show_amp.get(): self.update_amp_lines(draw=False)
        if self.show_thetas.get(): self.update_theta_lines(draw=False)
        if draw: self.canvas.draw()

    def update_amp_lines(self, draw=True, *args):
        log.debug(f"update_amp_lines")
        for amp, line in zip(self.parent.data.TC_amplitudes,self.amp_lines):
            line.set_ydata(amp)
        if draw: self.canvas.draw()

    def update_theta_lines(self, draw=True, *args):
        log.debug(f"update_theta_lines")
        for theta, line in zip(self.parent.data.TC_thresholds, self.theta_lines):
            line.set_ydata(theta)
        if draw: self.canvas.draw()

    def draw_TC_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.draw_TC_lines")
        if self.show_thetas.get():
            self.draw_theta_lines(draw=False)
        if self.show_amp.get():
            self.draw_amp_lines(draw=False)
        if draw: self.canvas.draw()

    def draw_theta_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.draw_theta_lines")
        if self.theta_lines:
            self.remove_theta_lines()
        for theta in self.parent.data.TC_thresholds:
            line = self.current_plot.axhline(theta, ls='--', c='r', alpha=0.3)
            self.theta_lines.append(line)
        if draw: self.canvas.draw()

    def draw_amp_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.draw_amp_lines")
        if self.amp_lines:
            self.remove_amp_lines()
        for amp in self.parent.data.TC_amplitudes:
            line = self.current_plot.axhline(amp, ls='--', c='b', alpha=0.3)
            self.amp_lines.append(line)
        if draw: self.canvas.draw()

    def remove_TC_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.remove_TC_lines")
        self.remove_amp_lines(draw=False)
        self.remove_theta_lines(draw=False)
        if draw: self.canvas.draw()

    def remove_theta_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.remove_theta_lines")
        if self.theta_lines:
            for line in self.theta_lines:
                line.remove()
        self.theta_lines = list()
        if draw: self.canvas.draw()

    def remove_amp_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.remove_amp_lines")
        if self.amp_lines:
            for line in self.amp_lines:
                line.remove()
        self.amp_lines = list()
        if draw: self.canvas.draw()

    def plot(self, new=False, *args):
        """
        Draw the all the plots. If `new` is true everything is drawn from
        scratch, otherwise only the lines in the plots are updated.
        """
        log.debug(f"plotframe.plot")
        if self.plotted and not new:
            self.update_plots()
        else:
            if len(self.parent.data['raw_'])>0:
                plt.clf()
                self.setup_plots()
                self.init_plot()

    def init_plot(self):
        self.plotted = True
        log.debug(f"PlotFrame.init_plot")
        episode = self.parent.episode
        if self.command_plot is not None:
            self.c_line, = self.command_plot.plot(episode.time, episode.command)
        self.t_line, = self.current_plot.plot(episode.time, episode.trace)
        if episode.idealization is not None:
            self.i_line,  = self.current_plot.plot(episode.time,
                                    episode.idealization,
                                    visible=bool(self.show_idealization.get()))
        #if idealization not present create invisble plot as placeholder
        else:
            self.i_line,  = self.current_plot.plot(episode.time,
                              np.mean(episode.trace)*np.ones(episode.time.size),
                              visible=False, alpha=.6)

        if self.piezo_plot is not None:
            self.p_line, = self.piezo_plot.plot(episode.time, episode.piezo)

        self.amp_lines = list()
        self.theta_lines = list()
        self.draw_TC_lines(draw=False)

        if self.histogram is not None:
            episode = self.parent.episode

            if self.show_hist_single.get():
                heights, _, centers, width \
                = create_histogram(episode.time, [episode.piezo],
                               [episode.trace],
                               active=self.hist_piezo_active.get(),
                               select_piezo=self.hist_piezo_interval.get(),
                               deviation=float(self.hist_piezo_deviation.get()),
                               n_bins=int(self.hist_n_bins.get()),
                               density=self.hist_density.get(),
                               intervals=self.hist_intervals,
                               sampling_rate=self.parent.data.sampling_rate,
                               time_unit=self.parent.data.time_unit)
                self.single_hist = self.histogram.barh(centers, heights, width,
                                    align='center')

            if self.show_hist_all.get():
                indices = self.parent.get_episodes_in_lists()
                piezos = [episode.piezo for episode in self.parent.series \
                                            if episode.n_episode in indices]
                traces = [episode.trace for episode in self.parent.series \
                                            if episode.n_episode in indices]
                heights, _, centers, width \
                = create_histogram(episode.time, piezos, traces,
                               active=self.hist_piezo_active.get(),
                               select_piezo=self.hist_piezo_interval.get(),
                               n_bins=int(self.hist_n_bins.get()),
                               deviation=float(self.hist_piezo_deviation.get()),
                               density=self.hist_density.get(),
                               intervals=self.hist_intervals,
                               sampling_rate=self.parent.data.sampling_rate,
                               time_unit=self.parent.data.time_unit)

                self.all_hist = self.histogram.barh(centers, heights, width,
                                    alpha=0.2, color='orange', align='center')
                self.all_hist_line, = self.histogram.plot(heights, centers,
                                                           color='orange')

        self.toolbar.update()
        self.canvas.draw()

    def setup_plots(self):
        log.debug(f"plotframe.setup_plots")
        show_command = self.show_command.get()\
                       and self.parent.data.has_command
        show_piezo = self.show_piezo.get()\
                     and self.parent.data.has_piezo
        # decide how many plots there will be
        num_plots = 1+show_command+show_piezo
        show_hist = 1
        x_share = None
        show_hist = int(self.show_hist_single.get() or self.show_hist_all.get())
        # plot grid to make current plot bigger
        #arguments are nRows by nCols
        pgs = gs.GridSpec(num_plots+1,1+2*show_hist)
        if show_command:
            # always plot command voltage on bottom (-1 row)
            self.command_plot = self.fig.add_subplot(pgs[-1,:1+show_hist])
            c_y = self.parent.series.max_command-self.parent.series.min_command
            self.command_plot.set_ylim(self.parent.series.min_command-.1*c_y,
                                       self.parent.series.max_command+.1*c_y)
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
        trace_y = self.parent.series.max_current-self.parent.series.min_current
        self.current_plot.set_ylim(self.parent.series.min_current-.1*trace_y,
                                   self.parent.series.max_current+.1*trace_y)
        self.current_plot.set_ylabel(f"Current [{self.parent.data.trace_unit}]")
        if show_command: self.current_plot.set_xticklabels([])
        else:
            self.current_plot.set_xlabel(f"Time [{self.parent.data.time_unit}]")
        #sharex with current or command voltage
        x_share = x_share if show_command else self.current_plot
        if show_piezo:
            #always plots piezo voltage on top
            self.piezo_plot = self.fig.add_subplot(pgs[0,:1+show_hist],
                                                   sharex=x_share)
            piezo_y = self.parent.series.max_piezo-self.parent.series.min_piezo
            self.piezo_plot.set_ylim(self.parent.series.min_piezo-.1*piezo_y,
                                    self.parent.series.max_piezo+.1*piezo_y)
            self.piezo_plot.set_ylabel(f"Piezo [{self.parent.data.piezo_unit}]")
            self.piezo_plot.set_xticklabels([])
        else: self.piezo_plot = None

        if show_hist:
            # self.histogram = self.fig.add_subplot(pgs[:, -1], sharey=self.current_plot)
            self.histogram = self.fig.add_subplot(pgs[trace_pos:trace_pos+2,-1],
                                                  sharey=self.current_plot)

            self.histogram.set_ylim(self.parent.series.min_current-.1*trace_y,
                                    self.parent.series.max_current+.1*trace_y)
            self.histogram.yaxis.set_label_position('right')
            self.histogram.yaxis.tick_right()
        else: self.histogram = None

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
