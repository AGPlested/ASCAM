"""
ASCAM for processing and analysis of data from single ion channels.

Style:
`ClassNames` have the first letter of each word in them capitalized
`classInstances` and `variableNames` start with a lower case letter but have
the first letter of all consecutive words capitalized
`method_names` are all lower case and different words are seperated by '_'

"""

<<<<<<< HEAD
from gui import GUI
import sys

VERBOSE = False
axotest = False
bintest = False
mattest = False

if __name__ == '__main__':
=======

from gui import GUI
# if __name__ == '__main__':
#     gui.cwd = os.getcwd()
#     try:
#         if 'axo' in sys.argv:
#             gui.axotest = True
#         elif 'bin' in sys.argv:
#             gui.bintest = True
#         if 'v' in sys.argv:
#             gui.VERBOSE = True
#     except IndexError:
#         pass
#     gui.MainWindow.run()
#     print(type(mainWindow))

if __name__ == '__main__':
    import sys, copy
    axotest = mattest = bintest = VERBOSE = False
>>>>>>> io
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
<<<<<<< HEAD

    GUI.run(VERBOSE,axotest,bintest,mattest)
## moving the hard coded parameters for testing from the gui is difficult
## because once the tkinter mainloop is running no more code will be executed;
## the interaction of GUI with anything else is purely event based
=======
    GUI.run(VERBOSE, axotest, bintest, mattest)
>>>>>>> io
