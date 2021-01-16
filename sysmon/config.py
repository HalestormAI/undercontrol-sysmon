import argparse
import logging
from pathlib import Path
from typing import Any, Dict, TypeVar, List

import toml

from .logger import logger

ValueType = TypeVar('T')
_config = {}


class ConfigError(Exception):
    pass

def check_dir_paths(paths: List[str]):
    for p in paths:
        if not Path(p).is_dir():
            raise ConfigError(
                f"The path '{p}' does not exist - cannot check for disk usage.")


def parse_args(default_args: Dict = None) -> argparse.Namespace:

    class ReadableDirectoryPath(argparse.Action):
        def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace, values: List[str], option_string: str = None):
            check_dir_paths(values)
            setattr(namespace, self.dest, values)

    parser = argparse.ArgumentParser(
        description="A small program to gather system stats and publish to a web service.")
    parser.add_argument("--config", default=None,
                        help="Path to the config file from which to load arguments. Can be overriden on the command line.")
    c_args, remaining_args = parser.parse_known_args()

    group = parser.add_argument_group("Server Config")
    group.add_argument("--host", default="0.0.0.0",
                       help="The server host. Set to 0.0.0.0 to listen for connections on all NICs.")
    group.add_argument("--port", default=7653, type=int,
                       help="The server port.")
    group.add_argument("--num-workers", type=int, default=1,
                       help="Number of concurrent workers for the web-service.")
    group.add_argument("--reload", action="store_true",
                       help="Enable auto-reload. Not advisable when running as a service")
    group = parser.add_argument_group("Stats")
    group.add_argument("--per-cpu", action="store_true",
                       help="Display stats such as CPU Frequency per core, rather than a holistic value.")
    group.add_argument("--disks", action=ReadableDirectoryPath, nargs="*",
                       help="Paths to disks that should be monitored for usage.")

    if c_args.config is not None:
        with open(c_args.config, "r") as fh:
            config_defaults = toml.load(fh)
            if "disks" in config_defaults:
                check_dir_paths(config_defaults["disks"])
        parser.set_defaults(**config_defaults)

    return parser.parse_args(remaining_args)


def get(key: str, default_val: ValueType = None) -> ValueType:
    return _config.get(key, default_val)


def load():
    args = parse_args()
    _config.update(vars(args))


def log():
    logger.info(_config)