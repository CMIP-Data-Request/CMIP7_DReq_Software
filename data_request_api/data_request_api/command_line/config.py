#!/usr/bin/env python3

import argparse

from data_request_api.utilities import config as dreqcfg


def main():
    parser = argparse.ArgumentParser(
        description="Config CLI",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Arguments:
  init (or no arguments): Initialize the config file,
      i.e. create a config file with default values if it does not exist.
  list: List all keys in the config file.
  reset: Reset the config file to default values.
  <key> <value>: Update a specific key in the config file.
  help: print this help message.

Examples:
  CMIP7_data_request_api_config offline true
  CMIP7_data_request_api_config reset""",
    )

    if parser.prog.startswith("config"):
        parser.usage = "python -m data_request_api.command_line.config <arguments>"
    else:
        parser.usage = "CMIP7_data_request_api_config <arguments>"

    parser.add_argument("command", nargs="*")

    # Add the --cfgfile option just for testing purposes
    parser.add_argument("--cfgfile", type=str, help=argparse.SUPPRESS)

    args = parser.parse_args()

    # Add the --cfgfile option just for testing purposes
    if args.cfgfile:
        dreqcfg.CONFIG_FILE = args.cfgfile

    if len(args.command) == 0 or args.command[0] == "init":
        print(f"Initializing config file: '{dreqcfg.CONFIG_FILE}'")
        dreqcfg.load_config()
    elif args.command[0] == "reset":
        print("Resetting config with defaults:")
        for key, value in dreqcfg.DEFAULT_CONFIG.items():
            dreqcfg.update_config(key, value)
    elif args.command[0] == "list":
        for key, value in dreqcfg.load_config().items():
            print(f"{key}: {value}")
    elif len(args.command) == 2:
        dreqcfg.update_config(args.command[0], args.command[1])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
