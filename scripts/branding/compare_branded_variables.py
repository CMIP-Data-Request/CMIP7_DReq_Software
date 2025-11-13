#!/usr/bin/env python
'''
Group variables together that share the same branded variable name,
and check for consistency in their metadata attributes.
'''

import argparse
import json
import os
import yaml

from collections import defaultdict, OrderedDict


def parse_args():

    parser = argparse.ArgumentParser(
        description='Compare metadata between data request variables sharing the same branded name'
    )

    parser.add_argument('input_file', help='JSON file containing data request variables metadata \
                        (produced by get_variables_metadata)')
    parser.add_argument('output_file', help='name of output JSON file summarizing metadata differences')

    parser.add_argument('-c', '--config_attributes', default='branded_variable_attributes.yaml',
                        help='yaml file specifying metadata attributes to compare (will be created if it \
                            doesn\'t exist)')

    return parser.parse_args()


def main():

    args = parse_args()

    # Get info from config file
    filepath = args.config_attributes
    if not os.path.exists(filepath):
        # If config file doesn't exist, create it
        config = {
            'compare_attributes': [
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
        }
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            print('Wrote ' + filepath)
    # Load config file
    with open(filepath, 'r') as f:
        config = yaml.safe_load(f)
        # compare_attributes = sorted(config['compare_attributes'], key=str.lower)
        compare_attributes = config['compare_attributes']
        if len(compare_attributes) != len(set(compare_attributes)):
            raise ValueError(f'compare_attributes had duplicate entries: {compare_attributes}')

    # Load file containing variables metadata
    filepath = args.input_file
    with open(filepath, 'r') as f:
        d = json.load(f)
        dreq_vars = d['Compound Name']
        dreq_header = d['Header']
        del d
        print('Loaded ' + filepath)

    replace_ismip_grids = False
    # replace_ismip_grids = True
    if replace_ismip_grids:
        # For purpose of comparison, replace xgre,ygre,xant,yant with lon,lat
        print('* replacing ISMIP grids! *')
        rename_dim = {
            # 'xgre': 'longitude',
            # 'xant': 'longitude',
            # 'ygre': 'latitude',
            # 'yant': 'latitude',

            'latitude longitude': 'longitude latitude', # fix glitch in v1.2.2.1betarc
        }
        for var_info in dreq_vars.values():
            for dim, new_dim in rename_dim.items():
                if dim in var_info['dimensions']:
                    assert var_info['dimensions'].count(dim) == 1
                    var_info['dimensions'] = var_info['dimensions'].replace(dim, new_dim)

    # Check attributes exist
    var_info = next(iter(dreq_vars.values()))
    # (assuming here all var_info dicts have the same set of attributes)
    for attr in compare_attributes:
        if attr not in var_info:
            raise ValueError(f'Metadata attribute "{attr}" not found in data request variables')
    
    # Ensure that we don't check attributes that are allowed to differ by data request variable
    # for the same branded variable name. These are attributes specified by the data request,
    # not in the variable register.
    dreq_attributes = ['frequency', 'region']
    dreq_attributes.append('cmip7_compound_name')
    dreq_attributes.append('cmip6_compound_name') # it's useful to see the CMIP6-era names in the output summary

    compare_attributes = [s for s in compare_attributes if s not in dreq_attributes]

    print(f'The following {len(compare_attributes)} metadata attributes will be compared:')
    for s in compare_attributes:
        print(' '*4 + s)

    # Group variables by branded name
    branded_vars = defaultdict(list)
    for var_info in dreq_vars.values():
        branded_variable_name = var_info['branded_variable_name']

        primary_realm = var_info['modeling_realm'].split()[0]
        # branded_variable_name += '___' + primary_realm

        region = var_info['region']
        # branded_variable_name += '___' + region

        # realm = var_info['modeling_realm']
        # assert var_info['cmip7_compound_name'].startswith(realm)

        branded_vars[branded_variable_name].append(var_info)
    print(f'Found {len(branded_vars)} branded variables from {len(dreq_vars)} data request variables')

    testing = False
    if testing:
        # write out json file of variables grouped by their branded name
        out = OrderedDict()
        for bv_name in sorted(branded_vars.keys(), key=str.lower):
            out[bv_name] = branded_vars[bv_name]
        outfile = 'bn_tmp.json'
        with open(outfile, 'w') as f:
            json.dump(out, f, indent=4)
            print('wrote ' + outfile)

    # For each branded variable, gather all values for each attribute being compared.
    # If more than one value is present for an attribute, then the data request variables do not
    # have consistent values of that attribute (for that particular branded variable).
    comparison = OrderedDict()
    count_diffs = OrderedDict({attr: 0 for attr in compare_attributes})
    affected_dreq_vars = set()
    for bv_name in sorted(branded_vars.keys(), key=str.lower):
        var_list = branded_vars[bv_name]
        var_diff = OrderedDict()
        # Find out if there are any differences
        attributes_with_differences = []
        for attr in compare_attributes:
            # var_diff[attr] = list(set([var_info[attr] for var_info in var_list]))
            var_diff[attr] = set([var_info[attr] for var_info in var_list])
            if len(var_diff[attr]) > 1:
                attributes_with_differences.append(attr)
                count_diffs[attr] += 1
        if len(attributes_with_differences) > 0:
            # One or more differences were found
            show_attributes = []
            show_attributes += list(dreq_attributes) # also dispaly the diffs in these attributes (these ones SHOULD differ)
            # show_attributes += [attr for attr in compare_attributes if len(var_diff[attr]) > 1]
            show_attributes += attributes_with_differences

            show_diffs_as = 'list'
            show_diffs_as = 'dict'

            if show_diffs_as == 'list':
                # Show differences by attribute as lists of attribute values
                var_diff = OrderedDict()
                for attr in show_attributes:
                    var_diff[attr] = [var_info[attr] for var_info in var_list]

            elif show_diffs_as == 'dict':
                # Dict of attribute:value pairs, including only attributes with differences
                var_diff = []
                for var_info in var_list:
                    var_diff.append(OrderedDict({attr: var_info[attr] for attr in show_attributes}))

            comparison[bv_name] = OrderedDict({
                'no. of data request variables': len(var_list),
                'attributes with differences': var_diff,
            })

            for var_info in var_list:
                var_name = var_info['cmip6_compound_name']
                assert var_name not in affected_dreq_vars, f'{var_name} has appeared in the list for more than one branded variable!'
                affected_dreq_vars.add(var_name)

            # print(bv_name)

    print(f'{len(comparison)} branded variables have differences in their data request variables')
    print(f'This affects {len(affected_dreq_vars)} data request variables')


    # Write results to json file
    outfile = args.output_file
    out = OrderedDict({
        'Header': OrderedDict({
            'Description': 'Consistency check on branded variable metadata attributes',
            'no. of data request variables': len(dreq_vars),
            'no. of branded variables': len(branded_vars),
            'no. of branded variables with attribute differences': len(comparison),
            'attributes compared': compare_attributes,
            'no. of branded variables with differences in each attribute': count_diffs,
        }),
        'Comparison': comparison,
    })
    add_header_info = ['dreq content version', 'dreq content file', 'dreq content sha256 hash']
    for s in add_header_info:
        out['Header'][s] = dreq_header[s]
    with open(outfile, 'w') as f:
        json.dump(out, f, indent=4)
        print('Wrote ' + outfile)


    compare_to_dreq_lists = not True
    if compare_to_dreq_lists:
        print('\nComparing affected DR variables to different variable sets')
        
        compare = []
        compare.append(('BCV.json', 'amip'))
        compare.append(('hist.json', 'historical'))
        compare.append(('pictl.json', 'piControl'))
        # compare.append(('hist.json', 'esm-hist'))
        # compare.append(('pictl.json', 'esm-piControl'))

        summary = OrderedDict()

        for filename,expt in compare:
            with open(filename, 'r') as f:
                d = json.load(f)
                request = d['experiment'][expt]
                print('\nLoaded ' + filename)
                del d
            # print(request)
            affected = OrderedDict()
            all_vars = set()
            for priority, var_list in request.items():
                vars = set(var_list)
                if len(vars) == 0:
                    continue
                assert len(vars) == len(var_list)
                affected[priority] = vars.intersection(affected_dreq_vars)
                all_vars.update(vars)
            print(f'No. of DR variables affected by priority level for {expt} experiment:')
            count = 0
            for priority in affected:
                n = len(affected[priority])
                print(f'  {priority}: {n}')
                count += n
            print(f'Total DR variables affected: {count}')
            if affected_dreq_vars.issubset(all_vars):
                print(f'All {len(affected_dreq_vars)} affected DR variables are requested by this experiment')

            for priority in affected:
                affected[priority] = sorted(affected[priority], key=str.lower)
            summary[f'{filename}, {expt}'] = affected

        filename = 'compare_to_dreq_lists.json'
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=4)
            print('\nWrote ' + filename)



if __name__ == '__main__':
    main()
