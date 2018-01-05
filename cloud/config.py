import argparse
from configparser import ConfigParser

__all__ = [
    "get_standard_parser",
    "load_config",
    "load_config_and_parse_cmdline",
]


def get_standard_parser():
    """Get standard parser for command line arguments.

    Returns:
        An argparse.ArgumentParser object.
    """

    parser = argparse.ArgumentParser(
        add_help=False,
    )
    parser.add_argument(
        'start', type=str, default=None, nargs="?",
        help='Start time as string in format "YYYY-MM-DD hh:mm:ss" '
             '("hh:mm:ss" is optional). If not given, the [General][start] '
             'option from the config file is used.'
    )
    parser.add_argument(
        'end', type=str, default=None, nargs="?",
        help='End time as string in format "YYYY-MM-DD hh:mm:ss" '
             '("hh:mm:ss" is optional). If not given, the [General][end] '
             'option from the config file is used.'
    )
    parser.add_argument(
        '--config', type=str, default="config.ini",
        help='The path to the configuration file. Default is "config.ini".'
    )

    return parser


def load_config(filename):
    """Load the config dictionary from a file.

    Args:
        filename: Path and name of the config file.

    Returns:
        A configparser.Namespace object (you can handle it like a dictionary).
    """

    # Import the configuration file:
    config = ConfigParser()
    config.read(filename)

    return config


def load_config_and_parse_cmdline(parser=None):
    """Load config file and get command line options.

    Args:
        parser: An argparse object for parsing command line options. If not
            given, the standard command line parser is used.

    Returns:
        A tuple of a config dictionary and the parsed arguments.
    """

    if parser is None:
        parser = get_standard_parser()

    args = parser.parse_args()
    config = load_config(args.config)

    if args.start is None:
        args.start = config["General"]["start"]

    if args.end is None:
        args.end = config["General"]["end"]

    return config, args
