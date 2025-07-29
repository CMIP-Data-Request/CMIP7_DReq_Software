#!/usr/bin/env bash
# -*- coding: utf-8 -*-
set -e

coverage erase

coverage run

coverage run --parallel-mode scripts/workflow_example.py
rm -f "requested_v1.2.json" "requested_raw.json"

coverage run --parallel-mode scripts/database_transformation.py --test --export="raw" --version="v1.0"
coverage run --parallel-mode scripts/database_transformation.py --test --export="release" --version="v1.0"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="raw" --version="v1.0"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="release" --version="v1.0"
coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="raw" --version="v1.0"
coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="release" --version="v1.0"

# coverage run --parallel-mode scripts/database_transformation.py --test --export="raw" --version="v1.1"
coverage run --parallel-mode scripts/database_transformation.py --test --export="release" --version="v1.1"
# coverage run --parallel-mode scripts/workflow_example_2.py --test --export="raw" --version="v1.1"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="release" --version="v1.1"
# coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="raw" --version="v1.1"
coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="release" --version="v1.1"

coverage run --parallel-mode scripts/database_transformation.py --test --export="raw" --version="v1.2"
coverage run --parallel-mode scripts/database_transformation.py --test --export="release" --version="v1.2"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="raw" --version="v1.2"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="release" --version="v1.2"
coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="raw" --version="v1.2"
coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="release" --version="v1.2"

coverage run --parallel-mode scripts/database_transformation.py --test --export="raw" --version="v1.2.1"
coverage run --parallel-mode scripts/database_transformation.py --test --export="release" --version="v1.2.1"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="raw" --version="v1.2.1"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="release" --version="v1.2.1"
coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="raw" --version="v1.2.1"
coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="release" --version="v1.2.1"

coverage run --parallel-mode scripts/database_transformation.py --test --export="raw" --version="v1.2.2rc"
coverage run --parallel-mode scripts/database_transformation.py --test --export="release" --version="v1.2.2rc"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="raw" --version="v1.2.2rc"
coverage run --parallel-mode scripts/workflow_example_2.py --test --export="release" --version="v1.2.2rc"
coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="raw" --version="v1.2.2rc"
coverage run --parallel-mode scripts/check_variables_attributes.py --test --export="release" --version="v1.2.2rc"

coverage combine

coverage html
