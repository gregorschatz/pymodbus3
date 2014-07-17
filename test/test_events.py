import unittest
from pymodbus3.events import *
from pymodbus3.exceptions import ParameterException


class ModbusEventsTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.device module
    """

    def setUp(self):
        """ Sets up the test environment """
        pass

    def tearDown(self):
        """ Cleans up the test environment """
        pass

    def test_modbus_event_base_class(self):
        event = ModbusEvent()
        self.assertRaises(NotImplementedError, event.encode)
        self.assertRaises(NotImplementedError, lambda: event.decode(None))

    def test_remote_receive_event(self):
        event = RemoteReceiveEvent()
        event.decode('\x70')
        self.assertTrue(event.overrun)
        self.assertTrue(event.listen)
        self.assertTrue(event.broadcast)

    def test_remote_sent_event(self):
        event = RemoteSendEvent()
        result = event.encode()
        self.assertEqual(result, '\x40')
        event.decode('\x7f')
        self.assertTrue(event.read)
        self.assertTrue(event.slave_abort)
        self.assertTrue(event.slave_busy)
        self.assertTrue(event.slave_nak)
        self.assertTrue(event.write_timeout)
        self.assertTrue(event.listen)

    def test_remote_sent_event_encode(self):
        arguments = {
            'read': True,
            'slave_abort': True,
            'slave_busy': True,
            'slave_nak': True,
            'write_timeout': True,
            'listen': True,
        }
        event = RemoteSendEvent(**arguments)
        result = event.encode()
        self.assertEqual(result, '\x7f')

    def test_entered_listen_mode_event(self):
        event = EnteredListenModeEvent()
        result = event.encode()
        self.assertEqual(result, '\x04')
        event.decode('\x04')
        self.assertEqual(event.value, 0x04)
        self.assertRaises(ParameterException, lambda: event.decode('\x00'))

    def test_communication_restart_event(self):
        event = CommunicationRestartEvent()
        result = event.encode()
        self.assertEqual(result, '\x00')
        event.decode('\x00')
        self.assertEqual(event.value, 0x00)
        self.assertRaises(ParameterException, lambda: event.decode('\x04'))

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
