"""
This module provides functions for loading the important user files such as
configuration, logbook, masks, etc. It can also deal with the command line
parameters.
"""

import argparse
from configparser import ConfigParser
import logging
import logging.config
import os.path

import numpy as np
import PIL.Image
import PIL.PngImagePlugin
from typhon.spareice.datasets import Dataset, DatasetManager, NoFilesError
from typhon.spareice.handlers import FileHandler, NetCDF4, Plot

from cloud import dumbo, pinocchio, metadata, ThermalCamMovie

__all__ = [
    "get_standard_parser",
    "init_toolbox",
    "load_config",
    "load_datasets",
    "load_logbook",
    "load_mask",
    "NoFilesError",
]


DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        '': {
            'level': 'INFO',
        },
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
}

logging.config.dictConfig(DEFAULT_LOGGING)
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s')


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


def init_toolbox(parser=None,):
    """Load all configurations, parse the command line args and load datasets.

    Load the configurations from the config file, parse the command line
    options and load all datasets (incl. logbook).

    Args:
        parser: An argparse object for parsing command line options. If not
            given, the standard command line parser is used.

    Returns:
        A tuple of a config dictionary, the parsed arguments and a
        DatasetManager with loaded datasets.
    """

    logging.info("Initialise cloud toolbox")

    if parser is None:
        parser = get_standard_parser()

    args = parser.parse_args()
    config = load_config(args.config)

    if args.start is None:
        args.start = config["General"]["start"]

    if args.end is None:
        args.end = config["General"]["end"]

    # Load all relevant datasets:
    datasets = load_datasets(config)

    return config, args, datasets


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


def load_datasets(config):
    """Load all datasets into one DatasetManager object

    Args:
        config: Dictionary with configuration keys and values.

    Returns:
        A DatasetManager object.
    """

    basedir = config["General"]["basedir"]

    # This DatasetManager can handle all dataset objects:
    datasets = DatasetManager()

    ###########################################################################
    # Pinocchio - Datasets:
    datasets += Dataset(
        name="Pinocchio-netcdf",
        path=os.path.join(
            config["General"]["basedir"],
            config["Pinocchio"]["nc_files"],
        ),
        handler=FileHandler(
            reader=ThermalCamMovie.from_netcdf,
            writer=ThermalCamMovie.to_netcdf,
        ),
        max_processes=int(config["General"]["processes"]),
    )
    datasets += Dataset(
        name="Pinocchio-archive",
        path=os.path.join(basedir, config["Pinocchio"]["archive_files"]),
        max_processes=int(config["General"]["processes"]),
    )

    # Load logbook from Pinocchio:
    logbook = None
    if "logbook" in config["Pinocchio"]:
        logbook = load_logbook(
            os.path.join(basedir, config["Pinocchio"]["logbook"])
        )
    datasets += Dataset(
        name="Pinocchio-raw",
        path=os.path.join(
            config["General"]["basedir"],
            os.path.splitext(config["Pinocchio"]["archive_files"])[0],
            config["Pinocchio"]["files_in_archive"],
        ),
        handler=pinocchio.ThermalCam(
            os.path.join(
                config["General"]["basedir"],
                config["Pinocchio"]["calibration"],
            )
        ),
        max_processes=int(config["General"]["processes"]),
        exclude=logbook,
    )
    datasets += Dataset(
        path=os.path.join(basedir, config["Pinocchio"]["stats"]),
        name="Pinocchio-stats",
        handler=NetCDF4(return_type="xarray"),
        max_processes=int(config["General"]["processes"]),
    )
    ###########################################################################

    ###########################################################################
    # Dumbo - Datasets:
    datasets += Dataset(
        name="Dumbo-netcdf",
        path=os.path.join(
            config["General"]["basedir"],
            config["Dumbo"]["nc_files"],
        ),
        handler=FileHandler(
            reader=ThermalCamMovie.from_netcdf,
            writer=ThermalCamMovie.to_netcdf,
        ),
        max_processes=int(config["General"]["processes"]),
    )

    # Load logbook from Dumbo:
    logbook = None
    if "logbook" in config["Dumbo"]:
        logbook = load_logbook(
            os.path.join(basedir, config["Dumbo"]["logbook"])
        )

    datasets += Dataset(
        name="Dumbo-raw",
        path=os.path.join(
            config["General"]["basedir"],
            config["Dumbo"]["raw_files"],
        ),
        handler=dumbo.ThermalCamASCII(),
        # Since the raw files have no temporal information in their filename,
        # we have to retrieve it from by their handler.
        info_via="handler",
        max_processes=int(config["General"]["processes"]),
        exclude=logbook,
    )
    datasets += Dataset(
        path=os.path.join(basedir, config["Dumbo"]["stats"]),
        name="Dumbo-stats",
        handler=NetCDF4(return_type="xarray"),
        max_processes=int(config["General"]["processes"]),
    )
    ###########################################################################

    datasets += Dataset(
        path=os.path.join(basedir, config["Ceilometer"]["files"]),
        name="Ceilometer",
        # Each file covers roughly 24 hours:
        time_coverage="24 hours",
        handler=NetCDF4(return_type="xarray"),
        max_processes=int(config["General"]["processes"]),
    )
    datasets += Dataset(
        path=os.path.join(basedir, config["DShip"]["files"]),
        handler=metadata.ShipMSM(),
        name="DShip",
        max_processes=int(config["General"]["processes"]),
    )
    datasets += Dataset(
        path=os.path.join(basedir, config["Plots"]["overview"]),
        name="plot-overview",
        handler=Plot(),
        max_processes=int(config["General"]["processes"]),
    )
    datasets += Dataset(
        path=os.path.join(basedir, config["Plots"]["comparison"]),
        name="plot-comparison",
        handler=Plot(),
        max_processes=int(config["General"]["processes"]),
    )
    datasets += Dataset(
        path=os.path.join(basedir, config["Plots"]["anomaly"]),
        name="plot-anomaly",
        handler=Plot(),
        max_processes=int(config["General"]["processes"]),
    )

    return datasets


def load_logbook(filename):
    """Loads the logbook.

    The logbook is a file with time periods that should be excluded from
    processing. Those files wont be converted from raw files to netCDF files.

    Args:
        filename: Path and name of the logbook file.

    Returns:
        A numpy.ndarray with the time periods.
    """
    data = np.genfromtxt(
        filename,
        dtype=np.datetime64,
        usecols=(0, 1),
    )

    if (np.diff(data) < np.timedelta64()).any():
        msg = \
            "The logbook '%s' contains invalid time periods. The start time "\
            "must always be earlier than the end time.\nFound invalid time " \
            "periods in (line numbers without header):\n" % filename

        fraud_lines = np.diff(data).flatten() < np.timedelta64()
        for line, line_is_fraud in enumerate(fraud_lines, 1):
            if line_is_fraud:
                msg += "\tLine %d\n" % line

        logging.critical(msg)
        exit()

    # One line logbooks get a different array shape
    if len(data.shape) == 1:
        data.shape = (1, data.shape[0])

    return data.astype("O")


def load_mask(filename):
    """Loads a mask file and returns it as a numpy array where the masked
    values are False.

    This method can handle ASCII or PNG files as masks.

    Args:
        filename: Path and name of the mask file

    Returns:
        numpy.array with w x h dimensions.
    """

    if filename is None:
        return None

    mask = None
    if filename.endswith(".png"):
        # read image
        image = PIL.Image.open(filename, 'r')

        # convert it to a grey scale image
        mask = np.float32(np.array(image.convert('L')))
        mask = np.flipud(mask)
        mask = mask == 255
    elif filename.endswith(".txt"):
        # Count the number of columns in that mask file.
        with open(filename, "r") as f:
            num_columns = len(f.readline().split(","))

        mask = np.genfromtxt(
            filename,
            delimiter=",",
            skip_header=1,
            usecols=list(range(1, num_columns))
        )

        mask = mask == 1

    return mask
