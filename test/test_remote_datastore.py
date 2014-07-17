import unittest
from pymodbus3.datastore.remote import RemoteSlaveContext
from pymodbus3.bit_read_message import *
from pymodbus3.bit_write_message import *
from pymodbus3.register_read_message import *
from pymodbus3.pdu import ExceptionResponse
from .modbus_mocks import mock


class RemoteModbusDataStoreTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.datastore.remote module
    """

    def test_remote_slave_context(self):
        """ Test a modbus remote slave context """
        context = RemoteSlaveContext(None)
        self.assertNotEqual(str(context), None)
        self.assertRaises(NotImplementedError, lambda: context.reset())

    def test_remote_slave_set_values(self):
        """ Test setting values against a remote slave context """
        client = mock()
        client.write_coils = lambda a, b: WriteMultipleCoilsResponse()

        context = RemoteSlaveContext(client)
        result = context.set_values(1, 0, [1])
        self.assertTrue(True)

    def test_remote_slave_get_values(self):
        """ Test getting values from a remote slave context """
        client = mock()
        client.read_coils = lambda a, b: ReadCoilsResponse([1]*10)
        client.read_input_registers = lambda a, b: ReadInputRegistersResponse([10]*10)
        client.read_holding_registers = lambda a, b: ExceptionResponse(0x15)

        context = RemoteSlaveContext(client)
        result = context.get_values(1, 0, 10)
        self.assertEqual(result, [1]*10)

        result = context.get_values(4, 0, 10)
        self.assertEqual(result, [10]*10)

        result = context.get_values(3, 0, 10)
        self.assertNotEqual(result, [10]*10)

    def test_remote_slave_validate_values(self):
        """ Test validating against a remote slave context """
        client = mock()
        client.read_coils = lambda a, b: ReadCoilsResponse([1]*10)
        client.read_input_registers = lambda a, b: ReadInputRegistersResponse([10]*10)
        client.read_holding_registers = lambda a, b: ExceptionResponse(0x15)

        context = RemoteSlaveContext(client)
        result = context.validate(1, 0, 10)
        self.assertTrue(result)

        result = context.validate(4, 0, 10)
        self.assertTrue(result)

        result = context.validate(3, 0, 10)
        self.assertFalse(result)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
