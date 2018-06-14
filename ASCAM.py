"""
ASCAM for processing and analysis of data from single ion channels.
"""
from gui import GUI
import sys
import os
import logging
import datetime

def initialize_logger(output_dir):
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # create debug file handler and set level to debug
    handler = logging.FileHandler(os.path.join(output_dir,'ASCAM'+'_'+date+'.log'),"w")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(lineno)d:%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def main():
    VERBOSE = False #only here until VERBOSE has been replaced with logging everywhere
    # parameters for testing
    axotest = False
    bintest = False
    mattest = False

    #set up the logging module, for now logs are saved in current working
    #directory
    initialize_logger('.')
    logging.info("-"*20+"Start of new ASCAM session"+"-"*20)

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

if __name__ == '__main__': main()
