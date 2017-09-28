# -*- coding: utf-8 -*-

"""All handler modules."""

import abc

__all__ = [
    'FileHandler',
]


class FileHandler:
    __metaclass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        ...

    @abc.abstractmethod
    def get_info(self, filename):
        """Get info parameters from a file (time coverage, etc).

        Args:
            filename: Path and name of the file.

        Returns:
            A dictionary with info parameters. It has to contain a key "times" with a tuple of two datetime objects as
            value.
        """
        pass

    @abc.abstractmethod
    def read(self, filename, **kwargs):
        """This method should open a file by its name, read its content and return a numpy.array with the
        following structure:



        This method is abstract therefore it has to be implemented in the specific file handler subclass.

        Args:
            filename:

        Returns:
            numpy.array
        """
        pass

    def write(self, filename, data, **kwargs):
        """This method should store data to a file.

        This method is not abstract and therefore it is optional whether a file handler subclass does support a
        writing-data-to-file feature.

        Args:
            filename:
            data:

        Returns:
            None
        """
        raise NotImplementedError("This file handler does not support writing data to a file. You should use a "
                                  "different file handler.")