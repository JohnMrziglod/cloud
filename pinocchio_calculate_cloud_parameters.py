#!/usr/bin/env python3

"""
This script calculates the cloud parameters (coverage, inhomogeneity, etc.) from
pinocchio netcdf thermal cam images.
"""

from datetime import datetime
import argparse
import sys

import cloud.handlers.image.pinocchio
from cloud.image import ThermoCamImage
from typhon.spareice.datasets import Dataset


def calculate_parameters(path, date1, date2,  outfile, clear_sky_temperature):
    # Define where to find the netcdf thermal cam files of Pinocchio:
    pinocchio = Dataset(
        name="pinocchio.thermo_cam",
        files=path,
        # This handler can open and read the pinocchio files:
        handler=cloud.handlers.image.ThermoCamImage(fmt="netcdf"),
        # We cache the pinocchio image times in this file:
        times_cache="pinocchio_times.json",
    )

    # Calculate the cloud parameters for each image and store them to the files.
    print("Retrieve cloud parameters for images between %s and %s ..." % (
        date1, date2
    ))
    results = pinocchio.map_content(
        date1, date2, ThermoCamImage.cloud_parameters,
        method_arguments={
            "clear_sky_temperature" : clear_sky_temperature,
        },
        overwrite=True,
        include_file_info_in_results=True
    )

    with open(outfile, "w") as file:
        template = "{time}\t{coverage:.5f}\t{mean_temperature:.5f}\t{inhomogeneity:.5f}\n"
        file.write("time [UTC]\tcoverage [0-1]\tmean temperature [C]\tinhomogeneity \n")

        for result in sorted(results, key=lambda x: x[1][0]):
            time = result[1][0].strftime("%Y %m %d %H %M %S")
            params = result[2]

            file.write(template.format(time=time, **params))


def get_cmd_options():
    parser = argparse.ArgumentParser(
        usage="%(prog)s path date1 date2 outfile [temperature]\n\n",
        description="This script calculates the cloud parameters (coverage, inhomgenity, etc.) from pinocchio netcdf thermal cam images and write them to a file.",
        prog="pinocchio_calculate_cloud_parameters.py",
    )

    parser.add_argument(
        'path', action="store", type=str,
        help="The path name of the files including placeholders (e.g. {year}, {month}, {day}). For example, '/home/mpim/m300472/work/data/pinocchio/netcdf/{year}{month}{day}/{hour}/tm{year2}{month}{day}{hour}{minute}{second}{millisecond}.nc'",
    )
    parser.add_argument(
        'date1', action="store", type=str,
        help="The starting date, must be in this format 'YYYY-MM-DD_hh' (e.g. '2017-09-24_13'). 'hh' means hour.",
    )
    parser.add_argument(
        'date2', action="store", type=str,
        help="The ending date, must be in the same format as the starting date.",
    )
    parser.add_argument(
        'outfile', action="store", type=str,
        help="The path and name of the output file (where the cloud parameters should be stored).",
    )
    parser.add_argument(
        'temperature', action="store", type=float,
        help="The threshold temperature for clear sky (all pixel with temperatures greater than this threshold are considered to be a cloud).",
        nargs='?',
        default=0,
    )

    return parser.parse_args()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        args = get_cmd_options()
        date1 = datetime.strptime(args.date1, "%Y-%m-%d_%H")
        date2 = datetime.strptime(args.date2, "%Y-%m-%d_%H")
        calculate_parameters(args.path, date1, date2, args.outfile, args.temperature)
    else:
        calculate_parameters(
            path="/home/mpim/m300472/work/data/pinocchio/netcdf/{year}{month}{day}/{hour}/tm{year2}{month}{day}{hour}{minute}{second}{millisecond}.nc",
            date1=datetime(2017, 7, 5, 8),
            date2=datetime(2017, 7, 5, 9),
            outfile="pinocchio_cloud_data.txt",
            clear_sky_temperature=5,
        )
