#!/usr/bin/env python
'''
Find out the pressure levels (plev) of requested variables.
Output json files summarizing the info.

This script started life dealing just with plevs, but has evolved to gather other variable info.
Some of the bits might be useful elsewhere.
'''

import os
import json


import data_request_api.stable.content.dreq_api.dreq_content as dc
import data_request_api.stable.query.dreq_query as dq
from data_request_api.stable.query import dreq_classes

from collections import OrderedDict, defaultdict
from copy import deepcopy

from importlib import reload
reload(dq)
reload(dc)

###############################################################################
# Load data request content

# use_dreq_version = 'first_export'
# use_dreq_version = 'v1.0alpha'
use_dreq_version = 'v1.0beta'

# # Download specified version of data request content (if not locally cached)
# dc.retrieve(use_dreq_version, export='raw')
# # Load content into python dict
# content = dc.load(use_dreq_version, consolidate=False, export='raw')

use_consolidated = True
use_export = 'release'
use_export = 'raw'

load_manually = not True

if load_manually:
    # just for testing
    path = '/home/rja001/code/dreq/CMIP7_DReq_Content/airtable_export'
    filepath = os.path.join(path, 'dreq_working.json')
    with open(filepath, 'r') as f:
        content = json.load(f)
        print('loaded ' + filepath)

    use_consolidated = False


else:
    # this is the usual thing

    # Download specified version of data request content (if not locally cached)
    dc.retrieve(use_dreq_version, export=use_export)
    # Load content into python dict
    content = dc.load(use_dreq_version, export=use_export, consolidate=use_consolidated)



print(content.keys())

###############################################################################
# Find variables requested for a set of opportunities.

dq.DREQ_VERSION = use_dreq_version
# Initialize table objects to represent the various tables in the data request
# base = dq.create_dreq_tables_for_request(content)
base = dq.create_dreq_tables_for_request(deepcopy(content), consolidated=use_consolidated)

# use subset of opportunities:
# use_opps = []
# use_opps.append('Baseline Climate Variables for Earth System Modelling')
# use_opps.append('Synoptic systems and impacts')

# use all opportunities:
Opps = base['Opportunity']
use_opps = [opp.title for opp in Opps.records.values()]

# dict to store all of opportunity's vars, grouped by priority:
opp_vars_by_priority = {opp_title : OrderedDict() for opp_title in use_opps}
# dict to store all of opportunity's vars, grouped by variable group:
opp_vars_by_group = {opp_title : OrderedDict() for opp_title in use_opps}

VarGroups = base['Variable Group']
Vars = base['Variables']

if 'Priority Level' in base:
    PriorityLevel = base['Priority Level']
    priority_levels = [rec.name for rec in PriorityLevel.records.values()]
else:
    # retain this option for non-consolidated raw export?
    priority_levels = ['Core', 'High', 'Medium', 'Low']

# Loop over opportunities to get requested variables for each one.
# Requested experiments are ignored because here we only want the variables.
opp_ids = dq.get_opp_ids(use_opps, Opps)
verbose = False
for opp_id in opp_ids:
    opp = Opps.records[opp_id] # one record from the Opportunity table
    print(f'Opportunity: {opp.title}')

    for link in opp.variable_groups:
        # var_group = VarGroups.records[link.record_id]
        var_group = VarGroups.get_record(link)

        if not hasattr(var_group, 'variables'):
            continue

        if isinstance(var_group.priority_level, str):
            # retain this option for non-consolidated raw export?
            priority_level = var_group.priority_level
        else:
            priority = PriorityLevel.get_record(var_group.priority_level[0])
            priority_level = priority.name

        assert var_group.name not in opp_vars_by_group[opp.title], 'variable group name is not unique in this opportunity!'
        # opp_vars_by_group[opp.title][var_group.name] = set()
        opp_vars_by_group[opp.title][var_group.name] = []
        
        if priority_level not in opp_vars_by_priority[opp.title]:
            # opp_vars_by_priority[opp.title][priority_level] = set()
            opp_vars_by_priority[opp.title][priority_level] = []

        for link in var_group.variables:
            var = Vars.get_record(link)
            var_name = dq.get_unique_var_name(var)

            # opp_vars_by_group[opp.title][var_group.name].add(var_name)
            opp_vars_by_group[opp.title][var_group.name].append(var_name)

            # opp_vars_by_priority[opp.title][priority_level].add(var_name)
            if var_name not in opp_vars_by_priority[opp.title][priority_level]:
                # If the same variable is requested by >1 variable group at the same priority level, it might already be in the list
                opp_vars_by_priority[opp.title][priority_level].append(var_name)

        if len(opp_vars_by_group[opp.title][var_group.name]) != len(set(opp_vars_by_group[opp.title][var_group.name])):
            raise Exception('overlap between variable groups for opportunity: ' + opp.title)

###############################################################################
# The above has used the "request" part of the data request to find out what variables
# are requested by each opportunity.
# Now use the "data" part, i.e. tables that define the variables, to retrieve info
# about each variable.

# base = dq.create_dreq_tables_for_variables(content)
base = dq.create_dreq_tables_for_variables(deepcopy(content), consolidated=use_consolidated)


Vars = base['Variables']

# Choose which table to use for freqency

# freq_table_name = 'Frequency'  # not available in v1.0beta release export, need to use CMIP7 or CMIP6 one instead
# freq_table_name = 'CMIP7 Frequency'
# freq_table_name = 'CMIP6 Frequency (legacy)'

try_freq_table_name = []
try_freq_table_name.append('Frequency')
try_freq_table_name.append('CMIP7 Frequency')
try_freq_table_name.append('CMIP6 Frequency (legacy)')

for freq_table_name in try_freq_table_name:
    freq_attr_name = dreq_classes.format_attribute_name(freq_table_name)
    # assert freq_attr_name in Vars.attr2field, 'attribute not found: ' + freq_attr_name
    if freq_attr_name not in Vars.attr2field:
        continue
    if 'frequency' not in Vars.attr2field:
        # code below assumes a variable's frequency is given by its "frequency" 
        Vars.rename_attr(freq_attr_name, 'frequency')
    if freq_table_name in base:
        Frequency = base[freq_table_name]
    break

SpatialShape = base['Spatial Shape']
Dimensions = base['Coordinates and Dimensions']
TemporalShape = base['Temporal Shape']
CellMethods = base['Cell Methods']
PhysicalParameter = base['Physical Parameters']

CFStandardName = None
if 'CF Standard Names' in base:
    CFStandardName = base['CF Standard Names']

# Use compound name to look up record id of each variable in the Vars table
var_name_map = {record.compound_name : record_id for record_id, record in Vars.records.items()}
assert len(var_name_map) == len(Vars.records), 'compound names do not uniquely map to variable record ids'

# Dicts to store the results
plev_info = {} # records list of pressure levels in each plev set, indexed by plev set name
opp_var_info = OrderedDict()
opp_var_info_by_group = OrderedDict()
opp_var_plev = OrderedDict()
all_var_info = {}
opp_vars_at_multiple_priorities = defaultdict(set)

# Loop over opportunities (sorted by title)
opp_titles = sorted(list(opp_vars_by_priority), key=str.lower)
for opp_title in opp_titles:

    var_plev = OrderedDict() # records plev set, indexed by compound name
    var_info = OrderedDict() # records a collection of info about a variable, indexed by compound name
    opp_var_plev[opp_title] = var_plev
    opp_var_info[opp_title] = var_info

    # Determin var_plev, var_info for all variables requested by this opportunity
    for priority_level, var_names in opp_vars_by_priority[opp_title].items():
        # print('\n', priority_level, var_names)
        for var_name in var_names:
            record_id = var_name_map[var_name]
            var = Vars.records[record_id] # variable record, representing one variable
            # var = Vars.get_record(record_id)
            assert var.compound_name == var_name, 'is compound name being used as the unique variable name?'
            # print('  ', priority_level, var_name, record_id)
            del record_id

            if var_name in var_info:
                # This means the variable is already requested at another priority level in opportunity.
                # Should this be allowed? Not sure.
                # If not allowed, then should be cleaned up in the primary info source (i.e., Airtable).
                # Output a json file summarizing the offending variables.
                opp_vars_at_multiple_priorities[opp_title].add(var_name)

            # Follow links starting from the variable record to find out info about the variable
            var_info[var_name] = OrderedDict()

            if isinstance(var.frequency[0], str):
                # retain this option for non-consolidated raw export?
                assert isinstance(var.frequency, list)
                frequency = var.frequency[0]
            else:
                link = var.frequency[0]
                freq = Frequency.get_record(link)
                frequency = freq.name

            link = var.temporal_shape[0]
            temporal_shape = TemporalShape.get_record(link)

            if hasattr(var, 'cell_methods'):
                assert len(var.cell_methods) == 1
                link = var.cell_methods[0]
                cell_methods = CellMethods.get_record(link).cell_methods
            else:
                cell_methods = ''

            # get the 'Spatial Shape' record, which contains info about dimensions
            assert len(var.spatial_shape) == 1
            link = var.spatial_shape[0]
            spatial_shape = SpatialShape.get_record(link)

            if not hasattr(spatial_shape, 'dimensions'):
                # not all variables have dimensions info
                continue
            levels = ''
            var_dims = []
            for link in spatial_shape.dimensions:
                dims = Dimensions.get_record(link)
                var_dims.append(dims.name)
                if hasattr(dims, 'axis_flag') and dims.axis_flag == 'Z':
                    assert levels == '', 'found more than one vertical dimension'
                    levels = dims.name
                if 'plev' in dims.name:
                    if var_name not in var_plev:
                        # record the plev set used by this variable
                        var_plev[var_name] = dims.name
                    else:
                        # or, if we already found the pressure levels, make sure they're consistent with what we previously found
                        assert dims.name == var_plev[var_name]

                    # also record, in a separate dict, what these pressure levels actually are
                    if dims.name not in plev_info:
                        # get list of pressure values for this plev set
                        plev_info[dims.name] = [float(s) for s in dims.requested_values.split()]
                        assert dims.units == 'Pa'
                        assert dims.stored_direction == 'decreasing'

            # Get CF standard name, if it exists
            # record_id = var.cf_standard_name_from_physical_parameter[0]  # not a real link! 
            # phys_param = PhysicalParameter.get_record(record_id)
            link = var.physical_parameter[0]
            phys_param = PhysicalParameter.get_record(link)
            if hasattr(phys_param, 'cf_standard_name'):
                if isinstance(phys_param.cf_standard_name, str):
                    # retain this option for non-consolidated raw export?
                    var_info[var_name].update({
                        'CF standard name' : phys_param.cf_standard_name,
                    })
                else:
                    link = phys_param.cf_standard_name[0]
                    cfsn = CFStandardName.get_record(link)
                    var_info[var_name].update({
                        'CF standard name' : cfsn.name,
                    })
            else:
                var_info[var_name].update({
                    'CF standard name (proposed)' : phys_param.proposed_cf_standard_name,
                })

            var_info[var_name].update({
                'units' : phys_param.units,
                'cell_methods' : cell_methods,
                'dimensions' : ' '.join(var_dims),
                'frequency' : frequency,
                'spatial_shape' : spatial_shape.name,
                'temporal_shape' : temporal_shape.name,
                'vertical_levels' : levels,
                # 'hor_label_dd' : spatial_shape.hor_label_dd,
                # 'vertical_label_dd' : spatial_shape.vertical_label_dd,
                # 'temporal_brand' : temporal_shape.brand,
            })

            if var_name not in all_var_info:
                all_var_info[var_name] = var_info[var_name]

    # Store the same var_info in another dict that groups variables by their variable groups
    # (in case this is more convenient for reviewing variable groups)
    # opp_var_info_by_group[opp_title] = {var_group_name : {} for var_group_name in opp_vars_by_group[opp_title]}
    opp_var_info_by_group[opp_title] = {var_group_name : OrderedDict() for var_group_name in opp_vars_by_group[opp_title]}
    for var_group_name, var_names in opp_vars_by_group[opp_title].items():
        for var_name in var_names:
            opp_var_info_by_group[opp_title][var_group_name][var_name] = var_info[var_name]

# Sort the all-variables dict
d = OrderedDict()
for var_name in sorted(all_var_info.keys(), key=str.lower):
    d[var_name] = all_var_info[var_name]
all_var_info = d
del d


# For each levels set, list all the variables requested on it
requests = {}
for var_name, var_info in all_var_info.items():
    levs = var_info['vertical_levels']
    if levs == '':
        continue
    if levs not in requests:
        requests[levs] = set()
    requests[levs].add(var_name)
d = OrderedDict()
for levs in sorted(requests.keys(), key=str.lower):
    d[levs] = sorted(requests[levs], key=str.lower)
requests = d
del d





###############################################################################
# write various kinds json files summarizing the info

# write file that says what each plev grid is
filepath = 'plev_info.json'
order = [t[1] for t in sorted([(len(v),k) for k,v in plev_info.items()])]
d = OrderedDict()
for s in order:
    d[s] = plev_info[s]
plev_info = d
del d 
with open(filepath, 'w') as f:
    # json.dump(plev_info, f, indent=4, sort_keys=True)
    json.dump(plev_info, f, indent=4)
    print('wrote ' + filepath)

# write file giving plevs for all variables in an opportunity on plevs
filepath = 'opp_var_plev.json'
with open(filepath, 'w') as f:
    json.dump(opp_var_plev, f, indent=4, sort_keys=True)
    # json.dump(opp_var_plev, f, indent=4)
    print('wrote ' + filepath)

# write file giving selected info on all variables in an opportunity (including their vertical levels)
filepath = 'opp_var_info.json'
with open(filepath, 'w') as f:
    json.dump(opp_var_info, f, indent=4, sort_keys=True)
    # json.dump(opp_var_info, f, indent=4)
    print('wrote ' + filepath)

# write another file giving selected info on all variables in an opportunity, 
# but this one groups the variables by their variable groups
filepath = 'opp_var_info_by_group.json'
with open(filepath, 'w') as f:
    json.dump(opp_var_info_by_group, f, indent=4)
    print('wrote ' + filepath)

# write yet another file giving the same variable info, but this one doesn't group anything
# by opportunity, so each variable appears only once
filepath = 'all_var_info.json'
with open(filepath, 'w') as f:
    json.dump(all_var_info, f, indent=4)
    print('wrote ' + filepath)

if len(opp_vars_at_multiple_priorities) > 0:
    # Write file indicating which opportunities have requested the same variable at multiple priority levels
    filepath = 'opp_vars_at_multiple_priorities.json'
    opp_vars_at_multiple_priorities = {k : sorted(v, key=str.lower) for k,v in opp_vars_at_multiple_priorities.items()}
    with open(filepath, 'w') as f:
        json.dump(opp_vars_at_multiple_priorities, f, indent=4, sort_keys=True)
        print('wrote ' + filepath)

filepath = 'requested_by_level.json'
with open(filepath, 'w') as f:
    json.dump(requests, f, indent=4)
    print('wrote ' + filepath)

filepath = 'requested_by_plev.json'
requests2 = {k:v for k,v in requests.items() if k.startswith('plev')}
with open(filepath, 'w') as f:
    json.dump(requests2, f, indent=4)
    print('wrote ' + filepath)


