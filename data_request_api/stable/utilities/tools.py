#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tools for data request.
"""
from __future__ import division, absolute_import, print_function, unicode_literals

import json
import os

from data_request_api.stable.utilities.logger import get_logger


def read_json_file(filename):
    logger = get_logger()
    if os.path.isfile(filename):
        with open(filename, "r") as fic:
            content = json.load(fic)
    else:
        logger.error(f"Filename {filename} is not readable")
        raise OSError(f"Filename {filename} is not readable")
    return content


def read_json_input_file_content(filename):
    content = read_json_file(filename)
    return content


def write_json_output_file_content(filename, content, **kwargs):
    with open(filename, "w") as fic:
        defaults = dict(indent=4, allow_nan=True, sort_keys=True)
        defaults.update(kwargs)
        json.dump(content, fic, **defaults)
