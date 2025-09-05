#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Logger.
"""

from __future__ import unicode_literals, print_function, absolute_import, division

import logging
import os
import sys


log_dir = "."
log_filename = "log.out"
log_file = os.sep.join([log_dir, log_filename])
log_level = "info"

logger = logging.getLogger()


def change_log_file(logfile=log_file, default=False):
    global log_file, logger
    if default:
        logger = get_logger()
        for hdlr in logger.handlers[:]:
            hdlr.flush()
            hdlr.close()
            logger.removeHandler(hdlr)
        new_hdlr = logging.StreamHandler(sys.stdout)
    else:
        log_file = logfile
        log_dir = os.path.dirname(os.path.abspath(log_file))
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        logger = logging.getLogger()
        for hdlr in logger.handlers[:]:
            hdlr.flush()
            hdlr.close()
            logger.removeHandler(hdlr)
        new_hdlr = logging.FileHandler(log_file)
    new_hdlr.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    logger.addHandler(new_hdlr)
    return logger


def get_logger():
    return logger


def log_level_to_int(level):
    if isinstance(level, str):
        if level.lower() in ['debug', ]:
            return logging.DEBUG
        elif level.lower() in ['critical', ]:
            return logging.CRITICAL
        elif level.lower() in ['info', ]:
            return logging.INFO
        elif level.lower() in ['warning', ]:
            return logging.WARNING
        elif level.lower() in ['error', ]:
            return logging.ERROR
    else:
        return level


def log_msg(level, *args, **kwargs):
    logger.log(log_level_to_int(level), *args, **kwargs)


def change_log_level(level=log_level):
    global logger, log_level
    log_level = level
    logger.setLevel(log_level_to_int(level))
