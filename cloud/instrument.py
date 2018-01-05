from time import time
import os.path
from scipy.interpolate import interp1d

import cloud

__all__ = [
    "calculate_cloud_statistics",
    "convert_raw_files",
]


def _create_hourly_movies(movies, mask):
    """

    Args:
        movies:
        mask:

    Returns:

    """
    if not movies:
        return None

    # Connect all short movies (single images) to one movie:
    movie = cloud.ThermalCamMovie.concatenate(movies)
    start, end = movie.get_range("time")
    print("\tJoined %s to %s files to hourly bundle" % (start, end))

    # Apply the mask on the movie
    if mask is not None:
        movie.apply_mask(mask)

    return movie


def convert_raw_files(datasets, instrument, config, start, end,):
    """Convert the raw files from jpg to netcdf.

    Args:
        datasets:
        instrument:
        config:
        start:
        end:

    Returns:
        None
    """

    mask = None
    if "mask" in config[instrument]:
        print("Load the mask")
        mask = cloud.load_mask(
            os.path.join(
                config["General"]["basedir"], config[instrument]["mask"])
        )

        print("Convert the raw files to netcdf and apply mask")
    else:
        print("Convert the raw files to netcdf")

    # Convert all pinocchio files and join them to hourly netcdf files.
    # Apply also a mask if available.
    datasets[instrument+"-raw"].map_content(
        start, end, func=_create_hourly_movies,
        func_arguments={
            "mask": mask,
        },
        # join files to hourly bundles
        bundle="1H",
        # the converted images will be saved into this dataset:
        output=datasets[instrument+"-netcdf"],
        verbose=True,
    )


def _load_metadata(datasets, config_dict, start, end):
    global all_metadata
    global config
    config = config_dict
    print("\tGet air temperature from %s dataset" %
          config["General"]["metadata"])

    all_metadata = \
        datasets[config["General"]["metadata"]].accumulate(start, end)


def _cloud_parameters(movie):
    """

    Args:
        movie: A ThermalCamMovie object that contains many thermal cam images.

    Returns:

    """
    start, end = movie.get_range("time")

    print("\tCalculate cloud parameters between %s and %s" % (start, end))

    metadata = all_metadata.limit_by("time", start, end)

    # Did not find any DShip data for the given time period
    if not metadata:
        return None

    # Interpolate the ground temperature from ship data. Note: Outside of
    # the time coverage of the dship data, the data will be extrapolated.
    temperature = interp1d(
        metadata["time"].astype("M8[s]").astype("int"),
        metadata["air_temperature"], fill_value="extrapolate"
    )

    return movie.cloud_parameters(
        temperature,
        [float(config["General"]["lapse_rate"]) * 2.,
         float(config["General"]["lapse_rate"]) * 4.,
         float(config["General"]["lapse_rate"]) * 6.]
    )


def calculate_cloud_statistics(datasets, instrument, config, start, end,):
    """

    Args:
        datasets:
        instrument:
        config:
        start:
        end:

    Returns:

    """
    print("Prepare calculation of cloud parameters between %s and %s" % (
        start, end))

    # Calculate the cloud parameters for each image and store them to this
    # dataset:
    datasets[instrument+"-netcdf"].map_content(
        start, end, _cloud_parameters,
        output=datasets[instrument+"-stats"],
        # For classifying the clouds by their height, we need the air
        # temperature from a metadata dataset (usually DShip)
        process_initializer=_load_metadata,
        process_initargs=(datasets, config, start, end),
        verbose=True
    )

