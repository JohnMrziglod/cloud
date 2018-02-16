"""Works with the files of both cameras Dumbo and Pinocchio.

Provides a function to convert raw files to netCDF files and apply a mask on
them. A second function can calculate the cloud statistics of those files.
"""

import logging
import os.path
from time import time

import xarray as xr
from scipy.interpolate import interp1d

import cloud

__all__ = [
    "calculate_cloud_statistics",
    "convert_raw_files",
]


def _apply_mask(movie, files, mask):
    """Small helper function to apply a mask onto a movie.

    Args:
        movie: A cloud.ThermalCamMovie object.
        files: A list of FileInfo object with the opened files. This is
            necessary if running it with Dataset.map().
        mask: A mask that should be applied on those movies

    Returns:
        One concatenated long movie out of *movies*.
    """

    if not movie:
        return None

    start, end = movie.get_range("time")
    logging.info(f"Apply mask on images from {start} to {end}")

    try:
        # Apply the mask on the movie
        if mask is not None:
            movie.apply_mask(mask)

        return movie
    except cloud.NoFilesError as err:
        logging.error(str(err))
    except Exception:
        logging.error("during converting:", exc_info=True)

    return None


def convert_raw_files(datasets, instrument, config, start, end,):
    """Convert the raw files from an instrument to netCDF format.

    If a mask file is set for this instrument in *config*, then the mask will
    be applied on its images.

    Args:
        datasets: A DatasetManager object.
        instrument: The name of the instrument that should be processed.
        config: A dictionary-like object with configuration keys.
        start: Start time as string.
        end: End time as string.

    Returns:
        None
    """

    mask = None
    if "mask" in config[instrument]:
        logging.info("Load the mask")
        mask = cloud.load_mask(
            os.path.join(
                config["General"]["basedir"], config[instrument]["mask"])
        )

        logging.info("Convert the raw files to netcdf and apply mask")
    else:
        logging.info("Convert the raw files to netcdf")

    # Convert all pinocchio files and join them to hourly netcdf files.
    # Apply also a mask if available.
    datasets[instrument+"-raw"].map(
        start, end, func=_apply_mask,
        on_content=True,
        kwargs={
            "mask": mask,
        },
        # join files to hourly bundles
        bundle="1H",
        # the converted images will be saved into this dataset:
        output=datasets[instrument+"-netcdf"],
    )


def _load_metadata(datasets, config_dict, start, end):
    """Small helper function that load the metadata to a global variable.

    """

    # Global variables are okay when we use multiprocessing:
    global all_metadata
    global config
    config = config_dict
    logging.info(
        "Get air temperature from %s dataset" % config["General"]["metadata"])

    # A list with a data object for each metadata file:
    all_metadata = datasets[config["General"]["metadata"]].collect(
        start, end, read_args={"fields": ["air_temperature"]},
    )

    print(all_metadata)


def _cloud_parameters(movie, file):
    """Helper function for calculating cloud statistics.

    Args:
        movie: A ThermalCamMovie object that contains many thermal cam images.
        file: A FileInfo object of the file to open. Is necessary to run it
            with Dataset.map().

    Returns:
        An GroupedArrays object with cloud parameters
    """
    start, end = movie.get_range("time")

    logging.info("Calculate cloud parameters between %s and %s" % (start, end))

    metadata = all_metadata.sel(time=slice(start, end))

    # Did not find any DShip data for the given time period
    if not metadata.time.size:
        return None

    try:
        # Interpolate the ground temperature from ship data. Note: Outside of
        # the time coverage of the DShip data, the data will be extrapolated.
        temperature = interp1d(
            metadata["time"].data.astype("M8[s]").astype("int"),
            metadata["air_temperature"].data, fill_value="extrapolate"
        )

        parameters = movie.cloud_parameters(
            temperature,
            [float(config["General"]["lapse_rate"]) * 2.,
             float(config["General"]["lapse_rate"]) * 4.,
             float(config["General"]["lapse_rate"]) * 6.]
        )
        return parameters
    except cloud.NoFilesError as err:
        logging.error(str(err))
    except Exception:  # noqa
        logging.error("during parameter calculation:", exc_info=True)

    return None


def calculate_cloud_statistics(datasets, instrument, config, start, end,):
    """Calculate cloud statistics for a period of thermal cam images.

    Uses the netcdf files from a instrument.

    Args:
        datasets: A DatasetManager object.
        instrument: The name of the instrument that should be processed.
        config: A dictionary-like object with configuration keys.
        start: Start time as string.
        end: End time as string.

    Returns:
        None
    """
    logging.info(
        "Prepare calculation of cloud parameters between %s and %s" % (
            start, end))

    # Calculate the cloud parameters for each image and store them to this
    # dataset:
    datasets[instrument+"-netcdf"].map(
        start, end, func=_cloud_parameters,
        on_content=True, output=datasets[instrument+"-stats"],
        # For classifying the clouds by their height, we need the air
        # temperature from a metadata dataset (usually DShip)
        worker_initializer=_load_metadata,
        worker_initargs=(datasets, config, start, end),
    )

