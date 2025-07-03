#!/usr/bin/env python
'''
Example script for basic use of CMIP7 data request content.

See main repo README or docs for how to create an environment with the required dependencies.
To run the script at the shell prompt:
    python workflow_example.py
or in ipython:
    run -i workflow_example.py
A command-line equivalent of this script is available after pip installing the package.
For usage info:
    export_dreq_lists_json -h

'''
import os
import sys

# add repo top-level dir to system path so that data_request_api imports work from scripts/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_request_api.content import dreq_content as dc
from data_request_api.query import dreq_query as dq
from importlib import reload
reload(dq)

use_dreq_version = 'v1.2.1'

# Download specified version of data request content (if not locally cached)
#MPM_not_needed dc.retrieve(use_dreq_version)
# Load content into python dict
content = dc.load(use_dreq_version)

# Specify opportunities that modelling group chooses to support
# This can be a subset:
use_opps = []
#use_opps.append('Baseline Climate Variables for Earth System Modelling')
#use_opps.append('Synoptic systems')
use_opps.append('Energy System Impacts')
# Or, to support all opportunities in the data request:
use_opps = 'all'

# Get the requested variables for each opportunity and aggregate them into variable lists by experiment
# (i.e., for every experiment, a list of the variables that should be produced to support all of the
# specified opportunities)
priority_cutoff = 'Low'
expt_vars = dq.get_requested_variables(content, use_dreq_version,
                                       use_opps=use_opps, priority_cutoff=priority_cutoff,
                                       verbose=False)


if len(expt_vars['experiment']) > 0:

    # Show user what was found
    dq.show_requested_vars_summary(expt_vars, use_dreq_version)

    # Write json file with the variable lists
    content_path = dc._dreq_content_loaded['json_path']
    outfile = f'requested_{use_dreq_version}.json'
    dq.write_requested_vars_json(outfile, expt_vars, use_dreq_version, priority_cutoff, content_path)

else:
    print(f'\nFor data request version {use_dreq_version}, no requested variables were found')

# To remove locally cached version:
# dc.delete(use_dreq_version)
# To remove all locally cached versions:
# dc.delete()
