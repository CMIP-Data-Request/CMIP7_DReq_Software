#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test data_request.py
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import os.path
import re
import sys
import unittest
import cProfile
import codecs
import io
import pstats

from data_request_api.stable.query.data_request import DataRequest
from data_request_api.stable.content.dreq_api.dreq_content import _dreq_res
from data_request_api.stable.utilities.tools import read_json_input_file_content
from data_request_api.stable.content.dump_transformation import correct_dictionaries, transform_content_one_base


def add_profiling(func):
	def do_profiling(self, *args, **kwargs):
		if self.profiling:
			pr = cProfile.Profile()
			pr.enable()
		rep = func(self, *args, **kwargs)
		if self.profiling:
			pr.disable()
			stdout = sys.stdout
			test_name = str(self)
			test_name = re.sub("(?P<name>.*) .*", "\g<name>", test_name)
			file_name = f"tests/profiling_{test_name}.txt"
			if os.path.isfile(file_name):
				os.remove(file_name)
			with codecs.open(file_name, "w", encoding="utf-8") as statsfile:
				sys.stdout = statsfile
				s = io.StringIO()
				sortby = "cumulative"
				ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
				ps.print_stats()
				print(s.getvalue())
			sys.stdout = stdout
		return rep

	return do_profiling


class TestDataRequest11(unittest.TestCase):
	def setUp(self):
		self.profiling = False
		self.version = "v1.1"
		export_version = "release"
		self.single = f"{_dreq_res}/{self.version}/dreq_{export_version}_export.json"
		self.single_content = read_json_input_file_content(self.single)
		self.single_format = correct_dictionaries((self.single_content))
		self.vs_file = f"{_dreq_res}/{self.version}/VS_{export_version}_content.json"
		self.vs_dict = read_json_input_file_content(self.vs_file)
		self.input_database_file = f"{_dreq_res}/{self.version}/DR_{export_version}_content.json"
		self.input_database = read_json_input_file_content(self.input_database_file)

	@unittest.skip
	@add_profiling
	def test_from_separated_inputs(self):
		obj = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_dict)

	@unittest.skip
	@add_profiling
	def test_from_single_input(self):
		obj = DataRequest.from_input(self.single, version=self.version)

	@unittest.skip
	@add_profiling
	def test_correct_dictionaries(self):
		content = correct_dictionaries(self.single_content)

	@unittest.skip
	@add_profiling
	def test_transform_to_one(self):
		content = transform_content_one_base(self.single_format)
