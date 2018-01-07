"""Contains the classes and functions for mask and movie handling.

Every thermal camera image will be converted to a ThermalCamMovie object by the
file handlers of Pinocchio or Dumbo.
"""

from collections import defaultdict
import warnings

import numpy as np
import PIL.Image
import PIL.PngImagePlugin
from typhon.spareice.array import Array, ArrayGroup


__all__ = [
    "load_mask",
    "Movie",
    "ThermalCamMovie",
]


def load_mask(filename):
    """Loads a mask file and returns it as a numpy array where the masked
    values are False.

    This method can handle ASCII or PNG files as masks.

    Args:
        filename: Path and name of the mask file

    Returns:
        numpy.array with w x h dimensions.
    """

    if filename is None:
        return None

    mask = None
    if filename.endswith(".png"):
        # read image
        image = PIL.Image.open(filename, 'r')

        # convert it to a grey scale image
        mask = np.float32(np.array(image.convert('L')))
        mask = np.flipud(mask)
        mask = mask == 255
    elif filename.endswith(".txt"):
        # Count the number of columns in that mask file.
        with open(filename, "r") as f:
            num_columns = len(f.readline().split(","))

        mask = np.genfromtxt(
            filename,
            delimiter=",",
            skip_header=1,
            usecols=list(range(1, num_columns))
        )

        mask = mask == 1

    return mask


class Movie(ArrayGroup):
    """A sequence of images and their timestamps. """

    def apply_mask(self, mask):
        """ Applies a mask on this movie.

        Args:
            mask: A numpy.array of boolean values. Where this mask
                is false the pixels of the image will be covered.

        Returns:
            None
        """

        # self = np.ma.masked_where(~mask, self)
        self["images"][:, ~mask] = np.nan

    @staticmethod
    def count_edges(array):
        v_edges = np.nansum(Movie.edge_mask(array, "v"), axis=(1, 2))
        h_edges = np.nansum(Movie.edge_mask(array, "h"), axis=(1, 2))
        return v_edges + h_edges

    # def cut(self, x, y):
    #     """Selects a part of the image that should be cut off.
    #
    #     Args:
    #         x: The columns of the image that you want to cut off.
    #         y: The rows of the image that you want to cut off.
    #
    #     Returns:
    #         None
    #
    #     Examples:
    #         # Delete one pixel row from the left and top border.
    #         >> image.cut(0, 0)
    #     """
    #
    #     cut_img = np.delete(self, x, 0)
    #     cut_img = np.delete(cut_img, y, 1)
    #     return cut_img

    @staticmethod
    def edge_mask(array, direction="h"):
        image = array.astype("int")
        image[image == 0] = -1

        if direction == "v":
            return image[:, :-1] + image[:, 1:] == 0
        else:
            return image[:-1, :] + image[1:, :] == 0

    @property
    def height(self):
        return self["images"].shape[1]

    # def to_gray_scale(self):
    #     """ Converts this image to gray scale.
    #
    #     Args:
    #        data: A two-dimensional numpy.array containing image data
    #
    #     Returns:
    #        A numpy.array of normalized data.
    #     """
    #
    #     self = 255 * (self + np.abs(np.nanmin(self))) / (
    #         np.nanmax(self) + np.abs(np.nanmin(self)))

    # def to_brightness(self):
    #     """ Converts all pixels of this image to brightness values between 0
    #     and 255.
    #
    #     Returns:
    #        None
    #     """
    #
    #     if len(self["images"].shape) == 4:
    #         self = 255. * (np.nansum(self, 2) / (3*255.))

    # def show(self):
    #     image = PIL.Image.fromarray(self)
    #     image.show()

    @property
    def width(self):
        return self["images"].shape[0]


class ThermalCamMovie(Movie):
    """An object that can hold a sequence of thermal cam images and calculate
    cloud statistics from them."""

    clouds = None

    def cloud_coverage(self,):
        """Calculates the cloud coverage of this image.

        Returns:
            A numpy.array with a float between 0 and 1 for each image.
        """
        if self.clouds is None:
            raise ValueError("Cannot calculate cloud parameter! You have to "
                             "call ThermalCamMovie.find_clouds() first!")

        all_cloud_pixels = np.count_nonzero(
            ~np.isnan(self.clouds), axis=(1, 2,))

        all_pixels = np.count_nonzero(
            ~np.isnan(self["images"]), axis=(1, 2,))

        return all_cloud_pixels / all_pixels

    def cloud_max_temperature(self, ):
        """Calculates the cloud max temperature.

        This is simply the cloud pixel with the highest temperature.

        Returns:
            A numpy.array with the cloud max temperature for each image.
            If there is no cloud, NaN will be returned.
        """
        if self.clouds is None:
            raise ValueError("Cannot calculate cloud parameter! You have to "
                             "call ThermalCamMovie.find_clouds() first!")

        return np.nanmax(self.clouds, axis=(1, 2,))

    def cloud_min_temperature(self, ):
        """Calculates the cloud min temperature.

        This is simply the cloud pixel with the lowest temperature.

        Returns:
            A numpy.array with the cloud min temperature for each image.
            If there is no cloud, NaN will be returned.
        """
        if self.clouds is None:
            raise ValueError("Cannot calculate cloud parameter! You have to "
                             "call ThermalCamMovie.find_clouds() first!")

        return np.nanmin(self.clouds, axis=(1, 2,))

    def cloud_mean_temperature(self,):
        """Calculates the cloud min temperature.

        This is simply the mean temperature of all cloud pixels.

        Returns:
            A numpy.array with the cloud mean temperature for each image.
            If there is no cloud, NaN will be returned.
        """
        if self.clouds is None:
            raise ValueError("Cannot calculate cloud parameter! You have to "
                             "call ThermalCamMovie.find_clouds() first!")

        return np.nanmean(self.clouds, axis=(1, 2,))

    def cloud_inhomogeneity(self,):
        """Calculates the cloud inhomogeneity.

        Warnings:
            This function does not work right now with Dumbo images.

        A number that represents the jaggedness of the clouds. It is defined by
        the ratio between the perimeter and the area of the cloud pixels:

        .. math::

            CI = \frac{p_cloud}{A_cloud}


        Returns:
            A numpy.array with the cloud inhomogeneity for each image.
        """
        if self.clouds is None:
            raise ValueError("Cannot calculate cloud parameter! You have to "
                             "call ThermalCamMovie.find_clouds() first!")

        cloud_mask = ~np.isnan(self.clouds)
        size = np.nansum(cloud_mask, axis=(1, 2,)).astype("float")

        # We cannot divide by zero
        size[size < 1] = np.nan

        # 10 is an arbitrary scaling parameter
        inhomogeneity = 10 * Movie.count_edges(cloud_mask) / size

        # Replace the NaN with zero again to retrieve the correct inhomogeneity
        # value
        inhomogeneity[np.isnan(inhomogeneity)] = 0.

        return inhomogeneity

    def cloud_level_mask(self, t_surface, lapse_rate=None):
        """Classifies each pixel according to its temperature to a height
        level.

        The levels are:
            * Up to 2000m: Low clouds - class 1.
            * 2000m - 6000m: Middle high clouds - class 2.
            * 6000m - 10000m: Middle high clouds - class 3.
            * No cloud - class 0.

        Args:
            t_surface: Temperature of the surface / near surface. Either it is
                temperature function fit.
            lapse_rate: Temperature descent gradient per 1 km. Default is
                -4K/km.

        Returns:
            Matrix with classes for each pixel.
        """
        if lapse_rate is None:
            # The standard wet atmosphere lapse rate:
            lapse_rate = -4.

        # Temperatures for each level
        level_temps = t_surface + lapse_rate * np.array([2, 6, 10])

        level_mask = np.zeros_like(self)
        # Low clouds
        level_mask[self > level_temps[0]] = 1
        # Middle high clouds
        level_mask[
            (level_temps[0] > self) &
            (self > level_temps[1])] = 2
        # High clouds
        level_mask[
            (level_temps[1] > self) &
            (self > level_temps[2])] = 3

        return level_mask

    def find_clouds(self, min_temperature, max_temperature=None):
        """Find all clouds in this movie by using temperature thresholds.

        Args:
            min_temperature: Temperature of the clear sky that will be
                used as threshold to decide between cloud and non-cloud.
            max_temperature:

        Returns:
            A 3-dimensional numpy.array where all non-cloud pixels are NaN
            values.
        """

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            min_temperature.shape = (min_temperature.shape[0], 1, 1)

            if max_temperature is None:
                cloud_mask = self["images"] > min_temperature
                self.clouds = self["images"].copy()
                self.clouds[~cloud_mask] = np.nan
                return self.clouds

            # Otherwise broadcasting fails
            max_temperature.shape = (max_temperature.shape[0], 1, 1)

            cloud_mask = (self["images"] > min_temperature) & \
                   (self["images"] < max_temperature)

            # Save the cloud pixels
            self.clouds = self["images"].copy()
            self.clouds[~cloud_mask] = np.nan

            return self.clouds

    def cloud_parameters(self, temperatures, levels=None):
        """Calculates the cloud parameters of this image.

        Args:
            temperatures: Temperature of the clear sky that will be
                used as threshold to decide between cloud and non-cloud. Should
                be a interpolation function (i.e. a
                scipy.interpolate.interp1d).
            levels: A list of different temperature thresholds

        Returns:
            A dictionary with the values for the different parameters (
            coverage, inhomogeneity, etc.)
        """

        parameters = {
            "cloud_coverage": [
                self.cloud_coverage,
                {"description": "cloud coverage",
                 "units": "coverage [0-1]"},
            ],
            "cloud_mean_temperature": [
                self.cloud_mean_temperature,
                {"description": "cloud mean temperature",
                 "units": "temperature [°C]"},
            ],
            # TODO: The cloud inhomogeneity does not seem to work right now,
            # TODO: it has some broadcasting issues.
            # "cloud_inhomogeneity": [
            #     self.cloud_inhomogeneity,
            #     {"description": "cloud inhomogeneity",
            #      "units": "coverage [0-1]"},
            # ],
            "cloud_max_temperature": [
                self.cloud_max_temperature,
                {"description": "cloud max. temperature",
                 "units": "temperature [°C]"},
            ],
            "cloud_min_temperature": [
                self.cloud_min_temperature,
                {"description": "cloud min. temperature",
                 "units": "temperature [°C]"},
            ]
        }

        results = defaultdict(list)

        for level, decrement in enumerate(levels):
            # We need a cloud mask before calculating the cloud statistics.
            if level == 0:
                self.find_clouds(
                    temperatures(self["time"]) + decrement,
                    None,
                )
            else:
                self.find_clouds(
                    temperatures(self["time"]) + decrement,
                    temperatures(self["time"]) + levels[level-1],
                )

            # Calculate the cloud parameters (we ignore warnings because when
            # we do not find clouds many messages are triggered)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                for parameter, func in parameters.items():
                    results[parameter].append(func[0]())

        cloud_stats = ArrayGroup()
        cloud_stats["time"] = self["time"]
        cloud_stats["time"].dims = ["time"]
        for parameter, result in results.items():
            cloud_stats[parameter] = Array(
                np.column_stack(result),
                attrs=parameters[parameter][1],
                dims=["time", "level"],
            )

        return cloud_stats
