"""
ASCAM for processing and analysis of data from single ion channels.

Style:
`ClassNames` have the first letter of each word in them capitalized
`classInstances` and `variableNames` start with a lower case letter but have
the first letter of all consecutive words capitalized
`method_names` are all lower case and different words are seperated by '_'

"""

from gui import GUI
import sys

VERBOSE = False
axotest = False
bintest = False
mattest = False

if __name__ == '__main__':
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

    GUI.run(VERBOSE,axotest,bintest,mattest)
## moving the hard coded parameters for testing from the gui is difficult
## because once the tkinter mainloop is running no more code will be executed;
## the interaction of GUI with anything else is purely event based
