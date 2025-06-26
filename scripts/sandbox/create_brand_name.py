#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Add brand name in VS database.

To make quality control check on the branded name computed with official software.
"""
from __future__ import division, print_function, unicode_literals, absolute_import

import os
import re
import sys
import argparse
import tempfile
from collections import defaultdict

from data_request_api.query.data_request import DataRequest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_request_api.content.dump_transformation import get_transformed_content
from data_request_api.utilities.tools import write_json_output_file_content, read_json_input_file_content
from data_request_api.utilities.logger import change_log_file, change_log_level
from data_request_api.utilities.parser import append_arguments_to_parser
from data_request_api.utilities.decorators import append_kwargs_from_config

parser = argparse.ArgumentParser()
parser.add_argument("--version", default="latest_stable", help="Version to be used")
parser.add_argument("--extended_brand_name", action="store_true", default=False,
                    help="Should extended brand name be used?")
parser = append_arguments_to_parser(parser)
subparser = parser.add_mutually_exclusive_group()
subparser.add_argument("--output_dir", default=None, help="Dedicated output directory to use")
subparser.add_argument("--test", action="store_true",
                       help="Is the launch a test? If so, launch in temporary directory.")
args = parser.parse_args()


def compute_brand(variable, extended_brand_name=False):
	var_name = str(variable.variablerootdd)
	if var_name in ["undef", ]:
		var_name = str(variable.name)
	param_name = str(variable.physical_parameter.name)
	freq_name = str(variable.cmip7_frequency.name)
	cell_methods = str(variable.cell_methods.cell_methods)
	dimensions = str(variable.dimensions).split(", ")
	# Temporal label
	if "time: max" in cell_methods or "time: min" in cell_methods:
		tlabel = "tstat"
	elif "time: sum" in cell_methods:
		tlabel = "tsum"
	elif "time" in dimensions or "timefxc" in dimensions:
		tlabel = "tavg"
	elif "time1" in dimensions:
		tlabel = "tpt"
	elif "time2" in dimensions:
		tlabel = "tclm"
	elif "time3" in dimensions:
		tlabel = "tclmdc"
	else:
		tlabel = "ti"
	# Vertical label
	vlabel = "u"
	if "sdepth" in dimensions or "olevel" in dimensions or "alevel" in dimensions or "alevhalf" in dimensions \
			or "olevhalf" in dimensions:
		vlabel = "l"
	elif "rho" in dimensions:
		vlabel = "rho"
	else:
		height_pattern = "^height(\d+)m$"
		depth_pattern = "^((depth)|(olayer))(\d+)m?$"
		sdepth_pattern = "^sdepth(\d+)$"
		opbar_pattern = "^op(\d+)bar$"
		splevel_pattern = "^pl?(\d+)$"
		alt_pattern = "^alt(\d+)$"
		plevel_pattern = "^plev(\d+[uch]?)$"
		oplevel_pattern = "^oplev(\d+)$"
		height_dims = [dim for dim in dimensions if re.compile(height_pattern).match(dim) is not None]
		depth_dims = [dim for dim in dimensions if re.compile(depth_pattern).match(dim) is not None]
		sdepth_dims = [dim for dim in dimensions if re.compile(sdepth_pattern).match(dim) is not None]
		opbar_dims = [dim for dim in dimensions if re.compile(opbar_pattern).match(dim) is not None]
		splevel_dims = [dim for dim in dimensions if re.compile(splevel_pattern).match(dim) is not None]
		alt_dims = [dim for dim in dimensions if re.compile(alt_pattern).match(dim) is not None]
		plevel_dims = [dim for dim in dimensions if re.compile(plevel_pattern).match(dim) is not None]
		oplevel_dims = [dim for dim in dimensions if re.compile(oplevel_pattern).match(dim) is not None]
		if len(height_dims) > 0:
			vlabel = f"h{re.match(height_pattern, height_dims[0]).group(1)}m"
		elif len(sdepth_dims) > 0:
			vlabel = f"d{re.match(sdepth_pattern, sdepth_dims[0]).group(1)}0cm"
		elif len(depth_dims) > 0:
			vlabel = f"d{re.match(depth_pattern, depth_dims[0]).group(4)}m"
		elif len(opbar_dims) > 0:
			vlabel = f"op{re.match(opbar_pattern, opbar_dims[0]).group(1)}bar"
		elif len(splevel_dims) > 0:
			vlabel = f"{re.match(splevel_pattern, splevel_dims[0]).group(1)}hPa"
		elif len(alt_dims) > 0:
			vlabel = f"h{re.match(alt_pattern, alt_dims[0]).group(1)}"
		elif len(plevel_dims) > 0:
			vlabel = f"p{re.match(plevel_pattern, plevel_dims[0]).group(1)}"
		elif len(oplevel_dims) > 0:
			vlabel = f"op{re.match(oplevel_pattern, oplevel_dims[0]).group(1)}"
	# Horizontal label
	if (("latitude" in dimensions and "longitude" in dimensions) or ("xant" in dimensions and "yant" in dimensions) or
			("xgre" in dimensions and "ygre" in dimensions)):
		hlabel = "hxy"
	elif "latitude" in dimensions and "longitude" not in dimensions and "basin" not in dimensions:
		hlabel = "hy"
	elif "site" in dimensions:
		hlabel = "hxys"
	elif "latitude" in dimensions and "basin" in dimensions:
		hlabel = "hys"
	elif ("gridlatitude" in dimensions and "basin" in dimensions) or "oline" in dimensions or "siline" in dimensions:
		hlabel = "ht"
	else:
		hlabel = "hm"
	# Area label
	if "where" not in cell_methods:
		alabel = "u"
	elif "air" in cell_methods:
		alabel = "air"
	elif "convective_cloud" in cell_methods:
		alabel = "ccl"
	elif "stratiform_cloud" in cell_methods:
		alabel = "scl"
	elif "cloud" in cell_methods:
		alabel = "cl"
	elif "crops" in cell_methods:
		alabel = "crp"
	elif "floating_ice_shelf" in cell_methods:
		alabel = "fis"
	elif "grounded_ice_sheet" in cell_methods:
		alabel = "gis"
	elif "ice_sheet" in cell_methods:
		alabel = "is"
	elif "ice_free_sea" in cell_methods:
		alabel = "ifs"
	elif "sea_ice_melt_pond" in cell_methods:
		alabel = "simp"
	elif "sea_ice_ridges" in cell_methods:
		alabel = "sir"
	elif "sea_ice" in cell_methods:
		alabel = "si"
	elif "sea" in cell_methods:
		alabel = "sea"
	elif "land_ice" in cell_methods:
		alabel = "li"
	elif "land" in cell_methods:
		alabel = "lnd"
	elif "natural_grasses" in cell_methods:
		alabel = "ng"
	elif "pastures" in cell_methods:
		alabel = "pst"
	elif "shrubs" in cell_methods:
		alabel = "shb"
	elif "snow" in cell_methods:
		alabel = "sn"
	elif "trees" in cell_methods:
		alabel = "tree"
	elif "unfrozen_soil" in cell_methods:
		alabel = "ufs"
	elif "vegetation" in cell_methods:
		alabel = "veg"
	elif "wetland" in cell_methods:
		alabel = "wl"
	elif "sector" in cell_methods:
		alabel = "multi"
	else:
		alabel = "undef"
	# Region
	if "xgre" in dimensions or "ygre" in dimensions or "Gre" in var_name:
		rlabel = "gre"
	elif "xant" in dimensions or "yant" in dimensions or "Ant" in var_name:
		rlabel = "ant"
	elif "site" in dimensions:
		rlabel = "site"
	else:
		rlabel = "global"
	rep = "-".join([param_name, tlabel, vlabel, hlabel, alabel])
	if extended_brand_name:
		return ".".join([rep, freq_name, rlabel])
	else:
		return rep


@append_kwargs_from_config
def create_brand_name(version, output_dir, extended_brand_name, **kwargs):
	change_log_file(default=True, logfile=kwargs["log_file"])
	change_log_level(kwargs["log_level"])
	### Step 1: Get the data request content
	content_dict = get_transformed_content(version=version, output_dir=output_dir, **kwargs)
	DR = DataRequest.from_separated_inputs(**content_dict)
	### Step 2: Create the brand name
	vs_content = read_json_input_file_content(content_dict["VS_input"])
	for var in vs_content["variables"].keys():
		vs_content["variables"][var]["brand"] = compute_brand(DR.find_element("variable", var),
		                                                      extended_brand_name=extended_brand_name)
	### Step 3: Rewrite file
	write_json_output_file_content(content_dict["VS_input"], vs_content)
	### Step 4: Create statistics file
	brand_statistics = defaultdict(list)
	for (var, values) in vs_content["variables"].items():
		brand_statistics[values["brand"]].append(var)
	write_json_output_file_content(content_dict["VS_input"].replace(".json", "_brand.json"), brand_statistics)
	issues_brand = {key: values for (key, values) in brand_statistics.items() if len(values) > 1}
	write_json_output_file_content(content_dict["VS_input"].replace(".json", "_issues_brand.json"), issues_brand)


kwargs = args.__dict__

if args.test:
	with tempfile.TemporaryDirectory() as output_dir:
		kwargs["output_dir"] = output_dir
		create_brand_name(**kwargs)
else:
	create_brand_name(**kwargs)
