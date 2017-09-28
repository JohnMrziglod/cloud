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

cloud.handlers.image.pinocchio.create_calibration_file(
    "/home/mpim/m300472/work/data/calibration/pinocchio_0042016_2017-09-05/",
    "/home/mpim/m300472/work/data/calibration/pinocchio_0042016_2017-09-05/calibration_pinocchio_004-2016_2017-09-05.csv",
    "/home/mpim/m300472/work/data/calibration/pinocchio_0042016_2017-09-05/brightness_to_temperature.csv",
    calibration_mask,
    "/home/mpim/m300472/work/data/calibration/pinocchio_0042016_2017-09-05/calibration_curve.png",
)
