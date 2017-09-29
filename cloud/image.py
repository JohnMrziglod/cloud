from datetime import datetime, timezone
import io
import warnings

from netCDF4 import Dataset, num2date, date2num
import numpy as np
import PIL.Image
import PIL.PngImagePlugin
import matplotlib.pyplot as plt


def load_mask(self, filename: str):
    """ Loads a mask file and returns it as a numpy array where the masked values are False.

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
        image = Image.open(filename, 'r')

        # convert it to a grey scale image
        mask = np.float32(np.array(image.convert('L')))
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

    mask = mask.astype("int")

    return mask == 1


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
        """ Apply mask on data.

        Args:
            mask: A numpy.array of boolean values. All indices where this mask is false, the pixels of the image will be
                covered.

        Returns:
            None
        """

        self.data[~mask] = np.nan #np.ma.masked_where(~mask, self.data)

    @staticmethod
    def count_edges(array):
        v_edges = np.nansum(Image.edge_mask(array, "v"))
        h_edges = np.nansum(Image.edge_mask(array, "h"))
        return v_edges + h_edges

    def cut(self, x, y):
        """Selects a part of the image and cut off the borders.

        Args:
            x: The columns of the image that you want to keep.
            y: The rows of the image that you want to keep.

        Returns:

        """
        self.data = self.data[y, x]

    @staticmethod
    def edge_mask(array, direction="h"):
        image = array.astype("int")
        image[image == 0] = -1

        if direction == "v":
            return image[:, :-1] + image[:, 1:] == 0
        else:
            return image[:-1, :] + image[1:, :] == 0

    def save(self, filename, **kwargs):
        """ Saves the image to a file.

        Args:
            filename: File to which the image should be saved.
            **kwargs: Additonal arguments.

        Returns:
            None
        """
        image = PIL.Image.fromarray(self.data).convert('RGB')

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

        self.data = 255 * (self.data + np.abs(np.nanmin(self.data))) / (np.nanmax(self.data)
                                                                            + np.abs(np.nanmin(self.data)))

    def to_brightness(self):
        """ Converts all pixels of this image to brightness values between 0 and 255.

        Args:
           data: A two-dimensional numpy.array containing image data

        Returns:
           A numpy.array of normalized data.
        """

        if len(self.data.shape) == 3:
            self.data = 255. * (np.nansum(self.data, 2) / (3*255.))

    def show(self):
        image = PIL.Image.fromarray(self.data)
        image.show()


class ThermoCamImage(Image):
    def __init__(self, *args, **kwargs):
        """ A specialised image class that handles thermal cam images (matrizes of temperatures).

        Args:
            *args: Positonal arguments of the base class Image.
            **kwargs: Keyword arguments of the base class Image.
        """
        # Call the base class initializer
        Image.__init__(self, *args, **kwargs)

        self.cloud_param = {
        }

        self._temperature_range = (0, 0)

    @staticmethod
    def cloud_coverage(cloud_mask):
        """Calculates the cloud coverage of this image.

        Args:
            cloud_mask: Matrix with boolean values for each pixel. True means cloud, False means non-cloud.

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

    def cloud_mask(self, clear_sky_temperature):
        """Creates a cloud mask (boolean matrix) of this image.

        Args:
            clear_sky_temperature: Temperature of the clear sky that will be used as threshold to decide between cloud
                and non-cloud.

        Returns:
            A 2-dimensional numpy.array.
        """

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return self.data > clear_sky_temperature

    def cloud_parameters(self, clear_sky_temperature=0):
        """Calculates the cloud parameters of this image.

        Args:
            clear_sky_temperature: Temperature of the clear sky that will be used as threshold to decide between cloud
                and non-cloud.

        Returns:
            A dictionary with the values for the different parameters (coverage, inhomogeneity, etc.)
        """
        cloud_mask = self.cloud_mask(clear_sky_temperature)

        # Calculate the coverage parameters:
        self.cloud_param["coverage"] = self.cloud_coverage(cloud_mask)
        self.cloud_param["mean_temperature"] = self.cloud_mean_temperature(cloud_mask)
        self.cloud_param["inhomogeneity"] = self.cloud_inhomogeneity(cloud_mask)
        self.cloud_param["mask"] = cloud_mask

        return self.cloud_param

    @classmethod
    def from_file(cls, filename):
        """Reads a thermal cam image from a netcdf file.

        Args:
            filename: Path and name of the file.

        Returns:
            ThermoCamImage object
        """
        fh = Dataset(filename, "r", format="NETCDF4")

        try:
            time = datetime.fromtimestamp(fh["times"][0])#, file["times"].units)
        except:
            time = None

        data = fh["images"][0][:]

        image = cls(data, time)

        # Get attributes:
        for name in fh.ncattrs():
            image.attr[name] = getattr(fh, name)

        fh.close()

        return image

    def to_file(self, filename, fmt="netcdf", cmap=None):
        """ Saves the image to a file. Since it is a matrix of temperature values, the temperature will converted to
        colours according to a color map.

        Args:
            filename: File to which the image should be saved.
            fmt: Format of the files. Can be either "netcdf" or "png". Default is "netcdf".
            cmap: The colormap that should be used when saving as PNG file.

        Returns:
            None
        """

        if fmt == "png":
            if cmap is None:
                cmap = "jet"

            # The following code is taken from https://stackoverflow.com/a/8598881 and https://stackoverflow.com/a/10552742.
            fig, ax = plt.subplots()
            im = ax.imshow(self.data, cmap=cmap)  # Show the image
            im.set_clim(vmin=-20, vmax=30)
            # pos = plt.axes([0.93, 0.1, 0.02, 0.35])  # Set colorbar position in fig
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
        elif fmt == "netcdf":
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
            images = file.createVariable("images", "f8",
                                         ("time", "height", "width"))
            images.missing_value = np.nan
            images.units = "°C"
            images[:] = np.array([image_data])

            for param, value in self.cloud_param.items():
                if param == "mask":
                    # Do not save the cloud mask!
                    continue
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

    @property
    def temperature_range(self):
        return self._temperature_range

    @temperature_range.setter
    def temperature_range(self, temperatures):
        self._temperature_range = temperatures
