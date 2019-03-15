import logging
import tkinter as tk
from tkinter import ttk


import numpy as np

class FirstActivationFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        self.parent = parent #parent is main window
        self.fa_threshold = tk.StringVar()
        self.click_to_next = tk.IntVar()
        self.click_to_next.set(1)

        #mainly cosmetic, if threshold_crossing idealization has been performed
        #we can use the smallest threshold value as initial value for the first
        #event threshold
        if (self.parent.data.fa_threshold is None \
            and np.any(parent.data._tc_thresholds)
           ):
            self.parent.data.fa_threshold = parent.data._tc_thresholds[0]
        else:
            self.parent.data.fa_threshold \
            = np.mean(self.parent.data.episode.trace)
        self.fa_threshold.set(f"{self.parent.data.fa_threshold:.5f}")
        self.create_widgets()

        #set up plots and switch to first episode
        self.parent.plots.draw_fa_line(draw=False)
        if self.parent.data.episode.first_activation is None:
            self.parent.data.detect_fa()
        self.parent.plots.draw_fa_mark(draw=False)
        self.parent.n_episode.set(0)
        self.parent.plots.show_fa_line.set(1)
        self.parent.plots.show_fa_mark.set(1)

        self.manual_mode = False
        self.tracking_on = False
        self.manually_set_eps = set()

    def change_threshold(self, *args):
        logging.debug(f"change_threshold")
        #update the string showing the threshold value
        self.fa_threshold.set(f"{self.parent.data.fa_threshold:.5f}")

    def toggle_tracking(self):
        logging.debug(f"toggle_tracking")
        if not self.tracking_on:
            if self.manual_mode: self.toggle_manual_mode()
            if self.manually_set_eps:
                warning = tk.Toplevel(self)
                tk.Label(warning, text=('You have manually located the first '
                                        'event for some episode(s).\n \n'
                                        'Do you wish to overwrite these events '
                                        'or would you like to only apply '
                                        'automatic detection to the remaining '
                                        'episodes?')).grid(columnspan=2)
                tk.Button(warning, text='Detect for all episodes',
                          command=lambda *args: [self.manually_set_eps.clear(),
                                                 warning.destroy()]
                         ).grid(row=1)
                tk.Button(warning, text='Detect for remaining episodes',
                            command=warning.destroy).grid(row=1, column=1)

            self.plot_track_cid = self.parent.plots.fig.canvas.mpl_connect(
                                                          'motion_notify_event',
                                                          self.track_cursor)
            self.toggle_button.config(relief="sunken")
        else:
            self.parent.plots.fig.canvas.mpl_disconnect(self.plot_track_cid)
            self.toggle_button.config(relief="raised")
        self.tracking_on = not self.tracking_on

    def track_cursor(self, event):
        #while dragging the threshold line on the plot get the position
        #of the cursor and update the plot
        if (self.parent.plots.toolbar._active is None
            and event.button==1
            and event.inaxes is not None
            ):
            self.parent.data.fa_threshold = event.ydata
            self.change_threshold()
            self.parent.data.detect_fa(exclude=self.manually_set_eps)
            self.parent.plots.update_fa_mark(draw=False)
            self.parent.plots.update_fa_line()

    def create_widgets(self):
        logging.debug(f"create_widgets")
        self.toggle_button = tk.Button(self, text='Set Threshold',
                                        command=self.toggle_tracking)
        self.toggle_button.grid()
        ttk.Entry(self, textvariable=self.fa_threshold, width=10)\
            .grid(row=0, column=1)
        ttk.Label(self, text=f"[{self.parent.data.tc_unit}]")\
            .grid(row=0, column=2)

        self.manual_button = tk.Button(self, text="Mark events manually",
                                        command=self.toggle_manual_mode)
        self.manual_button.grid(row=1)
        ttk.Label(self, text='Clicking moves to next episode: ')\
            .grid(row=1, column=1)
        self.cb_click_next = tk.Checkbutton(self, variable=self.click_to_next)
        self.cb_click_next.grid(row=1, column=2)

        ttk.Button(self, text='Finish', command=self.ok_click).grid(row=5)
        ttk.Button(self,text="Cancel", command=self.click_cancel)\
            .grid(row=5, column=1)

    def toggle_manual_mode(self):
        logging.debug(f"toggle_manual_mode")
        if not self.manual_mode:
            if self.tracking_on: self.toggle_tracking()
            self.plot_manual_cid = self.parent.plots.fig.canvas.mpl_connect(
                                                          'button_press_event',
                                                       self.manual_fa_selection)
            self.manual_button.config(relief="sunken")
        else:
            self.parent.plots.fig.canvas.mpl_disconnect(self.plot_manual_cid)
            self.manual_button.config(relief="raised")
        self.manual_mode = not self.manual_mode

    def manual_fa_selection(self, event):
        logging.debug(f"manual_fa_selection")
        if (self.parent.plots.toolbar._active is None
            and event.button==1
            and event.inaxes is not None
            ):
            self.parent.data.episode.first_activation = event.xdata
            self.manually_set_eps.add(self.parent.n_episode.get())
            self.parent.plots.update_fa_mark()
            if self.click_to_next:
                self.parent.n_episode.set(self.parent.n_episode.get()+1)
            self.parent.plots.update_fa_mark()

    def click_cancel(self):
        logging.debug(f"click_cancel")
        self.parent.plots.show_fa_mark.set(0)
        for episode in self.parent.data.series:
            episode._first_activation = None
        self.close_frame()

    def ok_click(self):
        logging.debug(f"ok_click")
        self.close_frame()

    def close_frame(self):
        logging.debug(f"close_frame")
        #return plot to previous settings
        if self.tracking_on:
            self.parent.plots.fig.canvas.mpl_disconnect(self.plot_track_cid)
        if self.manual_mode:
            self.parent.plots.fig.canvas.mpl_disconnect(self.plot_manual_cid)
        self.parent.plots.show_fa_line.set(0)
        self.parent.plots.update_plots()
        #remove reference in main window
        self.parent.fa_frame = None
        self.destroy()
