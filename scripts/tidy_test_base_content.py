#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to tidy test base content
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import copy
import json
import os
import argparse
import re
from collections import defaultdict

from data_request_api.utilities.logger import get_logger
from data_request_api.utilities.tools import read_json_input_file_content, write_json_output_file_content
from data_request_api.content.dump_transformation import transform_content


parser = argparse.ArgumentParser()
parser.add_argument("--input_content", help="Input json file")
parser.add_argument("--output_directory", help="Output directory")
args = parser.parse_args()
kwargs = args.__dict__
kwargs["opportunities"] = ["1", "49", "68", "69"]
kwargs["experiment_groups"] = ["dcpp", "deck", "fast-track", "historical", "scenarios", "scenarios_extensions"]
kwargs["experiments"] = ["dcppB-forecast-cmip6", "amip", "esm-hist", "esm-piControl", "historical", "esm-flat10", 
                         "g7-1p5K-sai", "land-hist", "piClim-NOX", "scen7-hl", "scen7-m", "scen7-vl", "scen7-hl-ext", 
                         "scen7-m-ext", "scen7-vl-ext", "esm-scen7-hl", "esm-scen7-m", "esm-scen7-vl", 
                         "esm-scen7-hl-ext", "esm-scen7-m-ext", "esm-scen7-vl-ext"]
kwargs["variables"] = ["atmos.pr.tavg-u-hxy-u.day.glb", "atmos.ps.tavg-u-hxy-u.day.glb", "atmos.psl.tavg-u-hxy-u.day.glb",
                       "atmos.sfcWind.tavg-h10m-hxy-u.day.glb", "atmos.ta.tavg-p19-hxy-air.day.glb", "atmos.tas.tavg-h2m-hxy-u.day.glb",
                       "atmos.tas.tmax-h2m-hxy-u.day.glb", "atmos.tas.tmin-h2m-hxy-u.day.glb", "atmos.zg.tavg-p19-hxy-air.day.glb",
                       "ocean.sos.tavg-u-hxy-sea.day.glb", "ocean.tos.tavg-u-hxy-sea.day.glb", "ocean.zos.tavg-u-hxy-sea.day.glb",
                       "seaIce.siconc.tavg-u-hxy-u.day.glb", "atmos.areacella.ti-u-hxy-u.fx.glb", "atmos.sftlf.ti-u-hxy-u.fx.glb",
                       "land.mrsofc.ti-u-hxy-lnd.fx.glb", "land.orog.ti-u-hxy-u.fx.glb", "land.rootd.ti-u-hxy-lnd.fx.glb",
                       "land.sftgif.ti-u-hxy-u.fx.glb", "land.slthick.ti-sl-hxy-lnd.fx.glb", "ocean.areacello.ti-u-hxy-u.fx.glb",
                       "ocean.basin.ti-u-hxy-u.fx.glb", "ocean.deptho.ti-u-hxy-sea.fx.glb", "ocean.hfgeou.ti-u-hxy-sea.fx.glb",
                       "ocean.masscello.ti-ol-hxy-sea.fx.glb", "ocean.sftof.ti-u-hxy-u.fx.glb", "ocean.thkcello.ti-ol-hxy-sea.fx.glb",
                       "atmos.pr.tavg-u-hxy-u.mon.glb", "atmos.prc.tavg-u-hxy-u.mon.glb", "atmos.sfcWind.tavg-h10m-hxy-u.mon.glb",
                       "atmos.ta.tavg-p19-hxy-air.mon.glb", "atmos.tas.tavg-h2m-hxy-u.mon.glb", "atmos.tas.tmaxavg-h2m-hxy-u.mon.glb",
                       "atmos.tas.tminavg-h2m-hxy-u.mon.glb", "atmos.ts.tavg-u-hxy-u.mon.glb", "atmos.zg.tavg-p19-hxy-air.mon.glb",
                       "land.lai.tavg-u-hxy-lnd.mon.glb", "land.mrso.tavg-u-hxy-lnd.mon.glb", "land.mrsol.tavg-d10cm-hxy-lnd.mon.glb",
                       "landIce.snc.tavg-u-hxy-lnd.mon.glb", "ocean.bigthetao.tavg-ol-hxy-sea.mon.glb", "ocean.so.tavg-ol-hxy-sea.mon.glb",
                       "ocean.sos.tavg-u-hxy-sea.mon.glb", "ocean.thetao.tavg-ol-hxy-sea.mon.glb", "ocean.tos.tavg-u-hxy-sea.mon.glb",
                       "ocean.wo.tavg-ol-hxy-sea.mon.glb", "ocean.zos.tavg-u-hxy-sea.mon.glb", "ocean.zostoga.tavg-u-hm-sea.mon.glb",
                       "seaIce.siconc.tavg-u-hxy-u.mon.glb", "seaIce.simass.tavg-u-hxy-si.mon.glb", "seaIce.sithick.tavg-u-hxy-si.mon.glb",
                       "seaIce.siu.tavg-u-hxy-si.mon.glb", "seaIce.siv.tavg-u-hxy-si.mon.glb", "atmos.hurs.tavg-h2m-hxy-u.6hr.glb",
                       "atmos.huss.tpt-h2m-hxy-u.3hr.glb", "atmos.pr.tavg-u-hxy-u.1hr.glb", "atmos.pr.tavg-u-hxy-u.3hr.glb",
                       "atmos.ta.tpt-p3-hxy-air.6hr.glb", "atmos.tas.tpt-h2m-hxy-u.3hr.glb", "atmos.bldep.tpt-u-hxy-u.3hr.glb",
                       "atmos.hfls.tavg-u-hxy-u.3hr.glb", "atmos.hfss.tavg-u-hxy-u.3hr.glb", "atmos.ps.tpt-u-hxy-u.3hr.glb",
                       "land.mrsol.tpt-d10cm-hxy-lnd.3hr.glb", "land.srfrad.tavg-u-hxy-u.3hr.glb", "land.tslsi.tpt-u-hxy-lsi.3hr.glb",
                       "atmos.rlds.tavg-u-hxy-u.3hr.glb", "atmos.rlus.tavg-u-hxy-u.3hr.glb", "atmos.ta.tpt-p6-hxy-air.3hr.glb",
                       "land.hfdsl.tavg-u-hxy-lnd.3hr.glb", "land.mrsol.tavg-d100cm-hxy-lnd.3hr.glb", "land.tran.tavg-u-hxy-u.3hr.glb",
                       "ocean.mlotst.tavg-u-hxy-sea.day.glb", "ocean.mlotst.tmax-u-hxy-sea.mon.glb", "ocean.mlotst.tmin-u-hxy-sea.mon.glb",
                       "ocean.tnkebto.tavg-u-hxy-sea.yr.glb", "ocean.uos.tavg-u-hxy-sea.day.glb", "ocean.vos.tavg-u-hxy-sea.day.glb",
                       "ocean.so.tavg-ol-hxy-sea.day.glb", "thetao.tavg-op20bar-hxy-sea.day.glb", "ocnBgchem.arag.tavg-ols-hxy-sea.mon.glb",
                       "ocnBgchem.arag.tavg-ol-hxy-sea.mon.glb", "ocnBgchem.calc.tavg-ols-hxy-sea.mon.glb", "ocnBgchem.calc.tavg-ol-hxy-sea.mon.glb",
                       "ocnBgchem.chl.tavg-op20bar-hxy-sea.day.glb", "ocnBgchem.dissic.tavg-ol-hxy-sea.mon.glb", "ocnBgchem.o2.tavg-op20bar-hxy-sea.day.glb",
                       "ocnBgchem.ph.tavg-op20bar-hxy-sea.day.glb", "ocnBgchem.talk.tavg-ol-hxy-sea.mon.glb", "ocean.thetao.tavg-op20bar-hxy-sea.day.glb",
                       "ocean.bigthetao.tavg-op20bar-hxy-sea.day.glb", "ocean.tos.tpt-u-hxy-sea.3hr.glb", "ocean.tossq.tavg-u-hxy-sea.day.glb",
                       "ocean.zossq.tavg-u-hxy-sea.mon.glb", "ocean.zostoga.tavg-u-hm-sea.day.glb", "ocean.mpw.tpt-u-hxy-sea.3hr.glb",
                       "ocean.mpw.tavg-u-hxy-sea.mon.glb", "ocean.swh.tpt-u-hxy-sea.3hr.glb", "ocean.swh.tavg-u-hxy-sea.mon.glb",
                       "ocean.wpp.tpt-u-hxy-sea.3hr.glb", "ocean.wpp.tavg-u-hxy-sea.mon.glb", "atmos.psl.tpt-u-hxy-u.1hr.glb",
                       "atmos.uas.tpt-h10m-hxy-u.1hr.glb", "atmos.vas.tpt-h10m-hxy-u.1hr.glb", "ocean.tos.tpt-u-hxy-sea.3hr.glb",
                       "seaIce.sithick.tavg-u-hxy-si.day.glb", "seaIce.siu.tavg-u-hxy-si.day.glb", "seaIce.siv.tavg-u-hxy-si.day.glb"
                       ]


def remove_unused_links_one_base(input_content, dict_to_remove, category, linked_category, linked_reference_list, remove_id_if_void=False):
	base_name = list(input_content)[0]
	for record in input_content[base_name][linked_category]["records"]:
		reference_list = input_content[base_name][linked_category]["records"][record].get(linked_reference_list, list())
		reference_list = sorted(list(set(reference_list) - set(dict_to_remove[category])))
		if len(reference_list) > 0:
			input_content[base_name][linked_category]["records"][record][linked_reference_list] = reference_list
		else:
			if linked_reference_list in input_content[base_name][linked_category]["records"][record]:
				del input_content[base_name][linked_category]["records"][record][linked_reference_list]
			if remove_id_if_void:
				dict_to_remove[linked_category].append(record)
	for record in dict_to_remove[linked_category]:
		if record in input_content[base_name][linked_category]["records"]:
			del input_content[base_name][linked_category]["records"][record]
	return input_content, dict_to_remove


def remove_unused_links_several_base(input_content, dict_to_remove, base_category, category, linked_category, linked_reference_list, linked_base, remove_id_if_void=False, base_linked_name=None):
	if base_category == linked_base:
		for record in input_content[linked_base][linked_category]["records"]:
			reference_list = input_content[linked_base][linked_category]["records"][record].get(linked_reference_list, list())
			if isinstance(reference_list, str):
				reference_list = reference_list.split(", ")
				to_join = True
			else:
				to_join = False
			reference_list = sorted(list(set(reference_list) - set(dict_to_remove[base_category][category])))
			if to_join:
				reference_list = ", ".join(reference_list)
			if len(reference_list) > 0:
				input_content[linked_base][linked_category]["records"][record][linked_reference_list] = reference_list
			else:
				if linked_reference_list in input_content[linked_base][linked_category]["records"][record]:
					del input_content[linked_base][linked_category]["records"][record][linked_reference_list]
				if remove_id_if_void:
					dict_to_remove[linked_base][linked_category].append(record)
	else:
		if base_linked_name is None:
			raise ValueError("Must specify base_linked_name for category %s" % category)
		reference_list = [input_content[base_category][category]["records"][record][base_linked_name]
		                  for record in sorted(list(set(list(input_content[base_category][category]["records"])) - set(dict_to_remove[base_category][category])))]
		for record in input_content[linked_base][linked_category]["records"]:
			if input_content[linked_base][linked_category]["records"][record].get(linked_reference_list) not in reference_list:
				dict_to_remove[linked_base][linked_category].append(record)
	for record in dict_to_remove[linked_base][linked_category]:
		if record in input_content[linked_base][linked_category]["records"]:
			del input_content[linked_base][linked_category]["records"][record]
	return input_content, dict_to_remove

# Read input content
input_content = read_json_input_file_content(kwargs["input_content"])

to_check_linked = read_json_input_file_content("scripts/tidy_config.json")

# Check if there are one or several bases
if len(input_content) == 1:
	input_type = "release"
	# One base case: all identifiers are unique
	base_name = list(input_content)[0]
	dict_to_remove = defaultdict(list)
	to_check_linked = to_check_linked["single"]
	for dict_check in to_check_linked:
		category = dict_check["category"]
		category_name = dict_check.get("category_name", None)
		if category_name is not None:
			category_kwargs_input = kwargs[dict_check["category_kwargs_input"]]
			dict_to_remove[category].extend([record for record in input_content[base_name][category]["records"]
			                                 if input_content[base_name][category]["records"][record][category_name] not in category_kwargs_input])
		require_one = dict_check.get("require_one", list())
		if len(require_one) > 0:
			for record in input_content[base_name][category]["records"]:
				if all(elt not in input_content[base_name][category]["records"][record] for elt in require_one):
					dict_to_remove[category].append(record)

		for record in dict_to_remove[category]:
			if record in input_content[base_name][category]["records"]:
				del input_content[base_name][category]["records"][record]

		if len(dict_to_remove[category]) > 0:
			for (linked_category, value) in dict_check["linked"].items():
				for (linked_reference_list, remove_id_if_void) in value:
					input_content, dict_to_remove = remove_unused_links_one_base(input_content=input_content,
					                                                             dict_to_remove=dict_to_remove,
					                                                             category=category,
					                                                             linked_category=linked_category,
					                                                             linked_reference_list=linked_reference_list,
					                                                             remove_id_if_void=remove_id_if_void)
else:
	input_type = "raw"
	# Several bases case: some identifiers may not be unique and equivalences must be kept
	to_check_linked = to_check_linked["several"]
	dict_to_remove = defaultdict(lambda: defaultdict(list))

	for dict_check in to_check_linked:
		category = dict_check["category"]
		category_name = dict_check.get("category_name", None)
		category_base = dict_check["category_base"]
		category_linked_name = dict_check.get("category_linked_name", category_name)
		if category_name is not None:
			category_kwargs_input = kwargs[dict_check["category_kwargs_input"]]
			dict_to_remove[category_base][category].extend([record for record in input_content[category_base][category]["records"]
			                                                if input_content[category_base][category]["records"][record][category_name] not in category_kwargs_input])
		require_one = dict_check.get("require_one", list())
		if len(require_one) > 0:
			for record in input_content[category_base][category]["records"]:
				if all(elt not in input_content[category_base][category]["records"][record] for elt in require_one):
					dict_to_remove[category_base][category].append(record)

		for record in dict_to_remove[category_base][category]:
			if record in input_content[category_base][category]["records"]:
				del input_content[category_base][category]["records"][record]

		if len(dict_to_remove[category_base][category]) > 0:
			for (linked_base, values) in dict_check["linked"].items():
				for (linked_category, value) in values.items():
					for (linked_reference_list, remove_id_if_void) in value:
						input_content, dict_to_remove = remove_unused_links_several_base(input_content=input_content,
						                                                                 dict_to_remove=dict_to_remove,
						                                                                 category=category,
						                                                                 base_category=category_base,
						                                                                 linked_category=linked_category,
						                                                                 linked_reference_list=linked_reference_list,
						                                                                 remove_id_if_void=remove_id_if_void,
						                                                                 linked_base=linked_base,
						                                                                 base_linked_name=category_linked_name)

write_json_output_file_content(os.sep.join([kwargs["output_directory"], os.path.basename(kwargs["input_content"])]), input_content)
DR, VS = transform_content(input_content, "test")
write_json_output_file_content(os.sep.join([kwargs["output_directory"], f"DR_{input_type}_not-consolidate_content.json"]), DR)
write_json_output_file_content(os.sep.join([kwargs["output_directory"], f"VS_{input_type}_not-consolidate_content.json"]), VS)