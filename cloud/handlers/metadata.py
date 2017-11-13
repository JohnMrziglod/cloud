from datetime import datetime

from typhon.spareice.handlers.common import CSV

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
            skip_header=4
        )

    def read(self, filename, fields=None):
        data = super(ShipMSM, self).read(filename, fields)
        data.rename({
            "Weatherstation.PDWDA.Air_pressure": "air_pressure",
            "Weatherstation.PDWDA.Air_temperature": "air_temperature",
            "Weatherstation.PDWDA.Humidity": "humidity",
            "Weatherstation.PDWDA.Water_temperature": "water_temperature",
        })
        data["time"] = \
            [datetime.strptime(str(dt, "utf-8"), "%Y/%m/%d %H:%M:%S")
             for dt in data["date time"]]
        data.drop(("date time",))

        return data

