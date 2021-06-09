# -*- coding: utf-8 -*-

"""
Project functions
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from config.config import Config

logger = False


def log():
    """
    Get logger. simply use with `log().info("my log")`
    If main.py is ran with `-v`, the logger also write to sys.stdout
    """
    global logger

    if logger:
        return logger

    root_path = Config.read()['root_path']
    log_path = root_path + '/logs'

    if not os.path.isdir(log_path):
        os.mkdir(log_path, 0o770)

    # Logger object
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")

    # If `-v` also log to stdout
    if Config.read()['args'].verbose:
        logger.addHandler(logging.StreamHandler(sys.stdout))

    # debug handler
    debug_handler = RotatingFileHandler(log_path + '/debug.log', maxBytes=1024 * 1024 * 5, backupCount=7)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    debug_handler.addFilter(type('', (logging.Filter,), {'filter': staticmethod(lambda r: r.levelno <= logging.DEBUG)}))
    logger.addHandler(debug_handler)

    # info handler
    info_handler = RotatingFileHandler(log_path + '/info.log', maxBytes=1024 * 1024 * 5, backupCount=7)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_handler.addFilter(type('', (logging.Filter,), {'filter': staticmethod(lambda r: r.levelno == logging.INFO)}))
    logger.addHandler(info_handler)

    # error handler
    error_handler = RotatingFileHandler(log_path + '/error.log', maxBytes=1024 * 1024 * 5, backupCount=7)
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger
