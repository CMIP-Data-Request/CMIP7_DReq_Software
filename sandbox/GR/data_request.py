#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data request.
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import argparse
import os

import six

from logger import get_logger, change_log_file, change_log_level
from dump_transformation import transform_content
from tools import read_json_file
from vocabulary_server import VocabularyServer, Variable, Experiment

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
		return [f"{indent}{type(self).__name__}: {self.vs.get_element(self.DR_type, self.id, 'name')} (id: {self.id})", ]


class Theme(DRObjects):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.DR_type = "data_request_themes"


class ExperimentsGroup(DRObjects):
	def __init__(self, experiments=list(), **kwargs):
		super().__init__(**kwargs)
		self.experiments = experiments
		self.DR_type = "experiments_groups"

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
			indent = "    " * level
			rep.append(f"{indent}Experiments included:")
			for experiment in self.get_experiments():
				rep.extend(experiment.print_content(level=level + 1))
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
		self.DR_type = "variables_groups"

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
			indent = "    " * level
			rep.append(f"{indent}Variables included:")
			for variable in self.get_variables():
				rep.extend(variable.print_content(level=level + 1))
		return rep


class Opportunity(DRObjects):
	def __init__(self, experiments_groups=list(), variables_groups=list(), themes=list(), **kwargs):
		super().__init__(**kwargs)
		self.experiments_groups = experiments_groups
		self.variables_groups = variables_groups
		self.themes = themes
		self.DR_type = "opportunities"

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
	def from_input(cls, dr, experiments_groups=list(), variables_groups=list(), themes=list(), **kwargs):
		return super().from_input(
			experiments_groups=[dr.get_experiments_group(exp_group) for exp_group in experiments_groups],
			variables_groups=[dr.get_variables_group(var_group) for var_group in variables_groups],
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
			superindent = "    " * (level + 2)
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
		self.experiments_groups = {id: ExperimentsGroup.from_input(id=id, vs=self.VS, **input_dict)
		                           for (id, input_dict) in input_database["experiments_groups"].items()}
		self.variables_groups = {id: VariablesGroup.from_input(id=id, vs=self.VS, **input_dict)
		                         for (id, input_dict) in input_database["variables_groups"].items()}
		self.opportunities = {id: Opportunity.from_input(id=id, dr=self, vs=self.VS, **input_dict)
		                      for (id, input_dict) in input_database["opportunities"].items()}
		self.clean()

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
		to_delete = list()
		for exp_group in self.get_experiments_groups():
			if not(any([exp_group in opportunity.get_experiments_groups() for opportunity in self.get_opportunities()])):
				to_delete.append(exp_group.id)
		for id in to_delete:
			logger.debug(f"Experiments group with id {id} is not associated with any opportunity - skip it.")
			del self.experiments_groups[id]
		to_delete = list()
		for var_group in self.get_variables_groups():
			if not (any([var_group in opportunity.get_variables_groups() for opportunity in self.get_opportunities()])):
				to_delete.append(var_group.id)
		for id in to_delete:
			logger.debug(f"Variables group with id {id} is not associated with any opportunity - skip it.")
			del self.variables_groups[id]

	@classmethod
	def from_input(cls, json_input, version, **kwargs):
		DR_content, VS_content = cls._split_content_from_input_json(json_input, version=version)
		VS = VocabularyServer(VS_content)
		return cls(input_database=DR_content, VS=VS, **kwargs)

	@classmethod
	def from_separated_inputs(cls, DR_input, VS_input, **kwargs):
		if isinstance(DR_input, six.string_types):
			DR = read_json_file(DR_input)
		else:
			DR = DR_input
		if isinstance(VS_input, six.string_types):
			VS = VocabularyServer.from_input(VS_input)
		else:
			VS = VocabularyServer(VS_input)
		return cls(input_database=DR, VS=VS, **kwargs)

	@staticmethod
	def _split_content_from_input_json(input_json, version):
		if isinstance(input_json, six.string_types):
			content = read_json_file(input_json)
		else:
			content = input_json
		DR, VS = transform_content(content, version=version)
		return DR, VS

	def __str__(self):
		rep = list()
		rep.append("Data Request content:")
		rep.append("    Experiments groups:")
		for elt in self.get_experiments_groups():
			rep.extend(elt.print_content(level=2))
		rep.append("    Variables groups:")
		for elt in self.get_variables_groups():
			rep.extend(elt.print_content(level=2))
		rep.append("    Opportunities:")
		for elt in self.get_opportunities():
			rep.extend(elt.print_content(level=2))
		return os.linesep.join(rep)

	def get_experiments_groups(self):
		return [self.experiments_groups[elt] for elt in self.experiments_groups]

	def get_experiments_group(self, id):
		if id in self.experiments_groups:
			return self.experiments_groups[id]
		else:
			raise ValueError(f"Could not find experiments group {id}.")

	def get_variables_groups(self):
		return [self.variables_groups[elt] for elt in self.variables_groups]

	def get_variables_group(self, id):
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


if __name__ == "__main__":
	change_log_file(default=True)
	change_log_level("debug")
	parser = argparse.ArgumentParser()
	parser.add_argument("--DR_json", default="DR_request_basic_dump2.json")
	parser.add_argument("--VS_json", default="VS_request_basic_dump2.json")
	args = parser.parse_args()
	DR = DataRequest.from_separated_inputs(args.DR_json, args.VS_json)
	print(DR)
