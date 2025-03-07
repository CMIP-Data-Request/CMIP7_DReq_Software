#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data request.
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import argparse
import copy
import os
from collections import defaultdict

from data_request_api.stable.utilities.logger import get_logger, change_log_file, change_log_level
from data_request_api.stable.content.dump_transformation import transform_content
from data_request_api.stable.utilities.tools import read_json_file, write_csv_output_file_content
from data_request_api.stable.query.vocabulary_server import VocabularyServer, is_link_id_or_value, build_link_from_id, \
    to_singular

version = "1.0.1"


class ConstantValueObj(object):
    """
    Constant object which return the same value each time an attribute is asked.
    It is used to avoid discrepancies between objects and strings.
    """
    def __init__(self, value="undef"):
        self.value = value

    def __getattr__(self, item):
        return str(self)

    def __str__(self):
        return self.value

    def __hash__(self):
        return hash(self.value)

    def __copy__(self):
        return ConstantValueObj(self.value)

    def __eq__(self, other):
        return str(self) == str(other)

    def __gt__(self, other):
        return str(self) > str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    def __deepcopy__(self, memodict={}):
        return self.__copy__()


class DRObjects(object):
    """
    Base object to build the ones used within the DR API.
    Use to define basic information needed.
    """
    def __init__(self, id, dr, DR_type="undef", structure=dict(), **attributes):
        """
        Initialisation of the object.
        :param str id: id of the object
        :param DataRequest dr: reference data request object
        :param str DR_type: type of DR object (for reference in vocabulary server)
        :param dict structure: if needed, elements linked by structure to the current object
        :param dict attributes: attributes of the object coming from vocabulary server
        """
        self.DR_type = DR_type
        _, attributes["id"] = is_link_id_or_value(id)
        self.dr = dr
        self.attributes = self.transform_content(attributes, dr)
        self.structure = self.transform_content(structure, dr, force_transform=True)

    @staticmethod
    def transform_content_inner(key, value, dr, force_transform=False):
        if isinstance(value, str) and (force_transform or is_link_id_or_value(value)[0]):
            return dr.find_element(key, value)
        elif isinstance(value, str):
            return ConstantValueObj(value)
        else:
            return value

    def transform_content(self, input_dict, dr, force_transform=False):
        """
        Transform the input dict to have only elements which are object (either DRObject -for links- or
        ConstantValueObj -for strings-).
        :param dict input_dict: input dictionary to transform
        :param DataRequest dr: reference Data Request to find elements from VS
        :param bool force_transform: boolean indicating whether all elements should be considered as linked and
        transform into DRObject (True) or alternatively to DRObject if link or ConstantValueObj if string.
        :return dict: transformed dictionary
        """
        for (key, values) in input_dict.items():
            if isinstance(values, list):
                input_dict[key] = [self.transform_content_inner(key=key, value=value, dr=dr,
                                                                force_transform=force_transform) for value in values]
            else:
                input_dict[key] = self.transform_content_inner(key=key, value=values, dr=dr,
                                                               force_transform=force_transform)
        return input_dict

    @classmethod
    def from_input(cls, dr, id, DR_type="undef", elements=dict(), structure=dict()):
        """
        Create instance of the class using specific arguments.
        :param DataRequest dr: reference Data Request objects
        :param str id: id of the object
        :param str DR_type: type of the object
        :param dict elements: attributes of the objects (coming from VS)
        :param dict structure: structure of the object through Data Request
        :return: instance of the current class.
        """
        elements["id"] = id
        return cls(dr=dr, DR_type=DR_type, structure=structure, **elements)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.id == other.id and self.DR_type == other.DR_type and \
            self.structure == other.structure and self.attributes == other.attributes

    def __lt__(self, other):
        return self.id < other.id

    def __gt__(self, other):
        return self.id > other.id

    def __copy__(self):
        return type(self).__call__(dr=self.dr, DR_type=copy.deepcopy(self.DR_type),
                                   structure=copy.deepcopy(self.structure), **copy.deepcopy(self.attributes))

    def __deepcopy__(self, memodict={}):
        return self.__copy__()

    def check(self):
        """
        Make checks on the current object.
        :return:
        """
        pass

    def __str__(self):
        return os.linesep.join(self.print_content())

    def __repr__(self):
        return os.linesep.join(self.print_content())

    def __getattr__(self, item):
        return self.attributes.get(item, ConstantValueObj())

    def get(self, item):
        return self.__getattr__(item)

    def print_content(self, level=0, add_content=True):
        """
        Function to return a printable version of the content of the current class.
        :param level: level of indent of the result
        :param add_content: should inner content be added?
        :return: a list of strings that can be assembled to print the content.
        """
        indent = "    " * level
        return [f"{indent}{to_singular(self.DR_type)}: {self.name} (id: {is_link_id_or_value(self.id)[1]})", ]

    def filter_on_request(self, request_value):
        """
        Check whether the current object can be filtered by the requested value.
        :param request_value: an object to be tested
        :return bool, bool: a bool indicating whether the current object can be filtered by the requested one,
                            a bool indicating whether the current object is linked to the request one.
        """
        return request_value.DR_type == self.DR_type, request_value == self


class ExperimentsGroup(DRObjects):
    def __init__(self, id, dr, DR_type="experiment_groups", structure=dict(experiments=list()), **attributes):
        super().__init__(id=id, dr=dr, DR_type=DR_type, structure=structure, **attributes)

    def check(self):
        super().check()
        logger = get_logger()
        if self.count() == 0:
            logger.critical(f"No experiment defined for {self.DR_type} id {self.id}")

    def count(self):
        """
        Return the number of experiments linked to the ExperimentGroup
        :return int: number of experiments of the ExperimentGroup
        """
        return len(self.get_experiments())

    def get_experiments(self):
        """
        Return the list of experiments linked to the ExperimentGroup.
        :return list of DRObjects: list of the experiments linked to the ExperimentGroup
        """
        return self.structure["experiments"]

    def print_content(self, level=0, add_content=True):
        rep = super().print_content(level=level)
        if add_content:
            indent = "    " * (level + 1)
            rep.append(f"{indent}Experiments included:")
            for experiment in self.get_experiments():
                rep.extend(experiment.print_content(level=level + 2))
        return rep

    @classmethod
    def from_input(cls, dr, id, experiments=list(), **kwargs):
        return super().from_input(DR_type="experiment_groups", dr=dr, id=id, structure=dict(experiments=experiments),
                                  elements=kwargs)

    def filter_on_request(self, request_value):
        if request_value.DR_type in ["experiments", ]:
            return True, request_value in self.get_experiments()
        else:
            return super().filter_on_request(request_value=request_value)


class Variable(DRObjects):
    def __init__(self, id, dr, DR_type="variables", structure=dict(), **attributes):
        super().__init__(id=id, dr=dr, DR_type=DR_type, structure=structure, **attributes)

    @classmethod
    def from_input(cls, dr, id, **kwargs):
        return super().from_input(DR_type="variables", dr=dr, id=id, elements=kwargs, structure=dict())

    def print_content(self, level=0, add_content=True):
        """
        Function to return a printable version of the content of the current class.
        :param level: level of indent of the result
        :param add_content: should inner content be added?
        :return: a list of strings that can be assembled to print the content.
        """
        indent = "    " * level
        return [f"{indent}{self.DR_type.rstrip('s')}: {self.physical_parameter.name} at frequency "
                f"{self.cmip7_frequency.name} (id: {is_link_id_or_value(self.id)[1]}, title: {self.title})", ]

    def filter_on_request(self, request_value):
        request_type = request_value.DR_type
        if request_type in ["table_identifiers", ]:
            return True, request_value in self.table
        elif request_type in ["temporal_shape", ]:
            return True, request_value == self.temporal_shape
        elif request_type in ["spatial_shape", ]:
            return True, request_value == self.spatial_shape
        elif request_type in ["structure", ]:
            return True, request_value == self.structure_title
        elif request_type in ["physical_parameters", ]:
            return True, request_value == self.physical_parameter
        elif request_type in ["modelling_realm", ]:
            return True, request_value in self.modelling_realm
        elif request_type in ["esm-bcv", ]:
            return True, request_value == self.esm_bcv
        elif request_type in ["cf_standard_names", ]:
            return True, request_value == self.cf_standard_name
        elif request_type in ["cell_methods", ]:
            return True, request_value == self.cell_methods
        elif request_type in ["cell_measures", ]:
            return True, request_value == self.cell_measures
        else:
            return super().filter_on_request(request_value)


class VariablesGroup(DRObjects):
    def __init__(self, id, dr, DR_type="variable_groups",
                 structure=dict(variables=list(), mips=list(), priority_level="High"), **attributes):
        super().__init__(id=id, dr=dr, DR_type=DR_type, structure=structure, **attributes)

    def check(self):
        super().check()
        logger = get_logger()
        if self.count() == 0:
            logger.critical(f"No variable defined for {self.DR_type} id {self.id}")

    @classmethod
    def from_input(cls, dr, id, variables=list(), mips=list(), priority_level="High", **kwargs):
        return super().from_input(DR_type="variable_groups", dr=dr, id=id, elements=kwargs,
                                  structure=dict(variables=variables, mips=mips, priority_level=priority_level))

    def count(self):
        """
        Count the number of variables linked to the VariablesGroup.
        :return int: number of variables linked to the VariablesGroup
        """
        return len(self.get_variables())

    def get_variables(self):
        """
        Return the list of Variables linked to the VariablesGroup.
        :return list of Variable: list of Variable linked to VariablesGroup
        """
        return self.structure["variables"]

    def get_mips(self):
        """
        Return the list of MIPs linked to the VariablesGroup.
        :return list of DrObject: list of MIPs linked to VariablesGroup
        """
        return self.structure["mips"]

    def get_priority_level(self):
        """
        Return the priority level of the VariablesGroup.
        :return DrObject: priority level of VariablesGroup
        """
        return self.structure["priority_level"]

    def print_content(self, level=0, add_content=True):
        rep = super().print_content(level=level)
        if add_content:
            indent = "    " * (level + 1)
            rep.append(f"{indent}Variables included:")
            for variable in self.get_variables():
                rep.extend(variable.print_content(level=level + 2))
        return rep

    def filter_on_request(self, request_value):
        request_type = request_value.DR_type
        if request_type in ["variables", ]:
            return True, request_value in self.get_variables()
        elif request_type in ["mips", ]:
            return True, request_value in self.get_mips()
        elif request_type in ["max_priority_level", ]:
            priority = self.dr.find_element("priority_level", self.get_priority_level().id)
            req_priority = self.dr.find_element("priority_level", request_value.id)
            return True, priority.value < req_priority.value
        elif request_type in ["priority_level", ]:
            _, priority = is_link_id_or_value(self.get_priority_level().id)
            _, req_priority = is_link_id_or_value(request_value.id)
            return True, req_priority == priority
        elif request_type in ["table_identifiers", "temporal_shape", "spatial_shape", "structure",
                              "physical_parameters", "modelling_realm", "esm-bcv", "cf_standard_names", "cell_methods",
                              "cell_measures"]:
            return True, any(var.filter_on_request(request_value=request_value)[1] for var in self.get_variables())
        else:
            return super().filter_on_request(request_value=request_value)


class Opportunity(DRObjects):
    def __init__(self, id, dr, DR_type="opportunities",
                 structure=dict(experiment_groups=list(), variable_groups=list(), data_request_themes=list(),
                                time_subsets=list()),
                 **attributes):
        super().__init__(id=id, dr=dr, DR_type=DR_type, structure=structure, **attributes)

    def check(self):
        super().check()
        logger = get_logger()
        if len(self.get_experiment_groups()) == 0:
            logger.critical(f"No experiments group defined for {self.DR_type} id {self.id}")
        if len(self.get_variable_groups()) == 0:
            logger.critical(f"No variables group defined for {self.DR_type} id {self.id}")
        if len(self.get_data_request_themes()) == 0:
            logger.critical(f"No theme defined for {self.DR_type} id {self.id}")

    @classmethod
    def from_input(cls, dr, id, experiment_groups=list(), variable_groups=list(), data_request_themes=list(),
                   time_subsets=list(), mips=list(), **kwargs):

        return super().from_input(DR_type="opportunities", dr=dr, id=id, elements=kwargs,
                                  structure=dict(experiment_groups=experiment_groups, variable_groups=variable_groups,
                                                 data_request_themes=data_request_themes, time_subsets=time_subsets,
                                                 mips=mips))

    def get_experiment_groups(self):
        """
        Return the list of ExperimentsGroup linked to the Opportunity.
        :return list of ExperimentsGroup: list of ExperimentsGroup linked to Opportunity
        """
        return self.structure["experiment_groups"]

    def get_variable_groups(self):
        """
        Return the list of VariablesGroup linked to the Opportunity.
        :return list of VariablesGroup: list of VariablesGroup linked to Opportunity
        """
        return self.structure["variable_groups"]

    def get_data_request_themes(self):
        """
        Return the list of themes linked to the Opportunity.
        :return list of DRObject or ConstantValueObj: list of themes linked to Opportunity
        """
        return self.structure["data_request_themes"]

    def get_themes(self):
        """
        Return the list of themes linked to the Opportunity.
        :return list of DRObject or ConstantValueObj: list of themes linked to Opportunity
        """
        return self.get_data_request_themes()

    def get_time_subsets(self):
        """
        Return the list of time subsets linked to the Opportunity.
        :return list of DRObject: list of time subsets linked to Opportunity
        """
        return self.structure["time_subsets"]

    def get_mips(self):
        """
        Return the list of MIPs linked to the Opportunity.
        :return list of DRObject: list of MIPs linked to Opportunity
        """
        return self.structure["mips"]

    def print_content(self, level=0, add_content=True):
        rep = super().print_content(level=level)
        if add_content:
            indent = "    " * (level + 1)
            rep.append(f"{indent}Experiments groups included:")
            for experiments_group in self.get_experiment_groups():
                rep.extend(experiments_group.print_content(level=level + 2, add_content=False))
            rep.append(f"{indent}Variables groups included:")
            for variables_group in self.get_variable_groups():
                rep.extend(variables_group.print_content(level=level + 2, add_content=False))
            rep.append(f"{indent}Themes included:")
            for theme in self.get_data_request_themes():
                rep.extend(theme.print_content(level=level + 2, add_content=False))
            rep.append(f"{indent}Time subsets included:")
            for time_subset in self.get_time_subsets():
                rep.extend(time_subset.print_content(level=level + 2, add_content=False))
        return rep

    def filter_on_request(self, request_value):
        request_type = request_value.DR_type
        if request_type in ["data_request_themes", ]:
            return True, request_value in self.get_data_request_themes()
        elif request_type in ["experiment_groups", ]:
            return True, request_value in self.get_experiment_groups()
        elif request_type in ["variable_groups", ]:
            return True, request_value in self.get_variable_groups()
        elif request_type in ["time_subset", ]:
            return True, request_value in self.get_time_subsets()
        elif request_type in ["mips", ]:
            return True, request_value in self.get_mips() or \
                         any(var_grp.filter_on_request(request_value=request_value)[1]
                             for var_grp in self.get_variable_groups())
        elif request_type in ["variables", "priority_level", "table_identifiers", "temporal_shape",
                              "spatial_shape", "structure", "physical_parameters", "modelling_realm", "esm-bcv",
                              "cf_standard_names", "cell_methods", "cell_measures", "max_priority_level"]:
            return True, any(var_grp.filter_on_request(request_value=request_value)[1]
                             for var_grp in self.get_variable_groups())
        elif request_type in ["experiments", ]:
            return True, any(exp_grp.filter_on_request(request_value=request_value)[1]
                             for exp_grp in self.get_experiment_groups())
        else:
            return super().filter_on_request(request_value=request_value)


class DataRequest(object):
    """
    Data Request API object used to navigate among the Data Request and Vocabulary Server contents.
    """
    def __init__(self, input_database, VS, **kwargs):
        """
        Initialisation of the Data Request object
        :param dict input_database: dictionary containing the DR database
        :param VocabularyServer VS: reference Vocabulary Server to et information on objects
        :param dict kwargs: additional parameters
        """
        self.VS = VS
        self.content_version = input_database["version"]
        self.structure = input_database
        self.mapping = defaultdict(lambda: defaultdict(lambda: dict))
        self.content = defaultdict(lambda: defaultdict(lambda: dict))
        for op in input_database["opportunities"]:
            self.content["opportunities"][op] = self.find_element("opportunities", op)
        self.cache = dict()

    def check(self):
        """
        Method to check the content of the Data Request.
        :return:
        """
        logger = get_logger()
        logger.info("Check data request metadata")
        logger.info("... Check experiments groups")
        for elt in self.get_experiment_groups():
            elt.check()
        logger.info("... Check variables groups")
        for elt in self.get_variable_groups():
            elt.check()
        logger.info("... Check opportunities")
        for elt in self.get_opportunities():
            elt.check()

    @property
    def software_version(self):
        """
        Method to get the version of the software.
        :return str: version of the software
        """
        return version

    @property
    def version(self):
        """
        Method to get the version of both software and content
        :return str : formatted version of the software and the content
        """
        return f"Software {self.software_version} - Content {self.content_version}"

    @classmethod
    def from_input(cls, json_input, version, **kwargs):
        """
        Method to instanciate the DataRequest object from a single input.
        :param str or dict json_input: dictionary or name of the dedicated json file containing the export content
        :param str version: version of the content
        :param dict kwargs: additional parameters
        :return DataRequest: instance of the DataRequest object.
        """
        DR_content, VS_content = cls._split_content_from_input_json(json_input, version=version)
        VS = VocabularyServer(VS_content)
        return cls(input_database=DR_content, VS=VS, **kwargs)

    @classmethod
    def from_separated_inputs(cls, DR_input, VS_input, **kwargs):
        """
        Method to instanciate the DataRequestObject from two inputs.
        :param str or dict DR_input: dictionary or name of the json file containing the data request structure
        :param str or dict VS_input: dictionary or name of the json file containing the vocabulary server
        :param dict kwargs: additional parameters
        :return DataRequest: instance of the DataRequest object
        """
        logger = get_logger()
        if isinstance(DR_input, str) and os.path.isfile(DR_input):
            DR = read_json_file(DR_input)
        elif isinstance(DR_input, dict):
            DR = copy.deepcopy(DR_input)
        else:
            logger.error("DR_input should be either the name of a json file or a dictionary.")
            raise TypeError("DR_input should be either the name of a json file or a dictionary.")
        if isinstance(VS_input, str) and os.path.isfile(VS_input):
            VS = VocabularyServer.from_input(VS_input)
        elif isinstance(VS_input, dict):
            VS = VocabularyServer(copy.deepcopy(VS_input))
        else:
            logger.error("VS_input should be either the name of a json file or a dictionary.")
            raise TypeError("VS_input should be either the name of a json file or a dictionary.")
        return cls(input_database=DR, VS=VS, **kwargs)

    @staticmethod
    def _split_content_from_input_json(input_json, version):
        """
        Split the export if given through a single file and not from two files into the two dictionaries.
        :param dict or str input_json: json input containing the bases or content as a dict
        :param str version: version of the content used
        :return dict, dict: two dictionaries containing the DR and the VS
        """
        logger = get_logger()
        if not isinstance(version, str):
            logger.error(f"Version should be a string, not {type(version).__name__}.")
            raise TypeError(f"Version should be a string, not {type(version).__name__}.")
        if isinstance(input_json, str) and os.path.isfile(input_json):
            content = read_json_file(input_json)
        elif isinstance(input_json, dict):
            content = input_json
        else:
            logger.error("input_json should be either the name of a json file or a dictionary.")
            raise TypeError("input_json should be either the name of a json file or a dictionary.")
        DR, VS = transform_content(content, version=version)
        return DR, VS

    def __str__(self):
        rep = list()
        indent = "    "
        rep.append("Data Request content:")
        rep.append(f"{indent}Experiments groups:")
        for elt in self.get_experiment_groups():
            rep.extend(elt.print_content(level=2))
        rep.append(f"{indent}Variables groups:")
        for elt in self.get_variable_groups():
            rep.extend(elt.print_content(level=2))
        rep.append(f"{indent}Opportunities:")
        for elt in self.get_opportunities():
            rep.extend(elt.print_content(level=2))
        return os.linesep.join(rep)

    def _get_sorted_list(self, list_id):
        if self.cache.get(list_id) is None:
            self.cache[list_id] = [self.content[list_id][key] for key in sorted(list(self.content[list_id]))]
        return self.cache[list_id]

    def get_experiment_groups(self):
        """
        Get the ExperimentsGroup of the Data Request.
        :return list of ExperimentsGroup: list of the ExperimentsGroup of the DR content.
        """
        return self._get_sorted_list("experiment_groups")

    def get_experiment_group(self, id):
        """
        Get the ExperimentsGroup associated with a specific id.
        :param str id: id of the ExperimentsGroup
        :return ExperimentsGroup: the ExperimentsGroup associated with the input id
        """
        rep = self.find_element("experiment_groups", id, default=None)
        if rep is not None:
            return rep
        else:
            raise ValueError(f"Could not find experiments group {id} among {self.get_experiment_groups()}.")

    def get_variable_groups(self):
        """
        Get the VariablesGroup of the Data Request.
        :return list of VariablesGroup: list of the VariablesGroup of the DR content.
        """
        return self._get_sorted_list("variable_groups")

    def get_variable_group(self, id):
        """
        Get the VariablesGroup associated with a specific id.
        :param str id: id of the VariablesGroup
        :return VariablesGroup: the VariablesGroup associated with the input id
        """
        rep = self.find_element("variable_groups", id, default=None)
        if rep is not None:
            return rep
        else:
            raise ValueError(f"Could not find variables group {id}.")

    def get_opportunities(self):
        """
        Get the Opportunity of the Data Request.
        :return list of Opportunity: list of the Opportunity of the DR content.
        """
        return self._get_sorted_list("opportunities")

    def get_opportunity(self, id):
        """
        Get the Opportunity associated with a specific id.
        :param str id: id of the Opportunity
        :return Opportunity: the Opportunity associated with the input id
        """
        rep = self.find_element("opportunities", id, default=None)
        if rep is not None:
            return rep
        else:
            raise ValueError(f"Could not find opportunity {id}.")

    def get_variables(self):
        """
        Get the Variable of the Data Request.
        :return list of Variable: list of the Variable of the DR content.
        """
        if self.cache.get("variables") is None:
            rep = set()
            for var_grp in self.get_variable_groups():
                rep = rep | set(var_grp.get_variables())
            self.cache["variables"] = sorted(list(rep))
        return self.cache["variables"]

    def get_mips(self):
        """
        Get the MIPs of the Data Request.
        :return list of DRObject or ConstantValueObj: list of the MIPs of the DR content.
        """
        if self.cache.get("mips") is None:
            rep = set()
            for op in self.get_opportunities():
                rep = rep | set(op.get_mips())
            for var_grp in self.get_variable_groups():
                rep = rep | set(var_grp.get_mips())
            self.cache["mips"] = sorted(list(rep))
        return self.cache["mips"]

    def get_experiments(self):
        """
        Get the experiments of the Data Request.
        :return list of DRObject: list of the experiments of the DR content.
        """
        if self.cache.get("experiments") is None:
            rep = set()
            for exp_grp in self.get_experiment_groups():
                rep = rep | set(exp_grp.get_experiments())
            self.cache["experiments"] = sorted(list(rep))
        return self.cache["experiments"]

    def get_data_request_themes(self):
        """
        Get the themes of the Data Request.
        :return list of DRObject: list of the themes of the DR content.
        """
        if self.cache.get("data_request_themes") is None:
            rep = set()
            for op in self.get_opportunities():
                rep = rep | set(op.get_themes())
            self.cache["data_request_themes"] = sorted(list(rep))
        return self.cache["data_request_themes"]

    def find_variables_per_priority(self, priority):
        """
        Find all the variables which have a specified priority.
        :param DRObjects or ConstantValueObj or str priority: priority to be considered
        :return list of Variable: list of the variables which have a specified priority.
        """
        return self.filter_elements_per_request(elements_to_filter="variables",
                                                requests=dict(priority_level=[priority, ]))

    def find_opportunities_per_theme(self, theme):
        """
        Find all the opportunities which are linked to a specified theme.
        :param DRObjects or ConstantValueObj or str theme: theme to be considered
        :return list of Opportunity: list of the opportunities which are linked to a specified theme.
        """
        return self.filter_elements_per_request(elements_to_filter="opportunities",
                                                requests=dict(data_request_themes=[theme, ]))

    def find_experiments_per_theme(self, theme):
        """
        Find all the experiments which are linked to a specified theme.
        :param DRObjects or ConstantValueObj or str theme: theme to be considered
        :return list of DRObjects or ConstantValueObj: list of the experiments which are linked to a specified theme.
        """
        return self.filter_elements_per_request(elements_to_filter="experiments",
                                                requests=dict(data_request_themes=[theme, ]))

    def find_variables_per_theme(self, theme):
        """
        Find all the variables which are linked to a specified theme.
        :param DRObjects or ConstantValueObj or str theme: theme to be considered
        :return list of Variable: list of the variables which are linked to a specified theme.
        """
        return self.filter_elements_per_request(elements_to_filter="variables",
                                                requests=dict(data_request_themes=[theme, ]))

    def find_mips_per_theme(self, theme):
        """
        Find all the MIPs which are linked to a specified theme.
        :param DRObjects or ConstantValueObj or str theme: theme to be considered
        :return list of DRObjects or ConstantValueObj: list of the MIPs which are linked to a specified theme.
        """
        return self.filter_elements_per_request(elements_to_filter="mips", requests=dict(data_request_themes=[theme, ]))

    def find_themes_per_opportunity(self, opportunity):
        """
        Find all the themes which are linked to a specified opportunity.
        :param Opportunity or str opportunity: opportunity to be considered
        :return list of DRObjects or ConstantValueObj: list of the themes which are linked to a specified opportunity.
        """
        return self.filter_elements_per_request(elements_to_filter="data_request_themes",
                                                requests=dict(opportunities=[opportunity, ]))

    def find_experiments_per_opportunity(self, opportunity):
        """
        Find all the experiments which are linked to a specified opportunity.
        :param Opportunity or str opportunity: opportunity to be considered
        :return list of DRObjects or ConstantValueObj: list of the experiments which are linked to a specified
                opportunity.
        """
        return self.filter_elements_per_request(elements_to_filter="experiments",
                                                requests=dict(opportunities=[opportunity, ]))

    def find_variables_per_opportunity(self, opportunity):
        """
        Find all the variables which are linked to a specified opportunity.
        :param Opportunity or str opportunity: opportunity to be considered
        :return list of Variable: list of the variables which are linked to a specified opportunity.
        """
        return self.filter_elements_per_request(elements_to_filter="variables",
                                                requests=dict(opportunities=[opportunity, ]))

    def find_mips_per_opportunity(self, opportunity):
        """
        Find all the MIPs which are linked to a specified opportunity.
        :param Opportunity or str opportunity: opportunity to be considered
        :return list of DRObjects or ConstantValueObj: list of the MIPs which are linked to a specified opportunity.
        """
        return self.filter_elements_per_request(elements_to_filter="mips", requests=dict(opportunities=[opportunity, ]))

    def find_opportunities_per_variable(self, variable):
        """
        Find all the opportunities which are linked to a specified variable.
        :param Variable or str variable: variable to be considered
        :return list of Opportunity: list of the opportunities which are linked to a specified variable.
        """
        return self.filter_elements_per_request(elements_to_filter="opportunities",
                                                requests=dict(variables=[variable, ]))

    def find_themes_per_variable(self, variable):
        """
        Find all the themes which are linked to a specified variable.
        :param Variable or str variable: variable to be considered
        :return list of DRObjects or ConstantValueObj: list of the themes which are linked to a specified variable.
        """
        return self.filter_elements_per_request(elements_to_filter="data_request_themes",
                                                requests=dict(variables=[variable, ]))

    def find_mips_per_variable(self, variable):
        """
        Find all the MIPs which are linked to a specified variable.
        :param Variable or str variable: variable to be considered
        :return list of DRObjects or ConstantValueObj: list of the MIPs which are linked to a specified variable.
        """
        return self.filter_elements_per_request(elements_to_filter="mips", requests=dict(variables=[variable, ]))

    def find_opportunities_per_experiment(self, experiment):
        """
        Find all the opportunities which are linked to a specified experiment.
        :param DRObjects or ConstantValueObj or str experiment: experiment to be considered
        :return list of Opportunity: list of the opportunities which are linked to a specified experiment.
        """
        return self.filter_elements_per_request(elements_to_filter="opportunities",
                                                requests=dict(experiments=[experiment, ]))

    def find_themes_per_experiment(self, experiment):
        """
        Find all the themes which are linked to a specified experiment.
        :param DRObjects or ConstantValueObj or str experiment: experiment to be considered
        :return list of DRObjects or ConstantValueObj: list of the themes which are linked to a specified experiment.
        """
        return self.filter_elements_per_request(elements_to_filter="data_request_themes",
                                                requests=dict(experiments=[experiment, ]))

    def find_element_per_identifier_from_vs(self, element_type, key, value, default=False, **kwargs):
        """
        Find an element of a specific type and specified by a value (of a given kind) from vocabulary server.
        :param str element_type: type of the element to be found (same as in vocabulary server).
        :param str key: type of the value key to be looked for ("id", "name"...)
        :param str value: value to be looked for
        :param default: default value to be used if the value is not found
        :param dict kwargs: additional attributes to be used for vocabulary server search.
        :return Opportunity or VariablesGroup or ExperimentsGroup or Variables or DRObjects or ConstantValueObj or
                default: the element found from vocabulary server or the default value if none is found.
        """
        if key in ["id", ]:
            value = build_link_from_id(value)
        rep = self.VS.get_element(element_type=element_type, element_id=value, id_type=key, default=default, **kwargs)
        if rep not in [default, ]:
            structure = self.structure.get(element_type, dict()).get(rep["id"], dict())
            if element_type in ["opportunities", ]:
                rep = Opportunity.from_input(dr=self, **rep, **structure)
            elif element_type in ["variable_groups", ]:
                rep = VariablesGroup.from_input(dr=self, **rep, **structure)
            elif element_type in ["experiment_groups", ]:
                rep = ExperimentsGroup.from_input(dr=self, **rep, **structure)
            elif element_type in ["variables", ]:
                rep = Variable.from_input(dr=self, **rep)
            else:
                rep = DRObjects.from_input(dr=self, id=rep["id"], DR_type=element_type, elements=rep)
        return rep

    def find_element_from_vs(self, element_type, value, default=False):
        """
        Find an element of a specific type and specified by a value from vocabulary server.
        Update the content and mapping list not to have to ask the vocabulary server again for it.
        :param str element_type: kind of element to be looked for
        :param str value: value to be looked for
        :param default: default value to be returned if no value found
        :return: element corresponding to the specified value of a given type if found, else the default value
        """
        rep = self.find_element_per_identifier_from_vs(element_type=element_type, value=value, key="id", default=None)
        if rep is None:
            rep = self.find_element_per_identifier_from_vs(element_type=element_type, value=value, key="name",
                                                           default=default)
        if rep not in [default, ]:
            self.content[element_type][rep.id] = rep
            self.mapping[element_type][rep.name] = rep
        return rep

    def find_element(self, element_type, value, default=False):
        """
        Find an element of a specific type and specified by a value from mapping/content if existing,
         else from vocabulary server.
        :param str element_type: kind of element to be found
        :param str value: value to be looked for
        :param default: value to be returned if non found
        :return: the found element if existing, else the default value
        """
        check_val = is_link_id_or_value(value)[1]
        if check_val in self.content[element_type]:
            return self.content[element_type][check_val]
        elif check_val in self.mapping[element_type]:
            return self.mapping[element_type][check_val]
        else:
            return self.find_element_from_vs(element_type=element_type, value=value, default=default)

    def get_elements_per_kind(self, element_type):
        """
        Return the list of elements of kind element_type
        :param str element_type: the kind of the elements to be found
        :return list: the list of elements of kind element_type
        """
        logger = get_logger()
        if element_type in ["opportunities", ]:
            elements = self.get_opportunities()
        elif element_type in ["experiment_groups", ]:
            elements = self.get_experiment_groups()
        elif element_type in ["variable_groups", ]:
            elements = self.get_variable_groups()
        elif element_type in ["variables", ]:
            elements = self.get_variables()
        elif element_type in ["experiments", ]:
            elements = self.get_experiments()
        elif element_type in ["data_request_themes", ]:
            elements = self.get_data_request_themes()
        elif element_type in ["mips", ]:
            elements = self.get_mips()
        else:
            logger.debug("Find elements list from vocabulary server.")
            element_type, elements_ids = self.VS.get_element_type_ids(element_type)
            elements = [self.find_element(element_type, id) for id in elements_ids]
        return elements

    @staticmethod
    def _two_elements_filtering(filtering_elt_1, filtering_elt_2, list_to_filter):
        """
        Check if a list of elements can be filtered by two values
        :param filtering_elt_1: first element for filtering
        :param filtering_elt_2: second element for filtering
        :param list list_to_filter: list of elements to be filtered
        :return bool, bool: a boolean to tell if it relevant to filter list_to_filter by filtering_elt_1 and
                            filtering_elt_2, a boolean to tell, if relevant, if filtering_elt_1 and filtering_elt_2 are
                             linked to list_to_filter
        """
        elt = list_to_filter[0]
        filtered_found_1, found_1 = elt.filter_on_request(filtering_elt_1)
        filtered_found_2, found_2 = elt.filter_on_request(filtering_elt_2)
        filtered_found = filtered_found_1 and filtered_found_2
        found = found_1 and found_2
        if filtered_found and not found:
            found = any([elt.filter_on_request(filtering_elt_1)[1] and
                         elt.filter_on_request(filtering_elt_2)[1]
                         for elt in list_to_filter])
        return filtered_found, found

    def filter_elements_per_request(self, elements_to_filter, requests=dict(), operation="all", skip_if_missing=False):
        """
        Filter the elements of kind element_type with a dictionary of requests.
        :param str or list od DRObjects elements_to_filter: kind of elements to be filtered
        :param dict requests: dictionary of the filters to be applied
        :param str operation: should at least one filter be applied ("any") or all filters be fulfilled ("all")
        :param bool skip_if_missing: if a request filter is missing, should it be skipped or should an error be raised?
        :return: list of elements of kind element_type which correspond to the filtering requests
        """
        logger = get_logger()
        if operation not in ["any", "all"]:
            raise ValueError(f"Operation does not accept {operation} as value: choose among 'any' (match at least one"
                             f" requirement) and 'all' (match all requirements)")
        else:
            # Prepare the request dictionary
            request_dict = defaultdict(list)
            for (req, values) in requests.items():
                if not isinstance(values, list):
                    values = [values, ]
                for val in values:
                    if isinstance(val, str):
                        new_val = self.find_element(element_type=req, value=val, default=None)
                    else:
                        new_val = val
                    if new_val is not None:
                        request_dict[req].append(new_val)
                    elif skip_if_missing:
                        logger.warning(f"Could not find value {val} for element type {req}, skip it.")
                    else:
                        logger.error(f"Could not find value {val} for element type {req}.")
                        raise ValueError(f"Could not find value {val} for element type {req}.")
            # Get elements corresponding to element_type
            if isinstance(elements_to_filter, str):
                elements = self.get_elements_per_kind(elements_to_filter)
            else:
                elements = elements_to_filter
                elements_to_filter = elements[0].DR_type
            # Filter elements
            rep = defaultdict(lambda: defaultdict(set))
            for (request, values) in request_dict.items():
                for val in values:
                    for elt in elements:
                        filtered_found, found = elt.filter_on_request(val)
                        if not filtered_found:
                            filtered_found, found = val.filter_on_request(elt)
                        if not filtered_found:
                            filtered_found, found = self._two_elements_filtering(val, elt, self.get_experiment_groups())
                        if not filtered_found:
                            filtered_found, found = self._two_elements_filtering(val, elt, self.get_variables())
                        if not filtered_found:
                            filtered_found, found = self._two_elements_filtering(val, elt, self.get_variable_groups())
                        if not filtered_found:
                            filtered_found, found = self._two_elements_filtering(val, elt, self.get_opportunities())
                        if not filtered_found:
                            logger.error(f"Could not filter {elements_to_filter} by {request}")
                            raise ValueError(f"Could not filter {elements_to_filter} by {request}")
                        if found:
                            rep[request][val.id].add(elt)
            if len(rep) == 0:
                rep_list = set(elements)
            elif operation in ["any", ]:
                rep_list = set()
                for req in rep:
                    for val in rep[req]:
                        rep_list = rep_list | rep[req][val]
            elif operation in ["all", ]:
                rep_list = set(elements)
                for req in rep:
                    for val in rep[req]:
                        rep_list = rep_list & rep[req][val]
            else:
                raise ValueError(f"Unknown value {operation} for operation (only 'all' and 'any' are available).")
            rep_list = sorted(list(rep_list))
            return rep_list

    def find_opportunities(self, operation="any", skip_if_missing=False, **kwargs):
        """
        Find the opportunities corresponding to filtering criteria.
        :param str operation: should at least one filter be applied ("any") or all filters be fulfilled ("all")
        :param bool skip_if_missing: if a request filter is missing, should it be skipped or should an error be raised?
        :param dict kwargs: filters to be applied
        :return list of Opportunity: opportunities linked to the filters
        """
        return self.filter_elements_per_request(elements_to_filter="opportunities", requests=kwargs,
                                                operation=operation, skip_if_missing=skip_if_missing)

    def find_experiments(self, operation="any", skip_if_missing=False, **kwargs):
        """
        Find the experiments corresponding to filtering criteria.
        :param str operation: should at least one filter be applied ("any") or all filters be fulfilled ("all")
        :param bool skip_if_missing: if a request filter is missing, should it be skipped or should an error be raised?
        :param dict kwargs: filters to be applied
        :return list of DRObjects: experiments linked to the filters
        """
        return self.filter_elements_per_request(elements_to_filter="experiments", requests=kwargs, operation=operation,
                                                skip_if_missing=skip_if_missing)

    def find_variables(self, operation="any", skip_if_missing=False, **kwargs):
        """
        Find the variables corresponding to filtering criteria.
        :param str operation: should at least one filter be applied ("any") or all filters be fulfilled ("all")
        :param bool skip_if_missing: if a request filter is missing, should it be skipped or should an error be raised?
        :param dict kwargs: filters to be applied
        :return list of Variable: variables linked to the filters
        """
        return self.filter_elements_per_request(elements_to_filter="variables", requests=kwargs, operation=operation,
                                                skip_if_missing=skip_if_missing)

    def sort_func(self, data_list, sorting_request=list()):
        """
        Method to sort a list of objects based on some criteria
        :param list data_list: the list of objects to be sorted
        :param list sorting_request: list of criteria to sort the input list
        :return list: sorted list
        """
        sorting_request = copy.deepcopy(sorting_request)
        if len(sorting_request) == 0:
            return sorted(data_list, key=lambda x: x.id)
        else:
            sorting_val = sorting_request.pop(0)
            sorting_values_dict = defaultdict(list)
            for data in data_list:
                sorting_values_dict[data.get(sorting_val)].append(data)
            rep = list()
            for elt in sorted(list(sorting_values_dict)):
                rep.extend(self.sort_func(sorting_values_dict[elt], sorting_request))
            return rep

    def export_data(self, main_data, output_file, filtering_requests=dict(), filtering_operation="all",
                    filtering_skip_if_missing=False, export_columns_request=list(), sorting_request=list(), **kwargs):
        """
        Method to export a filtered and sorted list of data to a csv file.
        :param str main_data: kind of data to be exported
        :param str output_file: name of the output faile (csv)
        :param dict filtering_requests: filtering request to be applied to the list of object of main_data kind
        :param str filtering_operation: filtering operation to be applied to the list of object of main_data kind
        :param bool filtering_skip_if_missing: filtering skip_if_missing to be applied to the list of object of
                                               main_data kind
        :param list export_columns_request: columns to be putted in the output file
        :param list sorting_request: sorting criteria to be applied
        :param dict kwargs: additional arguments to be given to function write_csv_output_file_content
        :return: an output csv file
        """
        filtered_data = self.filter_elements_per_request(elements_to_filter=main_data, requests=filtering_requests,
                                                         operation=filtering_operation,
                                                         skip_if_missing=filtering_skip_if_missing)
        sorted_filtered_data = self.sort_func(filtered_data, sorting_request)

        export_columns_request.insert(0, "id")
        content = list()
        content.append(export_columns_request)
        for data in sorted_filtered_data:
            content.append([str(data.__getattr__(key)) for key in export_columns_request])

        write_csv_output_file_content(output_file, content, **kwargs)

    def export_summary(self, lines_data, columns_data, output_file, sorting_line="id", title_line="name",
                       sorting_column="id", title_column="name", filtering_requests=dict(), filtering_operation="all",
                       filtering_skip_if_missing=False, **kwargs):
        """
        Create a 2D tables of csv kind which give the linked between the two list of elements kinds specified
        :param str lines_data: kind of data to be put in row
        :param str columns_data: kind of data to be put in range
        :param str output_file: name of the output file (csv)
        :param str sorting_line: criteria to sort raw data
        :param str title_line: attribute to be used for raw header
        :param str sorting_column: criteria to sort range data
        :param str title_column: attribute to be used for range header
        :param dict filtering_requests: filtering request to be applied to the list of object of main_data kind
        :param str filtering_operation: filtering operation to be applied to the list of object of main_data kind
        :param bool filtering_skip_if_missing: filtering skip_if_missing to be applied to the list of object of
                                               main_data kind
        :param dict kwargs: additional arguments to be given to function write_csv_output_file_content
        :return: a csv output file
        """
        logger = get_logger()
        logger.debug(f"Generate summary for {lines_data}/{columns_data}")
        filtered_data = self.filter_elements_per_request(elements_to_filter=lines_data, requests=filtering_requests,
                                                         operation=filtering_operation,
                                                         skip_if_missing=filtering_skip_if_missing)
        sorted_filtered_data = self.sort_func(filtered_data, sorting_request=[sorting_line, ])
        columns_datasets = self.filter_elements_per_request(elements_to_filter=columns_data)
        columns_datasets = self.sort_func(columns_datasets, sorting_request=[sorting_column, ])
        columns_title = [str(elt.__getattr__(title_column)) for elt in columns_datasets]
        table_title = f"{lines_data} {title_line} / {columns_data} {title_column}"
        lines_title = {elt.id: elt.__getattr__(title_line) for elt in sorted_filtered_data}

        nb_lines = len(sorted_filtered_data)
        logger.debug(f"{nb_lines} elements found for {lines_data}")
        logger.debug(f"{len(columns_title)} found elements for {columns_data}")

        logger.debug("Generate summary")
        content = defaultdict(lambda: dict())
        DR_type = columns_datasets[0].DR_type
        for (column_data, column_title) in zip(columns_datasets, columns_title):
            filter_line_datasets = self.filter_elements_per_request(elements_to_filter=sorted_filtered_data,
                                                                    requests={DR_type: column_data}, operation="all")
            for line in filter_line_datasets:
                content[lines_title[line.id]][column_title] = "x"

        logger.debug("Format summary")
        rep = list()
        rep.append([table_title, ] + columns_title)
        for line_data in sorted_filtered_data:
            line_data_title = lines_title[line_data.id]
            rep.append([line_data_title, ] +
                       [content[line_data_title].get(column_title, "") for column_title in columns_title])

        logger.debug("Write summary")
        write_csv_output_file_content(output_file, rep, **kwargs)


if __name__ == "__main__":
    change_log_file(default=True)
    change_log_level("debug")
    parser = argparse.ArgumentParser()
    parser.add_argument("--DR_json", default="DR_request_basic_dump2.json")
    parser.add_argument("--VS_json", default="VS_request_basic_dump2.json")
    args = parser.parse_args()
    DR = DataRequest.from_separated_inputs(args.DR_json, args.VS_json)
    print(DR)
