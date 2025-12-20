#!/usr/bin/env python
'''
Compare CMOR variable metadata between different data request versions or to CMOR tables.
'''
import argparse
import json
import os
import yaml
from collections import OrderedDict, defaultdict


def parse_args():

    parser = argparse.ArgumentParser(
        description='Compare variables metadata between data request versions'
    )
    parser.add_argument('compare', nargs=2,
                        help='versions of variables to compare: json file or cmor tables')
    parser.add_argument('-c', '--config_attributes', default='attributes.yaml',
                        help='yaml file specifying metadata attributes to compare (will be created if it doesn\'t exist)')
    return parser.parse_args()


def main():

    args = parse_args()
    compare_versions = list(args.compare)

    # Output file names
    outfile_vars = 'diffs_by_variable.json'
    outfile_attr = 'diffs_by_attribute.json'
    outfile_missing = 'missing_variables.json'

    filepath = args.config_attributes
    if not os.path.exists(filepath):
        # If config file doesn't exist, create it
        config = {
            'compare_attributes': [
                'frequency',
                'modeling_realm',
                'standard_name',
                'units',
                'cell_methods',
                'cell_measures',
                'long_name',
                'comment',
                'dimensions',
                'out_name',
                'type',
                'positive',
            ],
            'repos': {
                'cmip6': {
                    'url': 'https://github.com/PCMDI/cmip6-cmor-tables',
                }
            }
        }
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            print('Wrote ' + filepath)

    # Load config file
    with open(filepath, 'r') as f:
        config = yaml.safe_load(f)
        compare_attributes = sorted(config['compare_attributes'], key=str.lower)
        repos = config['repos']

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
    diffs_by_name = OrderedDict()
    attr_diffs = set()
    region_change_map = OrderedDict()
    for var_name in all_var_names:
        missing = False
        region_case_change = False
        # allow for changes in case of region
        alt_var_name = generate_alternate_region_case_variable_name(var_name)
        for version in compare_versions:
            if var_name not in dreq_vars[version] and alt_var_name not in dreq_vars[version]:
                missing_vars[version].add(var_name)
                missing = True
        if missing:
            # Variable is not available in both versions
            continue
        ver0, ver1 = compare_versions

        try:
            var_info0 = dreq_vars[ver0][var_name]
        except KeyError:
            var_info0 = dreq_vars[ver0][alt_var_name]
            # first dreq version has the case change
            region_case_change = 1
        try:
            var_info1 = dreq_vars[ver1][var_name]
        except KeyError:
            var_info1 = dreq_vars[ver1][alt_var_name]
            # second dreq version has the case change
            region_case_change = 2

        # build dictionary catching region changes
        if region_case_change == 1:
            region_change_map[alt_var_name] = var_name
        elif region_case_change == 2:
            region_change_map[var_name] = alt_var_name

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
        if len(var_diff) > 0 and var_name not in region_change_map:
            diffs_by_name[var_name] = var_diff

    # Create another dict with the same info, but organized by attribute name instead of variable name
    diffs_by_attr = OrderedDict()
    attr_diffs = sorted(attr_diffs, key=str.lower)
    for attr in attr_diffs:
        diffs_by_attr[attr] = OrderedDict()
    for var_name, var_diff in diffs_by_name.items():
        for attr in var_diff:
            diffs_by_attr[attr][var_name] = var_diff[attr]

    # Show summary on stdout
    print(f'Total number of variables with differences: {len(diffs_by_name)}')
    if len(diffs_by_name) > 0:
        print(f'Number of variables with differences in each metadata attribute:')
        m = max([len(s) for s in attr_diffs])
        fmt = f'%-{m}s'
        for attr in attr_diffs:
            n = len(diffs_by_attr[attr])
            print(f'  {fmt % attr}  {n}')

    # Write output file summarizing missing variables
    # (i.e., differences in the variables list between the two compared versions)
    ver0, ver1 = compare_versions
    common_vars = set(dreq_vars[ver0].keys()).intersection(set(dreq_vars[ver1].keys()))
    missing = OrderedDict({
        f'Variables in {ver0} not found in {ver1}': OrderedDict({
            'no. of variables': len(missing_vars[ver1]),
            'Compound Name': sorted(missing_vars[ver1], key=str.lower),
        }),
        f'Variables in {ver1} not found in {ver0}': OrderedDict({
            'no. of variables': len(missing_vars[ver0]),
            'Compound Name': sorted(missing_vars[ver0], key=str.lower),
        }),
        f'Variables found in both {ver0} and {ver1}': OrderedDict({
            'no. of variables': len(common_vars),
            'Compound Name': sorted(common_vars, key=str.lower),
        })
    })
    out = OrderedDict({
        'Header': OrderedDict({
            'Description': f'Comparison of variable lists between {ver0} and {ver1}',
            f'No. of variables in {ver0}': len(dreq_vars[ver0]),
            f'No. of variables in {ver1}': len(dreq_vars[ver1]),
            'No. of variables in both': len(common_vars)
        }),
        'Missing': missing,
    })
    if region_change_map:
        print('Including region changes in missing_variables file')
        print('Note that JSON files will be organised based on compound names '
              'from the second JSON file provided on the command line')
        out[f'region case changes between {ver0} and {ver1}'] = region_change_map

    outfile = outfile_missing
    with open(outfile, 'w') as f:
        json.dump(out, f, indent=4)
        print('Wrote ' + outfile)

    # Write output files summarizing the differences between variables
    count_attr_diffs = OrderedDict()
    for attr in attr_diffs:
        count_attr_diffs[attr] = len(diffs_by_attr[attr])
    diff_count_summary = OrderedDict({
        f'No. of variables in {ver0}': len(dreq_vars[ver0]),
        f'No. of variables in {ver1}': len(dreq_vars[ver1]),
        'No. of variables with differences': len(diffs_by_name),
        'No. of variables with differences in each metadata attribute': count_attr_diffs
    })
    # Write output file organized by variable name
    out = OrderedDict({
        'Header': OrderedDict({
            'Description': f'Comparison of variable metadata between {ver0} and {ver1}, ' +
            'arranged by variable',
        }),
        'Compound Name': diffs_by_name,
    })
    out['Header'].update(diff_count_summary)
    outfile = outfile_vars
    with open(outfile, 'w') as f:
        json.dump(out, f, indent=4)
        print('Wrote ' + outfile)
    # Write output file organized by metadata attribute name
    out = OrderedDict({
        'Header': OrderedDict({
            'Description': f'Comparison of variable metadata between {ver0} and {ver1}, ' +
            'arranged by metadata attribute',
        }),
        'Attribute': diffs_by_attr,
    })
    out['Header'].update(diff_count_summary)
    outfile = outfile_attr
    with open(outfile, 'w') as f:
        json.dump(out, f, indent=4)
        print('Wrote ' + outfile)


def generate_alternate_region_case_variable_name(var_name):
    var_name_list = var_name.split('.')
    region = var_name_list[-1]
    if region.isupper():
        var_name_list[-1] = region.lower()
    elif region.islower():
        var_name_list[-1] = region.upper()
    alt_var_name = '.'.join(var_name_list)
    return alt_var_name


if __name__ == '__main__':
    main()
