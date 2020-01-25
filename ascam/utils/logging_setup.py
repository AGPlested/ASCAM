import logging
import os
import datetime


def initialize_logger(output_dir=".", verbose=False, debug=False):
    """Start the root logger and the handlers.

    Args:
        output_dir - the directory in which the logs should be stored
        verbose (bool) - if true print analysis log contents to console
        debug (bool) - if true print debug log contents to console
    """

    analysis_logger = logging.getLogger("ascam.analysis")
    debug_logger = logging.getLogger("ascam.debug")

    # do not show these logs in root logger (avoids double printing)
    analysis_logger.propagate = False
    debug_logger.propagate = False

    analysis_logger.setLevel(logging.DEBUG)
    debug_logger.setLevel(logging.DEBUG)

    if verbose:
        setup_cl_handlers(analysis_logger)
    if debug:
        setup_cl_handlers(debug_logger)

    date = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    setup_file_handler(debug_logger, output_dir, f"debug_ASCAM_{date}.log")
    setup_file_handler(debug_logger, output_dir, f"analysis_ASCAM_{date}.log")


def setup_file_handler(logger, output_dir, filename):
    formatter = logging.Formatter(
        "%(asctime)s:%(levelname)s:%(module)s:" "%(lineno)d:%(message)s"
    )
    logfile_name = os.path.join(output_dir, filename)
    file_handler = logging.FileHandler(logfile_name, "w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def setup_cl_handlers(logger):
    """Set up handler for command line logging."""

    formatter = logging.Formatter(
        "%(levelname)s:%(module)s:" "%(lineno)d - %(message)s"
    )
    cl_handler = logging.StreamHandler()
    cl_handler.setFormatter(formatter)
    logger.addHandler(cl_handler)

