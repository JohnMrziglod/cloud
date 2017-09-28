import numpy as np

import cloud.handlers

__all__ = [
    "ShipDataFile",
]

class ShipDataFile(cloud.handlers.FileHandler):
    """ This class can read ship meta data files in the CSV format.


    """

    def __init__(self, **kwargs):
        # Call the base class initializer
        cloud.handlers.FileHandler.__init__(self, **kwargs)

    def get_info(self, filename):
        """

        Args:
            filename:

        Returns:
            A dictionary with info parameters.
        """
        pass


    def read(self, filename, fields=None):
        """Loads a ship meta data file and loads its to a numpy array.

        Args:
            filename: Path and name of file

        Returns:
            numpy.array
        """

        data = None

        with open(filename, "r", encoding="ISO-8859-1") as f:
            # The header information is in the second line:
            f.readline()
            line = f.readline()
            available_fields = line.split(";")
            columns = []
            for field in fields:
                if field == "timestamp":
                    # The timestamp column does not have any label in the header. It is always the first column.
                    columns.append(0)
                else:
                    columns.append(available_fields.index(field))

            data = np.genfromtxt(
                # Okay, what are we doing here? We need a numpy array from an ascii file. numpy.genfromtxt() expects as
                # first argument an iterable argument (see http://stackoverflow.com/a/18744706). We give it by looping
                # over all lines from the file.
                (line.encode('utf-8') for line in f),
                delimiter=';',
                usecols=columns,
                dtype=None,
                skip_header=2
            )

        return data.T