import json
import os
import re
import warnings

from data_request_api.stable.utilities.logger import get_logger  # noqa

from .mapping_table import version_consistency, version_consistency_drop_tables, version_consistency_fields, version_consistency_drop_fields

# UID generation
default_count = 0
default_template = "default_{:d}"

# Filtered records
filtered_records = []


def _map_record_id(record, records, keys):
    """
    Identifies a record_id in list of records using key.
    """
    matches = []
    # For each of the specified "keys", check if there is an entry in "records"
    #   that matches with "record"
    for key in keys:
        if key in record:
            recval = record[key]
            matches = [r for r, v in records.items() if key in v and v[key] == recval]
            if len(matches) == 1:
                break
    return matches


def _map_attribute(attr, records, key):
    """
    Identifies a record_id in list of records using key and matching with the attribute value.
    """
    # For the specified "key", check if there is an entry in "records"
    #   that matches with "attr"
    matches = [r for r, v in records.items() if key in v and v[key] == attr]
    return matches


def _apply_consistency_fixes(data, version=""):
    """
    Modifies the table names to be consistent with the data request current software version.
    """
    logger = get_logger()

    # Table names
    for tfrom, tto in version_consistency.items():
        if tfrom in data:
            logger.debug(
                f"Consistency across versions - renaming table: {tfrom} -> {tto}"
            )
            data[tto] = data.pop(tfrom)
    for tfrom in version_consistency_drop_tables:
        if tfrom in data:
            logger.debug(
                f"Consistency across versions - dropping table: {tfrom}"
            )
            data.pop(tfrom)
    # Field names
    for tfrom, fnm in version_consistency_fields.items():
        if tfrom in data:
            field_names = [j["name"] for i,j in data[tfrom]["fields"].items()]
            for keyold, keynew in fnm.items():
                if keyold in field_names:
                    logger.debug(
                        f"Consistency across versions - renaming field in table '{tfrom}': '{keyold}' -> '{keynew}'"
                    )
                    for r, v in data[tfrom]["records"].items():
                        if keyold in v:
                            data[tfrom]["records"][r][keynew] = data[tfrom]["records"][r].pop(keyold)
    for tfrom in version_consistency_drop_fields:
        if tfrom in data:
            field_names = {j["name"]: i for i,j in data[tfrom]["fields"].items()}
            for key in version_consistency_drop_fields[tfrom]:
                if key in field_names:
                    logger.debug(
                        f"Consistency across versions - dropping field in table '{tfrom}': '{key}'"
                    )
                    data[tfrom]["fields"].pop(field_names[key])
                    for r, v in data[tfrom]["records"].items():
                        if key in v:
                            data[tfrom]["records"][r].pop(key)
    return data


def _filter_references(val, key, table, rid):
    """
    Filters lists of or strings with comma-separated references to other records.
    """
    global filtered_records
    logger = get_logger()

    if isinstance(val, list):
        filtered = [v for v in val if v not in filtered_records]
        if len(filtered) != len(val):
            if filtered == []:
                if len(val) == 1:
                    logger.warning(
                        f"'{table}': Filtered the only reference for '{key}' of record '{rid}'."
                    )
                else:
                    logger.warning(
                        f"'{table}': Filtered all {len(val)} references for '{key}' of record '{rid}'."
                    )
            else:
                logger.debug(
                    f"'{table}': Filtered {len(val) - len(filtered)} of {len(val)}"
                    f"references for '{key}' of record '{rid}'."
                )
        return filtered
    elif isinstance(val, str) and "rec" in val:
        if "," in val:
            vallist = [v.strip() for v in val.split(",")]
            filtered = [v for v in vallist if v not in filtered_records]
            if len(filtered) != len(vallist):
                if filtered == []:
                    logger.warning(
                        f"'{table}': Filtered all {len(vallist)} references for"
                        f" '{key}' of record '{rid}'."
                    )
                else:
                    logger.debug(
                        f"'{table}': Filtered {len(vallist) - len(filtered)} of"
                        f" {len(vallist)} references for '{key}' of record '{rid}'."
                    )
            return ",".join(filtered)
        elif val.strip() in filtered_records:
            logger.warning(
                f"'{table}': Filtered the only reference for '{key}' of record '{rid}'."
            )
            return ""
        else:
            return val.strip()
    else:
        return val


def map_data(data, mapping_table, version):
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
    filtered_records_dict = dict()

    # Check if data is already one-base
    if len(data.keys()) in [3, 4]:

        # Set version
        mapped_data["version"] = version

        # Get filtered records
        for table, mapinfo in mapping_table.items():
            if mapinfo["source_base"] in data and any(
                [
                    st in data[mapinfo["source_base"]]
                    for st in mapinfo["source_table"]
                ]
            ):
                source_table = [st for st in mapinfo["source_table"] if st in data[mapinfo["source_base"]]][0]
                if "internal_filters" in mapinfo:
                    for record_id, record in data[mapinfo["source_base"]][source_table]["records"].items():
                        filter_results = []
                        for filter_key, filter_val in mapinfo["internal_filters"].items():
                            if all([filter_alias not in record for filter_alias in [filter_key] + filter_val["aliases"]]):
                                filter_results.append(False)
                            elif filter_val["operator"] == "nonempty":
                                filter_results.append(
                                    any(
                                        [
                                            bool(record[fk])
                                            for fk in [filter_key]
                                            + filter_val["aliases"]
                                            if fk in record
                                        ]
                                    )
                                )
                            elif filter_val["operator"] == "in":
                                for fk in [filter_key] + filter_val["aliases"]:
                                    if fk in record:
                                        if isinstance(record[filter_key], list):
                                            filter_results.append(
                                                any(
                                                    fj in filter_val["values"]
                                                    for fj in record[filter_key]
                                                )
                                            )
                                            break
                                        else:
                                            filter_results.append(
                                                record[filter_key]
                                                in filter_val["values"]
                                            )
                            elif filter_val["operator"] == "not in":
                                for fk in [filter_key] + filter_val["aliases"]:
                                    if fk in record:
                                        if isinstance(record[filter_key], list):
                                            filter_results.append(
                                                any(
                                                    fj
                                                    not in filter_val["values"]
                                                    for fj in record[filter_key]
                                                )
                                            )
                                        break
                                else:
                                    filter_results.append(
                                        record[filter_key]
                                        not in filter_val["values"]
                                    )
                        if not all(filter_results):
                            logger.debug(
                                f"Filtered record '{record_id}'"
                                f" {'(' + record['name'] + ')' if 'name' in record else ''}"
                                f" from '{table}'."
                            )
                            filtered_records.append(record_id)
                            if table in filtered_records_dict:
                                filtered_records_dict[table].append(record_id)
                            else:
                                filtered_records_dict[table] = [record_id]
        for key in filtered_records_dict:
            logger.debug(
                f"Filtered {len(filtered_records_dict[key])} records for '{key}'."
            )
        logger.debug(f"Filtered {len(filtered_records)} records in total.")

        # Perform mapping in case of three-base structure
        for table, mapinfo in mapping_table.items():
            intm = mapinfo["internal_mapping"]
            if mapinfo["source_base"] in data and any(
                [
                    st in data[mapinfo["source_base"]]
                    for st in mapinfo["source_table"]
                ]
            ):
                # Copy the selected data to the one-base structure
                # - skip filtered records
                # - rename record attributes according to
                #   "internal_consistency" settings
                # - filter references to records for fields that are not
                #   internally mapped below
                source_table = [st for st in mapinfo["source_table"] if st in data[mapinfo["source_base"]]][0]
                logger.debug(f"Mapping '{mapinfo['source_base']}' : '{source_table}' -> '{table}'")
                mapped_data["Data Request"][table] = {
                    **data[mapinfo["source_base"]][source_table],
                    "records": {
                        record_id: {
                            mapinfo["internal_consistency"].get(
                                reckey, reckey
                            ): _filter_references(
                                recvalue, reckey, table, record_id
                            )
                            for reckey, recvalue in record.items()
                            if reckey not in mapinfo["drop_keys"]
                        }
                        for record_id, record in data[mapinfo["source_base"]][
                            source_table
                        ]["records"].items()
                        if record_id not in filtered_records
                    },
                }

                # If record attributes require mapping
                if intm != {}:
                    # for each attribute that requires mapping
                    for attr in intm.keys():
                        for record_id, record in data[mapinfo["source_base"]][source_table]["records"].items():
                            if record_id in filtered_records:
                                continue
                            elif (
                                attr not in record
                                or record[attr] is None
                                or record[attr] == ""
                                or record[attr] == []
                            ):
                                logger.debug(f"{table}: Attribute '{attr}' not found for record '{record_id}'.")
                                continue
                            attr_vals = record[attr]

                            # Get list of record-keys of the attribute (eg. "Variables")
                            #   that is connected to the current record of the "source_table
                            #   (eg. "Variable Groups") by the specified "operation"
                            if intm[attr]["operation"] == "split":
                                attr_vals = re.split(r"\s*,\s*", attr_vals)
                            elif intm[attr]["operation"] == "":
                                if isinstance(attr_vals, str):
                                    attr_vals = [attr_vals]
                            else:
                                errmsg = (
                                    f"Unknown internal mapping operation for attribute '{attr}'"
                                    f" ('{source_table}'): '{intm[attr]['operation']}'"
                                )
                                logger.error("ValueError:", errmsg)
                                raise ValueError(errmsg)

                            # Get mapped record_ids for this list of record-keys
                            # entry_type - single record_id or list of record_ids
                            # - map by record_id
                            if intm[attr]["entry_type"] == "record_id":
                                if not intm[attr]["base_copy_of_table"]:
                                    errmsg = (
                                        "A copy of the table in the same base is required if 'entry_type'"
                                        " is set to 'record_id', but 'base_copy_of_table' is set to"
                                        f" False: '{source_table}' - '{attr}'"
                                    )
                                    logger.error("ValueError:", errmsg)
                                    raise ValueError(errmsg)
                                elif not intm[attr]["base"] in data:
                                    errmsg = (
                                        f"Base '{intm[attr]['base']}' not found in data."
                                    )
                                    logger.error("KeyError:", errmsg)
                                    raise KeyError(errmsg)
                                elif intm[attr]["base_copy_of_table"] not in data[mapinfo["source_base"]]:
                                    errmsg = (
                                        f"Table '{intm[attr]['table']}' not found in base '{intm[attr]['base_copy']}'."
                                    )
                                    logger.error("KeyError:", errmsg)
                                    raise KeyError(errmsg)

                                recordIDs_new = []
                                for attr_val in attr_vals:
                                    # The record copy in the current base
                                    record_copy = data[mapinfo["source_base"]][
                                        intm[attr]["base_copy_of_table"]
                                    ]["records"][attr_val]
                                    # The entire list of records in the base of origin
                                    recordlist = data[intm[attr]["base"]][intm[attr]["table"]]["records"]
                                    recordID_new = _map_record_id(
                                        record_copy,
                                        recordlist,
                                        intm[attr]["map_by_key"],
                                    )
                                    recordID_filtered = [
                                        r
                                        for r in recordID_new
                                        if r not in filtered_records
                                    ]
                                    if len(recordID_filtered) == 0:
                                        if len(recordID_new) == 0:
                                            logger.debug(
                                                f"Consolidation of {table}@{intm[attr]['table']}: No matching"
                                                f" record found for attribute '{attr}' with value '{attr_val}'."
                                            )
                                    elif len(recordID_filtered) > 1:
                                        logger.debug(
                                            f"Consolidation of {table}@{intm[attr]['table']}:"
                                            f" Multiple matching records found for attribute '{attr}' with"
                                            f" value '{attr_val}': {recordID_new}. Using first match."
                                        )
                                        recordIDs_new.append(recordID_filtered[0])
                                    else:
                                        recordIDs_new.append(recordID_filtered[0])

                            # entry_type - name (eg. unique label or similar)
                            # - map by attribute value
                            elif intm[attr]["entry_type"] == "name":
                                recordIDs_new = []
                                for attr_val in attr_vals:
                                    recordID_new = _map_attribute(
                                        attr_val,
                                        data[intm[attr]["base"]][intm[attr]["table"]]["records"],
                                        (
                                            intm[attr]["map_by_key"]
                                            if isinstance(intm[attr]["map_by_key"], str)
                                            else intm[attr]["map_by_key"][0]
                                        ),
                                    )
                                    recordID_filtered = [
                                        r
                                        for r in recordID_new
                                        if r not in filtered_records
                                    ]
                                    if len(recordID_filtered) == 0:
                                        if len(recordID_new) == 0:
                                            logger.debug(
                                                f"Consolidation of {table}@{intm[attr]['table']}: No matching"
                                                f" record found for attribute '{attr}' with value '{attr_val}'."
                                            )
                                    elif len(recordID_filtered) > 1:
                                        logger.debug(
                                            "Consolidation of"
                                            f" {table}@{intm[attr]['table']}: Multiple matching records found"
                                            f" for attribute '{attr}' with value '{attr_val}': {recordID_new}"
                                        )
                                        recordIDs_new.append(recordID_filtered[0])
                                    else:
                                        recordIDs_new.append(recordID_filtered[0])
                            else:
                                errmsg = (
                                    f"Unknown 'entry_type' specified for attribute '{attr}'"
                                    f" ('{source_table}'): '{intm[attr]['entry_type']}'"
                                )
                                logger.error("ValueError:", errmsg)
                                raise ValueError(errmsg)
                            if not recordIDs_new:
                                errmsg = (
                                    f"{table} (record '{record_id}'): For attribute"
                                    f" '{attr}' no records could be mapped."
                                )
                                logger.error(errmsg)
                                raise KeyError(errmsg)
                            try:
                                mapped_data["Data Request"][table]["records"][
                                    record_id
                                ][
                                    mapinfo["internal_consistency"].get(
                                        attr, attr
                                    )
                                ] = recordIDs_new
                            except KeyError:
                                logger.debug(
                                    f"Consolidation of {table}@{intm[attr]['table']}:"
                                    f" '{record_id}' not found when adding"
                                    f" Attribute '{attr}': {recordIDs_new}"
                                )
            else:
                if mapinfo["source_base"] not in data:
                    missing_bases.append(mapinfo["source_base"])
                elif all(
                    [
                        st not in data[mapinfo["source_base"]]
                        for st in mapinfo["source_table"]
                    ]
                ):
                    missing_tables.append(mapinfo["source_table"][0])
        if len(missing_bases) > 0:
            errmsg = (
                "Encountered missing bases when consolidating the data:"
                f" {set(missing_bases)}"
            )
            logger.critical(errmsg)
            raise KeyError(errmsg)
        if len(missing_tables) > 0:
            logger.warning(
                "Encountered missing tables when consolidating the data (not"
                f" necessarily problematic): {missing_tables}"
            )
        return mapped_data
    # Return the data if it is already one-base
    elif len(data.keys()) == 1:
        l_version = next(iter(data.keys())).replace("Data Request ", "")
        if l_version != version:
            logger.warning(
                "The Data Request version inferred from the content dictionary"
                f" ({l_version}) is different than the requested version"
                f" ({version}). This warning can be ignored if not loading a"
                " tagged version of the Data Request."
            )
        # Consistency fixes
        mapped_data = next(iter(data.values()))        
        mapped_data = _apply_consistency_fixes(mapped_data, version)
        return {"Data Request": mapped_data, "version": version}
    else:
        errmsg = "The loaded Data Request has an unexpected data structure."
        logger.error(errmsg)
        raise ValueError(errmsg)
