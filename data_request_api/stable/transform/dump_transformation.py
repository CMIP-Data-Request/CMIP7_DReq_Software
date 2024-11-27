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


def correct_dictionaries(input_dict):
    logger = get_logger()
    if isinstance(input_dict, dict):
        rep = dict()
        for (key, value) in input_dict.items():
            new_key = correct_key_string(key)
            if isinstance(value, dict):
                for elt in value:
                    if isinstance(value[elt], dict):
                        value[elt] = correct_dictionaries(value[elt])
                rep[new_key] = value
            else:
                rep[new_key] = copy.deepcopy(value)
    else:
        logger.error(f"Deal with dict types, not {type(input_dict).__name__}")
        raise TypeError(f"Deal with dict types, not {type(input_dict).__name__}")
    return rep


def transform_content_one_base(content):
    logger = get_logger()
    if isinstance(content, dict):
        default_count = 0
        default_template = "default_{:d}"
        # Tidy the content of the export file
        content = content[list(content)[0]]
        data_request = dict()
        vocabulary_server = dict()
        to_remove_keys = {
            "CF Standard Names": ["Physical Parameters", "Physical Parameters 2"],
            "Cell Measures": ["Variables", ],
            "Cell Methods": ["Structures", "Variables"],
            "Coordinates and Dimensions": ["Structure", "Variables"],
            "Experiment Group": ["Opportunity", ],
            "Experiments": ["Experiment Group", ],
            "Frequency": ["Table Identifiers", "Variables"],
            "CMIP7 Frequency": ["Table Identifiers", "Variables"],
            "Glossary": ["Opportunity", ],
            "MIPs": ["Variable Group", "Variable Groups of interest", "Variable Groups", "Variable Group of interest"],
            "Modelling Realm": ["Variables", ],
            "Opportunity": list(),
            "Opportunity/Variable Group Comments": ["Experiment Groups", "Opportunities", "Theme", "Variable Groups"],
            "Physical Parameters Comments": ["Physical parameters", ],
            "Physical Parameters": ["Variables", ],
            "Priority Level": ["Variable Group", ],
            "Ranking": list(),
            "Spatial Shape": ["Dimensions", "Structure", "Variables"],
            "Structure": ["Variables", ],
            "Table Identifiers": ["Variables", ],
            "Temporal Shape": ["Dimensions", "Structure", "Variables"],
            "Variable Comments": ["Variables", ],
            "Variable Group": ["Opportunity", "Theme"],
            "Variables": ["CMIP7 Variable Groups", ]
        }
        record_to_uid_index = dict()
        for subelt in sorted(list(content)):
            for record_id in sorted(list(content[subelt]["records"])):
                if subelt in to_remove_keys:
                    keys_to_remove = copy.deepcopy(to_remove_keys[subelt])
                else:
                    keys_to_remove = list()
                list_keys = list(content[subelt]["records"][record_id])
                keys_to_remove.extend([key for key in list_keys if "(MJ)" in key or "test" in key.lower() or
                                       ("last" in key.lower() and "modified" in key.lower()) or "count" in key.lower()])
                for key in set(keys_to_remove) & set(list_keys):
                    del content[subelt]["records"][record_id][key]
                if "UID" in list_keys:
                    content[subelt]["records"][record_id]["uid"] = content[subelt]["records"][record_id].pop("UID")
                elif "uid" not in list_keys:
                    uid = default_template.format(default_count)
                    content[subelt]["records"][record_id]["uid"] = uid
                    default_count += 1
                    logger.debug(f"Undefined uid for element {os.sep.join([subelt, 'records', record_id])}, set {uid}")
                record_to_uid_index[record_id] = content[subelt]["records"][record_id].pop("uid")
                if subelt in ["Opportunity", ] and "Title of Opportunity" in list_keys:
                    content[subelt]["records"][record_id]["name"] = content[subelt]["records"][record_id].pop("Title of Opportunity")
                elif "name" not in list_keys and "Name" not in list_keys:
                    content[subelt]["records"][record_id]["name"] = "undef"
        # Replace record_id by uid
        logger.debug("Replace record ids by uids")
        content_string = json.dumps(content)
        for (record_id, uid) in record_to_uid_index.items():
            content_string = content_string.replace(f'"{record_id}"', f'"{uid}"')
        content = json.loads(content_string)
        # Build the data request
        logger.debug("Build DR and VS")
        for subelt in sorted(list(content)):
            if subelt in ["Opportunity", ]:
                new_subelt = "opportunities"
                data_request[new_subelt] = dict()
                vocabulary_server[new_subelt] = dict()
                for uid in content[subelt]["records"]:
                    value = copy.deepcopy(content[subelt]["records"][uid])
                    data_request[new_subelt][uid] = dict(
                        experiments_groups=value.pop("Experiment Groups", list()),
                        variables_groups=value.pop("Variable Groups", list()),
                        themes=value.pop("Themes", list())
                    )
                    vocabulary_server[new_subelt][uid] = value
            elif subelt in ["Variable Group", ]:
                new_subelt = "variables_groups"
                data_request[new_subelt] = dict()
                vocabulary_server[new_subelt] = dict()
                for uid in content[subelt]["records"]:
                    value = copy.deepcopy(content[subelt]["records"][uid])
                    data_request[new_subelt][uid] = dict(
                        variables=value.pop("Variables", list()),
                        mips=value.pop("MIPs", value.pop("Of interest to MIPs", list())),
                        priority=value.pop("Priority Level", None)
                    )
                    vocabulary_server[new_subelt][uid] = value
            elif subelt in ["Experiment Group", ]:
                new_subelt = "experiments_groups"
                data_request[new_subelt] = dict()
                vocabulary_server[new_subelt] = dict()
                for uid in content[subelt]["records"]:
                    value = copy.deepcopy(content[subelt]["records"][uid])
                    data_request[new_subelt][uid] = dict(
                        experiments=value.pop("Experiments", list())
                    )
                    vocabulary_server[new_subelt][uid] = value
            else:
                vocabulary_server[subelt] = copy.deepcopy(content[subelt]["records"])
        return data_request, vocabulary_server
    else:
        logger.error(f"Deal with dict types, not {type(content).__name__}")
        raise TypeError(f"Deal with dict types, not {type(content).__name__}")


def transform_content_three_bases(content):
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
        for elt in list(content[opportunity_table]):
            new_content[elt] = content[opportunity_table].pop(elt)
        new_content["Variables"] = content[variables_table].pop("Variable")
        new_content["Coordinates and Dimensions"] = content[variables_table].pop("Coordinate or Dimension")
        new_content["Variable Comments"] = content[variables_table].pop("Comment")
        for elt in list(content[variables_table]):
            new_content[elt] = content[variables_table].pop(elt)
        new_content["Physical Parameters Comments"] = content[physical_parameters_table].pop("Comment")
        new_content["Physical Parameters"] = content[physical_parameters_table].pop("Physical Parameter")
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
        # Rename some entries
        for record_id in list(new_content["Cell Methods"]["records"]):
            if "Structure" in new_content["Cell Methods"]["records"][record_id]:
                new_content["Cell Methods"]["records"][record_id]["Structures"] = \
                    new_content["Cell Methods"]["records"][record_id].pop("Structure")
            if "Comments" in new_content["Cell Methods"]["records"][record_id]:
                new_content["Cell Methods"]["records"][record_id]["Variable Comments"] = \
                    new_content["Cell Methods"]["records"][record_id].pop("Comments")
        # Create a new frequency entry if none
        if "Frequency" not in new_content:
            new_content["Frequency"] = dict(records=dict())
            for var_id in new_content["Variables"]["records"]:
                for frequency_id in copy.deepcopy(new_content["Variables"]["records"][var_id]["Frequency"]):
                    if frequency_id not in new_content["Frequency"]["records"]:
                        new_content["Frequency"]["records"][frequency_id] = dict(name=frequency_id, uid=frequency_id)
        if "Data Request Themes" not in new_content:
            new_content["Data Request Themes"] = dict(records=dict())
            for opportunity_id in new_content["Opportunity"]["records"]:
                for theme_id in copy.deepcopy(new_content["Opportunity"]["records"][opportunity_id]["Themes"]):
                    if theme_id not in new_content["Data Request Themes"]["records"]:
                        new_content["Data Request Themes"]["records"][theme_id] = dict(name=theme_id, uid=theme_id)
        # Make one base transformation
        return transform_content_one_base({0: new_content})
    else:
        logger.error(f"Deal with dict types, not {type(content).__name__}")
        raise TypeError(f"Deal with dict types, not {type(content).__name__}")


def transform_content(content, version):
    logger = get_logger()
    if isinstance(content, dict):
        if len(content) == 1:
            data_request, vocabulary_server = transform_content_one_base(content)
        elif len(content) in [3, 4]:
            data_request, vocabulary_server = transform_content_three_bases(content)
        else:
            raise ValueError(f"Could not manage the {len(content):d} bases export file.")
        data_request["version"] = version
        vocabulary_server["version"] = version
        data_request = correct_dictionaries(data_request)
        vocabulary_server = correct_dictionaries(vocabulary_server)
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
