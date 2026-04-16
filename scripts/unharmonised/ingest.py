#!/usr/bin/env python
'''
Ingest a yaml file that specifies a data request Opportunity
'''

# import os
import argparse
import json
import yaml

from collections import OrderedDict
from pydantic import BaseModel

import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq
from data_request_api.query.dreq_classes import (
    PRIORITY_LEVELS, format_attribute_name)


class ExperimentGroup(BaseModel):
    title: str
    experiments: list[str]

class VariableGroup(BaseModel):
    title: str
    priority_level: str
    justification: str = ''
    notes: str = ''
    variables: list[str]

class Opportunity(BaseModel):
    title: str
    mip: str
    description: str
    expected_impacts: str = ''
    justification_of_resources: str = ''
    experiment_groups: list[str]
    variable_groups: list[str]


def parse_args():
    ''' Parse command line arguments'''
    parser = argparse.ArgumentParser(description="Validate data request Opportunity specified by input yaml file")

    # Mandatory arguments
    parser.add_argument('input', 
                        help="Opportunity specifications (yaml file)")
    parser.add_argument('output', 
                        help="Validated Opportunity specifications (json file)")
    parser.add_argument('dreq_version', choices=dc.get_versions(), 
                        help="Data Request version used to validate input")

    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()
    filepath = args.input

    # Read setup file for new Opportunity
    # filepath = 'DR_Opportunity_template.yaml'
    with open(filepath, 'r') as f:
        opp = yaml.safe_load(f)

    # Validate any new variable or experiment groups
    sections = ['New Experiment Groups', 'New Variable Groups']
    for section in sections:
        for name,info in opp[section].items():
            opp[section][name] = {format_attribute_name(k):v for k,v in info.items()}
        match section:
            case 'New Experiment Groups':
                expt_groups = {name: ExperimentGroup(**info) for name,info in opp[section].items()}
            case 'New Variable Groups':
                variable_groups = {name: VariableGroup(**info) for name,info in opp[section].items()}
            case _:
                raise ValueError('Invalid section: ' + section)
        opp.pop(section)

    # Check priority levels in new Variable Groups are valid
    for vg_name, vg in variable_groups.items():
        if vg.priority_level.lower() not in PRIORITY_LEVELS:
            raise ValueError(f'Unknown Priority Level for Variable Group {vg_name}: {vg.priority_level}')

    # Check variable names in new Variable Groups are valid
    content = dc.load(args.dreq_version)
    all_var_info = dq.get_variables_metadata(content, args.dreq_version)
    cmip7_compound_names = set([var_info['cmip7_compound_name'] for var_info in all_var_info.values()])
    cmip6_compound_names = set([var_info['cmip6_compound_name'] for var_info in all_var_info.values()])
    # assert len(cmip7_compound_names) == len(cmip6_compound_names)
    for vg_name, vg in variable_groups.items():
        invalid_variables = []
        for var_name in vg.variables:
            # TODO: should user be forced to say whether using CMIP6 or CMIP7 variable names?
            if not (var_name in cmip7_compound_names or var_name in cmip6_compound_names):
                invalid_variables.append(var_name)
        if len(invalid_variables) > 0:
            msg = f'Found {len(invalid_variables)} invalid variables found in Variable Group {vg_name}:\n' \
                + '\n'.join(invalid_variables)
            raise ValueError(msg)

    # Validate Opportunity
    opp = {format_attribute_name(k):v for k,v in opp.items()}
    opp = Opportunity(**opp)

    # Write output file
    out = OrderedDict({
        'Header': OrderedDict({
            'Provenance': f'Validated Opportunity from input file {args.input}',
            'Data Request version used for validation': args.dreq_version,
        }),
        'Opportunity' : OrderedDict(opp),
        'New Experiment Groups': OrderedDict({name: OrderedDict(info) for name,info in expt_groups.items()}),
        'New Variable Groups': OrderedDict({name: OrderedDict(info) for name,info in variable_groups.items()})
    })
    with open(args.output, 'w') as f:
        json.dump(out, f, indent=4)
        print('Wrote ' + args.output)
