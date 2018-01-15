from datetime import datetime
import logging
from time import time

import numpy as np
import pandas as pd
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

        timestamp = self._get_timestamp(filename)
        return FileInfo(filename, [timestamp, timestamp],)

    @staticmethod
    def _get_timestamp(filename):
        try:
            with open(filename) as file:
                # Reads the first line of the file and split it by the
                # tabulator. Convert the second half into a datetime object and
                # return it.
                date_time = file.readline().rstrip('\n').split('\t')[1]
                return datetime.strptime(date_time, "%d.%m.%Y %H:%M:%S")
        except Exception:
            logging.error(
                "Tried to derive file timestamp from Dumbo raw file '%s'. "
                "Check whether its first line has this pattern:"
                "'{name-of-original-file}	DD.MM.YYYY hh:mm:ss'!" %
                filename,
                exc_info=True
            )

    def read(self, filename, **kwargs):
        """
        Loads an ASCII file and converts it to cloud.ThermalCamMovie object.

        Args:
            filename: Path and name of the file

        Returns:
            A cloud.ThermalCamMovie object.
        """

        dataframe = pd.read_csv(
            filename, decimal=",", delimiter='\t',
            # There are 384 columns but the first contains the index.
            usecols=range(1, 385), dtype=float,
            engine="c", header=1,
        )

        timestamp = self._get_timestamp(filename)
        movie = ThermalCamMovie()

        # We skip the first column since it only contains the row number.
        movie["images"] = Array(
            [dataframe.as_matrix()], dims=["time", "height", "width"]
        )
        movie["time"] = [timestamp]

        return movie
