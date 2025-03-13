#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test dump_transformation.py
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import copy
import os
import unittest

from data_request_api.stable.utilities.tools import read_json_file, write_json_output_file_content
from data_request_api.stable.content.dump_transformation import correct_key_string, correct_dictionaries, \
    transform_content_one_base, transform_content_three_bases, transform_content, split_content_one_base
from data_request_api.tests import filepath


class TestCorrectKeyString(unittest.TestCase):
    def test_correct(self):
        self.assertEqual(correct_key_string("  This is a test & some specific chars. "),
                         "this_is_a_test_and_some_specific_chars.")
        self.assertEqual(correct_key_string("A string with elements to remove. DumMy test", "dummy", "Test"),
                         "a_string_with_elements_to_remove.")

    def test_error(self):
        with self.assertRaises(TypeError):
            correct_key_string(4)

        with self.assertRaises(TypeError):
            correct_key_string(["dummy", "test"])

        with self.assertRaises(TypeError):
            correct_key_string(dict(test="dummy"))


class TestCorrectDictionaries(unittest.TestCase):
    def test_correct(self):
        dict_1 = {"Test1": "dummy1", "&test2": "Dummy2&"}
        new_dict_1 = {"test1": "dummy1", "andtest2": "Dummy2&"}
        self.assertDictEqual(correct_dictionaries(dict_1), new_dict_1)

        dict_2 = {
            "test&1": ["dummy1", "DuMmy2"],
            "TesT 2": {
                "record&1": {"test 1": "Test2"},
                "Record2": {"dummy_1": "&dummy2"},
                "records": {
                    "test 1": "dummy&",
                    "&tesT2": "Dummy2"
                }
            },
            "test3 ": 4
        }
        new_dict_2 = {
            "testand1": ["dummy1", "DuMmy2"],
            "test_2": {
                "recordand1": {"test_1": "Test2"},
                "record2": {"dummy_1": "&dummy2"},
                "records": {
                    "test 1": "dummy&",
                    "&tesT2": "Dummy2"
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


class TestTransformContent(unittest.TestCase):
    def setUp(self):
        self.version = "test"
        self.one_base_input = read_json_file(filepath("one_base_input.json"))
        self.one_base_output_format = read_json_file(
            filepath("one_base_output_format.json"))
        self.one_base_output_transform = read_json_file(
            filepath("one_base_output_transform.json"))
        self.one_base_VS_output = read_json_file(
            filepath("one_base_VS_output.json"))
        self.one_base_DR_output = read_json_file(
            filepath("one_base_DR_output.json"))
        self.one_base_VS_output_noversion = copy.deepcopy(
            self.one_base_VS_output)
        del self.one_base_VS_output_noversion["version"]
        self.one_base_DR_output_noversion = copy.deepcopy(
            self.one_base_DR_output)
        del self.one_base_DR_output_noversion["version"]
        self.several_bases_input = read_json_file(
            filepath("several_bases_input.json"))
        self.several_bases_output_transform_to_one = read_json_file(
            filepath("several_bases_output_transform_to_one.json"))
        self.several_bases_output_format = read_json_file(
            filepath("several_bases_output_format.json"))
        self.several_bases_output_transform = read_json_file(
            filepath("several_bases_output_transform.json"))
        self.several_bases_VS_output = read_json_file(
            filepath("several_bases_VS_output.json"))
        self.several_bases_DR_output = read_json_file(
            filepath("several_bases_DR_output.json"))
        self.several_bases_VS_output_noversion = copy.deepcopy(
            self.several_bases_VS_output)
        del self.several_bases_VS_output_noversion["version"]
        self.several_bases_DR_output_noversion = copy.deepcopy(
            self.several_bases_DR_output)
        del self.several_bases_DR_output_noversion["version"]

    def test_one_base_correct(self):
        format_output = correct_dictionaries(self.one_base_input)
        self.assertDictEqual(format_output, self.one_base_output_format)
        transform_output = transform_content_one_base(format_output)
        self.assertDictEqual(transform_output, self.one_base_output_transform)
        DR_output, VS_output = split_content_one_base(transform_output)
        self.assertDictEqual(DR_output, self.one_base_DR_output_noversion)
        self.assertDictEqual(VS_output, self.one_base_VS_output_noversion)

    def test_all_correct_from_one(self):
        DR_output, VS_output = transform_content(
            self.one_base_input, version=self.version)
        self.assertDictEqual(DR_output, self.one_base_DR_output)
        self.assertDictEqual(VS_output, self.one_base_VS_output)

    def test_several_bases_correct(self):
        transform_input = transform_content_three_bases(
            self.several_bases_input)
        self.assertDictEqual(
            transform_input, self.several_bases_output_transform_to_one)
        format_output = correct_dictionaries(transform_input)
        self.assertDictEqual(format_output, self.several_bases_output_format)
        transform_output = transform_content_one_base(format_output)
        self.assertDictEqual(
            transform_output, self.several_bases_output_transform)
        DR_output, VS_output = split_content_one_base(transform_output)
        self.assertDictEqual(DR_output, self.several_bases_DR_output_noversion)
        self.assertDictEqual(VS_output, self.several_bases_VS_output_noversion)

    def test_all_correct_from_several(self):
        DR_output, VS_output = transform_content(
            self.several_bases_input, version=self.version)
        self.assertDictEqual(DR_output, self.several_bases_DR_output)
        self.assertDictEqual(VS_output, self.several_bases_VS_output)

    def test_one_base_error(self):
        with self.assertRaises(ValueError):
            transform_content_one_base(self.several_bases_input)

        with self.assertRaises(TypeError):
            transform_content_one_base(["dummy", "test"])

    def test_several_bases_error(self):
        with self.assertRaises(ValueError):
            transform_content_three_bases(self.one_base_input)

        with self.assertRaises(TypeError):
            transform_content_three_bases(["dummy", "test"])

    def test_all_error(self):
        with self.assertRaises(TypeError):
            transform_content(self.one_base_input)

        with self.assertRaises(TypeError):
            transform_content(["dummy", "test"], version="test")

        with self.assertRaises(TypeError):
            transform_content(4, version="test")
