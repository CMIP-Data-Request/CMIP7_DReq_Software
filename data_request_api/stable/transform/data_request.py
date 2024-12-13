#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data request.
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import argparse
import copy
import os

import six

from logger import get_logger, change_log_file, change_log_level
from dump_transformation import transform_content
from tools import read_json_file
from vocabulary_server import VocabularyServer, Variable, Experiment, is_link_id_or_value, build_link_from_id

version = "0.1"


class DRObjects(object):
	"""
	Base object to build the ones used within the DR API.
	Use to define basic information needed.
	"""
	def __init__(self, id, vs, **kwargs):
		self.id = id
		self.vs = vs
		self.DR_type = "undef"

	def __eq__(self, other):
		return isinstance(other, type(self)) and self.id == other.id and self.DR_type == other.DR_type

	def __lt__(self, other):
		return self.id < other.id

	def __gt__(self, other):
		return self.id > other.id

	def __copy__(self):
		return type(self).__call__(id=copy.deepcopy(self.id), vs=self.vs)

	def __deepcopy__(self, memodict={}):
		return self.__copy__()

	def check(self):
		pass

	@classmethod
	def from_input(cls, **kwargs):
		"""
		Create instance of the class using specific arguments.
		:param kwargs: list of arguments
		:return: instance of the current class.
		"""
		return cls(**kwargs)

	def __str__(self):
		return os.linesep.join(self.print_content())

	def print_content(self, level=0, add_content=True):
		"""
		Function to return a printable version of the content of the current class.
		:param level: level of indent of the result
		:param add_content: should inner content be added?
		:return: a list of strings that can be assembled to print the content.
		"""
		indent = "    " * level
		return [f"{indent}{type(self).__name__}: {self.vs.get_element(element_type=self.DR_type, element_id=self.id, element_key='name')} "
		        f"(id: {is_link_id_or_value(self.id)[1]})", ]


class Theme(DRObjects):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.DR_type = "data_request_themes"


class ExperimentsGroup(DRObjects):
	def __init__(self, experiments=list(), **kwargs):
		super().__init__(**kwargs)
		self.experiments = experiments
		self.DR_type = "experiment_groups"

	def __eq__(self, other):
		return super().__eq__(other) and self.experiments == other.experiments

	def __copy__(self):
		return type(self).__call__(id=copy.deepcopy(self.id), vs=self.vs, experiments=copy.deepcopy(self.experiments))

	def check(self):
		super().check()
		logger = get_logger()
		if len(self.experiments) == 0:
			logger.critical(f"No experiment defined for {type(self).__name__} id {self.id}")

	def count(self):
		return len(self.experiments)

	def get_experiments(self):
		return self.experiments

	def print_content(self, level=0, add_content=True):
		rep = super().print_content(level=level)
		if add_content:
			indent = "    " * (level + 1)
			rep.append(f"{indent}Experiments included:")
			for experiment in self.get_experiments():
				rep.extend(experiment.print_content(level=level + 2))
		return rep

	@classmethod
	def from_input(cls, vs, experiments=list(), **kwargs):
		experiments = [vs.get_experiment(id) for id in experiments]
		return cls(experiments=experiments, vs=vs, **kwargs)


class VariablesGroup(DRObjects):
	def __init__(self, variables=list(), mips=list(), priority="Low", **kwargs):
		logger = get_logger()
		super().__init__(**kwargs)
		self.variables = variables
		self.mips = mips
		self.priority = priority
		self.DR_type = "variable_groups"

	def __eq__(self, other):
		return super().__eq__(other) and self.variables == other.variables and self.mips == other.mips and \
			self.priority == other.priority

	def __copy__(self):
		return type(self).__call__(id=copy.deepcopy(self.id), vs=self.vs, variables=copy.deepcopy(self.variables),
		                           mips=copy.deepcopy(self.mips), priority=copy.deepcopy(self.priority))

	def check(self):
		super().check()
		logger = get_logger()
		if len(self.variables) == 0:
			logger.critical(f"No variable defined for {type(self).__name__} id {self.id}")

	@classmethod
	def from_input(cls, vs, variables=list(), **kwargs):
		variables = [vs.get_variable(id) for id in variables]
		return cls(variables=variables, vs=vs, **kwargs)

	def count(self):
		return len(self.variables)

	def get_variables(self):
		return self.variables

	def get_mips(self):
		return self.mips

	def print_content(self, level=0, add_content=True):
		rep = super().print_content(level=level)
		if add_content:
			indent = "    " * (level + 1)
			rep.append(f"{indent}Variables included:")
			for variable in self.get_variables():
				rep.extend(variable.print_content(level=level + 2))
		return rep


class Opportunity(DRObjects):
	def __init__(self, experiments_groups=list(), variables_groups=list(), themes=list(), **kwargs):
		super().__init__(**kwargs)
		self.experiments_groups = experiments_groups
		self.variables_groups = variables_groups
		self.themes = themes
		self.DR_type = "opportunities"

	def __eq__(self, other):
		return super().__eq__(other) and self.experiments_groups == other.experiments_groups and \
			self.variables_groups == other.variables_groups and self.themes == other.themes

	def __copy__(self):
		return type(self).__call__(id=copy.deepcopy(self.id), vs=self.vs, themes=copy.deepcopy(self.themes),
		                           experiments_groups=copy.deepcopy(self.experiments_groups),
		                           variables_groups=copy.deepcopy(self.variables_groups))

	def check(self):
		super().check()
		logger = get_logger()
		if len(self.experiments_groups) == 0:
			logger.critical(f"No experiments group defined for {type(self).__name__} id {self.id}")
		if len(self.variables_groups) == 0:
			logger.critical(f"No variables group defined for {type(self).__name__} id {self.id}")
		if len(self.themes) == 0:
			logger.critical(f"No theme defined for {type(self).__name__} id {self.id}")

	@classmethod
	def from_input(cls, dr, experiment_groups=list(), variable_groups=list(), themes=list(), **kwargs):
		return super().from_input(
			experiments_groups=[dr.get_experiments_group(exp_group) for exp_group in experiment_groups],
			variables_groups=[dr.get_variables_group(var_group) for var_group in variable_groups],
			themes=[Theme(id=id, vs=kwargs["vs"]) for id in themes],
			**kwargs)

	def get_experiments_groups(self):
		return self.experiments_groups

	def get_variables_groups(self):
		return self.variables_groups

	def get_themes(self):
		return self.themes

	def print_content(self, level=0, add_content=True):
		rep = super().print_content(level=level)
		if add_content:
			indent = "    " * (level + 1)
			rep.append(f"{indent}Experiments groups included:")
			for experiments_group in self.get_experiments_groups():
				rep.extend(experiments_group.print_content(level=level + 2, add_content=False))
			rep.append(f"{indent}Variables groups included:")
			for variables_group in self.get_variables_groups():
				rep.extend(variables_group.print_content(level=level + 2, add_content=False))
			rep.append(f"{indent}Themes included:")
			for theme in self.get_themes():
				rep.extend(theme.print_content(level=level + 2, add_content=False))
		return rep


class DataRequest(object):
	def __init__(self, input_database, VS, **kwargs):
		self.VS = VS
		self.content_version = input_database["version"]
		self.experiments_groups = self.build_dict_id(object_target=ExperimentsGroup, vs=self.VS,
		                                             input_database=input_database["experiment_groups"], **kwargs)
		self.variables_groups = self.build_dict_id(object_target=VariablesGroup, vs=self.VS,
		                                           input_database=input_database["variable_groups"], **kwargs)
		self.opportunities = self.build_dict_id(object_target=Opportunity, vs=self.VS, dr=self,
		                                        input_database=input_database["opportunities"], **kwargs)
		self.clean()

	@staticmethod
	def build_dict_id(object_target, input_database, **kwargs):
		return {id: object_target.from_input(id=build_link_from_id(id), **input_dict, **kwargs)
		        for (id, input_dict) in input_database.items()}

	def check(self):
		logger = get_logger()
		logger.info("Check data request metadata")
		logger.info("... Check experiments groups")
		for elt in self.get_experiments_groups():
			elt.check()
		logger.info("... Check variables groups")
		for elt in self.get_variables_groups():
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

	def clean(self):
		logger = get_logger()
		opportunities_exp_groups = list()
		opportunities_var_groups = list()
		for op in self.get_opportunities():
			opportunities_var_groups.extend([var_grp.id for var_grp in op.get_variables_groups()])
			opportunities_exp_groups.extend([exp_grp.id for exp_grp in op.get_experiments_groups()])
		opportunities_var_groups = [is_link_id_or_value(id)[1] for id in set(opportunities_var_groups)]
		opportunities_exp_groups = [is_link_id_or_value(id)[1] for id in set(opportunities_exp_groups)]
		for id in [elt.id for elt in self.get_experiments_groups() if is_link_id_or_value(elt.id)[1] not in opportunities_exp_groups]:
			logger.debug(f"Experiments group with id {id} is not associated with any opportunity - skip it.")
			del self.experiments_groups[id]
		for id in [elt.id for elt in self.get_variables_groups() if is_link_id_or_value(elt.id)[1] not in opportunities_var_groups]:
			logger.debug(f"Variables group with id {id} is not associated with any opportunity - skip it.")
			del self.variables_groups[id]

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
			logger.error(f"Version should be a string, not {type(version)}.")
			raise TypeError(f"Version should be a string, not {type(version)}.")
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
		for elt in self.get_experiments_groups():
			rep.extend(elt.print_content(level=2))
		rep.append(f"{indent}Variables groups:")
		for elt in self.get_variables_groups():
			rep.extend(elt.print_content(level=2))
		rep.append(f"{indent}Opportunities:")
		for elt in self.get_opportunities():
			rep.extend(elt.print_content(level=2))
		return os.linesep.join(rep)

	def get_experiments_groups(self):
		return [self.experiments_groups[elt] for elt in sorted(list(self.experiments_groups))]

	def get_experiments_group(self, id):
		_, id = is_link_id_or_value(id)
		if id in self.experiments_groups:
			return self.experiments_groups[id]
		else:
			raise ValueError(f"Could not find experiments group {id} among {list(self.experiments_groups)}.")

	def get_variables_groups(self):
		return [self.variables_groups[elt] for elt in sorted(list(self.variables_groups))]

	def get_variables_group(self, id):
		_, id = is_link_id_or_value((id))
		if id in self.variables_groups:
			return self.variables_groups[id]
		else:
			raise ValueError(f"Could not find variables group {id}.")

	def get_opportunities(self):
		return [self.opportunities[elt] for elt in self.opportunities]

	def get_opportunity(self, id):
		if id in self.opportunities:
			return self.opportunities[id]
		else:
			raise ValueError(f"Could not find opportunity {id}.")

	def find_variables_per_priority(self, priority):
		rep = set()
		for var_group in self.get_variables_groups():
			if var_group.priority in [priority, ]:
				rep = rep.union(set(var_group.get_variables()))
		return sorted(list(rep))

	def find_opportunity_per_theme(self, theme):
		rep = set()
		for opportunity in self.get_opportunities():
			if theme in opportunity.get_themes():
				rep.add(opportunity)
		return sorted(list(rep))

	def find_experiments_per_theme(self, theme):
		rep = set()
		for opportunity in self.get_opportunities():
			if theme in opportunity.get_themes():
				for exp_group in opportunity.get_experiments_groups():
					rep = rep.union(set(exp_group.get_experiments()))
		return sorted(list(rep))

	def find_variables_per_theme(self, theme):
		rep = set()
		for opportunity in self.get_opportunities():
			if theme in opportunity.get_themes():
				for var_group in opportunity.get_variables_groups():
					rep = rep.union(set(var_group.get_variables()))
		return sorted(list(rep))

	def find_mips_per_theme(self, theme):
		rep = set()
		for opportunity in self.get_opportunities():
			if theme in opportunity.get_themes():
				for var_group in opportunity.get_variables_groups():
					rep = rep.union(set(var_group.get_mips()))
		return sorted(list(rep))

	def find_themes_per_opportunity(self, opportunity):
		if not isinstance(opportunity, Opportunity):
			opportunity = self.get_opportunity(opportunity)
		return sorted(opportunity.get_themes())

	def find_experiments_per_opportunity(self, opportunity):
		if not isinstance(opportunity, Opportunity):
			opportunity = self.get_opportunity(opportunity)
		rep = set()
		for exp_group in opportunity.get_experiments_groups():
			rep = rep.union(set(exp_group.get_experiments()))
		return sorted(list(set(rep)))

	def find_variables_per_opportunity(self, opportunity):
		if not isinstance(opportunity, Opportunity):
			opportunity = self.get_opportunity(opportunity)
		rep = set()
		for var_group in opportunity.get_variables_groups():
			rep = rep.union(set(var_group.get_variables()))
		return sorted(list(rep))

	def find_mips_per_opportunity(self, opportunity):
		if not isinstance(opportunity, Opportunity):
			opportunity = self.get_opportunity(opportunity)
		rep = set()
		for var_group in opportunity.get_variables_groups():
			rep = rep.union(set(var_group.get_mips()))
		return sorted(list(rep))

	def find_opportunities_per_variable(self, variable):
		if isinstance(variable, Variable):
			variable = variable.id
		rep = set()
		for opportunity in self.get_opportunities():
			for var_group in opportunity.get_variables_groups():
				if variable in var_group.get_variables():
					rep.add(opportunity)
		return sorted(list(rep))

	def find_themes_per_variable(self, variable):
		if isinstance(variable, Variable):
			variable = variable.id
		rep = set()
		for opportunity in self.get_opportunities():
			for var_group in opportunity.get_variables_groups():
				if variable in var_group.get_variables():
					rep = rep.union(set(opportunity.get_themes()))
		return sorted(list(rep))

	def find_mips_per_variable(self, variable):
		if isinstance(variable, Variable):
			variable = variable.id
		rep = set()
		for var_group in self.get_variables_groups():
			if variable in var_group.get_variables():
				rep = rep.union(set(var_group.get_mips()))
		return sorted(list(rep))

	def find_opportunities_per_experiment(self, experiment):
		if isinstance(experiment, Experiment):
			experiment = experiment.id
		rep = set()
		for opportunity in self.get_opportunities():
			for exp_group in opportunity.get_experiments_groups():
				if experiment in exp_group.get_variables():
					rep.add(opportunity)
		return sorted(list(rep))

	def find_themes_per_experiment(self, experiment):
		if isinstance(experiment, Experiment):
			experiment = experiment.id
		rep = set()
		for opportunity in self.get_opportunities():
			for exp_group in opportunity.get_experiments_groups():
				if experiment in exp_group.get_variables():
					rep = rep.union(set(opportunity.get_themes()))
		return sorted(list(rep))

	def _find_filtering_reference(self, key, element):
		logger = get_logger()
		search_dict = dict(
			default=dict(
				obj_type=None,
				search_func=self.vs.get_element,
				search_options=dict(default=None),
				id_types=["uid", "name"]
			),
			experiment=dict(
				obj_type=Experiment,
				search_func=self.vs.get_experiment,
				id_types=["uid", "experiment"]
			),
			experiments_group=dict(
				obj_type=ExperimentsGroup,
				search_options=dict(element_type="experiment_groups")
			),
			opportunity=dict(
				obj_type=Opportunity,
				search_options=dict(element_type="opportunities")
			),
			priority=dict(
				search_options=dict(element_type="priority_level")
			),
			theme=dict(
				obj_type=Theme,
				search_options=dict(element_type="data_request_themes")
			),
			variable=dict(
				obj_type=Variable,
				search_func=self.vs.get_variable,
			),
			variables_group=dict(
				obj_type=VariablesGroup,
				search_options=dict(element_type="variable_groups")
			))
		if key in search_dict:
			obj_type = search_dict[key]["obj_type"]
			search_func = search_dict[key].get("search_func", search_dict["default"]["search_func"])
			search_options = copy.deepcopy(search_dict["default"]["search_options"])
			search_options.update(copy.deepcopy(search_dict[key].get("search_options", dict())))
			id_types = search_dict[key].get("id_types", search_dict["default"]["id_types"])
			if obj_type is not None and isinstance(element, obj_type):
				return element.id
			elif isinstance(element, six.string_types):
				i = 0
				found = False
				while i < len(id_types) and not found:
					value = search_func.__call__(element, id_type=id_types[i], **search_options)
					if value is None:
						i += 1
					else:
						found = True
				if found:
					return element.get("id")
			else:
				logger.error(f"Unable to filter reference on value type {type(element)}.")
				raise TypeError(f"Unable to filter reference on value type {type(element)}.")
		else:
			logger.error(f"Key {key} is not designed to filter references.")
			raise ValueError(f"Key {key} is not designed to filter references.")

	def _find_filtering_references(self, **kwargs):
		filtering_references = dict()
		for key in kwargs:
			filtering_references[key] = [self._find_filtering_reference(key=key, element=value)
			                             for value in kwargs[key]]
		return copy.deepcopy(filtering_references)

	def find_experiments(self, experiments_groups=list(), opportunities=list(), themes=list(), variables=list(),
	                     variables_groups=list(), priorities=list()):
		"""
		Find the experiments which fit with all the filtering requests
		:param experiments_groups: list of experiments_groups elements or ids
		:param opportunities: list of opportunities elements or ids
		:param priorities: list of priorities elements or ids
		:param themes: list of themes elements or ids
		:param variables: list of variables elements or ids
		:param variables_groups: list of variables_groups elements or ids
		:return:
		"""

	def export_data(self, main_data, filtering_requests=dict(), sorting_request=list()):
		logger = get_logger()
		main_data_choices = ["experiment", "experiment_group", "opportunity", "theme", "variable", "variable_group"]
		if main_data not in main_data_choices:
			logger.error(f"main_data possible values are {main_data_choices}.")
			raise ValueError(f"main_data possible values are {main_data_choices}.")
		filtering_requests_choices = copy.deepcopy(main_data_choices)
		filtering_requests_choices.remove(main_data)
		filtering_requests_choices.append("priority")
		not_filtering_allowed = sorted(list(set(list(filtering_requests)) - set(filtering_requests_choices)))
		if len(not_filtering_allowed) > 0:
			logger.error(f"The following filtering requests are not allowed: {not_filtering_allowed}.")
			raise ValueError(f"The following filtering requests are not allowed: {not_filtering_allowed}.")


if __name__ == "__main__":
	change_log_file(default=True)
	change_log_level("debug")
	parser = argparse.ArgumentParser()
	parser.add_argument("--DR_json", default="DR_request_basic_dump2.json")
	parser.add_argument("--VS_json", default="VS_request_basic_dump2.json")
	args = parser.parse_args()
	DR = DataRequest.from_separated_inputs(args.DR_json, args.VS_json)
	print(DR)
