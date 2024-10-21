import re
import warnings


def map_data(data, mapping_table):
    """
    Maps the data to the one-base structure using the mapping table.

    Args:
        data: dict (three-base or one-base Airtable export)
        mapping_table: The mapping table to apply to map to one base.

    Returns:
        dict: of the mapped data with one-base structure.

    Note:
        Returns the input dict if the data is already one-base.
    """
    missing_bases = []
    missing_tables = []
    mapped_data = {"Data Request": {}}
    # Perform mapping in case of three-base structure
    if len(data.keys()) in [3, 4]:
        for table, mapinfo in mapping_table.items():
            intm = mapinfo["internal_mapping"]
            if (
                mapinfo["source_base"] in data
                and mapinfo["source_table"] in data[mapinfo["source_base"]]
            ):

                # Copy the selected data to the one-base structure
                # print(f"Mapping '{mapinfo['source_base']}' -> '{table}'")
                mapped_data["Data Request"][table] = data[mapinfo["source_base"]][
                    mapinfo["source_table"]
                ]

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
                                print(
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
                                    recordIDs_new.append(
                                        _map_record_id(
                                            record_copy,
                                            recordlist,
                                            intm[attr]["map_by_key"],
                                        )
                                    )
                            # entry_type - name (eg. unique label or similar)
                            elif intm[attr]["entry_type"] == "name":
                                recordIDs_new = []
                                for attr_val in attr_vals:
                                    recordIDs_new.append(
                                        _map_attribute(
                                            attr_val,
                                            data[intm[attr]["base"]][
                                                intm[attr]["table"]
                                            ]["records"],
                                            (
                                                intm[attr]["map_by_key"]
                                                if isinstance(
                                                    intm[attr]["map_by_key"], str
                                                )
                                                else intm[attr]["map_by_key"][0]
                                            ),
                                        )
                                    )
                            else:
                                raise ValueError(
                                    f"Unknown 'entry_type' specified for attribute '{attr}' ('{mapinfo['source_table']}'): '{intm[attr]['entry_type']}'"
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
        mapped_data["Data Request"] = data[data.keys()[0]]
        return mapped_data
    else:
        raise ValueError("The loaded Data Request has an unexpected data structure.")


def _map_record_id(record, records, keys):
    """
    Identifies a record_id in list of records using key
    """
    matches = []
    for key in keys:
        if key in record:
            recval = record[key]
            matches = [r for r, v in records.items() if key in v and v[key] == recval]
            if len(matches) == 1:
                break
    if len(matches) == 1:
        return matches[0]
    else:
        raise KeyError(f"None or multiple matches when consolidating '{record}'.")


def _map_attribute(attr, records, key):
    """
    Identifies a record_id in list of records using key and matching with the attribute value.
    """
    matches = [r for r, v in records.items() if key in v and v[key] == attr]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) == 0:
        # raise KeyError(f"No matches when consolidating '{attr}' via '{key}'.")
        print(f"No matches when consolidating '{attr}' via '{key}'.")
    else:
        # raise KeyError(f"Multiple matches when consolidating '{attr}' via '{key}'.")
        print(f"Multiple matches when consolidating '{attr}' via '{key}'.")


"""
Mapping Table

The mapping_table dictionary defines how to map the three-base structure to the one-base structure.
Each entry in the dictionary represents a table in the one-base structure and includes the information
how to obtain it from the three-base structure.

Explanation of the dictionary keys:

Base ("source_base"):
   The base containing the table to be selected.

Table ("source_table"):
    The table to be selected from the "source_base".

Internal Mapping of record attributes ("internal_mapping"):
    Record attributes may point to records of other tables.
    However, there is no cross-linkage between the three bases,
    so these links need to be mapped as well.
    "internal_mapping" is a dictionary with the key corresponding
    to the record attributes to be mapped and the values containing
    the actual mapping information.

    The mapping information is again a dictionary with the following keys:
    - base_copy_of_table:
        If a copy of table corresponding to the record attribute exists in the current base,
        provide the name; otherwise, set to False.
    - base:
        The base containing the original table the record attribute points to.
    - table:
        The original table the record attribute points to.
    - operation:
        The operation to perform on the attribute value (either "split" or "", if it is
        already provided as list or a string without comma separated values).
    - map_by_key:
        A list of keys to map by.
    - entry_type:
        The type of entry (either "record_id" or "name").

Example Configuration

Suppose we want to map the "CMIP7 Variable Groups" key in the "Variables" table of the "Data Request Variables (Public)"
base to a list of record IDs of "Variable Group" records in the "Data Request Opportunities (Public)" base.

We would define the mapping_table as follows:
mapping_table = {
      "Variables": {
                "base": "Data Request Variables (Public)",
                "source_table": "Variables",
                "internal_mapping": {
                    "CMIP7 Variable Groups": {
                        "base_copy_of_table": False,
                        "base": "Data Request Opportunities (Public)",
                        "table": "Variable Group",
                        "operation": "split",
                        "map_by_key": ["Name"],
                        "entry_type": "name",
                    },
                },
      },
}
"""
mapping_table = {
    "Opportunity": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Opportunity",
        "internal_mapping": {},
    },
    "Variable Group": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Variable Group",
        "internal_mapping": {
            "Variables": {
                "base_copy_of_table": "Variables",
                "base": "Data Request Variables (Public)",
                "table": "Variable",
                "operation": "",
                "map_by_key": ["UID", "Compound Name"],
                "entry_type": "record_id",
            },
        },
    },
    "Variables": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Variable",
        "internal_mapping": {
            "CMIP7 Variable Groups": {
                "base_copy_of_table": False,
                "base": "Data Request Opportunities (Public)",
                "table": "Variable Group",
                "operation": "split",
                "map_by_key": ["Name"],
                "entry_type": "name",
            },
            "Physical Parameter": {
                "base_copy_of_table": "Physical Parameter",
                "base": "Data Request Physical Parameters (Public)",
                "table": "Physical Parameter",
                "operation": "",
                "map_by_key": ["UID", "Name"],
                "entry_type": "record_id",
            },
            "CF Standard Name (from MIP Variables)": {
                "base_copy_of_table": False,
                "base": "Data Request Physical Parameters (Public)",
                "table": "CF Standard Name",
                "operation": "",
                "map_by_key": ["name"],
                "entry_type": "name",
            },
        },
    },
    "Experiment Group": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Experiment Group",
        "internal_mapping": {},
    },
    "Experiments": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Experiment",
        "internal_mapping": {},
    },
    "Physical Parameters": {
        "source_base": "Data Request Physical Parameters (Public)",
        "source_table": "Physical Parameter",
        "internal_mapping": {},
    },
    "MIPs": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "MIP",
        "internal_mapping": {},
    },
    "Data Request Themes": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Data Request Themes",
        "internal_mapping": {},
    },
    "Priority Level": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Priority Level",
        "internal_mapping": {},
    },
    "Docs for Opportunities": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Docs for Opportunities",
        "internal_mapping": {},
    },
    "Time Slice": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Time Slice",
        "internal_mapping": {},
    },
    "Opportunity/Variable Group Comments": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Comment",
        "internal_mapping": {},
    },
    "Glossary": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Glossary",
        "internal_mapping": {},
    },
    "Modelling Realm": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Modelling Realm",
        "internal_mapping": {},
    },
    "Frequency": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Frequency",
        "internal_mapping": {},
    },
    "Table Identifiers": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Table Identifiers",
        "internal_mapping": {},
    },
    "Spatial Shape": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Spatial Shape",
        "internal_mapping": {},
    },
    "Temporal Shape": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Temporal Shape",
        "internal_mapping": {},
    },
    "Structure": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Structure",
        "internal_mapping": {},
    },
    "Cell Methods": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Cell Methods",
        "internal_mapping": {},
    },
    "Cell Measures": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Cell Measures",
        "internal_mapping": {},
    },
    "Coordinates and Dimensions": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Coordinate or Dimension",
        "internal_mapping": {},
    },
    "Ranking": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Ranking",
        "internal_mapping": {},
    },
    "Variable Comments": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Comment",
        "internal_mapping": {},
    },
    "ESM-BCV 1.3": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "ESM-BCV 1.3",
        "internal_mapping": {},
    },
    "CF Standard Names": {
        "source_base": "Data Request Physical Parameters (Public)",
        "source_table": "CF Standard Name",
        "internal_mapping": {},
    },
    "Physical Parameter Comments": {
        "source_base": "Data Request Physical Parameters (Public)",
        "source_table": "Comment",
        "internal_mapping": {},
    },
}
