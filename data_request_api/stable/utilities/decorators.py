#!/usr/bin/env python

import functools

import data_request_api.stable.utilities.config as dreqcfg


def append_kwargs_from_config(func):
    """Decorator to append kwargs from a config file if not explicitly set."""

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        config = dreqcfg.load_config()
        for key, value in config.items():
            # Append kwarg if not set
            kwargs.setdefault(key, value)
        return func(*args, **kwargs)

    return decorator
