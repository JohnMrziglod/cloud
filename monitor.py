#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script can create two types of plots:

* Overview plot: monitors all measurements of all instruments of a cruise
  including dship data, pinocchio, dumbo and ceilometer measurements.
* Comparison plot: shows all cloud parameters of the Dumbo and Pinocchio
  instruments.

"""

import argparse
import logging
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typhon.files import NoFilesError
import xarray as xr

import cloud


def sample(fileset, config, start, end, fields=None):
    """Helper function to get a sample from the data and change its time
    resolution.

    Args:
        fileset: A FileSet object.
        config: A dictionary-like object with configuration keys.
        start: Start time of the plot
        end: End time of the plot
        fields: Fields that you want to extract.

    Returns:
        An integer.
    """
    if fields is None:
        reader_args = {}
    else:
        reader_args = {
            "fields": fields,
        }

    data = xr.concat(fileset.collect(
        start, end, read_args=reader_args
    ), dim="time")
    data = data.sortby("time")
    print(data)
    data = data.sel(time=slice(start, end))

    print(start, end)

    if (end - start) > pd.Timedelta("7 days"):
        new_resolution = config["Plots"]["weekly_plots_average"]
    elif (end - start) > pd.Timedelta("24 hours"):
        new_resolution = config["Plots"]["daily_plots_average"]
    else:
        new_resolution = config["Plots"]["hourly_plots_average"]

    data = data.resample(new_resolution, dim="time")
    # data["time"] = data["time"].astype(datetime)
    return data


def plot_temperature(ax, start, end, filesets, config):
    """Plot temperature data on matplotlib axis.

    Args:
        ax: A matplotlib.axis object.
        start: Start time as string.
        end: End time as string.
        filesets: A DatasetManager object.
        config: A dictionary-like object with configuration keys.

    Returns:
        None
    """
    data = sample(filesets[config["General"]["metadata"]], config, start, end)
    point_size = int(config["Plots"]["point_size"])

    ax.scatter(
        data["time"].data, data["air_temperature"],
        s=point_size, label="Air")
    ax.scatter(
        data["time"].data,
        data["water_temperature"],
        s=point_size, label="Water")
    ax.legend()
    ax.set_ylabel("Temperature")


def plot_pressure(ax, start, end, filesets, config):
    """Plot DShip data on matplotlib axis.

    Args:
        ax: A matplotlib.axis object.
        start: Start time as string.
        end: End time as string.
        filesets: A DatasetManager object.
        config: A dictionary-like object with configuration keys.

    Returns:
        None
    """
    data = sample(filesets[config["General"]["metadata"]], config, start, end)
    point_size = int(config["Plots"]["point_size"])

    ax.scatter(
        data["time"].data,
        data["air_pressure"],
        s=point_size,
    )
    ax.set_ylabel("Pressure")


def plot_humidity(ax, start, end, filesets, config):
    """Plot DShip data on matplotlib axis.

    Args:
        ax: A matplotlib.axis object.
        start: Start time as string.
        end: End time as string.
        filesets: A DatasetManager object.
        config: A dictionary-like object with configuration keys.

    Returns:
        None
    """
    data = sample(filesets[config["General"]["metadata"]], config, start, end)
    point_size = int(config["Plots"]["point_size"])

    ax.scatter(
        data["time"].data,
        data["humidity"],
        s=point_size
    )
    ax.set_ylabel("Humidity")


def plot_cloud_coverage(ax, start, end, filesets, config, instrument):
    """Plot cloud coverage data on matplotlib axis.

    Args:
        ax: A matplotlib.axis object.
        start: Start time as string.
        end: End time as string.
        filesets: A DatasetManager object.
        config: A dictionary-like object with configuration keys.

    Returns:
        None
    """
    data = sample(filesets[instrument+"-stats"], config, start, end)
    point_size = int(config["Plots"]["point_size"])

    ax.scatter(
        data["time"].data,
        data["cloud_coverage"][:, 0],
        s=point_size
    )
    ax.scatter(
        data["time"].data,
        data["cloud_coverage"][:, 1],
        s=point_size, c="r"
    )
    ax.scatter(
        data["time"].data,
        data["cloud_coverage"][:, 2],
        s=point_size, c="k"
    )
    ax.legend(["Low", "Middle", "High"])
    ax.set_ylabel("Cloud coverage")
    ax.set_title(instrument)


def plot_dumbo(*args):
    """Plot Dumbo data on matplotlib axis.

    Args:
        *args: Arguments that will passed to :func:`plot_cloud_coverage`.

    Returns:
        None
    """
    plot_cloud_coverage(*args, "Dumbo")


def plot_pinocchio(*args):
    """Plot Pinocchio data on matplotlib axis.

    Args:
        *args: Arguments that will passed to :func:`plot_cloud_coverage`.

    Returns:
        None
    """
    plot_cloud_coverage(*args, "Pinocchio")


def plot_ceilometer(ax, start, end, filesets, config):
    """Plot ceilometer plot on matplotlib axis.

    Args:
        ax: A matplotlib.axis object.
        start: Start time as string.
        end: End time as string.
        filesets: A DatasetManager object.
        config: A dictionary-like object with configuration keys.

    Returns:
        None
    """

    data = sample(filesets["Ceilometer"], config, start, end,
                  fields=["cbh", "time"],)
    point_size = int(config["Plots"]["point_size"])

    ax.scatter(
        data["time"].data,
        data["cbh"][:, 0],
        s=point_size,
    )
    ax.scatter(
        data["time"].data,
        data["cbh"][:, 1],
        s=point_size
    )
    ax.scatter(
        data["time"].data,
        data["cbh"][:, 2],
        s=point_size
    )
    ax.legend(["Layer 1", "Layer 2", "Layer 3"])
    ax.set_ylabel("Cloud base height")
    ax.set_title("Ceilometer")


def plot_overview(filesets, config, start, end, ):
    """Create overview plot

    Args:
        filesets: A FileSetManager object.
        config: A dictionary-like object with configuration keys.
        start: Start time as string.
        end: End time as string.

    Returns:
        None
    """

    logging.info("Plot overview from %s to %s" % (start, end))

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
    no_data = True
    for i, plot in enumerate(plots.items()):
        name, plot_func = plot

        # Even if some error is raised during plotting we do not want it to
        # abort the whole script:
        try:
            plot_func(axes[i], start, end, filesets, config)
            no_data = False
        except NoFilesError as err:
            logging.warning(str(err))
        except Exception:
            logging.error("Could not create %s plot:" % name, exc_info=True)
        axes[i].grid()

    if no_data:
        logging.info("Skip this plot because there is no data!")
        return

    axes[0].set_title(
        f"Overview from {start.to_pydatetime()} to {end.to_pydatetime()}"
    )
    axes[-1].set_xlabel("Time")
    axes[-1].set_xlim([
        pd.Timestamp(start),
        pd.Timestamp(end),
    ])
    fig.tight_layout()

    # Save the generated plot:
    filename = filesets["plots"].get_filename(
        (start, end), fill={"plot": "overview"}
    )
    logging.info("Save plot to %s" % filename)
    filesets["plots"].write(fig, filename, in_background=True)


def plot_four_statistics(axes, data, config, instrument, add_labels=False):
    point_size = int(config["Plots"]["point_size"])

    data_vars = iter(data.data_vars.values())
    for i, ax in enumerate(axes.flatten()):
        var = next(data_vars)
        if add_labels:
            ax.set_title(var.attrs["description"])
            ax.set_ylabel(var.attrs["units"])

        ax.scatter(
            data["time"].data, var, s=point_size, label=instrument,
        )


def _prepare_parameters(data):
    """Prepare data parameters for plotting functions.

    Args:
        data: An GroupedArrays data object.

    Returns:
        The prepared data object
    """
    data["total_coverage"] = data["cloud_coverage"].sum(dim="level")
    del data["cloud_coverage"]
    if "inhomogeneity" in data:
        del data["inhomogeneity"]
    if "cloud_inhomogeneity" in data:
        del data["cloud_inhomogeneity"]
    data["cloud_mean_temperature"] = \
        data["cloud_mean_temperature"].mean(dim="level")
    data["cloud_min_temperature"] = \
        data["cloud_min_temperature"].min(dim="level")
    data["cloud_max_temperature"] = \
        data["cloud_max_temperature"].max(dim="level")

    return data


def plot_comparison(filesets, config, start, end, ptype):
    """Plot comparison plots.

    Args:
        filesets: A DatasetManager object.
        config: A dictionary-like object with configuration keys.
        start: Start time as string.
        end: End time as string.
        ptype:

    Returns:
        None
    """
    logging.info("Plot %s from %s to %s" % (ptype, start, end))

    plt.rcParams.update({'font.size': 15})
    fig, axes = plt.subplots(
        2, 2, sharex=True, figsize=(16, 12), dpi=300
    )

    instruments = ["Pinocchio", "Dumbo"]
    no_data = True
    for instrument in instruments:
        try:
            data = sample(
                filesets[instrument+"-stats"], config, start, end
            )
            data = _prepare_parameters(data)

            plot_four_statistics(axes, data, config, instrument)
            no_data = False
        except NoFilesError as err:
            logging.warning(str(err))
        except Exception as err:
            logging.error("Could not create %s plot:" % instrument,
                          exc_info=True)

    if no_data:
        logging.info("Skip this plot because there is no data!")
        return

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

    # Save the generated plot:
    filename = filesets["plots"].get_filename(
        (start, end), fill={"plot": "comparison"}
    )
    logging.info("Save plot to %s" % filename)
    filesets["plots"].write(fig, filename)


def get_cmd_line_parser():
    description = """Create plots for all instruments.\n

    This script can create plots of all filesets that are available, i.e.:
        - Ceilometer
        - DShip atmosphere variables
        - Dumbo instrument
        - Pinocchio instrument
    """

    examples = """
Examples:

    > ./%(prog)s -o "2017-11-03" "2017-11-10"
    Plot an overview of all instruments from 2017-11-02 to 2017-11-10.
    
    > ./%(prog)s -c "2017-11-03" "2017-11-04"
    Plot a comparison of Dumbo and Pinocchio instrument from the 3rd of 
    November 2017.

    > ./%(prog)s -of 3H "2017-11-03" "2017-11-10"
    Same as above but instead of creating one plot for the full time period,
     we create one plot for every three hours. For this, we are using the 
    frequency (-f) option.
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
             'from all instruments and filesets available. Saves the plots '
             'in the path that is set by [Plots][overview] config option.'
    )
    parser.add_argument(
        '-c', '--comparison', action='store_true',
        help='Create comparison plots for Dumbo and Pinocchio. Saves the plots'
             ' in the path that is set by [Plots][comparison] config option.'
    )
    parser.add_argument(
        '-a', '--anomaly', action='store_true',
        help='Note: DEPRECATED at the moment! Create anomaly plots for '
             'Dumbo and Pinocchio. Saves the plots in the path that is set by '
             '[Plots][anomaly] config option.'
    )

    return parser


def make_plots(filesets, config, args, start, end):
    """Call the plotting functions for the plots requested by *args*.

    Args:
        filesets: A DatasetManager object.
        config: A dictionary-like object with configuration keys.
        args: An argparse object.
        start: Start time as string.
        end: End time as string.

    Returns:

    """
    if args.overview:
        plot_overview(filesets, config,
                      pd.Timestamp(start),
                      pd.Timestamp(end), )

    if args.comparison:
        plot_comparison(filesets, config,
                        pd.Timestamp(start),
                        pd.Timestamp(end), "comparison")

    if args.anomaly:
        plot_comparison(filesets, config,
                        pd.Timestamp(start),
                        pd.Timestamp(end), "anomaly")


def main():
    # Parse all command line arguments and load the config file and the
    # filesets:
    config, args, filesets = cloud.init_toolbox(
        get_cmd_line_parser()
    )

    if args.frequency is not None:
        for period in pd.period_range(
                args.start, args.end, freq=args.frequency):

            make_plots(filesets, config, args,
                       period.start_time, period.end_time, )
    else:
        make_plots(filesets, config, args, args.start, args.end, )


if __name__ == '__main__':
    # Catch all warnings because they are annoying (especially from numpy)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        main()
