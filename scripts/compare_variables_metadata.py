#!/usr/bin/env python
'''
Compare CMOR variable metadata extracted from data request (dreq) content to other tables, such as CMIP6 cmor tables.
'''
import json
import os
from collections import OrderedDict
###############################################################################

filter_by_cmor_table = not True  # False ==> include all tables, and include_cmor_tables is ignored
include_cmor_tables = ['Amon', 'day']

# File containing variable metadata extracted from data request content
filepath = '_all_var_info.json'

# Name of output file to write with the diffs
outfile_name = 'diffs_by_variable_name.json'
outfile_attr = 'diffs_by_metadata_attribute.json'

# Names of attributes to compare
compare_attributes = [
    'frequency', 
    'modeling_realm', 
    'standard_name', 
    'units', 
    'cell_methods', 
    'cell_measures', 
    'long_name', 
    # 'comment', 
    'dimensions', 
    # 'out_name', 
    'type', 
    'positive',     
]
# compare_attributes = ['standard_name']
# compare_attributes = ['units']
# compare_attributes = ['dimensions']
# compare_attributes = ['cell_methods']
# compare_attributes = ['frequency']

check_min_max_attributes = True
min_max_attributes = [
    'valid_min', 
    'valid_max', 
    'ok_min_mean_abs', 
    'ok_max_mean_abs',
]

# Corrections for typos or minor differences in dreq var names from their equivalents in the tables that
# we're comparing to. These could reflect updates or errors in the dreq var names, but in any case it's
# useful to ignore them for the comparison.
name_corrections = {
    'Amon.co2massCLim' : 'Amon.co2massClim'
}

###############################################################################

# Load file containing info on dreq variables
with open(filepath, 'r') as f:
    d = json.load(f)
    dreq_vars = d['Compound Name']
    dreq_header = d['Header']
    del d
    print('Loaded ' + filepath)

# Download CMOR tables for comparison, if necessary
repo_tables = 'https://github.com/PCMDI/cmip6-cmor-tables'
repo_name = os.path.basename(os.path.normpath(repo_tables))
filename_template = 'CMIP6_{table}.json'
path_tables = f'{repo_name}/Tables'
if not os.path.exists(repo_name):
    cmd = f'git clone {repo_tables}'
    os.system(cmd)
assert os.path.exists(path_tables), 'missing path to CMOR tables: ' + path_tables


dreq_tables = set([var_info['cmip6_cmor_table'] for var_info in dreq_vars.values()])
include_cmor_tables = sorted(set(include_cmor_tables), key=str.lower)
if filter_by_cmor_table:
    for table_id in list(include_cmor_tables):
        if table_id not in dreq_tables:
            print(f'WARNING: excluding table {table_id} that is not found in data request')
            include_cmor_tables.remove(table_id)
    # include_cmor_tables = [table_id for table_id in include_cmor_tables if table_id in dreq_tables]
else:
    # Use all available tables
    include_cmor_tables = sorted(dreq_tables, key=str.lower)

for old,new in name_corrections.items():
    if old in dreq_vars:
        assert new not in dreq_vars, f'variable already exists in dreq: {new}'
        dreq_vars[new] = dreq_vars[old]
        dreq_vars.pop(old)

missing_from_table_vars = set()
missing_from_dreq_vars = set()
diffs = OrderedDict()
table_header0 = None
table_header_keep = [
    'data_specs_version',
    'cmor_version', 
    'table_date', 
    'mip_era', 
    'Conventions',
]
tables_checked = []
attr_diffs = set()
for table_id in include_cmor_tables:
    filepath = os.path.join(path_tables, filename_template.format(table=table_id))
    if not os.path.exists(filepath):
        print(f'{filepath} not found, skipping this table')
        continue
    with open(filepath, 'r') as f:
        cmor_table = json.load(f)
        print('Loaded ' + filepath)
        table_vars = cmor_table['variable_entry']
        table_header = {k:v for k,v in cmor_table['Header'].items() if k in table_header_keep}
        if table_header0 is None:
            table_header0 = table_header
        else:
            assert table_header == table_header0, f'inconsistent table header info from {filepath}'
        del cmor_table
    tables_checked.append(table_id)

    # Names of all variables found in the cmor table
    table_var_names = set([f'{table_id}.{variable_id}' for variable_id in table_vars])
    # Names of all dreq variables with the same table_id
    dreq_var_names = set([var_name for var_name,var_info in dreq_vars.items() \
                          if var_info['cmip6_cmor_table'] == table_id])
    # Get names of dreq vars that are not in the cmor table
    missing_from_table_vars.update( dreq_var_names.difference(table_var_names) )
    # Get names of cmor table vars that are not in the dreq
    missing_from_dreq_vars.update( table_var_names.difference(dreq_var_names) )

    # Go variable-by-variable to compare metadata
    for variable_id in table_vars:
        table_var_info = table_vars[variable_id]

        var_name = f'{table_id}.{variable_id}'
        if var_name in missing_from_dreq_vars:
            continue
        dreq_var_info = dreq_vars[var_name]

        var_diff = OrderedDict()
        for attr in compare_attributes:
            if attr not in dreq_var_info:
                continue
            if table_var_info[attr] != dreq_var_info[attr]:
                var_diff[attr] = OrderedDict({
                    'PREV' : table_var_info[attr],
                    'DREQ' : dreq_var_info[attr],
                })
                attr_diffs.add(attr)
        if len(var_diff) > 0:
            diffs[var_name] = var_diff

        if check_min_max_attributes:
            for attr in min_max_attributes:
                if attr in table_var_info:
                    if table_var_info[attr] not in ['']:
                        print(f'{var_name}  {attr} : {table_var_info[attr]}')


out = OrderedDict({
    'Header' : {
        'Description': 'Comparison of variable metadata between data request (DREQ) and previous cmor tables (PREV)',
        'dreq content version': dreq_header['dreq content version'],
        'dreq content file' : dreq_header['dreq content file'],
        'dreq content sha256 hash' : dreq_header['dreq content sha256 hash'],
        'cmor tables source' : repo_tables,
        'cmor tables version' : table_header0,
        'tables checked' : tables_checked,
    },
    'Compound Name' : diffs
})
outfile = outfile_name
with open(outfile, 'w') as f:
    json.dump(out, f, indent=4)
    print('Wrote ' + outfile)

# Write another output file with the same info but instead organized by attribute as the top-level dict key
diffs_by_attr = OrderedDict()
attr_diffs = sorted(attr_diffs, key=str.lower)
for attr in attr_diffs:
    diffs_by_attr[attr] = OrderedDict()
for var_name, var_diff in diffs.items():
    for attr in var_diff:
        diffs_by_attr[attr][var_name] = var_diff[attr]
del out['Compound Name']
out['Metadata Attribute'] = diffs_by_attr
outfile = outfile_attr
with open(outfile, 'w') as f:
    json.dump(out, f, indent=4)
    print('Wrote ' + outfile)

# Summarize what was fond
print(f'\nTotal number of variables with differences: {len(diffs)}')
print(f'Number of variables with differences in each metadata attribute:')
m = max([len(s) for s in attr_diffs])
fmt = f'%-{m}s'
for attr in attr_diffs:
    n = len(diffs_by_attr[attr])
    print(f'  {fmt % attr}  {n}')
