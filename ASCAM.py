"""
ASCAM for processing and analysis of data from single ion channels.

Style:
`ClassNames` have the first letter of each word in them capitalized
`classInstances` and `variableNames` start with a lower case letter but have
the first letter of all consecutive words capitalized
`method_names` are all lower case and different words are seperated by '_'

"""

import gui

if __name__ == '__main__':
    gui.cwd = os.getcwd()
    try:
        if 'axo' in sys.argv:
            gui.axotest = True
        elif 'bin' in sys.argv:
            gui.bintest = True
        if 'v' in sys.argv:
            gui.VERBOSE = True
    except IndexError:
        pass
    gui.MainWindow.run()
    print(type(mainWindow))

## moving the hard coded parameters for testing from the gui is difficult 
## because once the tkinter mainloop is running no more code will be executed;
## the interaction of GUI with anything else is purely event based
