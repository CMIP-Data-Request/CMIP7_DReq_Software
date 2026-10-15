#!/usr/bin/env python
'''
Make variable group yaml file from json or csv input
'''

import argparse
import csv
import json
import yaml

from pathlib import Path

import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq
import data_request_api.query.dreq_variables as dv


def parse_args():
    ''' Parse command line arguments'''
    parser = argparse.ArgumentParser(description="Create variable group yaml file from json or csv input")

    # Mandatory arguments
    parser.add_argument('input', 
                        help="Variables to include (json or csv)")
    parser.add_argument('output', 
                        help="Variable group filename, example: new_variable_group.yaml")

    parser.add_argument('-v', '--validate', type=str, default='latest',
                        help='DR version against which to validate, examples: "latest", "v1.2.2.5"')   

    return parser.parse_args()


def main():
    args = parse_args()

    filepath = Path( args.input )
    var_name_key = 'Compound Name'
    if filepath.suffix == '.json':
        with open(filepath, 'r') as f:
            vars = json.load(f)[var_name_key]
    elif filepath.suffix == '.csv':
        with open(filepath) as f:
            reader = csv.reader(f)
            vars = {}
            columns = next(reader)
            for row in reader:
                var_info = {col:val for col,val in zip(columns, row)}
                var_name = var_info[var_name_key]
                del var_info[var_name_key]
                vars[var_name] = var_info
    else:
        raise ValueError(f'Unrecognized input file type: {filepath.suffix}')

    # Template content
    vg_template = {
        'Title': 'Short descriptive title of the Variable Group',
        'Priority Level': 'Set to "High", "Medium", or "Low" (not case sensitive)',
        'Justification': '(Optional) Explanation of why these variables are important.',
        'Notes': '(Optional) Any additional comments about the variable group.',
        'Variables': [],  # list of requested variable names
    }

    # Get DR variables for reference, to validate the submitted variables
    dreq_version = args.validate
    if dreq_version.lower() == 'latest':
        dreq_version = dc._get_latest_version()
    dc.retrieve(dreq_version)
    dr_content = dc.load(dreq_version)
    # Get metadata for variables
    vars_reference = dq.get_variables_metadata(dr_content, dreq_version)
    # Ensure it is keyed by CMIP7 Compound Name
    vars_reference = {var_info['cmip7_compound_name']: var_info for var_info in vars_reference.values()}

    # For the Variable Group template, ensure the CMIP7 Compound Name is used to name variables
    available_values = dv.get_available_values(vars_reference)
    var_names = set(vars.keys())
    valid_var_name_types = [
        'cmip7_compound_name',
        'cmip6_compound_name',
        'uid'
    ]
    n = len(available_values['cmip7_compound_name'])
    for var_name_type in valid_var_name_types:
        if len(available_values[var_name_type]) != n:
            # This should not happen, but check just in case
            raise ValueError(f'Mapping from cmip7_compound_name to {var_name_type} is not unique!')

    if var_names.issubset(available_values['cmip7_compound_name']):
        mapping = None
    elif var_names.issubset(available_values['cmip6_compound_name']):
        mapping = {var_info['cmip6_compound_name']: var_info['cmip7_compound_name']
                   for var_info in vars_reference.values()}
    elif var_names.issubset(available_values['uid']):
        mapping = {var_info['uid']: var_info['cmip7_compound_name']
                   for var_info in vars_reference.values()}
    else:
        raise ValueError('Could not determine a single type of variable name. Options are: ' +
                         ', '.join(valid_var_name_types))
    if mapping:
        vars = {mapping[var_name]: vars[var_name] for var_name in vars}

    # Check that submitted variables (from user input) agree with the reference DR variables
    for var_name, var_info in vars.items():
        ref_var_info = vars_reference[var_name]
        for attr in var_info:
            if var_info[attr] != ref_var_info[attr]:
                print(f'{var_name} mismatch for {attr}: expected {ref_var_info[attr]}, received {var_info[attr]}')

    vg_template['Variables'] = sorted(vars.keys(), key=str.lower)

    filepath = args.output
    with open(filepath, 'w') as f:
        yaml.dump(vg_template, f, sort_keys=False, indent=2)
        print(f'Wrote {filepath}')


if __name__ == '__main__':
    main()

