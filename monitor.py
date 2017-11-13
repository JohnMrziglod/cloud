#!/usr/bin/env python3

"""
This script monitors all measurements of a cruise including dship data,
pinocchio, dumbo and ceilometer measurements.
"""

from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from typhon.spareice.datasets import Dataset, DatasetManager, NoFilesError
from typhon.spareice.handlers.common import NetCDF4

from cloud.handlers.metadata import ShipMSM

# The time period that you want to see:
date1 = "2017-11-02"
date2 = "2017-11-11"

# The base dir of all data:
data_dir = "/Users/jm.mac.mobil/Data/MSM68-2/"
plot_number = 510

# Define all needed datasets:
dataset = DatasetManager()
dataset += Dataset(
    data_dir + "dship/atmosphere/{year}{month}{day}_{hour}{minute}{second}-"
               "{end_year}{end_month}{end_day}_{end_hour}{end_minute}"
               "{end_second}",
    handler=ShipMSM(),
    name="DSHIP",
)
dataset += Dataset(
    data_dir + "cloud_stats/pinocchio004/{year}{month}" \
               "{day}-{end_year}{end_month}{end_day}.nc",
    handler=NetCDF4(),
    name="Pinocchio",
)
dataset += Dataset(
    data_dir + "cloud_stats/pinocchio004/{year}{month}" \
               "{day}-{end_year}{end_month}{end_day}.nc",
    handler=NetCDF4(),
    name="Dumbo",
)
dataset += Dataset(
    data_dir + "cloud_stats/Ceilometer/"
               "{year}{month}{day}_FS_MERIAN_CHM090102.nc",
    handler=NetCDF4(),
    name="Ceilometer",
)

# Plotting of DShip data
dship = dataset["DSHIP"].accumulate(date1, date2)
dship = dship[dship["air_temperature"] < 99]
dship = dship[dship["air_pressure"] > 500]

temp_plot = plt.subplot(plot_number + 1)
plt.grid()
plt.plot(dship["time"], dship["air_temperature"])
plt.plot(dship["time"], dship["water_temperature"])
# plt.plot(dship["time"], dship["air_temperature"] - 2*4.)
# plt.plot(dship["time"], dship["air_temperature"] - 6*4.)
# plt.plot(dship["time"], dship["air_temperature"] - 10*4.)
plt.setp(temp_plot.get_xticklabels(), visible=False)
temp_plot.legend(["Air", "Water",])
# temp_plot.legend(["Air", "Water", "T_low", "T_middle", "T_high"])
temp_plot.set_ylabel("Temperature")

# Plotting of cloud coverage data (coming from dumbo and pinocchio):
cc_plot = plt.subplot(plot_number + 2, sharex=temp_plot)
plt.grid()
plt.setp(cc_plot.get_xticklabels(), visible=False)
cc_plot.set_ylabel("Cloud coverage")

# try:
#     pinocchio = dataset["Pinocchio"].accumulate(date1, date2)
#     plt.plot(pinocchio["time"], pinocchio["coverage"][:, 0])
#     plt.plot(pinocchio["time"], pinocchio["coverage"][:, 1])
#     plt.plot(pinocchio["time"], pinocchio["coverage"][:, 2])
#     plt.plot(pinocchio["time"], np.sum(pinocchio["coverage"], 1))
#     print(pinocchio["time"])
# except NoFilesError:
#     print("Found no pinocchio files to show.")

try:
    cbh_plot = plt.subplot(plot_number + 3, sharex=temp_plot)
    plt.grid()
    cbh_plot.set_xlabel("Time")
    cbh_plot.set_ylabel("Cloud base height")
    ceilometer = dataset["Ceilometer"].accumulate(
        date1,
        date2, reading_args={"fields": ("cbh", "time")}
    )
    plt.plot(ceilometer["time"], ceilometer["cbh"][:, 0])
    plt.plot(ceilometer["time"], ceilometer["cbh"][:, 1])
    plt.plot(ceilometer["time"], ceilometer["cbh"][:, 2])
    plt.setp(cbh_plot.get_xticklabels(), visible=False)
    cbh_plot.legend(["Layer 1", "Layer 2", "Layer 3"])
except:
    pass

# Plotting the rest of the dship data:
p_plot = plt.subplot(plot_number + 4, sharex=temp_plot)
plt.grid()
plt.plot(dship["time"], dship["air_pressure"])
plt.setp(p_plot.get_xticklabels(), visible=False)
p_plot.set_ylabel("Pressure")

rh_plot = plt.subplot(plot_number + 5, sharex=temp_plot)
plt.grid()
plt.plot(dship["time"], dship["humidity"])
plt.setp(rh_plot.get_xticklabels(), fontsize=6)
rh_plot.set_xlabel("Time")
rh_plot.set_ylabel("Humidity")

plt.show()