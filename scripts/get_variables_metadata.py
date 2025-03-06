#!/usr/bin/env python
'''
Extract metadata of CMOR variables and write them to a json file.
Example output file: scripts/variable_info/all_var_info.json
Output file names (filepath) are set below.
'''
import argparse
import hashlib
import json
import os
from collections import OrderedDict

import sys
sys.path.append(os.path.abspath('..'))

import data_request_api.stable.content.dreq_api.dreq_content as dc
import data_request_api.stable.query.dreq_query as dq
from data_request_api.stable.query import dreq_classes
from data_request_api import version as api_version


default_dreq_version = 'v1.1'

outfile_extensions = ['.json', '.csv']

parser = argparse.ArgumentParser(
    description='Get CMOR variables metadata and write to json.'
    )
parser.add_argument('-dr', '--dreq_version', type=str, default=default_dreq_version,
                    help='version of data request content to use')
parser.add_argument('-o', '--outfile', nargs='+', type=str,
                    help=f'outfile (one or more), identified by extensions: {outfile_extensions}')
parser.add_argument('-cn', '--compound_names', nargs='+', type=str,
                    help='include only variables with the specified Compound Names (examples: "Amon.tas", "Omon.sos")')
parser.add_argument('-t', '--cmor_tables', nargs='+', type=str,
                    help='include only the specified CMOR tables (aka MIP tables, examples: "Amon", "Omon")')
parser.add_argument('-v', '--cmor_variables', nargs='+', type=str,
                    help='include only the specified CMOR variables (out_name, examples: "tas", "siconc")')
args = parser.parse_args()


# Load data request content
use_dreq_version = args.dreq_version
dc.retrieve(use_dreq_version)  
content = dc.load(use_dreq_version)

# Get metadata for variables
all_var_info = dq.get_variables_metadata(
    content,
    compound_names=args.compound_names,
    cmor_tables=args.cmor_tables,
    cmor_variables=args.cmor_variables,
    use_dreq_version=use_dreq_version  # TO DEPRECATE
    )

# Write output file(s)
for filepath in args.outfile:
    dq.write_variables_metadata(
        all_var_info,
        filepath,
        api_version=api_version,
        use_dreq_version=use_dreq_version,
        content_path = dc._dreq_content_loaded['json_path']
        )
