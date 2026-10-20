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

use_dreq_version = 'v1.2.2.5'

# Download specified version of data request content (if not locally cached)
#MPM_not_needed dc.retrieve(use_dreq_version)
# Load content into python dict
content = dc.load(use_dreq_version)



# Load unharmonised DR content
# TODO: load from (validated) yaml files directly
# TODO: should expt,var groups be in opp json files or separate files? probably separate
import json
filenames = []
filenames.append('newopp.json')
content_udr = {
    'Opportunity': {},
    'Experiment Group': {},
    'Variable Group': {}
}
opp_count = 0
for filename in filenames:
    with open(filename) as f:
        opp_info = json.load(f)

    # Create an Opportunity id label
    fmt='%.3i'
    opp_count += 1
    opp_id = f'udr.{fmt % opp_count}'

    # Add to dict containing UDR Opportunities
    content_udr['Opportunity'][opp_id] = opp_info['Opportunity']

    # Add to dict containing UDR experiment groups
    for name, info in opp_info['Experiment Group'].items():
        # assert name not in content_udr['Experiment Group']
        content_udr['Experiment Group'][name] = info

    # Add to dict containing UDR variable groups
    for name, info in opp_info['Variable Group'].items():
        # assert name not in content_udr['Variable Group']
        content_udr['Variable Group'][name] = info



# Specify opportunities that modelling group chooses to support
# This can be a subset:
use_opps = []
use_opps.append('Baseline Climate Variables for Earth System Modelling')
#use_opps.append('Synoptic systems')
# use_opps.append('Energy System Impacts')
# Or, to support all opportunities in the data request:
# use_opps = 'all'

# Get the requested variables for each opportunity and aggregate them into variable lists by experiment
# (i.e., for every experiment, a list of the variables that should be produced to support all of the
# specified opportunities)
priority_cutoff = 'Low'
expt_vars = dq.get_requested_variables(content, use_dreq_version,
                                       use_opps=use_opps, priority_cutoff=priority_cutoff,
                                       verbose=False,
                                       content_udr=content_udr,
                                       )


# keep_expts = ['amip', 'historical']
# expt_vars['experiment'] = {expt: expt_vars['experiment'][expt] for expt in keep_expts}


if len(expt_vars['experiment']) > 0:

    # Show user what was found
    dq.show_requested_vars_summary(expt_vars, use_dreq_version)

    # Write json file with the variable lists
    content_path = dc._dreq_content_loaded['json_path']
    outfile = f'requested.json'
    dq.write_requested_vars_json(outfile, expt_vars, use_dreq_version, priority_cutoff, content_path)

else:
    print(f'\nFor data request version {use_dreq_version}, no requested variables were found')

# To remove locally cached version:
# dc.delete(use_dreq_version)
# To remove all locally cached versions:
# dc.delete()
