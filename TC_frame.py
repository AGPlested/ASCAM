import tkinter as tk
from tkinter import ttk
import copy

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Cursor as PlotCursor

# import plotting
from plotting import plot_traces, plot_histogram
from recording import Recording

class TC_Frame(tk.Toplevel):
    def __init__(self, parent):
        # ttk.Frame.__init__(self, master)
        # self.master = master
        tk.Toplevel.__init__(self, parent)
        self.parent = parent #parent is main
        # self.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        # self.grid_rowconfigure(0, weight=1)
        # self.grid_columnconfigure(0, weight=1)

        self.n_episode = tk.IntVar()
        self.n_episode.set(parent.Nepisode)
        self.datakey = tk.StringVar()
        self.datakey.set(self.parent.datakey.get())
        #get a temporary copy of the Recording objec
        self.temp_data = copy.deepcopy(self.parent.data)

        self.plots = PlotFrame(self)
        self.plots.grid(row=0, column=0, rowspan=3, columnspan=3, padx=5,
                        pady=5, sticky=tk.W)
        self.plots.grid_rowconfigure(0, weight=1)
        self.plots.grid_columnconfigure(0, weight=1)

        self.show_tc = tk.IntVar()
        self.show_tc.set(1)
        self.show_amp = tk.IntVar()
        self.show_amp.set(1)

        self.thresholds = np.array([])
        self.amplitudes = np.array([])

        self.conf = ConfFrame(self)
        self.conf.grid(row=0, column=3)

        self.plots.plot()

class ConfFrame(ttk.Frame):
    def __init__(self,parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent #parent is main frame

        self.tc_amps = tk.StringVar()
        self.tc_thresholds = tk.StringVar()
        self.create_widgets()

    def get_amps(self, *args):
        if ',' in self.tc_amps.get():
            self.parent.amplitudes = np.array(self.tc_amps.get().split(','),
                                              dtype=np.float)
        else:
            self.parent.amplitudes = np.array(self.tc_amps.get().split(),
                                              dtype=np.float)
        self.apply_idealization()
        self.parent.plots.plot()

    def toggle_amp(self, *args):
        self.get_amps()
        if self.parent.show_amp.get()==0:
            self.parent.show_amp.set(1)
            self.amp_button.config(relief="sunken")
        else:
            self.parent.show_amp.set(0)
            self.amp_button.config(relief="raised")

    def get_thresholds(self, *args):
        if ',' in self.tc_amps.get():
            self.parent.thresholds = np.array(
                             self.tc_thresholds.get().split(','),dtype=np.float)
        else:
            self.parent.thresholds = np.array(self.tc_thresholds.get().split(),
                                              dtype=np.float)
        self.apply_idealization()
        self.parent.plots.plot()

    def toggle_tc(self, *args):
        self.get_thresholds()
        if self.parent.show_tc.get()==0:
            self.parent.show_tc.set(1)
            self.tc_button.config(relief="sunken")
        else:
            self.parent.show_tc.set(0)
            self.tc_button.config(relief="raised")

    def apply_idealization(self):
        self.parent.temp_data[self.parent.datakey.get()][
                   self.parent.n_episode.get()].idealize(self.parent.amplitudes,
                                                         self.parent.thresholds)
        self.parent.plots.plot()

    def create_widgets(self):
        datakey_options = self.parent.temp_data.keys()
        self.datakey_selection = tk.OptionMenu(self, self.parent.datakey, *datakey_options)
        self.datakey_selection.grid(row=0,column=0,columnspan=2,sticky=tk.N)

        episode_options = list(range(len(self.parent.temp_data[self.parent.datakey.get()])))
        self.episode_selection = tk.OptionMenu(self, self.parent.n_episode, *episode_options)
        self.episode_selection.grid(row=1,column=0,columnspan=2,sticky=tk.N)

        #entry for amplitudes
        self.amp_button = tk.Button(self, text="Amplitudes", width=12,
                                    relief="sunken", command=self.toggle_amp)
        self.amp_button.grid(row=4, column=0)
        amp_entry = ttk.Entry(self, textvariable=self.tc_amps, width=40)
        amp_entry.grid(row=4, column=1)
        amp_entry.bind('<FocusOut>', self.get_amps)
        amp_entry.bind('<Return>', self.get_amps)

        #entry for thresholds
        self.tc_button = tk.Button(self, text="Thresholds", width=12,
                                   relief="sunken", command=self.toggle_tc)
        self.tc_button.grid(row=5, column=0)
        tc_entry = ttk.Entry(self, textvariable=self.tc_thresholds, width=40)
        tc_entry.grid(row=5, column=1)
        tc_entry.bind('<FocusOut>', self.get_thresholds)
        tc_entry.bind('<Return>', self.get_thresholds)

        ttk.Button(self, text="OK", command=self.ok_click).grid(row=7)
        ttk.Button(self, text="Cancel", command=self.parent.destroy\
                   ).grid(row=7, column=1)

    def ok_click(self):
        #when clicking 'ok' apply the idealization with the last settings
        #to the actual data in the main window
        self.parent.parent.data.idealize_series(self.parent.amplitudes,
                                                self.parent.thresholds)
        self.parent.parent.datakey.set(self.parent.parent.data.currentDatakey)
        self.parent.parent.update_list()
        self.parent.parent.draw_plots()
        self.parent.destroy()

class PlotFrame(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent #parent is main frame
        #initiliaze figure
        self.fig = plt.figure(figsize=(10,5))

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        #bind matplotlib callback to canvas widget
        self.fig.canvas.callbacks.connect('motion_notify_event', self.track_cursor)

        self.toolbar = PlotToolbar(self.canvas, self)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def plot(self):
        plt.clf() #clear figure from memory

        datakey = self.parent.datakey.get()
        episode = self.parent.temp_data[datakey][self.parent.n_episode.get()]

        self.ax = self.fig.add_subplot(111)

        self.ax.plot(episode.time, episode.trace)
        if episode.idealization is not None:
            self.ax.plot(episode.time, episode.idealization, alpha=.6)

        if self.parent.show_tc.get():
            for threshold in self.parent.thresholds:
                self.ax.axhline(threshold, ls='--', c='r', alpha=0.3)
        if self.parent.show_amp.get():
            for amplitude in self.parent.amplitudes:
                self.ax.axhline(amplitude, ls='--', c='b', alpha=0.3)

        self.toolbar.update()
        self.canvas.draw() # draw plots

    def track_cursor(self, event):
        """
        Track the position of the mouse cursor over the plot and if mouse 1 is
        pressed adjust the nearest threshold/amplitude line by dragging the
        cursor.
        """
        if event.button==1 and event.inaxes is not None \
           and self.parent.thresholds.size+self.parent.amplitudes.size>0:
            y_pos = event.ydata
            if self.parent.thresholds.size>0:
                tc_diff = np.abs(self.parent.thresholds-y_pos)
            else: tc_diff = np.inf
            if self.parent.amplitudes.size>0:
                amp_diff = np.abs(self.parent.amplitudes-y_pos)
            else: amp_diff = np.inf
            if np.min(tc_diff)<np.min(amp_diff):
                i = np.argmin(tc_diff)
                self.parent.thresholds[i] = y_pos
            else:
                i = np.argmin(amp_diff)
                self.parent.amplitudes[i] = y_pos
            self.parent.conf.apply_idealization()

class PlotToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, parent):
        self.parent = parent
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
        self_zoom_out_cid = self.canvas.mpl_connect('button_press_event', self.zoom_out)
        NavigationToolbar2Tk.zoom(self)

    def zoom_out(self, event):
        """
        Zoom out in this case is done by calling `back` on right-click to
        restore the previous view (i.e. undo last zoom)
        """
        if self._active=='ZOOM' and event.button==3:
            NavigationToolbar2Tk.back(self)
