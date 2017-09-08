import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
import matplotlib
matplotlib.use('TkAgg')
import model, os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

cwd = os.getcwd()
testing=True

class Main(ttk.Frame):
    """
    Main frame of the GUI for ASCAM.
    All the variables and objects are stored as attributes of this object to
    make refering them uniform.
    """
    ###create main frame that will hold all permanent widgets
    def __init__(self, master):
        #mainframe configuration
        ttk.Frame.__init__(self, master)
        self.master = master
        self.master.protocol('WM_DELETE_WINDOW', quit)
        self.master.geometry("500x300+500+200")
        # self.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        # self.columnconfigure(0, weight=1)
        # self.rowconfigure(0, weight=1)
        #file parameters
        self.filenamefull = tk.StringVar()
        self.filename = tk.StringVar()
        self.headerlength = tk.StringVar()
        self.datatype = tk.StringVar()
        self.samplingrate = tk.StringVar()
        self.path = tk.StringVar()
        self.filetypefull = tk.StringVar()
        self.filetype = tk.StringVar()        
        #backend interface variable
        self.recording = None
        ## frame contents
        # command bar
        self.commandbar = Commandframe(self)
        self.commandbar.grid(column=1,row=1,sticky=(tk.E, tk.N, tk.W))
        self.commandbar.loadbutton.focus()
        # plot
        self.plots = Plotframe(self)
        # options
        self.options = Options(self)
        # list of episodes
        self.List = EpisodeList(self, 'nothing yet')
    def uptdate_list(self, datakey):
        self.List = EpisodeList(self, datakey)
    def quit(self):
        """
        Close all windows and exit the main loop
        """
        self.master.destroy()
        self.master.quit()
    
class Commandframe(ttk.Frame):
    """
    This frame will contain all the command buttons such as loading data and 
    plotting
    """
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.grid(columnspan=3, row=1, sticky=(tk.N, tk.W, tk.E))
        # self.rowconfigure(0, weight=1)
        self.create_widgets()
    def create_widgets(self):
        self.loadbutton = ttk.Button(self, text="Load file", command=self.load_dialog)
        self.loadbutton.grid(column=1,row=1,sticky=(tk.N, tk.E))
        self.plotbutton = ttk.Button(self, text="Plot", command=self.create_plot)
        self.plotbutton.grid(column=2,row=1,sticky=(tk.N))
    def load_dialog(self):
        subframe = Loadframe(self.parent)
    def create_plot(self):
        if testing:
            self.parent.recording = model.Recording(cwd+'/data/sim1600.bin', 4e4, 'bin', 3072, np.int16)
            self.parent.recording.load_data()
        if self.parent.recording==None:
            pass
        else:
            episode = self.parent.recording.data['raw'][0]
            self.parent.plots.plot(episode)
        
class Plotframe(ttk.Frame):
    """
    Frame that will contain plots.
    For now `episode` is the specific episode of which the current trace will be
    plotted
    """
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.grid(columnspan=3, row=2, sticky=(tk.W, tk.E))
        self.plot()
    def plot(self, episode=False):
        fig = plt.figure(figsize=(5,2))
        if episode:
            x = episode.time
            y = episode.currentTrace
        else:
            x = [0,1]
            y = [0,0]
        plt.plot(x,y)
        canvas = FigureCanvasTkAgg(fig, self)
        canvas.show()
        canvas.get_tk_widget().pack() #this backend seems to not work with .grid management
        toolbar = NavigationToolbar2TkAgg(canvas, self)
        toolbar.update()
        canvas._tkcanvas.pack()

class Options(ttk.Frame):
    """docstring for Options"""
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.grid(row=3, columnspan=3, sticky=(tk.S,tk.W))
        ttk.Label(self, text="buttons for filtering and the other cool stuff will be").grid()

class EpisodeList(ttk.Frame):
    """docstring for EpisodeList"""
    def __init__(self, parent, datakey):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.grid(row=1, rowspan=2,column=4,sticky=(tk.E))
        # self.create_list(datakey)
        ttk.Label(self, text="some text").grid()
        ###################################################################################################################################################
        
        ###################################################################################################################################################
    def create_list(self, datakey):
        self.episodelist = tk.Listbox(self)
        self.episodelist.grid(rowspan=2,column=10,sticky=tk.W)
        if self.parent.recording:
            for episode in self.parent.recording.data[datakey]:
                self.episodelist.insert(tk.END, "episode "+str(episode.nthEpisode))
        else:
            for i in range(5):
                self.episodelist.insert(tk.END, "placeholder")

class Loadframe(tk.Toplevel):
    """ 
    Temporary frame that gets the file and information about it.
    Select file and load it by clicking 'ok' button, in case of binary file
    another window pops up to ask for additional parameters.
    """
    def __init__(self, parent):
        tk.Toplevel.__init__(self,parent)
        self.parent = parent
        self.title("Select file")
        self.padding="3 3 12 12"
        self.create_widgets()
        self.loadbutton.focus()

    def create_widgets(self):
        # first row - filename and button for choosing file
        ttk.Label(self, text='File:').grid(column=1, row=1, sticky = (tk.N, tk.W))
        filenamelabel = ttk.Label(self, textvariable=self.parent.filename)
        filenamelabel.grid(column=2, row=1, sticky=tk.N)
        self.loadbutton = ttk.Button(self, text='Select file', command=self.get_file)
        self.loadbutton.grid(column = 3, row = 1, sticky=(tk.N, tk.E))
        #second row - show filepath
        ttk.Label(self, text='Path:').grid(column=1, row=2, sticky = tk.W)
        ttk.Label(self, textvariable=self.parent.path).grid(column=2, row=2)
        #third row - show filetype
        ttk.Label(self, text='Filetype:').grid(column=1, row=3, sticky = tk.W)
        ttk.Label(self, textvariable=self.parent.filetypefull).grid(column=2, row=3, sticky=(tk.W, tk.E))
        #fourth row - enter sampling rate
        self.samplingentry = ttk.Entry(self, width=7, textvariable=self.parent.samplingrate)
        self.samplingentry.grid(column=2,row=4)
        ttk.Label(self, text="Samplingrate (Hz):").grid(column=1,row=4,sticky=(tk.W))
        #fifth row - ok button to close and go to next window
        self.okbutton = ttk.Button(self, text="Ok", command=self.ok_button)
        self.okbutton.grid(column=1, row=5, sticky=(tk.S, tk.W))
        self.closebutton = ttk.Button(self, text="Quit", command=self.parent.quit)
        self.closebutton.grid(column=3, row=5, sticky=(tk.S, tk.E))

    def ok_button(self):
        if self.parent.filetype.get() == 'bin':
            binframe = Binaryquery(self.parent)
        elif self.parent.filetype.get() == 'axo':
            self.parent.recording = model.Recording(self.parent.filenamefull.get(), self.parent.samplingrate.get(), self.parent.filetype.get())
            self.parent.recording.load_data()
        self.destroy()

    def get_file(self):
        """
        Get data by clicking
        relies on tkinter and gets name and type of the file
        """
        fn = askopenfilename()
        self.parent.filenamefull.set(fn)
        extension = ''
        i = 0
        N = len(fn)
        for char in fn[::-1]:
            if char=='.': 
            	period = N-i
            if char=='/':
                slash = N-i
                break
            i+=1
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
    If the filetype is '.bin' this asks for the additional parameters such as 
    the length of the header (can be zero) and the datatype (should be given
    as numpy type, such as "np.int16")
    """
    def __init__(self, parent):
        #frame configuration
        tk.Toplevel.__init__(self,parent)
        self.parent = parent
        self.padding="3 3 12 12"
        self.title("Additional parameters for binary file")
        #initialize content
        self.create_widgets()
        self.headerentry.focus()
    def create_widgets(self):
        # #entry field for headerlength
        self.headerentry = ttk.Entry(self, width=7, textvariable=self.parent.headerlength)
        self.headerentry.grid(column=3,row=1,sticky=(tk.W,tk.N))
        ttk.Label(self, text="Headerlength:").grid(column=2,row=1,sticky=(tk.N))
        #entry field for filetype
        self.typeentry = ttk.Entry(self, width=7, textvariable=self.parent.datatype)
        self.typeentry.grid(column=3,row=2,sticky=(tk.W,tk.S))
        ttk.Label(self, text="Datatype:").grid(column=2,row=2,sticky=tk.S)
        #'ok' and 'cancel button
        self.okbutton = ttk.Button(self, text="Ok", command=self.ok_button)
        self.okbutton.grid(columnspan=2, row=3, sticky=(tk.S, tk.W))
    def ok_button(self):
        # if self.parent.datatype.get()=='np.int16':
        datatype = np.int16 #this is here because stringvar.get returns a string which numpy doesnt understand
        self.parent.recording = model.Recording(self.parent.filenamefull.get(), self.parent.samplingrate.get(), self.parent.filetype.get(), self.parent.headerlength.get(), datatype)
        self.parent.recording.load_data()
        self.destroy()

def gui_main():
    ### initialize tkinter root window
    root = tk.Tk()
    ### initialize mainframe
    main = Main(root)
    for child in root.winfo_children(): child.grid_configure(padx=5, pady=5)        
    root.mainloop()

if __name__ == '__main__':
  	gui_main()