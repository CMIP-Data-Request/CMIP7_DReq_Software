#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vocabulary server.
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import copy
import os

import six

from logger import get_logger
from tools import read_json_file


class VSObject(object):
	def __init__(self, id, vs, **kwargs):
		self.vs = vs
		self.attributes = dict(id=id)

	@property
	def id(self):
		return self.attributes["id"]

	def get_value_from_vs(self, key, element_type=None, target_type=None):
		if element_type is None:
			element_type = key
		value = self.attributes[key]
		if not isinstance(value, list):
			value = [value, ]
		value = [self.vs.get_element(element_type=element_type, element_id=val) for val in value]
		value = copy.deepcopy(value)
		if not target_type in ["list", ] and isinstance(value, list) and len(value) == 1:
			value = value[0]
		return value

	def __copy__(self):
		return type(self).__call__(vs=self.vs, **copy.deepcopy(self.attributes))

	def __deepcopy__(self, memodict={}):
		return self.__copy__()

	def get(self, item, default=None):
		return self.attributes.get(item, default)

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
		Function to return a printable version of the content of the current class.
		:param level: level of indent of the result
		:param add_content: should inner content be added?
		:return: a list of strings that can be assembled to print the content.
		"""
		indent = "    " * level
		return [f"{indent}{type(self).__name__}: {self.id}", ]


class Experiment(VSObject):
	def __init__(self, id, name, **kwargs):
		super().__init__(id, **kwargs)
		self.attributes["name"] = name

	@property
	def name(self):
		return self.attributes["name"]

	def print_content(self, level=0, add_content=True):
		indent = "    " * level
		return [f"{indent}experiment {self.name} (id: {self.id})", ]

	@classmethod
	def from_input(cls, id, vs, input_dict):
		return cls(id, vs=vs, name=input_dict["experiment"])


class Variable(VSObject):
	def __init__(self, id, **kwargs):
		super().__init__(id, **kwargs)
		keys = ["cf_standard_name", "cell_measures", "cell_methods", "description", "cmip7_frequency",
		        "modelling_realm", "content_type", "title", "spatial_shape", "temporal_shape", "table", "compound_name",
		        "structure_label", "structure_title", "physical_parameter"]
		defaults_dict = {key: "???" for key in keys}
		defaults_dict.update(kwargs)
		for elt in set(list(defaults_dict)) - set(keys):
			del defaults_dict[elt]
		attrs = copy.deepcopy(self.attributes)
		attrs.update(defaults_dict)
		self.attributes = attrs

	@property
	def uid(self):
		return self.id

	@property
	def cf_standard_name(self):
		return self.get_value_from_vs(key="cf_standard_name", element_type="cf_standard_names")

	@property
	def cell_measures(self):
		return self.get_value_from_vs(key="cell_measures", target_type="list")

	@property
	def cell_methods(self):
		return self.get_value_from_vs(key="cell_methods", target_type="list")

	@property
	def compound_name(self):
		return self.get("compound_name")

	@property
	def content_type(self):
		return self.get("content_type")

	@property
	def description(self):
		return self.get("description")

	@property
	def frequency(self):
		return self.get_value_from_vs(key="cmip7_frequency")

	@property
	def modelling_realm(self):
		return self.get_value_from_vs(key="modelling_realm", target_type="list")

	@property
	def physical_parameter(self):
		return self.get_value_from_vs(key="physical_parameter", element_type="physical_parameters")

	@property
	def spatial_shape(self):
		return self.get_value_from_vs(key="spatial_shape", target_type="list")

	@property
	def structure_title(self):
		return self.get_value_from_vs(key="structure_title", element_type="structure")

	@property
	def table(self):
		return self.get_value_from_vs(key="table", element_type="table_identifiers", target_type="list")

	@property
	def temporal_shape(self):
		return self.get_value_from_vs(key="temporal_shape", target_type="list")

	@property
	def title(self):
		return self.get("title")

	def print_content(self, level=0, add_content=True):
		indent = "    " * level
		physical_parameter = self.physical_parameter["name"]
		frequency = self.frequency["name"]
		return [f"{indent}variable {physical_parameter} at frequency {frequency} (id: {self.id}, title: {self.title})", ]

	@classmethod
	def from_input(cls, id, vs, input_dict):
		if "content_type" not in input_dict:
			input_dict["content_type"] = input_dict.pop("type", "???")
		if "cf_standard_name" not in input_dict:
			input_dict["cf_standard_name"] = input_dict.pop("cf_standard_name_(from_physical_parameter)", "???")
		return cls(id=id, vs=vs, **input_dict)


class VocabularyServer(object):
	def __init__(self, input_database, **kwargs):
		self.version = input_database.pop("version")
		self.vocabulary_server = copy.deepcopy(input_database)
		self.transform_content()

	def transform_content(self):
		for (id, elt) in self.vocabulary_server["variables"].items():
			self.vocabulary_server["variables"][id] = Variable.from_input(id, vs=self, input_dict=elt)
		for (id, elt) in self.vocabulary_server["experiments"].items():
			self.vocabulary_server["experiments"][id] = Experiment.from_input(id, vs=self, input_dict=elt)

	@classmethod
	def from_input(cls, input_database):
		content = read_json_file(input_database)
		return cls(content)

	def get_variable(self, element_id, element_key=None, id_type="uid", default=False):
		rep = self.get_element(element_type="variables", element_id=element_id, default=default, id_type=id_type)
		if element_key is not None:
			rep = rep.get(element_key)
		return rep

	def get_experiment(self, element_id, element_key=None, default=False, id_type="uid"):
		rep = self.get_element(element_type="experiments", element_id=element_id, default=default, id_type=id_type)
		if element_key is not None:
			rep = rep.get(element_key)
		return rep

	def get_element(self, element_type, element_id, element_key=None, default=False, id_type="uid"):
		logger = get_logger()
		if element_type in self.vocabulary_server:
			if element_id in ["???", None]:
				logger.critical(f"Undefined id of type {element_type}")
				return element_id
			else:
				found = False
				if id_type in ["uid", ] and element_id in self.vocabulary_server[element_type]:
					value = self.vocabulary_server[element_type][element_id]
					found = True
				elif isinstance(id_type, six.string_types):
					value = list()
					for (key, val) in self.vocabulary_server[element_type].items():
						if element_id is None:
							raise ValueError("None element_id found")
						if element_id in val.get(id_type, list()) or element_id == val.get(id_type, list()):
							value.append(key)
					# value = [elt for (elt, val) in self.vocabulary_server[element_type].items()
					#          if element_id in val.get(id_type, list()) or element_id == val.get(id_type, list())]
					if len(value) == 1:
						found = True
						element_id = value[0]
						value = self.vocabulary_server[element_type][element_id]
					elif len(value) > 1:
						logger.error(f"id_type {id_type} provided is not unique for element type {element_type} and "
						             f"value {element_key}.")
						raise ValueError(f"id_type {id_type} provided is not unique for element type {element_type} "
						                 f"and value {element_key}.")
				if found:
					value = copy.deepcopy(value)
					if element_key is not None:
						if element_key in value:
							value = value[element_key]
						else:
							logger.error(f"Could not find key {element_key} of id {element_id} of type {element_type} "
							             f"in the vocabulary server.")
							raise ValueError(f"Could not find key {element_key} of id {element_id} of type "
							                 f"{element_type} in the vocabulary server.")
					elif isinstance(element_key, dict):
						value["uid"] = element_id
					return value
				elif default:
					logger.critical(f"Could not find {id_type} {element_id} of type {element_type}"
					                f" in the vocabulary server.")
					return default
				else:
					logger.error(f"Could not find {id_type} {element_id} of type {element_type} "
					             f"in the vocabulary server.")
					raise ValueError(f"Could not find {id_type} {element_id} of type {element_type} "
					                 f"in the vocabulary server.")
		else:
			logger.error(f"Could not find element type {element_type} in the vocabulary server.")
			raise ValueError(f"Could not find element type {element_type} in the vocabulary server.")
