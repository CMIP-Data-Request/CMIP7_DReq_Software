#!/usr/bin/env python

import sys
import json
add_paths = ['../../sandbox/MS/dreq_api/']
for path in add_paths:
    if path not in sys.path:
        sys.path.append(path)
import dreq_content as dc
import dreq_query as dq

from importlib import reload
reload(dq)


# use_dreq_version = 'first_export'
use_dreq_version = 'v1.0alpha'

# Download specified version of data request content (if not locally cached)
dc.retrieve(use_dreq_version)
# Load content into python dict
content = dc.load(use_dreq_version)


# use subset of opportunities:
use_opps = []
use_opps.append('Baseline Climate Variables for Earth System Modelling')
use_opps.append('Synoptic systems and impacts')

# use all opportunities:
Opps = base['Opportunity']
use_opps = [opp.title for opp in Opps.records.values()]


dq.DREQ_VERSION = use_dreq_version
base = dq.create_dreq_table_objects(content)
opp_expt_vars = {opp_title : {} for opp_title in use_opps}
for opp_title in use_opps:
    opp_expt_vars[opp_title] = dq.get_requested_variables(base, [opp_title], max_priority='Low')

Vars = base['Variables']
SpatialShape = base['Spatial Shape']
Dimensions = base['Coordinates and Dimensions']
Frequency = base['Frequency']
TemporalShape = base['Temporal Shape']
CellMethods = base['Cell Methods']

# Use compound name to look up record id
var_name_map = {record.compound_name : record_id for record_id, record in Vars.records.items()}
assert len(var_name_map) == len(Vars.records), 'compound names do not uniquely map to variable record ids'

plev_info = {} # records list of pressure levels in each plev set, indexed by plev set name
opp_var_info = {}
opp_var_plev = {}
for opp_title in opp_expt_vars:

    expt_vars = opp_expt_vars[opp_title]['experiment']
    if len(expt_vars) == 0:
        print(opp_title)
        continue
    expt = list(expt_vars.keys())[0] # 1st experiment is sufficient, request is same for all experiments in an opportunity

    var_plev = {} # records plev set, indexed by compound name
    var_info = {} # records a collection of info about a variable, indexed by compound name
    opp_var_plev[opp_title] = var_plev
    opp_var_info[opp_title] = var_info

    for priority_level, var_names in expt_vars[expt].items():
        # print('\n', priority_level, var_names)
        for compound_name in var_names:
            record_id = var_name_map[compound_name]
            var = Vars.records[record_id]
            # var = Vars.get_record(record_id)
            assert var.compound_name == compound_name
            # print('  ', priority_level, compound_name, record_id)
            del record_id

            if compound_name not in var_info:
                var_info[compound_name] = {}
            
            link = var.frequency[0]
            # freq = Frequency.records[link.record_id]
            freq = Frequency.get_record(link)

            link = var.temporal_shape[0]
            # temporal_shape = TemporalShape.records[link.record_id]
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
            # spatial_shape = SpatialShape.records[link.record_id]
            spatial_shape = SpatialShape.get_record(link)

            if not hasattr(spatial_shape, 'dimensions'):
                # not all variables have dimensions info
                continue
            levels = ''
            for link in spatial_shape.dimensions:
                # dims = Dimensions.records[link.record_id]
                dims = Dimensions.get_record(link)
                if hasattr(dims, 'axis_flag') and dims.axis_flag == 'Z':
                    assert levels == '', 'found more than one vertical dimension'
                    levels = dims.name
                if 'plev' in dims.name:
                    if compound_name not in var_plev:
                        # record the plev set used by this variable
                        var_plev[compound_name] = dims.name
                    else:
                        # or, if we already found the pressure levels, make sure they're consistent with what we previously found
                        assert dims.name == var_plev[compound_name]

                    # also record, in a separate dict, what these pressure levels actually are
                    if dims.name not in plev_info:
                        # get list of pressure values for this plev set
                        plev_info[dims.name] = [float(s) for s in dims.requested_values.split()]
                        assert dims.units == 'Pa'
                        assert dims.stored_direction == 'decreasing'

            var_info[compound_name].update({
                'cell_methods' : cell_methods,
                'frequency' : freq.name,
                'spatial_shape' : spatial_shape.name,
                'hor_label_dd' : spatial_shape.hor_label_dd,
                'vertical_label_dd' : spatial_shape.vertical_label_dd,
                'vertical_levels' : levels,
                # 'temporal_shape' : temporal_shape.name,
                # 'temporal_brand' : temporal_shape.brand,
            })


# write file giving plevs for all variables in an opportunity on plevs
filepath = 'opp_var_plev.json'
with open(filepath, 'w') as f:
    json.dump(opp_var_plev, f, indent=4, sort_keys=True)
    print('wrote ' + filepath)

# write file giving selected info on all variables in an opportunity (including their vertical levels)
filepath = 'opp_var_info.json'
with open(filepath, 'w') as f:
    json.dump(opp_var_info, f, indent=4, sort_keys=True)
    print('wrote ' + filepath)

# write file that says what each plev grid is
filepath = 'plev_info.json'
with open(filepath, 'w') as f:
    json.dump(plev_info, f, indent=4, sort_keys=True)
    print('wrote ' + filepath)
