# -*- coding: utf-8 -*-

"""
Handle the version information here; you should only have to
change the version tuple.

Since we are using twisted's version class, we can also query
the svn version as well using the local .entries file.
"""


class Version(object):

    def __init__(self, package, major, minor, micro):
        """

        :param package: Name of the package that this is a version of.
        :param major: The major version number.
        :param minor: The minor version number.
        :param micro: The micro version number.
        """
        self.package = package
        self.major = major
        self.minor = minor
        self.micro = micro

    def short(self):
        """ Return a string in canonical short version format
        <major>.<minor>.<micro>
        """
        return '{0}.{1}.{2}'.format(self.major, self.minor, self.micro)

    def __str__(self):
        """ Returns a string representation of the object

        :returns: A string representation of this object
        """
        return '[{0}, version {1}]'.format(self.package, self.short())

    @staticmethod
    def get_current_version():
        version = Version('pymodbus3', 1, 0, 0)
        version.__name__ = 'pymodbus3'  # fix epydoc error
        return version
