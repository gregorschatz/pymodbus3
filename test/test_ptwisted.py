import unittest

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#


class TwistedInternalCodeTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.internal.ptwisted code
    """

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def test_install_conch(self):
        """ Test that we can install the conch backend """
        pass

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
