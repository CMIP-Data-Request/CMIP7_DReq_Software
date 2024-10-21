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

from logger import get_logger, change_log_level, change_log_file

default_count = 0
default_template = "default_{:d}"


def read_json_file(filename):
    if os.path.isfile(filename):
        with open(filename, "r") as fic:
            content = json.load(fic)
    else:
        raise OSError(f"Filename {filename} is not readable")
    return content


def read_json_input_file_content(filename):
    content = read_json_file(filename)
    return content


def write_json_output_file_content(filename, content):
    with open(filename, "w") as fic:
        json.dump(content, fic, indent=4, allow_nan=True, sort_keys=True)


def correct_key_string(input_string, *to_remove_strings):
    logger = get_logger()
    input_string = input_string.lower()
    for to_remove_string in to_remove_strings:
        input_string = input_string.replace(to_remove_string, "")
    input_string = input_string.strip()
    input_string = input_string.replace("&", "and").replace(" ", "_")
    return input_string


def correct_dictionaries(input_dict):
    rep = dict()
    for (key, value) in input_dict.items():
        new_key = correct_key_string(key)
        if isinstance(value, dict) and key not in ["records", ]:
            rep[new_key] = correct_dictionaries(value)
        elif isinstance(value, dict):
            for elt in value:
                value[elt] = correct_dictionaries(value[elt])
            rep[new_key] = value
        else:
            rep[new_key] = copy.deepcopy(value)
    return rep


def transform_content(content):
    logger = get_logger()
    global default_count
    # Tidy the content of the export file
    data_request = dict()
    vocabulary_server = dict()
    to_remove_keys = {
        "CF Standard Names": ["Physical Parameters", ],
        "Cell Measures": ["Variables", ],
        "Cell Methods": ["Structures", "Variables"],
        "Coordinates and Dimensions": ["Structure", "Variables"],
        "Experiment Group": ["Opportunity", ],
        "Experiments": ["Experiment Group", ],
        "Frequency": ["Table Identifiers", "Variables"],
        "Glossary": ["Opportunity", ],
        "MIPs": ["Variable Group", ],
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
    for elt in sorted(list(content)):
        for subelt in sorted(list(content[elt])):
            for record_id in sorted(list(content[elt][subelt]["records"])):
                if subelt in to_remove_keys:
                    keys_to_remove = copy.deepcopy(to_remove_keys[subelt])
                else:
                    keys_to_remove = list()
                list_keys = list(content[elt][subelt]["records"][record_id])
                keys_to_remove.extend([key for key in list_keys if "(MJ)" in key or "test" in key.lower() or
                                       ("last" in key.lower() and "modified" in key.lower()) or "count" in key.lower()])
                for key in set(keys_to_remove) & set(list_keys):
                    del content[elt][subelt]["records"][record_id][key]
                if "UID" in list_keys:
                    content[elt][subelt]["records"][record_id]["uid"] = content[elt][subelt]["records"][record_id].pop("UID")
                elif "uid" not in list_keys:
                    uid = default_template.format(default_count)
                    content[elt][subelt]["records"][record_id]["uid"] = uid
                    default_count += 1
                    logger.debug(f"Undefined uid for element {os.sep.join([elt, subelt, 'records', record_id])}, set {uid}")
                record_to_uid_index[record_id] = content[elt][subelt]["records"][record_id].pop("uid")
                if subelt in ["Opportunity", ] and "Title of Opportunity" in list_keys:
                    content[elt][subelt]["records"][record_id]["name"] = content[elt][subelt]["records"][record_id].pop("Title of Opportunity")
                elif "name" not in list_keys and "Name" not in list_keys:
                    content[elt][subelt]["records"][record_id]["name"] = "undef"
    # Replace record_id by uid
    logger.debug("Replace record ids by uids")
    content_string = json.dumps(content)
    for (record_id, uid) in record_to_uid_index.items():
        content_string = content_string.replace(f'"{record_id}"', f'"{uid}"')
    content = json.loads(content_string)
    # Build the data request
    logger.debug("Build DR and VS")
    for elt in sorted(list(content)):
        for subelt in sorted(list(content[elt])):
            if subelt in ["Opportunity", ]:
                new_subelt = "opportunities"
                data_request[new_subelt] = dict()
                vocabulary_server[new_subelt] = dict()
                for uid in content[elt][subelt]["records"]:
                    value = copy.deepcopy(content[elt][subelt]["records"][uid])
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
                for uid in content[elt][subelt]["records"]:
                    value = copy.deepcopy(content[elt][subelt]["records"][uid])
                    data_request[new_subelt][uid] = dict(
                        variables=value.pop("Variables", list()),
                        mips=value.pop("MIPs", list()),
                        priority=value.pop("Priority Level", None)
                    )
                    vocabulary_server[new_subelt][uid] = value
            elif subelt in ["Experiment Group", ]:
                new_subelt = "experiments_groups"
                data_request[new_subelt] = dict()
                vocabulary_server[new_subelt] = dict()
                for uid in content[elt][subelt]["records"]:
                    value = copy.deepcopy(content[elt][subelt]["records"][uid])
                    data_request[new_subelt][uid] = dict(
                        experiments=value.pop("Experiments", list())
                    )
                    vocabulary_server[new_subelt][uid] = value
            else:
                vocabulary_server[subelt] = copy.deepcopy(content[elt][subelt]["records"])
    version = list(content)[0].replace("Data Request", "").strip()
    data_request["version"] = version
    vocabulary_server["version"] = version
    data_request = correct_dictionaries(data_request)
    vocabulary_server = correct_dictionaries(vocabulary_server)
    return data_request, vocabulary_server


if __name__ == "__main__":
    change_log_file(default=True)
    change_log_level("debug")
    logger = get_logger()
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", default="dreq_raw_export.json",
                        help="Json file exported from airtable")
    parser.add_argument("--output_files_template", default="request_basic_dump2.json",
                        help="Template to be used for output files")
    args = parser.parse_args()
    content = read_json_input_file_content(args.input_file)
    data_request, vocabulary_server = transform_content(content)
    write_json_output_file_content("_".join(["DR", args.output_files_template]), data_request)
    write_json_output_file_content("_".join(["VS", args.output_files_template]), vocabulary_server)
