#!/usr/bin/env python3

"""
This script does the whole workflow for pinocchio data, including:

1) Extraction of tar zipped files.
2) Conversion of raw pinocchio files (JPG format) into netcdf format.
3) Calculation of cloud parameters (DShip data needed).
"""

from datetime import datetime
import os.path
import shutil
import tarfile

import pandas as pd
from scipy.interpolate import interp1d
from typhon.spareice.array import Array, ArrayGroup
from typhon.spareice.datasets import Dataset
from typhon.spareice.handlers import FileHandler
from typhon.spareice.handlers.common import NetCDF4

from cloud.handlers.metadata import ShipMSM
from cloud.handlers.pinocchio import ThermoCam
from cloud.image import load_mask, ThermoCamImage

# JUST CHANGE THOSE LINES --
date1 = datetime(2017, 11, 2)
date2 = datetime(2017, 11, 5, 23)

temperatures = [3.2, -12.8, -28.8]
# -- UNTIL HERE

data_dir = "/Users/jm.mac.mobil/Data/MSM68-2/"
pinocchio_dir = data_dir + "pinocchio004/ThermalCam/"
nc_dir = pinocchio_dir + \
             "netcdf/{year}/{month}/{day}/{hour}/tm{year2}{month}{day}" \
             "{hour}{minute}{second}.nc"
calibration_file = "calibration/pinocchio_004_brightness_to_temperature.csv"
mask_file = "masks/MSM68-2-pinocchio004-thermo.png"
stats_dir = data_dir + "cloud_stats/pinocchio004/{year}{month}" \
    "{day}-{end_year}{end_month}{end_day}.nc"

# Set this to true if you need to extract the archive and convert the raw files
if True:
    for date in pd.date_range(date1, date2):
        archive_filename = \
            "{basedir}/t{date}.tgz".format(
                basedir=pinocchio_dir, date=date.strftime("%y%m%d")
            )
        tmpdir = os.path.splitext(archive_filename)[0]

        # The files are in gzipped in a tar archive:
        archive = tarfile.open(archive_filename, mode="r:gz")

        print("Extract all files from the archive.")
        archive.extractall(path=tmpdir)

    print("Convert the raw files to netcdf and copy them to another location.")
    pinocchio_raw = Dataset(
        pinocchio_dir + "t{year2}{month}"
        "{day}/tm{year2}{month}{day}{hour}{minute}{second}{millisecond}.jpg",
        handler=ThermoCam(calibration_file),
        # We cache the pinocchio image times in this file:
        times_cache="pinocchio_times.json",
    )
    pinocchio = pinocchio_raw.copy(
        date1, date2,
        nc_dir,
        # This handler can open and read the pinocchio files:
        converter=FileHandler(
            reader=ThermoCamImage.from_netcdf,
            writer=ThermoCamImage.to_netcdf,
        ),
    )

    if mask_file is not None:
        print("Apply the mask.")
        mask = load_mask(mask_file)

        results = pinocchio.map_content(
            date1, date2, ThermoCamImage.apply_mask,
            func_arguments={
                "mask": mask,
            },
            max_processes=8,
            overwrite=True,
        )

    print("Delete extracted files.")
    shutil.rmtree(tmpdir)
else:
    pinocchio = Dataset(
        files=nc_dir,
        # This handler can open and read the pinocchio files:
        handler=FileHandler(
            reader=ThermoCamImage.from_netcdf,
            writer=ThermoCamImage.to_netcdf,
        ),
        # We cache the pinocchio image times in this file:
        times_cache="pinocchio_times.json",
    )

# Set this to true if you want to calculate the cloud parameters:
if True:
    def cloud_parameters(dataset, filename, times, temperature):
        image = dataset.read(filename)

        # Interpolate the ground temperature from ship data. Note: Outside of
        # the time coverage of the dship data, the data will be extrapolated.
        ground_temperature = temperature(times[0].timestamp())

        lapse_rate = -4.

        return image.cloud_parameters(
            [ground_temperature + lapse_rate * 2.,
             ground_temperature + lapse_rate * 4.,
             ground_temperature + lapse_rate * 6.]
        )

    # Load the dship data:
    dship_dataset = Dataset(
        data_dir + "dship/atmosphere/{year}{month}{day}_{hour}{minute}{second}-"
                   "{end_year}{end_month}{end_day}_{end_hour}{end_minute}"
                   "{end_second}",
        handler=ShipMSM(),
        name="DSHIP",
    )
    dship = dship_dataset.accumulate(date1, date2)
    dship = dship[dship["air_temperature"] < 99]
    dship = dship[dship["air_pressure"] > 500]

    # Create interpolation function from ship data:
    temperature = interp1d(
        dship["time"].astype("M8[s]").astype("int"),
        dship["air_temperature"], fill_value="extrapolate"
    )

    # Calculate the cloud parameters for each image and store them to this
    # dataset:
    print("Retrieve cloud parameters between %s and %s" % (date1, date2))
    results = pinocchio.map(
        date1, date2, cloud_parameters,
        func_arguments={
            "temperature": temperature,
        },
        include_file_info=True,
        max_processes=8
    )

    print("Save parameters to netcdf file.")
    sorted_results = [r for r in sorted(results, key=lambda x: x[1][0])]

    data = ArrayGroup()
    data.attrs["description"] = \
        "Cloud statistics for pinocchio thermal cam images."
    data["time"] = [r[1][0] for r in sorted_results]
    print(data["time"])

    params = ["coverage", "mean_temperature", "base_temperature", "inhomogeneity"]
    for param in params:
        data[param] = Array(
            [r[2][param] for r in sorted_results], dims=["time", "level"]
        )

    # Write the data to this dataset:
    param_dataset = Dataset(stats_dir, handler=NetCDF4())
    param_dataset[date1:date2] = data
