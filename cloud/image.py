from datetime import datetime, timezone
import io
import warnings

from netCDF4 import Dataset
import numpy as np
import PIL.Image
import PIL.PngImagePlugin
import matplotlib.pyplot as plt


__all__ = [
    "load_mask",
    "Image",
    "ThermoCamImage",
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


class Image:
    def __init__(self, data, time=None, **kwargs):
        """ A class that handles image data in a numpy.array.

        Args:
            data: Two- or three-dimensional numpy array with the image data.
            time: Time when the photo was taken.
            **kwargs:
        """
        self.attr = kwargs
        self.data = data
        self._time = None
        self.time = time

    def apply_mask(self, mask):
        """ Applies a mask on this image.

        Args:
            mask: A numpy.array of boolean values. Where this mask
                is false the pixels of the image will be covered.

        Returns:
            None
        """

        # self.data = np.ma.masked_where(~mask, self.data)
        self.data[~mask] = np.nan

    @staticmethod
    def count_edges(array):
        v_edges = np.nansum(Image.edge_mask(array, "v"))
        h_edges = np.nansum(Image.edge_mask(array, "h"))
        return v_edges + h_edges

    def cut(self, x, y):
        """Selects a part of the image that should be cut off.

        Args:
            x: The columns of the image that you want to cut off.
            y: The rows of the image that you want to cut off.

        Returns:
            None

        Examples:
            # Delete one pixel row from the left and top border.
            >> image.cut(0, 0)
        """

        self.data = np.delete(self.data, x, 0)
        self.data = np.delete(self.data, y, 1)
        return self.data

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
        return self.data.shape[1]

    def save(self, filename, **kwargs):
        """ Saves the image to a file.

        Args:
            filename: File to which the image should be saved.
            **kwargs: Additonal arguments.

        Returns:
            None
        """
        image = PIL.Image.fromarray(self.data)#.convert('RGB')

        # Create a meta data dictionary for the image
        meta = PIL.PngImagePlugin.PngInfo()

        if self.time is not None:
            # Save the time tag in the image (as metadata)
            meta.add_text("time", self.time.strftime("%Y-%m-%d %H:%M:%S"))
        for attr, value in self.attr.items():
            meta.add_text(attr, value)

        # Save the image
        image.save(filename, pnginfo=meta)

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = value

    def to_gray_scale(self):
        """ Converts this image to gray scale.

        Args:
           data: A two-dimensional numpy.array containing image data

        Returns:
           A numpy.array of normalized data.
        """

        self.data = 255 * (self.data + np.abs(np.nanmin(self.data))) / (
            np.nanmax(self.data) + np.abs(np.nanmin(self.data)))

    def to_brightness(self):
        """ Converts all pixels of this image to brightness values between 0
        and 255.

        Returns:
           None
        """

        if len(self.data.shape) == 3:
            self.data = 255. * (np.nansum(self.data, 2) / (3*255.))

    def show(self):
        image = PIL.Image.fromarray(self.data)
        image.show()

    @property
    def width(self):
        return self.data.shape[0]


class ThermoCamImage(Image):
    def __init__(self, *args, **kwargs):
        """ A specialised image class that handles thermal cam images (matrices
        of temperatures).

        Args:
            *args: Positonal arguments of the base class Image.
            **kwargs: Keyword arguments of the base class Image.
        """
        # Call the base class initializer
        Image.__init__(self, *args, **kwargs)

        self.cloud_param = {
        }

        self._temperature_range = (0, 0)

    def cloud_base_temperature(self, cloud_mask):
        """Calculates the cloud base temperature of this image.

        This is simply the cloud pixel with the highest temperature.

        Args:
            cloud_mask: Matrix with boolean values for each pixel. True means
                cloud, False means non-cloud.

        Returns:
            The lowest temperature of all cloud pixels. If there is no cloud,
            NaN will be returned.
        """
        if cloud_mask.any():
            return np.nanmax(self.data[cloud_mask])
        else:
            return np.nan

    @staticmethod
    def cloud_coverage(cloud_mask):
        """Calculates the cloud coverage of this image.

        Args:
            cloud_mask: Matrix with boolean values for each pixel. True means
            cloud, False means non-cloud.

        Returns:
            A float between 0 and 1.
        """
        return np.nansum(cloud_mask) / np.sum(~np.isnan(cloud_mask))

    def cloud_mean_temperature(self, cloud_mask):
        if not cloud_mask.any():
            return 0.0   

        return np.nanmean(self.data[cloud_mask].data)

    @staticmethod
    def cloud_inhomogeneity(cloud_mask):
        size = np.nansum(cloud_mask)
        if size == 0:
            return 0
        # 10 is an arbitrary scaling parameter
        return 10 * Image.count_edges(cloud_mask) / size

    def cloud_level_mask(self, t_surface, lapse_rate=None):
        """Classifies each pixel according to its temperature to a height
        level.

        The levels are:
            Up to 2000m: Low clouds - class 1.
            2000m - 6000m: Middle high clouds - class 2.
            6000m - 10000m: Middle high clouds - class 3.
            No cloud - class 0.

        Args:
            t_surface: Temperature of the surface / near surface.
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

        level_mask = np.zeros_like(self.data)
        # Low clouds
        level_mask[self.data > level_temps[0]] = 1
        # Middle high clouds
        level_mask[
            (level_temps[0] > self.data) &
            (self.data > level_temps[1])] = 2
        # High clouds
        level_mask[
            (level_temps[1] > self.data) &
            (self.data > level_temps[2])] = 3

        return level_mask

    def cloud_mask(self, min_temperature, max_temperature=None):
        """Creates a cloud mask (boolean matrix) of this image.

        Args:
            min_temperature: Temperature of the clear sky that will be
                used as threshold to decide between cloud and non-cloud.
            max_temperature:

        Returns:
            A 2-dimensional numpy.array.
        """

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if max_temperature is None:
                return self.data > min_temperature

            return (self.data > min_temperature) & \
                   (self.data < max_temperature)

    def cloud_parameters(self, temperatures=None):
        """Calculates the cloud parameters of this image.

        Args:
            temperatures: Temperature of the clear sky that will be
                used as threshold to decide between cloud and non-cloud. Can be
                either one number or a list of numbers. Default is 0.

        Returns:
            A dictionary with the values for the different parameters (
            coverage, inhomogeneity, etc.)
        """

        if temperatures is None:
            temperatures = [0, ]
        elif isinstance(temperatures, (int, float)):
            temperatures = [temperatures]

        self.cloud_param = {
            "coverage": [],
            "mean_temperature": [],
            "inhomogeneity": [],
            "base_temperature": [],
            #"mask": []
        }

        # 3.2, -11.8, -28.8
        for i, temperature in enumerate(temperatures):
            if i == 0:
                cloud_mask = self.cloud_mask(temperature, None)
            else:
                cloud_mask = self.cloud_mask(temperature, temperatures[i-1])

            # Calculate the coverage parameters:
            self.cloud_param["coverage"].append(
                self.cloud_coverage(cloud_mask))
            self.cloud_param["mean_temperature"].append(
                self.cloud_mean_temperature(cloud_mask))
            self.cloud_param["inhomogeneity"].append(
                self.cloud_inhomogeneity(cloud_mask))
            self.cloud_param["base_temperature"].append(
                self.cloud_base_temperature(cloud_mask))
            # self.cloud_param["mask"].append(cloud_mask)

        return self.cloud_param

    @classmethod
    def from_netcdf(cls, filename):
        """Reads a thermal cam image from a netcdf file.

        Args:
            filename: Path and name of the file.

        Returns:
            A ThermoCamImage object
        """
        fh = Dataset(filename, "r", format="NETCDF4")

        try:
            time = datetime.fromtimestamp(fh["times"][0])
        except:
            time = None

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            data = fh["temperatures"][0][:]

        image = cls(data, time)

        # Get attributes:
        for name in fh.ncattrs():
            image.attr[name] = getattr(fh, name)

        fh.close()

        return image

    def to_netcdf(self, filename, save_cloud_mask=True):
        """ Saves the image to a netcdf file. Since it is a matrix of
        temperature values, the temperature will converted to colours according
        to a color map.

        Args:
            filename: File to which the image should be saved.
            save_cloud_mask: Save cloud mask in netcdf file.

        Returns:
            None
        """

        file = Dataset(filename, "w", format="NETCDF4")
        time = file.createDimension("time", None)

        for attr, value in self.attr.items():
            setattr(file, attr, value)

        if self.time is not None:
            times = file.createVariable("times", "f8", ("time", ))
            times.units = "s"
            times[:] = np.asarray(
                [self.time.replace(tzinfo=timezone.utc).timestamp()]
            )

        try:
            image_data = self.data.filled()
        except:
            image_data = self.data

        height = file.createDimension("height", image_data.shape[0])
        width = file.createDimension("width", image_data.shape[1])
        temperatures = file.createVariable("temperatures", "f8",
                                     ("time", "height", "width"))
        temperatures.missing_value = np.nan
        temperatures.units = "°C"
        temperatures[:] = np.array([image_data])

        for param, value in self.cloud_param.items():
            if param == "mask" and save_cloud_mask:
                var = file.createVariable("cloud_"+param, "i1",
                                          ("time", "height", "width"))
                var.units = "[bool]"
                var.description = "True where a cloud is."
                var[:] = np.array([value])
                continue

            var = file.createVariable("cloud_" + param, "f8", ("time",))
            var.units = "[0-1]"
            var[:] = np.array([value])

        file.close()

    def to_png(self, filename, cmap=None):
        """Saves the image to a file. Since it is a matrix of temperature
        values, the temperature will converted to colours according to a color
        map.

        Args:
            filename: File to which the image should be saved.
            cmap: The colormap that should be used. Default is jet.

        Returns:
            None
        """

        if cmap is None:
            cmap = "jet"

        # The following code is taken from
        # https://stackoverflow.com/a/8598881 and
        # https://stackoverflow.com/a/10552742.
        fig, ax = plt.subplots()
        im = ax.imshow(self.data, cmap=cmap)  # Show the image
        im.set_clim(vmin=-20, vmax=30)
        # pos = plt.axes([0.93, 0.1, 0.02, 0.35])  # Set colorbar position
        # in fig
        cbar = fig.colorbar(im, )  # Create the colorbar
        cbar.set_label('Temperature [°C]')
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        plt.close(fig)

        buf.seek(0)
        image = PIL.Image.open(buf)

        # Create a meta data dictionary for the image
        meta = PIL.PngImagePlugin.PngInfo()

        # Add the minimum and maximum temperature in the picture:
        meta.add_text("min_temperature", str(-20))
        meta.add_text("max_temperature", str(30))

        if self.time is not None:
            # Save the time tag in the image (as metadata)
            meta.add_text("time", self.time.strftime("%Y-%m-%d %H:%M:%S"))
        for attr, value in self.attr.items():
            meta.add_text(attr, value)

        # Save the image
        image.save(filename, "png", pnginfo=meta)
        buf.close()

    @property
    def temperature_range(self):
        return self._temperature_range

    @temperature_range.setter
    def temperature_range(self, temperatures):
        self._temperature_range = temperatures
