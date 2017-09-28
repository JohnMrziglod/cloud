import atexit
from collections import defaultdict
import copy
import datetime
import glob
import json
from multiprocessing import Pool
import os.path
import re
import shutil
import time
import warnings

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import typhon.files

__all__ = [
    #"ImageDataset",
]

#class ImageDataset(Dataset):

# def load_mask(self, filename: str):
#     """ Loads a mask file and returns it as a numpy array where the masked values are NaNs.
#
#     This method can handle ASCII or PNG files as masks.
#
#     Args:
#         filename: Path and name of the mask file
#
#     Returns:
#         numpy.array with w x h dimensions.
#     """
#
#     if filename is None:
#         return None
#
#     mask = None
#     if filename.endswith(".png"):
#         # read image
#         image = Image.open(filename, 'r')
#
#         # convert it to a grey scale image
#         mask = np.float32(np.array(image.convert('L')))
#     elif filename.endswith(".txt"):
#         # Count the number of columns in that mask file.
#         with open(filename, "r") as f:
#             num_columns = len(f.readline().split(","))
#
#         mask = np.genfromtxt(
#             filename,
#             delimiter=",",
#             skip_header=1,
#             usecols=list(range(1, num_columns))
#         )
#
#     mask[np.where(mask == 0)] = np.nan
#
#     self.mask = mask
#     # self.mask_transparent_pixels = mask.size - np.sum(np.isnan(self.mask))
#
# def load_meta_data(self, filename, file_handler):
#     """ Loads the meta data of the dataset from a file.
#
#     Args:
#         filename:
#         file_handler:
#
#     Returns:
#         None
#     """
#     fields = ["timestamp", "position latitude", "position longitude"]
#     meta_data = file_handler().read(filename, fields)
#     self.meta_data = {
#         "times" : None,
#         "lat" : None,
#         "lon" : None,
#     }
#     self.meta_data["times"], self.meta_data["lat"], self.meta_data["lon"] = zip(*meta_data)