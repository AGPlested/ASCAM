#!/usr/bin/env python
"""
ASCAM for processing and analysis of data from single ion channels.
"""
import os
import sys
import platform
import logging

import getopt

from PySide2.QtWidgets import QApplication
try :
    from .gui.mainwindow import MainWindow
except:
    from src.gui.mainwindow import MainWindow
try :
    from .utils import initialize_logger
except:
    from src.utils import initialize_logger

if platform.system() == 'Darwin':
    os.environ['QT_MAC_WANTS_LAYER'] = '1'

debug_logger = logging.getLogger("ascam.debug")


def parse_options():
    """
    Parse the command line options when launching ASCAM.

    Returns:
        debug (bool) - if true print contents of debug log to console
        silent (bool) - if true do not print contents of analysis log to console
        logdir (string) - the directory in which the log should be saved
        test (bool) - if true load example data
    """
    debug = False
    silent = False
    logdir = "./ASCAM_logfiles"
    test = False
    try:
        options, _ = getopt.getopt(
            sys.argv[1:], "dsl:th", ["loglevel=", "logdir=", "help", "test"]
        )
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        display_help()
        sys.exit(2)

    for opt, arg in options:
        if opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-s", "--silent"):
            silent = True
        elif opt in ("-l", "--logdir"):
            logdir = arg
        elif opt in ("-t", "test"):
            test = True
        elif opt in ("-h", "--help"):
            display_help()
            sys.exit(2)
        else:
            assert False, "unhandled option"

    return silent, logdir, test, debug


def display_help():
    """
    Print a manual for calling ASCAM to the commandline.
    """
    print(
        """Usage: ./run --debug --silent --test --logdir=./logfiles

            -d --debug : print debug messages to console
            -s --silent : do not print content of analysis log to console
            -l --logdir : directory in which the log file should be saved
            -t --test : load example data
            -h --help : display this message"""
    )


def get_version():
    here = os.path.abspath(os.path.dirname(__file__))
    stream = os.popen(f"pip freeze")
    pip_freeze = stream.read()

    stream = os.popen(f"cd {here}; git show")
    git_info = stream.read()
    git_info = "\n".join(git_info.split("\n")[:3])

    return pip_freeze, git_info


def main():
    silent, logdir, test, debug = parse_options()

    initialize_logger(logdir, silent, debug)
    logging.info("-" * 20 + "Start of new ASCAM session" + "-" * 20)

    pip_freeze, git_info = get_version()

    logging.info(git_info)
    logging.info(pip_freeze)

    app = QApplication([])
    screen_resolution = (1920, 1080)  # assume HD display
    for screen in app.screens():
        if screen.geometry().topLeft() != (0, 0):
            screen_resolution = screen.size().toTuple()
    main_window = MainWindow(screen_resolution=screen_resolution)
    main_window.show()
    if test:
        main_window.load_example_data()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Change menubar name from 'python' to 'SAFT' on macOS
    # from https://stackoverflow.com/questions/5047734/
    if sys.platform.startswith('darwin'):
    # Python 3: pyobjc-framework-Cocoa is needed
        try:
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                app_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
                app_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if app_info:
                    app_info['CFBundleName'] = app_name.upper() # ensure text is in upper case.
        except ImportError:
            print ("Failed to import NSBundle, couldn't change menubar name." )

    main()
