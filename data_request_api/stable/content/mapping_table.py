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

(Internal) Filters of record attributes ("internal_filters"):
    Not all records of the raw export shall be included since they may be
    labeled as junk or not be approved by the community. The filters are applied on all records
    and also internally on links to other records. "internal_filters" is a dictionary
    with the key corresponding to the record attributes used for filtering and the value
    another dictionary with the following possible keys:
    - operator: Can be one of "nonempty", "in", "not in"
    - values:  A list of values, not necessary for "nonempty" operator.

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
                "internal_filters": {
                    "Status": {"operator": "not in", "values": ["Junk"]},
                }
      },
}
"""

mapping_table = {
    "CF Standard Names": {
        "source_base": "Data Request Physical Parameters (Public)",
        "source_table": "CF Standard Name",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Physical Parameters", "Physical Parameters 2"],
    },
    "Cell Measures": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Cell Measures",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Variables"],
    },
    "Cell Methods": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Cell Methods",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Structures", "Variables"],
    },
    "Coordinates and Dimensions": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Coordinate or Dimension",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Structure", "Variables"],
    },
    "Data Request Themes": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Data Request Themes",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": [],
    },
    "Docs for Opportunities": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Docs for Opportunities",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": [],
    },
    "ESM-BCV 1.3": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "ESM-BCV 1.3",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": [],
    },
    "Experiment Group": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Experiment Group",
        "internal_mapping": {},
        "internal_filters": {
            "Status": {"operator": "not in", "values": ["Junk"]},
            "Status (from Opportunity)": {
                "operator": "in",
                "values": ["New", "Under review", "Accepted"],
            },
        },
        "rm_keys": ["Opportunity"],
    },
    "Experiments": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Experiment",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Experiment Group"],
    },
    "CMIP6 Frequency (legacy)": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "CMIP6 Frequency (legacy)",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": [],
    },
    "CMIP7 Frequency": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "CMIP7 Frequency",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Table Identifiers", "Variables"],
    },
    "Glossary": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Glossary",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Opportunity"],
    },
    "MIPs": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "MIP",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Variable Group"],
    },
    "Modelling Realm": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Modelling Realm",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Variables"],
    },
    "Opportunity": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Opportunity",
        "internal_mapping": {},
        "internal_filters": {
            "Status": {"operator": "any", "values": ["Under review", "Accepted"]},
        },
        "rm_keys": [],
    },
    "Opportunity/Variable Group Comments": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Comment",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Experiment Groups", "Opportunities", "Theme", "Variable Groups"],
    },
    "Physical Parameter Comments": {
        "source_base": "Data Request Physical Parameters (Public)",
        "source_table": "Comment",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Physical parameters"],
    },
    "Physical Parameters": {
        "source_base": "Data Request Physical Parameters (Public)",
        "source_table": "Physical Parameter",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Variables"],
    },
    "Priority Level": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Priority Level",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Variable Group"],
    },
    "Ranking": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Ranking",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": [],
    },
    "Spatial Shape": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Spatial Shape",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Dimensions", "Structure", "Variables"],
    },
    "Structure": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Structure",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Variables"],
    },
    "Table Identifiers": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Table Identifiers",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Variables"],
    },
    "Temporal Shape": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Temporal Shape",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Dimensions", "Structure", "Variables"],
    },
    "Time Slice": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": "Time Slice",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": [],
    },
    "Variable Comments": {
        "source_base": "Data Request Variables (Public)",
        "source_table": "Comment",
        "internal_mapping": {},
        "internal_filters": {},
        "rm_keys": ["Variables"],
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
            }
        },
        "internal_filters": {
            "Final Opportunity selection": {"operator": "nonempty"},
            "Status (from Final Opportunity selection)": {
                "operator": "in",
                "values": ["Under review", "Accepted"],
            },
        },
        "rm_keys": ["Opportunity", "Theme"],
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
        "internal_filters": {
            "CMIP7 Variable Groups": {"operator": "nonempty"},
            "Opportunity Status (from CMIP7 Variable Groups)": {
                "operator": "in",
                "values": ["Under review", "Accepted"],
            },
        },
        "rm_keys": ["CMIP7 Variable Groups"],
    },
}

# Renaming of certain tables dependent on the release version
#  version : {table_name_old : table_name_new}
version_consistency = {
    "v1.0alpha": {
        "Frequency": "CMIP7 Frequency",
    },
}
