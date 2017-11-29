#!/usr/bin/env python3

"""
This script monitors all measurements of a cruise including dship data,
pinocchio, dumbo and ceilometer measurements.
"""

from datetime import datetime

import matplotlib.pyplot as plt
from typhon.spareice.datasets import Dataset, DatasetManager
from typhon.spareice.handlers.common import NetCDF4

from cloud.handlers.metadata import ShipMSM


def define_datasets(data_dir):
    # Define all needed datasets:
    dataset = DatasetManager()
    dataset += Dataset(
        data_dir + "cloud_stats/Pinocchio004/{year}{month}"
                   "{day}-{end_year}{end_month}{end_day}.nc",
        handler=NetCDF4(),
        name="Pinocchio",
    )
    dataset += Dataset(
        data_dir + "cloud_stats/Dumbo/{year}{month}"
                   "{day}-{end_year}{end_month}{end_day}.nc",
        handler=NetCDF4(),
        name="Dumbo",
    )
    dataset += Dataset(
        data_dir + "Ceilometer/data/"
                   "{year}{month}{day}_FS_MERIAN_CHM090102.nc",
        handler=NetCDF4(),
        name="Ceilometer",
    )
    dataset += Dataset(
        data_dir + "DSHIP/cruise_data_20171102-20171113.txt",
        handler=ShipMSM(),
        name="DSHIP",
    )

    return dataset


def plot_temperature(ax, date1, date2, dataset):
    dship = dataset["DSHIP"].accumulate(date1, date2)
    dship = dship[dship["air_temperature"] < 99]
    dship = dship[dship["air_pressure"] > 500]

    ax.scatter(dship["time"], dship["air_temperature"], s=1)
    ax.scatter(dship["time"], dship["water_temperature"], s=1)
    # plt.plot(dship["time"], dship["air_temperature"] - 2*4.)
    # plt.plot(dship["time"], dship["air_temperature"] - 6*4.)
    # plt.plot(dship["time"], dship["air_temperature"] - 10*4.)
    ax.legend(["Air", "Water", ])
    # temp_plot.legend(["Air", "Water", "T_low", "T_middle", "T_high"])
    ax.set_ylabel("Temperature")


def plot_pressure(ax, date1, date2, dataset):
    dship = dataset["DSHIP"].accumulate(date1, date2)
    dship = dship[dship["air_temperature"] < 99]
    dship = dship[dship["air_pressure"] > 500]

    ax.scatter(dship["time"], dship["air_pressure"], s=1)
    ax.set_ylabel("Pressure")


def plot_humidity(ax, date1, date2, dataset):
    dship = dataset["DSHIP"].accumulate(date1, date2)
    dship = dship[dship["air_temperature"] < 99]
    dship = dship[dship["air_pressure"] > 500]

    ax.scatter(dship["time"], dship["humidity"], s=1)
    ax.set_ylabel("Humidity")


def plot_pinocchio(ax, date1, date2, dataset):
    data = dataset["Pinocchio"].accumulate(date1, date2)
    indices = data["time"].argsort()
    time = data["time"][indices][1::100]
    # plt.plot(
    #     time,
    #     np.sum(pinocchio["coverage"][indices], axis=1).average(100))
    ax.scatter(time, data["coverage"][:, 0].average(100), s=1, alpha=0.5)
    ax.scatter(time, data["coverage"][:, 1].average(100), s=1, alpha=0.5,
                c="r")
    ax.scatter(time, data["coverage"][:, 2].average(100), s=1, alpha=0.5,
                c="k")
    ax.legend(["Low", "Middle", "High"])
    ax.set_ylabel("Cloud coverage")


def plot_dumbo(ax, date1, date2, dataset):
    pass


def plot_ceilometer(ax, date1, date2, dataset):
    ceilometer = dataset["Ceilometer"].accumulate(
        date1,
        date2, reading_args={"fields": ("cbh", "time")}
    )
    ceilometer = ceilometer[ceilometer["time"] > datetime(2017, 11, 2)]
    ax.scatter(ceilometer["time"], ceilometer["cbh"][:, 0], s=1)
    ax.scatter(ceilometer["time"], ceilometer["cbh"][:, 1], s=1)
    ax.scatter(ceilometer["time"], ceilometer["cbh"][:, 2], s=1)
    ax.legend(["Layer 1", "Layer 2", "Layer 3"])
    ax.set_ylabel("Cloud base height")

# The time period that you want to see:
date1 = "2017-11-02"
date2 = "2017-11-13"

# The base dir of all data:
data_dir = "/Users/jm.mac.mobil/Data/MSM68-2/"

dataset = define_datasets(data_dir)

plots = [
    plot_temperature,
    plot_pinocchio,
    plot_dumbo,
    plot_ceilometer,
    plot_pressure,
    plot_humidity,
]
plot_position = len(plots) * 100 + 10

first_plot = None
for i, plot in enumerate(plots, 1):
    # All plots should be oriented along the x axis of the first plot:
    if first_plot is None:
        first_plot = ax = plt.subplot(plot_position + i)
    else:
        ax = plt.subplot(plot_position + i, sharex=first_plot)

    # Only the last plot should show the Time label:
    if i+1 < len(plots):
        plt.setp(ax.get_xticklabels(), visible=False)
    else:
        plt.setp(ax.get_xticklabels(), fontsize=6)
        ax.set_xlabel("Time")

    ax.grid()

    # Some error could be raised during plotting but we do not want it to abort
    # the program:
    try:
        plot(ax, date1, date2, dataset)
    except Exception as e:
        print("Could not plot #%d: %s" % (i, str(e)))

plt.xlim([
    Dataset._to_datetime(date1),
    Dataset._to_datetime(date2),
])

plt.show()