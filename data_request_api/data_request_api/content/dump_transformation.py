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

from data_request_api.utilities.decorators import append_kwargs_from_config
from data_request_api.utilities.logger import get_logger, change_log_level, change_log_file
from data_request_api.utilities.tools import read_json_input_file_content, write_json_output_file_content
from data_request_api.content import dreq_content as dc


def correct_key_string(input_string, *to_remove_strings):
    """
    Change the input string by replacing '&' by 'and' and spaces by underscores.
    It also removes others specified strings.
    :param str input_string: the input string to be changed
    :param list of str to_remove_strings: the list of strings to be removed from input_string
    :return str: the changed string
    """
    logger = get_logger()
    if isinstance(input_string, str):
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
    """
    Correct the input_dict to correct the strings except the record ids.
    :param dict input_dict: the input dictionary to be corrected
    :param bool is_record_ids: a boolean to indicate whether the keys of input_dict contain record ids or not
    :return dict: the corrected dictionary
    """
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


def get_transform_settings(version):
    def update_dict(elt_1, elt_2):
        rep = copy.deepcopy(elt_1)
        for (elt, value) in elt_2.items():
            if isinstance(value, dict):
                val = rep.get(elt, dict())
                for (subelt, subvalue) in value.items():
                    if isinstance(subvalue, dict):
                        val[subelt] = val.get(subelt, dict())
                        val[subelt].update(subvalue)
                    else:
                        val[subelt] = subvalue
                rep[elt] = val
            elif isinstance(value, list):
                rep[elt] = rep.get(elt, list()) + value
            else:
                rep[elt] = value
        return rep

    transform = read_json_input_file_content(os.sep.join([os.path.dirname(os.path.abspath(__file__)), "transform.json"]))
    common = transform.pop("common", dict())
    if version not in ["default", ]:
        common = update_dict(common["default"], common.get(version, dict()))
    else:
        common = common["default"]
    for (elt, content) in transform.items():
        default_content = update_dict(common, content["default"])
        if version not in ["default", ]:
            default_content = update_dict(default_content, content.get(version, dict()))
        transform[elt] = default_content
    return transform


def distribute_on_entry(func):
    def distribute(content, per_entry_input, **common_inputs):
        for (key, value) in content.items():
            list_args = [value, ]
            if key in per_entry_input:
                list_args.append(per_entry_input[key])
            content[key] = func(*list_args, **copy.deepcopy(common_inputs))
        return content

    return distribute


@distribute_on_entry
def remove_unused_keys(content, patterns_to_remove=list(), default_patterns_to_remove=list()):
    content = content["records"]
    patterns_to_remove.extend(default_patterns_to_remove)
    patterns_to_remove = [re.compile(elt) for elt in patterns_to_remove]
    for record_id in content:
        list_keys_to_remove = [elt for elt in content[record_id]
                               if any(patt.match(elt) is not None for patt in patterns_to_remove)]
        for key in list_keys_to_remove:
            del content[record_id][key]
    return content


@distribute_on_entry
def rename_useful_keys(content, patterns_to_rename=dict()):
    for record_id in content:
        for (patt, repl) in patterns_to_rename.items():
            patt = re.compile(patt)
            to_rename = [elt for elt in content[record_id] if patt.match(elt) is not None]
            if len(to_rename) == 1:
                content[record_id][repl] = content[record_id].pop(to_rename[0])
            elif len(to_rename) > 1:
                raise ValueError(f"Several keys ({to_rename}) match pattern {patt}.")
    return content


@distribute_on_entry
def merge_useful_keys(content, patterns_to_merge=dict()):
    for record_id in content:
        for (patt, repl) in patterns_to_merge.items():
            patt = re.compile(patt)
            to_merge = [elt for elt in content[record_id] if patt.match(elt) is not None]
            if len(to_merge) > 0:
                content[record_id][repl] = list()
                for elts in to_merge:
                    if isinstance(content[record_id][elts], list):
                        content[record_id][repl].extend(content[record_id].pop(elts))
                    else:
                        content[record_id][repl].append(content[record_id].pop(elts))
    return content


@distribute_on_entry
def sort_useful_keys(content, patterns_to_sort=list()):
    patterns_to_sort = [re.compile(elt) for elt in patterns_to_sort]
    for uid in content:
        # Sort content of needed keys
        list_keys_to_sort = [elt for (elt, val) in content[uid].items()
                             if any(patt.match(elt) is not None and isinstance(val, list) for patt in patterns_to_sort)]
        for key in list_keys_to_sort:
            content[uid][key] = sorted(list(set(content[uid][key])))
    return content


@distribute_on_entry
def reshape_useful_keys(content, patterns_to_reshape=list(), reshape_style=None):
    logger = get_logger()
    patterns_to_reshape = [re.compile(elt) for elt in patterns_to_reshape]
    for uid in content:
        list_keys_to_reshape = [elt for elt in content[uid]
                                if any(patt.match(elt) is not None for patt in patterns_to_reshape)]
        for key in list_keys_to_reshape:
            val = content[uid][key]
            if reshape_style in ["list_to_string", ]:
                if isinstance(val, list):
                    if len(val) == 1:
                        content[uid][key] = val[0]
                    elif len(val) == 0:
                        logger.warning(f"Remove void key {key} from id {uid}")
                        del content[uid][key]
                    else:
                        logger.error(f"Could not reshape key {key} from id {uid}: contains several elements")
                        raise ValueError(f"Could not reshape key {key} from id {uid}: contains several elements")
                elif isinstance(val, str):
                    logger.warning(f"Could not reshape key {key} from id {uid}: already a string")
                else:
                    logger.error(f"Could not reshape key {key} from id {uid}: not a list")
                    raise ValueError(f"Could not reshape key {key} from id {uid}: not a list")
            elif reshape_style in ["string_to_list", ]:
                if isinstance(val, str):
                    content[uid][key] = [val, ]
                elif isinstance(val, list):
                    logger.warning(f"Could not reshape key {key} from id {uid}: already a list")
                else:
                    logger.error(f"Could not reshape key {key} from id {uid}: not a string")
                    raise ValueError(f"Could not reshape key {key} from id {uid}: not a string")
            else:
                logger.error(f"Unknown value for reshaping: {reshape_style}")
                raise ValueError(f"Unknown value for reshaping: {reshape_style}")
    return content


def add_useful_keys(content):
    logger = get_logger()
    record_to_uid_index = defaultdict(lambda: dict())
    default_count = 0
    default_template = "default_{:d}"
    list_entries = sorted(list(content))
    for subelt in list_entries:
        list_record_ids = sorted(list(content[subelt]),
                                 key=lambda record_id: "|".join([content[subelt][record_id].get("name", "undef"),
                                                                 content[subelt][record_id].get("uid", "undef"),
                                                                 record_id]))
        for record_id in list_record_ids:
            if "name" not in content[subelt][record_id]:
                content[subelt][record_id]["name"] = "undef"
            if "uid" not in content[subelt][record_id]:
                uid = default_template.format(default_count)
                content[subelt][record_id]["uid"] = uid
                default_count += 1
                logger.debug(f"Undefined uid for element {os.sep.join([subelt, 'records', record_id])}, set {uid}")
            uid = content[subelt][record_id].pop("uid")
            if uid.endswith(os.linesep):
                logger.debug(f"uid of element type {subelt} and record id {record_id} endswith '\\n'.")
                uid = uid.rstrip(os.linesep)
            record_to_uid_index[subelt][record_id] = uid
            content[subelt][uid] = content[subelt].pop(record_id)
    return content, record_to_uid_index


def filter_content(content):
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
        elif content[subelt][record_id].get("status") in ["Junk", ]:
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
    return content


def tidy_content(content, record_to_uid_index):
    logger = get_logger()
    # Replace record_id by uid
    logger.debug("Replace record ids by uids")
    to_remove_entries = defaultdict(lambda: defaultdict(lambda: 0))
    list_content = list(content)
    len_list_content = len(list_content)
    for content_subelt in list_content:
        content_string = json.dumps(content[content_subelt], indent=0)
        for subelt in record_to_uid_index:
            for (record_id, uid) in record_to_uid_index[subelt].items():
                tmp_content_string = content_string.replace(f'"{record_id}"', f'"link::{uid}"')
                if content_string == tmp_content_string:
                    to_remove_entries[subelt][(record_id, uid)] += 1
                content_string = tmp_content_string
        content[content_subelt] = json.loads(content_string)
    for content_subelt in ["opportunities", "coordinates_and_dimensions"]:
        if content_subelt in to_remove_entries:
            to_remove = [elt for (elt, nb) in to_remove_entries[content_subelt].items() if nb == len_list_content]
            for record_id, _ in to_remove:
                del record_to_uid_index[content_subelt][record_id]
            del to_remove_entries[content_subelt]
    for (subelt, to_remove) in to_remove_entries.items():
        to_remove = [elt for (elt, nb) in to_remove.items() if nb == len_list_content]
        for (record_id, uid) in to_remove:
            del content[subelt][uid]
            del record_to_uid_index[subelt][record_id]
    # Tidy the content once again
    content_str = json.dumps(content)
    for subelt in record_to_uid_index:
        for uid in [uid for uid in record_to_uid_index[subelt].values() if content_str.count(uid) < 2]:
            del content[subelt][uid]
    return content


def transform_content_inner(content, settings, change_tables=False):
    """
    Transform a one base export content to:
    - remove unused keys which could create circle import later
    - harmonise some entries
    - reshape entries if needed
    - remove elements which are not used
    - filter content on status
    :param dict content: one base content export (direct export or created from `transform_content_three_bases`
    :return dict: the transform content
    """
    logger = get_logger()
    if isinstance(content, dict) and len(content) == 1 and change_tables:
        logger.error("For one base dict, change_tables must be False.")
        raise ValueError("For one base dict, change_tables must be False.")
    elif isinstance(content, dict) and len(content) > 1 and not change_tables:
        logger.error("For several bases dict, changes_tables must be True.")
        raise ValueError("For several bases dict, changes_tables must be True.")
    elif isinstance(content, dict):
        # If needed, deal with one base creation
        if change_tables:
            new_content = dict()
            for (elt, (base, table)) in settings["tables_provenance"].items():
                new_content[elt] = content[settings["several_bases_name"][base]][table]
            logger.info("Harmonise bases content record ids")
            content_str = json.dumps(new_content)
            for ((base_old, table_old, key_old), (base_new, table_new, key_new)) in settings["several_bases_link"].values():
                old_table = content[settings["several_bases_name"][base_old]][table_old]["records"]
                new_table = content[settings["several_bases_name"][base_new]][table_new]["records"]
                old_dict = {record_id: value[key_old] for (record_id, value) in old_table.items()}
                new_dict = {value[key_new]: record_id for (record_id, value) in new_table.items()}
                for (id, val) in old_dict.items():
                    content_str = content_str.replace(f'"{id}"', f'"{new_dict[val]}"')
            content = json.loads(content_str)
        else:
            content = content[list(content)[0]]
        # Rename some elements
        for (patt, repl) in settings["tables_to_rename"].items():
            for key in [key for key in content if re.compile(patt).match(key) is not None]:
                content[re.sub(patt, repl, key)] = content.pop(key)
        for elt in [elt for elt in list(content) if any(re.compile(patt).match(elt) for patt in settings["tables_to_delete"])]:
            del content[elt]
        # Tidy the content of the export file
        default_patterns_to_remove = settings["default_keys_to_delete"]
        to_remove_keys_patterns = settings["keys_to_delete"]
        to_rename_keys_patterns = settings["keys_to_rename"]
        to_merge_keys_patterns = settings["keys_to_merge"]
        to_sort_keys_content = settings["keys_to_sort"]
        content = remove_unused_keys(content=content, per_entry_input=to_remove_keys_patterns,
                                     default_patterns_to_remove=default_patterns_to_remove)
        content = rename_useful_keys(content=content, per_entry_input=to_rename_keys_patterns)
        content = merge_useful_keys(content=content, per_entry_input=to_merge_keys_patterns)
        # Filter on status if needed then remove linked keys
        content = filter_content(content)
        # Add name and uid if needed, build equivalence dict between record_id and uid
        content, record_to_uid_index = add_useful_keys(content)
        # Tidy the content of the dictionary by removing unused entries
        content = tidy_content(content, record_to_uid_index)
        # Sort content of needed keys
        content = sort_useful_keys(content, per_entry_input=to_sort_keys_content)
        for (reshape_style, from_list_to_string_keys_content) in settings["keys_to_format"].items():
            content = reshape_useful_keys(content, per_entry_input=from_list_to_string_keys_content,
                                          reshape_style=reshape_style)
        return content
    else:
        logger.error(f"Deal with dict types, not {type(content).__name__}")
        raise TypeError(f"Deal with dict types, not {type(content).__name__}")


def split_content_one_base(content):
    """
    Split the one base content into two dictionaries:
    - the DR (structure)
    - the VS (vocabulary server with all information)
    :param dict content: dictionary containing the one base content
    :return dict, dict: two dictionaries containing respectively the DR and VS
    """
    logger = get_logger()
    data_request = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: dict)))
    keys_to_dr_dict = {
        "opportunities": [("experiment_groups", list, list()),
                          ("variable_groups", list, list()),
                          ("data_request_themes", list, list()),
                          ("time_subsets", list, ["80ac3156-a698-11ef-914a-613c0433d878", ]),
                          ("mips", list, list())],
        "variable_groups": [("variables", list, list()),
                            ("mips", list, list()),
                            ("priority_level", (str, type(None)), None)],
        "experiment_groups": [("experiments", list, list()), ]
    }
    if "80ac3156-a698-11ef-914a-613c0433d878" not in content["time_subsets"]:
        content["time_subsets"]["80ac3156-a698-11ef-914a-613c0433d878"] = dict(start=None, end=None, title="Whole time serie", name="all", type="void")
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
    """
    Function to transform the export content (single or several base-s- export) to VS and DR dictionaries.
    The key "version" is added to the DR and VS dictionaries.
    :param dict content: input export content (either single base or several bases)
    :param str version: string containing the version of the export content
    :return dict, dict: DR and VS dictionaries containing respectively the structure (DR) and the vocabulary (VS)
    """
    logger = get_logger()
    if "Data Request" in content:
        content["Data Request"].pop("version", None)
    transform_settings = get_transform_settings(version)
    if isinstance(content, dict):
        # Correct dictionaries
        content = correct_dictionaries(content)
        # Get back to one database case if needed
        if len(content) == 1:
            logger.info("Single database case - no structure transformation needed")
            content = transform_content_inner(content, transform_settings["one_to_transform"])
        elif len(content) in [3, 4]:
            logger.info("Several databases case - structure transformation needed")
            content = transform_content_inner(content, transform_settings["several_to_transform"], change_tables=True)
        else:
            raise ValueError(f"Could not manage the {len(content):d} bases export file.")
        # Separate DR and VS files
        data_request, vocabulary_server = split_content_one_base(content)
        data_request["version"] = version
        vocabulary_server["version"] = version
        return data_request, vocabulary_server
    else:
        logger.error(f"Deal with dict types, not {type(content).__name__}")
        raise TypeError(f"Deal with dict types, not {type(content).__name__}")


@append_kwargs_from_config
def get_transformed_content(version="latest_stable", export="release", consolidate=False,
                            force_retrieve=False, output_dir=None,
                            default_transformed_content_pattern="{kind}_{export_version}_content.json", **kwargs):
    # Download specified version of data request content (if not locally cached)
    versions = dc.retrieve(version, export=export, consolidate=consolidate, **kwargs)

    # Check that there is only one version associated
    if len(versions) > 1:
        raise ValueError("Could only deal with one version.")
    elif len(versions) == 0:
        raise ValueError("No version found.")
    else:
        version = list(versions)[0]
        content = versions[version]
        if output_dir is None:
            output_dir = os.path.dirname(content)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        DR_content = default_transformed_content_pattern.format(kind="DR", export_version=export)
        VS_content = default_transformed_content_pattern.format(kind="VS", export_version=export)
        DR_content = os.sep.join([output_dir, DR_content])
        VS_content = os.sep.join([output_dir, VS_content])
        if force_retrieve or not (all(os.path.exists(filepath) for filepath in [DR_content, VS_content])):
            if os.path.exists(DR_content):
                os.remove(DR_content)
            if os.path.exists(VS_content):
                os.remove(VS_content)
        if not (all(os.path.exists(filepath) for filepath in [DR_content, VS_content])):
            content = dc.load(version, export=export, consolidate=consolidate)
            data_request, vocabulary_server = transform_content(content, version)
            write_json_output_file_content(DR_content, data_request)
            write_json_output_file_content(VS_content, vocabulary_server)
        return dict(DR_input=DR_content, VS_input=VS_content)


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
