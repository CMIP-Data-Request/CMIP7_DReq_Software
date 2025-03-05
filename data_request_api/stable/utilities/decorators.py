#!/usr/bin/env python


import functools

from data_request_api.stable.utilities.config import load_config


def append_kwargs_from_config(func):
    """Decorator to append kwargs from a config file if not explicitly set."""

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        for key, value in load_config().items():
            # Append kwarg if not set
            kwargs.setdefault(key, value)
        return func(*args, **kwargs)

    return decorator
