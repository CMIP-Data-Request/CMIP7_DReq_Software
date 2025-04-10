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


import data_request_api.stable.content.dreq_content as dc
from data_request_api.stable.content.dump_transformation import transform_content
from data_request_api.stable.utilities.tools import write_json_output_file_content
from data_request_api.stable.utilities.logger import change_log_file, change_log_level
from data_request_api.stable.query.data_request import DataRequest
from data_request_api.stable.utilities.parser import append_arguments_to_parser
from data_request_api.stable.utilities.decorators import append_kwargs_from_config


parser = argparse.ArgumentParser()
parser.add_argument("--version", default="latest_stable", help="Version to be used")
parser = append_arguments_to_parser(parser)
subparser = parser.add_mutually_exclusive_group()
subparser.add_argument("--output_dir", default=None, help="Dedicated output directory to use")
subparser.add_argument("--test", action="store_true", help="Is the launch a test? If so, launch in temporary directory.")
args = parser.parse_args()


@append_kwargs_from_config
def database_transformation(version, output_dir, **kwargs):
    change_log_file(default=True, logfile=kwargs["log_file"])
    change_log_level(kwargs["log_level"])
    # Download specified version of data request content (if not locally cached)
    versions = dc.retrieve(version, **kwargs)

    for (version, content) in versions.items():
        # Load the content
        content = dc.load(version, **kwargs)

        # Transform content into DR and VS
        data_request, vocabulary_server = transform_content(content, version=version)

        # Write down the two files
        DR_file = os.path.sep.join([output_dir, version, f"DR_{kwargs['export']}_content.json"])
        VS_file = os.path.sep.join([output_dir, version, f"VS_{kwargs['export']}_content.json"])
        write_json_output_file_content(DR_file, data_request)
        write_json_output_file_content(VS_file, vocabulary_server)

        # Test that the two files do not produce issues with the API
        DR = DataRequest.from_separated_inputs(DR_input=DR_file, VS_input=VS_file)


kwargs = args.__dict__

if args.test:
    with tempfile.TemporaryDirectory() as output_dir:
        kwargs["output_dir"] = output_dir
        database_transformation(**kwargs)
else:
    database_transformation(**kwargs)
