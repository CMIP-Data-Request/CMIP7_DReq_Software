#!/usr/bin/env bash
# -*- coding: utf-8 -*-

coverage erase

coverage run
# To be moved before once tests are fixed
set -e
coverage run --parallel-mode scripts/workflow_example.py
rm -f "requested_v1.1.json" "requested_raw.json"
coverage run --parallel-mode scripts/database_transformation.py --test --export="raw" --version="v1.0"
coverage run --parallel-mode scripts/database_transformation.py --test --export="release" --version="v1.0"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="raw" --version="v1.0"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="release" --version="v1.0"
coverage run --parallel-mode scripts/database_transformation.py --test --export="raw" --version="v1.1"
coverage run --parallel-mode scripts/database_transformation.py --test --export="release" --version="v1.1"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="raw" --version="v1.1"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="release" --version="v1.1"

coverage combine

coverage html
