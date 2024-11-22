#!/usr/bin/env python
'''
Extract metadata of CMOR variables and write to json
'''
import sys
import json
import os
import hashlib
add_paths = []
add_paths.append('../content/dreq_api')
add_paths.append('../transform')
for path in add_paths:
    if path not in sys.path:
        sys.path.append(path)
import dreq_content as dc
import dreq_query as dq
import dreq_classes

from collections import OrderedDict

# from importlib import reload
# reload(dq)
# reload(dc)
###############################################################################


filter_by_cmor_table = not True  # False ==> include all tables (i.e., all variables in the data request)
include_cmor_tables = ['Amon', 'day']

organize_by_standard_name = True  # True ==> write additional file that groups variables by CF standard name


###############################################################################
# Load data request content

use_dreq_version = 'v1.0beta'

# Download specified version of data request content (if not locally cached)
dc.retrieve(use_dreq_version)
# Load content into python dict
content = dc.load(use_dreq_version)

###############################################################################
# Retrive info about variables

base = dq.create_dreq_tables_for_variables(content)

Vars = base['Variables']
# The Variables table is the master list of variables in the data request.
# Each entry (row) is a CMOR variable, containing the variable's metadata.
# Many of these entries are links to other tables in the database (see below).

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

# Get other tables from the database that are required to find all of a variable's metadata used by CMOR.
SpatialShape = base['Spatial Shape']
Dimensions = base['Coordinates and Dimensions']
TemporalShape = base['Temporal Shape']
CellMethods = base['Cell Methods']
PhysicalParameter = base['Physical Parameters']
CFStandardName = None
if 'CF Standard Names' in base:
    CFStandardName = base['CF Standard Names']
CMORtables = base['Table Identifiers']
Realm = base['Modelling Realm']
CellMeasures = base['Cell Measures']

# Compound names will be used to uniquely identify variables.
# Check here that this is indeed a unique name as expected.
var_name_map = {record.compound_name : record_id for record_id, record in Vars.records.items()}
assert len(var_name_map) == len(Vars.records), 'compound names do not uniquely map to variable record ids'

if filter_by_cmor_table:
    print('Retaining only these CMOR tables: ' + ', '.join(include_cmor_tables))

substitute = {
    # replacement character(s) : [characters to replace with the replacement character]
    '_' : ['\\_']
}
all_var_info = {}
for var in Vars.records.values():

    assert len(var.table) == 1
    table_id = CMORtables.get_record(var.table[0]).name

    if filter_by_cmor_table:
        if table_id not in include_cmor_tables:
            continue

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

    cell_methods = ''
    area_label_dd = ''
    if hasattr(var, 'cell_methods'):
        assert len(var.cell_methods) == 1
        link = var.cell_methods[0]
        cm = CellMethods.get_record(link)
        cell_methods = cm.cell_methods
        if hasattr(cm, 'brand_id'):
            area_label_dd = cm.brand_id

    # get the 'Spatial Shape' record, which contains info about dimensions
    assert len(var.spatial_shape) == 1
    link = var.spatial_shape[0]
    spatial_shape = SpatialShape.get_record(link)

    dims_list = []
    dims = None
    if hasattr(spatial_shape, 'dimensions'):
        for link in spatial_shape.dimensions:
            dims = Dimensions.get_record(link)
            dims_list.append(dims.name)
    dims_list.append(temporal_shape.name)

    # Get CF standard name, if it exists
    # record_id = var.cf_standard_name_from_physical_parameter[0]  # not a real link! 
    # phys_param = PhysicalParameter.get_record(record_id)
    link = var.physical_parameter[0]
    phys_param = PhysicalParameter.get_record(link)
    out_name = phys_param.name
    standard_name = ''
    standard_name_proposed = ''
    if hasattr(phys_param, 'cf_standard_name'):
        if isinstance(phys_param.cf_standard_name, str):
            # retain this option for non-consolidated raw export?
            standard_name = phys_param.cf_standard_name
        else:
            link = phys_param.cf_standard_name[0]
            cfsn = CFStandardName.get_record(link)
            standard_name = cfsn.name
    else:
        standard_name_proposed = phys_param.proposed_cf_standard_name

    modeling_realm = [Realm.get_record(link).id for link in var.modelling_realm]

    cell_measures = ''
    if hasattr(var, 'cell_measures'):
        # assert len(var.cell_measures) == 1
        # link = var.cell_measures[0]
        # cell_measures = CellMeasures.get_record(link).name
        cell_measures = [CellMeasures.get_record(link).name for link in var.cell_measures]

    positive = ''
    if hasattr(var, 'positive_direction'):
        positive = var.positive_direction

    comment = ''
    if hasattr(var, 'description'):
        comment = var.description

    var_info = OrderedDict()
    # Insert fields in order given by CMIP6 cmor tables (https://github.com/PCMDI/cmip6-cmor-tables)
    var_info.update({
        'frequency' : frequency,
        'modeling_realm' : ' '.join(modeling_realm),
    })
    if standard_name != '':
        var_info['standard_name'] = standard_name
    else:
        var_info['standard_name_proposed'] = standard_name_proposed
    var_info.update({
        'units' : phys_param.units,
        'cell_methods' : cell_methods,
        'cell_measures' : ' '.join(cell_measures),

        'long_name' : var.title,
        'comment' : comment,

        'dimensions' : ' '.join(dims_list),
        'out_name' : out_name,
        'type' : var.type,
        'positive' : positive,

        'spatial_shape' : spatial_shape.name,
        'temporal_shape' : temporal_shape.name,

        # 'temporalLabelDD' : temporal_shape.brand,
        # 'verticalLabelDD' : spatial_shape.vertical_label_dd,
        # 'horizontalLabelDD' : spatial_shape.hor_label_dd,
        # 'areaLabelDD' : area_label_dd,  # this comes from cell methods

        'cmip6_cmor_table' : table_id,
    })
    for k,v in var_info.items():
        v = v.strip()
        for replacement in substitute:
            for s in substitute[replacement]:
                if s in v:
                    v = v.replace(s, replacement)
        var_info[k] = v
    var_name = var.compound_name  # note, comment in Header below refers to Compound Name, so update it if this changes
    assert var_name not in all_var_info, 'non-unique variable name: ' + var_name
    all_var_info[var_name] = var_info

    del var_info, var_name


# Sort the all-variables dict
d = OrderedDict()
for var_name in sorted(all_var_info, key=str.lower):
    d[var_name] = all_var_info[var_name]
all_var_info = d
del d


# Get provenance of content to include in the Header
content_path = dc._dreq_content_loaded['json_path']
with open(content_path, 'rb') as f:
    content_hash = hashlib.sha256(f.read()).hexdigest()

out = OrderedDict({
    'Header' : OrderedDict({
        'Description' : 'Metadata attributes that characterize CMOR variables. Each variable is uniquely idenfied by a compound name comprised of a CMIP6-era table name and a short variable name.',
        'dreq version': use_dreq_version,
        'dreq content file' : os.path.basename(os.path.normpath(content_path)),
        'dreq content sha256 hash' : content_hash,
    }),
    'Compound Name' : all_var_info,
})
 
filepath = '_all_var_info.json'
with open(filepath, 'w') as f:
    json.dump(out, f, indent=4)
    print(f'wrote {filepath} for {len(all_var_info)} variables')


###############################################################################
if organize_by_standard_name:

    name_in_file = {
        'standard_name' : 'CF Standard Name',
        'standard_name_proposed' : 'CF Standard Name (Proposed)',
    }
    n = 0
    for sn_type in ['standard_name', 'standard_name_proposed']:
        names = set()
        for var_info in all_var_info.values():
            if sn_type in var_info:
                names.add(var_info[sn_type])
        names = sorted(set(names), key=str.lower)
        sn = OrderedDict()
        for name in names:
            sn[name] = OrderedDict()
            for var_name, var_info in all_var_info.items():
                if sn_type in var_info and var_info[sn_type] == name:
                    sn[name][var_name] = var_info
                    n += 1
        if len(sn) > 0:
            out[name_in_file[sn_type]] = sn
    out.pop('Compound Name')

    out['Header']['Description'] += ' Organized by CF standard name.'

    filepath = '_all_var_info_by_standard_name.json'
    with open(filepath, 'w') as f:
        json.dump(out, f, indent=4)
        print(f'wrote {filepath} for {n} variables')
