#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test data_request.py
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import copy
import os
import unittest
import sys


sys.path.append('../data_request_api/stable/transform')


from tools import read_json_input_file_content, write_json_output_file_content

from data_request import DRObjects, Theme, ExperimentsGroup, VariablesGroup, Opportunity, DataRequest, version
from vocabulary_server import VocabularyServer, is_link_id_or_value


class TestDRObjects(unittest.TestCase):
	def setUp(self):
		self.vs = VocabularyServer.from_input("test_datasets/VS_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			DRObjects()

		with self.assertRaises(TypeError):
			DRObjects("link::my_id")

		with self.assertRaises(TypeError):
			DRObjects(self.vs)

		obj = DRObjects("link::my_id", self.vs)
		obj = DRObjects(id="link::my_id", vs=self.vs)
		self.assertEqual(obj.DR_type, "undef")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			DRObjects.from_input()

		with self.assertRaises(TypeError):
			DRObjects.from_input("link::my_id")

		with self.assertRaises(TypeError):
			DRObjects.from_input(self.vs)

		with self.assertRaises(TypeError):
			DRObjects.from_input("link::my_id", self.vs)

		obj = DRObjects.from_input(id="link::my_id", vs=self.vs)

	def test_check(self):
		obj = DRObjects("my_id", self.vs)
		obj.check()

	@unittest.expectedFailure
	def test_print(self):
		obj = DRObjects(id="link::my_id", vs=self.vs)
		str(obj)

	def test_eq(self):
		obj = DRObjects(id="link::my_id", vs=self.vs)
		obj2 = copy.deepcopy(obj)
		self.assertEqual(obj, obj2)

		obj3 = DRObjects(id="link::my_id_2", vs=self.vs)
		self.assertNotEqual(obj, obj3)

		obj4 = Theme(id="link::my_id", vs=self.vs)
		self.assertNotEqual(obj, obj4)


class TestTheme(unittest.TestCase):
	def setUp(self):
		self.vs = VocabularyServer.from_input("test_datasets/VS_output.json")

	def test_print(self):
		obj = Theme(id="link::default_115", vs=self.vs)
		self.assertEqual(obj.DR_type, "data_request_themes")
		ref_str = "Theme: Atmosphere (id: default_115)"
		self.assertEqual(obj.print_content(), [ref_str, ])
		self.assertEqual(obj.print_content(level=1), ["    " + ref_str, ])
		self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
		self.assertEqual(str(obj), ref_str)

	def test_eq(self):
		obj = Theme(id="link::my_id", vs=self.vs)
		obj2 = copy.deepcopy(obj)
		self.assertEqual(obj, obj2)

		obj3 = Theme(id="link::my_id_2", vs=self.vs)
		self.assertNotEqual(obj, obj3)

		obj4 = DRObjects(id="link::my_id", vs=self.vs)
		self.assertNotEqual(obj, obj4)


class TestExperimentsGroup(unittest.TestCase):
	def setUp(self):
		self.vs = VocabularyServer.from_input("test_datasets/VS_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			ExperimentsGroup()

		with self.assertRaises(TypeError):
			ExperimentsGroup("link::my_id")

		with self.assertRaises(TypeError):
			ExperimentsGroup(self.vs)

		with self.assertRaises(TypeError):
			obj = ExperimentsGroup("link::my_id", self.vs)

		obj = ExperimentsGroup(id="link::my_id", vs=self.vs, experiments=["link::test1", "link::test2"])
		self.assertEqual(obj.DR_type, "experiment_groups")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			ExperimentsGroup.from_input()

		with self.assertRaises(TypeError):
			ExperimentsGroup.from_input("link::my_id")

		with self.assertRaises(TypeError):
			ExperimentsGroup.from_input(self.vs)

		with self.assertRaises(TypeError):
			ExperimentsGroup.from_input("link::my_id", self.vs)

		obj = ExperimentsGroup.from_input(id="link::my_id", vs=self.vs)

		with self.assertRaises(ValueError):
			obj = ExperimentsGroup.from_input(id="link::my_id", vs=self.vs, experiments=["link::test", ])

		obj = ExperimentsGroup.from_input(id="link::my_id", vs=self.vs, experiments=["link::default_291", "link::default_292"])

	def test_check(self):
		obj = ExperimentsGroup(id="link::my_id", vs=self.vs)
		obj.check()

		obj = ExperimentsGroup(id="link::my_id", vs=self.vs, experiments=["link::default_291", "link::default_292"])
		obj.check()

	def test_methods(self):
		obj = ExperimentsGroup(id="link::my_id", vs=self.vs)
		self.assertEqual(obj.count(), 0)
		self.assertEqual(obj.get_experiments(), list())

		obj = ExperimentsGroup.from_input(id="link::default_276", vs=self.vs, experiments=["link::default_291", "link::default_292"])
		self.assertEqual(obj.count(), 2)
		self.assertListEqual(obj.get_experiments(),
		                     [self.vs.get_experiment("link::default_291"), self.vs.get_experiment("link::default_292")])

	def test_print(self):
		obj = ExperimentsGroup.from_input(id="link::default_288", vs=self.vs, experiments=["link::default_317", "link::default_310"])
		ref_str = "ExperimentsGroup: historical (id: default_288)"
		ref_str_2 = [
			ref_str,
			"    Experiments included:",
			"        experiment historical (id: default_317)",
			"        experiment esm-hist (id: default_310)"
		]
		self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
		self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
		self.assertEqual(obj.print_content(), ref_str_2)
		self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
		self.assertEqual(str(obj), os.linesep.join(ref_str_2))

	def test_eq(self):
		obj = ExperimentsGroup(id="link::my_id", vs=self.vs)
		obj2 = copy.deepcopy(obj)
		self.assertEqual(obj, obj2)

		obj3 = ExperimentsGroup(id="link::my_id_2", vs=self.vs)
		self.assertNotEqual(obj, obj3)

		obj4 = ExperimentsGroup(id="link::my_id", vs=self.vs, experiments=["link::default_292", "link::default_301"])
		self.assertNotEqual(obj, obj4)

		obj5 = DRObjects(id="link::my_id", vs=self.vs)
		self.assertNotEqual(obj, obj5)


class TestVariablesGroup(unittest.TestCase):
	def setUp(self):
		self.vs = VocabularyServer.from_input("test_datasets/VS_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			VariablesGroup()

		with self.assertRaises(TypeError):
			VariablesGroup("link::my_id")

		with self.assertRaises(TypeError):
			VariablesGroup(self.vs)

		with self.assertRaises(TypeError):
			obj = VariablesGroup("link::my_id", self.vs)

		obj = VariablesGroup(id="link::my_id", vs=self.vs, variables=["link::test1", "link::test2"],
		                     mips=["link::MIP1", "link::MIP2"], priority="link::High")
		self.assertEqual(obj.DR_type, "variable_groups")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			VariablesGroup.from_input()

		with self.assertRaises(TypeError):
			VariablesGroup.from_input("link::my_id")

		with self.assertRaises(TypeError):
			VariablesGroup.from_input(self.vs)

		with self.assertRaises(TypeError):
			VariablesGroup.from_input("link::my_id", self.vs)

		obj = VariablesGroup.from_input(id="link::my_id", vs=self.vs)

		with self.assertRaises(ValueError):
			obj = VariablesGroup.from_input(id="link:my_id", vs=self.vs, variables=["link::test", ])

		obj = VariablesGroup.from_input(id="link::my_id", vs=self.vs,
		                                variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                           "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"])

	def test_check(self):
		obj = VariablesGroup(id="link::my_id", vs=self.vs)
		obj.check()

		obj = VariablesGroup(id="link::my_id", vs=self.vs,
		                     variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"])
		obj.check()

	def test_methods(self):
		obj = VariablesGroup(id="link::my_id", vs=self.vs, priority="High")
		self.assertEqual(obj.count(), 0)
		self.assertEqual(obj.get_variables(), list())
		self.assertEqual(obj.get_mips(), list())
		self.assertEqual(obj.priority, "High")

		obj = VariablesGroup.from_input(id="link::dafc7484-8c95-11ef-944e-41a8eb05f654", vs=self.vs,
		                                variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                           "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"],
		                                mips=["link::default_401", ])
		self.assertEqual(obj.count(), 2)
		self.assertListEqual(obj.get_variables(),
		                     [self.vs.get_variable("link::bab3cb52-e5dd-11e5-8482-ac72891c3257"),
		                      self.vs.get_variable("link::bab48ce0-e5dd-11e5-8482-ac72891c3257")])
		self.assertEqual(obj.get_mips(), ["link::default_401", ])
		self.assertEqual(obj.priority, "Low")

	def test_print(self):
		obj = VariablesGroup.from_input(id="link::default_581", vs=self.vs,
		                                variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                           "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"])
		ref_str = "VariablesGroup: baseline_monthly (id: default_581)"
		ref_str_2 = [
			ref_str,
			"    Variables included:",
			"        variable pr at frequency mon (id: bab3cb52-e5dd-11e5-8482-ac72891c3257, title: Precipitation)",
			"        variable psl at frequency mon (id: bab48ce0-e5dd-11e5-8482-ac72891c3257, title: Sea Level Pressure)"
		]
		self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
		self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
		self.assertEqual(obj.print_content(), ref_str_2)
		self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
		self.assertEqual(str(obj), os.linesep.join(ref_str_2))

	def test_eq(self):
		obj = VariablesGroup(id="link::my_id", vs=self.vs)
		obj2 = copy.deepcopy(obj)
		self.assertEqual(obj, obj2)

		obj3 = VariablesGroup(id="link::my_id_2", vs=self.vs)
		self.assertNotEqual(obj, obj3)

		obj4 = VariablesGroup(id="link::my_id", vs=self.vs, variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                                               "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"])
		self.assertNotEqual(obj, obj4)

		obj5 = VariablesGroup(id="link::my_id", vs=self.vs, mips=["link::default_401", ])
		self.assertNotEqual(obj, obj5)

		obj6 = VariablesGroup(id="link::my_id", vs=self.vs, priority="Medium")
		self.assertNotEqual(obj, obj6)

		obj7 = DRObjects(id="link::my_id", vs=self.vs)
		self.assertNotEqual(obj, obj7)


class TestOpportunity(unittest.TestCase):
	def setUp(self):
		self.vs = VocabularyServer.from_input("test_datasets/VS_output.json")
		self.dr = DataRequest.from_separated_inputs(DR_input="test_datasets/DR_output.json",
		                                            VS_input="test_datasets/VS_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			Opportunity()

		with self.assertRaises(TypeError):
			Opportunity("my_id")

		with self.assertRaises(TypeError):
			Opportunity(self.vs)

		with self.assertRaises(TypeError):
			obj = Opportunity("my_id", self.vs)

		obj = Opportunity(id="my_id", vs=self.vs, variables_groups=["test1", "test2"],
		                  experiments_groups=["test3", "test4"], themes=["theme1", "theme2"])
		self.assertEqual(obj.DR_type, "opportunities")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			Opportunity.from_input()

		with self.assertRaises(TypeError):
			Opportunity.from_input("my_id")

		with self.assertRaises(TypeError):
			Opportunity.from_input(self.vs)

		with self.assertRaises(TypeError):
			Opportunity.from_input("my_id", self.vs)

		obj = Opportunity.from_input(id="my_id", vs=self.vs, dr=self.dr)

		with self.assertRaises(ValueError):
			obj = Opportunity.from_input(id="my_id", vs=self.vs, dr=self.dr, variable_groups=["test", ])

		obj = Opportunity.from_input(id="my_id", vs=self.vs, dr=self.dr,
		                             variable_groups=["link::default_583", "link::default_584"],
		                             experiment_groups=["link::default_285", ],
		                             themes=["link::default_104", "link::default_105", "link::default_106"])

	def test_check(self):
		obj = Opportunity(id="my_id", vs=self.vs, dr=self.dr)
		obj.check()

		obj = Opportunity(id="my_id", vs=self.vs, dr=self.dr, variables_groups=["default_733", "default_734"])
		obj.check()

	def test_methods(self):
		obj = Opportunity(id="my_id", vs=self.vs, dr=self.dr)
		self.assertEqual(obj.get_experiments_groups(), list())
		self.assertEqual(obj.get_variables_groups(), list())
		self.assertEqual(obj.get_themes(), list())

		obj = Opportunity.from_input(id="link::default_425", vs=self.vs, dr=self.dr,
		                             variable_groups=["link::default_583", "link::default_584"],
		                             experiment_groups=["link::default_285", ],
		                             themes=["link::default_104", "link::default_105", "link::default_106"])
		self.assertListEqual(obj.get_experiments_groups(), [self.dr.get_experiments_group("default_285")])
		self.assertListEqual(obj.get_variables_groups(),
		                     [self.dr.get_variables_group("link::default_583"), self.dr.get_variables_group("link::default_584")])
		self.assertListEqual(obj.get_themes(),
		                     [Theme(id="link::default_104", vs=self.vs),
		                      Theme(id="link::default_105", vs=self.vs),
		                      Theme(id="link::default_106", vs=self.vs)
		                      ])

	def test_print(self):
		obj = Opportunity.from_input(id="link::default_426", vs=self.vs, dr=self.dr,
		                             variable_groups=["link::default_581", "link::default_582"],
		                             experiment_groups=["link::default_285", ],
		                             themes=["link::default_115", "link::default_117", "link::default_118"])
		ref_str = "Opportunity: Ocean Extremes (id: default_426)"
		ref_str_2 = [
			ref_str,
			"    Experiments groups included:",
			"        ExperimentsGroup: ar7-fast-track (id: default_285)",
			"    Variables groups included:",
			"        VariablesGroup: baseline_monthly (id: default_581)",
			"        VariablesGroup: baseline_subdaily (id: default_582)",
			"    Themes included:",
			"        Theme: Atmosphere (id: default_115)",
			"        Theme: Impacts & Adaptation (id: default_117)",
			"        Theme: Land & Land-Ice (id: default_118)"
		]
		self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
		self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
		self.assertEqual(obj.print_content(), ref_str_2)
		self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
		self.assertEqual(str(obj), os.linesep.join(ref_str_2))

	def test_eq(self):
		obj = Opportunity(id="my_id", vs=self.vs)
		obj2 = copy.deepcopy(obj)
		self.assertEqual(obj, obj2)

		obj3 = Opportunity(id="my_id_2", vs=self.vs)
		self.assertNotEqual(obj, obj3)

		obj4 = Opportunity(id="my_id", vs=self.vs, experiments_groups=["default_285", ])
		self.assertNotEqual(obj, obj4)

		obj5 = Opportunity(id="my_id", vs=self.vs, variables_groups=["default_733", "default_734"])
		self.assertNotEqual(obj, obj5)

		obj6 = Opportunity(id="my_id", vs=self.vs, themes=["default_104", "default_105", "default_106"])
		self.assertNotEqual(obj, obj6)

		obj7 = DRObjects(id="my_id", vs=self.vs)
		self.assertNotEqual(obj, obj7)


class TestDataRequest(unittest.TestCase):
	def setUp(self):
		self.vs_file = "test_datasets/VS_output.json"
		self.vs_dict = read_json_input_file_content(self.vs_file)
		self.vs = VocabularyServer.from_input(self.vs_file)
		self.input_database_file = "test_datasets/DR_output.json"
		self.input_database = read_json_input_file_content(self.input_database_file)
		self.complete_input_file = "test_datasets/one_base_input.json"
		self.complete_input = read_json_input_file_content(self.complete_input_file)
		self.DR_dump = "test_datasets/DR_dump.txt"

	def test_init(self):
		with self.assertRaises(TypeError):
			DataRequest()

		with self.assertRaises(TypeError):
			DataRequest(self.vs)

		with self.assertRaises(TypeError):
			DataRequest(self.input_database)

		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		self.assertEqual(len(obj.experiments_groups), 5)
		self.assertEqual(len(obj.variables_groups), 11)
		self.assertEqual(len(obj.opportunities), 4)

	def test_from_input(self):
		with self.assertRaises(TypeError):
			DataRequest.from_input()

		with self.assertRaises(TypeError):
			DataRequest.from_input(self.complete_input)

		with self.assertRaises(TypeError):
			DataRequest.from_input("test")

		with self.assertRaises(TypeError):
			DataRequest.from_input(self.input_database, version=self.vs)

		with self.assertRaises(TypeError):
			DataRequest.from_input(self.complete_input_file + "tmp", version="test")

		obj = DataRequest.from_input(json_input=self.complete_input, version="test")
		self.assertEqual(len(obj.experiments_groups), 5)
		self.assertEqual(len(obj.variables_groups), 11)
		self.assertEqual(len(obj.opportunities), 4)

		obj = DataRequest.from_input(json_input=self.complete_input_file, version="test")
		self.assertEqual(len(obj.experiments_groups), 5)
		self.assertEqual(len(obj.variables_groups), 11)
		self.assertEqual(len(obj.opportunities), 4)

	def test_from_separated_inputs(self):
		with self.assertRaises(TypeError):
			DataRequest.from_separated_inputs()

		with self.assertRaises(TypeError):
			DataRequest.from_separated_inputs(self.input_database)

		with self.assertRaises(TypeError):
			DataRequest.from_separated_inputs(self.vs)

		with self.assertRaises(TypeError):
			DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_file + "tmp")

		with self.assertRaises(TypeError):
			DataRequest.from_separated_inputs(DR_input=self.input_database_file + "tmp", VS_input=self.vs_dict)

		with self.assertRaises(TypeError):
			DataRequest.from_separated_inputs(DR_input=self.input_database_file, VS_input=self.vs)

		obj = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_dict)
		self.assertEqual(len(obj.experiments_groups), 5)
		self.assertEqual(len(obj.variables_groups), 11)
		self.assertEqual(len(obj.opportunities), 4)

		obj = DataRequest.from_separated_inputs(DR_input=self.input_database_file, VS_input=self.vs_dict)
		self.assertEqual(len(obj.experiments_groups), 5)
		self.assertEqual(len(obj.variables_groups), 11)
		self.assertEqual(len(obj.opportunities), 4)

		obj = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_file)
		self.assertEqual(len(obj.experiments_groups), 5)
		self.assertEqual(len(obj.variables_groups), 11)
		self.assertEqual(len(obj.opportunities), 4)

		obj = DataRequest.from_separated_inputs(DR_input=self.input_database_file, VS_input=self.vs_file)
		self.assertEqual(len(obj.experiments_groups), 5)
		self.assertEqual(len(obj.variables_groups), 11)
		self.assertEqual(len(obj.opportunities), 4)

	def test_split_content_from_input_json(self):
		with self.assertRaises(TypeError):
			DataRequest._split_content_from_input_json()

		with self.assertRaises(TypeError):
			DataRequest._split_content_from_input_json(self.complete_input)

		with self.assertRaises(TypeError):
			DataRequest._split_content_from_input_json("test")

		with self.assertRaises(TypeError):
			DataRequest._split_content_from_input_json(self.input_database, version=self.vs)

		with self.assertRaises(TypeError):
			DataRequest._split_content_from_input_json(self.complete_input_file + "tmp", version="test")

		DR, VS = DataRequest._split_content_from_input_json(input_json=self.complete_input, version="test")
		self.assertDictEqual(DR, self.input_database)
		self.assertDictEqual(VS, self.vs_dict)

		DR, VS = DataRequest._split_content_from_input_json(input_json=self.complete_input_file, version="test")
		self.assertDictEqual(DR, self.input_database)
		self.assertDictEqual(VS, self.vs_dict)

	def test_check(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		obj.check()

	def test_version(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		self.assertEqual(obj.software_version, version)
		self.assertEqual(obj.content_version, self.input_database["version"])
		self.assertEqual(obj.version, f"Software {version} - Content {self.input_database['version']}")

	def test_str(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		with open(self.DR_dump) as f:
			ref_str = f.read()
		self.assertEqual(str(obj), ref_str)

	def test_get_experiments_groups(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		exp_groups = obj.get_experiments_groups()
		self.assertEqual(len(exp_groups), 5)
		self.assertListEqual(exp_groups,
		                     [ExperimentsGroup.from_input(id=id, vs=self.vs,
		                                                  **self.input_database["experiment_groups"][is_link_id_or_value(id)[1]])
		                      for id in ["link::default_285", "link::default_286", "link::default_287", "link::default_288", "link::default_289"]])

	def test_get_experiments_group(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		exp_grp = obj.get_experiments_group("link::default_285")
		self.assertEqual(exp_grp,
		                 ExperimentsGroup.from_input(id="link::default_285", vs=self.vs,
		                                             **self.input_database["experiment_groups"]["default_285"]))

