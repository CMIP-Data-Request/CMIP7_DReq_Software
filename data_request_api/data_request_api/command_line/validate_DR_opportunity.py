#!/usr/bin/env python
'''
Ingest a yaml file that specifies a data request Opportunity
'''

import argparse
import json
import os
import yaml

from collections import OrderedDict
from pydantic import BaseModel

import esgvoc.api as ev

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

def main():

    args = parse_args()
    input_file = args.input
    output_file = args.output
    dreq_version = args.dreq_version
    project = 'cmip7'

    # Read setup file for new Opportunity
    with open(input_file, 'r') as f:
        opp = yaml.safe_load(f)

    # Get DR content used to validate the input
    dreq_content = dc.load(dreq_version)
    base = dq._get_base_dreq_tables(dreq_content, dreq_version, purpose='request')
    dreq_var_info = dq.get_variables_metadata(base, dreq_version)
    cmip7_compound_names = set([var_info['cmip7_compound_name'] for var_info in dreq_var_info.values()])
    cmip6_compound_names = set([var_info['cmip6_compound_name'] for var_info in dreq_var_info.values()])
    dreq_expt_group_names = set(rec.name for rec in base['Experiment Group'].records.values())
    dreq_var_group_names = set(rec.name for rec in base['Variable Group'].records.values())

    # Use Opportunity pydantic model to validate the input
    opp = {format_attribute_name(k):v for k,v in opp.items()}
    opp = Opportunity(**opp)

    # Check full Variable Group and Experiment Group lists either
    #   1. already exist in the DR, or
    #   2. are defined as new by a template in the appropriate folder.
    new_eg_names = [eg_name for eg_name in opp.experiment_groups if eg_name not in dreq_expt_group_names]
    new_vg_names  = [vg_name for vg_name in opp.variable_groups   if vg_name not in dreq_var_group_names]

    # Get info on any new experiment groups from yaml files in the Experiment_Group folder
    new_expt_groups = {}
    for eg_name in new_eg_names:
        eg_input_file = os.path.join('Experiment_Group', f'{eg_name}.yaml')
        with open(eg_input_file, 'r') as f:
            info = yaml.safe_load(f)
        info = {format_attribute_name(k):v for k,v in info.items()}
        assert eg_name not in new_expt_groups, f'duplicate new experiment group: {eg_name}'
        new_expt_groups[eg_name] = ExperimentGroup(**info)
    del new_eg_names

    # Get info on any new variable groups from yaml files in the Variable_Group folder
    new_var_groups = {}
    for vg_name in new_vg_names:
        vg_input_file = os.path.join('Variable_Group', f'{vg_name}.yaml')
        with open(vg_input_file, 'r') as f:
            info = yaml.safe_load(f)
        info = {format_attribute_name(k):v for k,v in info.items()}
        assert vg_name not in new_var_groups, f'duplicate new variable group: {vg_name}'
        new_var_groups[vg_name] = VariableGroup(**info)
    del new_vg_names

    # Check priority levels in new Variable Groups are valid
    for vg_name, vg in new_var_groups.items():
        if vg.priority_level.lower() == 'core':
            raise ValueError(f'Priority Level "Core" is reserved for Baseline Climate Variables')
        elif vg.priority_level.lower() not in PRIORITY_LEVELS:
            raise ValueError(f'Unknown Priority Level for Variable Group {vg_name}: {vg.priority_level}')

    # Check that the variable names in new Variable Groups are valid
    for vg_name, vg in new_var_groups.items():
        invalid_variables = []
        for var_name in vg.variables:
            # TODO: should user be forced to say whether using CMIP6 or CMIP7 variable names? Assume CMIP7 names?
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
    cv_expts = ev.get_all_terms_in_collection(project_id=project, collection_id='experiment')
    cv_expt_names = set([cv_info.drs_name for cv_info in cv_expts])
    for eg_name, eg in new_expt_groups.items():
        eg_expt_names = set(eg.experiments)
        if not eg_expt_names.issubset(cv_expt_names):
            invalid_expt_names = eg_expt_names.difference(cv_expt_names)
            msg = [f'Found {len(invalid_expt_names)} unknown experiments in experiment group "{eg_name}":']
            msg += sorted([f'  {s}' for s in invalid_expt_names])
            msg.append(f'Have these experiments been registered in the CVs for project={project}?')
            raise ValueError('\n'.join(msg))

    # Write output file
    out = OrderedDict({
        'Header': OrderedDict({
            'Provenance': f'Validated Opportunity from input file {input_file}',
            'Data Request version used for validation': dreq_version,
        }),
        'Opportunity' : OrderedDict(opp),
        'Experiment Group': OrderedDict({name: OrderedDict(info) for name,info in new_expt_groups.items()}),
        'Variable Group': OrderedDict({name: OrderedDict(info) for name,info in new_var_groups.items()})
    })
    with open(output_file, 'w') as f:
        json.dump(out, f, indent=4)
        print('Wrote ' + output_file)

if __name__ == '__main__':
    main()
