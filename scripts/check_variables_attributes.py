#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to check consistency of attributes for variables derived from the same physical parameter.
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
from data_request_api.stable.utilities.logger import change_log_file, change_log_level, get_logger
from data_request_api.stable.utilities.decorators import append_kwargs_from_config
from data_request_api.stable.utilities.tools import write_json_output_file_content


@append_kwargs_from_config
def check_variables_attributes(version="latest_stable", **kwargs):
	change_log_file(logfile="check_attributes.log")
	change_log_level("info")
	logger = get_logger()
	content = get_transformed_content(version=version, **kwargs)
	DR = DataRequest.from_separated_inputs(**content)

	rep = defaultdict(lambda: dict(cell_measures=set(), cell_methods=set(), frequencies=set(), descriptions=set(),
	                               modelling_realms=set(), spatial_shapes=set(), structure_titles=set(),
	                               temporal_shapes=set(), titles=set(), names=set()))
	for variable in DR.get_variables():
		physical_parameter = str(variable.physical_parameter.name)
		rep[physical_parameter]["cell_measures"] = \
			rep[physical_parameter]["cell_measures"] | set(str(elt.name) for elt in variable.cell_measures)
		rep[physical_parameter]["cell_methods"].add(str(variable.cell_methods.name))
		rep[physical_parameter]["frequencies"].add(str(variable.cmip7_frequency.name))
		rep[physical_parameter]["descriptions"].add(str(variable.description))
		rep[physical_parameter]["modelling_realms"] = \
			rep[physical_parameter]["modelling_realms"] | set(str(elt.name) for elt in variable.modelling_realm)
		rep[physical_parameter]["spatial_shapes"].add(str(variable.spatial_shape.name))
		rep[physical_parameter]["structure_titles"] = \
			rep[physical_parameter]["structure_titles"] | set(str(elt.name) for elt in variable.structure_title)
		rep[physical_parameter]["temporal_shapes"].add(str(variable.temporal_shape.name))
		rep[physical_parameter]["titles"].add(str(variable.title))
		rep[physical_parameter]["names"].add(str(variable.name))

	for param in sorted(list(rep)):
		logger.info(f"Check consistency of variables derived from physical parameter {param}...")
		all_right = list()
		several = list()
		missing = list()
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
			rep[param][attr] = val
		if test:
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

	write_json_output_file_content("check_attributes.txt", content=rep)


if __name__ == "__main__":
	check_variables_attributes()
