#!/usr/bin/env bash
# -*- coding: utf-8 -*-

export COVERAGE_RCFILE=tests/.coveragerc

coverage erase

coverage run
# To be moved before once tests are fixed
set -e
coverage run --parallel-mode scripts/database_transformation.py --output_dir="test" --dreq_export_version="raw"
coverage run --parallel-mode scripts/database_transformation.py --output_dir="test" --dreq_export_version="release"
coverage run --parallel-mode scripts/export_dreq_lists_json.py --all_opportunities "v1.0" "result.json"
rm -f result.json
coverage run --parallel-mode scripts/workflow_example.py
rm -f "requested_v1.0.json" "requested_raw.json"
coverage run --parallel-mode scripts/workflow_example_2.py --output_dir="test" --dreq_export_version="raw"
coverage run --parallel-mode scripts/workflow_example_2.py --output_dir="test" --dreq_export_version="release"

coverage combine

coverage html
