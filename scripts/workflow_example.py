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

'''
import sys
import json
import os
import hashlib
from collections import OrderedDict
add_paths = ['../sandbox/MS/dreq_api/', '../sandbox/JA', '../sandbox/GR']
for path in add_paths:
    if path not in sys.path:
        sys.path.append(path)
import dreq_content as dc
import dreq_query as dq
# from importlib import reload
# reload(dq)


use_dreq_version = 'v1.0beta'

# Download specified version of data request content (if not locally cached)
dc.retrieve(use_dreq_version)
# Load content into python dict
content = dc.load(use_dreq_version)

# Specify opportunities that modelling group chooses to support
# This can be a subset:
use_opps = []
use_opps.append('Baseline Climate Variables for Earth System Modelling')
use_opps.append('Synoptic systems and impacts')
# Or to use all opportunities in the data request:
use_opps = 'all'

# Get consolidated list of requested variables that supports these opportunities
dq.DREQ_VERSION = use_dreq_version
priority_cutoff = 'Low'
expt_vars = dq.get_requested_variables(content, use_opps, priority_cutoff=priority_cutoff, verbose=False)


if len(expt_vars['experiment']) > 0:

    # Show user what was found
    print(f'\nFor data request version {use_dreq_version}, number of requested variables found by experiment:')
    priority_levels = ['Core', 'High', 'Medium', 'Low']
    for expt, req in sorted(expt_vars['experiment'].items()):
        d = {p : 0 for p in priority_levels}
        for p in priority_levels:
            if p in req:
                d[p] = len(req[p])
        n_total = sum(d.values())
        print(f'  {expt} : ' + ' ,'.join(['{p}={n}'.format(p=p,n=d[p]) for p in priority_levels]) + f', TOTAL={n_total}')

    # Write results to json file
    Header = OrderedDict({
        'Opportunities' : sorted(expt_vars['Header']['Opportunities'], key=str.lower)
    })

    m = priority_levels.index(priority_cutoff)+1
    Header.update({
        'Priority levels' : priority_levels[:m]
    })
    for req in expt_vars['experiment'].values():
        for p in priority_levels[m:]:
            assert req[p] == []
            req.pop(p)

    # Get provenance of content to include in the Header
    content_path = dc._dreq_content_loaded['json_path']
    with open(content_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()
    Header.update({
        'dreq version' : use_dreq_version,
        'dreq content file' : os.path.basename(os.path.normpath(content_path)),
        'dreq content sha256 hash' : content_hash,
    })

    out = {
        'Header' : Header,
        'experiment' : OrderedDict(),
    }
    expt_names = sorted(expt_vars['experiment'].keys(), key=str.lower)
    for expt_name in expt_names:
        out['experiment'][expt_name] = OrderedDict()
        req = expt_vars['experiment'][expt_name]
        for p in priority_levels:
            if p in req:
                out['experiment'][expt_name][p] = req[p]

    # Write the results to json
    filename = f'requested_{use_dreq_version}.json'
    with open(filename, 'w') as f:
        # json.dump(expt_vars, f, indent=4, sort_keys=True)
        json.dump(out, f, indent=4)
        print('\nWrote requested variables to ' + filename)

else:
    print(f'\nFor data request version {use_dreq_version}, no requested variables were found')

# To remove locally cached version:
# dc.delete(use_dreq_version)
# To remove all locally cached versions:
# dc.delete()
