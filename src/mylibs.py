# -*- coding: utf-8 -*-

import logging
import os
from logging.handlers import RotatingFileHandler

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

    path = os.path.abspath('./logs/info.log')

    # FORMAT = '%(asctime)s %(message)s'
    # logging.basicConfig(format=FORMAT)

    # rotating handler
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
    handler = RotatingFileHandler(path, maxBytes=1024*1024*5, backupCount=5)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger
#----------------------------------------------------------------------
