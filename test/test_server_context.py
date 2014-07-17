import unittest
from pymodbus3.datastore import *
from pymodbus3.exceptions import *


class ModbusServerSingleContextTest(unittest.TestCase):
    """ This is the unittest for the pymodbus3.datastore.ModbusServerContext
    using a single slave context.
    """

    def setUp(self):
        """ Sets up the test environment """
        self.slave = ModbusSlaveContext()
        self.context = ModbusServerContext(slaves=self.slave, single=True)

    def tearDown(self):
        """ Cleans up the test environment """
        del self.context

    def test_single_context_gets(self):
        """ Test getting on a single context """
        for uid in range(0, 0xff):
            self.assertEqual(self.slave, self.context[uid])

    def test_single_context_deletes(self):
        """ Test removing on multiple context """
        def _test():
            del self.context[0x00]
        self.assertRaises(ParameterException, _test)

    def test_single_context_iter(self):
        """ Test iterating over a single context """
        expected = (0, self.slave)
        for slave in self.context:
            self.assertEqual(slave, expected)

    def test_single_context_default(self):
        """ Test that the single context default values work """
        self.context = ModbusServerContext()
        slave = self.context[0x00]
        self.assertEqual(slave, {})

    def test_single_context_set(self):
        """ Test a setting a single slave context """
        slave = ModbusSlaveContext()
        self.context[0x00] = slave
        actual = self.context[0x00]
        self.assertEqual(slave, actual)


class ModbusServerMultipleContextTest(unittest.TestCase):
    """ This is the unittest for the pymodbus3.datastore.ModbusServerContext
    using multiple slave contexts.
    """

    def setUp(self):
        """ Sets up the test environment """
        self.slaves = dict((uid, ModbusSlaveContext()) for uid in range(10))
        self.context = ModbusServerContext(slaves=self.slaves, single=False)

    def tearDown(self):
        """ Cleans up the test environment """
        del self.context

    def test_multiple_context_gets(self):
        """ Test getting on multiple context """
        for uid in range(0, 10):
            self.assertEqual(self.slaves[uid], self.context[uid])

    def test_multiple_context_deletes(self):
        """ Test removing on multiple context """
        del self.context[0x00]
        self.assertRaises(ParameterException, lambda: self.context[0x00])

    def test_multiple_context_iter(self):
        """ Test iterating over multiple context """
        for uid, slave in self.context:
            self.assertEqual(slave, self.slaves[uid])
            self.assertTrue(uid in self.context)

    def test_multiple_context_default(self):
        """ Test that the multiple context default values work """
        self.context = ModbusServerContext(single=False)
        self.assertRaises(ParameterException, lambda: self.context[0x00])

    def test_multiple_context_set(self):
        """ Test a setting multiple slave contexts """
        slaves = dict((uid, ModbusSlaveContext()) for uid in range(10))
        for uid, slave in slaves.items():
            self.context[uid] = slave
        for uid, slave in slaves.items():
            actual = self.context[uid]
            self.assertEqual(slave, actual)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
