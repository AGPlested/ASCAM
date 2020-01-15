import logging
import os
import datetime
import types

from ascam.constants import ANALYSIS_LEVELV_NUM


def initialize_logger(output_dir, log_level="INFO", silent=False):
    """Start the root logger and the handlers.

    Args:
        output_dir - the directory in which the logs should be stored
        log_level - 'ANALYSIS', 'DEBUG' or 'ALL', determines what is logged
        silent - if false the logs are printed the console
    """

    logger = logging.getLogger()
    logger.setLevel(ANALYSIS_LEVELV_NUM)

    if not silent:
        setup_cl_handlers(logger, log_level)

    # create debug file handler and set level to debug
    setup_file_handlers(logger, log_level, output_dir)


def setup_file_handlers(logger, log_level, output_dir):
    """Set up handlers for writing logs to files."""

    date = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M")
    formatter = logging.Formatter(
        "%(asctime)s:%(levelname)s:%(module)s:" "%(lineno)d:%(message)s"
    )

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ana_file_name = os.path.join(output_dir, f"ASCAM_{date}.log")
    ana_file_handler = logging.FileHandler(ana_file_name, "w")
    ana_file_handler.setLevel(ANALYSIS_LEVELV_NUM)
    ana_file_handler.addFilter(AnalysisFilter())
    ana_file_handler.setFormatter(formatter)
    logger.addHandler(ana_file_handler)

    if log_level == "DEBUG":
        debug_logfile_name = os.path.join(output_dir, f"DEBUG_ASCAM_{date}.log")
        debug_file_handler = logging.FileHandler(debug_logfile_name, "w")
        debug_file_handler.setLevel(logging.DEBUG)
        debug_file_handler.setFormatter(formatter)
        logger.addHandler(debug_file_handler)


def setup_cl_handlers(logger, log_level):
    """Set up handler for command line logging."""

    formatter = logging.Formatter(
        "%(levelname)s:%(module)s:" "%(lineno)d - %(message)s"
    )
    # create command line handler for analysis logging
    ana_cl_handler = logging.StreamHandler()
    ana_cl_handler.addFilter(AnalysisFilter())
    ana_cl_handler.setLevel(ANALYSIS_LEVELV_NUM)
    ana_cl_handler.setFormatter(formatter)

    debug_cl_handler = logging.StreamHandler()
    debug_cl_handler.setLevel(logging.DEBUG)
    debug_cl_handler.setFormatter(formatter)

    if log_level == "ANALYSIS":
        logger.addHandler(ana_cl_handler)
    elif log_level == "DEBUG":
        logger.addHandler(debug_cl_handler)
    elif log_level == "ALL":
        logger.addHandler(ana_cl_handler)
        logger.addHandler(debug_cl_handler)


class AnalysisFilter(logging.Filter):
    def filter(self, record):
        """Filter logging to only accept loglevel INFO"""

        return record.levelno == ANALYSIS_LEVELV_NUM
