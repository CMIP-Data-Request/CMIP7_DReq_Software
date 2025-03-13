#!/usr/bin/env python
'''
Helper utility to read data request "feedback" spreadsheet and produce a json file summarizing 
which Opportunities are supported, and which aren't. Also provides priority levels of variables
that are supported for each opportunity.

Produces a json file that can be read by scripts using the data request API to generate lists
of variables by experiment, given supported opportunities as input.
'''

import argparse
import os
import openpyxl as xp
from collections import OrderedDict
import json

description = '''
Command-line tool to read a spreadsheet (the "data request feedback" spreadsheet) that specifies 
which data request Opportunities are supported by a modelling centre.

Writes machine-readable summary to json file indicating:
1) whether each Opportunity is supported (yes/no)
2) the priority levels of variables to produce for each Opportunity
'''
parser = argparse.ArgumentParser(
    description=description, formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('filepath', type=str,
                    help=f'input spreadsheet indicating supported Opportunities')
parser.add_argument('-o', '--outfile', type=str,
                    default='opportunity_support.json', help='output file path (optional)')
args = parser.parse_args()

filepath = args.filepath
if not os.path.exists(filepath):
    raise Exception('Input file not found: ' + filepath)
workbook = xp.load_workbook(filepath, read_only=True, data_only=True)
print('Loaded spreadsheet: {}'.format(filepath))

sheet_name = 'Opportunities'
sheet = workbook[sheet_name]
use_columns = []
use_columns.append('CMIP7 production intent')


def sanitize_column_values(cols):
    if not isinstance(cols, list):
        raise TypeError('expected list of column values')
    for k, v in enumerate(cols):
        if isinstance(v, str):
            v = v.replace('\n', '')
        elif v is None:
            v = str(None)
        cols[k] = v


Opps_intention = {}
for k, row in enumerate(sheet.rows):
    cols = [c.value for c in row]
    if k == 0:
        column_names = cols
        if None in column_names:
            # Remove empty columns
            m = column_names.index(None)
            column_names = column_names[:m]
        assert all([isinstance(s, str)
                   for s in column_names]), 'column names should be string'
        sanitize_column_values(column_names)
        ncol = len(column_names)
    else:
        cols = cols[:ncol]
        sanitize_column_values(cols)
        d = dict(zip(column_names, cols))

        opp_title = d['Title of Opportunity']
        if opp_title in [None, 'None']:
            continue

        assert opp_title not in Opps_intention, 'Opportunity title is not unique: ' + opp_title
        opp_info = OrderedDict({key: d[key] for key in use_columns})
        Opps_intention[opp_title] = opp_info

        del d

Opps_intention = OrderedDict(
    {key: Opps_intention[key] for key in sorted(Opps_intention, key=str.lower)})

# Parse the production intent response strings
priority_levels = ['High', 'Medium', 'Low']
intention2maxpriority = {
    'Yes, HIGH(will aim to definitely produce)': 'Low',
    'Yes. MEDIUM (would like to produce, will depend on other factors)': 'Medium',
    'Yes, LOW(will only produce if time/volume allows)': 'High',
}
for opp_title, opp_info in Opps_intention.items():
    intent = opp_info['CMIP7 production intent'].strip()
    if intent.lower().startswith('yes'):
        p = intention2maxpriority[intent]
        m = priority_levels.index(p)
        opp_info['supporting'] = 'yes'
        opp_info['priority_levels'] = priority_levels[:m+1]
    else:
        opp_info['supporting'] = 'no'
        opp_info['priority_levels'] = []

supported_opps = sorted([opp_title for opp_title, opp_info in Opps_intention.items(
) if opp_info['supporting'] == 'yes'], key=str.lower)
unsupported_opps = sorted([opp_title for opp_title, opp_info in Opps_intention.items(
) if opp_info['supporting'] == 'no'], key=str.lower)

indent = ' '*2
n = len(unsupported_opps)
if n > 0:
    print(f'\nOpportunities that are NOT being supported ({n}):')
    for opp_title in unsupported_opps:
        print(indent + opp_title)
n = len(supported_opps)
if n > 0:
    print(
        f'\nOpportunities that ARE being supported ({n}) and their supported priority levels for variables:')
    for opp_title in supported_opps:
        print(indent + opp_title)
        opp_info = Opps_intention[opp_title]
        for key in sorted(opp_info, key=str.lower):
            if key == 'supporting':
                continue
            print(indent*2 + f'{key} : {opp_info[key]}')

# Write json file summarizing the info
Header = OrderedDict()
Header['Opportunities supported'] = len(supported_opps)
opp_count = OrderedDict()
Header['Opportunities supported, by priority level of variables'] = opp_count
for p in priority_levels:
    count = len([opp_info for opp_info in Opps_intention.values()
                if p in opp_info['priority_levels']])
    opp_count.update({
        p: count
    })
Header['Opportunities not supported'] = len(unsupported_opps)
Header['Input spreadsheet'] = filepath

output = OrderedDict()
output['Header'] = Header
output['Title of Opportunity'] = Opps_intention

outfile = args.outfile
with open(outfile, 'w') as f:
    json.dump(output, f, indent=4)
    print('\nWrote ' + outfile)
