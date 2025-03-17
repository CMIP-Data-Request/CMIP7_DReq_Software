#!/usr/bin/env bash
# -*- coding: utf-8 -*-

coverage erase

coverage run
# To be moved before once tests are fixed
set -e
# coverage run --parallel-mode scripts/database_transformation.py --output_dir="test" --dreq_export_version="raw"
coverage run --parallel-mode scripts/database_transformation.py --output_dir="test" --dreq_export_version="release"
coverage run --parallel-mode scripts/workflow_example.py
rm -f "requested_v1.0.json" "requested_raw.json"
# coverage run --parallel-mode scripts/workflow_example_2.py --output_dir="test" --dreq_export_version="raw"
coverage run --parallel-mode scripts/workflow_example_2.py --output_dir="test" --dreq_export_version="release"

coverage combine

coverage html
