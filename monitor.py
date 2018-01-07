#!/usr/bin/env python3

"""
This script can create two types of plots:

* Overview plot: monitors all measurements of all instruments of a cruise
  including dship data, pinocchio, dumbo and ceilometer measurements.
* Comparison plot: shows all cloud parameters of the Dumbo and Pinocchio
  instruments.

"""

import argparse
import logging
import os.path
import traceback
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import cloud


logger = logging.getLogger(__name__)


def get_bin_size(data_len, config):
    # Zero means no averaging
    if int(config["Plots"]["overview_max_points"]) == 0:
        return 1

    bin_size = data_len / int(config["Plots"]["overview_max_points"])
    if bin_size < 1:
        return 1

    return int(bin_size)


def plot_temperature(ax, date1, date2, dataset, config):
    data = dataset["DShip"].accumulate(date1, date2)
    data = data.limit_by("time", date1, date2)
    data = data.sort_by("time")

    point_size = int(config["Plots"]["point_size"])
    bin_size = get_bin_size(len(data["time"]), config)

    ax.scatter(
        data["time"].average(bin_size),
        data["air_temperature"].average(bin_size),
        s=point_size, label="Air")
    ax.scatter(
        data["time"].average(bin_size),
        data["water_temperature"].average(bin_size),
        s=point_size, label="Water")
    ax.legend()
    ax.set_ylabel("Temperature")


def plot_pressure(ax, date1, date2, dataset, config):
    data = dataset["DShip"].accumulate(date1, date2)
    data = data.limit_by("time", date1, date2)
    data = data.sort_by("time")

    point_size = int(config["Plots"]["point_size"])
    bin_size = get_bin_size(len(data["time"]), config)

    ax.scatter(
        data["time"].average(bin_size),
        data["air_pressure"].average(bin_size),
        s=point_size,
    )
    ax.set_ylabel("Pressure")


def plot_humidity(ax, date1, date2, dataset, config):
    data = dataset["DShip"].accumulate(date1, date2)
    data = data.limit_by("time", date1, date2)
    data = data.sort_by("time")

    point_size = int(config["Plots"]["point_size"])
    bin_size = get_bin_size(len(data["time"]), config)

    ax.scatter(
        data["time"].average(bin_size).astype("O"),
        data["humidity"].average(bin_size),
        s=point_size
    )
    ax.set_ylabel("Humidity")


def plot_cloud_coverage(ax, date1, date2, datasets, config, instrument):
    data = datasets[instrument+"-stats"].accumulate(date1, date2)
    data = data.limit_by("time", date1, date2)
    data = data.sort_by("time")

    point_size = int(config["Plots"]["point_size"])
    bin_size = get_bin_size(len(data["time"]), config)

    ax.scatter(
        data["time"].average(bin_size),
        data["cloud_coverage"][:, 0].average(bin_size),
        s=point_size
    )
    ax.scatter(
        data["time"].average(bin_size),
        data["cloud_coverage"][:, 1].average(bin_size),
        s=point_size, c="r"
    )
    ax.scatter(
        data["time"].average(bin_size),
        data["cloud_coverage"][:, 2].average(bin_size),
        s=point_size, c="k"
    )
    ax.legend(["Low", "Middle", "High"])
    ax.set_ylabel("Cloud coverage")
    ax.set_title(instrument)


def plot_dumbo(*args):
    plot_cloud_coverage(*args, "Dumbo")


def plot_pinocchio(*args):
    plot_cloud_coverage(*args, "Pinocchio")


def plot_ceilometer(ax, date1, date2, dataset, config):

    data = dataset["Ceilometer"].accumulate(
        date1, date2, fields=("cbh", "time")
    )
    data = data.limit_by("time", date1, date2)
    data = data.sort_by("time")

    point_size = int(config["Plots"]["point_size"])
    bin_size = get_bin_size(len(data["time"]), config)

    ax.scatter(
        data["time"].average(bin_size),
        data["cbh"][:, 0].average(bin_size),
        s=point_size,
    )
    ax.scatter(
        data["time"].average(bin_size),
        data["cbh"][:, 1].average(bin_size),
        s=point_size
    )
    ax.scatter(
        data["time"].average(bin_size),
        data["cbh"][:, 2].average(bin_size),
        s=point_size
    )
    ax.legend(["Layer 1", "Layer 2", "Layer 3"])
    ax.set_ylabel("Cloud base height")
    ax.set_title("Ceilometer")


def plot_overview(datasets, config, start, end, ):

    print("Plot overview from %s to %s" % (start, end))

    plt.rcParams.update({'font.size': 12})

    plots = {
        "temperature": plot_temperature,
        "pinocchio": plot_pinocchio,
        "dumbo": plot_dumbo,
        "ceilometer": plot_ceilometer,
        "pressure": plot_pressure,
        "humidity": plot_humidity,
    }

    fig, axes = plt.subplots(
        len(plots), sharex=True, figsize=(16, 12), dpi=300)
    for i, plot in enumerate(plots.items()):
        name, plot_func = plot

        # Even if some error is raised during plotting we do not want it to
        # abort the whole script:
        try:
            plot_func(axes[i], start, end, datasets, config)
        except Exception as err:
            logger.error("Could not create %s plot:" % name, exc_info=True)
            traceback.print_tb(err.__traceback__)

        axes[i].grid()

    axes[0].set_title("Overview from %s to %s" % (
        start.to_pydatetime(), end.to_pydatetime()))
    axes[-1].set_xlabel("Time")
    axes[-1].set_xlim([
        pd.Timestamp(start),
        pd.Timestamp(end),
    ])
    fig.tight_layout()

    path = datasets["plot-overview"].generate_filename(
        datasets["plot-overview"].files, start, end)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print("  Save to %s" % path)

    # Save the generated plot:
    fig.savefig(path)


def plot_four_statistics(axes, data, config, instrument, add_labels=False):
    point_size = int(config["Plots"]["point_size"])

    data_vars = set(data.vars())
    data_vars.remove("time")
    data_vars = list(data_vars)
    for i, ax in enumerate(axes.flatten()):
        ax.scatter(
            data["time"],
            data[data_vars[i]],
            s=point_size,
            label=instrument,
        )

        if add_labels:
            ax.set_title(data[data_vars[i]].attrs["description"])
            ax.set_ylabel(data[data_vars[i]].attrs["units"])


    # axes[0, 0].scatter(
    #     data["time"],
    #     data["cloud_coverage"].sum(axis=1),
    #     s=point_size,
    #     label=instrument,
    # )
    # axes[0, 1].scatter(
    #     data["time"],
    #     np.nanmean(data["cloud_mean_temperature"], axis=1),
    #     s=point_size,
    #     label=instrument,
    # )
    # axes[1, 0].scatter(
    #     data["time"],
    #     np.nanmin(data["cloud_min_temperature"], axis=1),
    #     s=point_size,
    #     label=instrument,
    # )
    # return axes[1, 1].scatter(
    #     data["time"],
    #     np.nanmax(data["cloud_max_temperature"], axis=1),
    #     s=point_size,
    #     label=instrument,
    # )


def _prepare_parameters(data):
    data["total_coverage"] = data["cloud_coverage"].sum(axis=1)
    del data["cloud_coverage"]#
    if "inhomogeneity" in data:
        del data["inhomogeneity"]
    if "cloud_inhomogeneity" in data:
        del data["cloud_inhomogeneity"]
    data["cloud_mean_temperature"] = \
        np.nanmean(data["cloud_mean_temperature"], axis=1)
    data["cloud_min_temperature"] = \
        np.nanmin(data["cloud_min_temperature"], axis=1)
    data["cloud_max_temperature"] = \
        np.nanmax(data["cloud_max_temperature"], axis=1)

    return data


def plot_comparison(datasets, config, start, end, ptype):
    logger.info("Plot %s from %s to %s" % (ptype, start, end))

    plt.rcParams.update({'font.size': 15})
    fig, axes = plt.subplots(
        2, 2, sharex=True, figsize=(16, 12), dpi=300
    )

    instruments = ["Pinocchio", "Dumbo"]
    for instrument in instruments:
        try:
            data = datasets[instrument+"-stats"].accumulate(start, end)
            data = data.limit_by("time", start, end)
            data = data.sort_by("time")
            data = _prepare_parameters(data)

            plot_four_statistics(axes, data, config, instrument)
        except Exception as err:
            logger.error("Could not plot %s!" % instrument, exc_info=True)

    fig.suptitle("%s %s (%s - %s)" % (
        ptype.capitalize(), "-".join(instruments), start, end
    ))
    axes[0, 0].set_xlim([start, end])
    axes[1, 0].set_xlabel("Time [UTC]")
    axes[1, 1].set_xlabel("Time [UTC]")

    # Show only every second xtick
    axes[1, 1].set_xticks(
        [xtick for i, xtick in enumerate(axes[1, 1].get_xticks())
         if i % 2 == 0]
    )

    for ax in axes.flatten():
        ax.grid()

    handles, labels = axes[1, 1].get_legend_handles_labels()
    fig.legend(handles, labels, 'upper left')

    path = datasets["plot-"+ptype].generate_filename(
        datasets["plot-"+ptype].files, start, end)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print("  Save to %s" % path)

    # Save the generated plot:
    fig.savefig(path,)


def get_cmd_line_parser():
    description = """Create plots for all instruments.\n

    This script can create plots of all datasets that are available, i.e.:
        - Ceilometer
        - DShip atmosphere variables
        - Dumbo instrument
        - Pinocchio instrument
    """

    examples = """
Examples:

    > %(prog)s -xcs "2017-11-02" "2017-11-03"
    Recommended usage: the program extracts the raw files from the 2nd November
    2017 (only necessary for Pinocchio files), converts them to netCDF files 
    and calculates the cloud statistics. If [instrument][mask] is set to a 
    valid filename, a mask will be applied on all images.

    > %(prog)s -xcs "2017-11-02 12:00:00" "2017-11-02 16:00:00"
    Same as above but processes only images recorded between 12 and 16 o'clock.

    > %(prog)s -cs -i Dumbo "2017-11-02" "2017-11-03"
    Process all Dumbo files from the 2nd November 2017.

    > %(prog)s -s "2017-11-02 12:00:00" "2017-11-02 16:00:00"
    Calculate the cloud statistics only (you need existing netCDF files that 
    you have converted earlier).
    """

    parser = argparse.ArgumentParser(
        description=description,
        epilog=examples,
        parents=[cloud.get_standard_parser()],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '-f', '--frequency', type=str, default=None,
        help="""
    You can split the time period given by START and END into smaller chunks, 
    e.g. to produce hourly or daily plots. To do so, set this option to a 
    string with the pattern "NR" where N is a number and R a 
    time frequency specifier (e.g. "1D" creates one plot for every day, 
    "2H" one plot for every two hours, "30T" one plot for every 30 minutes).
    """
    )
    parser.add_argument(
        '-o', '--overview', action='store_true',
        help='An overview plot will be created that presents all data '
             'from all instruments and datasets available. Saves the plots '
             'in the path that is set by [Plots][overview] config option.'
    )
    parser.add_argument(
        '-c', '--comparison', action='store_true',
        help='Create comparison plots for Dumbo and Pinocchio. Saves the plots'
             ' in the path that is set by [Plots][comparison] config option.'
    )
    parser.add_argument(
        '-a', '--anomaly', action='store_true',
        help='Create anomaly plots for Dumbo and Pinocchio. Saves the plots'
             ' in the path that is set by [Plots][anomaly] config option.'
    )

    return parser


def make_plots(datasets, config, args, start, end):
    if args.overview:
        plot_overview(datasets, config,
                      pd.Timestamp(start),
                      pd.Timestamp(end), )

    if args.comparison:
        plot_comparison(datasets, config,
                        pd.Timestamp(start),
                        pd.Timestamp(end), "comparison")

    if args.anomaly:
        plot_comparison(datasets, config,
                        pd.Timestamp(start),
                        pd.Timestamp(end), )


def main():
    # Parse all command line arguments and load the config file and the
    # datasets:
    config, args, datasets = cloud.init_toolbox(
        get_cmd_line_parser()
    )

    if args.frequency is not None:
        for period in pd.period_range(
                args.start, args.end, freq=args.frequency):

            make_plots(datasets, config, args,
                       period.start_time, period.end_time, )
    else:
        make_plots(datasets, config, args, args.start, args.end, )


if __name__ == '__main__':
    # Catch all warnings because they are annoying (especially from numpy)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main()
