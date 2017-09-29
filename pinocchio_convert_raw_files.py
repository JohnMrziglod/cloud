#!/usr/bin/env python3

"""
This script opens the raw files of the Pinocchio thermal cam, converts them
either to PNG images or netcdf files and apply a image mask.
"""

import argparse
from datetime import datetime
import sys

import cloud.handlers.image.pinocchio
from cloud.image import ThermoCamImage, load_mask
import numpy as np
from typhon.spareice.datasets import Dataset


def convert(inpath, outpath, date1, date2, calibration_file, mask_file=None):
    # Define where to find the original (raw) thermal cam files of Pinocchio:
    pinocchio_original = Dataset(
        name="pinocchio.thermo_cam",
        files=inpath,
        # This handler can open and read the pinocchio files:
        handler=cloud.handlers.image.pinocchio.ThermoCamFile(calibration_file),
        # We cache the pinocchio image times in this file:
        times_cache="pinocchio_times.json",
    )

    # We have two choices now: we can convert those files to images (PNG format) with a color bar indicating the
    # temperatures or we convert them to netcdf files. Images are better for the human eye but by converting them to netcdf
    # files we can process the data better.

    print("Process cloud images between %s and %s ..." % (
        date1, date2
    ))

    # Set this to True if you want to convert the files to PNG images and to False
    # if you need netcdf files.
    if False:
        # Copy those files to a new location and rename them
        print("Copy files and convert them to PNG...")
        pinocchio = pinocchio_original.copy(
            date1, date2,
            destination="/home/mpim/m300472/work/data/pinocchio/png/{year}{month}{day}/{hour}/{hour}{minute}{second}.png",
            converter=cloud.handlers.image.ThermoCamImage(fmt="png"),
        )
    else:
        # Let's copy the files to another location and convert them to netcdf files. The
        print("Copy files and convert them to netcdf...")
        pinocchio = pinocchio_original.copy(
            date1, date2,
            destination=outpath,
            # This handler can open and read the pinocchio files:
            converter=cloud.handlers.image.ThermoCamImage(fmt="netcdf"),
        )

    # Set this to true, if you want to apply a mask on this images (works only for
    # netcdf files!):
    if False:
        print("Load the mask...")
        # Either we can create the mask by ourselves here (for a 252x336
        # picture here) The mask be True where you want the image pixel to
        # be passed and False where you want to mask it.
        if mask_file is None:
            print("Create own mask!")
            mask = np.ones((252, 336))
            mask[0:20, :] = 0
            boolean_mask = mask == 1

        # Or we could load one from a file:
        else:
            boolean_mask = load_mask(mask_file)

        print("Apply the mask...")
        pinocchio.map_content(
            date1, date2, ThermoCamImage.apply_mask,
            method_arguments={
                "mask" : boolean_mask,
            },
            overwrite=True,
        )

    # Set this to true, if you want to cut off a part of the image.
    if True:
        print("Cut off a part of the images...")
        pinocchio.map_content(
            date1, date2, ThermoCamImage.cut,
            method_arguments={
                "x": slice(20, 252),
                "y": slice(0, 336),
            },
            overwrite=True,
        )


def get_cmd_options():
    parser = argparse.ArgumentParser(
        usage="%(prog)s inpath outpath date1 date2 calibration_file [mask_file]\n\n",
        description="This script opens the raw files of the Pinocchio thermal cam, converts them either to netcdf files and apply a image mask.",
        prog="pinocchio_calculate_cloud_parameters.py",
    )

    parser.add_argument(
        'inpath', action="store", type=str,
        help="The path name of the files including placeholders (e.g. {year}, {month}, {day}). For example, '/home/mpim/m300472/work/cameras/T_jpg_pinoc/tm{year2}{month}{day}{hour}{minute}{second}{millisecond}.jpg'",
    )
    parser.add_argument(
        'outpath', action="store", type=str,
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
        'calibration_file', action="store", type=str,
        help="The path and name of the calibration file for pinocchio.",
    )
    parser.add_argument(
        'mask_file', action="store", type=str,
        help="The path and name of the mask file. Can be .txt or .png.",
        nargs='?',
        default=None,
    )

    return parser.parse_args()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        args = get_cmd_options()
        date1 = datetime.strptime(args.date1, "%Y-%m-%d_%H")
        date2 = datetime.strptime(args.date2, "%Y-%m-%d_%H")
        convert(args.inpath, args.outpath, date1, date2, args.calibration_file, args.mask_file)
    else:
        inpath = "/home/mpim/m300472/work/cameras/T_jpg_pinoc/tm{year2}{month}{day}{hour}{minute}{second}{millisecond}.jpg"
        outpath = "/home/mpim/m300472/work/data/pinocchio/netcdf/{year}{month}{day}/{hour}/tm{year2}{month}{day}{hour}{minute}{second}{millisecond}.nc"
        calibration_file = "/home/mpim/m300472/work/data/calibration/pinocchio_0042016_2017-09-05/pixel_to_temperature.csv"
        date1 = datetime(2017, 7, 5)
        date2 = datetime(2017, 7, 5, 1)

        convert(inpath, outpath, date1, date2, calibration_file)
