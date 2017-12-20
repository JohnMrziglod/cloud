from datetime import datetime

import numpy as np
from typhon.spareice.handlers import FileHandler

from cloud.image import ThermoCamImage

__all__ = [
    "ThermoCamASCII",
]


class ThermoCamASCII(FileHandler):
    """ This class can read thermal cam ASCII files of the Dumbo instrument.
    """

    def __init__(self, **kwargs):
        # Call the base class initializer
        super(ThermoCamASCII, self).__init__(**kwargs)

    def get_info(self, filename, **kwargs):
        """ Get info parameters from a file (time coverage, etc).

        Args:
            filename:

        Returns:
            A dictionary with info parameters.
        """

        with open(filename, "r") as f:
            timestamp = self._get_timestamp(f)

            info = {
                "times": [
                    timestamp,
                    timestamp,
                ],
            }

            return info

    @staticmethod
    def _get_timestamp(file):
        date_time = file.readline().rstrip('\n').split('\t')[1]
        return datetime.strptime(date_time, "%d.%m.%Y %H:%M:%S")

    def read(self, filename, **kwargs):
        """
        Loads an ASCII file and converts it to np.array.

        Args:
            filename: Path and name of file

        Returns:
            numpy.array
        """

        data = None

        with open(filename, "r") as f:
            timestamp = self._get_timestamp(f)

            data = np.genfromtxt(
                # TODO: Replace this code with something readable!
                # Okay, what are we doing here? We need a numpy array from an
                # ascii file. numpy.genfromtxt() expects as first argument an
                # iterable argument (see http://stackoverflow.com/a/18744706).
                # We give it by looping over all lines from the file. Since we
                # want to skip the first line (it just contains indices), we
                # split up each line along its delimiter, skip the first column
                # and put them with the delimiter together again. Our ASCII
                # data contains commas as decimal delimiter, we have to replace
                # them here as well.
                ("\t".join(line.split('\t')[1:]).replace(',', '.').encode() for line in f),
                delimiter='\t',
                dtype=None,
                # We skipped already the first line in _get_timestamp, so only
                # two header lines are left.
                skip_header=2
            )

        return ThermoCamImage(data, time=timestamp)
