import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import matplotlib
matplotlib.use('TkAgg')
import model as backend
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                            NavigationToolbar2TkAgg)
from matplotlib import gridspec as gs
import plotting
from tools import stringList_parser

### parameters for testing and verbose output
VERBOSE = False
axotest = False
bintest = False
mattest = False

class GUI(ttk.Frame):
    """
    GUI frame of the GUI for ASCAM.
    All the variables and objects are stored as attributes of this
    object to make refering them uniform.
    All other widgets will be children of this frame.
    It is easier to make to represent floats and integers using tk.StringVar
    because then they can be entered in entry fields without problems
    """
    @classmethod
    def run(cls):
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

        ### parameters for loading of a file
        self.filenamefull = tk.StringVar()
        self.filename = tk.StringVar()
        self.headerlength = tk.StringVar()
        self.datatype = tk.StringVar()
        self.path = tk.StringVar()
        self.filetypefull = tk.StringVar()
        self.filetype = tk.StringVar()
        self.data_loaded = False

        ### parameters for the histogram
        self.hist_number_bins = tk.StringVar()
        self.hist_number_bins.set(50)
        self.hist_density = tk.IntVar()
        self.hist_density.set(0)
        self.hist_piezoSelection = tk.IntVar()
        self.hist_piezoSelection.set(0)
        self.hist_piezo_active = tk.IntVar()
        self.hist_piezo_active.set(1)
        self.hist_piezo_deviation = tk.StringVar()
        self.hist_piezo_deviation.set(0.05)
        self.hist_intervalSelection = tk.IntVar()
        self.hist_intervalSelection.set(0)
        self.hist_interval_entry = tk.StringVar()
        self.hist_interval_entry.set('')
        self.hist_intervals = []
        self.hist_single_ep = tk.IntVar()
        self.hist_single_ep.set(1)
        self.hist_single_ep.trace("w",self.draw_histogram)

        ### trace selection methods to be mutually exclusive
        self.hist_piezoSelection.trace("w",self.hist_piezo_NotInterval)
        self.hist_intervalSelection.trace("w",self.hist_interval_NotPiezo)

        ### parameters for the plots
        self.show_piezo = tk.IntVar()
        self.show_piezo.set(0)
        self.show_piezo.trace("w", self.plot_episode)
        self.show_command = tk.IntVar()
        self.show_command.set(0)
        self.show_command.trace("w", self.plot_episode)

        ### parameters of the data
        self.samplingrate = tk.StringVar()
        self.samplingrate.set("0")

        # dictionary for the data
        self.data = backend.Recording()
        # datakey of the current displayed data
        self.datakey = tk.StringVar()
        self.datakey.set('raw_')
        # episode number of the currently displayed episode
        self.Nepisode = 0

        self.create_widgets()
        self.configure_grid()

        self.commandbar.loadbutton.focus()

        if bintest or axotest or mattest:
            self.load_for_testing()
        ## if testing arguments have been given data will be loaded when the
        ## program starts

        self.bind("<Configure>", self.update_plots)
        # this line calls `draw` when it is run

    def load_for_testing(self):
        """
        this function is called if the program is called with arguments "mat",
        "bin" or 'axo' and
        """
        if bintest:
        ### testing mode that uses simulated data, the data is copied and
        ### multiplied with random numbers to create additional episodes
            if VERBOSE:
                print('Test mode with binary data')
            self.data = backend.Recording(
                                    cwd+'/data/sim1600.bin', 4e4,
                                    'bin', 3072, np.int16)
            self.data['raw_'][0]['trace']=self.data['raw_'][0]['trace'][:9999]
            self.data['raw_'][0]['time']=self.data['raw_'][0]['time'][:9999]
            for i in range(1,25):
                dummyepisode = copy.deepcopy(self.data['raw_'][0])
                randommultiplier = np.random.random(
                                    len(dummyepisode['trace']))
                dummyepisode['trace'] = dummyepisode['trace']*randommultiplier
                dummyepisode.nthEpisode = i
                self.data['raw_'].append(dummyepisode)
        elif axotest:
            if VERBOSE:
                print('Test mode with axograph data')
            self.data = backend.Recording(filename = 'data/170404 015.axgd',
                                        filetype = 'axo')
        elif mattest:
            if VERBOSE:
                print('Test mode with matlab data.')
            self.data = backend.Recording(
                                filename = 'data/171124 013 Copy Export.mat',
                                filetype = 'mat')
        self.samplingrate.set('4e4')
        self.data_loaded = True
        self.update_all()

    def update_all(self, *args):
        """
        Use to update all data dependent widgets in the main window
        """
        self.update_list()
        self.plotOptions.update()
        self.update_plots()
        self.displayFrame.update()

    def create_widgets(self):
        """
        Create the contents of the main window.
        """
        self.commandbar = Commandframe(self)
        self.histogramFrame = HistogramFrame(self)
        self.plots = Plotframe(self)
        self.manipulations = Manipulations(self)
        self.episodeList = EpisodeList(self)
        self.listSelection = ListSelection(self)
        self.histogramOptions = HistogramConfiguration(self)
        self.plotOptions = PlotOptions(self)
        self.displayFrame = Displayframe(self)

    def configure_grid(self):
        """
        Geometry management of the elements in the main window.

        The values in col/rowconfig refer to the position of the elements
        WITHIN the widgets
        """

        ##### Place the main window in the root window
        self.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ##### First row
        self.commandbar.grid(row=0, column=0, padx=5, pady=5,
                             sticky=tk.N+tk.W)

        self.plotOptions.grid(row=0, column=1,padx=5,pady=5,sticky=tk.N+tk.W)

        self.displayFrame.grid(row=0, column=2, padx=5, sticky=tk.S)

        self.listSelection.grid(row=0, column=3, rowspan=2, padx=5, pady=5,
                                sticky=tk.N)

        self.histogramOptions.grid(row=0, column=4, columnspan=3)


        ##### Second row
        self.plots.grid(row=1, column=0, rowspan=3, columnspan=3, padx=5,
                        pady=5, sticky=tk.W)
        self.plots.grid_rowconfigure(0, weight=1)
        self.plots.grid_columnconfigure(0, weight=1)

        self.histogramFrame.grid(row=1, column=4, rowspan=3, columnspan=3,
                                 sticky=tk.E)
        self.histogramFrame.grid_rowconfigure(0, weight=1)
        self.histogramFrame.grid_columnconfigure(0, weight=1)

        ##### Third row
        self.episodeList.grid(row=2, column=3, rowspan=2)
        for i in range(2):
            self.episodeList.grid_columnconfigure(i, weight=1)
            self.episodeList.grid_rowconfigure(i, weight=1)
        ##### Fourth row

        ##### Fifth row
        self.manipulations.grid(row=4, column=0, columnspan=3, padx=5, pady=5,
                                sticky=tk.S+tk.W)

    def plot_episode(self, *args):
        """
        Plot the current episode
        """
        if self.data:
            if VERBOSE: print('Calling `plot`, `self.data` is `True`')
            self.plots.plot()
            self.plots.toolbar.update()
        else:
            if VERBOSE: print('Cannot plot, `self.data` is `False`')
            pass

    def draw_histogram(self, *args):
        """
        draw a histogram of the current episode
        """
        if self.data:
            if VERBOSE: print('Calling histogram, `self.data` is `True`.')
            self.histogramFrame.draw_histogram()
        else:
            if VERBOSE: print('Cannot draw histogram, `self.data` is `False`')
            pass

    def update_plots(self,*args,**kwargs):
        """
        update the plot and histogram of the current episode
        """
        if VERBOSE: print("updating plots")
        self.plot_episode()
        self.draw_histogram()
        self.displayFrame.update()

    def update_list(self):
        if VERBOSE: print('calling `update_list`')
        self.update_episodelist()
        self.update_listmenu()
        ### for now `update_list` will update both the list and the dropdown
        ### menu, in case they need to be uncoupled use the two functions below

    def update_episodelist(self):
        if VERBOSE: print('calling `update_episodelist`')
        self.episodeList.create_list()

    def update_listmenu(self):
        if VERBOSE: print('calling `update_listmenu`')
        self.episodeList.create_dropdownmenu()

    def hist_interval_NotPiezo(self,*args):
        """
        If interval selection for histogram is turned on turn off the piezo
        selection
        """
        if self.hist_intervalSelection.get() == 1:
            self.hist_piezoSelection.set(0)

    def hist_piezo_NotInterval(self,*args):
        """
        If piezo selection for histogram is turned on turn off interval
        selection
        """
        if self.hist_piezoSelection.get() == 1:
            self.hist_intervalSelection.set(0)

    def parse_hist_interval_entry(self,*args):
        """
        Convert the string that is entered in the config menu into a list of
        intervals that can be used for the histogram
        """

    def get_episodes_in_lists(self):
        """
        return an array of the indices of all the episodes in the currently
        selected lists
        """
        if VERBOSE: print("getting episodes in list")
        indices = []
        for listname in self.data.current_lists:
            indices.extend(self.data.lists[listname][0])
            if VERBOSE:
                print('for list "{}" added:'.format(listname))
                print(self.data.lists[listname][0])
        ### remove duplicate indices
        indices = np.array(list(set(indices)))
        indices = indices.flatten()
        return indices

    def quit(self):
        if VERBOSE: print('exiting ASCAM')
        self.master.destroy()
        self.master.quit()

class Displayframe(ttk.Frame):
    """
    This frame is used to display information.
    Currently this means only the mean and standard deviation of the command
    voltage.
    """
    def __init__(self, parent):
        if VERBOSE: print("initializing DisplayFrame")

        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.show_command_stats()

        if VERBOSE: print("initialized DisplayFrame")

    def update(self):
        """
        Update all contents of the Display frame
        """
        if VERBOSE: print("updating DisplayFrame")
        self.show_filename()
        self.show_command_stats()

    def show_filename(self):
        if self.parent.data_loaded:
            filename = self.parent.filename.get()
            if VERBOSE:
                print('will show filename as "{}"'.format(filename))

            ttk.Label(self,text = filename).grid(row=0, column=0, pady=10)

    def show_command_stats(self):
        if self.parent.data_loaded:
            datakey = self.parent.datakey.get()
            episode = self.parent.data[datakey][self.parent.Nepisode]

            if episode['command'] is not None:
                if VERBOSE:
                    print("showing command stats for datakey "+datakey)
                    print("episode number {}".format(self.parent.Nepisode))
                mean, std = episode.get_command_stats()
                command_stats ="Command Voltage = "
                command_stats+="{:2f} +/- {:2f}".format(mean,std)
                command_stats+=self.parent.data.commandUnit
                ttk.Label(self, text=command_stats).grid(row=4, column=0)
            else:
                if VERBOSE: print("no command voltage found")
        else: pass

class Commandframe(ttk.Frame):
    """
    This frame will contain all the command buttons such as loading
    data and plotting
    Creating the tk.Toplevel pop ups could be done with lambda functions
    """
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        self.loadbutton = ttk.Button(self, text="Load file",
                                     command=self.load_dialog)
        self.loadbutton.grid(column=0,row=0,sticky=tk.N+tk.E)

        self.savebutton = ttk.Button(self, text="Save data",
                                     command=self.save_dialog)
        self.savebutton.grid(column=1,row=0,sticky=tk.N)

    def load_dialog(self):
        Loadframe(self.parent)

    def save_dialog(self):
        SaveFrame(self.parent)

class SaveFrame(tk.Toplevel):
    """docstring for SaveFrame"""
    def __init__(self, parent):
        if VERBOSE: print("initializing SaveFrame")

        tk.Toplevel.__init__(self,parent)
        self.parent = parent
        self.title("Save data")
        self.create_entryFields()
        self.create_widgets()
        # self.loadbutton.focus()

    def create_entryFields(self):
        self.filename = tk.StringVar()
        # self.dirname = tk.StringVar()
        self.filetype = tk.StringVar()
        self.filetype.set('mat')
        self.save_piezo = tk.IntVar()
        self.save_command = tk.IntVar()

    def create_widgets(self):
        ttk.Label(self, text="Filetype:").grid(row=0,column=0)
        ttk.Entry(self,width=5,textvariable=self.filetype).grid(row=0,column=2)

        ttk.Label(self, text="Save piezo data").grid(row=1,column=0)
        ttk.Checkbutton(self,variable=self.save_piezo).grid(row=1,column=2)

        ttk.Label(self, text="Save command voltage data").grid(row=2,column=0)
        ttk.Checkbutton(self,variable=self.save_command).grid(row=2,column=2)

        ttk.Button(self,text="Select File",command=self.select_button
                    ).grid(row=3,column=1)

        ttk.Label(self, text='Filename:').grid(row=4,column=0)
        ttk.Label(self, textvariable=self.filename).grid(row=4,column=2)


        ttk.Button(self,text="Save",command=self.save_button
                    ).grid(row=6,column=0)
        ttk.Button(self,text='Cancel',command=self.destroy
                    ).grid(row=6, column=2)

    def select_button(self):
        self.filename.set(asksaveasfilename())
        if VERBOSE: print("selected filename: '"+self.filename.get()+"'")

    def save_button(self):
        if VERBOSE: print("Calling save_data method")
        self.parent.data.save_data(filename = self.filename.get(),
                                   filetype = self.filetype.get(),
                                   save_piezo = bool(self.save_piezo.get()),
                                   save_command = bool(self.save_command.get()))
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
        ttk.Checkbutton(self, variable=self.parent.hist_piezoSelection).\
                                                                grid(row=1,
                                                                     column=1)

        ttk.Label(self, text="Active/Inactive").grid(row=2, column=0)
        ttk.Checkbutton(self, variable=self.parent.hist_piezo_active).\
                                                                grid(row=2,
                                                                     column=1)

        ttk.Label(self, text="deviation from max/min").grid(row=3, column=0)
        ttk.Entry(self,textvariable=self.parent.hist_piezo_deviation,
                  width=7).grid(row = 3, column=1)

        ### interval selection options
        ttk.Label(self, text="Use intervals").grid(row=1, column=3)
        ttk.Checkbutton(self, variable=self.parent.hist_intervalSelection).\
                                                                grid(row=1,
                                                                     column=4)
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
        if VERBOSE: print("initializing HistogramFrame")

        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.fig = plt.figure(1,figsize=(6,5))
        canvasHist = FigureCanvasTkAgg(self.fig, self)
        canvasHist.show()
        canvasHist.get_tk_widget().grid(row=0,column=0)
        self.canvas = canvasHist

        if VERBOSE: print("initialized HistogramFrame")

    def draw_histogram(self, **kwargs):
        """
        draw a histogram of the current episode and a transparent all point hist
        in the background
        """
        if VERBOSE: print("drawing histogram")

        ### get histogram parameters
        n_bins = int(float(self.parent.hist_number_bins.get()))
        density = bool(self.parent.hist_density.get())
        piezoSelection = bool(self.parent.hist_piezoSelection.get())
        active = bool(self.parent.hist_piezo_active.get())
        deviation = float(self.parent.hist_piezo_deviation.get())
        fs = float(self.parent.samplingrate.get())
        intervals = self.parent.hist_intervals


        if VERBOSE:
            print("number of bins = {}".format(n_bins))
            print("density is {}".format(density))
            print("piezoSelection is {}".format(piezoSelection))
            print("active is {}".format(active))
            print("deviation = {}".format(deviation))

        ### create the plot object so we can delete it later
        ax = self.fig.add_subplot(111)

        if self.parent.data_loaded:
            if VERBOSE: print("found data")
            ### get data
            series = self.parent.data[self.parent.datakey.get()]
            time = series[0]['time']

            ### get current episode values and put them in a list
            ### because the histogram function expects a list
            single_piezo = [series[self.parent.Nepisode]['piezo']]
            single_trace = [series[self.parent.Nepisode]['trace']]

            ### get the bins and their values or the current episode
            hist_single = plotting.histogram(time, single_piezo, single_trace,
                                             active = active,
                                             piezoSelection = piezoSelection,
                                             deviation = deviation,
                                             n_bins = n_bins,
                                             density = density,
                                             intervals = intervals,
                                             samplingRate = fs,
                                             **kwargs)
            (heights_single,bins_single,
             center_single, width_single) = hist_single

            if self.parent.data.current_lists:
                if VERBOSE:
                    print("list(s) selected")
                    print("current lists are:")
                    for entry in self.parent.data.current_lists:
                        print(entry)
                ### get a list of all the currents and all the traces
                all_piezos = [episode['piezo'] for episode in series ]
                all_traces = [episode['trace'] for episode in series ]

                ### get the indices of currently selected lists
                indices = self.parent.get_episodes_in_lists()

                ### get corresponding piezos and traces
                all_piezos = [all_piezos[i] for i in indices]
                all_traces = [all_traces[i] for i in indices]

                ### get the bins and their values for all episodes
                hist_all = plotting.histogram(time, all_piezos, all_traces,
                                              active = active,
                                              piezoSelection = piezoSelection,
                                              deviation=deviation,
                                              n_bins = n_bins,
                                              density = density,
                                              intervals = intervals,
                                              samplingRate = fs,
                                              **kwargs)
                heights_all, bins_all, center_all, width_all = hist_all


                ### draw bar graphs of the histogram values over all episodes
                ax.bar(center_all, heights_all, width = width_all, alpha=.2,
                         color='orange')
                ax.plot(center_all,heights_all,color='orange', lw=2)
                ax.set_xlabel("Current ["+self.parent.data.currentUnit+']')
                if self.parent.hist_density.get()==1:
                    if VERBOSE: print('setting y-label "Relative frequency"')
                    ax.set_ylabel("Relative frequency")
                elif self.parent.hist_density.get()==0:
                    if VERBOSE: print('setting y-label "Count"')
                    ax.set_ylabel("Count")

            ### histogram of single episode
            if self.parent.hist_single_ep.get()==1:
                if VERBOSE: print("plotting single episode histogram")
                ax.bar(center_single, heights_single, width = width_single,
                         alpha=1)

            ### draw the histogram and clear the ax object to avoid
            ### cluttering memory
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
        if VERBOSE: print("creating plotOptions")

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
                ttk.Checkbutton(self, variable=self.parent.show_piezo).grid(
                                                                        row=0,
                                                                     column=1)
                # if piezo exists, default is to plot it
                self.parent.show_piezo.set(1)

            if self.parent.data[datakey][0]['command'] is not None:
                ttk.Label(self, text="Command voltage").grid(row=1, column=0)
                ttk.Checkbutton(self, variable=self.parent.show_command).grid(
                                                                        row=1,
                                                                     column=1)
                # if command exists default is to not plot it
                self.parent.show_command.set(0)
        else: pass

class Plotframe(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.fig = plt.figure(figsize=(10,5))



        canvasPlot = FigureCanvasTkAgg(self.fig, master=self)
        canvasPlot.show()
        canvasPlot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.canvas = canvasPlot
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def plot(self):
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

            if VERBOSE:
                print('`data` exists, plotting...')
                print('datakey = '+datakey)
                print('Nepisode = '+str(self.parent.Nepisode))

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
                if VERBOSE: print('will plot piezo voltage')
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
                if VERBOSE: print('will plot command voltage')
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
            plt.clf() #clear figure from memory

class Manipulations(ttk.Frame):
    """docstring for Manipulations"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.cutoffFrequency = tk.StringVar()
        self.cutoffFrequency.set(1000)
        self.create_widgets()

    def create_widgets(self):
        self.filterallbutton = ttk.Button(self, text="Filter",
                                     command=self.filter_series)
        self.filterallbutton.grid(column=1,row=0,sticky=())

        self.cutoffentry = ttk.Entry(self, width=7, textvariable=(
                                                        self.cutoffFrequency))
        self.cutoffentry.grid(column=1,row=1)
        ttk.Label(self, text="Filter Frequency (Hz):").grid(column=0, row=1,
                                                            sticky=(tk.W))

        self.baselineButton = ttk.Button(self,text='baseline',
                                        command=self.baseline_correct_frame)
        self.baselineButton.grid(row = 0, column=2,columnspan=2)

    def filter_series(self):
        if VERBOSE: print('going to filter all episodes')
        #convert textvar to float
        cutoffFrequency = float(self.cutoffFrequency.get())
        if self.parent.data.call_operation('FILTER_',cutoffFrequency):
            if VERBOSE: print('called operation succesfully')
            self.parent.datakey.set(self.parent.data.currentDatakey)
            if VERBOSE: print('updating list and plots')
            self.parent.update_list()
            self.parent.update_plots()
        ## here we should also have that if the operation has been performed
        ## the selection switches to that operation

    def baseline_correct_frame(self):
        if VERBOSE:
            print('Opening the baseline correction frame.')
        BaselineFrame(self)

class BaselineFrame(tk.Toplevel):
    """
    Temporary frame in which to chose how and based on what points
    the baseline correction should be performed.
    """
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.title("Baseline correction.")

        ### variables to choose the method
        self.piezoSelection = tk.IntVar()
        self.piezoSelection.set(1)
        self.intervalSelection = tk.IntVar()
        self.intervalSelection.set(0)

        ### piezo and interval selection should be mutually exclusive
        self.piezoSelection.trace("w",self.piezo_NotInterval)
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
        ttk.Checkbutton(self, variable=self.piezoSelection). grid(row=2,
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
        if VERBOSE: print('going to baseline all episodes')
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
                                           piezoSelection = (
                                                self.piezoSelection.get()),
                                           active = self.piezo_active.get(),
                                           deviation = deviation
                                           ):
            if VERBOSE: print('called operation succesfully')
            self.parent.parent.datakey.set(
                                       self.parent.parent.data.currentDatakey)
            if VERBOSE: print('updating list and plots')
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
            self.piezoSelection.set(0)

    def piezo_NotInterval(self,*args):
        """
        If piezo selection is turned on turn off interval
        """
        if self.piezoSelection.get() == 1:
            self.intervalSelection.set(0)

class ListSelection(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.buttons = dict()
        ## the `buttons` dict holds ordered pairs of the button objects and
        ## the variables they refer to, `dict['name']=(button,var)`

        self.create_button()
        self.create_checkbox('all')

        ## for some reason the first element is skipped
        self.colors = ['red', 'green', 'yellow', 'purple', 'orange']
        self.colorind = 0
        ## until color selection is added we use these three colors to color
        ## the episodes

    def create_checkbox(self, name, key=''):
        """
        Create another checkbutton for a new selection of episodes and add
        them to the buttons dict.

        The function destroys the "add" button before it creates the
        checkbutton and then create a new button. Both objects are added using
        the `pack` which should ensure that they are places underneath one
        another.
        """
        if VERBOSE: print('Creating checkbox with name "{}"'.format(name))

        ### remove old 'add' button
        self.createBoxButton.destroy()

        ### create a checkbox and a variable for it
        variable = tk.IntVar()
        if name=='all':
            variable.set(1) ### start with 'all' selected
            button = ttk.Checkbutton(self, text=name, variable=variable)
        else:
            button = ttk.Checkbutton(self, text='[{}] {}'.format(key,name),
                                     variable=variable)
            variable.set(0)

        button.pack()

        ### store button and variable in dict
        self.buttons[name] = (button, variable)

        ### create new 'add' button underneath the checkbox
        self.create_button()

        ### create a new list of indices if the list is new
        if not name in self.parent.data.lists.keys():
            self.parent.data.lists[name] = [[],'']

        ### create function to color episode on keypress and add to list
        if key:

            ### convert key to lower case and take only the first letter if
            ### multiple were entered
            key=key.lower()
            key=key[0]
            color = self.colors[self.colorind]
            def color_episode(*args, **kwargs):
                n_episode = self.parent.Nepisode
                new_list = self.parent.data.lists[name][0]
                episodelist = self.parent.episodeList.episodelist

                if not (n_episode in new_list):
                    episodelist.itemconfig(n_episode, bg=color)
                    new_list.append(n_episode)
                    if VERBOSE:
                        print('''pressing "{}" added episode {} to list {}
                              '''.format(key,n_episode,name))
                        print('"{}" now contains:'.format(name))
                        print(new_list)
                else:
                    episodelist.itemconfig(n_episode, bg='white')
                    new_list.remove(n_episode)
                    if VERBOSE:
                        print('''pressing "{}" removed episode {} from list {}
                              '''.format(key,n_episode,name))
                        print('"{}" now contains:'.format(name))
                        print(new_list)
            self.parent.bind_all(key,color_episode)
            self.parent.data.lists[name][1] = color
            self.colorind+=1

        ### trace the variable to add/removoe the corresponding list to/from
        ### the list of current lists, also update the histogram to immediatly
        ### show the change
        def trace_variable(*args):
            if name in self.parent.data.current_lists:
                self.parent.data.current_lists.remove(name)
                if VERBOSE:
                    print('remove {} from `current_lists'.format(name))
            else:
                self.parent.data.current_lists.append(name)
                if VERBOSE:
                    print('added {} to `current_lists'.format(name))
            ### when changing lists update the histogram to display only
            ### episodes in selected lists
            self.parent.draw_histogram()
        variable.trace("w",trace_variable)

    def create_button(self):
        """
        Create the button that will open the dialog for adding new lists.
        This functions uses `pack` geometry because the button will be created
        and destroyed several times at different locations in the grid.
        """
        if VERBOSE: print("Creating new checkbox maker button")

        self.createBoxButton = ttk.Button(self,text='Add',
                                          command=lambda: AddListDialog(self))
        self.createBoxButton.pack()

class AddListDialog(tk.Toplevel):
    """
    The dialog that will pop up if a new list is created, it asks for the name
    of the list.
    """
    def __init__(self, parent):
        if VERBOSE: print("initializing AddListDialog")
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.title("Add list")
        self.name = tk.StringVar()
        self.key = tk.StringVar()
        self.create_widgets()

        if VERBOSE: print("Opened new AddListDialog")

    def create_widgets(self):
        if VERBOSE: print('populating dialog')
        ttk.Label(self, text='Name:').grid(row=0,column=0)
        name_entry = ttk.Entry(self, width=7, textvariable=self.name)
        name_entry.grid(row=0,column=1)
        name_entry.focus()

        ttk.Label(self, text='key:').grid(row=1,column=0)
        ttk.Entry(self, width=7, textvariable=self.key).grid(row=1,column=1)

        ttk.Button(self,text="OK",command=self.ok_button).grid(row=2,column=0)
        ttk.Button(self,text="Cancel",command=self.destroy).grid(row=2,
                                                                 column=1)

    def ok_button(self):
        if VERBOSE: print("Confirmed checkbox creation through dialog")
        if self.name.get() and self.key.get():
            self.parent.create_checkbox(self.name.get(),self.key.get())
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
        selected_episode = int(event.widget.curselection()[0])
        if VERBOSE:
            print("selected episode number {}".format(selected_episode))
        self.parent.Nepisode = selected_episode
        self.parent.update_plots()

    def create_list(self):
        """
        create the list of episodes and a scroll bar
        scroll bar is created first because episodelist references it
        the last line of scrollbar references episodelist so it has to come
        after the creating of episodelist
        """
        if VERBOSE: print("creating scrollbar")
        self.Scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.Scrollbar.grid(column=1, row=1, rowspan=3, sticky=tk.N+tk.S+tk.E)

        if VERBOSE: print("creating episodelist")
        self.episodelist = tk.Listbox(self, bd=2,
                                      yscrollcommand=self.Scrollbar.set)
        self.episodelist.grid(row=1, rowspan=3, sticky=tk.S+tk.W+tk.N)
        ### set what should happen when an episode is selected
        self.episodelist.bind('<<ListboxSelect>>', self.onselect_plot)

        self.episodelist.config(height=30)
        ### only create the list if there is data to fill it with
        if self.parent.data:
            if VERBOSE: print("found data to fill list with")
            for episode in self.parent.data[self.parent.datakey.get()]:
                self.episodelist.insert(tk.END, "episode #"
                                                +str(episode.nthEpisode))
                if VERBOSE:
                    print("inserting episode number {}".format(
                                                          episode.nthEpisode))
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
        if  VERBOSE: print("creating dropdown menu")
        if self.parent.data:
            if VERBOSE: print("found data")
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
        if VERBOSE: print(self.parent.datakey.get()+' selected')
        self.parent.update_episodelist()
        self.parent.update_plots()

class Loadframe(tk.Toplevel):
    """
    Temporary frame that gets the file and information about it.
    Select file and load it by clicking 'ok' button, in case of binary
    file another window pops up to ask for additional parameters.
    """
    def __init__(self, parent):
        if VERBOSE: print("initializing LoadFrame")

        tk.Toplevel.__init__(self,parent)
        self.parent = parent
        self.title("Select file")
        self.create_entryFields()
        self.create_widgets()
        self.loadbutton.focus()

        if VERBOSE: print("LoadFrame initialized")

    def create_entryFields(self):
        """
        create the variables that hold all the entries of the load dialog
        """
        if VERBOSE: print("creating StringVars for parameter entry")
        self.filenamefull = tk.StringVar()
        self.filetypefull = tk.StringVar()
        self.filetype = tk.StringVar()
        self.filename = tk.StringVar()
        self.samplingrate = tk.StringVar()
        self.path = tk.StringVar()

        self.filetype.set('')
        self.filename.set('')
        self.samplingrate.set('')
        self.path.set('')

    def create_widgets(self):
        if VERBOSE: print("creating LoadFrame widgets")
        # first row - filename and button for choosing file
        ttk.Label(self, text='File:').grid(column=1,row=1,sticky=(tk.N, tk.W))

        filenamelabel = ttk.Label(self, textvariable=self.filename)
        filenamelabel.grid(column=2, row=1, sticky=tk.N)

        self.loadbutton = ttk.Button(self, text='Select file',
                                     command=self.get_file)
        self.loadbutton.grid(column = 3, row = 1, sticky=(tk.N, tk.E))

        #second row - show filepath
        ttk.Label(self, text='Path:').grid(column=1, row=2, sticky = tk.W)
        ttk.Label(self, textvariable=self.path).grid(column=2, row=2)

        #third row - show filetype
        ttk.Label(self, text='Filetype:').grid(column=1, row=3, sticky = tk.W)
        ttk.Label(self, textvariable=self.filetypefull).grid(column=2,
                                                   row=3, sticky=(tk.W, tk.E))
        ###### lets see if this way of line splitting works

        #fourth row - enter sampling rate
        self.samplingentry = ttk.Entry(self, width=7,
                                       textvariable=self.samplingrate)
        self.samplingentry.grid(column=2,row=4)
        ttk.Label(self, text="Samplingrate (Hz):").grid(column=1,
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

        elif (self.filetype.get() == 'axo'
              or self.filetype.get() == 'mat'):
            try:
                ### move variables to parent if data loaded succesfully
                self.parent.filetype.set(self.filetype.get())
                self.parent.filename.set(self.filename.get())
                self.parent.samplingrate.set(self.samplingrate.get())
                self.parent.path.set(self.path.get())

                self.parent.data = backend.Recording(self.filenamefull.get(),
                                                     self.samplingrate.get(),
                                                     self.filetype.get())
                self.parent.datakey.set(self.parent.data.currentDatakey)
                self.parent.data_loaded = True
                self.parent.update_all()
            finally:
                self.destroy()

    def get_file(self):
        """
        Get data by clicking.
        Relies on tkinter and gets name and type of the file
        """
        filename = askopenfilename()
        self.filenamefull.set(filename)
        extension = ''

        N = len(filename)
        for i, char in enumerate(filename[::-1]):
            # loop over the full filename (which includes directory) backwards
            # to extract the extension and name of the file
            if char=='.':
                period = N-i
            if char=='/':
                slash = N-i
                break

        self.filename.set(filename[slash:])
        self.path.set(filename[:slash])
        extension=filename[period:]

        if extension == 'bin':
            if VERBOSE: print("found '.bin' extension")
            self.filetype.set('bin')
            self.filetypefull.set('binary')

        elif extension == 'axgd':
            if VERBOSE: print("found '.axgd' extension")
            self.filetype.set('axo')
            self.filetypefull.set('axograph')

        elif extension == 'mat':
            if VERBOSE: print("found '.mat' extension")
            self.filetype.set('mat')
            self.filetypefull.set('matlab')

        self.samplingentry.focus()

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
        self.parent.data = backend.Recording(self.parent.filenamefull.get(),
                                         self.parent.samplingrate.get(),
                                         self.parent.filetype.get(),
                                         self.parent.headerlength.get(),
                                         datatype)
        self.parent.update_all()
        self.loadframe.destroy()
        self.destroy()

if __name__ == '__main__':
    import sys, os, copy
    cwd = os.getcwd()
    try:
        if 'axo' in sys.argv:
            axotest = True
        elif 'bin' in sys.argv:
            bintest = True
        elif 'mat' in sys.argv:
            mattest = True
        if 'v' in sys.argv:
            VERBOSE = True
    except IndexError:
        pass

    GUI.run()
