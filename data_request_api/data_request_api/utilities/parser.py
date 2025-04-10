#!/usr/bin/env python
# -*- coding: utf-8 -*-

import data_request_api.utilities.config as dreqcfg


def append_arguments_to_parser(parser):
	config = dreqcfg.load_config()
	for (key, value) in config.items():
		parser.add_argument(f"--{key}", default=value, type=dreqcfg.DEFAULT_CONFIG_TYPES[key],
		                    help=dreqcfg.DEFAULT_CONFIG_HELP[key])
	return parser