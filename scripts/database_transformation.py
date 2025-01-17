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


import data_request_api.stable.content.dreq_api.dreq_content as dc
from data_request_api.stable.content.dump_transformation import transform_content, get_transformed_content
from data_request_api.stable.query.data_request import DataRequest
from data_request_api.stable.utilities.tools import write_json_output_file_content
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


def database_transformation(output_dir, dreq_version="latest_stable", dreq_export_version="release",
                            use_consolidation=False):
    # Download specified version of data request content (if not locally cached)
    versions = dc.retrieve(dreq_version, export=dreq_export_version, consolidate=use_consolidation)

    for (version, content) in versions.items():
        # Load the content
        content = dc.load(version, export=dreq_export_version, consolidate=use_consolidation)

        # Transform content into DR and VS
        data_request, vocabulary_server = transform_content(content, version=dreq_version)

        # Write down the two files
        DR_file = os.path.sep.join([output_dir, version, f"DR_{dreq_export_version}_content.json"])
        VS_file = os.path.sep.join([output_dir, version, f"VS_{dreq_export_version}_content.json"])
        write_json_output_file_content(DR_file, data_request)
        write_json_output_file_content(VS_file, vocabulary_server)

        # Test that the two files do not produce issues with the API
        DR = DataRequest.from_separated_inputs(DR_input=DR_file, VS_input=VS_file)


# Set up log file (default to stdout) and log level
change_log_file(default=True)
change_log_level(args.log_level)

if args.output_dir in ["default", "customed"]:
    if args.output_dir in ["default", ]:
        output_dir = dc._dreq_res
    elif args.output_dir_customed is not None:
        output_dir = args.output_dir_customed
    else:
        raise ValueError("If --output_dir='customed', --output_dir_customed should be defined with a not None value.")

    database_transformation(output_dir=output_dir, dreq_version=args.dreq_version,
                            dreq_export_version=args.dreq_export_version, use_consolidation=args.use_consolidation)
elif args.output_dir in ["test", ]:
    with tempfile.TemporaryDirectory() as output_dir:
        database_transformation(output_dir=output_dir, dreq_version=args.dreq_version,
                                dreq_export_version=args.dreq_export_version, use_consolidation=args.use_consolidation)
