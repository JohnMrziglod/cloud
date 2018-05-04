import pandas as pd
from typhon.files import CSV, expects_file_info

__all__ = [
    "ShipMSM",
    "ShipPS",
]


class ShipMSM(CSV):
    """ This class can read ship meta data files (DShip) from the RV Maria S.
    Merian in CSV format.
    """

    def __init__(self):
        # Call the base class initializer
        super(ShipMSM, self).__init__()

    @expects_file_info()
    def read(self, filename, fields=None, **read_csv):
        """Read a file in CSV format coming from DShip of RV Maria S. Merian.

        Args:
            filename: Path and name of file or FileInfo object.
            fields: Field that you want to extract from the file. If not given,
                all fields are going to be extracted.
            **read_csv: Additional keyword arguments for the pandas function
                `pandas.read_csv`. See for more details:
                https://pandas.pydata.org/pandas-docs/stable/generated/pandas.read_csv.html

        Returns:
            A xarray.Dataset object.
        """
        read_csv = {
           "delimiter": "\t",
           # This should be the column where the date time string is,
           # in this case 0:
           "parse_dates": {"time": [0]},
           "index_col": 0,
           # "header": 1,
        }

        # Call the reading routine from the base class
        data = super(ShipMSM, self).read(filename, **read_csv)

        # Probably, these field names will change for each ship. So, look at
        # one CSV file and try to find those fields to rename them:
        data.rename({
            "Weatherstation.PDWDA.Air_pressure": "air_pressure",
            "Weatherstation.PDWDA.Air_temperature": "air_temperature",
            "Weatherstation.PDWDA.Humidity": "humidity",
            "Weatherstation.PDWDA.Water_temperature": "water_temperature",
        }, inplace=True)

        # Filter out error values. The error values might be different for each
        # ship. Adjust these lines then:
        data = data.isel(
            time=(data.air_temperature < 99) & (data.air_pressure > 500))

        if fields is not None:
            data = data[fields]

        return data.sortby("time")


# This is an example how to create another file reader:
class ShipPS(CSV):
    """ This class is a draft of a file handler for reading DShip data from the
    RV Polarstern. This class has to be reviewed (and probably revised) before
    using it.
    """

    def __init__(self):
        # Call the base class initializer
        super(ShipPS, self).__init__()

    @expects_file_info()
    def read(self, filename, fields=None, **read_csv):
        """Read a file in CSV format coming from DShip of RV Polarstern.

        Args:
            filename: Path and name of the file.
            fields: Field that you want to extract from the file. If not given,
                all fields are going to be extracted.
            **read_csv: Additional keyword arguments for the pandas function
                `pandas.read_csv`. See for more details:
                https://pandas.pydata.org/pandas-docs/stable/generated/pandas.read_csv.html

        Returns:
            An GroupedArrays object.
        """
        read_csv = {
            "delimiter": "\t",
            # "header": 1,
        }

        data = super(ShipPS, self).read(filename, fields, **read_csv)

        # Probably, these field names will change for each ship. So, look at
        # one CSV file and try to find those fields to rename them here:
        data.rename({
            "Weatherstation.PDWDA.Air_pressure": "air_pressure",
            "Weatherstation.PDWDA.Air_temperature": "air_temperature",
            "Weatherstation.PDWDA.Humidity": "humidity",
            "Weatherstation.PDWDA.Water_temperature": "water_temperature",
        })
        data["time"] = pd.to_datetime(
            [dt.decode("utf-8") for dt in data["date time"]]
        )
        data.drop(("date time",))

        # Filter out error values. The error values might be different for each
        # ship. Adjust these lines then:
        data = data[data["air_temperature"] < 99]
        data = data[data["air_pressure"] > 500]

        return data
