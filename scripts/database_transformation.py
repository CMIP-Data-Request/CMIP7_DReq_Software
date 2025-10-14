#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database transformation testing script
"""
from __future__ import division, print_function, unicode_literals, absolute_import

import os
import sys
import argparse
import tempfile


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import data_request_api.content.dreq_content as dc
from data_request_api.content.dump_transformation import get_transformed_content
from data_request_api.utilities.logger import change_log_file, change_log_level
from data_request_api.query.data_request import DataRequest
from data_request_api.utilities.parser import append_arguments_to_parser, check_bool
from data_request_api.utilities.decorators import append_kwargs_from_config


parser = argparse.ArgumentParser()
parser.add_argument("--version", default="latest_stable", help="Version to be used")
parser.add_argument("--force_variable_name", default=False, type=check_bool,
                    help="Should variable name be forced to variable_name value?")
parser = append_arguments_to_parser(parser)
subparser = parser.add_mutually_exclusive_group()
subparser.add_argument("--output_dir", default=None, help="Dedicated output directory to use")
subparser.add_argument("--test", action="store_true", help="Is the launch a test? If so, launch in temporary directory.")
args = parser.parse_args()


@append_kwargs_from_config
def database_transformation(version, output_dir, force_variable_name=False, **kwargs):
    change_log_file(default=True, logfile=kwargs["log_file"])
    change_log_level(kwargs["log_level"])
    # Download specified version of data request content (if not locally cached)
    versions = dc.retrieve(version, **kwargs)

    for (version, content) in versions.items():
        # Load the content
        content = get_transformed_content(version=version, output_dir=output_dir,
                                          force_variable_name=force_variable_name, **kwargs)

        # Test that the two files do not produce issues with the API
        DR = DataRequest.from_separated_inputs(**content)


kwargs = args.__dict__

if args.test:
    with tempfile.TemporaryDirectory() as output_dir:
        kwargs["output_dir"] = output_dir
        database_transformation(**kwargs)
else:
    database_transformation(**kwargs)
