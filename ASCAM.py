#!/usr/bin/env python3
"""
ASCAM for processing and analysis of data from single ion channels.
"""
from gui import GUI
import sys
import os
import logging
import datetime
import getopt

def initialize_logger(output_dir,log_level='INFO',silent=False):
    """
    Set up the logging module to write INFO level output to the console and
    write everything to a file with timestamps and module name
    """
    date = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if not silent:
        # create console handler and set level to info
        handler = logging.StreamHandler()
        if log_level=='INFO':
            handler.setLevel(logging.INFO)
        elif log_level=='DEBUG':
            handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # create debug file handler and set level to debug
    if not os.path.exists(output_dir): os.makedirs(directory)
    handler = logging.FileHandler(os.path.join(output_dir,'ASCAM'+'_'+date+'.log'),"w")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(lineno)d:%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def parse_options():
    """
    Parse the command line options when launching ASCAM.
    Returns:
        log_level (string) - which level of logging should be printed to console
        test (string/bool) - if not False this is the type of file that should be loaded for testing
        silent (bool) - if true no logs will be printed to the console
        logdir (string) - the directory in which the log should be saved
    """
    log_level = 'INFO'
    test = False
    silent = True
    logdir = './logfiles'
    try:
        options, args = getopt.getopt(sys.argv[1:], "l:t:d:h", ["loglevel=", "test=", "logdir=","help"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    for opt, arg in options:
        if opt in ("-l", "--loglevel"):
            log_level = arg
            silent = False
        elif opt in ("-t", "--test"):
            test = arg
        elif opt in ("-d", "--logdir"):
            logdir = arg
        elif opt in ("-h", "--help"):
            usage()
            sys.exit(2)
        else: assert False, "unhandled option"
    return log_level, test, silent, logdir

def usage():
    """
    Print a manual for calling ASCAM to the commandline.
    """
    print("""Usage: ./ASCAM --loglevel=INFO --test=False --silent --logdir=.
            -l --loglevel : level of logging to be printed to console (INFO or DEBUG)
                            if no level is given nothing will be printed to console
            -t --test : type of file to be used for testing (mat, axo or bin)
            -d --logdir : directory in which the log file should be saved
            -h --help : display this message""")

def main():
    # parameters for testing
    axotest = False
    bintest = False
    mattest = False

    log_level, test, silent, logdir = parse_options()

    if test=='mat': mattest=True
    elif test=='bin': bintest=True
    elif test=='axo': axotest=True
    #set up the logging module, for now logs are saved in current working
    #directory
    initialize_logger(logdir,log_level,silent)
    logging.info("-"*20+"Start of new ASCAM session"+"-"*20)

    GUI.run(axotest, bintest, mattest)

if __name__ == '__main__': main()
