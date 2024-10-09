#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Other example script for basic use of CMIP7 data request content

Getting started
---------------
First create an environment with the required dependencies:

    conda env create -n my_dreq_env --file env.yml

(replacing my_dreq_env with your preferred env name). Then activate it and run the script:

    conda activate my_dreq_env
    python workflow_example.py

will load the data request content and save a json file of requested variables in the current dir.
To run interactively in ipython:

    run -i workflow_example.py
"""
from __future__ import division, print_function, unicode_literals, absolute_import

import sys
import pprint
from collections import defaultdict

add_paths = ['../sandbox/MS/dreq_api/', '../sandbox/JA', '../sandbox/GR']
for path in add_paths:
    if path not in sys.path:
        sys.path.append(path)


import dreq_content as dc
from data_request import DataRequest
from logger import change_log_file, change_log_level


# Set up log file (default to stdout) and log level
change_log_file(default=True)
change_log_level("info")

### Step 1: Get the content of the DR
# Define content version to be used
# use_dreq_version = 'v1.0alpha'
use_dreq_version = "first_export"
# Download specified version of data request content (if not locally cached)
dc.retrieve(use_dreq_version)
# Load content into python dict
content = dc.load(use_dreq_version)

### Step 2: Load it into the software of the DR
DR = DataRequest.from_input(json_input=content)

### Step 3: Get information from the DR
# -> Print DR content
print(DR)
# -> Print an experiment group content
print(DR.experiments_groups["recz5nwuvKpkr1fss"])
# -> Get all variables' id associated with an opportunity
print(DR.find_variables_per_opportunity("recD45ipnmfCTBH7B"))
# -> Get all experiments' id associated with an opportunity
print(DR.find_experiments_per_opportunity("recD45ipnmfCTBH7B"))
# -> Get information about the shapes of the variables of all variables groups
rep = dict()
rep_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
for elt in DR.get_variables_groups():
    rep[elt.id] = dict(cell_methods=set(), frequency=set(), temporal_shape=set(), variables=set())
    for var in elt.get_variables():
        rep[elt.id]["cell_methods"].add(var.cell_methods)
        rep[elt.id]["frequency"].add(var.frequency)
        rep[elt.id]["temporal_shape"].add(var.temporal_shape)
        rep[elt.id]["variables"].add(var.MIP_variable)
        rep_data[elt.id][var.frequency][var.temporal_shape].append(var.MIP_variable)

pprint.pprint(rep)
pprint.pprint(rep_data)