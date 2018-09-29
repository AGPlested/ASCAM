import logging as log
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import gridspec as gs
import numpy as np

from tools import PlotToolbar

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


    def setup_plots(self):
        log.debug(f"plotframe.setup_plots")
        show_command = self.show_command.get()\
                       and self.parent.data.has_command
        show_piezo = self.show_piezo.get()\
                     and self.parent.data.has_piezo
        # decide how many plots there will be
        num_plots = 1+show_command+show_piezo
        show_hist = False
        x_share = None
        # show_hist = int(self.parent.hist_single_ep.get() or self.parent.hist_all.get())
        # plot grid to make current plot bigger
        #arguments are nRows by nCols
        pgs = gs.GridSpec(num_plots+1,1+show_hist)
        if show_command:
            # always plot command voltage on bottom (-1 row)
            self.command_plot = self.fig.add_subplot(pgs[-1,:1+show_hist])
            x_share = self.command_plot
        else: self.command_plot = None
        #if piezo will be plotted current plot show be in row 1 else in row 0
        trace_pos = 1 if show_piezo else 0

        self.current_plot = self.fig.add_subplot(pgs[trace_pos:trace_pos+2,:1+show_hist], sharex=x_share)

        #sharex with current or command voltage
        x_share = x_share if show_command else self.current_plot
        if show_piezo:
            #always plots piezo voltage on top
            self.piezo_plot = self.fig.add_subplot(pgs[0,:1+show_hist], sharex=x_share)
        else: self.piezo_plot = None

        if show_hist:
            ax = self.fig.add_subplot(pgs[:,2])
        else: self.histogram = None

    def update_command_plot(self, draw=True):
        log.debug(f"update_command_plot")
        self.c_line.set_ydata(self.parent.episode.command)
        self.command_plot.draw_artist(self.c_line)
        if draw: self.canvas.draw()

    def update_current_plot(self, draw=True):
        log.debug(f"update_current_plot")
        self.t_line.set_ydata(self.parent.episode.trace)
        self.current_plot.draw_artist(self.t_line)
        if draw: self.canvas.draw()

    def update_idealization_plot(self, draw=True):
        log.debug(f"update_idealization_plot")
        if self.parent.episode.idealization is not None:
            if self.show_idealization.get():
                self.i_line.set_visible(True)
            else:
                self.i_line.set_visible(False)
            self.i_line.set_ydata(self.parent.episode.idealization)
            self.current_plot.draw_artist(self.i_line)
            if draw: self.canvas.draw()

    def update_piezo_plot(self, draw=True):
        log.debug(f"update_piezo_plot")
        self.p_line.set_ydata(self.parent.episode.piezo)
        self.piezo_plot.draw_artist(self.p_line)
        if draw: self.canvas.draw()

    def update_plots(self, draw=True):
        log.debug(f"plotframe.update_plots")

        if self.show_command.get(): self.update_command_plot(draw=False)
        self.update_current_plot(draw=False)
        if self.show_idealization: self.update_idealization_plot(draw=False)
        if self.show_piezo.get(): self.update_piezo_plot(draw=False)
        # self.current_plot.draw_artist(self.current_plot)
        # self.current_plot.draw_artist(self.current_plot.yaxis)
        # self.command_plot.draw_artist(self.command_plot)
        # self.command_plot.draw_artist(self.command_plot.yaxis)
        # self.piezo_plot.draw_artist(self.piezo_plot)
        # self.piezo_plot.draw_artist(self.piezo_plot.yaxis)
        if self.show_amp.get(): self.update_theta_lines(draw=False)
        if self.show_thetas.get(): self.update_amp_lines(draw=False)

        self.fig.canvas.flush_events()
        if draw: self.canvas.draw()

    def update_TC_lines(self, draw=True):
        log.debug(f"update_TC_lines")
        if self.show_amp.get(): self.update_amp_lines(draw=False)
        if self.show_thetas.get(): self.update_theta_lines(draw=False)
        if draw: self.canvas.draw()

    def update_amp_lines(self, draw=True):
        log.debug(f"update_amp_lines")
        for amp, line in zip(self.parent.data.TC_amplitudes,self.amp_lines):
            line.set_ydata(amp)
            self.current_plot.draw_artist(line)
        if draw: self.canvas.draw()

    def update_theta_lines(self, draw=True):
        log.debug(f"update_theta_lines")
        for theta, line in zip(self.parent.data.TC_thresholds, self.theta_lines):
            line.set_ydata(theta)
            self.current_plot.draw_artist(line)
        if draw: self.canvas.draw()

    def draw_TC_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.draw_TC_lines")
        if self.show_thetas.get():
            self.draw_amp_lines(draw=False)
        if self.show_amp.get():
            self.draw_theta_lines(draw=False)
        if draw: self.canvas.draw()

    def draw_theta_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.draw_theta_lines")
        if self.theta_lines:
            self.remove_theta_lines()
        for theta in self.parent.data.TC_thresholds:
            line = self.current_plot.axhline(theta, ls='--', c='r', alpha=0.3)
            self.theta_lines.append(line)
        self.canvas.draw()
        if draw: self.canvas.draw()

    def draw_amp_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.draw_amp_lines")
        if self.amp_lines:
            self.remove_amp_lines()
        for amp in self.parent.data.TC_amplitudes:
            line = self.current_plot.axhline(amp, ls='--', c='b', alpha=0.3)
            self.amp_lines.append(line)
        self.canvas.draw()
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
                # del line #del to make sure memory is cleared
            self.theta_lines = list()
        if draw: self.canvas.draw()

    def remove_amp_lines(self, draw=True, *args):
        log.debug(f"PlotFrame.remove_amp_lines")
        if self.amp_lines:
            for line in self.amp_lines:
                line.remove()
                # del line
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
            # self.remove_TC_lines()
            plt.clf()
            self.setup_plots()
            self.init_plot()

    def init_plot(self):
        self.plotted = True
        log.debug(f"PlotFrame.init_plot")
        # get data to plot
        episode = self.parent.episode
        if self.command_plot is not None:
            self.c_line, = self.command_plot.plot(episode.time, episode.command)
        self.t_line, = self.current_plot.plot(episode.time, episode.trace)
        if episode.idealization is not None:
            self.i_line,  = self.current_plot.plot(episode.time,
                                    episode.idealization,
                                    visible=bool(self.show_idealization.get()))
        #if idealization not present create invisble idealization plot as placeholder
        else:
            self.i_line,  = self.current_plot.plot(episode.time,
                              np.mean(episode.trace)*np.ones(episode.time.size),
                              visible=False)

        if self.piezo_plot is not None:
            self.p_line, = self.piezo_plot.plot(episode.time,episode.piezo)

        self.draw_TC_lines(draw=False)

        self.toolbar.update()
        self.canvas.draw() # draw plots
        #draw lines for idealization parameters

        # #plot histograms
        # active = bool(self.parent.hist_piezo_active.get()) \
        #          and self.parent.data.has_piezo
        # select_piezo = bool(self.parent.hist_piezo_interval.get()) \
        #                and self.parent.data.has_piezo
        # self.histogram, self.hist_data = plot_histogram(self.fig, self.pgs, episode, series,
        #         n_bins=int(float(self.parent.hist_number_bins.get())),
        #         density=bool(self.parent.hist_density.get()),
        #         select_piezo=select_piezo,
        #         active=active,
        #         deviation=float(self.parent.hist_piezo_deviation.get()),
        #         fs=float(self.parent.sampling_rate.get()),
        #         intervals=self.parent.hist_intervals,
        #         single_hist=self.parent.hist_single_ep.get(),
        #         allpoint_hist=allpoint_hist,
        #         current_unit=self.parent.data.currentUnit,
        #         episode_inds=self.parent.get_episodes_in_lists())
