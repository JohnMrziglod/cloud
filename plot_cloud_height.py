#!/usr/bin/env python3

import matplotlib.pyplot as plt
from typhon.spareice.datasets import Dataset, DatasetManager
from typhon.spareice.handlers.common import NetCDF4

date1 = "2017-11-02"
date2 = "2017-11-03"

ds = DatasetManager()

# Import pinocchio stats (created by pinocchio_workflow.py)
ds += Dataset(
    "/Users/jm.mac.mobil/Data/MSM68-2/cloud_stats/pinocchio004_{year}"
    "{month}{day}-{end_year}{end_month}{end_day}.nc",
    name="pinocchio",
    handler=NetCDF4(),
)

ds += Dataset(
    "/Users/jm.mac.mobil/Data/MSM68-2/cloud_stats/Ceilometer/{year}{month}"
    "{day}_FS_MERIAN_CHM090102.nc",
    name="ceilometer",
    handler=NetCDF4(),
)

ceilometer_data = ds["ceilometer"].accumulate(
    date1,
    date2, reading_args={"fields": ("cbh", "time")}
)
plt.plot(ceilometer_data["time"], ceilometer_data["cbh"][:, 0])
plt.plot(ceilometer_data["time"], ceilometer_data["cbh"][:, 1])
plt.plot(ceilometer_data["time"], ceilometer_data["cbh"][:, 2])
plt.show()