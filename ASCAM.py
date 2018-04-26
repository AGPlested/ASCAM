"""
ASCAM for processing and analysis of data from single ion channels.
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
    GUI.run(VERBOSE, axotest, bintest, mattest)
