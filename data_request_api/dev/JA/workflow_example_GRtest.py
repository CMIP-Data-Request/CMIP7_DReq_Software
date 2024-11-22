#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

"""
from __future__ import division, print_function, unicode_literals, absolute_import

import sys
import pprint
from collections import defaultdict

import six

import json

# add_paths = ['../sandbox/MS/dreq_api/', '../sandbox/JA', '../sandbox/GR']
add_paths = ['../MS/dreq_api/', '../GR']
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
use_dreq_version = 'v1.0beta'
# use_dreq_version = "first_export"
# use_dreq_version = 'new_export_15Oct2024'
# Download specified version of data request content (if not locally cached)
# dc.retrieve(use_dreq_version)
# Load content into python dict
# content = dc.load(use_dreq_version)

### Step 2: Load it into the software of the DR
# DR = DataRequest.from_input(json_input=content, version=use_dreq_version)
# path = f'../sandbox/MS/dreq_api/dreq_res/{use_dreq_version}'
path = f'../MS/dreq_api/dreq_res/{use_dreq_version}'
DR = DataRequest.from_separated_inputs(DR_input=f"{path}/DR_content.json",
                                       VS_input=f"{path}/VS_content.json")


GR_demo = False
if GR_demo:
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

    rep = defaultdict(lambda: defaultdict(set))
    for elt in DR.get_variables_groups():
        for var in elt.get_variables():
            param = var.physical_parameter["name"]
            freq = var.frequency["name"]
            realm = set([elt if isinstance(elt, six.string_types) else elt.get("name", "???") for elt in var.modelling_realm])
            spt_shp = set([elt if isinstance(elt, six.string_types) else elt.get("name", "???") for elt in var.spatial_shape])
            tmp_shp = set([elt if isinstance(elt, six.string_types) else elt.get("name", "???") for elt in var.temporal_shape])
            for (rlm, freq, sshp, tshp) in zip(realm, [freq, ], spt_shp, tmp_shp):
                rep[rlm][param].add(f"{freq} // {sshp} // {tshp}")
    pprint.pprint(rep)
    # pprint.pprint(rep_data)




# from copy import deepcopy
# DR0 = deepcopy(DR)

print(type(DR))

opp = DR.get_opportunities()[0]


# simpler way to do this?
def get_name(x):
    return x.vs.get_element(x.DR_type, x.id, 'name')

title = 'Ocean Extremes'
opp = [opp for opp in DR.get_opportunities() if get_name(opp) == 'Ocean Extremes'][0]

# print()
# print(opp)

# print()
# for theme in opp.get_themes():
#     print(theme)

# print()
# for expt_group in opp.get_experiments_groups():
#     print(expt_group)

# print()
# for var_group in opp.get_variables_groups():
#     print(var_group)

# print()


# print(len(opp_vars), len(opp_expts))

# var = opp_vars[0]

# copied this out of VS_content.json, surely there's a way to get this lookup info from DR object?
lookup = {
    "priority_level": {
        # note, this info is keyed on the uid, which is found in the export
        # e.g. in dreq_release_export.json for v1.0beta:
        # "Name": "High",
        # "Notes": "High priority should be used sparingly",
        # "UID": "527f5c94-8c97-11ef-944e-41a8eb05f654",
        # "Value": 2,
        "527f5c94-8c97-11ef-944e-41a8eb05f654": {
            "name": "High",
            "notes": "High priority should be used sparingly",
            "value": 2
        },
        "527f5c95-8c97-11ef-944e-41a8eb05f654": {
            "name": "Medium",
            "value": 3
        },
        "527f5c96-8c97-11ef-944e-41a8eb05f654": {
            "name": "Low",
            "value": 4
        },
        "527f5c97-8c97-11ef-944e-41a8eb05f654": {
            "name": "Core",
            "notes": "Top priority -- adopted by panels",
            "value": 1
        }
    }
}
priority_levels = [info['name'] for info in lookup['priority_level'].values()]

def get_unique_var_name(var):
    return var.compound_name


use_opps = []
use_opps.append('Baseline Climate Variables for Earth System Modelling')
use_opps.append('Synoptic systems and impacts')
# use_opps.append('Climate impact assessments on freshwater ecosystems')
# use_opps.append('Ocean Extremes')

use_opps = 'all'

# lookup table of opportunities by their title
opps = {}
for opp in DR.get_opportunities():
    title = get_name(opp)
    assert title not in opps, f'opp title not unique: {title}'
    opps[title] = opp

request = {} # dict to hold aggregated request

check = not True

if use_opps == 'all':
    use_opps = list(opps.keys())

use_opps = sorted(use_opps)
for title in use_opps:

    opp = opps[title]

    if check:
        opp_expts = set()
        for expt_group in opp.experiments_groups:
            opp_expts.update([expt.name for expt in expt_group.get_experiments()])
        opp_expts0 = opp_expts

    # -> Get all experiments' id associated with an opportunity
    opp_expts = DR.find_experiments_per_opportunity(opp)
    opp_expts = set([expt.name for expt in opp_expts])

    if check:
        assert opp_expts == opp_expts0
        del opp_expts0

    if check:
        # -> Get all variables' id associated with an opportunity
        opp_vars = DR.find_variables_per_opportunity(opp)
        opp_vars0 = set([get_unique_var_name(var) for var in opp_vars])

    # Loop over variable groups to get opportunity's variables separated by priority level
    opp_vars = {p : set() for p in priority_levels}
    for vg in opp.variables_groups:

        assert isinstance(vg.priority, list) and len(vg.priority) == 1
        priority_info = lookup['priority_level'][vg.priority[0]]
        priority_level = priority_info['name']  # e.g. "Core", "High", ...

        for var in vg.variables:
            var_name = get_unique_var_name(var)
            # Add this variable to the list of requested variables at the specified priority
            opp_vars[priority_level].add(var_name)

    if check:
        opp_vars1 = set()
        for priority_level in opp_vars:
            opp_vars1.update(opp_vars[priority_level])
        assert opp_vars1 == opp_vars0  # confirm that DR.find_variables_per_opportunity(opp) lumps all priority levels together
        del opp_vars0, opp_vars1

    # Aggregate this Opportunity's request into the master list of requests
    for expt_name in opp_expts:
        if expt_name not in request:
            # If we haven't encountered this experiment yet, initialize an expt_request object for it
            request[expt_name] = {p : set() for p in priority_levels}

        # Add this Opportunity's variables request to the expt_request object
        for priority_level, var_names in opp_vars.items():
            request[expt_name][priority_level].update(opp_vars[priority_level])


# Remove any overlaps in variable lists between different priority levels
priority_hierarchy = ['Core', 'High', 'Medium', 'Low']  # ordered from highest to lowest priority
assert set(priority_hierarchy) == set(priority_levels)
assert len(set(priority_hierarchy)) == len(priority_hierarchy)
for expt_request in request.values():
    for k,p in enumerate(priority_hierarchy):
        for p_higher in priority_hierarchy[:k]:
            expt_request[p] = expt_request[p].difference(expt_request[p_higher])
            # print(p,p_higher)
            # print()

    # convert sets to lists for json output
    for p in expt_request:
        expt_request[p] = sorted(expt_request[p], key=str.lower)

expt_vars = {
    'Header' : {
        'Opportunities' : use_opps,
        'dreq version' : use_dreq_version,
    },
    'experiment' : request,
}


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

    # Write the results to json
    filename = 'requested2.json'
    with open(filename, 'w') as f:
        json.dump(expt_vars, f, indent=4, sort_keys=True)
        print('\nWrote requested variables to ' + filename)

else:
    print(f'\nFor data request version {use_dreq_version}, no requested variables were found')




