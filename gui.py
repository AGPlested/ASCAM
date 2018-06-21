import os
import copy
import time
import logging as log

import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
from matplotlib import gridspec as gs

from tools import stringList_parser, parse_filename
import plotting
from recording import Recording

matplotlib.use('TkAgg')


class GUI(ttk.Frame):
    """
    GUI frame for ASCAM.
    All the variables and objects are stored as attributes of this
    object to make refering them uniform.
    All other widgets will be children of this frame.
    It is easier to make to represent floats and integers using tk.StringVar
    because then they can be entered in entry fields without problems
    """
    @classmethod
    def run(cls):
        log.info("Starting ASCAM GUI")
        root = tk.Tk()
        root.protocol('WM_DELETE_WINDOW', quit)
        root.title("ASCAM")
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        GUI = cls(root)
        root.mainloop()

    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.master = master
        log.info("initializing main window")
        # which window system is being used
        self.window_system = master.tk.call('tk', 'windowingsystem')
        log.debug("window system is {}".format(self.window_system))

        ### parameters for loading of a file
        self.filenamefull = tk.StringVar()
        self.filename = tk.StringVar()
        self.headerlength = tk.StringVar()
        self.datatype = tk.StringVar()
        self.path = tk.StringVar()
        self.filetypefull = tk.StringVar()
        self.filetype = tk.StringVar()
        self.data_loaded = False

        # bind window name updating
        self.filename.trace("w",
                lambda *args: self.master.title("ASCAM - "+self.filename.get()))

        ### parameters for the histogram
        self.hist_number_bins = tk.StringVar()
        self.hist_number_bins.set(50)
        self.hist_density = tk.IntVar()
        self.hist_density.set(0)

        self.hist_piezo_active = tk.IntVar()
        self.hist_piezo_active.set(1)
        self.hist_piezo_deviation = tk.StringVar()
        self.hist_piezo_deviation.set(0.05)

        self.hist_interval_entry = tk.StringVar()
        self.hist_interval_entry.set('')
        self.hist_intervals = []
        self.hist_single_ep = tk.IntVar()
        self.hist_single_ep.set(1)
        self.hist_single_ep.trace("w",self.draw_histogram)
        # radio button variable to decide how to select points in histogram
        self.hist_piezo_interval = tk.IntVar()
        self.hist_piezo_interval.set(1)

        ### parameters for the plots
        self.show_piezo = tk.IntVar()
        self.show_piezo.set(0)
        self.show_piezo.trace("w", self.plot_episode)
        self.show_command = tk.IntVar()
        self.show_command.set(0)
        self.show_command.trace("w", self.plot_episode)

        ### parameters of the data
        self.sampling_rate = tk.StringVar()
        self.sampling_rate.set("0")

        # dictionary for the data
        self.data = Recording()
        # datakey of the current displayed data
        self.datakey = tk.StringVar()
        self.datakey.set('raw_')
        # episode number of the currently displayed episode
        self.Nepisode = 0

        self.create_widgets()
        self.configure_grid()

        self.bind("<Configure>", self.update_plots)
        # this line calls `draw` when it is run

    def load_recording(self):
        """ Take a recording object and load it into the GUI.
        """
        log.info("""loading recording...""")
        # get filename and set GUI title
        # _, _, _, filename = parse_filename(self.data.filename)
        # self.master.title("ASCAM - "+filename)
        self.master.title("ASCAM - "+self.filename.get())

        # recreate user defined episodelists
        for name, (_, color, key) in self.data.lists.items():
            log.debug("""found list {}, color: {}, key: {}""".format(name, color, key))
            self.listSelection.create_checkbox(name = name,
                                               key = key,
                                               color = color)
        self.update_all()

    def update_all(self, *args):
        """
        Use to update all data dependent widgets in the main window
        """
        log.debug("""updating all""")
        self.update_list()
        self.plotOptions.update()
        self.update_plots()
        self.displayFrame.update()

    def create_widgets(self):
        """
        Create the contents of the main window.
        """
        log.info("""creating widgets""")
        self.histogramFrame = HistogramFrame(self)
        self.plots = PlotFrame(self)
        self.episodeList = EpisodeList(self)
        self.listSelection = ListSelection(self)
        self.histogramOptions = HistogramConfiguration(self)
        self.plotOptions = PlotOptions(self)
        self.displayFrame = Displayframe(self)
        self.menuBar = MenuBar(self)

    def configure_grid(self):
        """
        Geometry management of the elements in the main window.

        The values in col/rowconfig refer to the position of the elements
        WITHIN the widgets
        """
        log.info("""configuring tkinter grid""")
        # Place the main window in the root window
        self.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # First row
        self.plotOptions.grid(row=0, column=1,padx=5,pady=5,sticky=tk.N+tk.W)

        self.displayFrame.grid(row=0, column=2, padx=5, sticky=tk.S)

        self.listSelection.grid(row=0, column=3, rowspan=2, padx=5, pady=5,
                                sticky=tk.N)

        self.histogramOptions.grid(row=0, column=4, columnspan=3)


        # Second row
        self.plots.grid(row=1, column=0, rowspan=3, columnspan=3, padx=5,
                        pady=5, sticky=tk.W)
        self.plots.grid_rowconfigure(0, weight=1)
        self.plots.grid_columnconfigure(0, weight=1)
        #
        self.histogramFrame.grid(row=1, column=4, rowspan=3, columnspan=3,
                                 sticky=tk.E)
        self.histogramFrame.grid_rowconfigure(0, weight=1)
        self.histogramFrame.grid_columnconfigure(0, weight=1)

        # Third row
        self.episodeList.grid(row=2, column=3, rowspan=2)
        for i in range(2):
            self.episodeList.grid_columnconfigure(i, weight=1)
            self.episodeList.grid_rowconfigure(i, weight=1)
        # Fourth row


    def plot_episode(self, *args):
        """
        Plot the current episode
        """
        if self.data:
            log.info('Calling `plot`, `self.data` is `True`')
            self.plots.plot()
            self.plots.toolbar.update()
        else:
            log.info('Cannot plot, `self.data` is `False`')
            pass

    def draw_histogram(self, *args):
        """
        draw a histogram of the current episode
        """
        if self.data:
            log.info('Calling histogram, `self.data` is `True`.')
            self.histogramFrame.draw_histogram()
        else:
            log.info('Cannot draw histogram, `self.data` is `False`')
            pass

    def update_plots(self,*args,**kwargs):
        """
        update the plot and histogram of the current episode
        """
        log.info("updating plots")
        self.plot_episode()
        self.draw_histogram()
        self.displayFrame.update()

    def update_list(self):
        log.info('updatin list')
        # self.episodeList.create_list()
        log.info("created new list")
        self.episodeList.create_dropdownmenu()
        ### for now `update_list` will update both the list and the dropdown
        ### menu, in case they need to be uncoupled use the two functions below

    def get_episodes_in_lists(self):
        """
        return an array of the indices of all the episodes in the currently
        selected lists
        """
        log.info("getting episodes in currently selected lists")
        indices = []
        for listname in self.data.current_lists:
            indices.extend(self.data.lists[listname][0])
            log.debug('''for list "{}" added:\n {}'''.format(listname,self.data.lists[listname][0]))
        # remove duplicate indices
        indices = np.array(list(set(indices)))
        indices = indices.flatten()
        log.info("indices in currently selected lists:\n {}".format(indices))
        return indices

    def quit(self):
        log.info('exiting ASCAM')
        self.master.destroy()
        self.master.quit()

class Displayframe(ttk.Frame):
    """
    This frame is used to display information.
    Currently this means only the mean and standard deviation of the command
    voltage.
    """
    def __init__(self, parent):
        log.info("initializing DisplayFrame")
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.show_command_stats()
        log.info("initialized DisplayFrame")

    def update(self):
        """
        Update all contents of the Display frame
        """
        log.info("updating DisplayFrame")
        self.show_filename()
        self.show_command_stats()

    def show_filename(self):
        if self.parent.data_loaded:
            filename = self.parent.filename.get()
            log.info('will show filename as "{}"'.format(filename))
            ttk.Label(self,text = filename).grid(row=0, column=0, pady=10)

    def show_command_stats(self):
        if self.parent.data_loaded:
            datakey = self.parent.datakey.get()
            episode = self.parent.data[datakey][self.parent.Nepisode]

            if episode['command'] is not None:
                log.info("""showing command stats for {}
                         episode number: {}""".format(datakey,self.parent.Nepisode))
                mean, std = episode.get_command_stats()
                command_stats ="Command Voltage = "
                command_stats+="{:2f} +/- {:2f}".format(mean,std)
                command_stats+=self.parent.data.commandUnit
                ttk.Label(self, text=command_stats).grid(row=4, column=0)
            else:
                log.info("no command voltage found")
        else: pass

class MenuBar(tk.Menu):
    def __init__(self,parent):
        self.parent = parent #parent is main window
        tk.Menu.__init__(self, parent.master,tearoff=0)
        self.parent.master.config(menu=self)

        # menu holding all the cascading options
        # `tearoff` is needed because otherwise there is a seperator on top the
        # menu
        self.file_menu = tk.Menu(self, tearoff=0)
        self.analysis_menu = tk.Menu(self, tearoff=0)

        self.create_file_cascade()
        self.create_analysis_cascade()

        # the code below is needed to make the menuBar responsive on Mac OS
        # apple uses window system aqua
        if parent.window_system == 'aqua':
            log.info("trying to make the menu work on Mac")
            appmenu = tk.Menu(self, name='apple')
            self.add_cascade(menu=appmenu)
            appmenu.add_command(label='About My Application')
            appmenu.add_separator()
            self.parent.master['menu'] = self

    def create_file_cascade(self):
        """
        Create all the options associated with files in the menu (e.g. 'open',
        'export' and 'save')
        """
        self.add_cascade(label="File", menu=self.file_menu)
        #Submenus under 'File'
        self.file_menu.add_command(label="Open File",command=self.open_file)
        self.file_menu.add_command(label="Save",command=self.save_to_file)
        self.file_menu.add_command(label="Export",command=self.export)
        self.file_menu.add_command(label="Quit",command=self.parent.master.quit)

    def create_analysis_cascade(self):
        self.add_cascade(label='Analysis',menu=self.analysis_menu)
        self.analysis_menu.add_command(label="Baseline",
                                       command=lambda: BaselineFrame(self))
        self.analysis_menu.add_command(label="Filter",
                                       command=lambda: FilterFrame(self.parent))
        self.analysis_menu.add_command(label="Idealize")
        self.analysis_menu.add_command(label="Set t_zero")

    def open_file(self):
        # open the dialog for loading a single file
        filename = askopenfilename()
        log.info("selected file: '"+filename+"'")
        if filename is not None:
            OpenFileDialog(self.parent, filename)
        else:
            log.info("User pressed 'Cancel'")

    def save_to_file(self):
        # save the current recording object with all its attributes as a
        # pickle file
        filepath = asksaveasfilename()
        if filepath is not None:
            self.parent.data.save_to_pickle(filepath)
        else:
            log.info("User pressed 'Cancel'")

    def export(self):
        ExportFileDialog(self.parent)

class FilterFrame(tk.Toplevel):
    """docstring for FilterFrame."""
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.title("Filter")
        #filterframe variables
        self.filter_selection = tk.StringVar()
        self.filter_selection.trace("w",self.create_entry_frame)
        #paramters for gaussian filter
        self.gaussian_fc = tk.StringVar()
        self.gaussian_fc.set('1000')
        #parameters for Chung Kennedy filter
        self.n_predictors = tk.StringVar()
        self.weight_exponent = tk.StringVar()
        self.lengths_predictors = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        """
        create the dropdown menu from which to choose the type of filter
        placeholder frame for entry fields
        and 'ok' and 'cancel' buttons
        """
        log.info("""creating dropdown menu for filter selection""")
        listOptions = ['Gaussian', 'Chung-Kennedy']
        self.menu = tk.OptionMenu(self, self.filter_selection, *listOptions)
        self.menu.grid(row=0,column=0,columnspan=2,sticky=tk.N)

        self.entry_frame = ttk.Frame(self)
        self.entry_frame.grid(row=1,column=0,columnspan=2)

        ttk.Button(self, text="OK", command=self.ok_button).grid(row=5)
        ttk.Button(self, text="Cancel", command=self.cancel_button).grid(row=5,
                                                                       column=1)

    def create_entry_frame(self,*args,**kwargs):
        """
        Create a frame for the entry of the filter parameters
        """
        if self.filter_selection.get()=='Gaussian':
            ttk.Label(self.entry_frame, text="Frequency [Hz]").grid(row=0,
                                                                    column=0)
            ttk.Entry(self.entry_frame,textvariable=self.gaussian_fc, width=7).\
                                                         grid(row = 0, column=1)
        elif self.filter_selection.get()=='Chung-Kennedy':
            ttk.Label(self.entry_frame, text="Number of predictors").grid(row=0,
                                                                    column=0)
            ttk.Entry(self.entry_frame,textvariable=self.n_predictors,width=7).\
                                                         grid(row = 0, column=1)
            ttk.Label(self.entry_frame, text="Weight exponent").grid(row=1,
                                                                    column=0)
            ttk.Entry(self.entry_frame,
                      textvariable=self.weight_exponent,width=7).grid(row = 1,
                                                                      column=1)
            ttk.Label(self.entry_frame, text="Lengths of predictors").grid(
                                                                row=2, column=0)
            ttk.Entry(self.entry_frame,
                      textvariable=self.lengths_predictors,width=7).grid(
                                                              row = 2, column=1)
    def filter_series(self):
        log.info('going to filter all episodes')
        if self.filter_selection.get()=="Gaussian":
            #convert textvar to float
            cutoffFrequency = float(self.gaussian_fc.get())
            log.info("filter frequency is {}".format(cutoffFrequency))
            if self.parent.data.call_operation('FILTER_',cutoffFrequency):
                log.info('called operation succesfully')
                self.parent.datakey.set(self.parent.data.currentDatakey)
                log.info('updating list and plots')
                self.parent.update_list()
                self.parent.update_plots()
        elif self.filter_selection.get()=="Chung-Kennedy":
            #backend for CK filter is not finished
            messagebox.showerror("Sorry","Chung-Kennedy filter has not yet been implemented")
            # time.sleep(5)

    def ok_button(self):
        if self.filter_selection.get(): self.filter_series()
        self.destroy()

    def cancel_button(self):
        self.destroy()

class ExportFileDialog(tk.Toplevel):
    """
    placeholder for a dialog for exporting data
    """
    def __init__(self, parent):
        log.info("initializing ExportFileDialog")
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
            self.parent.data.export_matlab(filepath = filepath,
                                           datakey = self.datakey.get(),
                                           lists = lists_to_save,
                                           save_piezo = self.save_piezo.get(),
                                           save_command = self.save_command.get())
        else:
            log.info("User pressed 'Cancel'")
        self.destroy()

    def cancel(self):
        self.destroy()

class HistogramConfiguration(ttk.Frame):
    """
    A frame in which the setting of the histogram can be configured
    """
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        ### general options
        ttk.Label(self, text="Number of bins").grid(row=0, column=0)
        ttk.Entry(self,textvariable=self.parent.hist_number_bins, width=7).\
                                                       grid(row = 0, column=1)

        ttk.Label(self, text="Plot as density").grid(row=0, column=3)
        ttk.Checkbutton(self, variable=self.parent.hist_density).grid(row=0,
                                                                     column=4)

        # piezo selection options
        ttk.Label(self, text="Select using piezo voltage").grid(row=1,
                                                                column=0)
        ttk.Radiobutton(self,variable=self.parent.hist_piezo_interval,
        value=1).grid(row=1,column=1)


        ttk.Label(self, text="Active/Inactive").grid(row=2, column=0)
        ttk.Checkbutton(self, variable=self.parent.hist_piezo_active).\
                                                                grid(row=2,
                                                                     column=1)

        ttk.Label(self, text="deviation from max/min").grid(row=3, column=0)
        ttk.Entry(self,textvariable=self.parent.hist_piezo_deviation,
                  width=7).grid(row = 3, column=1)

        ### interval selection options
        ttk.Label(self, text="Use intervals").grid(row=1, column=3)
        ttk.Radiobutton(self,variable=self.parent.hist_piezo_interval,
        value=0).grid(row=1,column=4)

        ttk.Label(self, text="Intervals").grid(row=2, column=3)
        ttk.Entry(self,textvariable=self.parent.hist_interval_entry,
                  width=7).grid(row = 2, column=4)

        ### draw button
        ttk.Button(self, text="Draw", command=self.draw_histogram).grid(row=5,
                                                                 columnspan=2)

        ### checkbox for single histogram
        ttk.Label(self, text="Show single episode").grid(row=5, column=3)
        ttk.Checkbutton(self, variable=self.parent.hist_single_ep).\
                                                                grid(row=5,
                                                                     column=4)

    def draw_histogram(self):
        """
        redraw the histogram (with new settings)
        """
        try:
            self.parent.hist_intervals=stringList_parser(
                                        self.parent.hist_interval_entry.get())
        except: pass
        try:
            self.parent.draw_histogram()
        except: pass

class HistogramFrame(ttk.Frame):
    """
    Frame for the histograms.
    """
    def __init__(self, parent):
        log.info("initializing HistogramFrame")

        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.fig = plt.figure(1,figsize=(6,5))
        canvasHist = FigureCanvasTkAgg(self.fig, self)
        # canvasHist.show()
        canvasHist.get_tk_widget().grid(row=0,column=0)
        self.canvas = canvasHist

        log.info("initialized HistogramFrame")

    def draw_histogram(self, **kwargs):
        """
        draw a histogram of the current episode and a transparent all point hist
        in the background
        """
        log.info("drawing histogram")

        ### get histogram parameters
        n_bins = int(float(self.parent.hist_number_bins.get()))
        density = bool(self.parent.hist_density.get())
        # time points are selected based on piezo values if the variable
        # 'hist_piezo_interval' is 1
        piezo_selection = bool(self.parent.hist_piezo_interval.get())
        active = bool(self.parent.hist_piezo_active.get())
        deviation = float(self.parent.hist_piezo_deviation.get())
        fs = float(self.parent.sampling_rate.get())
        intervals = self.parent.hist_intervals

        log.debug("""number of bins = {}
            density = {}
            piezo_selection = {}
            active = {}
            deviation = {}""".format(n_bins,density,piezo_selection,
                                     active,deviation))
        ### create the plot object so we can delete it later
        ax = self.fig.add_subplot(111)

        if self.parent.data_loaded:
            log.info("found data")
            ### get data
            series = self.parent.data[self.parent.datakey.get()]
            time = series[0]['time']

            # get current episode values and put them in a list
            # because the histogram function expects a list
            single_piezo = [series[self.parent.Nepisode]['piezo']]
            single_trace = [series[self.parent.Nepisode]['trace']]

            # get the bins and their values or the current episode
            hist_single = plotting.histogram(time, single_piezo, single_trace,
                                             active=active,
                                             piezo_selection=piezo_selection,
                                             deviation=deviation,
                                             n_bins=n_bins,
                                             density=density,
                                             intervals=intervals,
                                             sampling_rate=fs,
                                             **kwargs)
            (heights_single,bins_single,
             center_single, width_single) = hist_single

            if self.parent.data.current_lists:
                log.info("""current lists are: {}""".format(
                                                self.parent.data.current_lists))
                # get a list of all the currents and all the traces
                all_piezos = [episode['piezo'] for episode in series ]
                all_traces = [episode['trace'] for episode in series ]

                # get the indices of currently selected lists
                indices = self.parent.get_episodes_in_lists()

                # get corresponding piezos and traces
                all_piezos = [all_piezos[i] for i in indices]
                all_traces = [all_traces[i] for i in indices]

                # get the bins and their values for all episodes
                hist_all = plotting.histogram(time, all_piezos, all_traces,
                                              active = active,
                                              piezo_selection = piezo_selection,
                                              deviation=deviation,
                                              n_bins = n_bins,
                                              density = density,
                                              intervals = intervals,
                                              sampling_rate = fs,
                                              **kwargs)
                heights_all, bins_all, center_all, width_all = hist_all
                # draw bar graphs of the histogram values over all episodes
                ax.barh(center_all, heights_all, width_all,
                        alpha=0.2, color='orange', align='center')
                ax.plot(heights_all,center_all,color='orange', lw=2)
                ax.set_ylabel("Current ["+self.parent.data.currentUnit+']')
                if self.parent.hist_density.get()==1:
                    log.info('setting y-label "Relative frequency"')
                    ax.set_xlabel("Relative frequency")
                elif self.parent.hist_density.get()==0:
                    log.info('setting y-label "Count"')
                    ax.set_xlabel("Count")

            # histogram of single episode
            if self.parent.hist_single_ep.get()==1:
                log.info("plotting single episode histogram")
                ax.barh(center_single, heights_single, width_single,
                        align='center', alpha=1)

            # draw the histogram and clear the ax object to avoid
            # cluttering memory
            self.canvas.draw()
            ax.clear()

class PlotOptions(ttk.Frame):
    """
    A frame in which the setting of the histogram can be configured
    """
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent

        self.create_widgets()
        log.info("creating plotOptions")

    def update(self):
        """
        For updating the plot options (in case they every do more than just
        show those two things)
        """
        self.create_widgets()

    def create_widgets(self):
        """
        If piezo/command voltage data exists create widgets to toggle their
        displey in the plots
        """
        if self.parent.data_loaded:
            datakey = self.parent.datakey.get()
            episode = self.parent.data[datakey][self.parent.Nepisode]
            if episode['piezo'] is not None:
                ttk.Label(self, text="Piezo voltage").grid(row=0, column=0)
                piezo = ttk.Checkbutton(self, variable=self.parent.show_piezo)
                piezo.grid(row=0, column=1)
                # if piezo exists, default is to plot it
                self.parent.show_piezo.set(1)

            if self.parent.data[datakey][0]['command'] is not None:
                ttk.Label(self, text="Command voltage").grid(row=1, column=0)
                command = ttk.Checkbutton(self,variable=self.parent.show_command)
                command.grid(row=1,column=1)
                # if command exists default is to not plot it
                self.parent.show_command.set(0)

class PlotFrame(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.fig = plt.figure(figsize=(10,5))

        canvasPlot = FigureCanvasTkAgg(self.fig, master=self)
        # canvasPlot.show()
        canvasPlot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas = canvasPlot
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def plot(self):
        plt.clf() #clear figure from memory
        datakey = self.parent.datakey.get()
        if self.parent.data.filename:
            # get data to plot
            episode = self.parent.data[datakey][self.parent.Nepisode]

            # decide how many plots there will be
            num_plots = (1 + self.parent.show_command.get()
                          + self.parent.show_piezo.get())
            n_plot = 1 #counter for plots

            # plot grid to make current plot bigger
            pgs = gs.GridSpec(num_plots+1,1)

            log.info("""`data` exists, will plot episode number {}
            from series {}""".format(self.parent.Nepisode,datakey))

            time = episode['time']

            #get axis bounds
            min_A = self.parent.data[datakey].get_min('trace')
            max_A = self.parent.data[datakey].get_max('trace')

            # plot the current trace
            current_plot = self.fig.add_subplot(pgs[:2,:])
            plotting.plotTrace(
                        ax = current_plot,
                        time = time,
                        trace = episode['trace'],
                        ylabel = "Current ["+self.parent.data.currentUnit+"]",
                        ybounds = (min_A, max_A))
            n_plot += 1 #move to next plot

            self.subplots = [current_plot]

            # plot the piezo
            if self.parent.show_piezo.get():
                log.info('will plot piezo voltage')
                piezo_plot = self.fig.add_subplot(pgs[n_plot,:])
                plotting.plotTrace(
                        ax = piezo_plot,
                        time = time,
                        trace = episode['piezo'],
                        ylabel = "Piezo ["+self.parent.data.piezoUnit+']',
                        ybounds = [])
                n_plot += 1
                self.subplots.append(piezo_plot)
            # plot command voltage
            if self.parent.show_command.get():
                log.info('will plot command voltage')
                try: #get axis bounds
                    min_V = self.parent.data[datakey].get_min('command')
                    max_V = self.parent.data[datakey].get_max('command')
                except: pass
                command_plot = self.fig.add_subplot(pgs[n_plot,:])
                plotting.plotTrace(
                        ax = command_plot,
                        time = time,
                        trace = episode['command'],
                        ylabel = "Command ["+self.parent.data.commandUnit+']',
                        ybounds = [min_V,max_V])
                n_plot += 1
                self.subplots.append(command_plot)

            ## configure x-axis
            for plot in self.subplots[:-1]:
                plot.set_xticklabels([]) #turn off numbering on upper plots
            # label only the last axis
            self.subplots[-1].set_xlabel("Time ["+self.parent.data.timeUnit+"]")
            self.canvas.draw() # draw plots

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
        self.piezo_selection = tk.IntVar()
        self.piezo_selection.set(1)
        self.intervalSelection = tk.IntVar()
        self.intervalSelection.set(0)

        ### piezo and interval selection should be mutually exclusive
        self.piezo_selection.trace("w",self.piezo_NotInterval)
        self.intervalSelection.trace("w",self.interval_NotPiezo)

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
        """
        Creates all widgets that apply to both modes.
        """

        ### general options

        ttk.Label(self,text='method').grid(column=1,row=0)
        ############## create dropdown menu
        ttk.Entry(self,width=7,textvariable=self.method).grid(
                                                            column=2,row = 0)

        ttk.Label(self,text='degree').grid(column=1,row=1)
        ttk.Entry(self,width=8,textvariable=self.degree).grid(row = 1,
                                                                column = 2)



        ### piezo selection options
        ttk.Label(self, text="Select using piezo voltage").grid(row=2,
                                                                column=0)
        ttk.Checkbutton(self, variable=self.piezo_selection). grid(row=2,
                                                                  column=1)

        ttk.Label(self, text="Active/Inactive").grid(row=3, column=0)
        ttk.Checkbutton(self, variable=self.piezo_active).grid(row=3,column=1)

        ttk.Label(self, text="deviation from max/min").grid(row=4, column=0)
        ttk.Entry(self,textvariable=self.deviation,
                  width=7).grid(row = 4, column=1)

        ### interval selection options
        ttk.Label(self, text="Use intervals").grid(row=2, column=3)
        ttk.Checkbutton(self, variable=self.intervalSelection).grid(row=2,
                                                                    column=4)
        ttk.Label(self, text="Intervals").grid(row=3, column=3)
        ttk.Entry(self,textvariable=self.interval_entry,width=7).grid(row = 3,
                                                                     column=4)


        ### ok and close
        ttk.Button(self, text="OK", command=self.ok_button).grid(row=5,
                                                                 columnspan=2)
        ttk.Button(self, text="Cancel", command=self.destroy).grid(row=5,
                                                                  column=3,
                                                                 columnspan=2)

    def ok_button(self):
        """
        redraw the histogram (with new settings) and close the dialog
        """
        log.info('going to baseline all episodes')
        try:
            self.intervals=stringList_parser(self.interval_entry.get())
        except: pass

        deviation = float(self.deviation.get())

        if self.parent.parent.data.call_operation('BC_',
                                           method = self.method.get(),
                                           degree = int(self.degree.get()),
                                           intervals = self.intervals,
                                           timeUnit = self.time_unit,
                                           intervalSelection = (
                                                self.intervalSelection.get()),
                                           piezo_selection = (
                                                self.piezo_selection.get()),
                                           active = self.piezo_active.get(),
                                           deviation = deviation
                                           ):
            log.info('called operation succesfully')
            self.parent.parent.datakey.set(
                                       self.parent.parent.data.currentDatakey)
            log.info('updating list and plots')
            self.parent.parent.update_list()
            self.parent.parent.update_plots()
        ## here we should also have that if the operation has been performed
        ## the selection switches to that operation
        self.destroy()

    def interval_NotPiezo(self,*args):
        """
        If interval selection is turned on turn off the piezo selection
        """
        if self.intervalSelection.get() == 1:
            self.piezo_selection.set(0)

    def piezo_NotInterval(self,*args):
        """
        If piezo selection is turned on turn off interval
        """
        if self.piezo_selection.get() == 1:
            self.intervalSelection.set(0)

class ListSelection(ttk.Frame):
    def __init__(self, parent):
        log.info("""initializing ListSelection frame""")
        ttk.Frame.__init__(self, parent)
        self.parent = parent # parent is mainframe
        self.create_button() #button for adding new lists

    def new_checkbox(self, name, key='', color=''):
        """
        Create a new checkbox but first check if a list by that name already
        exists
        """
        if name in self.parent.data.lists.keys():
            log.info("""tried to create list with the name ("{}") of an existing list\n list creation failed""".format(name))
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

        log.info('''Creating checkbox with name "{}" under key "{}"" with color {} '''.format(name,key,color))

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
            variable.set(0)
            button.pack()

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
                selected_eps = self.parent.episodeList.episodelist.curselection()
                new_list = self.parent.data.lists[name][0]
                episodelist = self.parent.episodeList.episodelist
                log.info("Currently selected episodes are {}".format(selected_eps))
                # loop over all currently selected episodes
                for n_episode in selected_eps:
                    # if episode not in list add it
                    if not (n_episode in new_list):
                        episodelist.itemconfig(n_episode, bg=color)
                        new_list.append(n_episode)
                        log.info("added {} to {}".format(n_episode,name))
                    # if already in list remove it
                    else:
                        episodelist.itemconfig(n_episode, bg='white')
                        new_list.remove(n_episode)
                        log.info("removed {} from {}".format(n_episode,name))
                log.debug("""'{}' now contains:\n {}""".format(name,new_list))
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
                    log.debug('removed {} from `current_lists'.format(name))
                else:
                    self.parent.data.current_lists.append(name)
                    log.debug('added {} from `current_lists'.format(name))
                # when changing lists update the histogram to display only
                # episodes in selected lists
                self.parent.draw_histogram()
            variable.trace("w",trace_variable)

    def create_button(self):
        """
        Create the button that will open the dialog for adding new lists.
        This functions uses `pack` geometry because the button will be created
        and destroyed several times at different locations in the grid.
        """
        log.info("Creating new checkbox maker button")
        self.createBoxButton = ttk.Button(self,text='Add',
                                          command=lambda: AddListDialog(self))
        self.createBoxButton.pack()

class AddListDialog(tk.Toplevel):
    """
    The dialog that will pop up if a new list is created, it asks for the name
    of the list.
    """
    def __init__(self, parent):
        log.info("initializing AddListDialog")
        tk.Toplevel.__init__(self, parent)
        self.parent = parent #parent is ListSelection frame
        self.title("Add list")
        self.name = tk.StringVar()
        self.key = tk.StringVar()
        self.color_choice = tk.StringVar()
        self.color_choice.set('green')
        self.colors = ['','red', 'green', 'yellow', 'purple', 'orange']
        self.create_widgets()

        log.info("Opened new AddListDialog")

    def create_widgets(self):
        log.info('populating dialog')
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
        log.info("Confirmed checkbox creation through dialog")
        if self.name.get() and self.key.get():
            self.parent.new_checkbox(name = self.name.get(),
                                        key = self.key.get(),
                                        color = self.color_choice.get())
        else: print("failed to enter name and/or key")
        self.destroy()

class EpisodeList(ttk.Frame):
    """
    Frame that holds a scrollable list of all the episodes in the currently
    selected series.
    """
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent

        ### create the variable tracking the current selection, `currentSeries`
        ### and assign it to call the function `selection_change` when it is
        ### changed
        self.parent.datakey.trace("w", self.selection_change)
        self.create_list()
        self.create_dropdownmenu()

    def onselect_plot(self, event):
        """
        When a new episode is selected by clicking or with arrow keys get the
        change the number of the current episode and update the plots
        """
        #uses try to catch and ignore the event of the user clickling
        #outside the list
        try:
            selected_episode = int(event.widget.curselection()[0])
            log.info("selected episode number {}".format(selected_episode))
            self.parent.Nepisode = selected_episode
            self.parent.update_plots()
        except IndexError: pass

    def create_list(self):
        """
        create the list of episodes and a scroll bar
        scroll bar is created first because episodelist references it
        the last line of scrollbar references episodelist so it has to come
        after the creating of episodelist
        """
        log.info("creating scrollbar")
        self.Scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.Scrollbar.grid(column=1, row=1, rowspan=3, sticky=tk.N+tk.S+tk.E)

        log.info("creating episodelist")
        self.episodelist = tk.Listbox(self, bd=2,
                                      yscrollcommand=self.Scrollbar.set,
                                      selectmode=tk.EXTENDED)
        self.episodelist.grid(row=1, rowspan=3, sticky=tk.S+tk.W+tk.N)
        ### set what should happen when an episode is selected
        self.episodelist.bind('<<ListboxSelect>>', self.onselect_plot)

        self.episodelist.config(height=30)
        ### only create the list if there is data to fill it with
        if self.parent.data:
            log.info("found data to fill list with")
            for episode in self.parent.data[self.parent.datakey.get()]:
                self.episodelist.insert(tk.END, "episode #"
                                                +str(episode.n_episode))
                log.debug("inserting episode number {}".format(episode.n_episode))
        ### color all episodes according to their list membership
            ### start from second element because white is default bg color
            for name in list(self.parent.data.lists.keys())[1:]:
                for index in self.parent.data.lists[name][0]:
                    self.episodelist.itemconfig(index,
                                    {'bg':self.parent.data.lists[name][1]})


        ### assign the scrollbar its function
        self.Scrollbar['command'] = self.episodelist.yview
        self.episodelist.selection_set(self.parent.Nepisode)

    def create_dropdownmenu(self):
        """
        create the dropdown menu that is a list of the available series
        """
        log.info("""creating dropdown menu""")
        if self.parent.data:
            log.info("found data")
            ### the options in the list are all the datakeys
            listOptions = self.parent.data.keys()
        else:
            listOptions = ['']
        self.menu = tk.OptionMenu(self, self.parent.datakey, *listOptions)
        self.menu.grid(row=0,column=0,columnspan=2,sticky=tk.N)

    def selection_change(self, *args):
        """
        when the `currentSeries` variable changes this function will be called
        it needs the `*args` arguments because tkinter passes some arguments
        to it (we currently dont need those)
        """
        log.info(self.parent.datakey.get()+' selected')
        self.create_list()
        self.parent.update_plots()

class OpenFileDialog(tk.Toplevel):
    """
    Temporary frame that gets the file and information about it.
    Select file and load it by clicking 'ok' button, in case of binary
    file another window pops up to ask for additional parameters.
    """
    def __init__(self, parent, filename):
        log.info("initializing OpenFileDialog")

        tk.Toplevel.__init__(self,parent)
        self.parent = parent
        self.title("Select file")

        log.info("creating StringVars for parameter entry")
        self.filenamefull = tk.StringVar()
        self.filetypefull = tk.StringVar()
        self.filetype = tk.StringVar()
        self.filename = tk.StringVar()
        self.sampling_rate = tk.StringVar()
        self.path = tk.StringVar()

        self.filenamefull.set(filename)
        filetype, path, filetypefull, filename = parse_filename(filename)
        self.filename.set(filename)
        self.path.set(path)
        self.filetype.set(filetype)
        self.filetypefull.set(filetypefull)

        self.create_widgets()
        self.samplingentry.focus()
        log.info("OpenFileDialog initialized")

    def create_widgets(self):
        log.info("creating OpenFileDialog widgets")
        # first row - filename and button for choosing file
        ttk.Label(self, text='File:').grid(column=1,row=1,sticky=(tk.N, tk.W))

        filenamelabel = ttk.Label(self, textvariable=self.filename)
        filenamelabel.grid(column=2, row=1, sticky=tk.N)

        #second row - show filepath
        ttk.Label(self, text='Path:').grid(column=1, row=2, sticky = tk.W)
        ttk.Label(self, textvariable=self.path).grid(column=2, row=2)

        #third row - show filetype
        ttk.Label(self, text='Filetype:').grid(column=1, row=3, sticky = tk.W)
        ttk.Label(self, textvariable=self.filetypefull).grid(column=2,
                                                   row=3, sticky=(tk.W, tk.E))

        #fourth row - enter sampling rate
        self.samplingentry = ttk.Entry(self, width=7,
                                       textvariable=self.sampling_rate)
        self.samplingentry.grid(column=2,row=4)
        ttk.Label(self, text="sampling_rate (Hz):").grid(column=1,
                                                        row=4, sticky=(tk.W))

        #fifth row - Load button to close and go to next window and close button
        self.loadbutton = ttk.Button(self, text="Load",
                                   command=self.load_button)
        self.loadbutton.grid(column=1, row=5, sticky=(tk.S, tk.W))

        self.closebutton = ttk.Button(self, text="Close",
                                      command=self.destroy)
        self.closebutton.grid(column=3, row=5, sticky=(tk.S, tk.E))

    def load_button(self):
        if self.filetype.get() == 'bin':
            binframe = Binaryquery(self)
        else:
            try:
                ### move variables to parent if data loaded succesfully
                self.parent.filetype.set(self.filetype.get())
                self.parent.filename.set(self.filename.get())
                self.parent.sampling_rate.set(self.sampling_rate.get())
                self.parent.path.set(self.path.get())

                self.parent.data = Recording(self.filenamefull.get(),
                                             self.sampling_rate.get(),
                                             self.filetype.get())
                self.parent.datakey.set(self.parent.data.currentDatakey)
                self.parent.data_loaded = True
                self.parent.load_recording()
            finally:
                self.destroy()

class Binaryquery(tk.Toplevel):
    """
    If the filetype is '.bin' this asks for the additional parameters
    such as the length of the header (can be zero) and the datatype
    (should be given as numpy type, such as "np.int16")
    """
    def __init__(self, parent):
        #frame configuration
        tk.Toplevel.__init__(self, parent)
        self.parent = parent.parent
        self.loadframe = parent
        self.title("Additional parameters for binary file")

        #initialize content
        self.create_widgets()
        self.headerentry.focus()

    def create_widgets(self):
        # #entry field for headerlength
        self.headerentry = ttk.Entry(self, width=7,
                                textvariable=self.parent.headerlength)
        self.headerentry.grid(column=3,row=1,sticky=(tk.W,tk.N))

        ttk.Label(self, text="Headerlength:").grid(column=2,row=1,
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
