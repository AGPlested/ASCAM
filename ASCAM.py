"""
ASCAM for processing and analysis of data from single ion channels.

Style:
`ClassNames` have the first letter of each word in them capitalized
`classInstances` and `variableNames` start with a lower case letter but have
the first letter of all consecutive words capitalized
`method_names` are all lower case and different words are seperated by '_'

"""


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
