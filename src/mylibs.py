# -*- coding: utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler
import os

#----------------------------------------------------------------------
logger = False

"""
Creates a rotating log
"""
def log():
    global logger

    if logger:
        return logger

    if not os.path.isdir("./logs"):
        os.mkdir('./logs', 0o770)

    # Logger object
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")

    # debug handler
    debug_handler = RotatingFileHandler(os.path.abspath('./logs/debug.log'), maxBytes=1024*1024*5, backupCount=7)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    debug_handler.addFilter(type('', (logging.Filter,), {'filter': staticmethod(lambda r: r.levelno <= logging.DEBUG)}))
    logger.addHandler(debug_handler)

    # info handler
    info_handler = RotatingFileHandler(os.path.abspath('./logs/info.log'), maxBytes=1024*1024*5, backupCount=7)
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_handler.addFilter(type('', (logging.Filter,), {'filter': staticmethod(lambda r: r.levelno == logging.INFO)}))
    logger.addHandler(info_handler)

    # error handler
    error_handler = RotatingFileHandler(os.path.abspath('./logs/error.log'), maxBytes=1024*1024*5, backupCount=7)
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger

#----------------------------------------------------------------------
