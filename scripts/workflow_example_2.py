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
    python workflow_example2.py

will load the data request content and save a json file of requested variables in the current dir.
To run interactively in ipython:

    run -i workflow_example2.py
"""
from __future__ import division, print_function, unicode_literals, absolute_import

import pprint
import sys
import os
import argparse
import tempfile
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from data_request_api.content.dump_transformation import get_transformed_content
from data_request_api.query.data_request import DataRequest
from data_request_api.utilities.logger import change_log_file, change_log_level, get_logger
from data_request_api.utilities.parser import append_arguments_to_parser
from data_request_api.utilities.decorators import append_kwargs_from_config


parser = argparse.ArgumentParser()
parser.add_argument("--version", default="latest_stable", help="Version to be used")
parser = append_arguments_to_parser(parser)
subparser = parser.add_mutually_exclusive_group()
subparser.add_argument("--output_dir", default=None, help="Dedicated output directory to use")
subparser.add_argument("--test", action="store_true", help="Is the launch a test? If so, launch in temporary directory.")
args = parser.parse_args()


@append_kwargs_from_config
def get_information_from_data_request(version, output_dir, **kwargs):
    change_log_file(default=True, logfile=kwargs["log_file"])
    change_log_level(kwargs["log_level"])
    logger = get_logger()
    ### Step 1: Get the data request content
    content_dict = get_transformed_content(version=version, output_dir=output_dir, **kwargs)
    DR = DataRequest.from_separated_inputs(**content_dict)

    ### Step 2: Get information from the DR
    # -> Print DR content
    logger.info("Print Data Request Content")
    print(DR)
    # -> Print an experiment group content
    logger.info("Print one experiment group info")
    print(DR.get_experiment_groups()[0])
    # -> Get all variables' id associated with an opportunity
    logger.info("Get all variables linked to an opportunity")
    print(DR.find_variables_per_opportunity(DR.get_opportunities()[0]))
    # -> Get all experiments' id associated with an opportunity
    logger.info("Get all experiments linked to an opportunity")
    print(DR.find_experiments_per_opportunity(DR.get_opportunities()[0]))
    # -> Get information about the shapes of the variables of all variables groups
    logger.info("Print physical parameters required per spatial shapes, frequency and temporal shape")
    rep = defaultdict(lambda: defaultdict(set))
    for elt in DR.get_variable_groups():
        for var in elt.get_variables():
            for key in ["spatial_shape", "cmip7_frequency", "temporal_shape", "physical_parameter"]:
                rep[elt.id][key].add(var.get(key).name)
    pprint.pprint(rep)

    logger.info("Print frequency, spatial shape and temporal shape per realm and physical parameter")
    rep = defaultdict(lambda: defaultdict(set))
    for elt in DR.get_variable_groups():
        for var in elt.get_variables():
            realm = set([elt.name for elt in var.modelling_realm])
            for realm in realm:
                rep[realm][var.physical_parameter.name].add(f"{var.cmip7_frequency.name}//"
                                                            f"{var.spatial_shape.name}//"
                                                            f"{var.temporal_shape.name}")
    pprint.pprint(rep)

    logger.info("Print experiments linked to the 'Atmosphere' realm")
    print(DR.find_experiments_per_theme("Atmosphere"))

    if output_dir is None:
        output_dir = "."

    logger.info("Create table of opportunities per themes")
    DR.export_summary("opportunities", "data_request_themes", os.sep.join([output_dir, "op_per_th.csv"]))
    logger.info("Create table of variables per opportunities")
    DR.export_summary("variables", "opportunities", os.sep.join([output_dir, "var_per_op.csv"]))
    DR.export_summary(lines_data="variables", columns_data="opportunities",
                      filtering_requests={"max_priority_level": "High"},
                      sorting_line=["physical_parameter", "frequency", "name"],
                      output_file=os.sep.join([output_dir, "var_per_op_regrouped_filtered.csv"]), regroup=True)
    DR.export_summary(lines_data="variables", columns_data="opportunities",
                      filtering_requests={"max_priority_level": "High"},
                      sorting_line=["physical_parameter", "frequency", "name"],
                      output_file=os.sep.join([output_dir, "var_per_op_filtered.csv"]))
    logger.info("Create table of variables per experiments")
    DR.export_summary(lines_data="variables", columns_data="experiments",
                      sorting_line=["physical_parameter", "frequency", "name"],
                      filtering_requests={"max_priority_level": "High"},
                      output_file=os.sep.join([output_dir, "var_per_exp_regrouped_filtered.csv"]), regroup=True)
    DR.export_summary(lines_data="variables", columns_data="experiments",
                      sorting_line=["physical_parameter", "frequency", "name"],
                      filtering_requests={"max_priority_level": "High"},
                      output_file=os.sep.join([output_dir, "var_per_exp_filtered.csv"]))
    logger.info("Create table of experiments per opportunities")
    DR.export_summary("experiments", "opportunities", os.sep.join([output_dir, "exp_per_op.csv"]))
    DR.export_summary(lines_data="experiments", columns_data="opportunities",
                      sorting_line=["physical_parameter", "frequency", "name"],
                      filtering_requests={"max_priority_level": "High"},
                      output_file=os.sep.join([output_dir, "exp_per_op_regrouped_filtered.csv"]), regroup=True)
    DR.export_summary(lines_data="experiments", columns_data="opportunities",
                      sorting_line=["physical_parameter", "frequency", "name"],
                      filtering_requests={"max_priority_level": "High"},
                      output_file=os.sep.join([output_dir, "exp_per_op_filtered.csv"]))
    logger.info("Create table of variables per spatial shapes")
    DR.export_summary("variables", "spatial_shape", os.sep.join([output_dir, "var_per_spsh.csv"]))
    DR.export_summary("variables", "variable_group", os.sep.join([output_dir, "var_per_vargrp.csv"]))
    DR.export_summary("experiments", "experiment_group", os.sep.join([output_dir, "exp_per_expgrp.csv"]))
    DR.export_summary("experiment_group", "opportunities", os.sep.join([output_dir, "expgrp_per_op.csv"]))
    DR.export_summary("variable_group", "opportunities", os.sep.join([output_dir, "vargrp_per_op.csv"]))
    DR.export_summary("variable_group", "priority_level", os.sep.join([output_dir, "vargrp_per_prio.csv"]))
    DR.export_summary("opportunities", "time_subsets", os.sep.join([output_dir, "op_per_timsub.csv"]))
    logger.info("Export opportunities info")
    DR.export_data("opportunities", os.sep.join([output_dir, "op.csv"]),
                   export_columns_request=["name", "lead_theme", "description"])
    DR.export_data("variables", os.sep.join([output_dir, "var.csv"]), add_id=False,
                   export_columns_request=["name", "cmip6_compound_name", "title"])


kwargs = args.__dict__

if args.test:
    with tempfile.TemporaryDirectory() as output_dir:
        kwargs["output_dir"] = output_dir
        get_information_from_data_request(**kwargs)
else:
    get_information_from_data_request(**kwargs)
