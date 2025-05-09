import pytest

from data_request_api.utilities.decorators import (
    append_kwargs_from_config,
)
from data_request_api.utilities.logger import (
    change_log_file,
    change_log_level,
)

# Configure logger for testing
change_log_file(default=True)
change_log_level("info")


def test_append_kwargs_from_config(monkeypatch):
    # Mock the load_config function to return a config dictionary
    config = {"key1": "value1", "key2": "value2"}

    def mock_load_config():
        return config

    def mock_sanity_check(key, value):
        return

    monkeypatch.setattr(
        "data_request_api.utilities.config.load_config", mock_load_config
    )
    monkeypatch.setattr(
        "data_request_api.utilities.decorators._sanity_check", mock_sanity_check
    )

    # Set up a test function with the decorator
    @append_kwargs_from_config
    def test_function(**kwargs):
        return kwargs

    # Call the decorated function with no kwargs
    result = test_function()
    assert result == config

    # Call the decorated function with some kwargs
    result = test_function(key3="value3")
    assert result == {"key1": "value1", "key2": "value2", "key3": "value3"}

    # Call the decorated function with a kwarg that overrides a config value
    result = test_function(key1="override_value")
    assert result == {"key1": "override_value", "key2": "value2"}


def test_append_kwargs_from_config_args(monkeypatch, recwarn):
    # Mock the load_config function to return a config dictionary
    config = {
        "cache_dir": "value1",
        "consolidate": True,
        "offline": True,
        "export": "raw",
        "log_level": "info",
        "log_file": "default",
    }

    def mock_load_config():
        return config

    monkeypatch.setattr(
        "data_request_api.utilities.config.load_config", mock_load_config
    )

    # Set up a test function with the decorator that has
    # parameters with the same name as config keys
    @append_kwargs_from_config
    def test_function(
        arg1, arg2, offline, arg4="value4", export="value5", **kwargs
    ):
        return locals()

    # Make sure that:
    # 1) A warning is issued for specifying a config-key as function parameter name incl. default value
    # 2) Function parameters that are also kwargs are kept as function parameters
    # 2.1) They keep the value as passed to the function
    # 2.2) Default values are overridden by the config dictionary
    # 3) kwargs are set as expected
    # 3.1) kwargs are sanity-checked
    # 3.2) non-config kwargs are left untouched

    # 1st test case
    result = test_function("a", "b", False)
    config_mod = {
        i: config[i] for i in config if i not in ["offline", "export"]
    }
    result_dict = {
        "arg1": "a",
        "arg2": "b",
        "offline": False,
        "arg4": "value4",
        "export": "raw",
        "kwargs": config_mod,
    }
    assert len(recwarn.list) == 1
    assert str(recwarn.list[0].message).startswith(
        "Parameter 'export' of function "
    )
    assert result == result_dict

    # 2nd test case
    result = test_function(0, 1, False, "value", "release", log_level="warning")
    assert result == {
        "arg1": 0,
        "arg2": 1,
        "offline": False,
        "arg4": "value",
        "export": "release",
        "kwargs": {**config_mod, "log_level": "warning"},
    }

    # 3rd test case
    #  ensure that _sanity_check raises an error
    #  for an illegal type/value of a function argument
    #  that is also a config-key
    with pytest.raises(TypeError):
        result = test_function("a", "b", "c")

    # Ensure that _sanity_check raises an error for
    #  the illegal value of config-key 'loglevel' despite it
    #  being not a function argument
    with pytest.raises(ValueError):
        result = test_function("a", "b", False, export="release", log_level="release")

    # Ensure a kwarg that is not part of
    #  the config dictionary is left untouched
    result = test_function(0, 1, False, "value", "release", somekwarg="somevalue")
    assert result == {
        "arg1": 0,
        "arg2": 1,
        "offline": False,
        "arg4": "value",
        "export": "release",
        "kwargs": {**config_mod, "somekwarg": "somevalue"},
    }
