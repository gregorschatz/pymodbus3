import unittest
import struct
from pymodbus3.utilities import pack_bitstring, unpack_bitstring
from pymodbus3.utilities import check_crc, check_lrc
from pymodbus3.utilities import dict_property, default

_test_master = {4: 'd'}


class DictPropertyTester(object):
    def __init__(self):
        self.test = {1: 'a'}
        self._test = {2: 'b'}
        self.__test = {3: 'c'}

    l1 = dict_property(lambda s: s.test, 1)
    l2 = dict_property(lambda s: s._test, 2)
    l3 = dict_property(lambda s: s.__test, 3)
    s1 = dict_property('test', 1)
    s2 = dict_property('_test', 2)
    g1 = dict_property(_test_master, 4)


class SimpleUtilityTest(unittest.TestCase):
    """
    This is the unittest for the pymod.utilities module
    """

    def setUp(self):
        """ Initializes the test environment """
        self.data = struct.pack('>HHHH', 0x1234, 0x2345, 0x3456, 0x4567)
        self.string = "test the computation"
        self.bits = [True, False, True, False, True, False, True, False]

    def tearDown(self):
        """ Cleans up the test environment """
        del self.bits
        del self.string

    def test_dict_property(self):
        """ Test all string <=> bit packing functions """
        d = DictPropertyTester()
        self.assertEqual(d.l1, 'a')
        self.assertEqual(d.l2, 'b')
        self.assertEqual(d.l3, 'c')
        self.assertEqual(d.s1, 'a')
        self.assertEqual(d.s2, 'b')
        self.assertEqual(d.g1, 'd')

        for store in 'l1 l2 l3 s1 s2 g1'.split(' '):
            setattr(d, store, 'x')

        self.assertEqual(d.l1, 'x')
        self.assertEqual(d.l2, 'x')
        self.assertEqual(d.l3, 'x')
        self.assertEqual(d.s1, 'x')
        self.assertEqual(d.s2, 'x')
        self.assertEqual(d.g1, 'x')

    def test_default_value(self):
        """ Test all string <=> bit packing functions """
        self.assertEqual(default(1), 0)
        self.assertEqual(default(1.1), 0.0)
        self.assertEqual(default(1+1j), 0j)
        self.assertEqual(default('string'), '')
        self.assertEqual(default([1, 2, 3]), [])
        self.assertEqual(default({1: 1}), {})
        self.assertEqual(default(True), False)

    def test_bit_packing(self):
        """ Test all string <=> bit packing functions """
        self.assertEqual(unpack_bitstring('\x55'), self.bits)
        self.assertEqual(pack_bitstring(self.bits), '\x55')

    def test_longitudinal_redundancy_check(self):
        """ Test the longitudinal redundancy check code """
        self.assertTrue(check_lrc(self.data, 0x1c))
        self.assertTrue(check_lrc(self.string, 0x0c))

    def test_cyclic_redundancy_check(self):
        """ Test the cyclic redundancy check code """
        self.assertTrue(check_crc(self.data, 0xe2db))
        self.assertTrue(check_crc(self.string, 0x889e))

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
