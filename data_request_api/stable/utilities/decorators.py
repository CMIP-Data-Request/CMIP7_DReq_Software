#!/usr/bin/env python

import functools
import inspect
import warnings

import data_request_api.stable.utilities.config as dreqcfg
from data_request_api.stable.utilities.config import _sanity_check
from data_request_api.stable.utilities.logger import get_logger


def append_kwargs_from_config(func):
    """Decorator to append kwargs from a config file if not explicitly set."""

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        logger = get_logger()
        logger.debug(
            f"Function '{func.__qualname__}': Passing **kwargs from config file."
        )

        # Get function args
        sig = inspect.signature(func)
        bound_args = sig.bind_partial(*args, **kwargs)
        params = sig.parameters

        config = dreqcfg.load_config()
        for key, value in config.items():
            if key in params.keys():
                # Function parameters also configurable in the config file
                # should not have a default value as the default behaviour
                # will be defined in the config file
                if params[key].default is not inspect.Parameter.empty:
                    warnings.warn(
                        f"Parameter '{key}' of function '{func.__qualname__}'"
                        " has a default value, but this default is overridden"
                        " by the value specified in the configuration file."
                    )
                # Skip overwriting *args with the default config **kwargs
                #   but perform a sanity check first
                if key in bound_args.arguments.keys():
                    _sanity_check(key, bound_args.arguments[key])
                    continue
            # Append kwarg if not set - this assigns function args if they have the same name
            kwargs.setdefault(key, value)
        return func(*args, **kwargs)

    return decorator
