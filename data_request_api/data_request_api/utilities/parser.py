#!/usr/bin/env python
# -*- coding: utf-8 -*-

import data_request_api.utilities.config as dreqcfg
from argparse import ArgumentTypeError


def check_bool(value):
    if isinstance(value, bool):
        return value
    elif isinstance(value, (str, int)):
        if value in ["", "0", "no", "none", "None", "False", "false", 0]:
            return False
        elif value in ["1", "yes", "True", "true", 1]:
            return True
        else:
            try:
                return bool(value)
            except ValueError:
                raise ArgumentTypeError("%s is not a boolean" % value)
    else:
        raise TypeError("Unexpected case")


def append_arguments_to_parser(parser):
    config = dreqcfg.load_config()
    for (key, value) in config.items():
        key_type = dreqcfg.DEFAULT_CONFIG_TYPES[key]
        if key_type == bool:
            key_type = check_bool
        key_help = dreqcfg.DEFAULT_CONFIG_HELP[key]
        parser.add_argument(f"--{key}", default=value, type=key_type, help=key_help)
    return parser
