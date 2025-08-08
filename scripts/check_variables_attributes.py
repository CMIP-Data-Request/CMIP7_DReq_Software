#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to check consistency of attributes for variables derived from the same physical parameter.
"""
from __future__ import division, print_function, unicode_literals, absolute_import

import sys
import os
import argparse
import tempfile
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from data_request_api.content.dump_transformation import get_transformed_content
from data_request_api.query.data_request import DataRequest
from data_request_api.utilities.logger import change_log_file, change_log_level, get_logger
from data_request_api.utilities.decorators import append_kwargs_from_config
from data_request_api.utilities.tools import write_json_output_file_content
from data_request_api.utilities.parser import append_arguments_to_parser


parser = argparse.ArgumentParser()
parser.add_argument("--version", default="latest_stable", help="Version to be used")
parser = append_arguments_to_parser(parser)
subparser = parser.add_mutually_exclusive_group()
subparser.add_argument("--output_dir", default=None, help="Dedicated output directory to use")
subparser.add_argument("--test", action="store_true", help="Is the launch a test? If so, launch in temporary directory.")
args = parser.parse_args()


@append_kwargs_from_config
def check_variables_attributes(version, output_dir, **kwargs):
	change_log_file(logfile=os.path.sep.join([output_dir, version, f"check_attributes_{kwargs['export']}.log"]))
	change_log_level("info")
	logger = get_logger()
	content = get_transformed_content(version=version, **kwargs)
	DR = DataRequest.from_separated_inputs(**content)

	rep = defaultdict(lambda: dict(cell_measures=set(), cell_methods=set(), cmip7_frequencies=set(), descriptions=set(),
	                               modelling_realms=set(), spatial_shapes=set(), temporal_shapes=set(), titles=set(),
	                               names=set()))
	for variable in DR.get_variables():
		physical_parameter = str(variable.physical_parameter.name)
		rep[physical_parameter]["cell_measures"] = \
			rep[physical_parameter]["cell_measures"] | set(str(elt.name) for elt in variable.cell_measures)
		rep[physical_parameter]["cell_methods"].add(str(variable.cell_methods.name))
		rep[physical_parameter]["cmip7_frequencies"].add(str(variable.cmip7_frequency.name))
		rep[physical_parameter]["descriptions"].add(str(variable.description))
		rep[physical_parameter]["modelling_realms"] = \
			rep[physical_parameter]["modelling_realms"] | set(str(elt.name) for elt in variable.modelling_realm)
		rep[physical_parameter]["spatial_shapes"].add(str(variable.spatial_shape.name))
		rep[physical_parameter]["temporal_shapes"].add(str(variable.temporal_shape.name))
		rep[physical_parameter]["titles"].add(str(variable.title))
		rep[physical_parameter]["names"].add(str(variable.name))

	for param in sorted(list(rep)):
		logger.info(f"Check consistency of variables derived from physical parameter {param}...")
		all_right = list()
		several = list()
		missing = list()
		overall_test = True
		for attr in sorted(list(rep[param])):
			val = rep[param][attr]
			val = sorted(list(val))
			test = True
			if "undef" in val or len(val) == 0:
				missing.append(attr)
				test = False
			if len(val) > 1:
				several.append(attr)
				test = False
			if test:
				all_right.append(attr)
			overall_test = overall_test and test
			rep[param][attr] = val
		if overall_test:
			logger.info(f"... all attributes are unique and no missing value found: {rep[param]}")
			del rep[param]
		else:
			logger.info(f"... the following attributes are fine: %s" % {attr: rep[param][attr] for attr in all_right})
			for attr in all_right:
				del rep[param][attr]
			if len(several) > 1:
				logger.info(f"... the following attributes have different values {several}.")
			if len(missing) > 1:
				logger.info(f"... the following attributes have missing values {missing}.")
			logger.info("... see output file.")

	write_json_output_file_content(os.path.sep.join([output_dir, version, f"check_attributes_{kwargs['export']}.json"]), content=rep)


kwargs = args.__dict__

if args.test:
	with tempfile.TemporaryDirectory() as output_dir:
		kwargs["output_dir"] = output_dir
		check_variables_attributes(**kwargs)
else:
	check_variables_attributes(**kwargs)
