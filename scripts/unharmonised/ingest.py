#!/usr/bin/env python
'''
Ingest a yaml file that specifies a data request Opportunity
'''

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
    input_file = args.input
    output_file = args.output
    dreq_version = args.dreq_version

    # Read setup file for new Opportunity
    with open(input_file, 'r') as f:
        opp = yaml.safe_load(f)

    # Validate any new variable or experiment groups
    sections = ['New Experiment Groups', 'New Variable Groups']
    for section in sections:
        for name,info in opp[section].items():
            opp[section][name] = {format_attribute_name(k):v for k,v in info.items()}
        match section:
            case 'New Experiment Groups':
                new_expt_groups = {name: ExperimentGroup(**info) for name,info in opp[section].items()}
            case 'New Variable Groups':
                new_var_groups = {name: VariableGroup(**info) for name,info in opp[section].items()}
            case _:
                raise ValueError('Invalid section: ' + section)
        opp.pop(section)

    # Check priority levels in new Variable Groups are valid
    for vg_name, vg in new_var_groups.items():
        if vg.priority_level.lower() not in PRIORITY_LEVELS:
            raise ValueError(f'Unknown Priority Level for Variable Group {vg_name}: {vg.priority_level}')

    # Get DR content to use in further validating the input
    dreq_content = dc.load(dreq_version)
    base = dq._get_base_dreq_tables(dreq_content, dreq_version, purpose='request')
    dreq_var_info = dq.get_variables_metadata(base, dreq_version)
    cmip7_compound_names = set([var_info['cmip7_compound_name'] for var_info in dreq_var_info.values()])
    cmip6_compound_names = set([var_info['cmip6_compound_name'] for var_info in dreq_var_info.values()])
    dreq_expt_group_names = set(rec.name for rec in base['Experiment Group'].records.values())
    dreq_var_group_names = set(rec.name for rec in base['Variable Group'].records.values())

    # Check new Variable Group names don't conflict with any already in the DR
    for vg_name in new_var_groups:
        if vg_name in dreq_var_group_names:
            raise ValueError(f'Variable Group already exists in DR {dreq_version}: {vg_name}')

    # Check variable names in new Variable Groups are valid
    for vg_name, vg in new_var_groups.items():
        invalid_variables = []
        for var_name in vg.variables:
            # TODO: should user be forced to say whether using CMIP6 or CMIP7 variable names?
            # TODO: if new variables are defined (beyond those in AFT DR) then need to add these here as valid names
            if not (var_name in cmip7_compound_names or var_name in cmip6_compound_names):
                invalid_variables.append(var_name)
        if len(invalid_variables) > 0:
            msg = f'Found {len(invalid_variables)} invalid variables found in Variable Group {vg_name}:\n' \
                + '\n'.join(invalid_variables)
            raise ValueError(msg)

    # Check new Experiment Group names don't conflict with any already in the DR
    for eg_name in new_expt_groups:
        if eg_name in dreq_expt_group_names:
            raise ValueError(f'Experiment Group already exists in DR {dreq_version}: {eg_name}')

    # Validate experiments against CVs
    # TODO: get valid CMIP7 experiments using esgvoc
    # (cannot rely on AFT DR list since community MIPs will define new experiments)

    # Validate Opportunity
    opp = {format_attribute_name(k):v for k,v in opp.items()}
    opp = Opportunity(**opp)

    # Check full Variable Group and Experiment Group lists either defined as new or existing in the DR
    all_expt_group_names = dreq_expt_group_names.union(new_expt_groups.keys())
    all_var_group_names = dreq_var_group_names.union(new_var_groups.keys())
    for eg_name in opp.experiment_groups:
        if eg_name not in all_expt_group_names:
            raise ValueError(f'Experiment Group {eg_name} has not been newly defined and does not already exist in DR {dreq_version}')
    for vg_name in opp.variable_groups:
        if vg_name not in all_var_group_names:
            raise ValueError(f'Variable Group {vg_name} has not been newly defined and does not already exist in DR {dreq_version}')

    # Write output file
    out = OrderedDict({
        'Header': OrderedDict({
            'Provenance': f'Validated Opportunity from input file {input_file}',
            'Data Request version used for validation': dreq_version,
        }),
        'Opportunity' : OrderedDict(opp),
        'New Experiment Groups': OrderedDict({name: OrderedDict(info) for name,info in new_expt_groups.items()}),
        'New Variable Groups': OrderedDict({name: OrderedDict(info) for name,info in new_var_groups.items()})
    })
    with open(output_file, 'w') as f:
        json.dump(out, f, indent=4)
        print('Wrote ' + output_file)
