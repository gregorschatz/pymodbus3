import unittest
from pymodbus3.datastore import *
from pymodbus3.datastore.store import BaseModbusDataBlock
from pymodbus3.exceptions import ParameterException


class ModbusDataStoreTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.datastore module
    """

    def setUp(self):
        pass

    def tearDown(self):
        """ Cleans up the test environment """
        pass

    def test_modbus_data_block(self):
        """ Test a base data block store """
        block = BaseModbusDataBlock()
        block.default(10, True)

        self.assertNotEqual(str(block), None)
        self.assertEqual(block.default_value, True)
        self.assertEqual(block.values, [True]*10)

        block.default_value = False
        block.reset()
        self.assertEqual(block.values, [False]*10)

    def test_modbus_data_block_iterate(self):
        """ Test a base data block store """
        block = BaseModbusDataBlock()
        block.default(10, False)
        for idx, value in block:
            self.assertEqual(value, False)

        block.values = {0: False, 2: False, 3: False }
        for idx, value in block:
            self.assertEqual(value, False)

    def test_modbus_data_block_other(self):
        """ Test a base data block store """
        block = BaseModbusDataBlock()
        self.assertRaises(NotImplementedError, lambda: block.validate(1, 1))
        self.assertRaises(NotImplementedError, lambda: block.get_values(1, 1))
        self.assertRaises(NotImplementedError, lambda: block.set_values(1, 1))

    def test_modbus_sequential_data_block(self):
        """ Test a sequential data block store """
        block = ModbusSequentialDataBlock(0x00, [False]*10)
        self.assertFalse(block.validate(-1, 0))
        self.assertFalse(block.validate(0, 20))
        self.assertFalse(block.validate(10, 1))
        self.assertTrue(block.validate(0x00, 10))

        block.set_values(0x00, True)
        self.assertEqual(block.get_values(0x00, 1), [True])

        block.set_values(0x00, [True]*10)
        self.assertEqual(block.get_values(0x00, 10), [True]*10)

    def test_modbus_sequential_data_block_factory(self):
        """ Test the sequential data block store factory """
        block = ModbusSequentialDataBlock.create()
        self.assertEqual(block.get_values(0x00, 65536), [False]*65536)
        block = ModbusSequentialDataBlock(0x00, 0x01)
        self.assertEqual(block.values, [0x01])

    def test_modbus_sparse_data_block(self):
        """ Test a sparse data block store """
        values = dict(enumerate([True]*10))
        block = ModbusSparseDataBlock(values)
        self.assertFalse(block.validate(-1, 0))
        self.assertFalse(block.validate(0, 20))
        self.assertFalse(block.validate(10, 1))
        self.assertTrue(block.validate(0x00, 10))
        self.assertTrue(block.validate(0x00, 10))
        self.assertFalse(block.validate(0, 0))
        self.assertFalse(block.validate(5, 0))

        block.set_values(0x00, True)
        self.assertEqual(block.get_values(0x00, 1), [True])

        block.set_values(0x00, [True]*10)
        self.assertEqual(block.get_values(0x00, 10), [True]*10)

        block.set_values(0x00, dict(enumerate([False]*10)))
        self.assertEqual(block.get_values(0x00, 10), [False]*10)

    def test_modbus_sparse_data_block_factory(self):
        """ Test the sparse data block store factory """
        block = ModbusSparseDataBlock.create()
        self.assertEqual(block.get_values(0x00, 65536), [False]*65536)

    def test_modbus_sparse_data_block_other(self):
        block = ModbusSparseDataBlock([True]*10)
        self.assertEqual(block.get_values(0x00, 10), [True]*10)
        self.assertRaises(
            ParameterException,
            lambda: ModbusSparseDataBlock(True)
        )

    def test_modbus_slave_context(self):
        """ Test a modbus slave context """
        store = {
            'di': ModbusSequentialDataBlock(0, [False]*10),
            'co': ModbusSequentialDataBlock(0, [False]*10),
            'ir': ModbusSequentialDataBlock(0, [False]*10),
            'hr': ModbusSequentialDataBlock(0, [False]*10),
        }
        context = ModbusSlaveContext(**store)
        self.assertNotEqual(str(context), None)
        
        for fx in [1, 2, 3, 4]:
            context.set_values(fx, 0, [True]*10)
            self.assertTrue(context.validate(fx, 0, 10))
            self.assertEqual(context.get_values(fx, 0, 10), [True]*10)
        context.reset()

        for fx in [1, 2, 3, 4]:
            self.assertTrue(context.validate(fx, 0, 10))
            self.assertEqual(context.get_values(fx, 0, 10), [False]*10)

    def test_modbus_server_context(self):
        """ Test a modbus server context """
        def _set(ctx):
            ctx[0xffff] = None
        context = ModbusServerContext(single=False)
        self.assertRaises(ParameterException, lambda: _set(context))
        self.assertRaises(ParameterException, lambda: context[0xffff])

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
