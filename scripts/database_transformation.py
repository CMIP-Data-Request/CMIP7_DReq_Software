#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database transformation testing script
"""
from __future__ import division, print_function, unicode_literals, absolute_import

import os
import sys

add_paths = ['../data_request_api/stable/content/dreq_api/', '../data_request_api/stable/query',
             '../data_request_api/stable/transform']
for path in add_paths:
    if path not in sys.path:
        sys.path.append(path)


import dreq_content as dc
from dump_transformation import transform_content
from data_request import DataRequest
from tools import write_json_output_file_content
from logger import change_log_file, change_log_level


# Set up log file (default to stdout) and log level
change_log_file(default=True)
change_log_level("debug")

### Step 1: Get the content of the DR
# Define content version to be used
# use_dreq_version = 'v1.0alpha'
# use_dreq_version = "first_export"
# use_dreq_version = 'new_export_15Oct2024'
use_dreq_version = "v1.0"
use_export_versions = ["raw", "release"]
output_directory = f'{dc._dreq_res}/{use_dreq_version}'
for use_export_version in use_export_versions:
    # Download specified version of data request content (if not locally cached)
    dc.retrieve(use_dreq_version, export=use_export_version)
    # Load content into python dict
    content = dc.load(use_dreq_version, export=use_export_version, consolidate=False)

    ### Step 2: Transform content into DR and VS
    data_request, vocabulary_server = transform_content(content, version=use_dreq_version)

    ### Step 3: Write down the two files
    DR_file = os.path.sep.join([output_directory, f"DR_{use_export_version}_content.json"])
    VS_file = os.path.sep.join([output_directory, f"VS_{use_export_version}_content.json"])
    write_json_output_file_content(DR_file, data_request)
    write_json_output_file_content(VS_file, vocabulary_server)

    DR = DataRequest.from_separated_inputs(DR_input=DR_file, VS_input=VS_file)


