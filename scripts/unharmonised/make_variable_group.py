#!/usr/bin/env python
'''
Make variable group yaml file from json or csv input
'''

import argparse
import json
import yaml


def parse_args():
    ''' Parse command line arguments'''
    parser = argparse.ArgumentParser(description="Create variable group yaml file from json or csv input")

    # Mandatory arguments
    parser.add_argument('input', 
                        help="Variables list (json or csv)")
    parser.add_argument('output', 
                        help="Variable group filename, example: Variable_Group/new_variable_group.yaml")

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    filepath = args.input
    if filepath.endswith('.json'):
        with open(filepath, 'r') as f:
            vars = json.load(f)['Compound Name']
    elif filepath.endswith('.csv'):
        # TODO: support csv input
        raise ValueError('add csv support')

    content = {
        'Title': 'Short descriptive title of the Variable Group',
        'Priority Level': 'Set to "High", "Medium", or "Low" (not case sensitive)',
        'Justification': '(Optional) Explanation of why these variables are important.',
        'Notes': '(Optional) Any additional comments about the variable group.',
        'Variables': [],  # list of requested variable names
    }

    # TODO: validate variables metadata against DR or CVs

    content['Variables'] = sorted(vars.keys(), key=str.lower)

    filepath = args.output
    with open(filepath, 'w') as f:
        yaml.dump(content, f, sort_keys=False, indent=2)
        print(f'Wrote {filepath}')
