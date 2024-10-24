#!/usr/bin/env python
'''
Compare CMIP7 request for a given experiment to what was produced for CMIP6 by
a specified model, which is found by searching ESGF.

Workflow
--------
In current dir, if don't already have search_esgf, clone it:
    git clone git@gitlab.com:JamesAnstey/search_esgf.git
and then (in same dir):
    conda activite my_dreq_env
    ipython
    run -i compare_cmip6.py

'''
import sys
path = 'search_esgf/bin'
if path not in sys.path:
    sys.path.append(path)
import esgfsearch as es
import json

expt = 'historical'
expt_cmip7 = expt  # adjust if the experiment name isn't identical in both CMIP phases
model = 'CanESM5'

request_file = 'requested.json'
with open(request_file, 'r') as f:
    request = json.load(f)

request_by_expt = request['experiment']
request_by_expt = {k.strip() : v for k,v in request_by_expt.items()}

assert expt_cmip7 in request_by_expt
vars_by_priority = request_by_expt[expt_cmip7]

axes = {
    'column'       : ['source_id', 'experiment_id'],
    # 'row'    : ['table_id', 'variable_id'],
    'row'    : ['table_id'],
}
tables = []
tables.append('no. of datasets')
tables.append('total size of datasets')

# Available ESGF search parameters from CMIP6 DRS:
#   parameter           example value
#   ---------           -------------
#   'mip_era'           'CMIP6'
#   'activity_drs'      'ScenarioMIP'
#   'institution_id'    'CCCma'
#   'source_id'         'CanESM5'
#   'experiment_id'     'ssp245'
#   'member_id'         'r1i1p1f1'
#   'table_id'          'Amon'
#   'variable_id'       'tas'
#   'grid_label'        'gn'
#   'version'           'v20190429' (see comments below re. version)

filters = []
f = {   
    'experiment_id' : expt,
    'source_id' : model,
    }
filters.append(f)

# Search ESGF
try:
    # if running interactively (e.g. ipython) this prevents redoing the search
    # to force redoing it, delete the 'found' dict
    found
except:
    found, info_found = es.search(filters)
# Summarize the search results
summary_dir=None
es.summarize(found, info_found, axes, tables, summary_dir)

# Get compound names of all variables found
var_names = set()
for dataset in found:
    params = found[dataset]['params']
    var_name = '{table_id}.{variable_id}'.format(**params)
    var_names.add(var_name)

print(f'For {model} {expt}, found {len(var_names)} published variables')

# ISSUE: the request specifies short names but not outnames? ESGF datasets will use the outname.

indent = ' '*2
priority_levels = ['High', 'Medium', 'Low']
assert set(priority_levels) == set(vars_by_priority.keys())
for priority_level in priority_levels:
    requested_vars = set(vars_by_priority[priority_level])
    overlap = requested_vars.intersection(var_names)

    print(f'\n{priority_level} priority:')
    print(indent + 'requested in CMIP7 for {expt}: {n}'.format(expt=expt_cmip7, n=len(requested_vars)))
    print(indent + 'overlap with published {model} {expt}: {n}'.format(model=model, expt=expt, n=len(overlap)))


