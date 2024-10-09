#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vocabulary server.
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import copy
import os

from logger import get_logger
from dump_transformation import read_json_file


class VSObject(object):
	def __init__(self, id, **kwargs):
		self.id = id

	def __str__(self):
		return os.linesep.join(self.print_content())

	def __repr__(self):
		return str(self)

	@classmethod
	def from_input(cls, **kwargs):
		return cls(**kwargs)

	def __lt__(self, other):
		return self.id < other.id

	def __gt__(self, other):
		return self.id > other.id

	def __eq__(self, other):
		return self.id == other.id

	def __hash__(self):
		return hash(self.id)

	def print_content(self, level=0, add_content=True):
		"""
		Function to return a rintable version of the content of the current class.
		:param level: level of indent of the result
		:param add_content: should inner content be added?
		:return: a list of strings that can be assembled to print the content.
		"""
		indent = "    " * level
		return [f"{indent}{type(self).__name__}: {self.id}", ]


class Experiment(VSObject):
	def __init__(self, id, name, **kwargs):
		super().__init__(id, **kwargs)
		self.name = name

	def print_content(self, level=0, add_content=True):
		indent = "    " * level
		return [f"{indent}experiment {self.name} (id: {self.id})", ]

	@classmethod
	def from_input(cls, id, input_dict):
		return cls(id, name=input_dict["experiment"])


class Variable(VSObject):
	def __init__(self, id, uid="???", CF_standard_name="???", cell_measures="???", cell_methods="???",
	             description="???", frequency="???", realm="???", MIP_variable="???", content_type="???", title="???",
	             spatial_structure="???", temporal_shape="???", table="???", compound_name="???", **kwargs):
		super().__init__(id, **kwargs)
		self.uid = uid
		self.CF_standard_name = CF_standard_name
		self.cell_measures = cell_measures
		self.cell_methods = cell_methods
		self.description = description
		self.frequency = frequency
		self.MIP_variable = MIP_variable
		self.content_type = content_type
		self.title = title
		self.spatial_structure = spatial_structure
		self.temporal_shape = temporal_shape
		self.table = table
		self.compound_name = compound_name
		self.realm = realm

	def print_content(self, level=0, add_content=True):
		indent = "    " * level
		return [f"{indent}variable {self.MIP_variable} at frequency {self.frequency} (id: {self.id}, title: {self.title})", ]

	@classmethod
	def from_input(cls, id, input_dict):
		input_dict["content_type"] = input_dict.pop("type", "???")
		input_dict["CF_standard_name"] = input_dict.pop("cf_standard_name_(from_mip_variables)", "???")
		input_dict["MIP_variable"] = input_dict.pop("mip_variables", "???")
		input_dict["spatial_structure"] = input_dict.pop("spatial_structure_(title)", "???")
		input_dict["realm"] = copy.deepcopy(input_dict.pop("modeling_realm", "???"))
		return cls(id=id, **input_dict)


class VocabularyServer(object):
	def __init__(self, input_database, **kwargs):
		self.vocabulary_server = copy.deepcopy(input_database)
		self.transform_content()

	def transform_content(self):
		for (id, elt) in self.vocabulary_server["data_request_opportunities_(public)"]["variables"]["records"].items():
			self.vocabulary_server["data_request_opportunities_(public)"]["variables"]["records"][id] = \
				Variable.from_input(id, elt)
		for (id, elt) in self.vocabulary_server["data_request_opportunities_(public)"]["experiment"]["records"].items():
			self.vocabulary_server["data_request_opportunities_(public)"]["experiment"]["records"][id] = \
				Experiment.from_input(id, elt)

	@classmethod
	def from_input(cls, input_database):
		content = read_json_file(input_database)
		return cls(content)

	def get_variable(self, element_id, element_key=None, default=False):
		rep = self.get_element(element_table="data_request_opportunities_(public)", element_type="variables",
		                       element_id=element_id, default=default)
		if element_key is not None:
			rep = rep.__getattribute__(element_key)
		return rep

	def get_experiment(self, element_id, element_key=None, default=False):
		rep = self.get_element(element_table="data_request_opportunities_(public)", element_type="experiment",
		                       element_id=element_id, default=default)
		if element_key is not None:
			rep = rep.__getattribute__(element_key)
		return rep

	def get_element(self, element_table, element_type, element_id, element_key=None, default=False):
		logger = get_logger()
		if element_table in self.vocabulary_server:
			if element_type in self.vocabulary_server[element_table]:
				if element_id in self.vocabulary_server[element_table][element_type]["records"]:
					value = copy.deepcopy(self.vocabulary_server[element_table][element_type]["records"][element_id])
					if element_key is not None:
						if element_key in value:
							value = value[element_key]
						else:
							logger.error(f"Could not find key {element_key} of id {element_id} of type {element_type} "
							             f"in table {element_table} in the vocabulary server.")
							raise ValueError(f"Could not find key {element_key} of id {element_id} of type "
							                 f"{element_type} in table {element_table} in the vocabulary server.")
					return value
				elif default:
					logger.critical(f"Could not find id {element_id} of type {element_type} in table {element_table}"
					                f" in the vocabulary server.")
					return default
				else:
					logger.error(f"Could not find id {element_id} of type {element_type} in table {element_table} "
					             f"in the vocabulary server.")
					raise ValueError(f"Could not find id {element_id} of type {element_type} in table {element_table} "
					                 f"in the vocabulary server.")
			else:
				logger.error(f"Could not find element type {element_type} in table {element_table} "
				             f"in the vocabulary server.")
				raise ValueError(f"Could not find element type {element_type} in table {element_table} "
				                 f"in the vocabulary server.")
		else:
			logger.error(f"Could not find element table {element_table} in the vocabulary server.")
			raise ValueError(f"Could not find element table {element_table} in the vocabulary server.")
