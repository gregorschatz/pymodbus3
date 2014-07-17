import unittest
from pymodbus3.exceptions import *


class SimpleExceptionsTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.exceptions module
    """

    def setUp(self):
        """ Initializes the test environment """
        self.exceptions = [
            ModbusException("bad base"),
            ModbusIOException("bad register"),
            ParameterException("bad parameter"),
            ConnectionException("bad connection"),
        ]

    def tearDown(self):
        """ Cleans up the test environment """
        pass

    def test_exceptions(self):
        """ Test all module exceptions """
        for ex in self.exceptions:
            try:
                raise ex
            except ModbusException as ex:
                self.assertTrue("Modbus Error:" in str(ex))
                pass
            else:
                self.fail("Excepted a ModbusExceptions")

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
