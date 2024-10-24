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

### Step 2: Load it into the software of the DR
# DR = DataRequest.from_input(json_input=content, version=use_dreq_version)
DR = DataRequest.from_separated_inputs(DR_input=f"../sandbox/MS/dreq_api/dreq_res/{use_dreq_version}/DR_content.json",
                                       VS_input=f"../sandbox/MS/dreq_api/dreq_res/{use_dreq_version}/VS_content.json")

### Step 3: Get information from the DR
# -> Print DR content
print(DR)
# -> Print an experiment group content
print(DR.get_experiments_groups()[0])
# -> Get all variables' id associated with an opportunity
print(DR.find_variables_per_opportunity(DR.get_opportunities()[0]))
# -> Get all experiments' id associated with an opportunity
print(DR.find_experiments_per_opportunity(DR.get_opportunities()[0]))
# -> Get information about the shapes of the variables of all variables groups
rep = dict()
for elt in DR.get_variables_groups():
    rep[elt.id] = dict(spatial_shape=set(), frequency=set(), temporal_shape=set(), physical_parameter=set())
    for var in elt.get_variables():
        for key in ["spatial_shape", "frequency", "temporal_shape", "physical_parameter"]:
            rep[elt.id][key] = rep[elt.id][key].union(set([elt.get("name", "???") if isinstance(elt, dict) else elt
                                                           for elt in var.__getattribute__(key)]))

pprint.pprint(rep)
# pprint.pprint(rep_data)