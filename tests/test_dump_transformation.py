#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test dump_transformation.py
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import copy
import unittest
import sys


sys.path.append("sandbox/GR")

from tools import read_json_file, write_json_output_file_content
from dump_transformation import correct_key_string, correct_dictionaries, transform_content_one_base,\
	transform_content_three_bases, transform_content


class CorrectKeyString(unittest.TestCase):
	def test_correct(self):
		self.assertEquals(correct_key_string("  This is a test & some specific chars. "),
		                  "this_is_a_test_and_some_specific_chars.")
		self.assertEquals(correct_key_string("A string with elements to remove. DumMy test", "dummy", "Test"),
		                  "a_string_with_elements_to_remove.")

	def test_error(self):
		with self.assertRaises(TypeError):
			correct_key_string(4)

		with self.assertRaises(TypeError):
			correct_key_string(["dummy", "test"])

		with self.assertRaises(TypeError):
			correct_key_string(dict(test="dummy"))


class CorrectDictionaries(unittest.TestCase):
	def test_correct(self):
		dict_1 = {"Test1": "dummy1", "&test2": "Dummy2&"}
		new_dict_1 = {"test1": "dummy1", "andtest2": "Dummy2&"}
		self.assertDictEqual(correct_dictionaries(dict_1), new_dict_1)

		dict_2 = {
			"test&1": ["dummy1", "DuMmy2"],
			"TesT 2": {
				"record&1": {"test 1": "Test2"},
				"Record2": {"dummy_1": "&dummy2"},
				"record3": {
					"test 1": "dummy&",
					"&tesT2": "Dummy2"
				}
			},
			"test3 ": 4
		}
		new_dict_2 = {
			"testand1": ["dummy1", "DuMmy2"],
			"test_2": {
				"record&1": {"test_1": "Test2"},
				"Record2": {"dummy_1": "&dummy2"},
				"record3": {
					"test_1": "dummy&",
					"andtest2": "Dummy2"
				}
			},
			"test3": 4
		}
		self.assertDictEqual(correct_dictionaries(dict_2), new_dict_2)

	def test_error(self):
		with self.assertRaises(TypeError):
			correct_dictionaries(4)

		with self.assertRaises(TypeError):
			correct_dictionaries(["dummy", "test"])

		with self.assertRaises(TypeError):
			correct_dictionaries("test")


class TransformContent(unittest.TestCase):
	def setUp(self):
		self.input_one_base = read_json_file("tests/test_datasets/one_base_input.json")
		# self.input_several_bases = read_json_file("tests/test_datasets/several_bases_input.json")
		self.VS_output_noformat = read_json_file("tests/test_datasets/VS_input_noformat.json")
		self.DR_output = read_json_file("tests/test_datasets/DR_input.json")
		self.version = "test"
		self.DR_output_complete = copy.deepcopy(self.DR_output)
		self.DR_output_complete["version"] = self.version
		self.VS_output = read_json_file("tests/test_datasets/VS_input.json")
		self.VS_output_complete = copy.deepcopy(self.VS_output)
		self.VS_output_complete["version"] = self.version

	def test_one_base_correct(self):
		DR_output, VS_output = transform_content_one_base(self.input_one_base)
		write_json_output_file_content("DR_output.json", DR_output)
		write_json_output_file_content("VS_output.json", VS_output)
		self.assertDictEqual(DR_output, self.DR_output)
		self.assertDictEqual(VS_output, self.VS_output_noformat)

	@unittest.expectedFailure
	def test_one_base_error(self):
		with self.assertRaises(ValueError):
			transform_content_one_base(self.input_several_bases)

		with self.assertRaises(TypeError):
			transform_content_one_base(["dummy", "test"])

	@unittest.expectedFailure
	def test_several_bases_correct(self):
		DR_output, VS_output = transform_content_three_bases(self.input_several_bases)
		self.assertDictEqual(DR_output, self.DR_output)
		self.assertDictEqual(VS_output, self.VS_output_noformat)

	@unittest.expectedFailure
	def test_several_bases_error(self):
		with self.assertRaises(ValueError):
			transform_content_three_bases(self.input_one_base)

		with self.assertRaises(TypeError):
			transform_content_three_bases(["dummy", "test"])

	def test_all_correct_from_one(self):
		DR_output, VS_output = transform_content(self.input_one_base, version=self.version)
		self.assertDictEqual(DR_output, self.DR_output_complete)
		self.assertDictEqual(VS_output, self.VS_output_complete)

	@unittest.expectedFailure
	def test_all_correct_from_several(self):
		DR_output, VS_output = transform_content(self.input_several_bases, version=self.version)
		self.assertDictEqual(DR_output, self.DR_output_complete)
		self.assertDictEqual(VS_output, self.VS_output_complete)

	def test_all_error(self):
		with self.assertRaises(TypeError):
			transform_content(self.input_one_base)

		with self.assertRaises(TypeError):
			transform_content(["dummy", "test"], version="test")

		with self.assertRaises(TypeError):
			transform_content(4, version="test")
