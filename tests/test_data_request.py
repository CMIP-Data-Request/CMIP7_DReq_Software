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

from data_request import DRObjects, ExperimentsGroup, VariablesGroup, Opportunity, DataRequest, version
from vocabulary_server import VocabularyServer, is_link_id_or_value


class TestDRObjects(unittest.TestCase):
	def setUp(self):
		self.dr = DataRequest.from_separated_inputs(VS_input="test_datasets/VS_output.json",
		                                            DR_input="test_datasets/DR_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			DRObjects()

		with self.assertRaises(TypeError):
			DRObjects("link::my_id")

		with self.assertRaises(TypeError):
			DRObjects(self.dr)

		obj = DRObjects("link::my_id", self.dr)
		obj = DRObjects(id="link::my_id", dr=self.dr)
		self.assertEqual(obj.DR_type, "undef")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			DRObjects.from_input()

		with self.assertRaises(TypeError):
			DRObjects.from_input("link::my_id")

		with self.assertRaises(TypeError):
			DRObjects.from_input(self.dr)

		obj = DRObjects.from_input(dr=self.dr, id="link::my_id")

		obj = DRObjects.from_input(dr=self.dr, id="link::my_id", DR_type="priority_level")

	def test_check(self):
		obj = DRObjects("my_id", self.dr)
		obj.check()

	def test_print(self):
		obj = DRObjects(id="link::my_id", dr=self.dr)
		self.assertEqual(str(obj), "undef: undef (id: my_id)")

	def test_eq(self):
		obj = DRObjects(id="link::my_id", dr=self.dr)
		obj2 = copy.deepcopy(obj)
		self.assertEqual(obj, obj2)

		obj3 = DRObjects(id="link::my_id_2", dr=self.dr)
		self.assertNotEqual(obj, obj3)
		self.assertTrue(obj < obj3)
		self.assertFalse(obj > obj3)

	def test_hash(self):
		obj = DRObjects(id="link::my_id", dr=self.dr)
		my_set = set()
		my_set.add(obj)
		my_set.add(DRObjects(id="link::my_id_2", dr=self.dr))
		my_set.add(copy.deepcopy(obj))
		self.assertEqual(len(my_set), 2)

	def test_filter_on_request(self):
		obj1 = DRObjects(id="my_id", DR_type="test", dr=self.dr)
		obj2 = copy.deepcopy(obj1)
		obj3 = DRObjects(id="my_other_id", DR_type="test", dr=self.dr)
		obj4 = DRObjects(id="my_id", DR_type="test2", dr=self.dr)
		self.assertEqual(obj1.filter_on_request(obj2), (True, True))
		self.assertEqual(obj1.filter_on_request(obj3), (True, False))
		self.assertEqual(obj1.filter_on_request(obj4), (False, False))


class TestExperimentsGroup(unittest.TestCase):
	def setUp(self):
		self.dr = DataRequest.from_separated_inputs(VS_input="test_datasets/VS_output.json",
		                                            DR_input="test_datasets/DR_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			ExperimentsGroup()

		with self.assertRaises(TypeError):
			ExperimentsGroup("link::my_id")

		with self.assertRaises(TypeError):
			ExperimentsGroup(self.dr)

		obj = ExperimentsGroup("link::my_id", self.dr)

		obj = ExperimentsGroup(id="link::my_id", dr=self.dr, name="test")
		self.assertEqual(obj.DR_type, "experiment_groups")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			ExperimentsGroup.from_input()

		with self.assertRaises(TypeError):
			ExperimentsGroup.from_input("link::my_id")

		with self.assertRaises(TypeError):
			ExperimentsGroup.from_input(self.dr)

		obj = ExperimentsGroup.from_input(id="link::my_id", dr=self.dr)

		with self.assertRaises(ValueError):
			obj = ExperimentsGroup.from_input(id="link::my_id", dr=self.dr, experiments=["link::test", ])

		obj = ExperimentsGroup.from_input(id="link::my_id", dr=self.dr, experiments=["link::default_291", "link::default_292"])

	def test_check(self):
		obj = ExperimentsGroup(id="link::my_id", dr=self.dr)
		obj.check()

		obj = ExperimentsGroup(id="link::my_id", dr=self.dr, experiments=["link::default_291", "link::default_292"])
		obj.check()

	def test_methods(self):
		obj = ExperimentsGroup(id="link::my_id", dr=self.dr)
		self.assertEqual(obj.count(), 0)
		self.assertEqual(obj.get_experiments(), list())

		obj = ExperimentsGroup.from_input(id="link::default_276", dr=self.dr,
		                                  experiments=["link::default_291", "link::default_292"])
		self.assertEqual(obj.count(), 2)
		self.assertListEqual(obj.get_experiments(),
		                     [self.dr.find_element("experiments", "link::default_291"),
		                      self.dr.find_element("experiments", "link::default_292")])
		self.assertEqual(obj.get_experiments()[0].DR_type, "experiments")

	def test_print(self):
		obj = ExperimentsGroup.from_input(id="link::default_288", dr=self.dr,
		                                  experiments=["link::default_317", "link::default_310"], name="historical")
		ref_str = "experiment_group: historical (id: default_288)"
		ref_str_2 = [
			ref_str,
			"    Experiments included:",
			"        experiment: historical (id: default_317)",
			"        experiment: esm-hist (id: default_310)"
		]
		self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
		self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
		self.assertEqual(obj.print_content(), ref_str_2)
		self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
		self.assertEqual(str(obj), os.linesep.join(ref_str_2))

	def test_eq(self):
		obj = ExperimentsGroup(id="link::my_id",dr=self.dr)
		obj2 = copy.deepcopy(obj)
		self.assertEqual(obj, obj2)

		obj3 = ExperimentsGroup(id="link::my_id_2", dr=self.dr)
		self.assertNotEqual(obj, obj3)

		obj4 = ExperimentsGroup(id="link::my_id", dr=self.dr, experiments=["link::default_292", "link::default_301"])
		self.assertNotEqual(obj, obj4)

		obj5 = DRObjects(id="link::my_id", dr=self.dr)
		self.assertNotEqual(obj, obj5)

	def test_filter_on_request(self):
		exp_grp1 = self.dr.find_element("experiment_groups", "link::default_286")
		exp_grp2 = copy.deepcopy(exp_grp1)
		exp_grp3 = self.dr.find_element("experiment_groups", "link::default_287")
		exp_1 = self.dr.find_element("experiments", "link::default_294")
		exp_2 = self.dr.find_element("experiments", "link::default_310")
		obj = DRObjects(id="link::my_id", dr=self.dr)
		self.assertEqual(exp_grp1.filter_on_request(exp_grp2), (True, True))
		self.assertEqual(exp_grp1.filter_on_request(exp_grp3), (True, False))
		self.assertEqual(exp_grp1.filter_on_request(exp_1), (True, True))
		self.assertEqual(exp_grp1.filter_on_request(exp_2), (True, False))
		self.assertEqual(exp_grp1.filter_on_request(obj), (False, False))


class TestVariablesGroup(unittest.TestCase):
	def setUp(self):
		self.dr = DataRequest.from_separated_inputs(DR_input="test_datasets/DR_output.json",
		                                            VS_input="test_datasets/VS_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			VariablesGroup()

		with self.assertRaises(TypeError):
			VariablesGroup("link::my_id")

		with self.assertRaises(TypeError):
			VariablesGroup(self.dr)

		obj = VariablesGroup("link::my_id", self.dr)
		self.assertEqual(obj.DR_type, "variable_groups")

		with self.assertRaises(ValueError):
			VariablesGroup("link::my_id", self.dr, name="test", physical_parameter="link::my_link")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			VariablesGroup.from_input()

		with self.assertRaises(TypeError):
			VariablesGroup.from_input("link::my_id")

		with self.assertRaises(TypeError):
			VariablesGroup.from_input(self.dr)

		obj = VariablesGroup.from_input(id="link::my_id", dr=self.dr)

		with self.assertRaises(ValueError):
			obj = VariablesGroup.from_input(id="link:my_id", dr=self.dr, variables=["link::test", ])

		obj = VariablesGroup.from_input(id="link::my_id", dr=self.dr,
		                                variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                           "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"])

	def test_check(self):
		obj = VariablesGroup(id="link::my_id", dr=self.dr)
		obj.check()

		obj = VariablesGroup(id="link::my_id", dr=self.dr,
		                     variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"])
		obj.check()

	def test_methods(self):
		obj = VariablesGroup.from_input(id="link::my_id", dr=self.dr, priority_level="High")
		self.assertEqual(obj.count(), 0)
		self.assertEqual(obj.get_variables(), list())
		self.assertEqual(obj.get_mips(), list())
		self.assertEqual(obj.get_priority_level(), self.dr.find_element("priority_level", "High"))

		obj = VariablesGroup.from_input(id="link::dafc7484-8c95-11ef-944e-41a8eb05f654", dr=self.dr,
		                                variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                           "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"],
		                                mips=["link::default_401", ], priority_level="High")
		self.assertEqual(obj.count(), 2)
		self.assertListEqual(obj.get_variables(),
		                     [self.dr.find_element("variables", "link::bab3cb52-e5dd-11e5-8482-ac72891c3257"),
		                      self.dr.find_element("variables", "link::bab48ce0-e5dd-11e5-8482-ac72891c3257")])
		self.assertEqual(obj.get_mips(), [self.dr.find_element("mips", "link::default_401")])
		self.assertDictEqual(obj.get_priority_level().attributes, {'name': "High", "notes": "High priority should be used sparingly",
		                                    "value": 1, 'id': "default_481"})

	def test_print(self):
		obj = VariablesGroup.from_input(id="link::default_575", dr=self.dr, priority_level="Medium",
		                                name="baseline_monthly",
		                                variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                           "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"])
		ref_str = "variable_group: baseline_monthly (id: default_575)"
		ref_str_2 = [
			ref_str,
			"    Variables included:",
			"        variable: pr at frequency mon (id: bab3cb52-e5dd-11e5-8482-ac72891c3257, title: Precipitation)",
			"        variable: psl at frequency mon (id: bab48ce0-e5dd-11e5-8482-ac72891c3257, title: Sea Level Pressure)"
		]
		self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
		self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
		self.assertEqual(obj.print_content(), ref_str_2)
		self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
		self.assertEqual(str(obj), os.linesep.join(ref_str_2))

	def test_eq(self):
		obj = VariablesGroup(id="link::my_id", dr=self.dr)
		obj2 = copy.deepcopy(obj)
		self.assertEqual(obj, obj2)

		obj3 = VariablesGroup(id="link::my_id_2", dr=self.dr)
		self.assertNotEqual(obj, obj3)

		obj4 = VariablesGroup(id="link::my_id", dr=self.dr, variables=["link::bab3cb52-e5dd-11e5-8482-ac72891c3257",
		                                                               "link::bab48ce0-e5dd-11e5-8482-ac72891c3257"])
		self.assertNotEqual(obj, obj4)

		obj5 = VariablesGroup(id="link::my_id", dr=self.dr, mips=["link::default_401", ])
		self.assertNotEqual(obj, obj5)

		obj6 = VariablesGroup(id="link::my_id", dr=self.dr, priority="Medium")
		self.assertNotEqual(obj, obj6)

		obj7 = DRObjects(id="link::my_id", dr=self.dr)
		self.assertNotEqual(obj, obj7)


class TestOpportunity(unittest.TestCase):
	def setUp(self):
		self.dr = DataRequest.from_separated_inputs(DR_input="test_datasets/DR_output.json",
		                                            VS_input="test_datasets/VS_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			Opportunity()

		with self.assertRaises(TypeError):
			Opportunity("my_id")

		with self.assertRaises(TypeError):
			Opportunity(self.dr)

		obj = Opportunity("my_id", self.dr)

		obj = Opportunity(id="my_id", dr=self.dr, variables_groups=["test1", "test2"],
		                  experiments_groups=["test3", "test4"], themes=["theme1", "theme2"])
		self.assertEqual(obj.DR_type, "opportunities")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			Opportunity.from_input()

		with self.assertRaises(TypeError):
			Opportunity.from_input("my_id")

		with self.assertRaises(TypeError):
			Opportunity.from_input(self.dr)

		obj = Opportunity.from_input("my_id", self.dr)

		obj = Opportunity.from_input(id="my_id", dr=self.dr)

		with self.assertRaises(ValueError):
			obj = Opportunity.from_input(id="my_id", dr=self.dr, variable_groups=["test", ])

		obj = Opportunity.from_input(id="my_id", dr=self.dr,
		                             variable_groups=["link::default_577", "link::default_578"],
		                             experiment_groups=["link::default_285", ],
		                             data_request_themes=["link::default_115", "link::default_116", "link::default_117"])

	def test_check(self):
		obj = Opportunity(id="my_id", dr=self.dr)
		obj.check()

		obj = Opportunity(id="my_id", dr=self.dr, variables_groups=["default_733", "default_734"])
		obj.check()

	def test_methods(self):
		obj = Opportunity(id="my_id", dr=self.dr)
		self.assertEqual(obj.get_experiment_groups(), list())
		self.assertEqual(obj.get_variable_groups(), list())
		self.assertEqual(obj.get_themes(), list())

		obj = Opportunity.from_input(id="link::default_425", dr=self.dr,
		                             variable_groups=["link::default_577", "link::default_578"],
		                             experiment_groups=["link::default_285", ],
		                             data_request_themes=["link::default_116", "link::default_117", "link::default_119"])
		self.assertListEqual(obj.get_experiment_groups(), [self.dr.find_element("experiment_groups", "default_285")])
		self.assertListEqual(obj.get_variable_groups(),
		                     [self.dr.find_element("variable_groups", "link::default_577"),
		                      self.dr.find_element("variable_groups", "link::default_578")])
		self.assertListEqual(obj.get_themes(),
		                     [self.dr.find_element("data_request_themes", "link::default_116"),
		                      self.dr.find_element("data_request_themes", "link::default_117"),
		                      self.dr.find_element("data_request_themes", "link::default_119")
		                      ])

	def test_print(self):
		obj = Opportunity.from_input(id="link::default_420", dr=self.dr, name="Ocean Extremes",
		                             variable_groups=["link::default_575", "link::default_576"],
		                             experiment_groups=["link::default_285", ],
		                             data_request_themes=["link::default_115", "link::default_117", "link::default_118"])
		ref_str = "opportunity: Ocean Extremes (id: default_420)"
		ref_str_2 = [
			ref_str,
			"    Experiments groups included:",
			"        experiment_group: ar7-fast-track (id: default_285)",
			"    Variables groups included:",
			"        variable_group: baseline_monthly (id: default_575)",
			"        variable_group: baseline_subdaily (id: default_576)",
			"    Themes included:",
			"        data_request_theme: Atmosphere (id: default_115)",
			"        data_request_theme: Impacts & Adaptation (id: default_117)",
			"        data_request_theme: Land & Land-Ice (id: default_118)",
			"    Time slices included:"
		]
		self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
		self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
		self.assertEqual(obj.print_content(), ref_str_2)
		self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
		self.assertEqual(str(obj), os.linesep.join(ref_str_2))

	def test_eq(self):
		obj = Opportunity(id="my_id", dr=self.dr)
		obj2 = copy.deepcopy(obj)
		self.assertEqual(obj, obj2)

		obj3 = Opportunity(id="my_id_2", dr=self.dr)
		self.assertNotEqual(obj, obj3)

		obj4 = Opportunity(id="my_id", dr=self.dr, experiments_groups=["default_285", ])
		self.assertNotEqual(obj, obj4)

		obj5 = Opportunity(id="my_id", dr=self.dr, variables_groups=["default_733", "default_734"])
		self.assertNotEqual(obj, obj5)

		obj6 = Opportunity(id="my_id", dr=self.dr, themes=["default_104", "default_105", "default_106"])
		self.assertNotEqual(obj, obj6)

		obj7 = DRObjects(id="my_id", dr=self.dr)
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
		self.assertEqual(len(obj.get_experiment_groups()), 5)
		self.assertEqual(len(obj.get_variable_groups()), 11)
		self.assertEqual(len(obj.get_opportunities()), 4)

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
		self.assertEqual(len(obj.get_experiment_groups()), 5)
		self.assertEqual(len(obj.get_variable_groups()), 11)
		self.assertEqual(len(obj.get_opportunities()), 4)

		obj = DataRequest.from_input(json_input=self.complete_input_file, version="test")
		self.assertEqual(len(obj.get_experiment_groups()), 5)
		self.assertEqual(len(obj.get_variable_groups()), 11)
		self.assertEqual(len(obj.get_opportunities()), 4)

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
		self.assertEqual(len(obj.get_experiment_groups()), 5)
		self.assertEqual(len(obj.get_variable_groups()), 11)
		self.assertEqual(len(obj.get_opportunities()), 4)

		obj = DataRequest.from_separated_inputs(DR_input=self.input_database_file, VS_input=self.vs_dict)
		self.assertEqual(len(obj.get_experiment_groups()), 5)
		self.assertEqual(len(obj.get_variable_groups()), 11)
		self.assertEqual(len(obj.get_opportunities()), 4)

		obj = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_file)
		self.assertEqual(len(obj.get_experiment_groups()), 5)
		self.assertEqual(len(obj.get_variable_groups()), 11)
		self.assertEqual(len(obj.get_opportunities()), 4)

		obj = DataRequest.from_separated_inputs(DR_input=self.input_database_file, VS_input=self.vs_file)
		self.assertEqual(len(obj.get_experiment_groups()), 5)
		self.assertEqual(len(obj.get_variable_groups()), 11)
		self.assertEqual(len(obj.get_opportunities()), 4)

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

	def test_get_experiment_groups(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		exp_groups = obj.get_experiment_groups()
		self.assertEqual(len(exp_groups), 5)
		self.assertListEqual(exp_groups,
		                     [obj.find_element("experiment_groups", id)
		                      for id in ["link::default_285", "link::default_286", "link::default_287", "link::default_288", "link::default_289"]])

	def test_get_experiment_group(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		exp_grp = obj.get_experiment_group("link::default_285")
		self.assertEqual(exp_grp,
		                 obj.find_element("experiment_groups", "link::default_285"))
		with self.assertRaises(ValueError):
			exp_grp = obj.get_experiment_group("test")

	def test_get_opportunities(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		opportunities = obj.get_opportunities()
		self.assertEqual(len(opportunities), 4)
		self.assertListEqual(opportunities,
		                     [obj.find_element("opportunities", id)
		                      for id in ["link::default_418", "link::default_419", "link::default_420", "link::default_421"]])

	def test_get_opportunity(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		opportunity = obj.get_opportunity("link::default_418")
		self.assertEqual(opportunity,
		                 obj.find_element("opportunities", "link::default_418"))
		with self.assertRaises(ValueError):
			op = obj.get_opportunity("test")

	def test_get_variable_groups(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		var_groups = obj.get_variable_groups()
		self.assertEqual(len(var_groups), 11)
		self.assertListEqual(var_groups,
		                     [obj.find_element("variable_groups", id)
		                      for id in ["link::default_569", "link::default_570", "link::default_571",
		                                 "link::default_572", "link::default_573", "link::default_574",
		                                 "link::default_575", "link::default_576", "link::default_577",
		                                 "link::default_578", "link::default_579"]])

	def test_get_variable_group(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		var_grp = obj.get_variable_group("link::default_575")
		self.assertEqual(var_grp,
		                 obj.find_element("variable_groups", "link::default_575"))
		with self.assertRaises(ValueError):
			var_grp = obj.get_variable_group("test")

	def test_get_variables(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		variables = obj.get_variables()
		self.assertListEqual(variables,
		                     [obj.find_element("variables", f"link::{nb}")
		                      for nb in sorted(list(self.vs.vocabulary_server["variables"]))])

	def test_get_mips(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		mips = obj.get_mips()
		self.assertListEqual(mips,
		                     [obj.find_element("mips", f"link::{nb}")
		                      for nb in sorted(list(self.vs.vocabulary_server["mips"]))])

	def test_get_experiments(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		experiments = obj.get_experiments()
		self.assertListEqual(experiments,
		                     [obj.find_element("experiments", f"link::{nb}")
		                      for nb in sorted(list(self.vs.vocabulary_server["experiments"]))])

	def test_get_themes(self):
		obj = DataRequest(input_database=self.input_database, VS=self.vs)
		themes = obj.get_data_request_themes()
		self.assertListEqual(themes,
		                     [obj.find_element("data_request_themes", f"link::{nb}")
		                      for nb in sorted(list(self.vs.vocabulary_server["data_request_themes"]))])


class TestDataRequestFilter(unittest.TestCase):
	def setUp(self):
		self.vs_file = "test_datasets/VS_output.json"
		self.vs = VocabularyServer.from_input(self.vs_file)
		self.input_database_file = "test_datasets/DR_output.json"
		self.input_database = read_json_input_file_content(self.input_database_file)
		self.dr = DataRequest(input_database=self.input_database, VS=self.vs)

	def test_element_per_identifier_from_vs(self):
		id_var = "link::1aab80fc-b006-11e6-9289-ac72891c3257"
		name_var = "Omon.wo"
		target_var = self.dr.find_element("variables", id_var)
		self.assertEqual(self.dr.find_element_per_identifier_from_vs(element_type="variables", key="id", value=id_var),
		                 target_var)
		self.assertEqual(self.dr.find_element_per_identifier_from_vs(element_type="variables", key="name",
		                                                             value=name_var),
		                 target_var)
		with self.assertRaises(ValueError):
			self.dr.find_element_per_identifier_from_vs(element_type="variables", key="name", value="toto")
		with self.assertRaises(ValueError):
			self.dr.find_element_per_identifier_from_vs(element_type="variables", key="id", value="link::toto")
		self.assertEqual(self.dr.find_element_per_identifier_from_vs(element_type="variables", key="id",
		                                                             value="link::toto", default=None),
		                 None)
		self.assertEqual(self.dr.find_element_per_identifier_from_vs(element_type="variables", key="name",
		                                                             value="toto", default=None),
		                 None)
		with self.assertRaises(ValueError):
			self.dr.find_element_per_identifier_from_vs(element_type="opportunity/variable_group_comments", key="name",
			                                            value="undef")

	def test_element_from_vs(self):
		id_var = "link::1aab80fc-b006-11e6-9289-ac72891c3257"
		name_var = "Omon.wo"
		target_var = self.dr.find_element("variables", id_var)
		self.assertEqual(self.dr.find_element_from_vs(element_type="variables", value=id_var), target_var)
		self.assertEqual(self.dr.find_element_from_vs(element_type="variables", value=name_var), target_var)
		with self.assertRaises(ValueError):
			self.dr.find_element_from_vs(element_type="variables", value="toto")
		with self.assertRaises(ValueError):
			self.dr.find_element_from_vs(element_type="variables", value="link::toto")
		self.assertEqual(self.dr.find_element_from_vs(element_type="variables", value="link::toto", default=None), None)
		self.assertEqual(self.dr.find_element_from_vs(element_type="variables", value="toto", default=None), None)
		with self.assertRaises(ValueError):
			self.dr.find_element_from_vs(element_type="opportunity/variable_group_comments", value="undef")

	def test_filter_elements_per_request(self):
		with self.assertRaises(TypeError):
			self.dr.filter_elements_per_request()

		self.assertEqual(self.dr.filter_elements_per_request("opportunities"), self.dr.get_opportunities())
		self.assertEqual(self.dr.filter_elements_per_request("opportunities", operation="any"),
		                 self.dr.get_opportunities())
		with self.assertRaises(ValueError):
			self.dr.filter_elements_per_request("opportunities", operation="one")

		with self.assertRaises(ValueError):
			self.dr.filter_elements_per_request("opportunities", requests=dict(variables="link::test_dummy"))
		self.assertEqual(self.dr.filter_elements_per_request("opportunities",
		                                                     requests=dict(variables="link::test_dummy"),
		                                                     skip_if_missing=True), self.dr.get_opportunities())

	def test_find_variables_per_priority(self):
		priority = "Medium"
		priority_obj = self.dr.find_element("priority_level", "link::default_482")
		target_var_list = [self.dr.find_element("variables", id)
		                   for id in ["link::83bbfb6e-7f07-11ef-9308-b1dd71e64bec",
		                              "link::83bbfb71-7f07-11ef-9308-b1dd71e64bec",
		                              "link::83bbfb7c-7f07-11ef-9308-b1dd71e64bec",
		                              "link::83bbfb7f-7f07-11ef-9308-b1dd71e64bec",
		                              "link::83bbfb94-7f07-11ef-9308-b1dd71e64bec",
		                              "link::83bbfc6e-7f07-11ef-9308-b1dd71e64bec",
		                              "link::83bbfc6f-7f07-11ef-9308-b1dd71e64bec",
		                              "link::ba9f3ac0-e5dd-11e5-8482-ac72891c3257",
		                              "link::ba9f643c-e5dd-11e5-8482-ac72891c3257",
		                              "link::ba9f686a-e5dd-11e5-8482-ac72891c3257",
		                              "link::ba9f91f0-e5dd-11e5-8482-ac72891c3257",
		                              "link::baa4e07e-e5dd-11e5-8482-ac72891c3257",
		                              "link::baa720e6-e5dd-11e5-8482-ac72891c3257",
		                              "link::baa72514-e5dd-11e5-8482-ac72891c3257",
		                              "link::c9180bae-c5e8-11e6-84e6-5404a60d96b5",
		                              "link::c9181982-c5e8-11e6-84e6-5404a60d96b5"
		                              ]]
		var_list = self.dr.find_variables_per_priority(priority=priority)
		self.assertEqual(len(var_list), 16)
		self.assertListEqual(var_list, target_var_list)
		var_list = self.dr.find_variables_per_priority(priority=priority_obj)
		self.assertEqual(len(var_list), 16)
		self.assertListEqual(var_list, target_var_list)

	def test_find_opportunities_per_theme(self):
		theme_id = "link::default_115"
		theme_name = "Atmosphere"
		theme_target = self.dr.find_element("data_request_themes", theme_id)
		opportunities = [self.dr.get_opportunity(id) for id in ["link::default_418", ]]
		self.assertListEqual(self.dr.find_opportunities_per_theme(theme_id), opportunities)
		self.assertListEqual(self.dr.find_opportunities_per_theme(theme_name), opportunities)
		self.assertListEqual(self.dr.find_opportunities_per_theme(theme_target), opportunities)
		with self.assertRaises(ValueError):
			self.dr.find_opportunities_per_theme("toto")
		with self.assertRaises(ValueError):
			self.dr.find_opportunities_per_theme("link::toto")

	def test_find_experiments_per_theme(self):
		theme_id = "link::default_115"
		theme_name = "Atmosphere"
		theme_target = self.dr.find_element("data_request_themes", theme_id)
		exp = [self.dr.find_element("experiments", id) for id in ["link::default_310", "link::default_317"]]
		self.assertListEqual(self.dr.find_experiments_per_theme(theme_id), exp)
		self.assertListEqual(self.dr.find_experiments_per_theme(theme_name), exp)
		self.assertListEqual(self.dr.find_experiments_per_theme(theme_target), exp)

	def test_find_variables_per_theme(self):
		theme_id = "link::default_115"
		theme_name = "Atmosphere"
		theme_target = self.dr.find_element("data_request_themes", theme_id)
		var = [self.dr.find_element("variables", id) for id in ["link::83bbfc65-7f07-11ef-9308-b1dd71e64bec",
		                                                        "link::83bbfc71-7f07-11ef-9308-b1dd71e64bec",
		                                                        "link::baaefbcc-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::baaf8452-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab034a6-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab1c668-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab3c904-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab47354-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab52b5a-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab59202-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab5df78-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab65138-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab91b20-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::babb12ae-e5dd-11e5-8482-ac72891c3257"]]
		self.assertListEqual(self.dr.find_variables_per_theme(theme_id), var)
		self.assertListEqual(self.dr.find_variables_per_theme(theme_name), var)
		self.assertListEqual(self.dr.find_variables_per_theme(theme_target), var)

	def test_find_mips_per_theme(self):
		theme_id = "link::default_115"
		theme_name = "Atmosphere"
		theme_target = self.dr.find_element("data_request_themes", theme_id)
		mips = [self.dr.find_element("mips", id) for id in ["link::default_404", "link::default_405",
		                                                    "link::default_409", "link::default_411"]]
		self.assertListEqual(self.dr.find_mips_per_theme(theme_id), mips)
		self.assertListEqual(self.dr.find_mips_per_theme(theme_name), mips)
		self.assertListEqual(self.dr.find_mips_per_theme(theme_target), mips)

	def test_themes_per_opportunity(self):
		op_id = "link::default_418"
		op_name = "Accurate assessment of land-atmosphere coupling"
		op_target = self.dr.find_element("opportunities", op_id)
		themes = [self.dr.find_element("data_request_themes", id) for id in ["link::default_115", "link::default_118"]]
		self.assertListEqual(self.dr.find_themes_per_opportunity(op_id), themes)
		self.assertListEqual(self.dr.find_themes_per_opportunity(op_name), themes)
		self.assertListEqual(self.dr.find_themes_per_opportunity(op_target), themes)

	def test_experiments_per_opportunity(self):
		op_id = "link::default_418"
		op_name = "Accurate assessment of land-atmosphere coupling"
		op_target = self.dr.find_element("opportunities", op_id)
		exp = [self.dr.find_element("experiments", id) for id in ["link::default_310", "link::default_317"]]
		self.assertListEqual(self.dr.find_experiments_per_opportunity(op_id), exp)
		self.assertListEqual(self.dr.find_experiments_per_opportunity(op_name), exp)
		self.assertListEqual(self.dr.find_experiments_per_opportunity(op_target), exp)

	def test_variables_per_opportunity(self):
		op_id = "link::default_418"
		op_name = "Accurate assessment of land-atmosphere coupling"
		op_target = self.dr.find_element("opportunities", op_id)
		var = [self.dr.find_element("variables", id) for id in ["link::83bbfc65-7f07-11ef-9308-b1dd71e64bec",
		                                                        "link::83bbfc71-7f07-11ef-9308-b1dd71e64bec",
		                                                        "link::baaefbcc-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::baaf8452-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab034a6-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab1c668-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab3c904-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab47354-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab52b5a-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab59202-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab5df78-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab65138-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::bab91b20-e5dd-11e5-8482-ac72891c3257",
		                                                        "link::babb12ae-e5dd-11e5-8482-ac72891c3257"]]
		self.assertListEqual(self.dr.find_variables_per_opportunity(op_id), var)
		self.assertListEqual(self.dr.find_variables_per_opportunity(op_name), var)
		self.assertListEqual(self.dr.find_variables_per_opportunity(op_target), var)

	def test_mips_per_opportunity(self):
		op_id = "link::default_418"
		op_name = "Accurate assessment of land-atmosphere coupling"
		op_target = self.dr.find_element("opportunities", op_id)
		mips = [self.dr.find_element("mips", id) for id in ["link::default_404", "link::default_405",
		                                                    "link::default_409", "link::default_411"]]
		self.assertListEqual(self.dr.find_mips_per_opportunity(op_id), mips)
		self.assertListEqual(self.dr.find_mips_per_opportunity(op_name), mips)
		self.assertListEqual(self.dr.find_mips_per_opportunity(op_target), mips)

	def test_opportunities_per_variable(self):
		var_id = "link::83bbfb69-7f07-11ef-9308-b1dd71e64bec"
		var_name = "Oday.zos"
		var_target = self.dr.find_element("variables", var_id)
		op = [self.dr.find_element("opportunities", id) for id in ["link::default_420", ]]
		self.assertListEqual(self.dr.find_opportunities_per_variable(var_id), op)
		self.assertListEqual(self.dr.find_opportunities_per_variable(var_name), op)
		self.assertListEqual(self.dr.find_opportunities_per_variable(var_target), op)

	def test_themes_per_variable(self):
		var_id = "link::83bbfb69-7f07-11ef-9308-b1dd71e64bec"
		var_name = "Oday.zos"
		var_target = self.dr.find_element("variables", var_id)
		themes = [self.dr.find_element("data_request_themes", id) for id in ["link::default_116", "link::default_117",
		                                                                     "link::default_119"]]
		self.assertListEqual(self.dr.find_themes_per_variable(var_id), themes)
		self.assertListEqual(self.dr.find_themes_per_variable(var_name), themes)
		self.assertListEqual(self.dr.find_themes_per_variable(var_target), themes)

	def test_mips_per_variable(self):
		var_id = "link::83bbfb69-7f07-11ef-9308-b1dd71e64bec"
		var_name = "Oday.zos"
		var_target = self.dr.find_element("variables", var_id)
		mips = [self.dr.find_element("mips", id) for id in ["link::default_400", "link::default_401",
		                                                    "link::default_403", "link::default_405",
		                                                    "link::default_406", "link::default_408",
		                                                    "link::default_409", "link::default_411",
		                                                    "link::default_414", "link::default_416"]]
		self.assertListEqual(self.dr.find_mips_per_variable(var_id), mips)
		self.assertListEqual(self.dr.find_mips_per_variable(var_name), mips)
		self.assertListEqual(self.dr.find_mips_per_variable(var_target), mips)

	def test_opportunities_per_experiment(self):
		exp_id = "link::default_294"
		exp_name = "Initialised prediction (2025-2036)"
		exp_target = self.dr.find_element("experiments", exp_id)
		op = [self.dr.find_element("opportunities", id) for id in ["link::default_420", "link::default_421"]]
		self.assertListEqual(self.dr.find_opportunities_per_experiment(exp_id), op)
		self.assertListEqual(self.dr.find_opportunities_per_experiment(exp_name), op)
		self.assertListEqual(self.dr.find_opportunities_per_experiment(exp_target), op)

	def test_themes_per_experiment(self):
		exp_id = "link::default_294"
		exp_name = "Initialised prediction (2025-2036)"
		exp_target = self.dr.find_element("experiments", exp_id)
		themes = [self.dr.find_element("data_request_themes", id) for id in ["link::default_116", "link::default_117",
		                                                                     "link::default_119"]]
		self.assertListEqual(self.dr.find_themes_per_experiment(exp_id), themes)
		self.assertListEqual(self.dr.find_themes_per_experiment(exp_name), themes)
		self.assertListEqual(self.dr.find_themes_per_experiment(exp_target), themes)

	def test_find_opportunities(self):
		theme_id = "link::default_115"
		exp_id = "link::default_294"
		list_all = list()
		list_any = [self.dr.find_element("opportunities", id) for id in ["link::default_418", "link::default_420",
		                                                                 "link::default_421"]]
		self.assertListEqual(self.dr.find_opportunities(operation="all", data_request_themes=theme_id,
		                                                experiments=[exp_id, ]), list_all)
		self.assertListEqual(self.dr.find_opportunities(operation="any", data_request_themes=theme_id,
		                                                experiments=[exp_id, ]), list_any)

	def test_find_experiments(self):
		op_id = "link::default_418"
		expgrp_id = ["link::default_286", "link::default_288"]
		list_all = list()
		list_any = [self.dr.find_element("experiments", id) for id in ["link::default_294", "link::default_310",
		                                                               "link::default_317"]]
		self.assertListEqual(self.dr.find_experiments(operation="all", opportunities=op_id,
		                                              experiment_groups=expgrp_id), list_all)
		self.assertListEqual(self.dr.find_experiments(operation="any", opportunities=op_id,
		                                              experiment_groups=expgrp_id), list_any)



