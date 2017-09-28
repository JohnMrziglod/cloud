#!/usr/bin/env python3

"""
This script creates a calibration file for the Pinocchio thermal cam from the calibration images.
"""

from datetime import datetime


import matplotlib as mpl
mpl.use('Agg')
import numpy as np
import cloud.handlers.image
import cloud.handlers.image.pinocchio

create_calibration_file = False
apply_calibration = True

# Create the calibration file (this should be run only once):
calibration_mask = np.zeros((252, 336))
calibration_mask[100:130, 145:160] = 1
# calibration_mask = [0, 0, 1, 0]
calibration_mask = calibration_mask == 1

if True:
    fh = cloud.handlers.image.pinocchio.ThermoCamFile()
    img = fh.read("/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/30/m170925105602821.jpg", convert_to_temperatures=False)
    img.apply_mask(calibration_mask)
    img.save("test.png")
    exit()

cloud.handlers.image.pinocchio.create_calibration_file(
    "/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/",
    "/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/calibration_pinocchio_001_2017-09-25.csv",
    "/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/pinocchio_001_brightness_to_temperature.csv",
    calibration_mask,
    "/home/mpim/m300472/work/data/calibration/pinocchio_001_2017-09-25/calibration_curve.png",
)
