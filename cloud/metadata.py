import pandas as pd
from typhon.spareice.handlers import CSV

__all__ = [
    "ShipMSM",
]


class ShipMSM(CSV):
    """ This class can read ship meta data files from the RV Maria S. Merian in
    the CSV format.
    """

    def __init__(self):
        # Call the base class initializer
        super(ShipMSM, self).__init__(
            delimiter="\t",
            header=1,
            skip_header=1
        )

    def read(self, filename, fields=None):
        data = super(ShipMSM, self).read(filename, fields)
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

        # Filter out error values.
        data = data[data["air_temperature"] < 99]
        data = data[data["air_pressure"] > 500]

        return data

