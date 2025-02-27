#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test data_request.py
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import unittest

from data_request_api.stable.query.data_request import DataRequest
from data_request_api.stable.content.dreq_api.dreq_content import _dreq_res
from data_request_api.stable.utilities.tools import read_json_input_file_content


class TestDataRequest11(unittest.TestCase):
	def setUp(self):
		self.version = "v1.1"
		export_version = "release"
		self.single = f"{_dreq_res}/{self.version}/dreq_{export_version}_export.json"
		self.vs_file = f"{_dreq_res}/{self.version}/VS_{export_version}_content.json"
		self.vs_dict = read_json_input_file_content(self.vs_file)
		self.input_database_file = f"{_dreq_res}/{self.version}/DR_{export_version}_content.json"
		self.input_database = read_json_input_file_content(self.input_database_file)

	def test_from_separated_inputs(self):
		obj = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_dict)

	def test_from_single_input(self):
		obj = DataRequest.from_input(self.single, version=self.version)
