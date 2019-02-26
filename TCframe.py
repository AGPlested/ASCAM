import tkinter as tk
from tkinter import ttk
import logging

import numpy as np

class TC_Frame(ttk.Frame):
    def __init__(self, parent):
        logging.debug("being TC_Frame.__init__")
        ttk.Frame.__init__(self, parent)
        self.parent = parent #parent is main
        #variables for entry
        self.amp_string = tk.StringVar() # string holding the amplitudes
        self.amp_string.set('0')
        self.theta_string = tk.StringVar() # string holding the thresholds
        self.res_string = tk.StringVar() # string holding the resolution
        # variable to keep track of whether thetas have been set manually
        self.manual_thetas = False
        # variables for moving the lines on the plots with the mouse
        self.tracking_on = True
        self.plot_track_cid = self.parent.plots.fig.canvas.mpl_connect(
                                                          'motion_notify_event',
                                                          self.track_cursor)
        # variables to store (and later restore) the state of the plots before
        # initializing TC
        self.previous_show_piezo = self.parent.plots.show_piezo.get()
        self.previous_show_command = self.parent.plots.show_command.get()
        self.previous_show_hist = self.parent.plots.show_hist.get()
        self.parent.plots.show_piezo.set(0)
        self.parent.plots.show_command.set(0)
        # trace episode switching in episodeList to idealize when selecting new
        # episode
        self.eplist_track_id = self.parent.episodeList.episodelist.bind(
                                                '<<ListboxSelect>>',
                                                self.show_idealization, add='+')

        self.create_widgets()
        self.toggle_amp()
        logging.debug("end TC_Frame.__init__")

    @property
    def show_amp(self):
        return self.parent.plots.show_amp.get()

    @property
    def show_thetas(self):
        return self.parent.plots.show_thetas.get()

    def create_widgets(self):
        """Create the tkiner widgets in this frame."""

        logging.debug(f"TC_Frame.create_widgets")
        # button to toggle display of amplitude lines on plot
        self.amp_button = tk.Button(self,
                            text=f"Amplitudes [{self.parent.data.trace_unit}]",
                            width=12, relief="raised", command=self.toggle_amp)
        self.amp_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # entry for amplitudes
        amp_entry = ttk.Entry(self, textvariable=self.amp_string, width=40)
        amp_entry.grid(row=5, column=0, columnspan=2, padx=5, pady=5)
        amp_entry.bind('<Return>', lambda *args: (self.toggle_amp()
                                                  if not self.show_amp
                                                  else self.get_amps()))

        # entry for thresholds
        self.tc_button = tk.Button(self,
                            text=f"Thresholds [{self.parent.data.trace_unit}]",
                            width=12, relief="raised", command=self.toggle_tc)
        self.tc_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)
        theta_entry = ttk.Entry(self, textvariable=self.theta_string, width=40)
        theta_entry.grid(row=7, column=0, columnspan=2, padx=5, pady=5)
        theta_entry.bind('<Return>', lambda *args: (self.toggle_tc()
                                                    if not self.show_thetas
                                                    else self.get_thresholds()))
        theta_entry.bind('<Return>', self.toggle_manual_thetas)

        # resolution
        ttk.Label(self, text=f"Resolution "
                             f"[{self.parent.data.episode.time_unit}]"
                  ).grid(row=8, column=0, columnspan=2, padx=5, pady=5)
        res_entry = ttk.Entry(self, textvariable=self.res_string, width=40)
        res_entry.grid(row=9, column=0, columnspan=2, padx=5, pady=5)
        res_entry.bind("<Return>", self.get_resolution)
        # demo button
        ttk.Button(self, text="Demo", command=self.demo_idealization
                    ).grid(row=10, columnspan=2, padx=5, pady=5)

        # frame closing buttons
        ttk.Button(self, text="Apply and finish", command=self.click_apply
                    ).grid(row=13, padx=5, pady=5)
        ttk.Button(self, text="Cancel", command=self.click_cancel
                    ).grid(row=13, column=1, padx=5, pady=5)

    def get_amps(self, update_plot=True, *args):
        """Get the amplitudes from the entry field.

        Also updates the idealization and if the number of amplitudes changes
        sets the thresholds automatically."""

        logging.debug(f"TC_Frame.get_amps")

        old_n_amps = self.parent.data.TC_amplitudes.size
        if ',' in self.amp_string.get():
            self.parent.data.TC_amplitudes = (
                  np.array(self.amp_string.get().split(','), dtype=np.float))
        else:
            self.parent.data.TC_amplitudes = (
                    np.array(self.amp_string.get().split(), dtype=np.float))
        new_n_amps = self.parent.data.TC_amplitudes.size

        # update the amp lines if command is given and the number didnt change
        # always draw new lines if the number changed
        if new_n_amps != old_n_amps:
            self.manual_thetas = False
        if not self.manual_thetas:
            self.auto_set_thetas()
            if update_plot:
                if new_n_amps == old_n_amps:
                    self.parent.plots.update_TC_lines()
                else:
                    self.parent.plots.draw_TC_lines()
        else:
            if update_plot:
                if new_n_amps == old_n_amps:
                    self.parent.plots.update_amp_lines()
                elif new_n_amps != old_n_amps:
                    self.parent.plots.draw_amp_lines()

        # redo the idealization
        self.show_idealization()

    def toggle_manual_thetas(self, *args):
        """Toggle manually specifying thresholds."""

        logging.debug(f"toggle_manual_thetas")

        # check if theta string is empty or conists only of whitespaces
        if self.theta_string.get().isspace() or self.theta_string.get():
            self.manual_thetas = False
            self.auto_set_thetas()
            self.parent.plots.update_theta_lines()
        else:
            self.manual_thetas = True

    def auto_set_thetas(self):
        """Automatically set the thresholds."""

        logging.debug(f"auto_set_thetas")

        # automatically set the thresholds to the midpoint between the amps
        self.parent.data.TC_thresholds \
        = (self.parent.data.TC_amplitudes[1:]\
           +self.parent.data.TC_amplitudes[:-1])/2
        # seperate the threshold string the same way as the amp string
        sep = ' ,' if ',' in self.amp_string.get() else ' '
        self.theta_string.set(
                  sep.join(np.char.mod('%.2e', self.parent.data.TC_thresholds)))

    def get_thresholds(self, update_plot=True, *args):
        """Get the thresholds from the entry field."""
        logging.debug(f"TC_Frame.get_thresholds")

        old_n_thetas = self.parent.data.TC_thresholds.size
        if ',' in self.amp_string.get():
            self.parent.data.TC_thresholds = (
                np.array(self.theta_string.get().split(','), dtype=np.float))
        else:
            self.parent.data.TC_thresholds = (
                    np.array(self.theta_string.get().split(), dtype=np.float))
        new_n_thetas = self.parent.data.TC_thresholds.size

        #update the amp lines if command is given and the number didnt change
        #always draw new lines if the number changed
        if update_plot:
            if old_n_thetas == new_n_thetas:
                self.parent.plots.update_theta_lines()
            elif old_n_thetas != new_n_thetas:
                self.parent.plots.draw_theta_lines()

        # redo the idealization
        self.show_idealization()

    def get_resolution(self, update_plot=True, *args):
        """Get the resolution from the entry."""
        logging.debug(f"TC_Frame.get_resolution")

        resolution = self.res_string.get()
        if resolution:
            self.parent.data.tc_resolution = float(resolution)
        else:
            self.parent.data.tc_resolution = None

        self.show_idealization()

    def toggle_amp(self, *args):
        """Toggle showing the amplitude lines on the plot."""
        logging.debug(f"TC_Frame.toggle_amp")

        if self.parent.plots.show_amp.get()==0:
            self.get_amps(update_plot=False)
            self.amp_button.config(relief="sunken")
            self.parent.plots.show_amp.set(1)
        else:
            self.parent.plots.show_amp.set(0)
            self.amp_button.config(relief="raised")

    def toggle_tc(self, *args):
        """Toggle showing the threshold lines on the plot."""
        logging.debug(f"TC_Frame.toggle_tc")

        if self.parent.plots.show_thetas.get()==0:
            try: self.get_thresholds(update_plot=False)
            except IndexError: return
            self.tc_button.config(relief="sunken")
            self.parent.plots.show_thetas.set(1)
        else:
            self.parent.plots.show_thetas.set(0)
            self.tc_button.config(relief="raised")

    def demo_idealization(self, *args):
        """Apply the idealization and show it on the plot."""
        logging.debug(f"TC_Frame.demo_idealization")
        self.get_amps(update_plot=False)
        if self.manual_thetas:
            self.get_thresholds(update_plot=False)
        self.get_resolution(update_plot=False)
        self.show_idealization()

    def show_idealization(self, *args):
        """Apply and plot the idealization."""

        self.parent.data.idealize_episode()
        self.parent.plots.update_idealization_plot()

    def click_cancel(self):
        """Cancel button callback, removes idealizatoin."""
        logging.debug(f"TC_Frame.click_cancel")

        for series in self.parent.data.values():
            for episode in series:
                episode.idealization = None
        self.close_frame()

    def click_apply(self):
        """Apply button callback."""
        logging.debug(f"TC_Frame.click_apply")

        #when clicking 'ok' apply the idealization with the last settings
        #to the actual data in the main window
        self.get_amps(update_plot=False)
        self.get_resolution(update_plot=False)
        self.parent.data.idealize_series()
        self.close_frame()

    def close_frame(self):
        """Close frame and reset the plot."""
        logging.debug(f"TC_Frame.close_frame")

        # #unbind idealization callback from episode list
        self.parent.episodeList.episodelist.unbind('<<ListboxSelect>>',
                                                    self.eplist_track_id)
        # tkinter isn't perfect and unbinding here actually unbinds all
        # callbacks, even though it uses the id from binding a specific one,
        # therefore we have to bind the original one again
        self.parent.episodeList.episodelist.bind('<<ListboxSelect>>',
                                            self.parent.episodeList.click_list)
        # return plot to previous settings
        self.parent.plots.show_command.set(self.previous_show_command)
        self.parent.plots.show_piezo.set(self.previous_show_piezo)
        self.parent.plots.show_hist.set(self.previous_show_hist)
        # hide TC parameters
        self.parent.plots.show_thetas.set(0)
        self.parent.plots.show_amp.set(0)
        self.parent.plots.fig.canvas.mpl_disconnect(self.plot_track_cid)
        # remove reference in main window
        self.parent.tc_frame = None
        self.destroy()

    def track_cursor(self, event):
        """Track the position of the mouse cursor over the plot and if mouse 1
        is pressed adjust the nearest threshold/amplitude line by dragging the
        cursor."""

        # if statment first checks if the toolbar is currently trying to capture
        # the mouse, then if the click is a left click and whether it is
        # within the figure
        if (self.parent.plots.toolbar._active is None
            and event.button==1 and event.inaxes is not None
            ):
            y_pos = event.ydata
            # these conditionals check whether thetas and amps are displayed or
            # only one and whether or not they exist
            # first if both are shown and at least one is nonempty
            if (self.parent.plots.show_thetas.get()
                and self.parent.plots.show_amp.get()
                and self.parent.data.TC_thresholds.size
                    + self.parent.data.TC_amplitudes.size > 0
                ):
                # since one array might be empty we check both
                # if one is empty the difference to it is infinite so the other
                # gets changed
                if self.parent.data.TC_thresholds.size > 0:
                    tc_diff = np.abs(self.parent.data.TC_thresholds-y_pos)
                else:
                    tc_diff = np.inf
                if self.parent.data.TC_amplitudes.size > 0:
                    amp_diff = np.abs(self.parent.data.TC_amplitudes-y_pos)
                else:
                    amp_diff = np.inf
                # update the closest line
                if np.min(tc_diff) < np.min(amp_diff):
                    i = np.argmin(tc_diff)
                    sep = ',' if ',' in self.theta_string.get() else ' '
                    split_string = self.theta_string.get().split(sep)
                    split_string[i] = f"{y_pos:.2e}"
                    self.theta_string.set(sep.join(split_string))
                    self.manual_thetas = True
                    self.get_thresholds(update_plot=False)
                else:
                    i = np.argmin(amp_diff)
                    self.parent.data.TC_amplitudes[i] = y_pos
                    sep = ',' if ',' in self.amp_string.get() else ' '
                    split_string = self.amp_string.get().split(sep)
                    split_string[i] = f"{y_pos:.2e}"
                    self.amp_string.set(sep.join(split_string))
                    self.get_amps(update_plot=False)
            # if thresholds are shown and are nonempty
            elif (self.parent.plots.show_thetas.get()
                and self.parent.data.TC_thresholds.size > 0
                ):
                tc_diff = np.abs(self.parent.data.TC_thresholds-y_pos)
                i = np.argmin(tc_diff)
                sep = ',' if ',' in self.theta_string.get() else ' '
                split_string = self.theta_string.get().split(sep)
                split_string[i] = f"{y_pos:.2e}"
                self.theta_string.set(sep.join(split_string))
                self.get_thresholds(update_plot=False)
                self.manual_thetas = True
            # if amplitudes are shown and are nonempty
            elif (self.parent.plots.show_amp.get()
                and self.parent.data.TC_amplitudes.size > 0
                ):
                amp_diff = np.abs(self.parent.data.TC_amplitudes-y_pos)
                i = np.argmin(amp_diff)
                sep = ',' if ',' in self.amp_string.get() else ' '
                split_string = self.amp_string.get().split(sep)
                split_string[i] = f"{y_pos:.2e}"
                self.amp_string.set(sep.join(split_string))
                self.get_amps(update_plot=False)
            if not self.manual_thetas:
                self.auto_set_thetas()
            self.parent.plots.update_TC_lines(draw=False)
            self.show_idealization()
