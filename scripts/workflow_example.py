#!/usr/bin/env python
'''
Example script for basic use of CMIP7 data request content

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

Note that a command-line equivalent of this script is also available in the scripts/ folder.
For usage info, do:

    ./export_dreq_lists_json.py -h    

Usage examples:

    ./export_dreq_lists_json.py v1.0 dreq_list.json --all_opportunities
    ./export_dreq_lists_json.py v1.0 dreq_list.json --opportunities_file opps.json

'''
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from data_request_api.stable.content.dreq_api import dreq_content as dc
from data_request_api.stable.query import dreq_query as dq
from importlib import reload
reload(dq)


use_dreq_version = 'v1.0'

# Download specified version of data request content (if not locally cached)
dc.retrieve(use_dreq_version)
# Load content into python dict
content = dc.load(use_dreq_version)

# Specify opportunities that modelling group chooses to support
# This can be a subset:
use_opps = []
use_opps.append('Baseline Climate Variables for Earth System Modelling')
use_opps.append('Synoptic systems')
# Or, to support all opportunities in the data request:
use_opps = 'all'

# Get consolidated list of requested variables that supports these opportunities
dq.DREQ_VERSION = use_dreq_version
priority_cutoff = 'Low'
expt_vars = dq.get_requested_variables(content, use_opps, priority_cutoff=priority_cutoff, verbose=False)


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
