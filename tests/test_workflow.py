#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test workflow
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import os
import unittest
import tempfile


from data_request_api.stable.content.dreq_api import dreq_content as dc
from data_request_api.stable.query.data_request import DataRequest


class TestWorkflow1(unittest.TestCase):

	def test_workflow_raw(self):
		content = dc.load(export="raw", consolidate=False)
		DR = DataRequest.from_input(content, version="latest")
		DR.find_opportunities()
		DR.find_variables()
		DR.find_experiments()
		with tempfile.TemporaryDirectory(prefix="test_workflow_raw") as tmpdir:
			DR.export_summary("opportunities", "data_request_themes", os.sep.join([tmpdir, "op_per_th.csv"]))
			DR.export_summary("variables", "opportunities", os.sep.join([tmpdir, "var_per_op.csv"]))
			DR.export_summary("experiments", "opportunities", os.sep.join([tmpdir, "exp_per_op.csv"]))
			DR.export_summary("variables", "spatial_shape", os.sep.join([tmpdir, "var_per_spsh.csv"]))
			DR.export_data("opportunities", os.sep.join([tmpdir, "op.csv"]),
			               export_columns_request=["name", "lead_theme", "description"])

	def test_workflow_release(self):
		content = dc.load(export="release", consolidate=False)
		DR = DataRequest.from_input(content, version="latest")
		DR.find_opportunities()
		DR.find_variables()
		DR.find_experiments()
		with tempfile.TemporaryDirectory(prefix="test_workflow_raw") as tmpdir:
			DR.export_summary("opportunities", "data_request_themes", os.sep.join([tmpdir, "op_per_th.csv"]))
			DR.export_summary("variables", "opportunities", os.sep.join([tmpdir, "var_per_op.csv"]))
			DR.export_summary("experiments", "opportunities", os.sep.join([tmpdir, "exp_per_op.csv"]))
			DR.export_summary("variables", "spatial_shape", os.sep.join([tmpdir, "var_per_spsh.csv"]))
			DR.export_data("opportunities", os.sep.join([tmpdir, "op.csv"]),
			               export_columns_request=["name", "lead_theme", "description"])
