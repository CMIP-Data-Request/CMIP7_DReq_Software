#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to change the basic airtable export into readable files.
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import copy
import json
import os
import argparse
import re
from collections import defaultdict

import six

from logger import get_logger, change_log_level, change_log_file
from tools import read_json_input_file_content, write_json_output_file_content


def correct_key_string(input_string, *to_remove_strings):
    logger = get_logger()
    if isinstance(input_string, six.string_types):
        input_string = input_string.lower()
        for to_remove_string in to_remove_strings:
            input_string = input_string.replace(to_remove_string.lower(), "")
        input_string = input_string.strip()
        input_string = input_string.replace("&", "and").replace(" ", "_")
    else:
        logger.error(f"Deal with string types, not {type(input_string).__name__}")
        raise TypeError(f"Deal with string types, not {type(input_string).__name__}")
    return input_string


def correct_dictionaries(input_dict, is_record_ids=False):
    logger = get_logger()
    if isinstance(input_dict, dict):
        rep = dict()
        for (key, value) in input_dict.items():
            if not is_record_ids:
                new_key = correct_key_string(key)
            else:
                new_key = key
            if isinstance(value, dict):
                rep[new_key] = correct_dictionaries(value, is_record_ids=key in ["records", "fields"])
            else:
                rep[new_key] = copy.deepcopy(value)
        return rep
    else:
        logger.error(f"Deal with dict types, not {type(input_dict).__name__}")
        raise TypeError(f"Deal with dict types, not {type(input_dict).__name__}")


def transform_content_three_bases(content, version):
    logger = get_logger()
    if isinstance(content, dict):
        new_content = dict()
        opportunity_table = [elt for elt in list(content) if "opportunities" in elt.lower()][0]
        variables_table = [elt for elt in list(content) if "variables" in elt.lower()][0]
        physical_parameters_table = [elt for elt in list(content) if "parameters" in elt.lower()][0]
        # Copy the bases
        old_variables_content = content[opportunity_table].pop("Variables")
        old_physical_parameters_content = content[variables_table].pop("Physical Parameter")
        new_content["Opportunity/variable Group Comments"] = content[opportunity_table].pop("Comment")
        new_content["Experiments"] = content[opportunity_table].pop("Experiment")
        new_content["MIPs"] = content[opportunity_table].pop("MIP")
        for elt in list(content[opportunity_table]):
            new_content[elt] = content[opportunity_table].pop(elt)
        new_content["Variables"] = content[variables_table].pop("Variable")
        new_content["Coordinates and Dimensions"] = content[variables_table].pop("Coordinate or Dimension")
        new_content["Variable Comments"] = content[variables_table].pop("Comment")
        new_content["Modelling Realm"] = content[variables_table].pop("Modeling Realm")
        for elt in list(content[variables_table]):
            new_content[elt] = content[variables_table].pop(elt)
        new_content["Physical Parameters Comments"] = content[physical_parameters_table].pop("Comment")
        new_content["Physical Parameters"] = content[physical_parameters_table].pop("Physical Parameter")
        new_content["CF Standard Names"] = content[physical_parameters_table].pop("CF Standard Name")
        for elt in list(content[physical_parameters_table]):
            new_content[elt] = content[physical_parameters_table].pop(elt)
        # Correct record id through several bases
        old_variables_ids = {record_id: value["Compound Name"] for (record_id, value) in
                             old_variables_content["records"].items()}
        new_variables_ids = {value["Compound Name"]: record_id for (record_id, value) in
                             new_content["Variables"]["records"].items()}
        for var_group_id in list(new_content["Variable Group"]["records"]):
            new_content["Variable Group"]["records"][var_group_id]["Variables"] = \
                [new_variables_ids[old_variables_ids[elt]] for elt in
                 new_content["Variable Group"]["records"][var_group_id]["Variables"]]
        old_physical_parameters_ids = {record_id: value["Name"] for (record_id, value) in
                                       old_physical_parameters_content["records"].items()}
        new_physical_parameters_ids = {value["Name"]: record_id for (record_id, value) in
                                       new_content["Physical Parameters"]["records"].items()}
        for var_id in list(new_content["Variables"]["records"]):
            new_content["Variables"]["records"][var_id]["Physical Parameter"] = \
                [new_physical_parameters_ids[old_physical_parameters_ids[elt]] for elt in
                 new_content["Variables"]["records"][var_id]["Physical Parameter"]]
        # Create a new frequency entry if none
        if "CMIP7 Frequency" not in new_content:
            if "Frequency" not in new_content:
                new_content["CMIP7 Frequency"] = dict(records=dict())
                for var_id in new_content["Variables"]["records"]:
                    for frequency_id in copy.deepcopy(new_content["Variables"]["records"][var_id]["Frequency"]):
                        if frequency_id not in new_content["CMIP7 Frequency"]["records"]:
                            new_content["CMIP7 Frequency"]["records"][frequency_id] = dict(name=frequency_id, uid=frequency_id)
            else:
                new_content["CMIP7 Frequency"] = new_content.pop("Frequency")
        if "Data Request Themes" not in new_content:
            new_content["Data Request Themes"] = dict(records=dict())
            for opportunity_id in new_content["Opportunity"]["records"]:
                for theme_id in copy.deepcopy(new_content["Opportunity"]["records"][opportunity_id]["Themes"]):
                    if theme_id not in new_content["Data Request Themes"]["records"]:
                        new_content["Data Request Themes"]["records"][theme_id] = dict(name=theme_id, uid=theme_id)
        # Harmonise record ids through bases
        logger.info("Harmonise bases content record ids")
        content_str = json.dumps(new_content)
        for id in sorted(list(old_variables_ids)):
            content_str = re.sub(f'"{id}"', f'"{new_variables_ids[old_variables_ids[id]]}"', content_str)
        for id in sorted(list(old_physical_parameters_ids)):
            content_str = re.sub(f'"{id}"', f'"{new_physical_parameters_ids[old_physical_parameters_ids[id]]}"', content_str)
        new_content = json.loads(content_str)
        # Return the content
        return {f"Data Request {version}": new_content}
    else:
        logger.error(f"Deal with dict types, not {type(content).__name__}")
        raise TypeError(f"Deal with dict types, not {type(content).__name__}")


def transform_content_one_base(content):
    logger = get_logger()
    if isinstance(content, dict):
        default_count = 0
        default_template = "default_{:d}"
        content = content[list(content)[0]]
        # Rename some elements
        esm_bcv = [elt for elt in list(content) if re.match(r"esm-bcv.*", elt)]
        if len(esm_bcv) == 1:
            esm_bcv = esm_bcv[0]
            content["esm-bcv"] = content.pop(esm_bcv)
        for (key, new_key) in [("opportunity", "opportunities"), ("experiment_group", "experiment_groups"),
                               ("variable_group", "variable_groups")]:
            if key in content:
                    content[new_key] = content.pop(key)
        for pattern in [".*rank.*", ]:
            elts = [elt for elt in list(content) if re.compile(pattern).match(elt)]
            for elt in elts:
                del content[elt]
        for pattern in ["(legacy)", ]:
            for elt in [elt for elt in list(content) if pattern in elt]:
                new_elt = elt.replace(pattern, "").strip("_")
                content[new_elt] = content.pop(elt)
        # Tidy the content of the export file
        default_patterns_to_remove = [r".*\(from.*\).*", r".*proposed.*", r".*review.*", r".*--.*",
                                      r".*created.*", r".*rank.*", ".*count.*", ".*alert.*", ".*tagged.*", ".*unique.*",
                                      "last_modified.*", ".*validation.*", ".*number.*"]
        to_remove_keys_patterns = {
            "cell_measures": [r"variables", "structure"],
            "cell_methods": [r"structure", r"variables"],
            "cf_standard_names": [r"physical_parameters.*", "esm-bcv.*"],
            "cmip6_frequency": [r"table_identifiers.*", r"variables.*"],
            "cmip7_frequency": [r"table_identifiers.*", r"variables.*"],
            "coordinates_and_dimensions": [r"spatial_shape", r"structure", "temporal_shape", "variables", "size"],
            "data_request_themes": [r"experiment_group.*", r".*opportunit.*", r"variable_group.*"],
            "esm-bcv": [r"v\d.*", "cf_standard_name"],
            "experiment_groups": [r"opportunit.*", r"theme.*", "comments.+"],
            "experiments": [r"experiment_group.*", r"opportunit.*", "variables", "mip"],
            "glossary": ["opportunit.*", ],
            "mips": ["variable_group.*", "experiments.*", ".*opportunit.*"],
            "modelling_realm": ["variables", ],
            "opportunities": [".*data_volume_estimate", "opportunity_id", "originally_requested_variable_groups"],
            "opportunity/variable_group_comments": ["experiment_groups", "opportunities", "theme", "variable_groups"],
            "physical_parameters": ["variables", "conditional", "does_a_cf.*"],
            "physical_parameters_comments": ["physical_parameters", "does_a.*"],
            "priority_level": ["variable_group", ],
            "spatial_shape": [r"dimensions.*", r"structure.*", r"variables.*", "hor.*", "vert.*"],
            "structure": [r"variables.*", "brand_.*", "calculation.*"],
            "table_identifiers": ["variables", ],
            "temporal_shape": ["variables", "structure"],
            "time_slice": ["uid.+", ],
            "variable_comments": ["variable.*", ],
            "variable_groups": [".*opportunit.*", "theme", r"size.*", "mip_ownership"],
            "variables": [r"priority.*", r".*variable_group.*", ".*experiment.*", "size", "vertical_dimension",
                          "temporal_sampling_rate", "horizontal_mesh", r"brand.*\[link\]", "structure_label",
                          "table_section.*", "theme"],
        }
        to_rename_keys_patterns = {
            "cell_methods": [("comments", "variables_comments"), ("label", "name")],
            "cf_standard_names": [("comments", "physical_parameters_comments")],
            "cmip7_frequency": [("cmip6_frequency.*", "cmip6_frequency")],
            "coordinates_and_dimensions": [("requested_bounds.+", "requested_bounds")],
            "data_request_themes": [("comments", "opportunity/variable_group_comments"), ("uid.+", "uid")],
            "esm-bcv": [('cmor_variables', "variables")],
            "experiments": [("experiment", "name")],
            "experiment_groups": [("comments", "opportunity/variable_group_comments")],
            "opportunities": [("title_of_opportunity", "name"), ("comments", "opportunity/variable_group_comments"),
                            ("ensemble_size", "minimum_ensemble_size"),
                              ("working/updated_variable_groups", "variable_groups")],
            "physical_parameters": [("comments", "physical_parameters_comments"),
                                    ("cf_proposal_github_issue", "proposal_github_issue")],
            "spatial_shape": [("comments", "variables_comments")],
            "temporal_shape": [("comments", "variables_comments")],
            "structure": [("label", "name")],
            "table_identifiers": [("comment", "notes")],
            "variable_groups": [(".*mips.*", "mips"), ("comments", "opportunity/variable_group_comments")],
            "variables": [("compound_name", "name"), ("cmip6_frequency.+", "cmip6_frequency"),
                          ("modeling_realm", "modelling_realm"), ("comments", "variables_comments")],
        }
        to_merge_keys_patterns = {
            # "opportunities": [(".+variable_groups", "variable_groups")]
        }
        to_sort_keys_content = {
            "opportunities": ["variable_groups", "themes", "experiment_groups", "time_slice"],
            "experiment_groups": ["experiments", ],
            "variable_groups": ["variables", "mips"]
        }
        for subelt in sorted(list(content)):
            # Remove everything save records
            records = content[subelt].pop("records")
            for subkey in list(content[subelt]):
                del content[subelt][subkey]
            content[subelt].update(records)
            # Find out list of patterns to remove, rename, merge, sort...
            patterns_to_remove = to_remove_keys_patterns.get(subelt, list())
            patterns_to_remove.extend(default_patterns_to_remove)
            patterns_to_remove = [re.compile(elt) for elt in patterns_to_remove]
            patterns_to_rename = to_rename_keys_patterns.get(subelt, list())
            patterns_to_rename = [(re.compile(elt[0]), elt[1]) for elt in patterns_to_rename]
            patterns_to_merge = to_merge_keys_patterns.get(subelt, list())
            patterns_to_merge = [(re.compile(elt[0]), elt[1]) for elt in patterns_to_merge]
            for record_id in sorted(list(content[subelt])):
                # Remove unused keys
                list_keys = sorted(list(content[subelt][record_id]))
                list_keys_to_remove = [elt for elt in list_keys if
                                       any(patt.match(elt) is not None for patt in patterns_to_remove)]
                for key in list_keys_to_remove:
                    del content[subelt][record_id][key]
                # Rename needed keys
                list_keys = sorted(list(content[subelt][record_id]))
                for (patt, repl) in patterns_to_rename:
                    to_rename = [elt for elt in list_keys if patt.match(elt) is not None]
                    if len(to_rename) == 1:
                        content[subelt][record_id][repl] = content[subelt][record_id].pop(to_rename[0])
                    elif len(to_rename) > 1:
                        raise ValueError(f"Several keys ({to_rename}) match pattern {patt} in subelt {subelt}.")
                # Merge needed keys
                list_keys = sorted(list(content[subelt][record_id]))
                for (patt, repl) in patterns_to_merge:
                    to_merge = [elt for elt in list_keys if patt.match(elt) is not None]
                    if len(to_merge) > 0:
                        content[subelt][record_id][repl] = list()
                        for elts in to_merge:
                            if isinstance(content[subelt][record_id][elts], list):
                                content[subelt][record_id][repl].extend(content[subelt][record_id].pop(elts))
                            else:
                                content[subelt][record_id][repl].append(content[subelt][record_id].pop(elts))
                # Add keys if needed
                list_keys = sorted(list(set(content[subelt][record_id])))
                if "name" not in list_keys:
                    content[subelt][record_id]["name"] = "undef"
        # Filter on status if needed then remove linked keys
        variable_groups = set()
        experiment_groups = set()
        variables = set()
        experiments = set()
        subelt = "opportunities"
        for record_id in sorted(list(content[subelt])):
            if content[subelt][record_id].get("status") not in ["Accepted", "Under review", None]:
                del content[subelt][record_id]
            else:
                variable_groups = variable_groups | set(content[subelt][record_id].get("variable_groups", list()))
                experiment_groups = experiment_groups | set(content[subelt][record_id].get("experiment_groups", list()))
        subelt = "variable_groups"
        for record_id in sorted(list(content[subelt])):
            if record_id not in variable_groups:
                del content[subelt][record_id]
            else:
                variables = variables | set(content[subelt][record_id].get("variables", list()))
        subelt = "experiment_groups"
        for record_id in sorted(list(content[subelt])):
            if record_id not in experiment_groups:
                del content[subelt][record_id]
            if content[subelt][record_id].get("status") in ["Junk", ]:
                del content[subelt][record_id]
                for op in list(content["opportunities"]):
                    if record_id in content["opportunities"][op]["experiment_groups"]:
                        content["opportunities"][op]["experiment_groups"].remove(record_id)
            else:
                experiments = experiments | set(content[subelt][record_id].get("experiments", list()))
        subelt = "variables"
        for record_id in sorted(list(set(content[subelt]) - variables)):
            del content[subelt][record_id]
        subelt = "experiments"
        for record_id in sorted(list(set(content[subelt]) - experiments)):
            del content[subelt][record_id]
        for subelt in list(content):
            for record_id in list(content[subelt]):
                for key in [key for key in list(content[subelt][record_id])
                            if re.compile(r".*status.*").match(key) is not None]:
                    del content[subelt][record_id][key]
        # Add uid if needed
        record_to_uid_index = dict()
        for subelt in sorted(list(content)):
            for record_id in sorted(list(content[subelt]),
                                    key=lambda record_id: "|".join([content[subelt][record_id].get("name"),
                                                                    content[subelt][record_id].get("uid", "undef"),
                                                                    record_id])):
                if "uid" not in content[subelt][record_id]:
                    uid = default_template.format(default_count)
                    content[subelt][record_id]["uid"] = uid
                    default_count += 1
                    logger.debug(f"Undefined uid for element {os.sep.join([subelt, 'records', record_id])}, set {uid}")
                uid = content[subelt][record_id].pop("uid")
                record_to_uid_index[record_id] = (uid, subelt)
                content[subelt][uid] = content[subelt].pop(record_id)
        # Replace record_id by uid
        logger.debug("Replace record ids by uids")
        to_remove_entries = defaultdict(list)
        content_string = json.dumps(content)
        for (record_id, (uid, subelt)) in record_to_uid_index.items():
            (content_string, nb) = re.subn(f'"{record_id}"', f'"link::{uid}"', content_string)
            if nb == 0:
                to_remove_entries[subelt].append((record_id, uid))
        content = json.loads(content_string)
        # Remove unused entries
        for subelt in to_remove_entries:
            for (record_id, uid) in to_remove_entries[subelt]:
                del content[subelt][uid]
                del record_to_uid_index[record_id]
        # Tidy the content once again
        content_str = json.dumps(content)
        to_remove_entries = defaultdict(list)
        for (record_id, (uid, subelt)) in record_to_uid_index.items():
            nb = content_str.count(uid)
            if nb < 2:
                to_remove_entries[subelt].append(uid)
        for subelt in to_remove_entries:
            for uid in to_remove_entries[subelt]:
                del content[subelt][uid]
        # Sort content of needed keys
        for subelt in sorted(list(content)):
            patterns_to_sort = to_sort_keys_content.get(subelt, list())
            patterns_to_sort = [re.compile(elt) for elt in patterns_to_sort]
            for uid in sorted(list(content[subelt])):
                # Sort content of needed keys
                list_keys = sorted(list(content[subelt][uid]))
                list_keys_to_sort = [elt for elt in list_keys
                                     if any(patt.match(elt) is not None for patt in patterns_to_sort)]
                for key in list_keys_to_sort:
                    content[subelt][uid][key] = sorted(list(set(content[subelt][uid][key])))
        return content
    else:
        logger.error(f"Deal with dict types, not {type(content).__name__}")
        raise TypeError(f"Deal with dict types, not {type(content).__name__}")


def split_content_one_base(content):
    logger = get_logger()
    data_request = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: dict)))
    keys_to_dr_dict = {
        "opportunities": [("experiment_groups", list, list()),
                          ("variable_groups", list, list()),
                          ("themes", list, list())],
        "variable_groups": [("variables", list, list()),
                            ("mips", list, list()),
                            ("priority_level", (str, type(None)), None)],
        "experiment_groups": [("experiments", list, list()), ]
    }
    if isinstance(content, dict):
        logger.debug("Build DR and VS")
        for subelt in sorted(list(content)):
            if subelt in keys_to_dr_dict:
                for uid in content[subelt]:
                    for (key, target_type, default) in keys_to_dr_dict[subelt]:
                        value = content[subelt][uid].pop(key, default)
                        if not isinstance(value, target_type):
                            if target_type in [list, ] and isinstance(value, (str, int, type(None))):
                                value = [value, ]
                            elif str in target_type and isinstance(value, list):
                                value = value[0]
                            else:
                                raise TypeError(f"Could not deal with target type {type(target_type)}")
                        data_request[subelt][uid][key] = value
        return data_request, content
    else:
        logger.error(f"Deal with dict types, not {type(content).__name__}")
        raise TypeError(f"Deal with dict types, not {type(content).__name__}")


def transform_content(content, version):
    logger = get_logger()
    if isinstance(content, dict):
        # Get back to one database case if needed
        if len(content) == 1:
            logger.info("Single database case - no structure transformation needed")
        elif len(content) in [3, 4]:
            logger.info("Several databases case - structure transformation needed")
            content = transform_content_three_bases(content, version=version)
        else:
            raise ValueError(f"Could not manage the {len(content):d} bases export file.")
        # Correct dictionaries
        content = correct_dictionaries(content)
        # Change several attributes
        content = transform_content_one_base(content)
        # Separate DR and VS files
        data_request, vocabulary_server = split_content_one_base(content)
        data_request["version"] = version
        vocabulary_server["version"] = version
        return data_request, vocabulary_server
    else:
        logger.error(f"Deal with dict types, not {type(content).__name__}")
        raise TypeError(f"Deal with dict types, not {type(content).__name__}")


if __name__ == "__main__":
    change_log_file(default=True)
    change_log_level("debug")
    logger = get_logger()
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", default="dreq_raw_export.json",
                        help="Json file exported from airtable")
    parser.add_argument("--output_files_template", default="request_basic_dump2.json",
                        help="Template to be used for output files")
    parser.add_argument("--version", default="unknown", help="Version of the data used")
    args = parser.parse_args()
    content = read_json_input_file_content(args.input_file)
    data_request, vocabulary_server = transform_content(content, args.version)
    write_json_output_file_content("_".join(["DR", args.output_files_template]), data_request)
    write_json_output_file_content("_".join(["VS", args.output_files_template]), vocabulary_server)
