##########################################
# Consistency for raw export versions
##########################################
"""
Mapping Table

The mapping_table dictionary defines how to map the three-base structure to the one-base structure.
Each entry in the dictionary represents a table in the one-base structure and includes the information
how to obtain it from the three-base structure. Not all source tables are available in all content
versions of the data request. For example, "ESM-BCV 1.3" has been replaced with "ESM-BCV 1.4" in newer
content versions.

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

Internal renaming of keys to achieve consistency across content versions ("internal_consistency"):
    "internal_consistency" is a dictionary with the key corresponding to the record attributes
    to be renamed and the value containing the new name. This is required as some attributes have
    been renamed in newer content versions or are renamed when setting up releases with airtable.

Attributes to remove ("drop_keys"):
    List of record attributes that are not needed in the one-base (=release) structure.



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
                },
                "internal_consistency": {"OldFieldName": "NewFieldName"},
                "drop_keys": ["Field1", "Field2"],
      },
}
"""

mapping_table = {
    "CF Standard Names": {
        "source_base": "Data Request Physical Parameters (Public)",
        "source_table": ["CF Standard Name"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["Comments"],
        "internal_consistency": {
            "name": "Name",
            "Physical parameters 2": "Physical parameters",
        },
    },
    "CMIP6 Table Identifiers (legacy)": {
        "source_base": "Data Request Variables (Public)",
        "source_table": [
            "CMIP6 Table Identifiers (legacy)",
            "Table Identifiers",
        ],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": [],
        "internal_consistency": {
            "Comment": "Notes",
        },
    },
    "CMIP6 Frequency (legacy)": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["CMIP6 Frequency (legacy)", "Frequency"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": [],
        "internal_consistency": {},
    },
    "CMIP7 Frequency": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["CMIP7 Frequency"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": [],
        "internal_consistency": {
            "CMIP6 Frequency": "CMIP6 Frequency (legacy)",
        },
    },
    "Cell Measures": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["Cell Measures"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["Variables comments"],
        "internal_consistency": {},
    },
    "Cell Methods": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["Cell Methods"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["Comments"],
        "internal_consistency": {"Structure": "Structures", "uid": "UID"},
    },
    "Coordinates and Dimensions": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["Coordinate or Dimension"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["Variables (from Spatial shape)"],
        "internal_consistency": {
            "Requested Bounds]": "Requested Bounds",
            "Spatial shape": "Spatial Shape",
            "Temporal shape": "Temporal Shape",
        },
    },
    "Data Request Themes": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["Data Request Themes"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["Comments", "Experiment Group"],
        "internal_consistency": {
            "Opportunities led": "Lead theme for Opportunity",
            "Opportunity": "Tagged for Opportunity",
        },
    },
    "Docs for Opportunities": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["Docs for Opportunities"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["Base"],
        "internal_consistency": {"language identifier": "Language Identifier"},
    },
    "ESM-BCV 1.4": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["ESM-BCV 1.4", "Grid view"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["Modeling Realm (from CMOR Variables)", "V1.1"],
        "internal_consistency": {
            "CF Standard Name (from MIP Variables) 2 (from CMOR Variables)": (
                "CF Standard Name (from Physical Parameter) (from Variables)"
            ),
            "MIP Variables (from CMOR Variables)": (
                "Physical Parameter (from Variables)"
            ),
            "Title (from CMOR Variables)": "Title (from Variables)",
            "Units": "Units (from Physical Parameter) (from Variables)",
        },
    },
    "Experiment Group": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["Experiment Group"],
        "internal_mapping": {},
        "internal_filters": {
            "Status": {"aliases": [], "operator": "not in", "values": ["Junk"]},
            "Status (from Opportunities)": {
                "aliases": [],
                "operator": "in",
                "values": ["New", "Under review", "Accepted"],
            },
        },
        "drop_keys": [
            "Atmosphere author team review",
            "Comments",
            "Comments 2",
            "Earth System author team review",
            "Impacts & adaptation author team review",
            "Land & land-ice author team review",
            "Ocean & sea-ice author team review",
            "Opportunities",
            "Status",
            "Status (from Opportunities)",
            "Themes to alert",
        ],
        "internal_consistency": {},
    },
    "Experiments": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["Experiment"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": [],
        "internal_consistency": {
            "Unique list of variables attached to Opportunity (linked) (from Opportunity)": (
                "Variables"
            )
        },
    },
    "Glossary": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["Glossary"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": [],
        "internal_consistency": {},
    },
    "MIPs": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["MIP"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": [],
        "internal_consistency": {},
    },
    "Modelling Realm": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["Modeling Realm"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": [],
        "internal_consistency": {
            "Variables": "Variables - primary realm",
        },
    },
    "Opportunity": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["Opportunity"],
        "internal_mapping": {},
        "internal_filters": {
            "Status": {
                "aliases": [],
                "operator": "in",
                "values": ["Under review", "Accepted"],
            },
        },
        "drop_keys": [
            "Atmosphere author team review",
            "Atmosphere review comments",
            "Comments",
            "Cross-thematic group review",
            "Cross-thematic group review comments",
            "Earth system author team review",
            "Earth system review comments",
            "Impacts & adaptation author team review",
            "Impacts & adaptation review comments",
            "Land & land-ice author team review",
            "Land & land-ice review comments",
            "Ocean & sea-ice author team review",
            "Ocean & sea-ice review comments",
            "Originally Requested Variable Groups",
            "Status",
            "Unique list of variables attached to Opportunity (linked)",
        ],
        "internal_consistency": {
            "Ensemble Size": "Minimum ensemble Size",
            "Minimum Ensemble Size": "Minimum ensemble Size",
            "Unique list of experiments (for volume calculation)": (
                "Unique list of experiments (from Experiment Groups)"
            ),
            "Opportunity data volume estimate": "Data volume estimate",
            "Working/Updated Variable Groups": "Variable Groups",
            "Notes": "Technical Notes",
        },
    },
    "Physical Parameters": {
        "source_base": "Data Request Physical Parameters (Public)",
        "source_table": ["Physical Parameter"],
        "internal_mapping": {},
        "internal_filters": {},
        # "Opportunity Status (from CMIP7 Variable Groups) (from Variables) (from Link to back sync)": {
        #    "aliases": [],
        #    "operator": "in",
        #    "values": ["Under review", "Accepted"],
        # },
        "drop_keys": [
            "Atmosphere review comments",
            "Atmosphere team review status",
            "Comments",
            "Cross-thematic review comments",
            "Earth system team review status",
            "Impacts & adaptation team review status",
            "Land & land-ice team review status",
            "Ocean & sea-ice team review status",
            "Tagged author team",
        ],
        "internal_consistency": {
            "Proposal github issue": "CF Proposal Github Issue"
        },
    },
    "Priority Level": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["Priority level"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": [],
        "internal_consistency": {},
    },
    "Ranking": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["Ranking Synced"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": [],
        "internal_consistency": {"Name": "ID"},
    },
    "Spatial Shape": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["Spatial Shape"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["Comments"],
        "internal_consistency": {},
    },
    "Temporal Shape": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["Temporal Shape"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["Comments"],
        "internal_consistency": {},
    },
    "Time Subset": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["Time Subset", "Time Slice"],
        "internal_mapping": {},
        "internal_filters": {},
        "drop_keys": ["uid copy"],
        "internal_consistency": {
            "SliceLen": "SubsetLen",
            "sliceLenUnit": "subsetLenUnit",
            "uid": "UID",
        },
    },
    "Variable Group": {
        "source_base": "Data Request Opportunities (Public)",
        "source_table": ["Variable Group"],
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
            "Final Opportunity selection": {
                "aliases": [],
                "operator": "nonempty",
            },
            "Opportunity Status": {
                "aliases": ["Status (from Final Opportunity selection)"],
                "operator": "in",
                "values": ["Under review", "Accepted"],
            },
        },
        "drop_keys": [
            "Atmosphere author review Status",
            "Atmosphere author review comments",
            "Comments",
            "Cross-thematic author review comments",
            "Earth system author review status",
            "Originally requested for Opportunity",
            "Impacts & adaptation author review status",
            "Land & land-ice author review status",
            "Ocean & sea-ice author review comments",
            "Ocean & sea-ice author review status",
            "Opportunity Status",
            "Status",
            "Themes (from Opportunity)",
        ],
        "internal_consistency": {
            "Count (Variables)": "Number of variables in group",
            "Experiment Groups (from Final Opportunity selection)": "Experiment Groups (from Opportunity)",
            "Final Opportunity selection": "Opportunity",
        },
    },
    "Variables": {
        "source_base": "Data Request Variables (Public)",
        "source_table": ["Variable"],
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
            "CMIP7 Variable Groups": {"aliases": [], "operator": "nonempty"},
            "Opportunity Status (from CMIP7 Variable Groups)": {
                "aliases": [],
                "operator": "in",
                "values": ["Under review", "Accepted"],
            },
        },
        "drop_keys": [
            "Atmosphere author team review",
            "Atmosphere review comment",
            "Comments",
            "Created",
            "Cross-thematic group review comment",
            "Cross-thematic team review",
            "Earth system author team review",
            "Extra Dimensions",
            "Impacts & adaptation author team review",
            "Land & land-ice author team review",
            "Ocean & sea-ice author team review",
            "Opportunity Status (from CMIP7 Variable Groups)",
            "Priority 1 (CMIP6) -- OLD",
            "Priority 2 (CMIP6 - OLD",
            "Priority 3 (CMIP6 - OLD)",
            "Rank by File Count",
            "Rank by Submissions",
            "Rank by Volume",
            "Theme",
        ],
        "internal_consistency": {
            "CF Standard Name (from MIP Variables)": (
                "CF Standard Name (from Physical Parameter)"
            ),
            "Compound name": "CMIP6 Compound Name",
            "ESM-BCV 1.3": "ESM-BCV 1.4",
            "Min Rank": "Min Rank in CMIP6 download statistics",
            "Modeling Realm": "Modelling Realm - Primary",
            "Modeling Realm - Primary": "Modelling Realm - Primary",
            "Modeling Realm - Secondary": "Modelling Realm - Secondary",
            "Status": "Variable Status",
            "Status (from Physical Parameter)": "Physical Parameter Status",
            "Table": "CMIP6 Table (legacy)",
        },
    },
}


##########################################
# Consistency for release export versions
##########################################

# Renaming of certain tables dependent on the release version
#  table_name_old : table_name_new
version_consistency = {
    "Frequency": "CMIP7 Frequency",
    "Ranking Synced": "Ranking",
    "Table Identifiers": "CMIP6 Table Identifiers (legacy)",
    "Time Slice": "Time Subset",
}
# Drop the following tables (list of table names)
version_consistency_drop_tables = [
    "Structure",
]
# Renaming of certain fields dependent on the release version
#  {table_name_new :{field_name_old : field_name_new}}
version_consistency_fields = {
    "CMIP6 Frequency (legacy)": {
        "CMIP6 Frequency (legacy) 2": "CMIP6 Frequency",
    },
    "CMIP7 Frequency": {
        "CMIP6 Frequency 2": "CMIP6 Frequency (legacy)",
    },
    "Data Request Themes": {
        "UID 2": "UID",
    },
    "MIPs": {
        "Variable Group": "Variable Groups of interest",
    },
    "Modeling Realm": {
        "Variables": "Variables - primary realm",
    },
    "Opportunities": {
        "Time Slice": "Time Subset",
        "Notes": "Technical Notes",
    },
    "Time Subset": {
        "SliceLen": "SubsetLen",
        "sliceLenUnit": "subsetLenUnit",
    },
    "Variable Group": {
        "MIPs": "Of interest to MIPs",
    },
    "Variables": {
        "Modelling Realm": "Modelling Realm - Primary",
        "Compound name": "CMIP6 Compound Name",
        "Table": "CMIP6 Table (legacy)",
        "Contitional": "Conditional",
    },
}
# Drop the following fields for tables
#  {table: [field1, field2], ...}
version_consistency_drop_fields = {}
