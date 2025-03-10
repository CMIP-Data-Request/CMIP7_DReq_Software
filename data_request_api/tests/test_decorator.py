import pytest

from data_request_api.stable.utilities.decorators import append_kwargs_from_config


def test_append_kwargs_from_config(monkeypatch):
    # Mock the load_config function to return a config dictionary
    config = {"key1": "value1", "key2": "value2"}

    def mock_load_config():
        return config

    monkeypatch.setattr(
        "data_request_api.stable.utilities.config.load_config", mock_load_config
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
