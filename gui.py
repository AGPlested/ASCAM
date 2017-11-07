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
VERBOSE = False
axotest = False
bintest = False

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
        # root.geometry("768x600+200+200")
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

        self.data = dict()
        self.datakey = 'raw_'
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
            self.data = backend.Model()
            self.uptdate_list()
            self.update_plot()

        self.bind("<Configure>", self.resize_plot)
        ### if this binding is done before the testing check the plot will
        ### initially be empty

    def resize_plot(self,*args,**kwargs):
        """
        Draw the plot again when the window size is changed.
        """
        self.update_plot()

    def create_widgets(self):
        """
        Create the contents of the main window.
        """
        self.commandbar = Commandframe(self)
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
        self.espisodeList.grid(row=1, rowspan=3, column=3, sticky=tk.E)
        for i in range(2):    
            self.espisodeList.grid_columnconfigure(i, weight=1)
            self.espisodeList.grid_rowconfigure(i, weight=1)

    def update_plot(self):
        if VERBOSE: print('call `update_plot`')
        if self.data:
            if VERBOSE: print('`self.data` is `True`')
            self.plots.plot()
        else:
            if VERBOSE: print('`self.data` is `False`')
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
    def load_dialog(self):
        subframe = Loadframe(self.parent)
        

class Plotframe(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.fig = plt.figure(figsize=(10,5))
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=0,column=0)
        self.canvas.show()
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
            if episode['commandVoltage'] is not None: 
                if VERBOSE: print('`commandVoltage` found')
                ys.append(episode['commandVoltage'])
                unitCommandVoltage = 'V'
                ylabels.append("Command ["+unitCommandVoltage+']')
        else:
            if VERBOSE:
                print("no data found, plotting dummy")
            x = [0,1]
            ys = [[0,0],[0,0],[0,0]]

        subplots = []
        for i, (y, ylabel) in enumerate(zip(ys, ylabels)):
            if VERBOSE: print("calling matplotlib")
            subplots.append(self.fig.add_subplot(len(ys),1,i+1))
            plt.plot(x,y)
            plt.ylabel(ylabel)

        self.canvas.draw()
        for subplot in subplots:
            subplot.clear()


class Manipulations(ttk.Frame):
    """docstring for Manipulations"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.cutoffFrequency = tk.StringVar()
        self.cutoffFrequency.set(1000)
        # ttk.Label(self, text="more buttons").grid(column=2)
        self.create_widgets()

    def create_widgets(self):
        self.filterallbutton = ttk.Button(self, text="Filter all", 
                                     command=(
                                            lambda: self.filterall(
                                                self.cutoffFrequency)))
        self.filterallbutton.grid(column=1,row=1,sticky=())

        self.filterbutton = ttk.Button(self, text="Filter", 
                                     command=(lambda: self.apply_filter(
                                                    self.cutoffFrequency)))
        self.filterbutton.grid(column=0,row=1,sticky=())

        self.cutoffentry = ttk.Entry(self, width=7, textvariable=(
                                                        self.cutoffFrequency))
        self.cutoffentry.grid(column=1,row=0)
        ttk.Label(self, text="Filter cutoffFrequency (Hz):").grid(column=0,
                                                        row=0,
                                                        sticky=(tk.W))
       
    def filterall(self, cutoffFrequency):
        newdatakey = self.parent.data.filter_data(
                                    filterfreq=float(cutoffFrequency.get()), 
                                    datakey=self.parent.datakey)
        self.parent.datakey=newdatakey
        self.parent.update_plot()

    def apply_filter(self,cutoffFrequency):
        pass


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
        self.Scrollbar.grid(column=1, row=0, rowspan=3, sticky=tk.N+tk.S+tk.E)
        self.episodelist = tk.Listbox(self, bd=2,
                                    yscrollcommand=self.Scrollbar.set)
        self.episodelist.grid(row=0, rowspan=3, sticky=tk.S+tk.W+tk.N)
        self.episodelist.bind('<<ListboxSelect>>', self.onselect_plot)
        self.episodelist.config(height=30)
        if self.parent.data:
            for episode in self.parent.data[self.parent.datakey]:
                self.episodelist.insert(tk.END, 
                                "episode "+str(episode.nthEpisode))
        self.Scrollbar['command'] = self.episodelist.yview


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

    def create_widgets(self):
        # first row - filename and button for choosing file
        ttk.Label(self, text='File:').grid(column=1, row=1, 
                                           sticky = (tk.N, tk.W))
        
        filenamelabel = ttk.Label(self, 
                                  textvariable=self.parent.filename)
        filenamelabel.grid(column=2, row=1, sticky=tk.N)
        
        self.loadbutton = ttk.Button(self, text='Select file', 
                                     command=self.get_file)
        self.loadbutton.grid(column = 3, row = 1, sticky=(tk.N, tk.E))
        
        #second row - show filepath
        ttk.Label(self, text='Path:').grid(column=1, row=2, 
                                           sticky = tk.W)
        ttk.Label(self, textvariable=self.parent.path).grid(column=2, 
                  row=2)
        
        #third row - show filetype
        ttk.Label(self, text='Filetype:').grid(column=1, row=3, 
                                               sticky = tk.W)
        ttk.Label(self, textvariable=self.parent.filetypefull).grid(
                                column=2, row=3, sticky=(tk.W, tk.E))
        ###### lets see if this way of line splitting works
        
        #fourth row - enter sampling rate
        self.samplingentry = ttk.Entry(self, width=7, 
                                       textvariable=(
                                            self.parent.samplingrate))
        self.samplingentry.grid(column=2,row=4)
        ttk.Label(self, text="Samplingrate (Hz):").grid(column=1,
                                                        row=4,
                                                        sticky=(tk.W))
        
        #fifth row - ok button to close and go to next window
        self.okbutton = ttk.Button(self, text="Load", 
                                   command=self.ok_button)
        self.okbutton.grid(column=1, row=5, sticky=(tk.S, tk.W))

        self.closebutton = ttk.Button(self, text="Close", 
                                      command=self.destroy)
        self.closebutton.grid(column=3, row=5, sticky=(tk.S, tk.E))

    def ok_button(self):
        if self.parent.filetype.get() == 'bin':
            binframe = Binaryquery(self)

        elif self.parent.filetype.get() == 'axo':
            self.parent.data = backend.Model(
                                    self.parent.filenamefull.get(), 
                                    self.parent.samplingrate.get(), 
                                    self.parent.filetype.get()) 
            self.parent.uptdate_list()
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
        if 'v' in sys.argv:
            VERBOSE = True
    except IndexError:
        pass

    GUI.run()