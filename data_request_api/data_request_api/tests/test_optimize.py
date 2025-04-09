#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test data_request.py
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import os.path
import re
import sys
import tempfile
import unittest
import cProfile
import codecs
import io
import pstats

from data_request_api.query.data_request import DataRequest
from data_request_api.content.dreq_content import _dreq_res
from data_request_api.utilities.tools import read_json_input_file_content
from data_request_api.content.dump_transformation import correct_dictionaries, transform_content_inner, \
    get_transformed_content, get_transform_settings
from data_request_api.tests import filepath


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
            test_name = re.sub(r"(?P<name>.*) .*", r"\g<name>", test_name)
            file_name = filepath(f"profiling_{test_name}.txt")
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
        self.profiling = True
        self.version = "v1.1"
        export_version = "release"
        content = get_transformed_content(version=self.version, export=export_version)
        self.vs_dict = content["VS_input"]
        self.input_database = content["DR_input"]
        self.single = f"{_dreq_res}/{self.version}/dreq_{export_version}_export.json"
        self.single_content = read_json_input_file_content(self.single)
        self.single_format = correct_dictionaries(self.single_content)

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
        content = transform_content_inner(self.single_format, get_transform_settings(self.version))

    @unittest.skip
    @add_profiling
    def test_filter_variables(self):
        DR = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_dict)
        content = DR.find_variables(operation="all", skip_if_missing=False, max_priority_level="Core")

    @unittest.skip
    @add_profiling
    def test_export_summary(self):
        DR = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_dict)
        with tempfile.TemporaryDirectory() as output_dir:
            DR.find_variables_per_opportunity(DR.get_opportunities()[0])
            DR.export_summary("variables", "opportunities", os.sep.join([output_dir, "var_per_op.csv"]))
            DR.export_summary("variables", "experiments", os.sep.join([output_dir, "var_per_exp.csv"]))
            DR.export_summary("variables", "experiments", os.sep.join([output_dir, "var_per_exp_prio1.csv"]),
                              filtering_requests=dict(max_priority_level="Core"))

    @unittest.skip
    @add_profiling
    def test_export_data(self):
        DR = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_dict)
        with tempfile.TemporaryDirectory() as output_dir:
            DR.export_data("opportunities", os.sep.join([output_dir, "op.csv"]),
                           export_columns_request=["name", "lead_theme", "description"])
