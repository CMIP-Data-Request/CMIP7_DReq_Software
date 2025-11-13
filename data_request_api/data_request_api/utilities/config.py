#!/usr/bin/env python

import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import requests
import yaml

# Config file location in the user's home directory
PACKAGE_NAME = "CMIP7_data_request_api"
CONFIG_FILE = os.environ.get(
    "CMIP7_DR_API_CONFIGFILE", Path.home() / f".{PACKAGE_NAME}_config"
)

# Default config dictionary
DEFAULT_CONFIG = {
    "offline": False,
    "export": "release",
    "consolidate": True,
    "log_level": "info",
    "log_file": "default",
    "cache_dir": str(Path.home() / f".{PACKAGE_NAME}_cache"),
    "check_api_version": True,
    "variable_name": "CMIP7 Compound Name",
}

# Valid types and values for each key
DEFAULT_CONFIG_TYPES = {
    "offline": bool,
    "export": str,
    "consolidate": bool,
    "log_level": str,
    "log_file": str,
    "cache_dir": str,
    "check_api_version": bool,
    "variable_name": str,
}

# Valid types and values for each key
DEFAULT_CONFIG_HELP = {
    "offline": "Should the script be launched offline?",
    "export": "Version of the export to be used (i.e. raw or release)",
    "consolidate": "Should consolidation be done?",
    "log_level": "Log level to use",
    "log_file": "Log file to use",
    "cache_dir": "Cache directory to use",
    "check_api_version": "Check pypi for the latest API version?",
    "variable_name": "Unique identifier to use for requested variables",
}

DEFAULT_CONFIG_VALID_VALUES = {
    "export": ["release", "raw"],
    "log_level": ["debug", "info", "warning", "error", "critical"],
}

# Global variable to hold the loaded config
CONFIG = {}


def _sanity_check(key, value):
    """Validate the given config key and value."""
    if key not in DEFAULT_CONFIG:
        raise KeyError(
            f"Invalid config key: {key}. Valid keys: {sorted(list(DEFAULT_CONFIG.keys()))}"
        )
    if not isinstance(value, DEFAULT_CONFIG_TYPES[key]):
        raise TypeError(
            f"Invalid type for config key {key}: {type(value)}. Expected type {DEFAULT_CONFIG_TYPES[key]}"
        )
    if (
        key in DEFAULT_CONFIG_VALID_VALUES
        and value not in DEFAULT_CONFIG_VALID_VALUES[key]
    ):
        raise ValueError(
            f"Invalid value for config key {key}: {value}. Valid values: {DEFAULT_CONFIG_VALID_VALUES[key]}"
        )


def load_config() -> dict:
    """Load the configuration file, creating it if necessary.

    Returns:
        dict: The configuration data.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is not in the correct format.
        KeyError: If the key is not in the DEFAULT_CONFIG.
        TypeError: If the value is not of the expected type for the key.
        ValueError: If the value is not within the valid values for the key.
    """
    global CONFIG
    if CONFIG == {}:
        try:
            with open(CONFIG_FILE) as f:
                CONFIG = yaml.safe_load(f)
        except FileNotFoundError:
            pass

        # Read configuration must be a dict - if no or an empty file is read,
        #  assign DEFAULT_CONFIG
        if CONFIG == "" or CONFIG is None or CONFIG == {}:
            with open(CONFIG_FILE, "w") as f:
                yaml.dump(DEFAULT_CONFIG, f)
            CONFIG = DEFAULT_CONFIG.copy()
        elif not isinstance(CONFIG, dict):
            raise TypeError(f"Config file ('{CONFIG_FILE}') must contain a dictionary")

        # Sanity test for allowed types and values
        for key, value in CONFIG.items():
            _sanity_check(key, value)

        # Ensure all required keys are present and update config file if necessary
        missing_keys = {k: v for k, v in DEFAULT_CONFIG.items() if k not in CONFIG}
        for key, value in missing_keys.items():
            update_config(key, value)

    return CONFIG


def update_config(key, value):
    """
    Update the configuration with the specified key-value pair.

    Args:
        key (str): The configuration key to update.
        value (Any): The new value for the configuration key. Boolean-like strings
                     ("true", "false") will be converted to actual booleans.

    Raises:
        KeyError: If the key is not in the DEFAULT_CONFIG.
        TypeError: If the value is not of the expected type for the key.
        ValueError: If the value is not within the valid values for the key.

    This function updates the global configuration dictionary with the given key-value
    pair and writes the updated configuration back to the configuration file.
    """
    global CONFIG
    if CONFIG == {}:
        CONFIG = load_config()

    # Convert boolean-like strings to actual booleans
    key = str(key)
    value = str(value)
    if value.lower() in {"true", "false"}:
        value = value.lower() == "true"
    _sanity_check(key, value)

    # Overwrite / set the value
    CONFIG[key] = value

    # Write the updated config back to the file
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(CONFIG, f)

    print(f"Updated {key} to {value} in '{CONFIG_FILE}'.")


def check_api_version():
    """
    Check pypi for latest release of the software and warn user if the installed version is not the latest release.
    Intended behaviour, assuming that latest version is '1.2.2':
        installed_version = '1.2.1' ==> warn user
        installed_version = '1.2.2' ==> don't warn user
        installed_version = '1.2.1.dev8+g6aa6222.d20250515' ==> warn user
        installed_version = '1.2.2.dev8+g6aa6222.d20250515' ==> don't warn user
    """
    try:
        installed_version = version(PACKAGE_NAME)
    except PackageNotFoundError:
        print(f"{PACKAGE_NAME} is not installed.")
        return

    try:
        response = requests.get(f"https://pypi.org/pypi/{PACKAGE_NAME}/json", timeout=5)
        response.raise_for_status()
        latest_version = response.json()["info"]["version"]
    except requests.RequestException as e:
        print(f"Error checking PyPI: {e}")
        return

    if installed_version < latest_version:
        # Warn user that installed version is earlier than the latest version on pypi
        msg = f"Warning: the installed version of {PACKAGE_NAME} is not the latest version available from PyPI!\n"
        msg += f"Latest version on PyPI:  {latest_version}\n"
        msg += f"Installed version:       {installed_version}\n"
        msg += "To install the latest version from PyPI:\n"
        msg += f"  pip install --upgrade {PACKAGE_NAME}\n"
        msg += "To turn off this warning:\n"
        msg += "  CMIP7_data_request_api_config check_api_version false"
        msg = "\n" + msg + "\n"

        # Add color to the warning message
        color_code = "\033[91m"
        color_code_end = color_code.split("[")[0] + "[0m"
        msg = color_code + msg + color_code_end

        print(msg)
