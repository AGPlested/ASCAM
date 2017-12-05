import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
import matplotlib
matplotlib.use('TkAgg')
import model as backend
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                            NavigationToolbar2TkAgg)
import plotting

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


        self.filenamefull = tk.StringVar()
        self.filename = tk.StringVar()
        self.headerlength = tk.StringVar()
        self.datatype = tk.StringVar()
        self.samplingrate = tk.StringVar()
        self.path = tk.StringVar()
        self.filetypefull = tk.StringVar()
        self.filetype = tk.StringVar()

        # dictionary for the data
        self.data = dict()
        # datakey of the current displayed data
        self.datakey = 'raw_'
        # episode number of the currently displayed episode
        self.Nepisode = 0

        self.create_widgets()
        self.configure_grid()

        self.commandbar.loadbutton.focus()

        if bintest:
        ### testing mode that uses simulated data, the data is copied and
        ### multiplied with random numbers to create additional episodes
            if VERBOSE:
                print('Test mode with binary data')
            self.data = backend.Model(
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
            self.uptdate_list()
            self.update_plot()
        elif axotest:
            if VERBOSE:
                print('Test mode with axograph data')
            self.data = backend.Model(filename = 'data/170404 015.axgd',
                                        filetype = 'axo')
            self.uptdate_list()
            # self.update_plot()
        elif mattest:
            if VERBOSE:
                print('Test mode with matlab data.')
            self.data = backend.Model(
                                filename = 'data/171025 020 Copy Export.mat',
                                filetype='mat')
            self.uptdate_list()
            self.draw()

        self.bind("<Configure>", self.resize_plot)
        # this line calls update plot when it is run


    def resize_plot(self,*args,**kwargs):
        """
        Draw the plot again when the window size is changed.

        """
        if VERBOSE: print('Resizing plot')
        self.update_plot()

    def create_widgets(self):
        """
        Create the contents of the main window.
        """
        self.commandbar = Commandframe(self)
        self.histogramFrame = HistogramFrame(self)
        self.plots = Plotframe(self)
        self.manipulations = Manipulations(self)
        self.espisodeList = EpisodeList(self)

    def configure_grid(self):
        """
        Geometry management of the elements in the main window.
        """
        self.grid(column=0, row=0, sticky=tk.N+tk.S+tk.E+tk.W)
        ### the first argument refer to position in the main window
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.commandbar.grid(row=0,column=0, columnspan=3, padx=5, pady=5,
                             sticky=tk.N+tk.W)
        self.plots.grid(row=1, rowspan=3, column=0,columnspan=3, padx=5,
                        pady=5, sticky=tk.W)
        ### the values in col/rowconfig refer to the position of the elements
        ### WITHIN the widgets
        self.plots.grid_rowconfigure(0, weight=1)
        self.plots.grid_columnconfigure(0, weight=1)
        self.manipulations.grid(row=4, column=0, columnspan=3, padx=5, pady=5,
                                sticky=tk.S+tk.W)
        self.espisodeList.grid(row=1, rowspan=3, column=3)
        for i in range(2):
            self.espisodeList.grid_columnconfigure(i, weight=1)
            self.espisodeList.grid_rowconfigure(i, weight=1)

        self.histogramFrame.grid(row=0,column=4,rowspan=3,columnspan=3,
                                    sticky=tk.E)

    def draw(self):
        """
        Draw all the plots anew.
        """
        if VERBOSE: print('called `draw`')
        self.update_plot()
        self.draw_histogram()
    def update_plot(self):
        if VERBOSE: print('call `update_plot`')
        if self.data:
            if VERBOSE: print('Calling `plot`, `self.data` is `True`')
            self.plots.plot()
        else:
            if VERBOSE: print('Cannot plot, `self.data` is `False`')
            pass
    def draw_histogram(self):
        if self.data:
            if VERBOSE: print('Calling histogram, `self.data` is `True`.')
            self.histogramFrame.draw_histogram()
        else:
            if VERBOSE: print('Cannot draw histogram, `self.data` is `False`')
            pass
    def uptdate_list(self):
        if VERBOSE: print('call `uptdate_list`')
        self.espisodeList.create_list()
    def quit(self):
        self.master.destroy()
        self.master.quit()


class Commandframe(ttk.Frame):
    """
    This frame will contain all the command buttons such as loading
    data and plotting
    """
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.create_widgets()
    def create_widgets(self):
        self.loadbutton = ttk.Button(self, text="Load file",
                                     command=self.load_dialog
                                     )
        self.loadbutton.grid(column=1,row=1,sticky=tk.N+tk.E)
        self.plotbutton = ttk.Button(self, text="Plot",
                                     command=self.parent.update_plot)
        self.plotbutton.grid(column=2,row=1,sticky=tk.N)

        self.histbutton = ttk.Button(self, text="Histogram",
                                     command=self.parent.draw_histogram)
        self.histbutton.grid(column=3,row=1,sticky=tk.N)

    def load_dialog(self):
        subframe = Loadframe(self.parent)

class HistogramFrame(ttk.Frame):
    """
    Frame for the all points histogram.
    """
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.fig = plt.figure(1, figsize=(8,5))
        canvasHist = FigureCanvasTkAgg(self.fig, self)
        canvasHist.show()
        canvasHist.get_tk_widget().grid(row=0,column=0)
        self.canvas = canvasHist


    def draw_histogram(self, active = True, deviation = .05, bins = 200, **kwargs):
        if VERBOSE: print("`draw_histogram`")
        series = self.parent.data[self.parent.datakey]
        time = series[0]['time']
        piezo_list = [episode['piezo'] for episode in series ]
        trace_list = [episode['trace'] for episode in series ]

        plot = self.fig.add_subplot(111)
        hist,bins, _, _, _ = plotting.all_point_histogram(time,piezo_list,
                                            trace_list, active, deviation,
                                            bins, **kwargs)
        width = (bins[1] - bins[0])
        center = (bins[:-1] + bins[1:]) / 2
        plot.bar(center, hist, width=width)
        self.canvas.draw()
        plot.clear()

class Plotframe(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.fig = plt.figure(2, figsize=(10,5))
        canvasPlot = FigureCanvasTkAgg(self.fig, self)
        canvasPlot.show()
        canvasPlot.get_tk_widget().grid(row=0,column=0)
        self.canvas = canvasPlot
        # self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        # self.toolbar.update()
        # self.canvas._tkcanvas.pack()

    def plot(self):
        if self.parent.data:
            if VERBOSE:
                print('`data` exists, plotting...')
                print('datakey = '+self.parent.datakey)
                print('Nepisode = '+str(self.parent.Nepisode))
            episode = self.parent.data[
                            self.parent.datakey][self.parent.Nepisode]
            x = episode['time']
            ys = [episode['trace']]
            unitCurrent = 'pA'
            unitTime = 'ms'
            ylabels = ["Current ["+unitCurrent+"]"]
            if episode['piezo'] is not None:
                if VERBOSE: print('`piezo` found')
                unitPiezoVoltage = 'V'
                ys.append(episode['piezo'])
                ylabels.append("Piezo ["+unitPiezoVoltage+']')
            ## commented out the below code as command voltage is not
            ## interesting to plot
            if episode['commandVoltage'] is not None:
                if VERBOSE: print('`commandVoltage` found')
                ys.append(episode['commandVoltage'])
                unitCommandVoltage = 'V'
                ylabels.append("Command ["+unitCommandVoltage+']')
        else:
            if VERBOSE: print("no data found, plotting dummy")
            x = [0,1]
            ys = [[0,0],[0,0],[0,0]]

        self.subplots = []
        for i, (y, ylabel) in enumerate(zip(ys, ylabels)):
            if VERBOSE: print("calling matplotlib")
            self.subplots.append(self.fig.add_subplot(len(ys),1,i+1))
            plt.plot(x,y)
            plt.ylabel(ylabel)
        self.canvas.draw()
        for subplot in self.subplots:
            subplot.clear()

class Manipulations(ttk.Frame):
    """docstring for Manipulations"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.cutoffFrequency = tk.StringVar()
        self.cutoffFrequency.set(1000)
        self.piezoSelection = True

        self.create_widgets()

    def create_widgets(self):
        self.filterallbutton = ttk.Button(self, text="Filter all",
                                     command=self.filter_series)
        self.filterallbutton.grid(column=1,row=0,sticky=())

        self.filterbutton = ttk.Button(self, text="Filter",
                                                    command=self.apply_filter)
        self.filterbutton.grid(column=0,row=0,sticky=())

        self.cutoffentry = ttk.Entry(self, width=7, textvariable=(
                                                        self.cutoffFrequency))
        self.cutoffentry.grid(column=1,row=1)
        ttk.Label(self, text="Filter Frequency (Hz):").grid(column=0,
                                                        row=1,
                                                        sticky=(tk.W))
        self.baselineButton = ttk.Button(self,text='baseline',
                                        command=self.baseline_correct_frame)
        self.baselineButton.grid(row = 0, column=2,columnspan=2)

        self.piezoCheckbutton = ttk.Checkbutton(self, text='Use Piezo', 
                            variable = self.piezoSelection)
        self.piezoCheckbutton.grid(row=1, column=2, sticky=tk.W+tk.N)

        self.intervalCheckbutton = ttk.Checkbutton(self, text='Use Intervals', 
                            variable = (not self.piezoSelection))
        self.intervalCheckbutton.grid(row=1, column=3, sticky=tk.E+tk.N)

    def filter_series(self):
        if VERBOSE: print('going to filter all episodes')
        #convert textvar to float
        cutoffFrequency = float(self.cutoffFrequency.get())
        self.parent.data.call_operation('FILTER_',cutoffFrequency)
        if VERBOSE: print('called operation')
        self.parent.datakey=self.parent.data.currentDatakey
        if VERBOSE: print('updating list and plots')
        self.parent.uptdate_list()
        self.parent.draw()

    def baseline_correct_frame(self):
        if VERBOSE: 
            print('Opening the baseline corrention frame.')
            print('piezoSelection is ',self.piezoSelection)
        subframe = BaselineFrame(self)

    def apply_filter(self):
        pass

class BaselineFrame(tk.Toplevel):
    """
    Temporary frame in which to chose how and based on what points
    the baseline correction should be performed.
    """
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.title("Baseline correction.")

        self.baselineMethod = tk.StringVar()
        self.baselineMethod.set('poly')
        self.baselineDegree = tk.StringVar()
        self.baselineDegree.set(1)

        if self.parent.piezoSelection:
            self.percentDeviation = tk.StringVar()
            self.percentDeviation.set(.05)
            self.create_piezo_widgets()
        else:
            self.create_interval_widgets()
        self.create_widgets()


    def create_widgets(self):
        """
        Creates all widgets that apply to both modes.
        """
        ttk.Label(self,text='method').grid(column=0,row=1)
        ttk.Entry(self,width=7,textvariable=self.baselineMethod).grid(
                                                            column=2,row = 1)

        ttk.Label(self,text='degree').grid(column=0,row=1)
        ttk.Entry(self,width=8,textvariable=self.baselineDegree)
        pass

    def create_piezo_widgets(self):
        """
        Create widgets for the piezo selection of time points.
        """
        ttk.Label(self, text='% deviation:').grid(column=0, row=0,
                                           sticky = (tk.N, tk.W))
        ttk.Entry(self,width=7,textvariable=self.percentDeviation)
        pass


    def create_interval_widgets(self):
        """
        Create widgets for specifying intervals to the select the time points.
        """
        pass


        # # first row - filename and button for choosing file
        # ttk.Label(self, text='File:').grid(column=1, row=1,
        #                                    sticky = (tk.N, tk.W))

        # filenamelabel = ttk.Label(self,
        #                           textvariable=self.parent.filename)
        # filenamelabel.grid(column=2, row=1, sticky=tk.N)

        # self.loadbutton = ttk.Button(self, text='Select file',
        #                              command=self.get_file)
        # self.loadbutton.grid(column = 3, row = 1, sticky=(tk.N, tk.E))

        # #second row - show filepath
        # ttk.Label(self, text='Path:').grid(column=1, row=2,
        #                                    sticky = tk.W)
        # ttk.Label(self, textvariable=self.parent.path).grid(column=2,
        #           row=2)

        # #third row - show filetype
        # ttk.Label(self, text='Filetype:').grid(column=1, row=3,
        #                                        sticky = tk.W)
        # ttk.Label(self, textvariable=self.parent.filetypefull).grid(
        #                         column=2, row=3, sticky=(tk.W, tk.E))
    # def apply_correction(self):
    #     if VERBOSE: print('applying baseline correction')
    #     baselineDegree = int(self.baselineDegree.get())
    #     self.parent.data.call_operation('BC_',)

class EpisodeList(ttk.Frame):
    """docstring for EpisodeList"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.create_list()
    def onselect_plot(self,event):
        self.parent.Nepisode = int(event.widget.curselection()[0])
        self.parent.update_plot()
    def create_list(self):
        self.Scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.Scrollbar.grid(column=1, row=1, rowspan=3, sticky=tk.N+tk.S+tk.E)
        self.episodelist = tk.Listbox(self, bd=2,
                                    yscrollcommand=self.Scrollbar.set)
        self.episodelist.grid(row=0, rowspan=3, sticky=tk.S+tk.W+tk.N)
        self.episodelist.bind('<<ListboxSelect>>', self.onselect_plot)
        self.episodelist.config(height=30)
        if self.parent.data:
            for episode in self.parent.data[self.parent.datakey]:
                self.episodelist.insert(tk.END,
                                "episode #"+str(episode.nthEpisode))
        self.Scrollbar['command'] = self.episodelist.yview
    # def create_menu(self):
        
class Loadframe(tk.Toplevel):
    """
    Temporary frame that gets the file and information about it.
    Select file and load it by clicking 'ok' button, in case of binary
    file another window pops up to ask for additional parameters.
    """
    def __init__(self, parent):
        tk.Toplevel.__init__(self,parent)
        self.parent = parent
        self.title("Select file")
        self.create_widgets()
        self.loadbutton.focus()

        #reset the file variables every time a load dialog is created
        self.parent.filetype.set('')
        self.parent.filename.set('')
        self.parent.samplingrate.set('')
        self.parent.path.set('')

    def create_widgets(self):
        # first row - filename and button for choosing file
        ttk.Label(self, text='File:').grid(column=1,row=1,sticky=(tk.N, tk.W))

        filenamelabel = ttk.Label(self, textvariable=self.parent.filename)
        filenamelabel.grid(column=2, row=1, sticky=tk.N)

        self.loadbutton = ttk.Button(self, text='Select file', 
                                     command=self.get_file)
        self.loadbutton.grid(column = 3, row = 1, sticky=(tk.N, tk.E))

        #second row - show filepath
        ttk.Label(self, text='Path:').grid(column=1, row=2, sticky = tk.W)
        ttk.Label(self, textvariable=self.parent.path).grid(column=2, row=2)

        #third row - show filetype
        ttk.Label(self, text='Filetype:').grid(column=1, row=3, sticky = tk.W)
        ttk.Label(self, textvariable=self.parent.filetypefull).grid(column=2, 
                                                   row=3, sticky=(tk.W, tk.E))
        ###### lets see if this way of line splitting works

        #fourth row - enter sampling rate
        self.samplingentry = ttk.Entry(self, width=7,
                                       textvariable=self.parent.samplingrate)
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
        if self.parent.filetype.get() == 'bin':
            binframe = Binaryquery(self)

        elif (self.parent.filetype.get() == 'axo'
              or self.parent.filetype.get() == 'mat'):
            self.parent.data = backend.Model(
                                    self.parent.filenamefull.get(),
                                    self.parent.samplingrate.get(),
                                    self.parent.filetype.get())
            self.parent.datakey = self.parent.data.currentDatakey
            self.parent.uptdate_list()
            self.parent.draw()
            self.destroy()

    def get_file(self):
        """
        Get data by clicking.
        Relies on tkinter and gets name and type of the file
        """
        filename = askopenfilename()
        self.parent.filenamefull.set(filename)
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

        self.parent.filename.set(filename[slash:])
        self.parent.path.set(filename[:slash])
        extension=filename[period:]

        if extension == 'bin':
            self.parent.filetype.set('bin')
            self.parent.filetypefull.set('binary')

        elif extension == 'axgd':
            self.parent.filetype.set('axo')
            self.parent.filetypefull.set('axograph')

        elif extension == 'mat':
            self.parent.filetype.set('mat')
            self.parent.filetypefull.set('matlab')

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
        self.parent.data = backend.Model(self.parent.filenamefull.get(),
                                         self.parent.samplingrate.get(),
                                         self.parent.filetype.get(),
                                         self.parent.headerlength.get(),
                                         datatype)
        self.parent.uptdate_list()
        self.parent.update_plot()
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
