import tkinter as tk
from tkinter import ttk
import logging

import numpy as np

from table_frame import TableFrame

class TC_Frame(ttk.Frame):
    def __init__(self, parent):
        logging.debug("being TC_Frame.__init__")
        ttk.Frame.__init__(self, parent)
        self.parent = parent  # parent is main

        # TODO implement a callback for switching between different series
        # while in idealization mode, keeping track of different idealization\
        # parameters for each series

        # variables for entry
        self.amp_string = tk.StringVar()  # string holding the amplitudes
        self.theta_string = tk.StringVar()  # string holding the thresholds
        self.res_string = tk.StringVar()  # string holding the resolution
        self.interpolate = tk.IntVar()  # bool for interpolating
        self.interpolation_factor = tk.StringVar()

        # if idealization has already been performed store the parameters
        # to recreate if cancel is clicked
        self.previous_params = dict()
        if self.parent.data.series.is_idealized:
            logging.debug(
                f"Series has been idealized, setting parameters\n"
                f"TC amplitudes = '{self.parent.data.tc_amplitudes}'\n"
                f"TC thresholds = '{self.parent.data.tc_thresholds}'\n"
                f"Resolution = '{self.parent.data.tc_resolution}'\n"
                f"interpolation_factor = '{self.parent.data.interpolation_factor}'"
            )
            self.previous_params = {
                self.parent.datakey.get(): (
                    self.parent.data.tc_amplitudes,
                    self.parent.data.tc_thresholds,
                    self.parent.data.tc_resolution,
                    self.parent.data.interpolation_factor,
                )
            }
            self.array_into_tkstring(
                self.parent.data.series.tc_amplitudes, self.amp_string
            )
            if self.parent.data.tc_thresholds is not None:
                self.array_into_tkstring(
                    self.parent.data.series.tc_thresholds, self.theta_string
                )
                self.manual_thetas = True
            if self.parent.data.tc_resolution is not None:
                self.res_string.set(str(self.parent.data.tc_resolution))
            if self.parent.data.interpolation_factor is not None:
                self.interpolation_factor.set(
                    str(self.parent.data.interpolation_factor)
                )
        else:
            self.amp_string.set("0")
            self.manual_thetas = False

        # variables for moving the lines on the plots with the mouse
        self.tracking_on = True
        self.plot_track_cid = self.parent.plots.fig.canvas.mpl_connect(
            "motion_notify_event", self.track_cursor
        )
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
            "<<ListboxSelect>>", self.apply_and_show_idealization, add="+"
        )

        self.create_widgets()
        logging.debug("end TC_Frame.__init__")

    @property
    def show_amp(self):
        return self.parent.plots.show_amp.get()

    @show_amp.setter
    def show_amp(self, val):
        val = 1 if val else 0
        self.parent.plots.show_amp.set(val)

    @property
    def show_thetas(self):
        return self.parent.plots.show_thetas.get()

    @show_thetas.setter
    def show_thetas(self, val):
        val = 1 if val else 0
        self.parent.plots.show_thetas.set(val)

    def create_widgets(self):
        """Create the tkiner widgets in this frame."""

        # button to toggle display of amplitude lines on plot
        self.amp_checkbox = ttk.Checkbutton(
            self,
            variable=self.parent.plots.show_amp,
            command=lambda *args: [self.get_amps(), self.apply_and_show_idealization()],
        )
        self.amp_checkbox.grid(row=4, column=0, columnspan=1, padx=5, pady=5)

        ttk.Label(self, text=f"Amplitudes [{self.parent.data.trace_unit}]").grid(
            row=4, column=1, columnspan=3, padx=5, pady=5
        )

        # entry for amplitudes
        amp_entry = ttk.Entry(self, textvariable=self.amp_string, width=40)
        amp_entry.grid(row=5, column=0, columnspan=4, padx=5, pady=5)
        amp_entry.bind(
            "<Return>",
            lambda *args: (
                None if self.show_amp else self.toggle_amp(),
                self.get_amps(),
                self.apply_and_show_idealization(),
            ),
        )

        # entry for thresholds
        self.theta_checkbox = ttk.Checkbutton(
            self,
            variable=self.parent.plots.show_thetas,
            command=lambda *args: [
                self.get_thresholds(),
                self.apply_and_show_idealization(),
            ],
        )
        self.theta_checkbox.grid(row=6, column=0, columnspan=1, padx=5, pady=5)

        ttk.Label(self, text=f"Thresholds [{self.parent.data.trace_unit}]").grid(
            row=6, column=1, columnspan=3, padx=5, pady=5
        )
        theta_entry = ttk.Entry(self, textvariable=self.theta_string, width=40)
        theta_entry.grid(row=7, column=0, columnspan=4, padx=5, pady=5)
        theta_entry.bind(
            "<Return>",
            lambda *args: (
                self.toggle_tc() if not self.show_thetas else None,
                self.get_thresholds(),
                self.apply_and_show_idealization(),
            ),
        )

        # resolution
        self.res_checkbox = ttk.Checkbutton(
            self,
            state=tk.DISABLED
            # variable=self.parent.plots.show_thetas,
            # command=lambda *args: [self.get_thresholds(), self.apply_and_show_idealization()],
        )
        self.res_checkbox.grid(row=8, column=0, columnspan=1, padx=5, pady=5)

        ttk.Label(
            self, text=f"Resolution " f"[{self.parent.data.episode.time_unit}]"
        ).grid(row=8, column=1, columnspan=3, padx=5, pady=5)
        res_entry = ttk.Entry(self, textvariable=self.res_string, width=40)
        res_entry.grid(row=9, column=0, columnspan=4, padx=5, pady=5)
        res_entry.bind(
            "<Return>",
            lambda *args: (self.get_resolution, self.apply_and_show_idealization()),
        )

        # interprolation
        self.intrp_checkbox = ttk.Checkbutton(
            self,
            variable=self.interpolate,
            command=lambda *args: (
                self.get_intrp_factor(),
                self.apply_and_show_idealization(),
            ),
        )
        self.intrp_checkbox.grid(row=11, column=0, columnspan=1, padx=5, pady=5)

        ttk.Label(self, text=f"Interpolation").grid(
            row=11, column=1, columnspan=3, pady=5, padx=5
        )

        intrp_entry = ttk.Entry(self, textvariable=self.interpolation_factor, width=40)
        intrp_entry.grid(row=12, column=0, columnspan=4, padx=5, pady=5)
        intrp_entry.bind(
            "<Return>",
            lambda *args: (
                self.toggle_intrp() if not self.interpolate.get() else None,
                self.get_intrp_factor(),
                self.apply_and_show_idealization(),
            ),
        )

        # show button
        ttk.Button(self, text="Show", command=self.demo_idealization).grid(
            row=13, columnspan=4, padx=5, pady=5
        )

        # frame closing buttons
        ttk.Button(self, text="Apply and close", command=self.click_apply).grid(
            row=14, columnspan=2, padx=5, pady=5
        )
        ttk.Button(self, text="Cancel", command=self.click_cancel).grid(
            row=14, column=3, columnspan=2, padx=5, pady=5
        )

        self.table_frame = TableFrame(self)
        self.table_frame.grid(row=15, columnspan=4)

    def get_amps(self, update_plot=True, *args):
        """Get the amplitudes from the entry field.

        Also updates the idealization and if the number of amplitudes changes
        sets the thresholds automatically."""

        logging.debug(f"TC_Frame.get_amps")

        old_n_amps = self.parent.data.tc_amplitudes.size
        self.parent.data.tc_amplitudes = self.tk_string_to_array(self.amp_string)
        new_n_amps = self.parent.data.tc_amplitudes.size

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

    def toggle_manual_thetas(self, *args):
        """Toggle manually specifying thresholds."""

        logging.debug(f"toggle_manual_thetas")

        # check if theta string is empty or conists only of whitespaces
        if not self.theta_string.get().strip():
            self.manual_thetas = False
            self.auto_set_thetas()
            self.parent.plots.update_theta_lines()
        else:
            self.manual_thetas = True

    def auto_set_thetas(self):
        """Automatically set the thresholds."""

        logging.debug(f"auto_set_thetas")

        # automatically set the thresholds to the midpoint between the amps
        self.parent.data.tc_thresholds = (
            self.parent.data.tc_amplitudes[1:] + self.parent.data.tc_amplitudes[:-1]
        ) / 2
        # seperate the threshold string the same way as the amp string
        sep = ", " if "," in self.amp_string.get() else " "
        self.array_into_tkstring(
            self.parent.data.tc_thresholds, self.theta_string, sep=sep
        )

    def get_thresholds(self, update_plot=True, *args):
        """Get the thresholds from the entry field."""
        logging.debug(f"TC_Frame.get_thresholds")

        old_n_thetas = self.parent.data.tc_thresholds.size
        self.parent.data.tc_thresholds = self.tk_string_to_array(self.theta_string)
        new_n_thetas = self.parent.data.tc_thresholds.size

        # update the amp lines if command is given and the number didnt change
        # always draw new lines if the number changed
        if update_plot:
            if old_n_thetas == new_n_thetas:
                self.parent.plots.update_theta_lines()
            elif old_n_thetas != new_n_thetas:
                self.parent.plots.draw_theta_lines()

    def get_resolution(self, update_plot=True, *args):
        """Get the resolution from the entry."""
        logging.debug(f"TC_Frame.get_resolution")

        resolution = self.res_string.get()
        if resolution:
            self.parent.data.tc_resolution = float(resolution)
        else:
            self.parent.data.tc_resolution = None

    def get_intrp_factor(self, *args):
        """Get the interpolation_factor from the entry."""
        logging.debug(f"TC_Frame.get_intrp_factor")
        self.parent.data.interpolation_factor = int(self.interpolation_factor.get())

    def toggle_intrp(self, *args):
        """Toggle the interpolation, turning it off sets the factor 1."""
        logging.debug(f"TC_Frame.toggle_intrp")

        if self.interpolate.get():
            self.interpolate.set(0)
            self.parent.data.interpolation_factor = 1
        else:
            self.interpolate.set(1)

    def toggle_amp(self, *args):
        logging.debug(f"TC_Frame.toggle_amp")

        if self.show_amp:
            self.show_amp = False
        else:
            self.show_amp = True

    def toggle_tc(self, *args):
        """Toggle showing the threshold lines on the plot."""
        logging.debug(f"TC_Frame.toggle_tc")

        if not self.parent.plots.show_thetas.get():
            self.parent.plots.show_thetas.set(1)
        else:
            self.parent.plots.show_thetas.set(0)

    def update_events_table(self, *args):
        logging.debug("updating events table")

        events = self.parent.data.episode.get_events()
        self.table_frame.fill_table(events)

    def demo_idealization(self, *args):
        """Apply the idealization and show it on the plot."""
        logging.debug(f"TC_Frame.demo_idealization")
        self.get_amps(update_plot=False)
        if self.manual_thetas:
            self.get_thresholds(update_plot=False)
        self.get_resolution(update_plot=False)
        self.apply_and_show_idealization()
        self.update_events_table()

    def apply_and_show_idealization(self, *args):
        """Apply and plot the idealization."""

        logging.debug("apply and show idealization")
        self.parent.data.idealize_episode()
        if self.interpolation_factor.get():
            self.parent.plots.update_current_plot()
        self.parent.plots.update_idealization_plot()

    def click_cancel(self):
        """Cancel button callback, removes idealization."""
        logging.debug(f"TC_Frame.click_cancel")
        for datakey, series in self.parent.data.items():
            # check if the series was previously idealized, if so repeat the
            # idealization with previously used parameters
            amps, thetas, res, intrp = self.previous_params.get(
                datakey, (None, None, None, None)
            )
            self.parent.data.tc_amplitudes = amps
            self.parent.data.tc_thresholds = thetas
            self.parent.data.tc_resolution = res
            self.parent.data.interpolation_factor = intrp
            if (amps is not None) and (amps.size not in (0, 1)):
                self.parent.data.idealize_series()
            else:
                for episode in series:
                    episode.idealization = None
        self.close_frame()

    def click_apply(self):
        """Apply button callback."""
        logging.debug(f"TC_Frame.click_apply")

        # when clicking 'ok' apply the idealization with the last settings
        # to the actual data in the main window
        self.get_amps(update_plot=False)
        if self.manual_thetas:
            self.get_thresholds(update_plot=False)
        self.get_resolution(update_plot=False)
        self.parent.data.idealize_series()
        self.close_frame()

    def close_frame(self):
        """Close frame and reset the plot."""
        logging.debug(f"TC_Frame.close_frame")

        # #unbind idealization callback from episode list
        self.parent.episodeList.episodelist.unbind(
            "<<ListboxSelect>>", self.eplist_track_id
        )
        # tkinter isn't perfect and unbinding here actually unbinds all
        # callbacks, even though it uses the id from binding a specific one,
        # therefore we have to bind the original one again
        self.parent.episodeList.episodelist.bind(
            "<<ListboxSelect>>", self.parent.episodeList.click_list
        )
        # return plot to previous settings
        self.parent.plots.show_command.set(self.previous_show_command)
        self.parent.plots.show_piezo.set(self.previous_show_piezo)
        self.parent.plots.show_hist.set(self.previous_show_hist)
        # hide TC parameters
        self.show_thetas = False
        self.show_amp = False
        self.parent.plots.fig.canvas.mpl_disconnect(self.plot_track_cid)
        # remove reference in main window
        del self.parent.tc_frame
        self.destroy()

    def track_cursor(self, event):
        """Track the position of the mouse cursor over the plot and if mouse 1
        is pressed adjust the nearest threshold/amplitude line by dragging the
        cursor."""

        # if statment first checks if the toolbar is currently trying to capture
        # the mouse, then if the click is a left click and whether it is
        # within the figure
        if (
            self.parent.plots.toolbar._active is None
            and event.button == 1
            and event.inaxes is not None
        ):
            y_pos = event.ydata
            # these conditionals check whether thetas and amps are displayed or
            # only one and whether or not they exist
            # first if both are shown and at least one is nonempty
            if self.parent.data.tc_thresholds.size > 0:
                tc_diff = np.abs(self.parent.data.tc_thresholds - y_pos)
            else:
                tc_diff = np.inf
            if self.parent.data.tc_amplitudes.size > 0:
                amp_diff = np.abs(self.parent.data.tc_amplitudes - y_pos)
            else:
                amp_diff = np.inf

            if (
                np.min(tc_diff) < np.min(amp_diff)
                and self.parent.plots.show_thetas.get()
            ):
                self.update_number_in_string(y_pos, self.theta_string)
                self.get_thresholds(update_plot=False)
                self.manual_thetas = True
            elif self.show_amp:
                self.update_number_in_string(y_pos, self.amp_string)
                self.get_amps(update_plot=False)
                if not self.manual_thetas:
                    self.auto_set_thetas()
            self.parent.plots.update_TC_lines(draw=False)
            self.apply_and_show_idealization()

    @staticmethod
    def update_number_in_string(new_val, tk_string):
        """Update a list of floats held in a TK.StringVar so that the value
        closest to new_val becomes new_val."""
        array = TC_Frame.tk_string_to_array(tk_string)
        differences = np.abs(array - new_val)
        i = np.argmin(differences)
        sep = "," if "," in tk_string.get() else " "
        split_string = tk_string.get().split(sep)
        split_string[i] = f"{new_val:.2f}"
        tk_string.set(sep.join(split_string))

    @staticmethod
    def tk_string_to_array(tk_string):
        """Take a TK.StringVar containing floats and return an numpy array."""

        if "," in tk_string.get():
            array = np.array(tk_string.get().split(","), dtype=np.float)
        else:
            array = np.array(tk_string.get().split(), dtype=np.float)
        return array

    @staticmethod
    def array_into_tkstring(array, tk_string, sep=" "):
        """Take a numpy array and enter it in to a TK.StringVar as a list of
        values seperated by commas."""

        tk_string.set(sep.join(np.char.mod("%.2f", array)))
