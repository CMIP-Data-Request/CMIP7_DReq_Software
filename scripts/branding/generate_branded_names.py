#!/usr/bin/env python
'''
Generating branded variable names using the mapper:
    https://github.com/znicholls/CMIP-branded-variable-mapper
This can be installed with:
    pip install cmip-branded-variable-mapper    

Was used to generate branded names for v1.2.2.2 DR content.
'''
import argparse
import json
import sys
from collections import OrderedDict

from cmip_branded_variable_mapper import map_to_cmip_branded_variable
from cmip_branded_variable_mapper import __version__ as bvm_version


def parse_args():

    parser = argparse.ArgumentParser(
        description='Generate branded names from DR variables metadata'
    )

    parser.add_argument('input_file', type=str, help='input JSON file containing data request variables metadata \
                        (produced by get_variables_metadata command-line tool)')
    parser.add_argument('output_file', type=str, help='output JSON file that will match the input file except \
                        with new or updated branded names')

    return parser.parse_args()

def main():

    args = parse_args()

    filepath = args.input_file
    outpath = args.output_file

    if outpath == filepath:
        proceed = input('Overwrite input file? Hit "y" to continue, otherwise will abort ')
        if proceed != 'y':
            sys.exit()

    with open(filepath, 'r') as f:
        d = json.load(f)
        print('Loaded ' + filepath)
        vars = d['Compound Name']
        Header = d['Header']
        del d

    # Loop over all DR variables in the input file
    for var_name, var_info in vars.items():

        # Get metadata required to generate branded variable name
        cell_methods = var_info['cell_methods']
        dimensions = tuple(var_info['dimensions'].split())
        root_name = var_info['variableRootDD']

        # Run the branded variable mapper
        branded_name = map_to_cmip_branded_variable(
            variable_name=root_name,
            cell_methods=cell_methods,
            dimensions=dimensions
        )

        # Do some basic checks on the result
        if branded_name.count('_') != 1:
            raise ValueError(f'Error in branded name: {branded_name}')
        root_name, branding_label = branded_name.split('_')
        if root_name != var_info['variableRootDD']:
            raise ValueError(f'Error in branded name: {branded_name}')
        if var_info['out_name'] != root_name:
            # This check isn't specifically related to the branding algorithm, but AFAIK we do expect the DR
            # metadata file use the same short name for the root name and outname.
            raise ValueError(f'Out name {var_info["out_name"]} does not match root name {root_name}')

        # Update the variable's metadata dict
        var_info.update({
            "branding_label": branding_label,
            "branded_variable_name": branded_name,
        })
        # Set CMIP7 compound name according to the recipe adopted for the AFT DR
        # For purpose of compound name generation, only use the primary modeling realm
        # (first entry in list of realms, if the list has more than one entry)
        d = dict(var_info)
        d['primary_modeling_realm'] = d['modeling_realm'].split()[0]
        cmip7_compound_name = '{primary_modeling_realm}.{variableRootDD}.{branding_label}.{frequency}.{region}'.format(**d)
        del d
        var_info.update({
            "cmip7_compound_name": cmip7_compound_name,
        })

    # Include mapper version in the output file header
    Header['CMIP-branded-variable-mapper version'] = bvm_version
    
    # Write output file
    out = OrderedDict({
        'Header': Header,
        'Compound Name': vars,
    })
    with open(outpath, 'w') as f:
        json.dump(out, f, indent=4)
        print(f'Wrote {outpath}')

    # While we're here, show stats about uniqueness of different types of vairable names
    name_check = []
    name_check.append('cmip6_compound_name')
    name_check.append('cmip7_compound_name')
    name_check.append('uid')
    name_check.append('branded_variable_name')
    print(f'no. of DR variables: {len(vars)}')
    for name_type in name_check:
        var_names_list = [var_info[name_type] for var_info in vars.values()]
        var_names = set(var_names_list)
        print(f'unique "{name_type}": {len(var_names)}')

if __name__ == '__main__':
    main()
