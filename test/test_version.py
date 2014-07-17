import unittest
from pymodbus3.version import Version


class ModbusVersionTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3._version code
    """

    def setUp(self):
        """ Initializes the test environment """
        pass

    def tearDown(self):
        """ Cleans up the test environment """
        pass

    def test_version_class(self):
        version = Version('test', 1, 2, 3)
        self.assertEqual(version.short(), '1.2.3')
        self.assertEqual(str(version), '[test, version 1.2.3]')

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
