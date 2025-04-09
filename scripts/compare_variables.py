#!/usr/bin/env python
'''
Compare CMOR variable metadata between different data request versions or to CMOR tables.
'''
import json
import os
from collections import OrderedDict, defaultdict

import sys
sys.path.append('..')

import argparse

def parse_args():

    parser = argparse.ArgumentParser(
        description='Compare variables metadata between data request versions'
    )

    parser.add_argument('compare', nargs=2,
                        help='versions of variables to compare: json file or cmor tables')

    return parser.parse_args()

def main():

    args = parse_args()
    compare_versions = list(args.compare)


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

    compare_attributes = sorted(compare_attributes, key=str.lower)

    # Name of output file to write with the diffs
    outfile_name = 'diffs_by_variable_name.json'
    outfile_attr = 'diffs_by_metadata_attribute.json'


    repos = {
        'cmip6' : {
            'url': 'https://github.com/PCMDI/cmip6-cmor-tables',
        }
    }

    # If comparing against existing CMOR tables, get variables from them
    for kc, version in enumerate(compare_versions):
        if version in repos:
            # Input specifies CMOR tables available from some repo
            repo_tables = repos[version]['url']
            repo_name = os.path.basename(os.path.normpath(repo_tables))
            # filename_template = repos[version]['filename_template']
            path_tables = f'{repo_name}/Tables'
            if not os.path.exists(repo_name):
                # Clone the repo if needed
                cmd = f'git clone {repo_tables}'
                os.system(cmd)
            if not os.path.exists(path_tables):
                raise Exception('missing path to CMOR tables: ' + path_tables)
            # Load all tables and save their variables in a json file
            outfile = f'{version}.json'
            all_vars = OrderedDict()
            table_files = sorted(os.listdir(path_tables), key=str.lower)
            for filepath in table_files:
                with open(os.path.join(path_tables, filepath), 'r') as f:
                    cmor_table = json.load(f)
                    if 'variable_entry' not in cmor_table:
                        continue
                    table_vars = cmor_table['variable_entry']
                    table_id = cmor_table['Header']['table_id'].split()[-1].strip()
                    if table_id in ['grids']:
                        continue
                for var_name in table_vars:
                    compound_name = f'{table_id}.{var_name}'
                    if compound_name in all_vars:
                        raise ValueError(f'variable {compound_name} was already found!')
                    all_vars[compound_name] = table_vars[var_name]
            out = OrderedDict({
                'Header': {},
                'Compound Name': all_vars,
            })
            with open(outfile, 'w') as f:
                json.dump(out, f, indent=4)
                print('Wrote ' + outfile)
            compare_versions[kc] = outfile

    # Load json files giving metadata of variables
    dreq_vars = {}
    dreq_header = {}
    for version in compare_versions:
        if os.path.splitext(version)[-1] != '.json':
            raise ValueError('json file containing variables metadata is required')
        filepath = version
        with open(filepath, 'r') as f:
            d = json.load(f)
            dreq_vars[version] = d['Compound Name']
            dreq_header[version] = d['Header']
            del d
            print('Loaded ' + filepath)

        # For purpose of comparison, treat a proposed standard_name as a final one
        if 'standard_name' in compare_attributes:
            for var_name, var_info in dreq_vars[version].items():
                if 'standard_name_proposed' in var_info:
                    if 'standard_name' in var_info:
                        raise ValueError(f'{var_name} in {version} should not have both proposed and final standard_name')
                    var_info['standard_name'] = var_info['standard_name_proposed']
                    var_info.pop('standard_name_proposed')

    all_var_names = set()
    for version in dreq_vars:
        all_var_names.update(dreq_vars[version].keys())
    all_var_names = sorted(all_var_names, key=str.lower)

    # Go variable-by-variable to compare metadata
    missing_vars = defaultdict(set)
    diffs = OrderedDict()
    attr_diffs = set()
    for var_name in all_var_names:
        missing = False
        for version in compare_versions:
            if var_name not in dreq_vars[version]:
                missing_vars[version].add(var_name)
                missing = True
        if missing:
            # Variable is not available in both versions
            continue
        ver0, ver1 = compare_versions
        var_info0 = dreq_vars[ver0][var_name]
        var_info1 = dreq_vars[ver1][var_name]
        var_diff = OrderedDict()
        for attr in compare_attributes:
            if attr not in var_info0:
                raise ValueError(f'{var_name} in {ver0} missing attribute: {attr}')
            if attr not in var_info1:
                raise ValueError(f'{var_name} in {ver1} missing attribute: {attr}')
            if var_info1[attr] != var_info0[attr]:
                var_diff[attr] = OrderedDict({
                    ver0: var_info0[attr],
                    ver1: var_info1[attr],
                })
                attr_diffs.add(attr)
        if len(var_diff) > 0:
            diffs[var_name] = var_diff

    print()
    out = OrderedDict({
        'Header' : {
            'Description': f'Comparison of variable metadata between {ver0} and {ver1}',
            # 'dreq content version': dreq_header['dreq content version'],
            # 'dreq content file' : dreq_header['dreq content file'],
            # 'dreq content sha256 hash' : dreq_header['dreq content sha256 hash'],
            # 'cmor tables source' : repo_tables,
            # 'cmor tables version' : table_header0,
            # 'tables checked' : tables_checked,
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
    if len(diffs) > 0:
        print(f'Number of variables with differences in each metadata attribute:')
        m = max([len(s) for s in attr_diffs])
        fmt = f'%-{m}s'
        for attr in attr_diffs:
            n = len(diffs_by_attr[attr])
            print(f'  {fmt % attr}  {n}')


if __name__ == '__main__':
    main()
