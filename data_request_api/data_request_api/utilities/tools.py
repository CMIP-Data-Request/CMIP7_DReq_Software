#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tools for data request.
"""
from __future__ import division, absolute_import, print_function, unicode_literals

import json
import os
import csv

from data_request_api.utilities.logger import get_logger


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
    logger = get_logger()
    logger.debug(f"Writing file {filename}.")
    dirname = os.path.dirname(filename)
    if len(dirname) > 0 and not os.path.isdir(dirname):
        logger.warning(f"Create directory {dirname}")
        os.makedirs(dirname)
    with open(filename, "w") as fic:
        defaults = dict(indent=4, allow_nan=True, sort_keys=True)
        defaults.update(kwargs)
        json.dump(content, fic, **defaults)


def write_csv_output_file_content(filename, content, **kwargs):
    with open(filename, 'w', newline='') as csvfile:
        csvfile_content = csv.writer(csvfile, **kwargs)
        for elt in content:
            csvfile_content.writerow(elt)
