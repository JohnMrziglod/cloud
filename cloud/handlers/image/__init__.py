# -*- coding: utf-8 -*-

"""All handler modules."""

import cloud.handlers
import cloud.image
from netCDF4 import Dataset, num2date, date2num

__all__ = [
    'ThermoCamImage',
    'WebCamImage',
]


class ThermoCamImage(cloud.handlers.FileHandler):

    def __init__(self, fmt="netcdf", **kwargs):
        """ File handler class that can be used to convert thermal cam files and convert them to PNG or netcdf files.
        Note: If you convert them to PNG files, this handler cannot read them. Choose "netcdf" as format if you want to
        process the data.

        Args:
            fmt: Format of the files. Can be either "netcdf" or "png". Default is "netcdf".
            **kwargs: None

        Examples:

        .. :code-block:: python

            from cloud.handlers.image import ThermoCamImage
            import cloud.handlers.image.pinocchio as pinocchio

            pinocchio_fh = pinocchio.ThermoCamFile("path/to/calibration_file.csv")
            image = pinocchio_fh.read("pinocchio_image.jpg")

            thermocam_fh = ThermoCamImage(fmt="png")
            thermocam_fh.write("pinocchio_image.png", image)
        """

        # Call the base class initializer
        cloud.handlers.FileHandler.__init__(self, **kwargs)

        self.fmt = fmt

    def get_info(self, filename):
        info = {}

        if self.fmt == "netcdf":
            file = Dataset(filename, "r", format="NETCDF4")
            time = num2date(file["times"][0], file["times"].units)
            info["times"] = [
                time,
                time
            ],

        return info

    def read(self, filename, **kwargs):
        if self.fmt == "netcdf":
            return cloud.image.ThermoCamImage.from_file(filename)
        else:
            raise NotImplementedError("No reading support for %s" % self.fmt)

    def write(self, filename, data, **kwargs):
        data.to_file(filename, self.fmt)


class WebCamImage(cloud.handlers.FileHandler):

    def __init__(self, **kwargs):
        # Call the base class initializer
        cloud.handlers.FileHandler.__init__(self, **kwargs)

    def get_info(self, filename):
        pass

    def read(self, filename, **kwargs):
        pass

    def write(self, filename, data, **kwargs):
        data.save(filename)