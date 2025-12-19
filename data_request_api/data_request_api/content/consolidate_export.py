import re
from collections import defaultdict

from data_request_api.content.utils import _parse_version
from data_request_api.utilities.logger import get_logger  # noqa

from .mapping_table import (version_consistency,
                            version_consistency_drop_fields,
                            version_consistency_drop_tables,
                            version_consistency_fields)

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


def _map_attribute(attr, records, keys):
    """
    Identifies a record_id in list of records using key and matching with the attribute value.
    """
    # For the specified "key", check if there is an entry in "records"
    #   that matches with "attr"
    matches = []
    for key in keys:
        matches.extend([r for r, v in records.items() if key in v and v[key] == attr])
        if len(matches) == 1:
            break
    return matches


def _apply_consistency_fixes(data):
    """
    Modifies the table names to be consistent with the data request current software version.
    """
    logger = get_logger()

    # Table names
    for tfrom, tto in version_consistency.items():
        if tfrom in data:
            logger.debug(
                f"Consistency across versions / releases - renaming table: {tfrom} -> {tto}"
            )
            data[tto] = data.pop(tfrom)
    for tfrom in version_consistency_drop_tables:
        if tfrom in data:
            logger.debug(
                f"Consistency across versions / releases - dropping table: {tfrom}"
            )
            data.pop(tfrom)
    # Field names
    for tfrom, fnm in version_consistency_fields.items():
        if tfrom in data:
            field_names = {j["name"]: i for i, j in data[tfrom]["fields"].items()}
            for keyold, keynew in fnm.items():
                if keyold in field_names:
                    logger.debug(
                        f"Consistency across versions / releases - renaming field in table '{tfrom}': '{keyold}' -> '{keynew}'"
                    )
                    data[tfrom]["fields"][field_names[keyold]]["name"] = keynew
                    for r, v in data[tfrom]["records"].items():
                        if keyold in v:
                            data[tfrom]["records"][r][keynew] = data[tfrom]["records"][
                                r
                            ].pop(keyold)
    for tfrom in version_consistency_drop_fields:
        if tfrom in data:
            field_names = {j["name"]: i for i, j in data[tfrom]["fields"].items()}
            for key in version_consistency_drop_fields[tfrom]:
                if key in field_names:
                    logger.debug(
                        f"Consistency across versions / releases - dropping field in table '{tfrom}': '{key}'"
                    )
                    data[tfrom]["fields"].pop(field_names[key])
                    for r, v in data[tfrom]["records"].items():
                        if key in v:
                            data[tfrom]["records"][r].pop(key)
    return data


def _apply_hard_fixes(data):
    """
    Applies hard-coded fixes to the data request dictionary, such as merging or deletion of records.
    """
    if data["Data Request"]["version"] == "v1.2":
        logger = get_logger()
        logger.debug(
            f"Consistency across versions / releases - applying hard fixes for version '{data['Data Request']['version']}'"
        )
        # v1.2 raw: MIPs - merge recC5TLtnrU7SVcas into recdHS1Xys1I97ju4
        for k, v in data["Data Request"]["MIPs"]["records"][
            "recC5TLtnrU7SVcas"
        ].items():
            if k != "MIP Short Name":
                data["Data Request"]["MIPs"]["records"]["recdHS1Xys1I97ju4"][k] = v
        data["Data Request"]["MIPs"]["records"].pop("recC5TLtnrU7SVcas")
        # v1.2 raw: Table Identifiers - delete recWXLdtRuQkdcTqC
        data["Data Request"]["CMIP6 Table Identifiers (legacy)"]["records"].pop(
            "recWXLdtRuQkdcTqC"
        )
        # v1.2 raw: Table Identifiers - alter recWX81OMKJSjRjS7 (80ac3145-a698-11ef-914a-613c0433d878)
        chdict = {
            "UID": "80ab73f5-a698-11ef-914a-613c0433d878",
            "Title": "6-hourly surface data",
            "Frequency": ["rectxxiQQwBXUszgx"],
            "Description": (
                "New in CMIP7. Contains surface or 2D data from any modelling realm.\n\n"
                "Justification: Existing 6hr tables (6hrLev, 6hrPlev &…evels) with the request"
                " for 6 hourly ocean surface variables requested for wind-wave coupled modelling [Opportunity ID 68]."
            ),
            "Alternative Label": "6hrOcean",
        }
        for k, v in chdict.items():
            data["Data Request"]["CMIP6 Table Identifiers (legacy)"]["records"][
                "recWX81OMKJSjRjS7"
            ][k] = v
        # v1.2 raw: This Table Identifier is also missing from the CMIP6 Frequency (legacy) rectxxiQQwBXUszgx
        data["Data Request"]["CMIP6 Frequency (legacy)"]["records"][
            "rectxxiQQwBXUszgx"
        ]["Table Identifiers"].append("recWX81OMKJSjRjS7")
    return data


def _apply_hard_fixes_one_base(data, version):
    """
    Applies hard-coded fixes to the one base data request dictionary, such as merging or deletion of records.
    """
    if version == "v1.1":
        logger = get_logger()
        logger.debug(
            f"Consistency across versions / releases - applying hard fixes for version '{version}'"
        )
        # v1.1 release: MIPs - merge recwXayS94wpn2bbL into rec3hKWuBm4Cbmsp9
        for k, v in data["MIPs"]["records"]["recwXayS94wpn2bbL"].items():
            if k != "MIP Short Name":
                data["MIPs"]["records"]["rec3hKWuBm4Cbmsp9"][k] = v
        data["MIPs"]["records"].pop("recwXayS94wpn2bbL")
    return data


def _filter_references(val, key, table, rid, dtype=None):
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
                    f" references for '{key}' of record '{rid}'."
                )
        return _fix_dtype(key, filtered, dtype)
    elif isinstance(val, str) and val.startswith("rec"):
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
            return _fix_dtype(key, ",".join(filtered), dtype)
        elif val.strip() in filtered_records:
            logger.warning(
                f"'{table}': Filtered the only reference for '{key}' of record '{rid}'."
            )
            return _fix_dtype(key, "", dtype)
        else:
            return _fix_dtype(key, _fix_str(val), dtype)
    else:
        return _fix_dtype(key, _fix_str(val), dtype)


def _gen_rid_uid_map(data):
    rid_uid_map = {}
    if len(data.keys()) in [3, 4]:
        for base in data:
            if "schema" in base.lower():
                continue
            for table in data[base]:
                for rid, record in data[base][table]["records"].items():
                    if "UID" in record:
                        rid_uid_map[rid] = record["UID"]
    elif len(data.keys()) == 1:
        for table in data["Data Request"]:
            if table == "version":
                continue
            for rid, record in data["Data Request"][table]["records"].items():
                if "UID" in record:
                    rid_uid_map[rid] = record["UID"]
    else:
        for table in data:
            if table == "version":
                continue
            for rid, record in data[table]["records"].items():
                if "UID" in record:
                    rid_uid_map[rid] = record["UID"]
    return rid_uid_map


def _fix_str(var):
    """Adds missing space after commas and strips whitespace from strings."""
    if isinstance(var, str):
        return re.sub(r",(?=\S)", ", ", var).strip()
    else:
        return var


def _fix_numeric_str(var):
    """Removes invalid characters from strings that represent numeric values."""
    if isinstance(var, str):
        return re.sub(r"[^0-9eE\+\-\.]", "", var)
    else:
        return var


def _fix_str_nested(data):
    """Adds missing space after commas and strips whitespace from strings in nested dictionary."""
    sub = re.sub
    pattern = r",(?=\S)"
    for table in data.values():
        for record in table["records"].values():
            record.update(
                {
                    k: sub(pattern, ", ", v).strip() if isinstance(v, str) else v
                    for k, v in record.items()
                }
            )


def _fix_dtype(fkey, fval, dtype=None):
    """Fixes data types for record fields."""
    logger = get_logger()

    if dtype is None:
        return fval
    elif dtype == "str":
        logger.debug(
            f"Consolidate export: Converting field '{fkey}' ('{fval}') to string."
        )
        return str(fval)
    elif dtype == "int":
        logger.debug(
            f"Consolidate export: Converting field '{fkey}' ('{fval}') to int."
        )
        return int(_fix_numeric_str(fval))
    elif dtype == "float":
        logger.debug(
            f"Consolidate export: Converting field '{fkey}' ('{fval}') to float."
        )
        return float(_fix_numeric_str(fval))
    elif dtype == "listofstr":
        logger.debug(
            f"Consolidate export: Converting field '{fkey}' to a list of strings."
        )
        if isinstance(fval, list):
            return [str(v) for v in fval]
        else:
            return [str(fval)]
    elif dtype == "listofint":
        logger.debug(
            f"Consolidate export: Converting field '{fkey}' to a list of ints."
        )
        if isinstance(fval, list):
            return [int(v) for v in fval]
        elif isinstance(fval, str):
            if "," in fval:
                return [int(ifval) for ifval in fval.replace(" ", "").split(",")]
            elif " " in fval:
                return [int(ifval) for ifval in fval.split() if ifval.strip() != ""]
            else:
                return [int(fval)]
        else:
            return [int(fval)]
    elif dtype == "listoffloat":
        logger.debug(
            f"Consolidate export: Converting field '{fkey}' to a list of floats."
        )
        if isinstance(fval, list):
            return [float(v) for v in fval]
        elif isinstance(fval, str):
            if "," in fval:
                return [float(ifval) for ifval in fval.replace(" ", "").split(",")]
            elif " " in fval:
                return [float(ifval) for ifval in fval.split() if ifval.strip() != ""]
            else:
                return [float(fval)]
        else:
            return [float(fval)]
    else:
        logger.warning(
            f"Consolidate export: Unsupported data type '{dtype}' for field '{fkey}'."
        )
        return fval


def map_data(data, mapping_table, version, **kwargs):
    """
    Maps the data to the one-base structure using the mapping table.

    Parameters
    ----------
    data : dict
        Three-base or one-base Airtable export.
    mapping_table dict
        The mapping table to apply to map to one base.
    version : str
        The version tag of the exported Data Request Content dictionary.

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

    # Check if data is already one-base
    if len(data.keys()) in [3, 4]:
        # Set version
        mapped_data["Data Request"]["version"] = version

        # Reset filtered records
        global filtered_records
        if filtered_records:
            filtered_records = []
        filtered_records_dict = dict()

        # Get filtered records
        for table, mapinfo in mapping_table.items():
            if mapinfo["source_base"] in data and any(
                [st in data[mapinfo["source_base"]] for st in mapinfo["source_table"]]
            ):
                source_table = [
                    st
                    for st in mapinfo["source_table"]
                    if st in data[mapinfo["source_base"]]
                ][0]
                if "internal_filters" in mapinfo:
                    for record_id, record in data[mapinfo["source_base"]][source_table][
                        "records"
                    ].items():
                        filter_results = []
                        for filter_key, filter_val in mapinfo[
                            "internal_filters"
                        ].items():
                            if all(
                                [
                                    filter_alias not in record
                                    for filter_alias in [filter_key]
                                    + filter_val["aliases"]
                                ]
                            ):
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
                                                    fj not in filter_val["values"]
                                                    for fj in record[filter_key]
                                                )
                                            )
                                        break
                                else:
                                    filter_results.append(
                                        record[filter_key] not in filter_val["values"]
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
                [st in data[mapinfo["source_base"]] for st in mapinfo["source_table"]]
            ):
                # Copy the selected data to the one-base structure
                # - skip filtered records
                # - rename record attributes according to
                #   "internal_consistency" settings
                # - filter references to records for fields that are not
                #   internally mapped below
                source_table = [
                    st
                    for st in mapinfo["source_table"]
                    if st in data[mapinfo["source_base"]]
                ][0]
                logger.debug(
                    f"Mapping '{mapinfo['source_base']}' : '{source_table}' -> '{table}'"
                )
                mapped_data["Data Request"][table] = {
                    **data[mapinfo["source_base"]][source_table],
                    "records": {
                        record_id: {
                            mapinfo["internal_consistency"].get(
                                reckey, reckey
                            ): _filter_references(
                                recvalue,
                                reckey,
                                table,
                                record_id,
                                mapinfo["field_dtypes"].get(
                                    mapinfo["internal_consistency"].get(reckey, reckey),
                                    None,
                                ),
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
                        intm_table = [
                            tn
                            for tn in mapping_table.keys()
                            if tn in mapping_table[tn]["source_table"]
                            and tn == intm[attr]["table"]
                        ][0]
                        intm_table_alias = [
                            tn
                            for tn in mapping_table[intm_table]["source_table"]
                            if tn in data[intm[attr]["base"]]
                        ]
                        try:
                            intm_table_alias = intm_table_alias[0]
                        except IndexError:
                            errmsg = f"None of the following tables exist in the data: {mapping_table[intm[attr]['table']]['source_table']}."
                            logger.error(errmsg)
                            raise ValueError(errmsg)

                        for record_id, record in data[mapinfo["source_base"]][
                            source_table
                        ]["records"].items():
                            if record_id in filtered_records:
                                continue
                            elif (
                                attr not in record
                                or record[attr] is None
                                or record[attr] == ""
                                or record[attr] == []
                            ):
                                # Attribute name not found for record, but might have a different name
                                #  in another export type or release version
                                logger.debug(
                                    f"{table}: Attribute '{attr}' not found for record '{record_id}'."
                                )
                                attr_aliases = [
                                    a
                                    for a in mapinfo["internal_consistency"].keys()
                                    if mapinfo["internal_consistency"][a] == attr
                                ]
                                attr_alias_found = False
                                for a in attr_aliases:
                                    if a in record:
                                        attr_vals = record[a]
                                        attr_alias_found = True
                                        logger.debug(
                                            f"{table}: Using attribute '{a}' instead for record '{record_id}'."
                                        )
                                        break
                                if not attr_alias_found:
                                    continue
                            else:
                                attr_vals = record[attr]

                            # Get list of record-keys of the attribute (eg. "Variables")
                            #   that is connected to the current record of the "source_table
                            #   (eg. "Variable Groups") by the specified "operation"
                            if intm[attr]["operation"] == "split":
                                if isinstance(attr_vals, list):
                                    errmsg = (
                                        f"Consolidation of {table}@{attr}: Selected 'split' operation"
                                        f" for a list {record_id}:",
                                        attr_vals,
                                    )
                                    logger.error(f"TypeError: {errmsg}")
                                    continue
                                    # raise TypeError({errmsg})
                                else:
                                    attr_vals = list(
                                        map(
                                            lambda x: x.strip('"'),
                                            re.split(
                                                r',\s*(?=(?:[^"]|"[^"]*")*$)', attr_vals
                                            ),
                                        )
                                    )
                            elif intm[attr]["operation"] == "":
                                if isinstance(attr_vals, str):
                                    attr_vals = [attr_vals]
                            else:
                                errmsg = (
                                    f"Unknown internal mapping operation for attribute '{attr}'"
                                    f" ('{source_table}'): '{intm[attr]['operation']}'"
                                )
                                logger.error(f"ValueError: {errmsg}")
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
                                    logger.error(f"ValueError: {errmsg}")
                                    raise ValueError(errmsg)
                                elif not intm[attr]["base"] in data:
                                    errmsg = f"Base '{intm[attr]['base']}' not found in data."
                                    logger.error(f"KeyError: {errmsg}")
                                    raise KeyError(errmsg)
                                elif (
                                    intm[attr]["base_copy_of_table"]
                                    not in data[mapinfo["source_base"]]
                                ):
                                    errmsg = f"Table '{intm[attr]['base_copy_of_table']}' not found in base '{mapinfo['source_base']}'."
                                    logger.error(f"KeyError: {errmsg}")
                                    raise KeyError(errmsg)

                                recordIDs_new = []
                                for attr_val in attr_vals:
                                    # The record copy in the current base
                                    record_copy = data[mapinfo["source_base"]][
                                        intm[attr]["base_copy_of_table"]
                                    ]["records"][attr_val]
                                    # The entire list of records in the base of origin
                                    recordlist = data[intm[attr]["base"]][
                                        intm_table_alias
                                    ]["records"]
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
                                                f"Consolidation of {table}@{intm_table_alias}: No matching"
                                                f" record found for attribute '{attr}' with value '{attr_val}'."
                                            )
                                    elif len(recordID_filtered) > 1:
                                        logger.warning(
                                            f"Consolidation of {table}@{intm_table_alias}:"
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
                                        data[intm[attr]["base"]][intm_table_alias][
                                            "records"
                                        ],
                                        (
                                            [intm[attr]["map_by_key"]]
                                            if isinstance(intm[attr]["map_by_key"], str)
                                            else intm[attr]["map_by_key"]
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
                                                f"Consolidation of {table}@{intm_table_alias}: No matching"
                                                f" record found for attribute '{attr}' with value '{attr_val}'."
                                            )
                                    elif len(recordID_filtered) > 1:
                                        logger.debug(
                                            "Consolidation of"
                                            f" {table}@{intm_table_alias}: Multiple matching records found"
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
                                logger.error(f"ValueError: {errmsg}")
                                raise ValueError(errmsg)
                            if not recordIDs_new:
                                errmsg = (
                                    f"{table} (record '{record_id}'): For attribute"
                                    f" '{attr}' no records could be mapped."
                                )
                                logger.error(errmsg)
                                # This case can actually happen for the 'Coordinate and Dimension' table
                                # raise KeyError(errmsg)
                            try:
                                mapped_data["Data Request"][table]["records"][
                                    record_id
                                ][
                                    mapinfo["internal_consistency"].get(attr, attr)
                                ] = list(
                                    set(recordIDs_new)
                                )
                            except KeyError:
                                logger.debug(
                                    f"Consolidation of {table}@{intm_table_alias}:"
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
        return _apply_hard_fixes(mapped_data)
    # Return the data if it is already one-base
    elif len(data.keys()) == 1:
        l_version = next(iter(data.keys())).replace("Data Request", "").strip()
        # Consistency fixes
        mapped_data = next(iter(data.values()))
        mapped_data = _apply_consistency_fixes(mapped_data)
        # String fixes
        logger.debug(
            "Consolidation: Removing / Adding (un)necessary whitespace to strings."
        )
        _fix_str_nested(mapped_data)
        if _parse_version(version) == (0, 0, 0, 0, "", 0):
            mapped_data["version"] = version
        else:
            if l_version != version:
                errmsg = (
                    f"The Data Request version inferred from the content dictionary"
                    f" ({l_version}) is different than the requested version ({version})."
                )
                logger.error(errmsg)
                raise ValueError(errmsg)
            mapped_data["version"] = version
        mapped_data = _apply_hard_fixes_one_base(mapped_data, version)
        return {"Data Request": mapped_data}
    else:
        errmsg = "The loaded Data Request has an unexpected data structure."
        logger.error(errmsg)
        raise ValueError(errmsg)
