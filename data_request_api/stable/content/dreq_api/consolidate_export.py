import json
import os
import re
import warnings

from data_request_api.stable.utilities.logger import get_logger  # noqa
from data_request_api.stable.content.dreq_api.mapping_table import version_consistency

# UID generation
default_count = 0
default_template = "default_{:d}"

# Filtered records
filtered_records = []


def _correct_key_string(input_string, *to_remove_strings):
    """
    Corrects a string by removing certain strings, stripping, and replacing some characters.

    Parameters
    ----------
    input_string : str
        The string to be corrected
    *to_remove_strings : str
      The strings to be removed from the input string

    Returns
    -------
    str
        The corrected string
    """
    # Convert the input string to lowercase
    input_string = input_string.lower()
    # Remove the specified strings from the input string
    for to_remove_string in to_remove_strings:
        input_string = input_string.replace(to_remove_string, "")
    # Strip leading and trailing whitespace from the input string
    input_string = input_string.strip()
    # Replace '&' with 'and' and ' ' with '_' in the input string
    input_string = input_string.replace("&", "and").replace(" ", "_")
    return input_string


def _correct_dictionaries(input_dict):
    """
    Corrects the keys in a dictionary.
    """
    rep = dict()
    for key, value in input_dict.items():
        # Correct the key using the correct_key_string function
        new_key = _correct_key_string(key)
        # If the value is a dictionary, recursively correct its keys
        if isinstance(value, dict):
            for elt in value:
                value[elt] = _correct_dictionaries(value[elt])
            rep[new_key] = value
        # If the value is not a dictionary, simply assign it to the corrected key
        else:
            rep[new_key] = value
    return rep


def _map_record_id(record, records, keys):
    """
    Identifies a record_id in list of records using key.
    """
    global filtered_records
    matches = []
    # For each of the specified "keys", check if there is an entry in "records" that matches with "record"
    for key in keys:
        if key in record:
            recval = record[key]
            matches_tmp = [
                r for r, v in records.items() if key in v and v[key] == recval
            ]
            matches = [m for m in matches_tmp if m not in filtered_records]
            if len(matches) == 1:
                break
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        if len(matches_tmp) == 0:
            raise KeyError(f"No matches when consolidating '{record}' via '{keys}'.")
    else:
        raise KeyError(f"Multiple matches when consolidating '{record}'.")


def _map_attribute(attr, records, key):
    """
    Identifies a record_id in list of records using key and matching with the attribute value.
    """
    global filtered_records
    # For the specified "key", check if there is an entry in "records" that matches with "attr"
    matches_tmp = [r for r, v in records.items() if key in v and v[key] == attr]
    matches = [m for m in matches_tmp if m not in filtered_records]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        if len(matches_tmp) == 0:
            raise KeyError(f"No matches when consolidating '{attr}' via '{key}'.")
    else:
        raise KeyError(f"Multiple matches when consolidating '{attr}' via '{key}'.")


def map_data(data, mapping_table):
    """
    Maps the data to the one-base structure using the mapping table.

    Parameters
    ----------
    data : dict
        Three-base or one-base Airtable export.
    mapping_table dict
        The mapping table to apply to map to one base.

    Returns
    -------
    dict
        Mapped data with one-base structure.

    Note
    ----
        Returns the input dict if the data is already one-base.
    """
    logger = get_logger()
    missing_bases = []
    missing_tables = []
    mapped_data = {"Data Request": {}}

    # Reset filtered records
    global filtered_records
    if filtered_records:
        filtered_records = []

    if len(data.keys()) in [3, 4]:

        # Get filtered records
        for table, mapinfo in mapping_table.items():
            if (
                mapinfo["source_base"] in data
                and mapinfo["source_table"] in data[mapinfo["source_base"]]
            ):
                if "internal_filters" in mapinfo:
                    for record_id, record in data[mapinfo["source_base"]][
                        mapinfo["source_table"]
                    ]["records"].items():
                        filter_results = []
                        for filter_key, filter_val in mapinfo[
                            "internal_filters"
                        ].items():
                            if filter_key not in record:
                                filter_results.append(False)
                            elif filter_val["operator"] == "nonempty":
                                filter_results.append(bool(record[filter_key]))
                            elif filter_val["operator"] == "in":
                                if isinstance(record[filter_key], list):
                                    filter_results.append(
                                        any(
                                            fj in filter_val["values"]
                                            for fj in record[filter_key]
                                        )
                                    )
                                else:
                                    filter_results.append(
                                        record[filter_key] in filter_val["values"]
                                    )
                            elif filter_val["operator"] == "not in":
                                if isinstance(record[filter_key], list):
                                    filter_results.append(
                                        any(
                                            fj not in filter_val["values"]
                                            for fj in record[filter_key]
                                        )
                                    )
                                else:
                                    filter_results.append(
                                        record[filter_key] not in filter_val["values"]
                                    )
                        if not all(filter_results):
                            logger.debug(
                                f"Filtered out record '{record_id}' {'('+record['name']+')' if 'name' in record else ''} from '{table}'."
                            )
                            filtered_records.append(record_id)
        logger.info(f"Filtered {len(filtered_records)} records.")

        # Perform mapping in case of three-base structure
        for table, mapinfo in mapping_table.items():
            intm = mapinfo["internal_mapping"]
            if (
                mapinfo["source_base"] in data
                and mapinfo["source_table"] in data[mapinfo["source_base"]]
            ):
                # Copy the selected data to the one-base structure
                logger.debug(f"Mapping '{mapinfo['source_base']}' -> '{table}'")
                mapped_data["Data Request"][table] = {
                    **data[mapinfo["source_base"]][mapinfo["source_table"]],
                    "records": {
                        record_id: record
                        for record_id, record in data[mapinfo["source_base"]][
                            mapinfo["source_table"]
                        ]["records"].items()
                        if record_id not in filtered_records
                    },
                }

                # If record attributes require mapping
                if intm != {}:
                    # for each attribute that requires mapping
                    for attr in intm.keys():
                        for record_id, record in data[mapinfo["source_base"]][
                            mapinfo["source_table"]
                        ]["records"].items():
                            if (
                                attr not in record
                                or record[attr] is None
                                or record[attr] == ""
                                or record[attr] == []
                            ):
                                logger.debug(
                                    f"{table}: Attribute '{attr}' not found for record '{record_id}'."
                                )
                                continue
                            attr_vals = record[attr]

                            # operation
                            if intm[attr]["operation"] == "split":
                                attr_vals = re.split(r"\s*,\s*", attr_vals)
                            elif intm[attr]["operation"] == "":
                                if isinstance(attr_vals, str):
                                    attr_vals = [attr_vals]
                            else:
                                raise ValueError(
                                    f"Unknown internal mapping operation for attribute '{attr}' ('{mapinfo['source_table']}'): '{intm[attr]['operation']}'"
                                )

                            # Get mapped record_ids
                            # entry_type - single record_id or list of record_ids
                            # - map by record_id
                            if intm[attr]["entry_type"] == "record_id":
                                if not intm[attr]["base_copy_of_table"]:
                                    raise ValueError(
                                        "A copy of the table in the same base is required if 'entry_type' is set to 'record_id', "
                                        f"but 'base_copy_of_table' is set to False: '{mapinfo['source_table']}' - '{attr}'"
                                    )
                                elif not intm[attr]["base"] in data:
                                    raise KeyError(
                                        f"Base '{intm[attr]['base']}' not found in data."
                                    )
                                elif (
                                    intm[attr]["base_copy_of_table"]
                                    not in data[mapinfo["source_base"]]
                                ):
                                    raise KeyError(
                                        f"Table '{intm[attr]['table']}' not found in base '{intm[attr]['base_copy']}'."
                                    )
                                recordIDs_new = []
                                for attr_val in attr_vals:
                                    # The record copy in the current base
                                    record_copy = data[mapinfo["source_base"]][
                                        intm[attr]["base_copy_of_table"]
                                    ]["records"][attr_val]
                                    # The entire list of records in the base of origin
                                    recordlist = data[intm[attr]["base"]][
                                        intm[attr]["table"]
                                    ]["records"]
                                    recordID_new = _map_record_id(
                                        record_copy,
                                        recordlist,
                                        intm[attr]["map_by_key"],
                                    )
                                    if recordID_new:
                                        recordIDs_new.append(recordID_new)
                            # entry_type - name (eg. unique label or similar)
                            # - map by attribute value
                            elif intm[attr]["entry_type"] == "name":
                                recordIDs_new = []
                                for attr_val in attr_vals:
                                    recordID_new = _map_attribute(
                                        attr_val,
                                        data[intm[attr]["base"]][intm[attr]["table"]][
                                            "records"
                                        ],
                                        (
                                            intm[attr]["map_by_key"]
                                            if isinstance(intm[attr]["map_by_key"], str)
                                            else intm[attr]["map_by_key"][0]
                                        ),
                                    )
                                    if recordID_new:
                                        recordIDs_new.append(recordID_new)
                            else:
                                raise ValueError(
                                    f"Unknown 'entry_type' specified for attribute '{attr}' ('{mapinfo['source_table']}'): '{intm[attr]['entry_type']}'"
                                )
                            if not recordIDs_new:
                                raise KeyError(
                                    f"{table} (record '{record_id}'): For attribute '{attr}' no records could be mapped."
                                )
                            mapped_data["Data Request"][table]["records"][record_id][
                                attr
                            ] = recordIDs_new

            else:
                if mapinfo["source_base"] not in data:
                    missing_tables.append(mapinfo["source_base"])
                elif mapinfo["source_table"] not in data[mapinfo["source_base"]]:
                    missing_bases.append(mapinfo["source_table"])
        if len(missing_bases) > 0:
            warnings.warn(
                f"Encountered missing bases when consolidating the data: {set(missing_bases)}"
            )
        if len(missing_tables) > 0:
            warnings.warn(
                f"Encountered missing tables when consolidating the data: {missing_tables}"
            )
        return mapped_data
    # Return the data if it is already one-base
    elif len(data.keys()) == 1:
        version = next(iter(data.keys())).replace("Data Request ", "")
        mapped_data = next(iter(data.values()))
        if version in version_consistency:
            for tfrom, tto in version_consistency[version].items():
                logger.debug(
                    f"Consistency across versions - renaming table: {tfrom} -> {tto}"
                )
                mapped_data[tto] = mapped_data.pop(tfrom)
        return {"Data Request": mapped_data}
    else:
        raise ValueError("The loaded Data Request has an unexpected data structure.")


def transform_content(data):
    """
    Transform the data request content into a tidy format.

    This function takes the data request content as input, tidies it up by removing
    unnecessary keys and renaming others, and returns the transformed data request
    and vocabulary server.

    Parameters:
    data (dict): The data request content to be transformed.

    Returns:
    tuple: A tuple containing the transformed data request and vocabulary server.
    """
    logger = get_logger()
    global default_count

    # Create an index to map record IDs to UIDs
    record_to_uid_index = dict()
    # Separate dreq and vocabulary information
    data_request = dict()
    vocabulary_server = dict()
    # Get the content of the Data Request
    content = data["Data Request"]

    # Define the keys to remove from each table
    to_remove_keys = {}

    # Iterate over each table in the content
    for subelt in sorted(list(content)):
        for record_id in sorted(list(content[subelt]["records"])):
            # Get the keys to remove for this table
            if subelt in to_remove_keys:
                keys_to_remove = to_remove_keys[subelt]
            else:
                keys_to_remove = list()

            # Get the list of keys for this record
            list_keys = list(content[subelt]["records"][record_id])

            # Add keys that match certain patterns to the list of keys to remove
            keys_to_remove.extend(
                [
                    key
                    for key in list_keys
                    if "(MJ)" in key
                    or "test" in key.lower()
                    or ("last" in key.lower() and "modified" in key.lower())
                    or "count" in key.lower()
                ]
            )

            # Remove the keys that should be removed
            for key in set(keys_to_remove) & set(list_keys):
                del content[subelt]["records"][record_id][key]

            # Rename the "UID" key to "uid" if it exists
            if "UID" in list_keys:
                content[subelt]["records"][record_id]["uid"] = content[subelt][
                    "records"
                ][record_id].pop("UID")
            elif "uid" not in list_keys:
                # If no "uid" key exists, create a default one
                uid = default_template.format(default_count)
                content[subelt]["records"][record_id]["uid"] = uid
                default_count += 1
                logger.debug(
                    f"Undefined uid for element {os.sep.join([subelt, 'records', record_id])}, set {uid}"
                )

            # Add the record ID to UID mapping to the index
            record_to_uid_index[record_id] = content[subelt]["records"][record_id][
                "uid"
            ]
            if (
                subelt
                in [
                    "Opportunity",
                ]
                and "Title of Opportunity" in list_keys
            ):
                content[subelt]["records"][record_id]["name"] = content[subelt][
                    "records"
                ][record_id].pop("Title of Opportunity")
            elif "name" not in list_keys and "Name" not in list_keys:
                content[subelt]["records"][record_id]["name"] = "undef"

    # Replace record_id by uid
    logger.debug("Replace record ids by uids")
    content_string = json.dumps(content)
    for record_id, uid in record_to_uid_index.items():
        content_string = content_string.replace(f'"{record_id}"', f'"{uid}"')
    content = json.loads(content_string)

    # Alternative
    # for key, value in content.items():
    #    if isinstance(value, dict):
    #        content[key] = {record_to_uid_index.get(k, k): v for k, v in value.items()}
    #    elif isinstance(value, list):
    #        content[key] = [{record_to_uid_index.get(k, k): v for k, v in item.items()} if isinstance(item, dict) else item for item in value]

    # Build the data request
    logger.debug("Build DR and VS")
    for subelt in sorted(list(content)):
        if subelt in [
            "Opportunity",
        ]:
            new_subelt = "opportunities"
            data_request[new_subelt] = dict()
            vocabulary_server[new_subelt] = dict()
            for uid in content[subelt]["records"]:
                value = content[subelt]["records"][uid]
                data_request[new_subelt][uid] = dict(
                    experiments_groups=value.pop("Experiment Groups", list()),
                    variables_groups=value.pop("Variable Groups", list()),
                    themes=value.pop("Themes", list()),
                    ensemble_size=value.pop("Ensemble Size", 1),
                )
                vocabulary_server[new_subelt][uid] = value
        elif subelt in [
            "Variable Group",
        ]:
            new_subelt = "variable_groups"
            data_request[new_subelt] = dict()
            vocabulary_server[new_subelt] = dict()
            for uid in content[subelt]["records"]:
                value = content[subelt]["records"][uid]
                data_request[new_subelt][uid] = dict(
                    variables=value.pop("Variables", list()),
                    mips=value.pop("MIPs", list()),
                    priority=value.pop("Priority Level", None),
                )
                vocabulary_server[new_subelt][uid] = value
        elif subelt in [
            "Experiment Group",
        ]:
            new_subelt = "experiment_groups"
            data_request[new_subelt] = dict()
            vocabulary_server[new_subelt] = dict()
            for uid in content[subelt]["records"]:
                value = content[subelt]["records"][uid]
                data_request[new_subelt][uid] = dict(
                    experiments=value.pop("Experiments", list())
                )
                vocabulary_server[new_subelt][uid] = value
        else:
            vocabulary_server[subelt] = content[subelt]["records"]
    return data_request, vocabulary_server


# def write_json_output_file_content(filename, content):
#    with open(filename, "w") as fic:
#        json.dump(content, fic, indent=4, allow_nan=True, sort_keys=True)
# data_request, vocabulary_server = transform_content(content, args.version)
# write_json_output_file_content(os.path.sep.join([output_directory, "DR_content.json"]), data_request)
# write_json_output_file_content(os.path.sep.join([output_directory, "VS_content.json"]), vocabulary_server)
