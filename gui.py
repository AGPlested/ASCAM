import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
import matplotlib
matplotlib.use('TkAgg')
import model
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
                                               NavigationToolbar2TkAgg
                                               )


class Main(ttk.Frame):
    """
    Main frame of the GUI for ASCAM.
    All the variables and objects are stored as attributes of this 
    object to make refering them uniform.
    All other widgets will be children of this frame.
    """
    @classmethod
    def run(cls):
        root = tk.Tk()
        root.geometry("768x300+500+200")
        root.protocol('WM_DELETE_WINDOW', quit)
        root.title("ASCAM")
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        main = cls(root)
        root.mainloop()

    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.master = master

        self.grid(column=0, row=0, sticky=(tk.N, tk.W))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0,weight=1)
        self.filenamefull = tk.StringVar()
        self.filename = tk.StringVar()
        self.headerlength = tk.StringVar()
        self.datatype = tk.StringVar()
        self.samplingrate = tk.StringVar()
        self.path = tk.StringVar()
        self.filetypefull = tk.StringVar()
        self.filetype = tk.StringVar()        

        self.recording = dict()
        self.datakey = 'raw'
        self.Nepisode = 0

        commandbargridoptions = {'sticky':(tk.N, tk.W), 'padx':5, 
                                 'pady':5}
        self.commandbar = Commandframe(self, commandbargridoptions)

        self.commandbar.loadbutton.focus()

        plotframegridoptions = {'row':2,'columnspan':3,'pady':5,
                                'padx':5}
        self.plots = Plotframe(self, plotframegridoptions)
        # self.plots.grid_rowconfigure(0,weight=1)

        self.manipulations = manipulations(self)
        self.manipulations.grid(row=3, columnspan=3, padx=5, pady=5, 
                          sticky=(tk.S,tk.W))

        self.List = EpisodeList(self)
        self.List.grid(row=2,column=4,sticky=(tk.E))

        if bintest:
            self.recording = model.Recording(
                                    cwd+'/data/sim1600.bin', 4e4, 
                                    'bin', 3072, np.int16)
            self.uptdate_list()
            self.update_plot()
        elif axotest:
            self.recording = model.Recording()
            self.uptdate_list()
            self.update_plot()
    def update_plot(self):
        if self.recording:
            self.plots.plot()
        else:
            pass
    def uptdate_list(self):
        self.List.create_list()
    def quit(self):
        self.master.destroy()
        self.master.quit()
    

class Commandframe(ttk.Frame):
    """
    This frame will contain all the command buttons such as loading 
    data and plotting
    """
    def __init__(self, parent,options):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.grid(**options)
        self.create_widgets()
    def create_widgets(self):
        self.loadbutton = ttk.Button(self, text="Load file", 
                                     command=self.load_dialog
                                     )
        self.loadbutton.grid(column=1,row=1,sticky=(tk.N, tk.E))
        self.plotbutton = ttk.Button(self, text="Plot", 
                                     command=self.parent.update_plot)
        self.plotbutton.grid(column=2,row=1,sticky=(tk.N))
    def load_dialog(self):
        subframe = Loadframe(self.parent)
        

class Plotframe(ttk.Frame):
    def __init__(self, parent, options):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.grid(**options)

        self.fig = plt.figure(1, figsize=(5,5))
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().grid(row=0,column=0)
        self.canvas.show()
        # self.toolbar = NavigationToolbar2TkAgg(self.canvas, self)
        # self.toolbar.update()
        # self.canvas._tkcanvas.pack()
        self.plot()

    def plot(self):
        if self.parent.recording:
            episode = self.parent.recording[
                            self.parent.datakey][self.parent.Nepisode]
            x = episode.time
            y = []
            y.append(episode.currentTrace)
            if episode.piezo is not None: 
                y.append(episode.piezo)
            if episode.commandVoltage is not None: 
                y.append(episode.commandVoltage)
        else:
            x = [0,1]
            y = [[0,0]]
        for i, y in enumerate(y):
            subplot=self.fig.add_subplot(3,1,i+1)
            subplot.plot(x,y)
        self.canvas.draw()
        subplot.clear()


class manipulations(ttk.Frame):
    """docstring for Manipulations"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        ttk.Label(self, text="mode buttons").grid(column=2)


class EpisodeList(ttk.Frame):
    """docstring for EpisodeList"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        # self.create_list()
    def onselect_plot(self,event):
        self.parent.Nepisode = int(event.widget.curselection()[0])
        self.parent.update_plot()
    def create_list(self):
        self.episodelist = tk.Listbox(self)
        self.episodelist.grid(row=1,column=1,sticky=tk.E)
        self.episodelist.bind('<<ListboxSelect>>', self.onselect_plot)
        if self.parent.recording:
            for episode in self.parent.recording[self.parent.datakey]:
                self.episodelist.insert(tk.END, 
                                "episode "+str(episode.nthEpisode))


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
            self.parent.recording = model.Recording(
                                    self.parent.filenamefull.get(), 
                                    self.parent.samplingrate.get(), 
                                    self.parent.filetype.get()) 
            self.parent.uptdate_list()
            self.parent.update_plot()
            self.destroy()

    def get_file(self):
        """
        Get data by clicking
        relies on tkinter and gets name and type of the file
        """
        fn = askopenfilename()
        self.parent.filenamefull.set(fn)
        extension = ''

        N = len(fn)
        for i, char in enumerate(fn[::-1]):
            if char=='.': 
            	period = N-i
            if char=='/':
                slash = N-i
                break

        self.parent.filename.set(fn[slash:])
        self.parent.path.set(fn[:slash])
        extension=fn[period:]

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
        self.parent.recording = model.Recording(
                                    self.parent.filenamefull.get(), 
                                    self.parent.samplingrate.get(), 
                                    self.parent.filetype.get(), 
                                    self.parent.headerlength.get(),
                                    datatype)
        self.parent.uptdate_list()
        self.parent.update_plot()
        self.loadframe.destroy()
        self.destroy()

def gui_main():
    root = tk.Tk()
    main = Main(root)
    for child in root.winfo_children(): 
        child.grid_configure(padx=5, pady=5)        
    root.mainloop()

if __name__ == '__main__':
    import sys
    import os
    cwd = os.getcwd()
    try:
        if sys.argv[1]=='axo':
            axotest = True
            bintest=False
        elif sys.argv[1]=='bin':
            bintest=True
            axotest=False
    except IndexError:
        pass
    Main.run()