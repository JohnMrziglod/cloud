#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script creates a calibration file for the Pinocchio thermal cam from the
calibration images.

Warnings:
        This is an old script that has not been updated since September 2017.
        It does not work probably at the moment, but it should be simple to
        rewrite it for using it again.
"""

import argparse
from collections import defaultdict
from os.path import join

import numpy as np
from typhon.files import FileSet

import cloud.pinocchio


def get_temperatures(temperatures_file=None):
    """Get the mapping from *label* to *real calibration* temperatures.

    *Label* temperatures are the temperatures coming from the (old) calibration
    gauge. The *real calibration* temperature should be measured with a KT19 or
    similar.

    Args:
        temperatures_file: So far not implemented.

    Returns:
        A dictionary with label temperatures as keys and real temperatures as
        values.
    """
    # TODO: Implement here how to read the temperatures file
    # Alternative: Simply insert here a dictionary The keys are the temperature
    # labels in the path to the images, the values are the real calibration
    # temperature (coming from KT19 or similar).
    temperatures = {
        20: 21,
        19: 20,
        ...: ...
    }

    return temperatures


def create_calibration_file(images, temperature, mask, out_file):
    """Create a calibration file for the pinocchio thermal cam.

    The created file is in CSV format and can be used as calibration for the
    cloud.pinocchio.ThermalCam() file handler class. It simply contains two
    columns of data: the first contains the target temperature and the second
    contains the corresponding pixel brightness [grey value 0-255].

    Args:
        images: A Dataset object containing the calibration images.
        temperature: A dictionary with label temperatures as keys and real
            calibration temperatures as keys in the calibration (normally
            recorded by a KT19 pyranometer).
        out_file: Name of the created output file.
        mask: A numpy.mask that only shows the area where the calibration
            target is.

    Returns:
        None

    Examples:

    .. :code-block::
        :caption: ls pinocchio/calibration/images/

        30/
        28/
        26/

    .. :code-block::
        :caption: temperature_file.csv

        header line no. 1
        header line no.2
        30;29.6
        28;28.1
        26;25.9
        ...

    .. :code-block:: python
        :caption: script.py

        # Create the calibration file once
        create_calibration_file(
            "pinocchio/calibration/images/",
            "temperature_file.csv",
            "pixel_to_temperature.csv")

        # Use it for converting pinocchio images:
        pinocchio_handler = cloud.pinocchio.ThermalCam(
            calibration_file="pixel_to_temperature.csv"
        )
    """
    # We retrieve the brightness values from the image pixels that are not
    # masked. Since the images have a temperature label in their file path, we
    # can use it to label the brightness values.
    brightness = defaultdict(list)

    for file, image in images.icollect(return_info=True):
        # Mask the unimportant parts:
        image.apply_mask(mask)

        # Add the pixel values
        brightness[file.attr["temperature"]].append(
            np.nanmedian(image["images"]).item(0)
        )

    if not brightness:
        print("Could not find any calibration images!")
        exit()

    # Average all pixel values and change the temperature to an integer:
    brightness = {
        int(temperature): np.median(np.array(pixel_values))
        for temperature, pixel_values in brightness.items()
    }

    # Create the mapping from brightness values to real (calibrated)
    # temperatures:
    brightness_temperature = {
        brightness[label]: temperature[label]
        for label in set(brightness) & set(temperature)
    }

    # Save the calibration in a file:
    filename = file.times[0].strftime(out_file)
    with open(filename, 'w') as file:
        file.write("Brightness Value[0-255];Temperature[deg C]\n")
        for brightness, temp in sorted(brightness_temperature.items()):
            file.write(f"{brightness};{temp}\n")


def get_cmd_line_parser():
    description = """Create a calibration file for Pinocchio thermal cam.\n
    
    Warnings:
        This is an old script that has not been updated since September 2017.
        It does not work probably at the moment, but it should be simple to
        rewrite it for using it again.

    This script creates a calibration file from Pinocchio calibration images.
    """

    examples = """Examples:

    > ./%(prog)s root_dir
    Default usage: the program extracts the calibration files from this given 
    path (replace root_dir with the base path to the folder with the 
    calibration images) and creates a calibration file called 
    'pinocchio_calibration_%%Y%%M%%D.csv'.
    """

    parser = argparse.ArgumentParser(
        description=description,
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'root_dir', type=str, default=None, nargs="?",
        help='Path to the calibration images. Must contain temporal '
             'placeholders ({year}, {month}, etc.) and {temperature} '
             '(placeholder for the temperature).'
    )

    return parser


def main():
    args = get_cmd_line_parser().parse_args()

    # TODO: Delete this line if you fixed this script
    print("Please check the code before running this.")
    #exit()

    images_path = join(args.root_dir,
                "{temperature}/m{year2}{month}{day}{hour}{minute}{second}*.jpg"
                )
    images = FileSet(
        path=images_path,
        handler=cloud.pinocchio.ThermalCam(to_temperatures=False),
        name="Calibration Images",
    )

    # Create the calibration mask. Only a small part of the image will show the
    # the correct pixel values for the corresponding temperature. The rest will
    # not see the calibration target.
    calibration_mask = np.zeros((252, 336))
    calibration_mask[115:130, 160:180] = 1
    calibration_mask = calibration_mask.astype("bool")

    # Get the temperatures (normally from a file, but this is not implemented
    # yet):
    temperature = get_temperatures()

    create_calibration_file(
        images,
        temperature,
        calibration_mask,
        'pinocchio_calibration_%Y%m%d.csv',
    )


if __name__ == '__main__':
    main()
