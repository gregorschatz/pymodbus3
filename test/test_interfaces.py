import unittest
from pymodbus3.interfaces import *


class _SingleInstance(Singleton):
    pass


class ModbusInterfaceTestsTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.interfaces module
    """

    def setUp(self):
        """ Initializes the test environment """
        pass

    def tearDown(self):
        """ Cleans up the test environment """
        pass

    def test_singleton_interface(self):
        """ Test that the singleton interface works """
        first = _SingleInstance()
        second = _SingleInstance()
        self.assertEquals(first, second)

    def test_modbus_decoder_interface(self):
        """ Test that the base class isn't implemented """
        x = None
        instance = IModbusDecoder()
        self.assertRaises(NotImplementedError, lambda: instance.decode(x))
        self.assertRaises(NotImplementedError, lambda: instance.lookup_pdu_class(x))

    def test_modbus_framer_interface(self):
        """ Test that the base class isn't implemented """
        x = None
        instance = IModbusFramer()
        self.assertRaises(NotImplementedError, instance.check_frame)
        self.assertRaises(NotImplementedError, instance.advance_frame)
        self.assertRaises(NotImplementedError, instance.is_frame_ready)
        self.assertRaises(NotImplementedError, instance.get_frame)
        self.assertRaises(NotImplementedError, lambda: instance.add_to_frame(x))
        self.assertRaises(NotImplementedError, lambda: instance.populate_result(x))
        self.assertRaises(NotImplementedError, lambda: instance.process_incoming_packet(x, x))
        self.assertRaises(NotImplementedError, lambda: instance.build_packet(x))

    def test_modbus_slave_context_interface(self):
        """ Test that the base class isn't implemented """
        x = None
        instance = IModbusSlaveContext()
        self.assertRaises(NotImplementedError, instance.reset)
        self.assertRaises(NotImplementedError, lambda: instance.validate(x, x, x))
        self.assertRaises(NotImplementedError, lambda: instance.get_values(x, x, x))
        self.assertRaises(NotImplementedError, lambda: instance.set_values(x, x, x))

    def test_modbus_payload_builder_interface(self):
        """ Test that the base class isn't implemented """
        x = None
        instance = IPayloadBuilder()
        self.assertRaises(NotImplementedError, lambda: instance.build())

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
