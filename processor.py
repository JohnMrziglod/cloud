#!/usr/bin/env python3

"""
This script does a part of the whole workflow for Pinocchio or Dumbo data,
including:

1. Extraction of tar zipped files (only for Pinocchio).
2. Conversion of raw files (JPG when Pinocchio, ASCII when Dumbo) into netCDF
   format.
3. Masking parts of the images according to a given mask.
4. Calculation of cloud parameters (DShip data needed).

"""

import argparse
import logging
import logging.config
import os.path
import shutil
import tarfile

import cloud


def extract_raw_files(datasets, config, start, end, convert=False):
    """Extract the archive files from Pinocchio

    Args:
        datasets: A DatasetManager object.
        config: A dictionary-like object with configuration keys.
        start: Start time as string.
        end: End time as string.
        convert: If true, the files will be also converted and afterwards
            deleted.

    Returns:
        None
    """

    for archive in datasets["Pinocchio-archive"].find_files(start, end):
        logging.info("Extract all files from %s" % archive.path)
        archive_file = tarfile.open(archive, mode="r:gz")
        tmpdir = os.path.splitext(archive)[0]
        archive_file.extractall(path=tmpdir)

        if convert:
            cloud.convert_raw_files(datasets, "Pinocchio", config, start, end)

            logging.info("Delete extracted files.")
            shutil.rmtree(tmpdir)


def get_cmd_line_parser():
    description = """Process Pinocchio or Dumbo images.\n
    
    This script can extract the raw images from its daily tarball archives (
    only necessary for Pinocchio images), convert them to hourly bundled netCDF
    files and calculate cloud statistics for them.
    
    For calculating cloud statistics a DShip dataset is required since it needs
    the air temperature.
    """

    examples = """Examples:
    
    > ./%(prog)s -xcs "2017-11-02" "2017-11-03"
    Recommended usage: the program extracts the raw files from the 2nd November
    2017 (only necessary for Pinocchio files), converts them to netCDF files 
    and calculates the cloud statistics. If [instrument][mask] is set to a 
    valid filename, a mask will be applied on all images.
    
    > ./%(prog)s -xcs "2017-11-02 12:00:00" "2017-11-02 16:00:00"
    Same as above but processes only images recorded between 12 and 16 o'clock.
    
    > ./%(prog)s -cs -i Dumbo "2017-11-02" "2017-11-03"
    Process all Dumbo files from the 2nd November 2017.
    
    > ./%(prog)s -s "2017-11-02 12:00:00" "2017-11-02 16:00:00"
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
        '-i', '--instrument', type=str, choices=["Pinocchio", "Dumbo"],
        default="Pinocchio",
        help='The instrument which files should be processed.'
    )
    parser.add_argument(
        '-x', '--extract', action='store_true',
        help='The raw images will be extracted from the original archives. '
             'Note: This option will be ignored for instruments other than '
             'Pinocchio. Uses the [Pinocchio][archive_files] config option.'
    )
    parser.add_argument(
        '-c', '--convert', action='store_true',
        help='The raw images will be converted to netCDF files. Uses the '
             '[instrument][files_in_archive] config option.'
    )
    parser.add_argument(
        '-s', '--stats', action='store_true',
        help='Calculate cloud statistics for each image. This action needs the'
             ' air temperature from the DShip dataset (set via '
             '[DShip][files]). Saves the statistics to the path in '
             '[instrument][stats].'
    )

    return parser


def main():
    # Parse all command line arguments and load the config file and the
    # datasets:
    config, args, datasets = cloud.init_toolbox(
        get_cmd_line_parser()
    )

    actions = [
        ["Start date:", str(args.start)],
        ["End date:", str(args.end)],
        ["Instrument:", str(args.instrument)],
        ["Extract:", str(args.extract)],
        ["Convert:", str(args.convert)],
        ["Statistics:", str(args.stats)],
    ]

    logging.info("Script configuration:")
    for i, action in enumerate(actions):
        print("    {:<15} {:<12}".format(*action))

    if args.extract and args.instrument == "Pinocchio":
        extract_raw_files(datasets, config, args.start, args.end, args.convert)
    elif args.convert:
        cloud.convert_raw_files(
            datasets, args.instrument, config, args.start, args.end)

    if args.stats:
        cloud.calculate_cloud_statistics(
            datasets, args.instrument, config, args.start, args.end)


if __name__ == "__main__":
    main()
