#!/usr/bin/env python3

"""
This script does the whole workflow for pinocchio data, including:

1) Extraction of tar zipped files.
2) Conversion of raw pinocchio files (JPG format) into netcdf format.
3) Calculation of cloud parameters (DShip data needed).
"""

from datetime import datetime
from scipy.interpolate import interp1d
from typhon.spareice.array import Array, ArrayGroup
from typhon.spareice.datasets import Dataset
from typhon.spareice.handlers.common import NetCDF4

from cloud.handlers.dumbo import ThermoCamASCII
from cloud.handlers.metadata import ShipMSM

# JUST CHANGE THOSE LINES --
date1 = datetime(2017, 11, 5)
date2 = datetime(2017, 11, 6)

temperatures = [3.2, -12.8, -28.8]
# -- UNTIL HERE

data_dir = "/Users/jm.mac.mobil/Data/MSM68-2/"
pinocchio_dir = data_dir + "Dumbo/ThermalCam/"
# nc_dir = pinocchio_dir + \
#              "netcdf/{year}/{month}/{day}/{hour}/tm{year2}{month}{day}" \
#              "{hour}{minute}{second}.nc"
# calibration_file = "calibration/pinocchio_004_brightness_to_temperature.csv"
# mask_file = "masks/MSM68-2-pinocchio004-thermo.png"
stats_dir = data_dir + "cloud_stats/Dumbo/{year}{month}" \
    "{day}-{end_year}{end_month}{end_day}.nc"

dumbo = Dataset(
    "/Users/jm.mac.mobil/Data/MSM68-2/dumbo/ThermalCam/{year2}"
    "{month}{day}ASC/*.asc",
    handler=ThermoCamASCII(),
    time_coverage="content",
    times_cache="dumbo_times.json"
)

#mask = load_mask("masks/MSM68-2-pinocchio004-thermo.png")
image = dumbo["2017-11-05 09:00:21"]
mask = image.data < -30.


def cloud_parameters(image, mask, temperature):
    # Interpolate the ground temperature from ship data. Note: Outside of
    # the time coverage of the dship data, the data will be extrapolated.
    ground_temperature = temperature(image.time.timestamp())

    lapse_rate = -4.

    image.apply_mask(mask)

    return image.cloud_parameters(
        [ground_temperature + lapse_rate * 2.,
         ground_temperature + lapse_rate * 4.,
         ground_temperature + lapse_rate * 6.]
    )


# Load the dship data:
dship_fh = ShipMSM()
dship = \
    dship_fh.read(data_dir + "DSHIP/cruise_data_20171102-20171113.txt")
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
results = dumbo.map_content(
    date1, date2, cloud_parameters,
    func_arguments={
        "mask": mask,
        "temperature": temperature,
    },
    include_file_info=True,
    max_processes=4,
)

print("Save parameters to netcdf file.")
sorted_results = [r for r in sorted(results, key=lambda x: x[1][0])]

data = ArrayGroup()
data.attrs["description"] = \
    "Cloud statistics for dumbo thermal cam images."
data["time"] = [r[1][0] for r in sorted_results]

params = ["coverage", "mean_temperature", "base_temperature", "inhomogeneity"]
for param in params:
    data[param] = Array(
        [r[2][param] for r in sorted_results], dims=["time", "level"]
    )

# Write the data to this dataset:
param_dataset = Dataset(stats_dir, handler=NetCDF4())
param_dataset[date1:date2] = data
