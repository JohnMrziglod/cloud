import os.path

import numpy as np
from typhon.spareice.datasets import Dataset, DatasetManager
from typhon.spareice.handlers import FileHandler

from cloud import dumbo, pinocchio, metadata, ThermalCamMovie


__all__ = [
    "load_datasets",
]


def load_logbook(filename):
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
        raise ValueError(msg)

    # One line logbooks get a different array shape
    if len(data.shape) == 1:
        data.shape = (1, data.shape[0])

    return data.astype("O")


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
        files=os.path.join(
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
        files=os.path.join(basedir, config["Pinocchio"]["archive_files"]),
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
        files=os.path.join(
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
        files=os.path.join(basedir, config["Pinocchio"]["stats"]),
        name="Pinocchio-stats",
        max_processes=int(config["General"]["processes"]),
    )
    ###########################################################################

    ###########################################################################
    # Dumbo - Datasets:
    datasets += Dataset(
        name="Dumbo-netcdf",
        files=os.path.join(
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
        files=os.path.join(
            config["General"]["basedir"],
            config["Dumbo"]["raw_files"],
        ),
        handler=dumbo.ThermalCamASCII(),
        # Since the raw files have no temporal information in their filename,
        # we have to retrieve it from their content.
        time_coverage="content",
        max_processes=int(config["General"]["processes"]),
        exclude=logbook,
    )
    datasets += Dataset(
        files=os.path.join(basedir, config["Dumbo"]["stats"]),
        name="Dumbo-stats",
        max_processes=int(config["General"]["processes"]),
    )
    ###########################################################################

    datasets += Dataset(
        files=os.path.join(basedir, config["Ceilometer"]["files"]),
        name="Ceilometer",
        max_processes=int(config["General"]["processes"]),
    )
    datasets += Dataset(
        files=os.path.join(basedir, config["DShip"]["files"]),
        handler=metadata.ShipMSM(),
        name="DShip",
        max_processes=int(config["General"]["processes"]),
    )
    datasets += Dataset(
        files=os.path.join(basedir, config["Plots"]["overview"]),
        name="plot-overview",
        max_processes=int(config["General"]["processes"]),
    )
    datasets += Dataset(
        files=os.path.join(basedir, config["Plots"]["comparison"]),
        name="plot-comparison",
        max_processes=int(config["General"]["processes"]),
    )

    return datasets
