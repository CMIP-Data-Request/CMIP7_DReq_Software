import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import data_request_api.utilities.config as dreqcfg


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


def test_init_config(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "data_request_api.command_line.config",
            "init",
            "--cfgfile",
            str(temp_config_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert str(dreqcfg.CONFIG_FILE) != str(
        Path.home() / "CMIP7_data_request_api_config"
    )
    assert os.path.isfile(dreqcfg.CONFIG_FILE)


def test_init_config_no_argument(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "data_request_api.command_line.config",
            "--cfgfile",
            str(temp_config_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert str(dreqcfg.CONFIG_FILE) != str(
        Path.home() / "CMIP7_data_request_api_config"
    )
    assert os.path.isfile(dreqcfg.CONFIG_FILE)


def test_init_config_entry_point(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    result = subprocess.run(
        [
            "CMIP7_data_request_api_config",
            "init",
            "--cfgfile",
            str(temp_config_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert str(dreqcfg.CONFIG_FILE) != str(
        Path.home() / "CMIP7_data_request_api_config"
    )
    assert os.path.isfile(dreqcfg.CONFIG_FILE)


def test_reset_config(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    dreqcfg.update_config("offline", True)
    dreqcfg.CONFIG = {}  # reset to allow reloading below
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "data_request_api.command_line.config",
            "reset",
            "--cfgfile",
            str(temp_config_file),
        ],
        capture_output=True,
        text=True,
    )
    assert "Updated offline to False" in result.stdout
    assert result.returncode == 0
    config = dreqcfg.load_config()
    assert config == dreqcfg.DEFAULT_CONFIG


def test_update_config(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "data_request_api.command_line.config",
            "offline",
            "true",
            "--cfgfile",
            str(temp_config_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Updated offline to True" in result.stdout
    config = dreqcfg.load_config()
    assert config["offline"] is True


def test_invalid_command(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "data_request_api.command_line.config",
            "invalid",
            "--cfgfile",
            str(temp_config_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (
        "usage: python -m data_request_api.command_line.config <arguments>"
        in result.stdout
    )


def test_invalid_command_entry_point(temp_config_file, monkeypatch):
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    result = subprocess.run(
        [
            "CMIP7_data_request_api_config",
            "invalid",
            "--cfgfile",
            str(temp_config_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "usage: CMIP7_data_request_api_config <arguments>" in result.stdout


def test_config_file_from_env_var(temp_config_file, monkeypatch):
    # Set the CMIP7_DR_API_CONFIGFILE environment variable
    monkeypatch.setenv("CMIP7_DR_API_CONFIGFILE", str(temp_config_file))

    # Run your test as usual
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "data_request_api.command_line.config",
            "init",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert temp_config_file.exists()
    with open(temp_config_file) as f:
        config = yaml.safe_load(f)
    assert config == dreqcfg.DEFAULT_CONFIG
