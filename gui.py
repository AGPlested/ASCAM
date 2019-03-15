import logging
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename

import numpy as np

from plotframe import PlotFrame
from tools import stringList_parser, parse_filename
from recording import Recording
from TCframe import TC_Frame
from firstactivationframe import FirstActivationFrame
from episode import Episode
from constants import DEFAULT_GAUSS_CUTOFF_FREQ


class GUI(ttk.Frame):
    """GUI frame for ASCAM.
    All the variables and objects are stored as attributes of this
    object to make refering them uniform.
    All other widgets will be children of this frame.
    It is easier to make to represent floats and integers using tk.StringVar
    because then they can be entered in entry fields without problems."""

    @classmethod
    def run(cls, test=False):
        """
        Call this method to start the GUI
        Initializes root tk window and GUI main frame
        Parameters:
            test [bool] - if true load the data in
                          'ASCAM/data/180426 000 Copy Export.mat'
        """
        logging.info("Starting ASCAM GUI")
        root = tk.Tk()
        root.protocol('WM_DELETE_WINDOW', quit)
        root.title("ASCAM")
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        cls(root, test)
        root.mainloop()

    def __init__(self, master, test):
        logging.debug("begin GUI.__init__")
        ttk.Frame.__init__(self, master)
        self.master = master
        # which window system is being used
        self.window_system = master.tk.call('tk', 'windowingsystem')
        logging.debug("window system is {}".format(self.window_system))

        self._init_fileparams()
        self._init_data_params()

        # placeholders for subframes
        # set to None so existence can be checked is `is not None`
        self.plots = None
        self.episodeList = None
        self.listSelection = None
        self.displayFrame = None
        self.menuBar = None
        self.fa_frame = None
        self.tc_frame = None

        # bind window name updating
        self.filename.trace("w",
            lambda *args: self.master.title(f"ASCAM - {self.filename.get()}"))

        if test:
            self.data = Recording()
        else:
            self.data = Recording('')

        # datakey of the current displayed data
        self.datakey = tk.StringVar()
        self.datakey.set(self.data.currentDatakey)
        self.datakey.trace('w', self.change_current_datakey)
        # episode number of the currently displayed episode
        self.n_episode = tk.IntVar()
        self.n_episode.trace('w', self.change_episode)
        self.n_episode.set(0)

        self.create_widgets()
        self.configure_grid()

        if test:
            #basic set up
            self.data.baseline_correction()
            self.data.gauss_filter_series(1e3)
            self.update_all()
            self.datakey.set('BC_GFILTER1000.0_')
            self.plots.plot(True)
            #test idealization
            # self.menuBar.launch_idealization()
            # self.tc_frame.amp_string.set('0 -1')

            #test first_activation
            # self.menuBar.launch_fa_mode()

        logging.debug(f"end GUI.__init__")

    def _init_data_params(self):
        # parameters of the data
        self.sampling_rate = tk.StringVar()
        self.time_input_unit = tk.StringVar()
        self.trace_input_unit = tk.StringVar()
        self.piezo_input_unit = tk.StringVar()
        self.command_input_unit = tk.StringVar()
        # set defaults
        self.time_input_unit.set('s')
        self.trace_input_unit.set('A')
        self.piezo_input_unit.set('V')
        self.command_input_unit.set('V')

    def _init_fileparams(self):
        """initialize parameters for loading of a file
        """
        self.filenamefull = tk.StringVar()
        self.filename = tk.StringVar()
        self.path = tk.StringVar()
        self.filetypefull = tk.StringVar()
        self.filetype = tk.StringVar()
        #old params that were used for binary files
        self.headerlength = tk.StringVar()
        self.datatype = tk.StringVar()

    def create_widgets(self):
        """
        Create the contents of the main window.
        """
        logging.debug("GUI.create_widgets")
        self.plots = PlotFrame(self)
        self.episodeList = EpisodeList(self)
        self.listSelection = ListSelection(self)
        # self.displayFrame = DiplayFrame(self)
        self.menuBar = MenuBar(self)

    def configure_grid(self):
        """
        Geometry management of the elements in the main window.
        """
        logging.debug("GUI.configure_grid")
        # Place the main window in the root window
        self.grid(sticky='NESW')
        # First row
        self.listSelection.grid(row=1, column=4, padx=5, pady=5,
                                sticky=tk.N)
        self.grid_rowconfigure(0, weight=0)
        # Second row
        self.plots.grid(row=1, column=1, rowspan=3, columnspan=3, padx=5,
                        pady=5, sticky='NEWS')
        # self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Third row
        self.episodeList.grid(row=2, column=4, sticky='NS')
        self.grid_rowconfigure(2, weight=1)

    def set_filename(self, filepath):
        """Take a path and set filename and type variables.
        """
        self.filenamefull.set(filepath)
        filetype, path, filetypefull, filename = parse_filename(filepath)
        self.filename.set(filename)
        self.path.set(path)
        self.filetype.set(filetype)
        self.filetypefull.set(filetypefull)

    def load_recording(self):
        """ Take a recording object and load it into the GUI."""
        logging.debug("""load_recording""")

        # set ASCAM title
        self.master.title("ASCAM - "+self.filename.get())
        self.data = Recording.from_file(
                              self.filenamefull.get(),
                              sampling_rate=self.sampling_rate.get(),
                              piezo_unit=self.piezo_input_unit.get(),
                              time_unit=self.time_input_unit.get(),
                              trace_unit=self.trace_input_unit.get(),
                              command_unit=self.command_input_unit.get())
        self.datakey.set(self.data.currentDatakey)
        # recreate user defined episodelists
        for name, (_, color, key) in self.data.lists.items():
            logging.debug("""found list {}, color: {}, key: {}"""
                          "".format(name, color, key))
            self.listSelection.create_checkbox(name=name, key=key, color=color)
            self.update_all()

    def change_current_datakey(self, *args, **kwargs):
        """This function changes the current datakey in the recording object,
        which is the one that determines what is filtered etc."""
        logging.debug(f"GUI.change_current_datakey")

        self.data.currentDatakey = self.datakey.get()
        self.episodeList.create_list()
        self.plots.plot(new=True)
        self.episodeList.episodelist.select_set(self.n_episode.get())

    def change_episode(self, *args):

        logging.debug(f"gui.change_episode")
        self.data.n_episode = self.n_episode.get()
        if self.episodeList is not None:
            self.episodeList.episodelist.selection_clear(0, tk.END)
            self.episodeList.episodelist.selection_set(self.n_episode.get())
            if self.plots is not None: self.plots.plot()

    def update_all(self, *args):
        """Use to update all data dependent widgets in the main window"""

        logging.debug("""gui.update_all""")

        self.update_episodelist()
        self.draw_plots()

    def draw_plots(self, new=False, *args):
        """Plot the current episode"""

        logging.debug(f"gui.draw_plots")

        self.plots.plot(new)

    def update_episodelist(self):
        """Update the list of episodes by recreating them"""

        self.episodeList.create_dropdownmenu()
        self.episodeList.create_list()

    def quit(self):
        """Close ASCAM completely"""

        logging.info('exiting ASCAM')
        self.master.destroy()
        self.master.quit()

class DiplayFrame(ttk.Frame):
    """
    This frame is used to display information.
    Currently this means only the mean and standard deviation of the command
    voltage.
    """
    def __init__(self, parent):
        logging.debug(f"begin DisplayFrame.__init__")
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.show_command_stats()
        logging.debug(f"end DisplayFrame.__init__")

    def update(self):
        """
        Update all contents of the Display frame
        """
        logging.debug(f"DisplayFrame.update")
        # self.show_filename()
        self.show_command_stats()

    def show_command_stats(self):
        logging.debug(f"DisplayFrame.show_command_stats")
        if self.parent.data.has_command:
            mean, std = self.parent.data.episode.get_command_stats()
            command_stats ="Command Voltage = "
            command_stats+="{:2f} +/- {:2f}".format(mean,std)
            command_stats+=self.parent.data.command_unit
            ttk.Label(self, text=command_stats).grid(row=4, column=0)
        else:
            logging.info("no command voltage found")

class MenuBar(tk.Menu):
    def __init__(self, parent):
        logging.debug(f"begin MenuBar.__init__")
        self.parent = parent #parent is main window
        tk.Menu.__init__(self, parent.master, tearoff=0)
        self.parent.master.config(menu=self)

        # menu holding all the cascading options
        # `tearoff` is needed because otherwise there is a seperator on top the
        # menu
        self.file_menu = tk.Menu(self, tearoff=0)
        self.analysis_menu = tk.Menu(self, tearoff=0)
        self.plot_menu = tk.Menu(self, tearoff=0)
        self.histogram_menu = tk.Menu(self, tearoff=0)

        self.create_file_cascade()
        self.create_analysis_cascade()
        self.create_plot_cascade()
        self.create_histogram_cascade()

        # the code below is needed to make the menuBar responsive on Mac OS
        # apple uses window system aqua
        if parent.window_system=='aqua':
            logging.info("trying to make the menu work on Mac")
            appmenu = tk.Menu(self, name='apple')
            self.add_cascade(menu=appmenu)
            appmenu.add_command(label='About My Application')
            appmenu.add_separator()
            self.parent.master['menu'] = self
        logging.debug(f"end MenuBar.__init__")

    def create_plot_cascade(self):
        logging.debug(f"MenuBar.create_plot_cascade")
        self.add_cascade(label='Plot', menu=self.plot_menu)
        self.plot_menu.add_command(label="Set t_zero",
                                   command=lambda: ZeroTFrame(self.parent))
        self.plot_menu.add_separator()
        self.plot_menu.add_checkbutton(label="Show piezo voltage",
                                   variable=self.parent.plots.show_piezo)
        self.plot_menu.add_checkbutton(label="Show command voltage",
                                   variable=self.parent.plots.show_command)
        self.plot_menu.add_checkbutton(label="Show idealization",
                                   variable=self.parent.plots.show_idealization)
        self.plot_menu.add_checkbutton(label="Show first activation",
                                   variable=self.parent.plots.show_fa_mark)

    def create_histogram_cascade(self):
        logging.debug(f"MenuBar.create_histogram_cascade")
        self.add_cascade(label='Histogram', menu=self.histogram_menu)
        self.histogram_menu.add_checkbutton(label="Show single episode",
                                    variable=self.parent.plots.show_hist_single)
        self.histogram_menu.add_checkbutton(label="Density",
                                        variable=self.parent.plots.hist_density)
        self.histogram_menu.add_separator()
        self.histogram_menu.add_command(label="Configuration",
                                        command=lambda:\
                                        HistogramConfiguration(self.parent))

    def create_file_cascade(self):
        """
        Create all the options associated with files in the menu (e.g. 'open',
        'export' and 'save')
        """
        logging.debug(f"MenuBar.create_file_cascade")
        self.add_cascade(label="File", menu=self.file_menu)
        # Submenus under 'File'
        self.file_menu.add_command(label="Open File", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_to_file)
        self.file_menu.add_command(label="Export", command=lambda:
                                   ExportFileDialog(self.parent))
        self.file_menu.add_command(label="Export Idealization",
                                   command=self.export_idealization)
        self.file_menu.add_command(label="Export Events",
                                   command=self.export_events)
        self.file_menu.add_command(label="Export First Activation",
                                   command=self.export_fa)
        self.file_menu.add_command(label="Quit",command=self.parent.master.quit)

    def create_analysis_cascade(self):
        logging.debug(f"MenuBar.create_analysis_cascade")
        self.add_cascade(label='Analysis', menu=self.analysis_menu)
        self.analysis_menu.add_command(label="Baseline",
                                       command=lambda: BaselineFrame(self))
        self.analysis_menu.add_command(label="Filter",
                                       command=lambda: FilterFrame(self.parent))
        self.analysis_menu.add_command(label="Idealize",
                                       command=self.launch_idealization)
        self.analysis_menu.add_command(label="First Activation",
                                       command=self.launch_fa_mode)

    def open_file(self):
        logging.debug(f"MenuBar.open_file")
        # open the dialog for loading a single file
        filename = askopenfilename()
        logging.info(f"selected file: '{filename}'")
        if filename is not None:
            self.parent.set_filename(filename)
            OpenFileDialog(self.parent)
        else:
            logging.info("User pressed 'Cancel'")

    def save_to_file(self):
        logging.debug(f"MenuBar.save_to_file")
        # save the current recording object with all its attributes as a
        # pickle file
        filepath = asksaveasfilename()
        if isinstance(filepath, str):
            self.parent.data.save_to_pickle(filepath)
        else:
            logging.info("User pressed 'Cancel'")

    def export_events(self):
        logging.debug(f"MenuBar.export_events")
        filepath = asksaveasfilename()
        if isinstance(filepath, str):
            self.parent.data.export_events(filepath)
        else:
            logging.info("User pressed 'Cancel'")

    def export_idealization(self):
        logging.debug(f"MenuBar.export_idealization")
        filepath = asksaveasfilename()
        if isinstance(filepath, str):
            self.parent.data.export_idealization(filepath)
        else:
            logging.info("User pressed 'Cancel'")

    def export_fa(self):
        logging.debug(f"MenuBar.export_fa")
        filepath = asksaveasfilename()
        if isinstance(filepath, str):
            self.parent.data.export_first_activation(filepath)
        else:
            logging.info("User pressed 'Cancel'")

    def launch_idealization(self):
        logging.debug(f"MenuBar.launch_idealization")
        self.parent.tc_frame = TC_Frame(self.parent)
        self.parent.tc_frame.grid(row=1, column=0)

    def launch_fa_mode(self):
        self.parent.fa_frame = FirstActivationFrame(self.parent)
        self.parent.fa_frame.grid(row=5, column=1, columnspan=3, padx=5, pady=5)


class ExportIdDialog(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent #parent is main window

        self.filename = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self,text='Filename: ').grid(row=0)
        ttk.Entry(self, textvariable=self.filename, width=20)\
            .grid(row=0,column=1)
        ttk.Button(self, text='OK', command=self.ok_click).grid(row=1)
        ttk.Button(self,text="Cancel", command=self.destroy)\
            .grid(row=1,column=1)

    def ok_click(self):

        lists_to_save = list()
        for (listname, var) in self.lists_to_export:
            if var.get(): lists_to_save.append(listname)
        filepath = asksaveasfilename()
        if filepath is not None:
            self.parent.data.export_idealization(filepath=filepath,
                                           datakey=self.datakey.get())
        else:
            logging.info("User pressed 'Cancel'")
        self.destroy()

class ZeroTFrame(tk.Toplevel):
    """Dialog for entering the offset for the time axis in plots"""
    def __init__(self, parent):
        logging.debug(f"begin ZeroTFrame.__init__")
        tk.Toplevel.__init__(self, parent)
        self.parent = parent #parent is main window
        self.title("Set time offset")
        entry = ttk.Entry(self, textvariable=self.parent.plot_t_zero, width=7)
        entry.grid(row=0, column=0, columnspan=3)
        entry.focus()
        ttk.Button(self, text="OK", command=self.ok_click\
                   ).grid(row=1, column=0, columnspan=3)
        logging.debug(f"end ZeroTFrame.__init__")

    def ok_click(self):
        logging.debug("ZeroTFrame.ok_click")
        self.parent.draw_plots()
        self.destroy()


class FilterFrame(tk.Toplevel):
    """Dialog to enter filtering parameters"""

    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        logging.debug(f"begin FilterFrame.__init__")
        self.parent = parent  # parent is main
        self.title("Filter")
        # filterframe variables
        self.filter_selection = tk.StringVar()
        self.filter_selection.set('Gaussian')
        self.filter_selection.trace("w", self.create_entry_frame)
        self.entry_frame = ttk.Frame()
        # paramters for gaussian filter
        self.gaussian_fc = tk.StringVar()
        self.gaussian_fc.set(str(DEFAULT_GAUSS_CUTOFF_FREQ))
        # parameters for Chung Kennedy filter
        self.weight_exponent = tk.StringVar()
        self.lengths_predictors = tk.StringVar()
        self.weight_window = tk.StringVar()
        self.ap_f_weights = tk.StringVar()
        self.ap_b_weights = tk.StringVar()

        self.create_widgets()
        self.create_entry_frame()
        logging.debug(f"end FilterFrame.__init__")

    def create_widgets(self):
        """Create the dropdown menu from which to choose the type of filter
        placeholder frame for entry fields
        and 'ok' and 'cancel' buttons."""

        logging.debug(f"FilterFrame.create_widgets")
        logging.debug("creating dropdown menu for filter selection")
        listOptions = ['Gaussian', 'Chung-Kennedy']
        self.menu = tk.OptionMenu(self, self.filter_selection, *listOptions)
        self.menu.grid(row=0, column=0, columnspan=2, sticky=tk.N)

        ttk.Button(self, text="OK", command=self.ok_click).grid(row=5)
        ttk.Button(self, text="Cancel", command=self.destroy\
                   ).grid(row=5, column=1)

    def create_entry_frame(self,*args,**kwargs):
        """Create a frame for the entry of the filter parameters."""

        logging.debug(f"FilterFrame.create_entry_frame")
        logging.debug(f"filter_selection is {self.filter_selection.get()}")
        self.entry_frame.destroy()
        self.entry_frame = ttk.Frame(self)
        self.entry_frame.grid(row=1, column=0, columnspan=2)
        if self.filter_selection.get()=='Gaussian':
            ttk.Label(self.entry_frame, text="Frequency [Hz]"\
                      ).grid(row=0, column=0)
            ttk.Entry(self.entry_frame, textvariable=self.gaussian_fc, width=7\
                      ).grid(row=0, column=1)

        elif self.filter_selection.get()=='Chung-Kennedy':
            ttk.Label(self.entry_frame, text="Widths of predictors"\
                      ).grid(row=0, column=0)
            ttk.Entry(self.entry_frame, textvariable=self.lengths_predictors,
                      width=20).grid(row=0, column=1)
            ttk.Label(self.entry_frame, text="Weight exponent (p)"\
                      ).grid(row=1, column=0)
            ttk.Entry(self.entry_frame, textvariable=self.weight_exponent,
                      width=7).grid(row=1, column=1)
            ttk.Label(self.entry_frame, text="weight window (M)"\
                      ).grid(row=2, column=0)
            ttk.Entry(self.entry_frame, textvariable=self.weight_window,
                      width=7).grid(row=2, column=1)
            ttk.Label(self.entry_frame, text="forward pi"\
                      ).grid(row=3, column=0)
            ttk.Entry(self.entry_frame, textvariable=self.ap_f_weights,
                      width=7).grid(row=3, column=1)
            ttk.Label(self.entry_frame, text="backward pi"\
                      ).grid(row=4, column=0)
            ttk.Entry(self.entry_frame, textvariable=self.ap_b_weights,
                      width=7).grid(row=4, column=1)

    def filter_series(self):
        logging.debug(f'FilterFrame.filter_series')
        logging.debug(f"filter_selection is {self.filter_selection.get()}")
        if self.filter_selection.get() == "Gaussian":
            # convert textvar to float
            cutoffFrequency = float(self.gaussian_fc.get())
            logging.info("filter frequency is {}".format(cutoffFrequency))
            self.parent.data.gauss_filter_series(cutoffFrequency)
            self.parent.datakey.set(self.parent.data.currentDatakey)
            self.parent.update_episodelist()
            self.parent.draw_plots()
        elif self.filter_selection.get() == "Chung-Kennedy":
            if self.ap_f_weights:
                ap_f = [int(x) for x in self.ap_f_weights.get().split()]
            else:
                ap_f = False
            if self.ap_b_weights:
                ap_b = [int(x) for x in self.ap_b_weights.get().split()]
            else:
                ap_b = False
            self.parent.data.CK_filter_series(
                       [int(x) for x in self.lengths_predictors.get().split()],
                       int(self.weight_exponent.get()),
                       int(self.weight_window.get()),
                       ap_b, ap_f)
            self.parent.datakey.set(self.parent.data.currentDatakey)
            self.parent.update_episodelist()
            self.parent.draw_plots()

    def ok_click(self):
        logging.debug(f"FilterFrame.ok_click")
        if self.filter_selection.get():
            self.filter_series()
        self.destroy()

class ExportFileDialog(tk.Toplevel):
    def __init__(self, parent):
        logging.debug(f"begin ExportFileDialog.__init__")
        tk.Toplevel.__init__(self,parent)
        self.parent = parent #parent should be main window

        #export parameters
        self.save_piezo = tk.IntVar()
        self.save_piezo.set(0)
        self.save_command = tk.IntVar()
        self.save_command.set(0)
        self.datakey = tk.StringVar()
        self.datakey.set('raw_')
        self.lists_to_export = list()

        self.create_widgets()
        logging.debug(f"end ExportFileDialog.__init__")


    def create_widgets(self):
        #first row - select the series
        ttk.Label(self,text='Select series: ')
        self.menu = tk.OptionMenu(self, self.datakey, *self.parent.data.keys())
        self.menu.grid(row=1,column=1,columnspan=3)
        #second row - save piezo and command?
        ttk.Label(self, text="Piezo").grid(row=2, column=0)
        ttk.Checkbutton(self, variable=self.save_piezo).grid(row=2, column=1)
        ttk.Label(self, text="Command").grid(row=2, column=3)
        ttk.Checkbutton(self, variable=self.save_command).grid(row=2, column=4)

        #third to end which lists to save?
        row_num = 3
        for list_name in self.parent.data.lists.keys():
            var = tk.IntVar()
            var.set(1) if list_name=='all' else var.set(0)
            ttk.Label(self, text=list_name).grid(row=row_num,column=1)
            ttk.Checkbutton(self, variable=var).grid(row=row_num,column=2)
            self.lists_to_export.append((list_name,var))
            row_num+=1

        #last row - save and cancel button
        save_button = ttk.Button(self, text="Save", command=self.save)
        save_button.grid(row=row_num, column=0)
        cancel_button = ttk.Button(self, text="Cancel", command=self.cancel)
        cancel_button.grid(row=row_num, column=2)

    def save(self):
        lists_to_save = list()
        for (listname, var) in self.lists_to_export:
            if var.get(): lists_to_save.append(listname)
        filepath = asksaveasfilename()
        if filepath is not None:
            self.parent.data.export_matlab(filepath=filepath,
                                           datakey=self.datakey.get(),
                                           lists_to_save=lists_to_save,
                                           save_piezo=self.save_piezo.get(),
                                           save_command=self.save_command.get())
        else:
            logging.info("User pressed 'Cancel'")
        self.destroy()

    def cancel(self):
        self.destroy()

class HistogramConfiguration(tk.Toplevel):
    """
    A frame in which the setting of the histogram can be configured
    """
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent #parent is main frame
        self.create_widgets()

    def create_widgets(self):
        # general options
        ttk.Label(self, text="Number of bins").grid(row=0, column=0)
        ttk.Entry(self,textvariable=self.parent.plots.hist_n_bins, width=7).\
                                                       grid(row = 0, column=1)

        ttk.Label(self, text="Plot as density").grid(row=0, column=3)
        ttk.Checkbutton(self, variable=self.parent.plots.hist_density)\
            .grid(row=0, column=4)

        # piezo selection options
        piez_int_label = ttk.Label(self, text="Select using piezo voltage")
        piez_int_label.grid(row=1, column=0)
        piezo_int_button = ttk.Radiobutton(self,
                variable=self.parent.plots.hist_piezo_interval,
                value=1)
        piezo_int_button.grid(row=1,column=1)


        act_label = ttk.Label(self, text="Active/Inactive")
        act_label.grid(row=2, column=0)
        act_button = ttk.Checkbutton(self,
                    variable=self.parent.plots.hist_piezo_active)
        act_button.grid(row=2, column=1)

        dev_label = ttk.Label(self, text="deviation from max/min")
        dev_label.grid(row=3, column=0)
        dev_entry = ttk.Entry(self,
                textvariable=self.parent.plots.hist_piezo_deviation, width=7)
        dev_entry.grid(row = 3, column=1)

        # interval selection options
        ttk.Label(self, text="Use intervals").grid(row=1, column=3)
        ttk.Radiobutton(self,variable=self.parent.plots.hist_piezo_interval,
                        value=0).grid(row=1,column=4)

        ttk.Label(self, text="Intervals").grid(row=2, column=3)
        ttk.Entry(self,textvariable=self.parent.plots.hist_interval_entry,
                  width=7).grid(row = 2, column=4)

        # draw button
        ttk.Button(self, text="OK", command=self.ok_click)\
            .grid(row=5, columnspan=2)
        # cancel button
        ttk.Button(self, text="Cancel", command=self.destroy)\
            .grid(row=5, column=3, columnspan=2)

        if not self.parent.data.has_piezo:
            for widget in [piez_int_label, piezo_int_button, act_label,
                            act_button, dev_entry, dev_label]:
                widget.configure(state='disable')
            self.parent.plots.hist_piezo_interval.set(0)

    def ok_click(self):
        """
        redraw the histogram (with new settings)
        """
        try:
            self.parent.plots.hist_intervals=\
                stringList_parser(self.parent.plots.hist_interval_entry.get())
        except: pass
        try:
            self.parent.draw_plots(new=True)
        except: pass
        self.destroy()

class BaselineFrame(tk.Toplevel):
    """
    Temporary frame in which to chose how and based on what points
    the baseline correction should be performed.
    """
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.title("Baseline correction")

        # variables to choose the method
        self.select_piezo = tk.IntVar()
        self.select_piezo.set(1)
        self.select_intvl = tk.IntVar()
        self.select_intvl.set(0)

        ### piezo and interval selection should be mutually exclusive
        self.select_piezo.trace("w", self.piezo_NotInterval)
        self.select_intvl.trace("w", self.interval_NotPiezo)

        ### parameters of the baseline procedure
        self.method = tk.StringVar()
        self.method.set('poly')
        self.degree = tk.StringVar()
        self.degree.set(1)

        ### parameters for piezo selection
        self.deviation = tk.StringVar()
        self.deviation.set(.05)
        self.piezo_active = tk.IntVar()
        self.piezo_active.set(0)

        ### parameters for interval selection
        self.interval_entry = tk.StringVar()
        self.interval_entry.set('')
        self.intervals = []
        self.time_unit = tk.StringVar()
        self.time_unit.set('ms')

        self.create_widgets()

    def create_widgets(self):
        """Creates all widgets that apply to both modes.
        """

        # general options

        ttk.Label(self, text='method').grid(column=1, row=0)
        # create dropdown menu
        ttk.Entry(self, width=7, textvariable=self.method).grid(column=2, row=0)

        ttk.Label(self, text='degree').grid(column=1, row=1)
        ttk.Entry(self,width=8, textvariable=self.degree)\
            .grid(row=1, column=2)

        ### piezo selection options
        ttk.Label(self, text="Select using piezo voltage")\
            .grid(row=2, column=0)
        ttk.Checkbutton(self, variable=self.select_piezo)\
            .grid(row=2, column=1)

        ttk.Label(self, text="Active/Inactive").grid(row=3, column=0)
        ttk.Checkbutton(self, variable=self.piezo_active).grid(row=3, column=1)

        ttk.Label(self, text="deviation from max/min").grid(row=4, column=0)
        ttk.Entry(self, textvariable=self.deviation, width=7)\
            .grid(row=4, column=1)

        # interval selection options
        ttk.Label(self, text="Use intervals").grid(row=2, column=3)
        ttk.Checkbutton(self, variable=self.select_intvl).grid(row=2, column=4)
        ttk.Label(self, text="Intervals").grid(row=3, column=3)
        ttk.Entry(self, textvariable=self.interval_entry, width=7)\
            .grid(row=3, column=4)

        # ok and close
        ttk.Button(self, text="OK", command=self.ok_click)\
            .grid(row=5, columnspan=2)
        ttk.Button(self, text="Cancel", command=self.destroy)\
            .grid(row=5, column=3, columnspan=2)

    def ok_click(self):
        """redraw the histogram (with new settings) and close the dialog"""
        logging.info('going to baseline all episodes')
        try:
            self.intervals = stringList_parser(self.interval_entry.get())
        except:
            pass

        deviation = float(self.deviation.get())
        self.parent.parent.data.baseline_correction(
                                        method=self.method.get(),
                                        poly_degree=int(self.degree.get()),
                                        intval=self.intervals,
                                        select_intvl=self.select_intvl.get(),
                                        select_piezo=self.select_piezo.get(),
                                        active_piezo=self.piezo_active.get(),
                                        piezo_diff=deviation)
        self.parent.parent.datakey.set(self.parent.parent.data.currentDatakey)
        self.parent.parent.update_episodelist()
        self.parent.parent.draw_plots(True)
        self.destroy()

    def interval_NotPiezo(self, *args):
        """
        If interval selection is turned on turn off the piezo selection
        """
        if self.select_intvl.get() == 1:
            self.select_piezo.set(0)

    def piezo_NotInterval(self, *args):
        """
        If piezo selection is turned on turn off interval
        """
        if self.select_piezo.get() == 1:
            self.select_intvl.set(0)


class ListSelection(ttk.Frame):
    def __init__(self, parent):
        logging.debug("__init__ ListSelection")
        ttk.Frame.__init__(self, parent)
        self.parent = parent # parent is mainframe
        #we need to store the variables, else they are deleted straight after
        #the call
        self.variable_store = list()
        self.create_button() #button for adding new lists

    def new_checkbox(self, name, key='', color=''):
        """
        Create a new checkbox but first check if a list by that name already
        exists
        """
        logging.debug(f"ListSelection.new_checkbox")
        if name in self.parent.data.lists.keys():
            logging.info(f'tried to create list with the name "{name}" of an \
                     existing list\n list creation failed')
            pass
        else: self.create_checkbox(name=name, key=key, color=color)

    def create_checkbox(self, name, key='', color=''):
        """
        Create another checkbutton for a new selection of episodes and add
        them to the buttons dict.

        The function destroys the "add" button before it creates the
        checkbutton and then create a new button. Both objects are added using
        the `pack` which should ensure that they are places underneath one
        another.
        """
        logging.debug(f"ListSelection.create_checkbox")
        logging.info(f'Creating checkbox with name "{name}" under key "{key}" with \
                 color {color} ')

        # remove old 'add' button
        self.createBoxButton.destroy()

        # create a checkbox and a variable for it
        variable = tk.IntVar()
        if name=='all':
            variable.set(1) ### start with 'all' selected
            button = ttk.Checkbutton(self, text=name, variable=variable)
            button.pack()
            self.create_button()
        else:
            button = ttk.Checkbutton(self, text='[{}] {}'.format(key,name),
                                     variable=variable)
            variable.set(1)
            button.pack()
            self.parent.data.current_lists.append(name)

            # create new 'add' button underneath the checkbox
            self.create_button()

            # initialize with empty elemnts
            self.parent.data.lists[name] = [list(),str(),str()]

            # create function to color episode on keypress and add to list
            # convert key to lower case and take only the first letter
            key = key[0].lower()
            def add_episode(*args, **kwargs):
                """
                for every list a function is created to add episodes to the
                list and color them
                """
                # get highlighted selection of episode from episode list
                selected_ep = self.parent.episodeList.episodelist.curselection()
                new_list = self.parent.data.lists[name][0]
                episodelist = self.parent.episodeList.episodelist
                logging.info(f"Currently selected episodes are {selected_ep}")
                # loop over all currently selected episodes
                for n_episode in selected_ep:
                    # if episode not in list add it
                    if not (n_episode in new_list):
                        episodelist.itemconfig(n_episode, bg=color)
                        new_list.append(n_episode)
                        logging.info("added {} to {}".format(n_episode,name))
                    # if already in list remove it
                    else:
                        episodelist.itemconfig(n_episode, bg='white')
                        new_list.remove(n_episode)
                        logging.info(f"removed {n_episode} from {name}")
                logging.debug(f"'{name}' now contains:\n {new_list}")
            # bind coloring function to key press
            self.parent.episodeList.episodelist.bind(key,add_episode)
            # add list attributes to the list dict in the recording instance
            self.parent.data.lists[name][1] = color
            self.parent.data.lists[name][2] = key

        # trace the variable to add/removoe the corresponding list to/from
        # the list of current lists, also update the histogram to immediatly
        # show the change
        def trace_variable(*args):
            if name in self.parent.data.current_lists:
                self.parent.data.current_lists.remove(name)
                logging.info('removed {} from `current_lists'.format(name))
            else:
                self.parent.data.current_lists.append(name)
                logging.info('added {} to `current_lists'.format(name))
            # when changing lists update the histogram to display only
            # episodes in selected lists
            self.parent.draw_plots()
        variable.trace('w', trace_variable)
        logging.debug("""tracing variable to add/remove list""")
        self.variable_store.append(variable)

    def create_button(self):
        """
        Create the button that will open the dialog for adding new lists.
        This functions uses `pack` geometry because the button will be created
        and destroyed several times at different locations in the grid.
        """
        logging.debug("ListSelection.create_button")
        self.createBoxButton = ttk.Button(self,text='new list',
                                          command=lambda: AddListDialog(self))
        self.createBoxButton.pack()

class AddListDialog(tk.Toplevel):
    """
    The dialog that will pop up if a new list is created, it asks for the name
    of the list.
    """
    def __init__(self, parent):
        logging.info("initializing AddListDialog")
        tk.Toplevel.__init__(self, parent)
        self.parent = parent #parent is ListSelection frame
        self.title("Add list")
        self.name = tk.StringVar()
        self.key = tk.StringVar()
        self.color_choice = tk.StringVar()
        self.color_choice.set('green')
        self.colors = ['','red', 'green', 'yellow', 'purple', 'orange']
        self.create_widgets()

        logging.info("Opened new AddListDialog")

    def create_widgets(self):
        logging.info('populating dialog')
        ttk.Label(self, text='Name:').grid(row=0,column=0)
        name_entry = ttk.Entry(self, width=7, textvariable=self.name)
        name_entry.grid(row=0,column=1)
        name_entry.focus()

        ttk.Label(self, text='key:').grid(row=1,column=0)
        ttk.Entry(self, width=7, textvariable=self.key).grid(row=1,column=1)

        ttk.Label(self,text="Color: ").grid(row=2,column=0)
        color = ttk.OptionMenu(self,self.color_choice,*self.colors)
        color.grid(row=2,column=1)

        ttk.Button(self,text="OK",command=self.ok_button).grid(row=3,column=0)
        ttk.Button(self,text="Cancel",command=self.destroy).grid(row=3,
                                                                 column=1)

    def ok_button(self):
        logging.info("Confirmed checkbox creation through dialog")
        if self.name.get() and self.key.get():
            self.parent.new_checkbox(name = self.name.get(),
                                     key = self.key.get(),
                                     color = self.color_choice.get())
        else: print("failed to enter name and/or key")
        self.destroy()

class EpisodeList(ttk.Frame):
    """Frame that holds a scrollable list of all the episodes in the currently
    selected series.
    """

    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        logging.debug(f"__init__ EpisodeList")
        # create the variable tracking the current selection, `currentSeries`
        # and assign it to call the function `selection_change` when it is
        # changed
        self.create_list()
        self.create_dropdownmenu()

    def click_list(self, event):
        """When a new episode is selected by clicking or with arrow keys get the
        change the number of the current episode
        """

        #uses try to catch and ignore the event of the user clickling
        #outside the list
        try:
            n_episode = int(event.widget.curselection()[0])
            logging.debug(f"EpisodeList.click_list")
            logging.debug(f"selected episode number {n_episode}")
            self.parent.n_episode.set(n_episode)
        except IndexError: pass

    def create_list(self):
        """create the list of episodes and a scroll bar
        scroll bar is created first because episodelist references it
        the last line of scrollbar references episodelist so it has to come
        after the creating of episodelist
        """
        logging.debug(f"create_list")

        self.Scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.Scrollbar.grid(column=1, row=1, rowspan=3, sticky="NESW")

        self.episodelist = tk.Listbox(self, bd=2,
                                      yscrollcommand=self.Scrollbar.set,
                                      selectmode=tk.EXTENDED)
        self.episodelist.grid(row=1, rowspan=3, sticky="NESW")
        # set what should happen when an episode is selected
        self.episodelist.bind('<<ListboxSelect>>', self.click_list)
        # self.episodelist.config(height=30)

        for episode in self.parent.data[self.parent.datakey.get()]:
            self.episodelist.insert(tk.END, f"episode #{episode.n_episode}")
        # color all episodes according to their list membership
        # start from second element because white is default bg color
        for name in list(self.parent.data.lists.keys())[1:]:
            for index in self.parent.data.lists[name][0]:
                self.episodelist.itemconfig(index,
                                        {'bg':self.parent.data.lists[name][1]})

        # assign the scrollbar its function
        self.Scrollbar['command'] = self.episodelist.yview
        self.episodelist.selection_set(self.parent.data.n_episode)
        # make list and scrollbar expand
        self.grid_rowconfigure(1, weight=1)

    def create_dropdownmenu(self):
        """create the dropdown menu that is a list of the available series
        """
        logging.debug(f"`EpisodeList.create_dropdownmenu`")

        # the options in the list are all the datakeys
        listOptions = self.parent.data.keys()

        self.menu = tk.OptionMenu(self, self.parent.datakey, *listOptions)
        self.menu.grid(row=0, column=0, columnspan=2, sticky=tk.N)

class OpenFileDialog(tk.Toplevel):
    """
    Temporary frame that gets the file and information about it.
    Select file and load it by clicking 'ok' button, in case of binary
    file another window pops up to ask for additional parameters.
    """
    def __init__(self, parent):
        logging.info("initializing OpenFileDialog")

        tk.Toplevel.__init__(self,parent)
        self.parent = parent
        self.title("Select file")

        self.create_widgets()
        self.sampling_entry.focus()

    def create_widgets(self):
        #gui variables
        logging.info("creating OpenFileDialog widgets")
        # first row - filename and button for choosing file
        ttk.Label(self, text='File:').grid(column=1,row=1,sticky=(tk.N, tk.W))

        filenamelabel = ttk.Label(self, textvariable=self.parent.filename)
        filenamelabel.grid(column=2, row=1, sticky=tk.N)

        #second row - show filepath
        ttk.Label(self, text='Path:').grid(column=1, row=2, sticky = tk.W)
        ttk.Label(self, textvariable=self.parent.path).grid(column=2, row=2)

        #third row - show filetype
        ttk.Label(self, text='Filetype:').grid(column=1, row=3, sticky = tk.W)
        ttk.Label(self, textvariable=self.parent.filetypefull).grid(column=2,
                                                   row=3, sticky=(tk.W, tk.E))

        #fourth row - enter sampling rate
        self.sampling_entry = ttk.Entry(self, width=7,
                                       textvariable=self.parent.sampling_rate)
        self.sampling_entry.grid(column=2,row=4)
        ttk.Label(self, text="sampling rate (Hz):").grid(column=1,
                                                        row=4, sticky=(tk.W))

        # fifth row - enter time unit of data
        self.time_unit_entry = tk.OptionMenu(self, self.parent.time_input_unit,
                                             *Episode.time_unit_factors.keys())
        self.time_unit_entry.grid(column=2,row=5)
        ttk.Label(self, text="time unit:").grid(column=1,
                                                        row=5, sticky=(tk.W))
        # 6th row - enter current trace unit of data
        self.trace_unit_entry = tk.OptionMenu(self,
                                             self.parent.trace_input_unit,
                                             *Episode.trace_unit_factors.keys())
        self.trace_unit_entry.grid(column=2,row=6)
        ttk.Label(self, text="current trace unit:").grid(column=1,
                                                        row=6, sticky=(tk.W))
        # 7th row - enter piezo unit of data
        self.piezo_unit_entry = tk.OptionMenu(self,
                                             self.parent.piezo_input_unit,
                                             *Episode.piezo_unit_factors.keys())
        self.piezo_unit_entry.grid(column=2, row=7)
        ttk.Label(self, text="piezo unit:").grid(column=1,
                                                 row=7, sticky=(tk.W))
        # 8th row - enter command unit of data
        self.command_unit_entry = (
                tk.OptionMenu(self, self.parent.command_input_unit,
                              *Episode.command_unit_factors.keys())
                              )
        self.command_unit_entry.grid(column=2, row=8)
        ttk.Label(self, text="command voltage unit:").grid(column=1,
                                                           row=8, sticky=(tk.W))
        # 9th row - Load button to close and go to next window and close button
        self.loadbutton = ttk.Button(self, text="Load",
                                     command=self.load_button)
        self.loadbutton.grid(column=1, row=9, sticky=(tk.S, tk.W))

        self.closebutton = ttk.Button(self, text="Close",
                                      command=self.destroy)
        self.closebutton.grid(column=3, row=9, sticky=(tk.S, tk.E))

    def load_button(self):
        logging.debug(f"OpenFileDialog.load_button")

        if self.parent.filetype.get() == 'bin':
            Binaryquery(self)
        else:
            self.parent.load_recording()
            self.destroy()


class Binaryquery(tk.Toplevel):
    # this is basically deprecated!
    # probably does not work any more
    """If the filetype is '.bin' this asks for the additional parameters
    such as the length of the header (can be zero) and the datatype
    (should be given as numpy type, such as "np.int16")."""

    def __init__(self, parent):
        # frame configuration
        tk.Toplevel.__init__(self, parent)
        self.parent = parent.parent
        self.loadframe = parent
        self.title("Additional parameters for binary file")

        # initialize content
        self.create_widgets()
        self.headerentry.focus()

    def create_widgets(self):
        # #entry field for headerlength
        self.headerentry = ttk.Entry(self, width=7,
                                     textvariable=self.parent.headerlength)
        self.headerentry.grid(column=3, row=1, sticky=(tk.W, tk.N))

        ttk.Label(self, text="Headerlength:").grid(column=2, row=1,
                                                   sticky=(tk.N))

        #entry field for filetype
        self.typeentry = ttk.Entry(self, width=7,
                                   textvariable=self.parent.datatype)
        self.typeentry.grid(column=3,row=2,sticky=(tk.W,tk.S))

        ttk.Label(self, text="Datatype:").grid(column=2,row=2,
                                               sticky=tk.S)

        #'ok' and 'cancel button
        self.okbutton = ttk.Button(self, text="Load",
                                   command=self.ok_button)
        self.okbutton.grid(columnspan=2, row=3, sticky=(tk.S, tk.W))

    def ok_button(self):
        # if self.parent.datatype.get()=='np.int16':
        datatype = np.int16 #this is here because stringvar.get
                            #returns a string which numpy doesnt
                            #understand
        self.parent.data = Recording(self.parent.filenamefull.get(),
                                     self.parent.sampling_rate.get(),
                                     self.parent.filetype.get(),
                                     self.parent.headerlength.get(),
                                     datatype)
        self.parent.update_all()
        self.parent.episodeList.create_list()
        self.loadframe.destroy()
        self.destroy()
