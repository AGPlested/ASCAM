import tkinter as tk
from tkinter import ttk
import logging as log

import numpy as np

from recording import Recording

class TC_Frame(ttk.Frame):
    def __init__(self, parent):
        log.debug("being TC_Frame.__init__")
        ttk.Frame.__init__(self, parent)
        self.parent = parent #parent is main
        self.parent.show_tc.set(1)
        self.parent.show_amp.set(1)
        self.tracking_on = True
        self.track_cid = self.parent.plots.fig.canvas.mpl_connect(
                                                          'motion_notify_event',
                                                          self.track_cursor)
        self.create_widgets()
        log.debug("end TC_Frame.__init__")

    def create_widgets(self):
        log.debug(f"TC_Frame.create_widgets")
        #entry for amplitudes
        self.amp_button = tk.Button(self, text="Amplitudes", width=12,
                                    relief="sunken", command=self.toggle_amp)
        self.amp_button.grid(row=4, column=0, columnspan=2)
        amp_entry = ttk.Entry(self, textvariable=self.parent.tc_amps, width=30)
        amp_entry.grid(row=5, column=0, columnspan=2)
        # amp_entry.bind('<FocusOut>', self.get_amps)
        amp_entry.bind('<Return>', self.get_amps)

        #entry for thresholds
        self.tc_button = tk.Button(self, text="Thresholds", width=12,
                                   relief="sunken", command=self.toggle_tc)
        self.tc_button.grid(row=6, column=0, columnspan=2)
        tc_entry = ttk.Entry(self, textvariable=self.parent.tc_thresholds,
                             width=30)
        tc_entry.grid(row=7, column=0, columnspan=2)
        # tc_entry.bind('<FocusOut>', self.get_thresholds)
        tc_entry.bind('<Return>', self.get_thresholds)

        ttk.Button(self, text="Show", command=lambda: [self.get_amps(),
                                                       self.get_thresholds()]
                    ).grid(row=8, columnspan=2)

        ttk.Button(self, text="Apply", command=self.click_apply).grid(row=11)
        ttk.Button(self, text="Cancel", command=self.click_cancel).grid(row=11,
                                                                       column=1)

    def get_amps(self, *args):
        log.debug(f"TC_Frame.get_amps")
        if ',' in self.parent.tc_amps.get():
            self.parent.data.TC_amplitudes \
            = np.array(self.parent.tc_amps.get().split(','), dtype=np.float)
        else:
            self.parent.data.TC_amplitudes \
            = np.array(self.parent.tc_amps.get().split(), dtype=np.float)
        self.demo_idealization()
        self.parent.plots.plot()

    def toggle_amp(self, *args):
        log.debug(f"TC_Frame.toggle_amp")
        if self.parent.show_amp.get()==0:
            self.parent.show_amp.set(1)
            self.amp_button.config(relief="sunken")
            self.get_amps()
        else:
            self.parent.show_amp.set(0)
            self.amp_button.config(relief="raised")

    def get_thresholds(self, *args):
        log.debug(f"TC_Frame.get_thresholds")
        if ',' in self.parent.tc_amps.get():
            self.parent.data.TC_thresholds = np.array(
                             self.parent.tc_thresholds.get().split(','),dtype=np.float)
        else:
            self.parent.data.TC_thresholds = np.array(self.parent.tc_thresholds.get().split(),
                                              dtype=np.float)
        self.demo_idealization()
        self.parent.plots.plot()

    def toggle_tc(self, *args):
        log.debug(f"TC_Frame.toggle_tc")
        if self.parent.show_tc.get()==0:
            self.parent.show_tc.set(1)
            self.tc_button.config(relief="sunken")
            self.get_thresholds()
        else:
            self.parent.show_tc.set(0)
            self.tc_button.config(relief="raised")

    def demo_idealization(self):
        log.debug(f"TC_Frame.demo_idealization")
        self.parent.data.idealize_series()
        self.parent.data[self.parent.data.currentDatakey].idealized = False
        self.parent.plots.plot()

    def click_cancel(self):
        log.debug(f"TC_Frame.click_cancel")
        for series in self.parent.data.values():
            if not series.idealized:
                for episode in series:
                    episode.idealization = None
        self.close_frame()

    def click_apply(self):
        log.debug(f"TC_Frame.click_apply")
        #when clicking 'ok' apply the idealization with the last settings
        #to the actual data in the main window
        self.parent.data.idealize_series()
        self.close_frame()

    def close_frame(self):
        log.debug(f"TC_Frame.close_frame")
        self.parent.show_tc.set(0)
        self.parent.show_amp.set(0)
        self.parent.draw_plots()
        self.parent.plots.fig.canvas.mpl_disconnect(self.track_cid)
        self.destroy()

    def track_cursor(self, event):
        """
        Track the position of the mouse cursor over the plot and if mouse 1 is
        pressed adjust the nearest threshold/amplitude line by dragging the
        cursor.
        """
        #if statment first checks if the toolbar is currently trying to capture
        #the mouse, then if the click is a left click and whether it is
        #within the figure
        if (self.parent.plots.toolbar._active is None
            and event.button==1
            and event.inaxes is not None
            ):
            y_pos = event.ydata

            if (self.parent.show_tc.get() and self.parent.show_amp.get()
                and self.parent.data.TC_thresholds.size
                    +self.parent.data.TC_amplitudes.size>0
                ):
                if self.parent.data.TC_thresholds.size>0:
                    tc_diff = np.abs(self.parent.data.TC_thresholds-y_pos)
                else: tc_diff = np.inf
                if self.parent.data.TC_amplitudes.size>0:
                    amp_diff = np.abs(self.parent.data.TC_amplitudes-y_pos)
                else: amp_diff = np.inf
                if np.min(tc_diff)<np.min(amp_diff):
                    i = np.argmin(tc_diff)
                    self.parent.data.TC_thresholds[i] = y_pos
                    sep = ',' if ',' in self.parent.tc_thresholds.get() else ' '
                    split_string = self.parent.tc_thresholds.get().split(sep)
                    split_string[i] = f"{y_pos:.2e}"
                    self.parent.tc_thresholds.set(sep.join(split_string))
                else:
                    i = np.argmin(amp_diff)
                    self.parent.data.TC_amplitudes[i] = y_pos
                    sep = ',' if ',' in self.parent.tc_amps.get() else ' '
                    split_string = self.parent.tc_amps.get().split(sep)
                    split_string[i] = f"{y_pos:.2e}"
                    self.parent.tc_amps.set(sep.join(split_string))
            elif (self.parent.show_tc.get()
                and self.parent.data.TC_thresholds.size>0
                ):
                tc_diff = np.abs(self.parent.data.TC_thresholds-y_pos)
                i = np.argmin(tc_diff)
                self.parent.data.TC_thresholds[i] = y_pos
                sep = ',' if ',' in self.parent.tc_thresholds.get() else ' '
                split_string = self.parent.tc_thresholds.get().split(sep)
                split_string[i] = f"{y_pos:.2e}"
                self.parent.tc_thresholds.set(sep.join(split_string))
            elif (self.parent.show_amp.get()
                and self.parent.data.TC_amplitudes.size>0
                ):
                amp_diff = np.abs(self.parent.data.TC_amplitudes-y_pos)
                i = np.argmin(amp_diff)
                self.parent.data.TC_amplitudes[i] = y_pos
                sep = ',' if ',' in self.parent.tc_amps.get() else ' '
                split_string = self.parent.tc_amps.get().split(sep)
                split_string[i] = f"{y_pos:.2e}"
                self.parent.tc_amps.set(sep.join(split_string))
            self.demo_idealization()
