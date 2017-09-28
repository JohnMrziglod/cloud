#!/usr/bin/env python3

"""
This script compares the brightness temperatures measured by Dumbo and Pinocchio to determine a systematic bias.
"""

from datetime import datetime

from typhon.spareice.datasets import Dataset
import cloud.handlers.image

# Add thermal cam files of Dumbo
dumbo = Dataset(
    "dumbo.thermo_cam",
    files="/home/mpim/m300472/work/data/dumbo/netcdf/{year}{month}{day}/{hour}/{hour}{minute}{second}.nc",
    handler=cloud.handlers.image.ThermoCamImage(),
    times_cache="dumbo_times.json",
)

# Add thermal cam files of Pinocchio
pinocchio = Dataset(
    "pinocchio.thermo_cam",
    files="/home/mpim/m300472/work/data/pinocchio/netcdf/{year}{month}{day}/{hour}/tm{hour}{minute}{second}.nc",
    handler=cloud.handlers.image.ThermoCamImage(),
    times_cache="pinocchio_times.json",
)

# Find the corresponding files to Dumbo from Pinocchio
date1 = datetime(2017, 7, 5)
date2 = datetime(2017, 7, 6)
for primaries, secondaries in dumbo.find_overlapping_files(date1, date2, pinocchio):
    print("Dumbo:", primaries)
    print("Pinocchio:", secondaries)