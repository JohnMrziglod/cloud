#!/usr/bin/env python3

"""
This script renames the ASCII files of the dumbo thermal cam  and converts them either to PNG images or netcdf files.
"""

from datetime import datetime

from typhon.spareice.datasets import Dataset

import cloud.handlers.dumbo
import cloud.handlers.image

# Define where to find the original thermal cam files of Dumbo:
dumbo_original = Dataset(
    "dumbo.thermo_cam",
    files="/home/mpim/m300472/work/data/dumbo/original/{year}{month}{day}ASC/*.asc.bz2",
    handler=cloud.handlers.dumbo.ThermoCamASCIIFile(),
    time_coverage_retrieving_method="content",
    times_cache="dumbo_times.json"
)

print(dumbo_original)

# We have two choices now: we can convert those files to images (PNG format) with a color bar indicating the
# temperatures or we convert them to netcdf files. Images are better for the human eye but by converting them to netcdf
# files we can process the data better.

# Set this to true if you want to convert the files to PNG images.
if False:
    # Copy those files to a new location and rename them
    date1 = datetime(2017, 7, 5)
    date2 = datetime(2017, 7, 6)
    dumbo_png = dumbo_original.copy_to(
        "/home/mpim/m300472/work/data/dumbo/png/{year}{month}{day}/{hour}/{hour}{minute}{second}.png",
        start=date1, end=date2,
        converter=cloud.handlers.image.ThermoCamImage(fmt="png"),
    )

# Set this to true if you want to convert the files to NetCDF4 format.
if True:
    # Copy those files to a new location and rename them
    date1 = datetime(2017, 7, 5)
    date2 = datetime(2017, 7, 6)
    dumbo_netcdf = dumbo_original.copy_to(
        "/home/mpim/m300472/work/data/dumbo/netcdf/{year}{month}{day}/{hour}/{hour}{minute}{second}.nc",
        start=date1, end=date2,
        converter=cloud.handlers.image.ThermoCamImage(fmt="netcdf"),
    )
