#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A script to check if an expected variable is present.
"""
from __future__ import division, print_function, unicode_literals, absolute_import

import json
import pprint
import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from data_request_api.content.dump_transformation import get_transformed_content
from data_request_api.query.data_request import DataRequest
from data_request_api.utilities.parser import append_arguments_to_parser


parser = argparse.ArgumentParser()
parser.add_argument("--version", default="latest_stable", help="Version to be used.")
parser.add_argument("--search_type", type=str, help="The element type to be searched for.")
parser.add_argument("--search_dict", type=json.loads, default=dict(), help="A dictionary giving the search criteria to fill.")
parser.add_argument("--search_operation", choices=["any", "all", "any_of_all", "all_of_any"], default="all", help="Operation to apply on search_dict results.")
parser.add_argument("--not_search_dict", type=json.loads, default=dict(), help="A dictionary giving the search criteria not to fill.")
parser.add_argument("--not_search_operation", choices=["any", "all", "any_of_all", "all_of_any"], default="any", help="Operation to apply on not_search_dict results.")
parser = append_arguments_to_parser(parser)
args = parser.parse_args()
kwargs = args.__dict__

# Step 1 Get the data request content
print(f"Load CMIP7 Data Request content version {kwargs['version']}")
content_dict = get_transformed_content(**kwargs)
DR = DataRequest.from_separated_inputs(**content_dict)

# Search for data
print(f"Look for element type {kwargs['search_type']} with to fill criteria {kwargs['search_dict']} and not to "
            f"fill criteria {kwargs['not_search_dict']}...")
rep = DR.filter_elements_per_request(elements_to_filter=kwargs['search_type'],
                                     requests=kwargs['search_dict'],
                                     request_operation=kwargs['search_operation'],
                                     not_requests=kwargs['not_search_dict'],
                                     not_request_operation=kwargs['not_search_operation'])
rep = sorted(list(set(rep)), key=lambda x: x.name)

# Print output
print(f"{len(rep)} elements of type {kwargs['search_type']} found:")
# pprint.pprint(rep)
