#!/usr/bin/env python
'''
Extract metadata of CMOR variables and write them to a json file.
Example output file: scripts/variable_info/all_var_info.json
Output file names (filepath) are set below.
'''
import argparse
import hashlib
import json
import os
from collections import OrderedDict

import sys
sys.path.append(os.path.abspath('..'))

import data_request_api.stable.content.dreq_api.dreq_content as dc
import data_request_api.stable.query.dreq_query as dq
from data_request_api.stable.query import dreq_classes
from data_request_api import version as api_version
from data_request_api.stable.utilities.tools import write_csv_output_file_content


default_dreq_version = 'v1.1'

outfile_extensions = ['.json', '.csv']

parser = argparse.ArgumentParser(
    description='Get CMOR variables metadata and write to json.'
    )
parser.add_argument('-dr', '--dreq_version', type=str, default=default_dreq_version,
                    help='version of data request content to use')
parser.add_argument('-o', '--outfile', nargs='+', type=str,
                    help=f'outfile (one or more), identified by extensions: {outfile_extensions}')
# parser.add_argument('-oj', '--outfile_json', type=str, default='all_var_info.json',
#                     help='name of output json file for variables metadata')
# parser.add_argument('-oc', '--outfile_csv', type=str, default='all_var_info.csv',
#                     help='name of output csv file for variables metadata')135
parser.add_argument('-t', '--cmor_tables', nargs='+', type=str,
                    help='include only the specified CMOR tables (aka MIP tables, examples: "Amon", "Omon")')
parser.add_argument('-v', '--cmor_variables', nargs='+', type=str,
                    help='include only the specified CMOR variables (out_name, examples: "tas", "siconc")')
args = parser.parse_args()


# Load data request content
use_dreq_version = args.dreq_version
dc.retrieve(use_dreq_version)  
content = dc.load(use_dreq_version)

# Get metadata for variables
all_var_info = dq.get_variables_metadata(
    content,
    cmor_tables=args.cmor_tables,
    cmor_variables=args.cmor_variables,
    use_dreq_version=use_dreq_version  # TO DEPRECATE
    )


for filepath in args.outfile:
    ext = os.path.splitext(filepath)[-1]

    if ext == '.json':
        # Get provenance of content to include in the Header
        content_path = dc._dreq_content_loaded['json_path']
        with open(content_path, 'rb') as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()

        # Create output dict
        out = OrderedDict({
            'Header' : OrderedDict({
                'Description' : 'Metadata attributes that characterize CMOR variables. Each variable is uniquely idenfied by a compound name comprised of a CMIP6-era table name and a short variable name.',
                'no. of variables' : len(all_var_info),
                'dreq content version': use_dreq_version,
                'dreq content file' : os.path.basename(os.path.normpath(content_path)),
                'dreq content sha256 hash' : content_hash,
                'dreq api version' : api_version,
            }),
            'Compound Name' : all_var_info,
        })

        # Write variables metadata to json
        with open(filepath, 'w') as f:
            json.dump(out, f, indent=4)
            print(f'Wrote {filepath} for {len(all_var_info)} variables, dreq version = {use_dreq_version}')

    elif ext == '.csv':
        # Write variables metadata to csv
        var_info = next(iter(all_var_info.values()))
        attrs = list(var_info.keys())
        columns = ['Compound Name']
        columns.append('standard_name')
        columns.append('standard_name_proposed')
        columns += [s for s in attrs if s not in columns]
        rows = [columns]  # column header line
        # Add each variable as a row
        for var_name, var_info in all_var_info.items():
            row = []
            for col in columns:
                if col == 'Compound Name':
                    val = var_name
                elif col in var_info:
                    val = var_info[col]
                else:
                    val = ''
                row.append(val)
            rows.append(row)
        write_csv_output_file_content(filepath, rows)
        n = out['Header']['no. of variables']
        print(f'Wrote {filepath} for {n} variables, dreq version = {use_dreq_version}')





###############################################################################

organize_by_standard_name = False  # True ==> write additional file that groups variables by CF standard name

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
        print(f'wrote {filepath} for {n} variables, dreq version = {use_dreq_version}')

###############################################################################
