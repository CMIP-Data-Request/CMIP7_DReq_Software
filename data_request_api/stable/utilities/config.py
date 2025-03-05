#!/usr/bin/env python


import sys
from pathlib import Path

import yaml

# Config file location in the user's home directory
PACKAGE_NAME = "CMIP7_data_request_api"
CONFIG_FILE = Path.home() / f".{PACKAGE_NAME}_config"

# Default config values
DEFAULT_CONFIG = {
    "offline": False,
    "export": "release",
    "consolidate": False,
    "log_level": "info",
    "log_file": "default",
}


def load_config():
    """Load the configuration file, creating it if necessary."""
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(DEFAULT_CONFIG, f)

    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f) or {}


def update_config(key, value):
    """Update a specific key in the config file."""
    config = load_config()

    key = str(key)
    if key not in DEFAULT_CONFIG:
        print(f"Error: '{key}' is not a valid config key.")
        print(f"Valid keys: {list(DEFAULT_CONFIG.keys())}")
        sys.exit(1)

    # Convert boolean-like strings to actual booleans
    value = str(value)
    if value.lower() in {"true", "false"}:
        value = value.lower() == "true"

    config[key] = value

    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f)

    print(f"Updated {key} to {value} in {CONFIG_FILE}")


def _print_usage():
    print("Usage: python -m utilities.config <arguments>")
    print()
    print("Arguments:")
    print("  init (or no arguments): Initialize the config file,")
    print("      i.e. create a config file with default values if it does not exist.")
    print("  reset: Reset the config file to default values.")
    print("  <key> <value>: Update a specific key in the config file.")
    print()
    print("Examples: python -m utilities.config offline true")
    print("          python -m utilities.config reset")


# CLI
def main():
    if len(sys.argv) == 3:
        update_config(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
        if sys.argv[1] == "init":
            print("Initializing config file:")
            load_config()
        elif sys.argv[1] == "reset":
            print("Resetting config with defaults:")
            for key, value in DEFAULT_CONFIG.items():
                update_config(key, value)
        else:
            _print_usage()
    elif len(sys.argv) == 1:
        load_config()
    else:
        _print_usage()


if __name__ == "__main__":
    main()
