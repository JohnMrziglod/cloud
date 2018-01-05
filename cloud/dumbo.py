from datetime import datetime

import numpy as np
from typhon.spareice.array import Array
from typhon.spareice.handlers import FileHandler, FileInfo

from cloud import ThermalCamMovie

__all__ = [
    "ThermalCamASCII",
]


class ThermalCamASCII(FileHandler):
    """ This class can read thermal cam ASCII files of the Dumbo instrument.
    """

    def __init__(self, **kwargs):
        # Call the base class initializer
        super(ThermalCamASCII, self).__init__(**kwargs)

    def get_info(self, filename, **kwargs):
        """ Get info parameters from a file (time coverage, etc).

        Args:
            filename: Name of the file.

        Returns:
            A FileInfo object.
        """

        with open(filename, "r") as f:
            timestamp = self._get_timestamp(f)

            return FileInfo(filename, [timestamp, timestamp],)

    @staticmethod
    def _get_timestamp(file):
        date_time = file.readline().rstrip('\n').split('\t')[1]
        return datetime.strptime(date_time, "%d.%m.%Y %H:%M:%S")

    def read(self, filename, **kwargs):
        """
        Loads an ASCII file and converts it to cloud.ThermalCamMovie object.

        Args:
            filename: Path and name of the file

        Returns:
            A cloud.ThermalCamMovie object.
        """

        with open(filename, "r") as f:
            timestamp = self._get_timestamp(f)

            # Unfortunately, the ASCII files contain commas instead of points
            # as decimal delimiter:
            line_iterator = (
                line.replace(',', '.').encode()
                for line in f
            )

            data = np.genfromtxt(
                line_iterator,
                delimiter='\t',
                dtype=float,
                # We skipped already the first line in _get_timestamp, so only
                # two header lines are left.
                skip_header=2,
            )

            movie = ThermalCamMovie()

            # We skip the first column since it only contains the row number.
            movie["images"] = Array(
                [data[:, 1:]], dims=["time", "height", "width"]
            )
            movie["time"] = [timestamp]

            return movie
