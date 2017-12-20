#!/usr/bin/env python3

"""
This script compares the brightness temperatures measured by Dumbo and Pinocchio to determine a systematic bias.
"""

from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from typhon.spareice.datasets import Dataset
from typhon.spareice.handlers.common import NetCDF4


def plot(ax, date1, date2, dataset):
    data = dataset.accumulate(date1, date2)
    data = data[(data["time"] > date1) & (data["time"] < date2)]
    indices = data["time"].argsort()
    time = data["time"][indices][1::6]
    ax.plot(
        time,
        np.sum(data["coverage"][indices], axis=1).average(6))
    # ax.scatter(time, data["coverage"][:, 0].average(6), s=1, alpha=0.5)
    # ax.scatter(time, data["coverage"][:, 1].average(6), s=1, alpha=0.5,
    #             c="r")
    # ax.scatter(time, data["coverage"][:, 2].average(6), s=1, alpha=0.5,
    #             c="k")
    ax.legend(["Low", "Middle", "High"])
    ax.set_ylabel("Cloud coverage")


data_dir = "/Users/jm.mac.mobil/Data/MSM68-2/cloud_stats/"

# Add stat files of Dumbo
dumbo = Dataset(
    data_dir + "Dumbo/20171105-20171106.nc",
    handler=NetCDF4(),
)

# Add stat files of Pinocchio
pinocchio = Dataset(
    data_dir + "Pinocchio004/20171102-20171111.nc",
    handler=NetCDF4(),
)

date1 = datetime(2017, 11, 5)
date2 = datetime(2017, 11, 6)

fig, ax = plt.subplots()
plot(ax, date1, date2, dumbo)
plot(ax, date1, date2, pinocchio)
plt.title("Total Cloud Coverage")
plt.legend(["Dumbo", "Pinocchio"])
plt.show()