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

import six

from data_request_api.stable.utilities.logger import get_logger, change_log_file, change_log_level
from data_request_api.stable.content.dump_transformation import transform_content
from data_request_api.stable.utilities.tools import read_json_file
from data_request_api.stable.query.vocabulary_server import VocabularyServer, is_link_id_or_value, build_link_from_id

version = "0.1"


class ConstantValueObj(object):
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
		self.DR_type = DR_type
		self.attributes = copy.deepcopy(attributes)
		_, self.attributes["id"] = is_link_id_or_value(id)
		self.structure = copy.deepcopy(structure)
		self.dr = dr
		self.attributes = self.transform_content(self.attributes, dr)
		self.structure = self.transform_content(self.structure, dr, force_transform=True)

	@staticmethod
	def transform_content(input_dict, dr, force_transform=False):
		for (key, values) in input_dict.items():
			if isinstance(values, list):
				for (i, value) in enumerate(values):
					if isinstance(value, six.string_types) and (force_transform or is_link_id_or_value(value)[0]):
						input_dict[key][i] = dr.find_element(key, value)
					elif isinstance(value, six.string_types):
						input_dict[key][i] = ConstantValueObj(value)
			elif isinstance(values, six.string_types) and (force_transform or is_link_id_or_value(values)[0]):
				input_dict[key] = dr.find_element(key, values)
			elif isinstance(values, six.string_types):
				input_dict[key] = ConstantValueObj(values)
		return input_dict

	@classmethod
	def from_input(cls, dr, id, DR_type="undef", elements=dict(), structure=dict()):
		"""
		Create instance of the class using specific arguments.
		:param kwargs: list of arguments
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
		return isinstance(other, type(self)) and self.id < other.id

	def __gt__(self, other):
		return isinstance(other, type(self)) and self.id > other.id

	def __copy__(self):
		return type(self).__call__(dr=self.dr, DR_type=copy.deepcopy(self.DR_type),
		                           structure=copy.deepcopy(self.structure), **copy.deepcopy(self.attributes))

	def __deepcopy__(self, memodict={}):
		return self.__copy__()

	def check(self):
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
		DR_type = copy.deepcopy(self.DR_type)
		DR_type = self.dr.VS.to_singular(DR_type)
		return [f"{indent}{DR_type}: {self.name} (id: {is_link_id_or_value(self.id)[1]})", ]

	def filter_on_request(self, request_value):
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
		return len(self.get_experiments())

	def get_experiments(self):
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
		return [f"{indent}{self.DR_type.rstrip('s')}: {self.physical_parameter.name} at frequency {self.cmip7_frequency.name} (id: {is_link_id_or_value(self.id)[1]}, title: {self.title})", ]

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
		return len(self.get_variables())

	def get_variables(self):
		return self.structure["variables"]

	def get_mips(self):
		return self.structure["mips"]

	def get_priority_level(self):
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
	             structure=dict(experiment_groups=list(), variable_groups=list(), data_request_themes=list(), time_slices=list()),
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
	               time_slices=list(), mips=list(), **kwargs):

		return super().from_input(DR_type="opportunities", dr=dr, id=id, elements=kwargs,
		                          structure=dict(experiment_groups=experiment_groups, variable_groups=variable_groups,
		                                         data_request_themes=data_request_themes, time_slices=time_slices,
		                                         mips=mips))

	def get_experiment_groups(self):
		return self.structure["experiment_groups"]

	def get_variable_groups(self):
		return self.structure["variable_groups"]

	def get_data_request_themes(self):
		return self.structure["data_request_themes"]

	def get_themes(self):
		return self.get_data_request_themes()

	def get_time_slices(self):
		return self.structure["time_slices"]

	def get_mips(self):
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
			rep.append(f"{indent}Time slices included:")
			for time_slice in self.get_time_slices():
				rep.extend(time_slice.print_content(level=level + 2, add_content=False))
		return rep

	def filter_on_request(self, request_value):
		request_type = request_value.DR_type
		if request_type in ["data_request_themes", ]:
			return True, request_value in self.get_data_request_themes()
		elif request_type in ["experiment_groups", ]:
			return True, request_value in self.get_experiment_groups()
		elif request_type in ["variable_groups", ]:
			return True, request_value in self.get_variable_groups()
		elif request_type in ["time_slice", ]:
			return True, request_value in self.get_time_slices()
		elif request_type in ["mips", ]:
			return True, request_value in self.get_mips() or \
			             any(var_grp.filter_on_request(request_value=request_value)[1]
			                 for var_grp in self.get_variable_groups())
		elif request_type in ["variables", "priority_level", "table_identifiers", "temporal_shape",
		                      "spatial_shape", "structure", "physical_parameters", "modelling_realm", "esm-bcv",
		                      "cf_standard_names", "cell_methods", "cell_measures"]:
			return True, any(var_grp.filter_on_request(request_value=request_value)[1]
			                 for var_grp in self.get_variable_groups())
		elif request_type in ["experiments", ]:
			return True, any(exp_grp.filter_on_request(request_value=request_value)[1]
			                 for exp_grp in self.get_experiment_groups())
		else:
			return super().filter_on_request(request_value=request_value)


class DataRequest(object):
	def __init__(self, input_database, VS, **kwargs):
		self.VS = VS
		self.content_version = input_database["version"]
		self.structure = input_database
		self.mapping = defaultdict(lambda: defaultdict(lambda: dict))
		self.content = defaultdict(lambda: defaultdict(lambda: dict))
		for op in input_database["opportunities"]:
			self.content["opportunities"][op] = self.find_element("opportunities", op)

	def check(self):
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
		return version

	@property
	def version(self):
		return f"Software {self.software_version} - Content {self.content_version}"

	@classmethod
	def from_input(cls, json_input, version, **kwargs):
		DR_content, VS_content = cls._split_content_from_input_json(json_input, version=version)
		VS = VocabularyServer(VS_content)
		return cls(input_database=DR_content, VS=VS, **kwargs)

	@classmethod
	def from_separated_inputs(cls, DR_input, VS_input, **kwargs):
		logger = get_logger()
		if isinstance(DR_input, six.string_types) and os.path.isfile(DR_input):
			DR = read_json_file(DR_input)
		elif isinstance(DR_input, dict):
			DR = copy.deepcopy(DR_input)
		else:
			logger.error("DR_input should be either the name of a json file or a dictionary.")
			raise TypeError("DR_input should be either the name of a json file or a dictionary.")
		if isinstance(VS_input, six.string_types) and os.path.isfile(VS_input):
			VS = VocabularyServer.from_input(VS_input)
		elif isinstance(VS_input, dict):
			VS = VocabularyServer(copy.deepcopy(VS_input))
		else:
			logger.error("VS_input should be either the name of a json file or a dictionary.")
			raise TypeError("VS_input should be either the name of a json file or a dictionary.")
		return cls(input_database=DR, VS=VS, **kwargs)

	@staticmethod
	def _split_content_from_input_json(input_json, version):
		logger = get_logger()
		if not isinstance(version, six.string_types):
			logger.error(f"Version should be a string, not {type(version).__name__}.")
			raise TypeError(f"Version should be a string, not {type(version).__name__}.")
		if isinstance(input_json, six.string_types) and os.path.isfile(input_json):
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

	def get_experiment_groups(self):
		return [self.content["experiment_groups"][key] for key in sorted(list(self.content["experiment_groups"]))]

	def get_experiment_group(self, id):
		rep = self.find_element("experiment_groups", id, default=None)
		if rep is not None:
			return rep
		else:
			raise ValueError(f"Could not find experiments group {id} among {self.get_experiment_groups()}.")

	def get_variable_groups(self):
		return [self.content["variable_groups"][key] for key in sorted(list(self.content["variable_groups"]))]

	def get_variable_group(self, id):
		rep = self.find_element("variable_groups", id, default=None)
		if rep is not None:
			return rep
		else:
			raise ValueError(f"Could not find variables group {id}.")

	def get_opportunities(self):
		return [self.content["opportunities"][key] for key in sorted(list(self.content["opportunities"]))]

	def get_opportunity(self, id):
		rep = self.find_element("opportunities", id, default=None)
		if rep is not None:
			return rep
		else:
			raise ValueError(f"Could not find opportunity {id}.")

	def get_variables(self):
		rep = set()
		for var_grp in self.get_variable_groups():
			rep = rep | set(var_grp.get_variables())
		rep = sorted(list(rep))
		return rep

	def get_mips(self):
		rep = set()
		for op in self.get_opportunities():
			rep = rep | set(op.get_mips())
		for var_grp in self.get_variable_groups():
			rep = rep | set(var_grp.get_mips())
		rep = sorted(list(rep))
		return rep

	def get_experiments(self):
		rep = set()
		for exp_grp in self.get_experiment_groups():
			rep = rep | set(exp_grp.get_experiments())
		rep = sorted(list(rep))
		return rep

	def get_data_request_themes(self):
		rep = set()
		for op in self.get_opportunities():
			rep = rep | set(op.get_themes())
		rep = sorted(list(rep))
		return rep

	def find_variables_per_priority(self, priority):
		return self.filter_elements_per_request(element_type="variables", requests=dict(priority_level=[priority, ]))

	def find_opportunities_per_theme(self, theme):
		return self.filter_elements_per_request(element_type="opportunities", requests=dict(data_request_themes=[theme, ]))

	def find_experiments_per_theme(self, theme):
		return self.filter_elements_per_request(element_type="experiments", requests=dict(data_request_themes=[theme, ]))

	def find_variables_per_theme(self, theme):
		return self.filter_elements_per_request(element_type="variables", requests=dict(data_request_themes=[theme, ]))

	def find_mips_per_theme(self, theme):
		return self.filter_elements_per_request(element_type="mips", requests=dict(data_request_themes=[theme, ]))

	def find_themes_per_opportunity(self, opportunity):
		return self.filter_elements_per_request(element_type="data_request_themes", requests=dict(opportunities=[opportunity, ]))

	def find_experiments_per_opportunity(self, opportunity):
		return self.filter_elements_per_request(element_type="experiments", requests=dict(opportunities=[opportunity, ]))

	def find_variables_per_opportunity(self, opportunity):
		return self.filter_elements_per_request(element_type="variables", requests=dict(opportunities=[opportunity, ]))

	def find_mips_per_opportunity(self, opportunity):
		return self.filter_elements_per_request(element_type="mips", requests=dict(opportunities=[opportunity, ]))

	def find_opportunities_per_variable(self, variable):
		return self.filter_elements_per_request(element_type="opportunities", requests=dict(variables=[variable, ]))

	def find_themes_per_variable(self, variable):
		return self.filter_elements_per_request(element_type="data_request_themes", requests=dict(variables=[variable, ]))

	def find_mips_per_variable(self, variable):
		return self.filter_elements_per_request(element_type="mips", requests=dict(variables=[variable, ]))

	def find_opportunities_per_experiment(self, experiment):
		return self.filter_elements_per_request(element_type="opportunities", requests=dict(experiments=[experiment, ]))

	def find_themes_per_experiment(self, experiment):
		return self.filter_elements_per_request(element_type="data_request_themes", requests=dict(experiments=[experiment, ]))

	def find_element_per_identifier_from_vs(self, element_type, key, value, default=False, **kwargs):
		if key in ["id", ]:
			value = build_link_from_id(value)
		rep = self.VS.get_element(element_type=element_type, element_id=value, id_type=key, default=default, **kwargs)
		if rep not in [default, ]:
			if element_type in ["opportunities", ]:
				rep = Opportunity.from_input(dr=self, **rep,
				                             **self.structure.get("opportunities", dict()).get(rep["id"], dict()))
			elif element_type in ["variable_groups", ]:
				rep = VariablesGroup.from_input(dr=self, **rep,
				                                **self.structure.get("variable_groups", dict()).get(rep["id"], dict()))
			elif element_type in ["experiment_groups", ]:
				rep = ExperimentsGroup.from_input(dr=self, **rep,
				                                  **self.structure.get("experiment_groups", dict()).get(rep["id"], dict()))
			elif element_type in ["variables", ]:
				rep = Variable.from_input(dr=self, **rep)
			else:
				rep = DRObjects.from_input(dr=self, id=rep["id"], DR_type=element_type, elements=rep)
		return rep

	def find_element_from_vs(self, element_type, value, default=False):
		rep = self.find_element_per_identifier_from_vs(element_type=element_type, value=value, key="id", default=None)
		if rep is not None:
			self.content[element_type][rep.id] = rep
		else:
			rep = self.find_element_per_identifier_from_vs(element_type=element_type, value=value, key="name",
			                                               default=default)
			if rep not in [default, ]:
				self.content[element_type][rep.id] = rep
				self.mapping[element_type][rep.name] = rep
		return rep

	def find_element(self, element_type, value, default=False):
		if value in self.content[element_type]:
			return self.content[element_type][value]
		elif value in self.mapping[element_type]:
			return self.mapping[element_type][value]
		else:
			return self.find_element_from_vs(element_type=element_type, value=value, default=default)

	def get_elements_per_kind(self, element_type):
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

	def filter_elements_per_request(self, element_type, requests=dict(), operation="all", skip_if_missing=False):
		logger = get_logger()
		if operation not in ["any", "all"]:
			raise ValueError(f"Operation does not accept {operation} as value: choose among 'any' (match at least one requirement) and 'all' (match all requirements)")
		else:
			# Prepare the request dictionary
			request_dict = defaultdict(list)
			for (req, values) in requests.items():
				if not isinstance(values, list):
					values = [values, ]
				for val in values:
					if isinstance(val, six.string_types):
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
			elements = self.get_elements_per_kind(element_type)
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
							logger.error(f"Could not filter {element_type} by {request}")
							raise ValueError(f"Could not filter {element_type} by {request}")
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
		return self.filter_elements_per_request(element_type="opportunities", operation=operation,
		                                        skip_if_missing=skip_if_missing, requests=kwargs)

	def find_experiments(self, operation="any", skip_if_missing=False, **kwargs):
		return self.filter_elements_per_request(element_type="experiments", operation=operation,
		                                        skip_if_missing=skip_if_missing, requests=kwargs)

	def find_variables(self, operation="any", skip_if_missing=False, **kwargs):
		return self.filter_elements_per_request(element_type="variables", operation=operation,
		                                        skip_if_missing=skip_if_missing, requests=kwargs)

	def sort_func(self, data_list, sorting_request=list()):
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
	                filtering_skip_if_missing=False, export_columns_request=list(), sorting_request=list()):
		filtered_data = self.filter_elements_per_request(element_type=main_data, requests=filtering_requests,
		                                                 operation=filtering_operation,
		                                                 skip_if_missing=filtering_skip_if_missing)
		sorted_filtered_data = self.sort_func(filtered_data, sorting_request)

		export_columns_request.insert(0, "id")
		content = list()
		content.append(";".join(export_columns_request))
		for data in sorted_filtered_data:
			content.append(";".join([str(data.__getattr__(key)) for key in export_columns_request]))

		with open(output_file, "w") as f:
			f.write(os.linesep.join(content))

	def export_summary(self, lines_data, columns_data, output_file, sorting_line="id", title_line="name",
	                   sorting_column="id", title_column="name", filtering_requests=dict(), filtering_operation="all",
	                   filtering_skip_if_missing=False):
		logger = get_logger()
		logger.info(f"Generate summary for {lines_data}/{columns_data}")
		filtered_data = self.filter_elements_per_request(element_type=lines_data, requests=filtering_requests,
		                                                 operation=filtering_operation,
		                                                 skip_if_missing=filtering_skip_if_missing)
		sorted_filtered_data = self.sort_func(filtered_data, sorting_request=[sorting_line, ])
		columns_datasets = self.filter_elements_per_request(element_type=columns_data)
		columns_datasets = self.sort_func(columns_datasets, sorting_request=[sorting_column, ])
		columns_title = [str(elt.__getattr__(title_column)) for elt in columns_datasets]
		table_title = f"{lines_data} {title_line} / {columns_data} {title_column}"

		nb_lines = len(sorted_filtered_data)
		logger.debug(f"{nb_lines} elements found for {lines_data}")
		logger.debug(f"{len(columns_title)} found elements for {columns_data}")

		logger.info("Generate summary")
		content = defaultdict(list)
		for (i, data) in enumerate(columns_datasets):
			logger.debug(f"Deal with column {i}/{len(columns_title)}")
			filter_line_datasets = self.filter_elements_per_request(element_type=lines_data,
			                                                        requests={data.DR_type: data},
			                                                        operation="all")
			for line_data in filtered_data:
				line_data_title = line_data.__getattr__(title_line)
				if line_data in filter_line_datasets:
					content[line_data_title].append("x")
				else:
					content[line_data_title].append("")

		logger.info("Format summary")
		rep = list()
		rep.append(";".join([table_title, ] + columns_title))
		for line_data in filtered_data:
			line_data_title = str(line_data.__getattr__(title_line))
			rep.append(";".join([line_data_title, ] + content[line_data_title]))

		logger.info("Write summary")
		with open(output_file, "w") as f:
			f.write(os.linesep.join(rep))


if __name__ == "__main__":
	change_log_file(default=True)
	change_log_level("debug")
	parser = argparse.ArgumentParser()
	parser.add_argument("--DR_json", default="DR_request_basic_dump2.json")
	parser.add_argument("--VS_json", default="VS_request_basic_dump2.json")
	args = parser.parse_args()
	DR = DataRequest.from_separated_inputs(args.DR_json, args.VS_json)
	print(DR)
