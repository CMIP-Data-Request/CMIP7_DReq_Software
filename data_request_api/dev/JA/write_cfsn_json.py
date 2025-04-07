#!/usr/bin/env python
'''
This opens a json file created by get_variables_metadata.py and writes a new one
containing the same info but organized by CF standard name, as prpoposed in Karl
Taylor's draft branded variables paper.

Parking this code here in case useful later.
'''

import argparse
import json
from collections import OrderedDict

parser = argparse.ArgumentParser(
    description='Write json file of variables metadata organized by CF standard name'
)
parser.add_argument('infile', type=str,
                    help='json file with variables metadata produced by get_variables_metadata.py')
parser.add_argument('outfile', type=str,  # default='all_var_info_by_cfsn.json',
                    help='output json file')
args = parser.parse_args()


with open(args.infile, 'r') as f:
    out = json.load(f)
    all_var_info = out['Compound Name']
    use_dreq_version = out['Header']['dreq content version']

name_in_file = {
    'standard_name': 'CF Standard Name',
    'standard_name_proposed': 'CF Standard Name (Proposed)',
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

filepath = args.outfile
with open(filepath, 'w') as f:
    json.dump(out, f, indent=4)
    print(f'wrote {filepath} for {n} variables, dreq version = {use_dreq_version}')
