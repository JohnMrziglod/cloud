import datetime

import cloud.handlers
from cloud.image import ThermoCamImage
import numpy as np

__all__ = [
    "ThermoCamASCIIFile",
]

class ThermoCamASCIIFile(cloud.handlers.FileHandler):
    """ This class can read thermal cam ASCII files of the Dumbo instrument.


    """

    def __init__(self, **kwargs):
        # Call the base class initializer
        cloud.handlers.FileHandler.__init__(self, **kwargs)

    def get_info(self, filename):
        """ Get info parameters from a file (time coverage, etc).

        Args:
            filename:

        Returns:
            A dictionary with info parameters.
        """

        with open(filename, "r") as f:
            date_time = f.readline().rstrip('\n').split('\t')[1]

            info = {
                "times": [
                    datetime.datetime.strptime(date_time, "%d.%m.%Y %H:%M:%S"),
                    datetime.datetime.strptime(date_time, "%d.%m.%Y %H:%M:%S")
                ],
            }

            return info


    def read(self, filename, fields=None):
        """
        Loads an ASCII file and converts it to np.array.

        Args:
            filename: Path and name of file

        Returns:
            numpy.array
        """

        data = None

        with open(filename, "r") as f:
            data = np.genfromtxt(
                # Okay, what are we doing here? We need a numpy array from an ascii file. numpy.genfromtxt() expects as
                # first argument an iterable argument (see http://stackoverflow.com/a/18744706). We give it by looping
                # over all lines from the file. Since we want to skip the first line (it just contains indices), we
                # split up each line along its delimiter, skip the first column and put them with the delimiter together
                # again. Our ASCII data contains commas as decimal delimiter, we have to replace them here as well.
                ("\t".join(line.split('\t')[1:]).replace(',', '.').encode() for line in f),
                delimiter='\t',
                dtype=None,
                skip_header=3
            )

        return ThermoCamImage(data)