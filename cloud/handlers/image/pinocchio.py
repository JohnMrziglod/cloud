import csv
import datetime
import glob
import os

import cloud.handlers
from cloud.image import ThermoCamImage, Image
import numpy as np
import PIL.Image
from PIL.ExifTags import TAGS
from scipy.optimize import curve_fit


__all__ = [
    "create_calibration_file",
    "ThermoCamFile",
    "WebCamFile"
]


def polynom_second(x, a, b, c):
    return a * np.square(x) + b * x + c


def get_calibration(brightness, temperature):
    """

    Args:
        brightness:
        temperature:

    Returns:
        A tuple of two elements: calibration coefficients and covariance matrix.
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


def create_calibration_file(calibration_images_path, temperature_file, calibration_file, mask, plot_file=None):
    """ This function creates a calibration file for the pinocchio thermal cam from the calibration images. The created
    file is in CSV format and can be used as calibration for the cloud.handler.pinocchio.ThermoCamFile() file handler
    class.

    Args:
        calibration_images_path: A path to the directories which contain the thermal cam images for each temperature.
            They should be named after the first column in the file given by temperature_file.
        temperature_file: A CSV file with two header lines and at least two columns separated by semicolons. The first
            columns describes the directory name where to find the image files (relative to calibration_images_path).
            The second is the corresponding temperature in the calibration (normally recorded by a KT19 pyranometer).
        calibration_file: Name of the created output file.
        mask: A numpy.mask that only shows the area where the calibration target is.
        plot_file: (optional) If this is given, a plot with the calibration curve will be stored in this file.

    Returns:
        None

    Examples:

    .. :code-block::
        :caption: ls pinocchio/calibration/images/

        30/
        28/
        26/

    .. :code-block::
        :caption: temperature_file.csv

        header line no. 1
        header line no.2
        30;29.6
        28;28.1
        26;25.9
        ...

    .. :code-block:: python
        :caption: script.py

        # Create the calibration file once
        create_calibration_file("pinocchio/calibration/images/", "temperature_file.csv", "pixel_to_temperature.csv")

        # Use it for converting pinocchio images:
        pinocchio_handler = cloud.handlers.pinocchio.ThermoCamFile(calibration_file="pixel_to_temperature.csv")
    """

    directory_temperature = dict()

    with open(temperature_file, 'r') as file:
        reader = csv.reader(file, delimiter=';')

        # skip the header (two lines)
        reader.__next__()
        reader.__next__()

        for row in reader:
            directory_temperature[row[0]] = float(row[1])

    pinocchio_handler = cloud.handlers.image.pinocchio.ThermoCamFile()

    temperature_pixel = dict()

    for directory, temperature in sorted(directory_temperature.items()):
        files = glob.glob(calibration_images_path + directory + "/*")
        values = np.ones(len(files))
        for i, file in enumerate(files):
            image = pinocchio_handler.read(file, convert_to_temperatures=False)
            image.to_brightness()
            image.apply_mask(mask)
            # values[i] = data[data.shape[0]/2][data.shape[1]/2]
            values[i] = np.nanmedian(image.data)  # [data.shape[0] / 2][data.shape[1] / 2]
        temperature_pixel[temperature] = np.nanmedian(values)

    curve = True
    if curve:
        temperatures = np.asarray([k for k in sorted(temperature_pixel)])
        pixels = np.asarray([temperature_pixel[k] for k in sorted(temperature_pixel)])
        print(pixels, temperatures)
        coeffs, _ = get_calibration(pixels, temperatures)
        print(coeffs)

        # Save the plot of the calibration curve:
        if plot_file is not None:
            import matplotlib.pyplot as plt
            plt.plot(np.linspace(50, 255), brightness_to_temperature(np.linspace(50, 255), coeffs), c="g")
            plt.hold(True)
            plt.plot(pixels, temperatures)
            plt.ylabel("calibration temperature [°C]")
            plt.xlabel("pixel brightness")
            plt.title("Pinocchio calibration, 5th September 2017")
            plt.grid()
            plt.legend(["T = {:.4f} X**2 + {:.2f} X + {:.2f}".format(*coeffs), "calibration"], loc='upper left')
            plt.savefig(plot_file)

    else:

        temperatures = np.asarray([k for k in sorted(temperature_pixel)])
        pixels = np.asarray([temperature_pixel[k] for k in sorted(temperature_pixel)])
        print(pixels, temperatures)

        relation = np.poly1d(np.polyfit(pixels, temperatures, 1))

        # Save the plot of the calibration curve:
        if plot_file is not None:
            import matplotlib.pyplot as plt
            plt.plot(np.linspace(50, 255), relation(np.linspace(50, 255)), c="g")
            plt.hold(True)
            plt.plot(pixels, temperatures)
            plt.ylabel("calibration temperature [°C]")
            plt.xlabel("pixel brightness")
            plt.title("Pinocchio calibration, 5th September 2017")
            plt.grid()
            plt.legend(["T = {:.4f} * X + {:.2f}".format(*relation.coeffs), "calibration"], loc='upper left')
            plt.savefig(plot_file)

    # Save the calibration in a file:
    with open(calibration_file, 'w') as file:
        file.write("Pixel Value[0-255];Temperature[deg C]\n")
        for temperature, pixel in sorted(temperature_pixel.items()):
            file.write("{};{}\n".format(pixel, temperature))


class ThermoCamFile(cloud.handlers.FileHandler):
    calibration_coefficients = None

    def __init__(self, calibration_file=None, **kwargs):
        """ This class can read thermal cam images of the Pinocchio instrument.

        Args:
            calibration_file: Name of the calibration file in CSV format. The file should contain two columns which are
                separated by semicolon. The first denotes the pixel value (between 0 and 255) and the second denotes the
                corresponding temperature. This reader will fit a curve to those calibration values and convert all
                pixels of a thermo cam image according to it.
            **kwargs:
        """
        # Call the base class initializer
        cloud.handlers.FileHandler.__init__(self, **kwargs)

        if calibration_file is not None:
            # Load the calibration data and calculate the pixel_to_temperature function:
            data = np.genfromtxt(
                calibration_file,
                delimiter=';',
                dtype=None,
                skip_header=1
            )
            ThermoCamFile.calibration_coefficients, _ = get_calibration(data[:, 0], data[:, 1])

    def get_info(self, filename):
        """
        Sollte mit EXIF Daten funktionieren, das kann man mit PIL machen:
        https://stackoverflow.com/questions/4764932/in-python-how-do-i-read-the-exif-data-for-an-image

        Args:
            filename:

        Returns:
            A dictionary with info parameters.
        """

        # read image
        image = PIL.Image.open(filename, 'r')

        name2tagnum = dict((name, num) for num, name in TAGS.items())
        time_string = image._getexif()[name2tagnum["DateTimeOriginal"]]
        time = datetime.datetime.strptime(time_string, "%Y:%m:%d %H:%M:%S")

        info = {
            "times" : [time, time],
        }

        return info

    def read(self, filename, fields=None, convert_to_temperatures=True):
        """
        Reads an image and converts it to np.array.

        Args:
            filename: Path and name of file

        Returns:
            Either a cloud.image.ThermoCamImage or a cloud.image.Image object.
        """

        print(filename)

        # read image
        image = PIL.Image.open(filename, 'r')

        # Retrieve the time via EXIF tags
        name2tagnum = dict((name, num) for num, name in TAGS.items())
        if image._getexif() is None:
            time = None
        else:
            time_string = image._getexif()[name2tagnum["DateTimeOriginal"]]
            time = datetime.datetime.strptime(time_string, "%Y:%m:%d %H:%M:%S")

        if convert_to_temperatures:
            if self.calibration_coefficients is None:
                raise ValueError("For converting to temperatures a calibration file is needed! Look at the "
                                 "documentation of the parameter calibration_file for more information.")
            # convert it to a grey scale image
            data = np.float32(np.array(image.convert('L')))
            data = brightness_to_temperature(data, self.calibration_coefficients)
            return ThermoCamImage(data, time)
        else:
            data = np.float32(np.array(image.convert('RGB')))
            return Image(data, time)

        # black pixels = NaN
        # data[data == 0] = np.nan


class WebCamFile(cloud.handlers.FileHandler):
    """ This class can read web cam images of the Pinocchio instrument.


    """

    def __init__(self, **kwargs):
        self.wichtig = True

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
        """
        Reads an image and converts it to np.array.

        Args:
            filename: Path and name of file

        Returns:
            Image
        """

        # read image
        image = PIL.Image.open(filename, 'r')

        # convert it to a grey scale image
        #data = np.float32(np.array(image.convert('L')))

        data = np.float32(np.array(image))

        # black pixels = NaN
        #data[data == 0] = np.nan

        return Image(data)


class WebCamFishEyeFile(WebCamFile):
    def __init__(self, **kwargs):
        super(WebCamFishEyeFile, self).__init__(**kwargs)

    def read(self, filename, fields=None):
        image = super(WebCamFishEyeFile, self).read(filename)

        #image.distortion()