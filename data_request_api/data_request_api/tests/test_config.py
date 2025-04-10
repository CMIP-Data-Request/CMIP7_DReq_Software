from pathlib import Path

import pytest
import yaml

import data_request_api.utilities.config as dreqcfg
from data_request_api.utilities.config import (
    DEFAULT_CONFIG,
    _sanity_check,
    load_config,
    update_config,
)


@pytest.fixture(scope="function")
def temp_config_file(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("data")
    config_file = temp_dir / ".CMIP7_data_request_api_config"
    try:
        yield config_file
    finally:
        config_file.unlink(missing_ok=True)
        dreqcfg.CONFIG = {}


@pytest.fixture(scope="function")
def monkeypatch(monkeypatch):
    return monkeypatch


def test_load_config_file_exists(temp_config_file, monkeypatch):
    with open(temp_config_file, "w") as f:
        yaml.dump(DEFAULT_CONFIG, f)
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    assert temp_config_file.exists()
    dreqcfg.CONFIG = {}
    config = load_config()
    assert config == DEFAULT_CONFIG
    assert config == dreqcfg.CONFIG


def test_load_config_file_does_not_exist(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    assert not temp_config_file.exists()
    assert dreqcfg.CONFIG == {}
    config = load_config()
    assert config == DEFAULT_CONFIG
    assert temp_config_file.exists()


def test_load_config_invalid_yaml(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    with open(temp_config_file, "w") as f:
        f.write("Just a string not proper yaml")
    with pytest.raises(TypeError):
        load_config()


def test_load_config_non_dict_yaml(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    with open(temp_config_file, "w") as f:
        f.write("['list', 'instead', 'of', 'dict']")
    with pytest.raises(TypeError):
        load_config()


def test_update_config_valid_key(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    update_config("offline", True)
    with open(temp_config_file) as f:
        config = yaml.safe_load(f)
    assert config == {**DEFAULT_CONFIG, "offline": True}


def test_update_config_invalid_key(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    with pytest.raises(KeyError):
        update_config("invalid_key", True)


def test_update_config_invalid_type_or_value(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    with pytest.raises(TypeError):
        update_config("offline", "invalid_value")
    with pytest.raises(ValueError):
        update_config("export", "invalid_value")


def test_load_custom_config_file(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )

    # 1 - Illegal value
    custom_config = {"offline": True, "export": "custom"}
    with open(temp_config_file, "w") as f:
        yaml.dump(custom_config, f)
    with pytest.raises(ValueError):
        config = load_config()
    # pytest catching the ValueError allows dreqcfg.CONFIG to take a value
    #  so need to reset.
    dreqcfg.CONFIG = {}

    # 2 - Legal values
    custom_config = {"offline": True, "export": "raw"}
    with open(temp_config_file, "w") as f:
        yaml.dump(custom_config, f)
    config = load_config()
    assert config == {**DEFAULT_CONFIG, **custom_config}


def test_update_custom_config_file(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    custom_config = {"offline": True, "export": "raw"}
    with open(temp_config_file, "w") as f:
        yaml.dump(custom_config, f)
    update_config("consolidate", True)
    with open(temp_config_file) as f:
        config = yaml.safe_load(f)
    assert config == {
        **DEFAULT_CONFIG,
        "offline": True,
        "export": "raw",
        "consolidate": True,
    }


def test_update_config_update_existing_key(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    update_config("offline", True)
    assert dreqcfg.CONFIG["offline"] is True
    update_config("offline", False)
    assert dreqcfg.CONFIG["offline"] is False


def test_sanity_checks():
    with pytest.raises(KeyError):
        _sanity_check("invalid_key", "invalid_value")

    with pytest.raises(ValueError):
        _sanity_check("log_level", "invalid_value")

    with pytest.raises(TypeError):
        _sanity_check("offline", "invalid_value")

    with pytest.raises(TypeError):
        _sanity_check("offline", 1)

    _sanity_check("offline", True)
    _sanity_check("export", "raw")
    _sanity_check("consolidate", True)
    _sanity_check("log_level", "info")
    _sanity_check("log_file", "default")
    _sanity_check(
        "cache_dir", str(Path.home() / ".CMIP7_data_request_api_cache")
    )


def test_caching(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    config1 = load_config()
    config2 = load_config()
    assert config1 is config2
