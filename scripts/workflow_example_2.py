#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Other example script for basic use of CMIP7 data request content

Getting started
---------------
First create an environment with the required dependencies:

    conda env create -n my_dreq_env --file env.yml

(replacing my_dreq_env with your preferred env name). Then activate it and run the script:

    conda activate my_dreq_env
    python workflow_example.py

will load the data request content and save a json file of requested variables in the current dir.
To run interactively in ipython:

    run -i workflow_example.py
"""
from __future__ import division, print_function, unicode_literals, absolute_import

import pprint
import sys
import os
import argparse
import tempfile
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from data_request_api.stable.content.dump_transformation import get_transformed_content
from data_request_api.stable.query.data_request import DataRequest
from data_request_api.stable.utilities.logger import change_log_file, change_log_level


parser = argparse.ArgumentParser()
parser.add_argument("--log_level", default="info", help="Log level")
parser.add_argument("--dreq_version", default="latest_stable", help="Version to be used")
parser.add_argument("--dreq_export_version", default="release", help="Export version to be used")
parser.add_argument("--use_consolidation", default=False, help="Should content consolidation be used?")
parser.add_argument("--output_dir", choices=["default", "test", "customed"], default="default",
                    help="Output directory management")
parser.add_argument("--output_dir_customed", default=None, help="Customed output directory to be used")
args = parser.parse_args()


def get_information_from_data_request(dreq_version, dreq_export_version, use_consolidation, output_dir):
    ### Step 1: Get the data request content
    DR_content, VS_content = get_transformed_content(version=dreq_version, export_version=dreq_export_version,
                                                     use_consolidation=use_consolidation, output_dir=output_dir)
    DR = DataRequest.from_separated_inputs(DR_input=DR_content, VS_input=VS_content)

    ### Step 2: Get information from the DR
    # -> Print DR content
    print(DR)
    # -> Print an experiment group content
    print(DR.get_experiment_groups()[0])
    # -> Get all variables' id associated with an opportunity
    print(DR.find_variables_per_opportunity(DR.get_opportunities()[0]))
    # -> Get all experiments' id associated with an opportunity
    print(DR.find_experiments_per_opportunity(DR.get_opportunities()[0]))
    # -> Get information about the shapes of the variables of all variables groups
    rep = defaultdict(lambda: defaultdict(set))
    for elt in DR.get_variable_groups():
        for var in elt.get_variables():
            for key in ["spatial_shape", "cmip7_frequency", "temporal_shape", "physical_parameter"]:
                rep[elt.id][key].add(var.get(key).name)
    pprint.pprint(rep)

    rep = defaultdict(lambda: defaultdict(set))
    for elt in DR.get_variable_groups():
        for var in elt.get_variables():
            realm = set([elt.name for elt in var.modelling_realm])
            for realm in realm:
                rep[realm][var.physical_parameter.name].add(f"{var.cmip7_frequency.name} // {var.spatial_shape.name} // {var.temporal_shape.name}")
    pprint.pprint(rep)

    print(DR.find_experiments_per_theme("Atmosphere"))

    if output_dir is None:
        output_dir = "."

    DR.export_summary("opportunities", "data_request_themes", os.sep.join([output_dir, "op_per_th.csv"]))
    DR.export_summary("variables", "opportunities", os.sep.join([output_dir, "var_per_op.csv"]))
    DR.export_summary("experiments", "opportunities", os.sep.join([output_dir, "exp_per_op.csv"]))
    DR.export_summary("variables", "spatial_shape", os.sep.join([output_dir, "var_per_spsh.csv"]))
    DR.export_data("opportunities", os.sep.join([output_dir, "op.csv"]),
                   export_columns_request=["name", "lead_theme", "description"])


# Set up log file (default to stdout) and log level
change_log_file(default=True)
change_log_level(args.log_level)

if args.output_dir in ["default", "customed"]:
    if args.output_dir in ["default", ]:
        output_dir = None
    elif args.output_dir_customed is not None:
        output_dir = args.output_dir_customed
    else:
        raise ValueError("If --output_dir='customed', --output_dir_customed should be defined with a not None value.")

    get_information_from_data_request(output_dir=output_dir, dreq_version=args.dreq_version,
                                      dreq_export_version=args.dreq_export_version,
                                      use_consolidation=args.use_consolidation)
elif args.output_dir in ["test", ]:
    with tempfile.TemporaryDirectory() as output_dir:
        get_information_from_data_request(output_dir=output_dir, dreq_version=args.dreq_version,
                                          dreq_export_version=args.dreq_export_version,
                                          use_consolidation=args.use_consolidation)
