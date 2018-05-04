import datetime

from typhon.files import expects_file_info, FileHandler, FileInfo
import numpy as np
import PIL.Image
from PIL.ExifTags import TAGS
from scipy.optimize import curve_fit
import xarray as xr

__all__ = [
    "ThermalCam",
    #"WebCam"
]


def polynom_second(x, a, b, c):
    return a * np.square(x) + b * x + c


def get_calibration(brightness, temperature):
    """

    Args:
        brightness:
        temperature:

    Returns:
        A tuple of two elements: calibration coefficients and covariance
        matrix.
    """
    return curve_fit(polynom_second, brightness, temperature, maxfev=1500)


def brightness_to_temperature(brightness, calibration_coefficients):
    """

    Args:
        brightness:
        calibration_coefficients:

    Returns:

    """
    return polynom_second(brightness, *calibration_coefficients)


class ThermalCam(FileHandler):
    calibration_coefficients = None

    def __init__(self, calibration_file=None, to_temperatures=True,
                 **kwargs):
        """ This class can read thermal cam images of the Pinocchio instrument.

        Args:
            calibration_file: Name of the calibration file in CSV format. The
                file should contain two columns which are separated by
                semicolon. The first denotes the pixel value (between 0 and
                255) and the second denotes the corresponding temperature. This
                reader will fit a curve to those calibration values and convert
                all pixels of a thermal cam image according to it.
            **kwargs: Additional keyword arguments for FileHandler base class.
        """
        # Call the base class initializer
        super(ThermalCam, self).__init__(**kwargs)

        self.to_temperatures = to_temperatures

        if self.to_temperatures and calibration_file is None:
                raise ValueError(
                    "For converting to temperatures a calibration file is "
                    "needed! Look at the documentation of the parameter "
                    "calibration_file for more information.")

        if calibration_file is not None:
            # Load the calibration data and calculate the pixel_to_temperature
            # function:
            data = np.genfromtxt(
                calibration_file,
                delimiter=';',
                dtype=None,
                skip_header=1
            )
            ThermalCam.calibration_coefficients, _ = \
                get_calibration(data[:, 0], data[:, 1])

    @expects_file_info()
    def get_info(self, filename, **kwargs):
        """Get the time coverage from a Pinocchio JPG image.

        Args:
            filename: Path and name of file or FileInfo object.

        Returns:
            A FileInfo object.
        """

        # read image
        image = PIL.Image.open(filename, 'r')

        name2tagnum = dict((name, num) for num, name in TAGS.items())
        time_string = image._getexif()[name2tagnum["DateTimeOriginal"]]
        time = datetime.datetime.strptime(time_string, "%Y:%m:%d %H:%M:%S")

        return FileInfo(
            filename
            [time, time],
        )

    @expects_file_info()
    def read(self, file, **kwargs):
        """Read an JPG image and convert it to a cloud.ThermalCamMovie object.

        Args:
            file: Path and name of file or FileInfo object.

        Returns:
            Either a cloud.ThermalCamMovie or a cloud.Movie object.
        """

        # read image
        image = PIL.Image.open(file.path, 'r')

        # Retrieve the time via EXIF tags
        name2tagnum = dict((name, num) for num, name in TAGS.items())
        if image._getexif() is None:
            time = None
        else:
            time_string = image._getexif()[name2tagnum["DateTimeOriginal"]]
            time = datetime.datetime.strptime(time_string, "%Y:%m:%d %H:%M:%S")

        if self.to_temperatures:
            # convert it to a grey scale image
            data = np.float32(np.array(image.convert('L')))
            data = np.flipud(data)
            data = brightness_to_temperature(
                data, self.calibration_coefficients)
        else:
            data = np.float32(np.array(image.convert('RGB')))

        movie = xr.Dataset()
        movie["images"] = xr.DataArray(
            [data], dims=["time", "height", "width"]
        )
        movie["time"] = "time", [time]

        return movie


# class WebCam(FileHandler):
#     """ This class can read web cam images of the Pinocchio instrument.
#
#
#     """
#
#     def __init__(self, **kwargs):
#
#         # Call the base class initializer
#         super(WebCam, self).__init__(**kwargs)
#
#     def get_info(self, filename):
#         """
#
#         Args:
#             filename:
#
#         Returns:
#             A dictionary with info parameters.
#         """
#         ...
#
#     def read(self, filename):
#         """
#         Reads an image and converts it to np.array.
#
#         Args:
#             filename: Path and name of file
#
#         Returns:
#             Image
#         """
#
#         # read image
#         image = PIL.Image.open(filename, 'r')
#
#         # convert it to a grey scale image
#         #data = np.float32(np.array(image.convert('L')))
#
#         data = np.float32(np.array(image))
#
#         # black pixels = NaN
#         #data[data == 0] = np.nan
#
#         return Movie(data)
#
#
# class WebCamFishEye(WebCam):
#     def __init__(self, **kwargs):
#         super(WebCamFishEye, self).__init__(**kwargs)
#
#     def read(self, filename):
#         image = super(WebCamFishEye, self).read(filename)
#
#         #image.distortion()