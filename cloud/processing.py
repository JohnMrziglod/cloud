"""Process the files of both cameras, Dumbo and Pinocchio.

Provides a function to convert raw files to netCDF files and apply a mask on
them. A second function can calculate the cloud statistics of those converted
files.
"""

import logging
import os.path

import xarray as xr
from scipy.interpolate import interp1d
from typhon.files import NoFilesError

import cloud

__all__ = [
    "calculate_cloud_statistics",
    "convert_raw_files",
]


def _apply_mask(images, mask):
    """Small helper function to apply a mask onto a movie.

    Args:
        images: A list with xarray.Dataset objects.
        mask: A mask that should be applied on those movies

    Returns:
        One concatenated long movie out of *movies*.
    """

    if not images:
        return None

    # Join all single images to one movie:
    movie = cloud.Movie(xr.concat(images, dim="time"))

    start, end = movie.time_coverage
    logging.info(f"Apply mask on images from {start} to {end}")

    try:
        # Apply the mask on the movie
        if mask is not None:
            movie.apply_mask(mask)

        # Return only the xarray.Dataset from the movie
        return movie.data
    except NoFilesError as err:
        logging.error(str(err))
    except Exception:
        logging.error("during converting:", exc_info=True)

    return None


def convert_raw_files(filesets, instrument, config, start, end,):
    """Convert the raw files from an instrument to netCDF format.

    If a mask file is set for this instrument in *config*, then the mask will
    be applied on its images.

    Args:
        filesets: A FileSetManager object.
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
                config["General"]["basedir"], config[instrument]["mask"]
            )
        )

        logging.info("Convert the raw files to netcdf and apply mask")
    else:
        logging.info("Convert the raw files to netcdf")

    # Convert all pinocchio files and join them to hourly netcdf files.
    # Apply also a mask if available.
    filesets[instrument+"-raw"].map(
        func=_apply_mask, kwargs={"mask": mask},
        on_content=True, start=start, end=end,
        # join files to hourly bundles
        bundle="1H",
        # the converted images will be saved into this dataset:
        output=filesets[instrument+"-netcdf"],
    )


def _cloud_parameters(images, temperatures, config):
    """Helper function for calculating cloud statistics.

    Args:
        images: A list with xarray.Dataset objects.

    Returns:
        A xarray.Dataset object with cloud parameters
    """
    movie = cloud.ThermalCamMovie(images)
    start, end = movie.time_coverage

    logging.info("Calculate cloud parameters between %s and %s" % (start, end))

    try:
        parameters = movie.cloud_parameters(
            temperatures,
            [float(config["General"]["lapse_rate"]) * 2.,
             float(config["General"]["lapse_rate"]) * 4.,
             float(config["General"]["lapse_rate"]) * 6.]
        )
        return parameters
    except Exception:  # noqa
        logging.error("during parameter calculation:", exc_info=True)

    return None


def calculate_cloud_statistics(filesets, instrument, config, start, end,):
    """Calculate cloud statistics for a period of thermal cam images.

    Uses the netcdf files from a instrument.

    Args:
        filesets: A FileSetManager object.
        instrument: The name of the instrument that should be processed.
        config: A dictionary-like object with configuration keys.
        start: Start time as string.
        end: End time as string.

    Returns:
        None
    """
    logging.info(
        f"Prepare calculation of cloud parameters between {start} and {end}")

    # For classifying the clouds by their height, we need the air
    # temperature from a metadata dataset (usually DShip)
    logging.info(
        "Get air temperature from %s dataset" % config["General"]["metadata"])

    # A list with a data object for each metadata file:
    metadata = xr.concat(
        filesets[config["General"]["metadata"]].collect(
            start, end, read_args={"fields": ["air_temperature"]},
        ), dim="time"
    )

    # Interpolate the ground temperature from ship data. Note: the data will be
    # extrapolated outside of the time coverage of the DShip data (hence, we
    # should not use the data outside from the time coverage):
    temperatures = interp1d(
        metadata["time"].data.astype("M8[s]").astype("int"),
        metadata["air_temperature"].data, fill_value="extrapolate"
    )

    # Calculate the cloud parameters for each image and store them to the
    # fileset "INSTRUMENT-stats" where INSTRUMENT is the name of the
    # instrument:
    filesets[instrument+"-netcdf"].map(
        func=_cloud_parameters, start=start, end=end,
        kwargs={
            "temperatures": temperatures,
            "config": config,
        },
        on_content=True, output=filesets[instrument+"-stats"],
    )

