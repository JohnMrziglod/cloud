#!/usr/bin/env python3

"""
This script creates a calibration file for the Pinocchio thermal cam from the
calibration images.

Warnings:
        This is an old function that has not been updated since September 2017.
        It does not work probably at the moment, but it should be simple to
        rewrite it for using it again.
"""

import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import cloud.pinocchio


def main():
    create_calibration_file = False
    apply_calibration = True

    # Create the calibration file (this should be run only once):
    calibration_mask = np.zeros((252, 336))
    calibration_mask[115:130, 160:180] = 1
    # calibration_mask = [0, 0, 1, 0]
    calibration_mask = calibration_mask == 1

    if True:
        fh = cloud.pinocchio.ThermalCam(convert_to_temperatures=False)
        img = fh.read(
            "/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/-14/m170925122802592.jpg",
        )
        img.to_brightness()
        img.apply_mask(calibration_mask)
        img.save("test.png")

    cloud.pinocchio.create_calibration_file(
        "/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/",
        "/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/calibration_pinocchio_001_2017-09-25.csv",
        "/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/pinocchio_001_brightness_to_temperature.csv",
        calibration_mask,
        "/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/calibration_curve.png",
    )


if __name__ == '__main__':
    main()