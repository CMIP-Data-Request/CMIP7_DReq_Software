#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database transformation testing script
"""
from __future__ import division, print_function, unicode_literals, absolute_import

import os
import sys

add_paths = ['../sandbox/MS/dreq_api/', '../sandbox/JA', '../sandbox/GR']
for path in add_paths:
    if path not in sys.path:
        sys.path.append(path)


import dreq_content as dc
from dump_transformation import transform_content, write_json_output_file_content
from logger import change_log_file, change_log_level


# Set up log file (default to stdout) and log level
change_log_file(default=True)
change_log_level("debug")

### Step 1: Get the content of the DR
# Define content version to be used
# use_dreq_version = 'v1.0alpha'
# use_dreq_version = "first_export"
use_dreq_version = 'new_export_15Oct2024'
# Download specified version of data request content (if not locally cached)
dc.retrieve(use_dreq_version)
# Load content into python dict
content = dc.load(use_dreq_version)

### Step 2: Transform content into DR and VS
data_request, vocabulary_server = transform_content(content, version=use_dreq_version)

### Step 3: Write down the two files
output_directory = f'../sandbox/MS/dreq_api/dreq_res/{use_dreq_version}'
write_json_output_file_content(os.path.sep.join([output_directory, "DR_content.json"]), data_request)
write_json_output_file_content(os.path.sep.join([output_directory, "VS_content.json"]), vocabulary_server)
