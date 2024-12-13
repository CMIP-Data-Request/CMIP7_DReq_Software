#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test vocabulary_server.py
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import copy
import unittest
import sys


sys.path.append('../data_request_api/stable/transform')


from vocabulary_server import VSObject, Experiment, Variable, VocabularyServer


class TestVSObject(unittest.TestCase):

	def setUp(self):
		self.vs = VocabularyServer.from_input("test_datasets/VS_output.json")
		self.obj_str = "VSObject: my_id"

	def test_init(self):
		with self.assertRaises(TypeError):
			VSObject()

		with self.assertRaises(TypeError):
			VSObject("my_id")

		with self.assertRaises(TypeError):
			VSObject(self.vs)

		obj = VSObject("my_id", self.vs)
		obj = VSObject(id="my_id", vs=self.vs)

	def test_properties(self):
		obj = VSObject(id="my_id", vs=self.vs)
		self.assertEqual(obj.id, "my_id")

	def test_buildins(self):
		obj = VSObject(id="my_id", vs=self.vs)
		self.assertEqual(str(obj), self.obj_str)
		self.assertEqual(repr(obj), self.obj_str)
		self.assertEqual(hash(obj), hash("my_id"))
		self.assertEqual(obj.get("id"), "my_id")

		obj2 = VSObject(id="other", vs=self.vs)
		self.assertNotEqual(obj, obj2)
		self.assertGreater(obj2, obj)
		self.assertLess(obj, obj2)
		self.assertEqual(obj2.get("id"), "other")

	def test_print_content(self):
		obj = VSObject(id="my_id", vs=self.vs)
		self.assertEqual(obj.print_content(), [self.obj_str, ])
		self.assertEqual(obj.print_content(level=0), [self.obj_str, ])
		self.assertEqual(obj.print_content(add_content=False), [self.obj_str, ])
		self.assertEqual(obj.print_content(level=1), ["    " + self.obj_str, ])

	def test_get_value_from_vs(self):
		# TODO: Implement this test
		pass


class TestExperiment(unittest.TestCase):

	def setUp(self):
		self.vs = VocabularyServer.from_input("test_datasets/VS_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			Experiment()

		with self.assertRaises(TypeError):
			Experiment("my_id")

		with self.assertRaises(TypeError):
			Experiment(vs=self.vs)

		with self.assertRaises(TypeError):
			Experiment(id="my_id", vs=self.vs)

		exp = Experiment(id="my_id", vs=self.vs, name="my_name")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			Experiment.from_input()

		with self.assertRaises(TypeError):
			Experiment.from_input(id="my_id")

		with self.assertRaises(TypeError):
			Experiment.from_input(name="my_name")

		with self.assertRaises(TypeError):
			Experiment.from_input(vs=self.vs)

		with self.assertRaises(TypeError):
			Experiment.from_input(id="my_id", vs=self.vs, name="my_name")

		exp = Experiment.from_input(id="my_id", vs=self.vs, input_dict=dict(name="my_name"))

	def test_properties(self):
		exp = Experiment(id="my_id", vs=self.vs, name="my_name")
		self.assertEqual(exp.name, "my_name")

	def test_print_content(self):
		exp = Experiment(id="my_id", vs=self.vs, name="my_name")
		exp_str = "experiment my_name (id: my_id)"
		self.assertEqual(exp.print_content(), [exp_str, ])
		self.assertEqual(exp.print_content(level=0), [exp_str, ])
		self.assertEqual(exp.print_content(add_content=False), [exp_str, ])
		self.assertEqual(exp.print_content(level=1), ["    " + exp_str, ])


class TestVariable(unittest.TestCase):
	def setUp(self):
		self.vs = VocabularyServer.from_input("test_datasets/VS_output.json")

	def test_init(self):
		with self.assertRaises(TypeError):
			Variable()

		with self.assertRaises(TypeError):
			Variable("my_id")

		with self.assertRaises(TypeError):
			Variable(vs=self.vs)

		var = Variable(id="my_id", vs=self.vs, name="my_name")

	def test_from_input(self):
		with self.assertRaises(TypeError):
			Variable.from_input()

		with self.assertRaises(TypeError):
			Variable.from_input(id="my_id")

		with self.assertRaises(TypeError):
			Variable.from_input(name="my_name")

		with self.assertRaises(TypeError):
			Variable.from_input(vs=self.vs)

		with self.assertRaises(TypeError):
			Variable.from_input(id="my_id", vs=self.vs, name="my_name")

		var = Variable.from_input(id="my_id", vs=self.vs,
		                          input_dict={"name": "my_name", "type": "test"})
		self.assertEqual(var.content_type, "test")
		self.assertEqual(var.name, "my_name")

	def test_properties(self):
		test_var_dict = {"cell_measures": ["link::default_4"],
		                 "cell_methods": ["link::CellMethods::amse-tmn"],
		                 "cmip7_frequency": ["link::default_113"],
		                 "description": "Prognostic z-ward velocity component resolved by the model.\n",
		                 "esm-bcv_1.3": ["link::default_240"],
		                 "modelling_realm": ["link::default_422"],
		                 "name": "Omon.wo",
		                 "physical_parameter": ["link::d476e6113f5c466d27fd3aa9e9c35411"],
		                 "processing_note": "Report on native horizontal grid. Online mapping to depth/pressure "
		                                    "vertical grid if depth or pressure are not native. Those who wish to "
		                                    "record vertical velocities and vertical fluxes on ocean half-levels may do"
		                                    " so. If using CMOR3 you will be required to specify artificial bounds "
		                                    "(e.g. located at full model levels) to avoid an error exit.\n",
		                 "provenance": "Omon ((isd.003))",
		                 "spatial_shape": ["link::a6562c2a-8883-11e5-b571-ac72891c3257"],
		                 "structure_title": ["link::default_498"],
		                 "table": ["link::MIPtable::Omon"],
		                 "temporal_shape": ["link::cf34c974-80be-11e6-97ee-ac72891c3257"],
		                 "title": "Sea Water Vertical Velocity",
		                 "type": "real"}
		test_var_dict_2 = copy.deepcopy(test_var_dict)
		del test_var_dict_2["spatial_shape"]
		del test_var_dict_2["modelling_realm"]
		var = Variable(id="my_id", vs=self.vs, **test_var_dict)
		var2 = Variable(id="my_id", vs=self.vs, **test_var_dict_2)

		self.assertEqual(var.id, "my_id")
		self.assertEqual(var2.id, "my_id")

		self.assertEqual(var.uid, "my_id")
		self.assertEqual(var2.uid, "my_id")

		self.assertEqual(var.cf_standard_name["name"], "upward_sea_water_velocity")
		self.assertEqual(var2.cf_standard_name["name"], "upward_sea_water_velocity")

		self.assertEqual(var.cell_measures, [{'name': 'area: areacello volume: volcello'}, ])
		self.assertEqual(var2.cell_measures, [{'name': 'area: areacello volume: volcello'}, ])

		self.assertEqual(var.cell_methods, [{'brand_id': 'sea', 'cell_methods': 'area: mean where sea time: mean',
		                                     'name': 'amse-tmn', 'regex': 1, 'title': 'Time Mean over Sea'}, ])
		self.assertEqual(var2.cell_methods, [{'brand_id': 'sea', 'cell_methods': 'area: mean where sea time: mean',
		                                     'name': 'amse-tmn', 'regex': 1, 'title': 'Time Mean over Sea'}, ])

		self.assertEqual(var.name, "Omon.wo")
		self.assertEqual(var2.name, "Omon.wo")

		self.assertEqual(var.content_type, "real")
		self.assertEqual(var2.content_type, "real")

		self.assertEqual(var.description, "Prognostic z-ward velocity component resolved by the model.\n")
		self.assertEqual(var2.description, "Prognostic z-ward velocity component resolved by the model.\n")

		self.assertEqual(var.frequency, {'description': 'monthly mean samples', 'name': 'mon', 'sampling_rate': 120}, )
		self.assertEqual(var2.frequency, {'description': 'monthly mean samples', 'name': 'mon', 'sampling_rate': 120}, )

		self.assertEqual(var.modelling_realm, [{'id': 'ocean', 'name': 'Ocean', 'other_name': 'Ocean'}])
		self.assertEqual(var2.modelling_realm, ["???", ])

		self.assertEqual(var.physical_parameter, {
            "cf_standard_name": ["link::default_99"],
            "description": "A velocity is a vector quantity. \"Upward\" indicates a vector component which is positive"
                           " when directed upward (negative downward).\n",
            "name": "wo",
            "provenance": "SPECS_Omon",
            "title": "Sea Water Vertical Velocity",
            "units": "m s-1"
        })
		self.assertEqual(var2.physical_parameter, {
            "cf_standard_name": ["link::default_99"],
            "description": "A velocity is a vector quantity. \"Upward\" indicates a vector component which is positive"
                           " when directed upward (negative downward).\n",
            "name": "wo",
            "provenance": "SPECS_Omon",
            "title": "Sea Water Vertical Velocity",
            "units": "m s-1"
        })

		self.assertEqual(var.spatial_shape, [{
            "level_flag": "False",
            "name": "XY-O",
            "title": "Global ocean field on model levels",
        }, ])
		self.assertEqual(var2.spatial_shape, ["???", ])

		self.assertEqual(var.structure_title, {
            "cell_measures": "area: areacello volume: volcello",
            "cell_methods": [
                "link::CellMethods::amse-tmn"
            ],
            "cmip6_title": "Temporal mean, Global ocean field on model levels [XY-O] [tmean]",
            "name": "str-157",
            "spatial_shape": [
                "link::a6562c2a-8883-11e5-b571-ac72891c3257"
            ],
            "summary": "Structure",
            "temporal_shape": [
                "link::cf34c974-80be-11e6-97ee-ac72891c3257"
            ],
            "title": "Temporal mean, Global ocean field on model levels [XY-O] [tmean]"
        })
		self.assertEqual(var2.structure_title, {
            "cell_measures": "area: areacello volume: volcello",
            "cell_methods": [
                "link::CellMethods::amse-tmn"
            ],
            "cmip6_title": "Temporal mean, Global ocean field on model levels [XY-O] [tmean]",
            "name": "str-157",
            "spatial_shape": [
                "link::a6562c2a-8883-11e5-b571-ac72891c3257"
            ],
            "summary": "Structure",
            "temporal_shape": [
                "link::cf34c974-80be-11e6-97ee-ac72891c3257"
            ],
            "title": "Temporal mean, Global ocean field on model levels [XY-O] [tmean]"
        })

		self.assertEqual(var.table, [{'alternative_label': 'Omon', 'cmip7_frequency': ['link::default_113'],
		                              'name': 'Omon', 'new_names': ['Omon'], 'title': 'Monthly ocean data'}, ])
		self.assertEqual(var2.table, [{'alternative_label': 'Omon', 'cmip7_frequency': ['link::default_113'],
		                               'name': 'Omon', 'new_names': ['Omon'], 'title': 'Monthly ocean data'}, ])

		self.assertEqual(var.temporal_shape, [{'brand': 'tavg', 'dimensions': ['link::dim:time', ], 'name': 'time-mean',
		                                       'title': 'Temporal mean',
		                                       'variables_comments': ['link::default_536', 'link::default_555']}, ])
		self.assertEqual(var2.temporal_shape, [{'brand': 'tavg','dimensions': ['link::dim:time', ], 'name': 'time-mean',
		                                        'title': 'Temporal mean',
		                                       'variables_comments': ['link::default_536', 'link::default_555']}, ])

		self.assertEqual(var.title, "Sea Water Vertical Velocity")
		self.assertEqual(var2.title, "Sea Water Vertical Velocity")

	def test_print_content(self):
		var = Variable(id="my_id", vs=self.vs, physical_parameter="link::d476e6113f5c466d27fd3aa9e9c35411",
		               cmip7_frequency="link::default_110", title="my_title")
		var_str = "variable wo at frequency day (id: my_id, title: my_title)"
		self.assertEqual(var.print_content(), [var_str, ])
		self.assertEqual(var.print_content(level=0), [var_str, ])
		self.assertEqual(var.print_content(add_content=False), [var_str, ])
		self.assertEqual(var.print_content(level=1), ["    " + var_str, ])


class TestVocabularyServer(unittest.TestCase):
	# TODO: Implement tests for Vocabulary Server
	pass
