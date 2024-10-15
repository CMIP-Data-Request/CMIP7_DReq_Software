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


def correct_DR_dictionary(input_dict):
    logger = get_logger()
    for elt in input_dict:
        for subelt in set(list(input_dict[elt])) - set(["name", 'description', 'records']):
            del input_dict[elt][subelt]
        for subelt in input_dict[elt]["records"]:
            status = dict()
            if "Status" in input_dict[elt]["records"][subelt]:
                status["general"] = input_dict[elt]["records"][subelt]["Status"]
                del input_dict[elt]["records"][subelt]["Status"]
            for key in [key for key in input_dict[elt]["records"][subelt] if "review" in key]:
                new_key = key.replace("author_team_review", "").replace("author_review_status", "").replace("review", "").strip("_").strip()
                status[new_key] = input_dict[elt]["records"][subelt][key]
                del input_dict[elt]["records"][subelt][key]
            for key in [key for key in status if "comments" in key]:
                new_key = key.replace("comments", "").strip("_")
                value = status.pop(key)
                value = value.strip(os.linesep)
                if new_key in status:
                    status[new_key] += f" with comments: {value}"
                else:
                    status[new_key] = f"New with comments: {value}"
            input_dict[elt]["records"][subelt]["status"] = copy.deepcopy(status)
            for subsubelt in [key for key in list(input_dict[elt]["records"][subelt]) if key.startswith("title")]:
                input_dict[elt]["records"][subelt]["title"] = input_dict[elt]["records"][subelt].pop(subsubelt)
            for subsubelt in [key for key in list(input_dict[elt]["records"][subelt]) if key.startswith("priority")]:
                input_dict[elt]["records"][subelt]["priority"] = input_dict[elt]["records"][subelt].pop(subsubelt)
    for elt in input_dict["opportunity"]["records"]:
        to_keep_entries = ["description", "status", "experiment_groups", "themes", "title",
                           "variable_groups", "lead_theme", "comments"]
        if len(input_dict["opportunity"]["records"][elt]) > 0:
            for subelt in set(list(input_dict["opportunity"]["records"][elt])) - set(to_keep_entries):
                del input_dict["opportunity"]["records"][elt][subelt]
            for subelt in to_keep_entries:
                logger.debug(f"Miss entry {subelt} in opportunity {elt}.")
            input_dict["opportunity"]["records"][elt]["name"] = input_dict["opportunity"]["records"][elt].pop("title", "???")
        else:
            logger.debug(f"Remove void opportunity {elt}.")
            del input_dict["opportunity"]["records"][elt]
    for elt in input_dict["experiment_group"]["records"]:
        to_keep_entries = ["status", "comments", "experiments", "name"]
        for subelt in set(list(input_dict["experiment_group"]["records"][elt])) - set(to_keep_entries):
            del input_dict["experiment_group"]["records"][elt][subelt]
        for subelt in to_keep_entries:
            logger.debug(f"Miss entry {subelt} in experiment group {elt}.")
    for elt in input_dict["variable_group"]["records"]:
        input_dict["variable_group"]["records"][elt]["description"] = input_dict["variable_group"]["records"][elt].get("justification")
        to_keep_entries = ["status", "comments", "variables", "name", "title", "mips", "priority", "description"]
        for subelt in set(list(input_dict["variable_group"]["records"][elt])) - set(to_keep_entries):
            del input_dict["variable_group"]["records"][elt][subelt]
        for subelt in to_keep_entries:
            logger.debug(f"Miss entry {subelt} in variable group {elt}.")
    return input_dict


def transform_content(content):
    data_request = dict()
    for elt in list(content):
        for subelt in list(content[elt]):
            if subelt in ["Opportunity", "Variable Group", "Experiment Group"]:
                data_request[subelt] = copy.deepcopy(content[elt][subelt])
                del content[elt][subelt]
    data_request = correct_dictionaries(data_request)
    data_request = correct_DR_dictionary(data_request)
    content = correct_dictionaries(content)
    return data_request, content


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
