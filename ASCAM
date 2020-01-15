#!/usr/bin/env python3
"""
ASCAM for processing and analysis of data from single ion channels.
"""
import sys
import os
import logging

# import datetime
import getopt

from gui import GUI
from logging_setup import initialize_logger


def parse_options():
    """
    Parse the command line options when launching ASCAM.

    Returns:
        log_level (string) - which level of logging should be printed to console
        silent (bool) - if true no logs will be printed to the console
        logdir (string) - the directory in which the log should be saved
    """
    log_level = "INFO"
    silent = True
    logdir = "./logfiles"
    test = False
    try:
        options, args = getopt.getopt(
            sys.argv[1:], "l:d:th", ["loglevel=", "logdir=", "help", "test"]
        )
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in options:
        if opt in ("-l", "--loglevel"):
            log_level = arg
            silent = False
        elif opt in ("-d", "--logdir"):
            logdir = arg
        elif opt in ("-t", "test"):
            test = True
        elif opt in ("-h", "--help"):
            display_help()
            sys.exit(2)
        else:
            assert False, "unhandled option"
    return log_level, silent, logdir, test


def display_help():
    """
    Print a manual for calling ASCAM to the commandline.
    """
    print(
        """Usage: ./ASCAM --loglevel=INFO --silent --logdir=./logfiles

            -l --loglevel : level of logging to be printed to console (INFO or
                            DEBUG)
                            if no level is given nothing will be printed to
                            console
            -d --logdir : directory in which the log file should be saved
            -t --test : load example data
            -h --help : display this message"""
    )


def main():
    log_level, silent, logdir, test = parse_options()

    # set up the logging module, for now logs are saved in current working
    # directory
    initialize_logger(logdir, log_level, silent)
    logging.info("-" * 20 + "Start of new ASCAM session" + "-" * 20)

    GUI.run(test)


if __name__ == "__main__":
    main()
