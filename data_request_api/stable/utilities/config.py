#!/usr/bin/env python


from pathlib import Path

import yaml

# Config file location in the user's home directory
PACKAGE_NAME = "CMIP7_data_request_api"
CONFIG_FILE = Path.home() / f".{PACKAGE_NAME}_config"

# Default config dictionary
DEFAULT_CONFIG = {
    "offline": False,
    "export": "release",
    "consolidate": False,
    "log_level": "info",
    "log_file": "default",
    "cache_dir": str(Path.home() / f".{PACKAGE_NAME}_cache"),
}

# Valid types and values for each key
DEFAULT_CONFIG_TYPES = {
    "offline": bool,
    "export": str,
    "consolidate": bool,
    "log_level": str,
    "log_file": str,
    "cache_dir": str,
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
        raise TypeError(f"Invalid type for config key {key}: {type(value)}")
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
            # Create the config file if it doesn't exist
            with open(CONFIG_FILE, "w") as f:
                yaml.dump(DEFAULT_CONFIG, f)
            CONFIG = DEFAULT_CONFIG.copy()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            raise

        # Read configuration must be a dict
        if not isinstance(CONFIG, dict):
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
