import unittest
import socket
import serial
from mock import patch, Mock
from twisted.test import test_protocols
from pymodbus3.client.sync import ModbusTcpClient, ModbusUdpClient
from pymodbus3.client.sync import ModbusSerialClient, BaseModbusClient
from pymodbus3.exceptions import ConnectionException
from pymodbus3.exceptions import ParameterException
from pymodbus3.transaction import ModbusAsciiFramer, ModbusRtuFramer
from pymodbus3.transaction import ModbusBinaryFramer

#---------------------------------------------------------------------------#
# Mock Classes
#---------------------------------------------------------------------------#


class MockSocket(object):

    def close(self):
        return True

    def recv(self, size):
        return '\x00' * size

    def read(self, size):
        return '\x00' * size

    def send(self, msg):
        return len(msg)

    def write(self, msg):
        return len(msg)

    def recvfrom(self, size):
        return ['\x00'*size]

    def sendto(self, msg, *args):
        return len(msg)

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#


class SynchronousClientTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.client.sync module
    """

    #-----------------------------------------------------------------------#
    # Test Base Client
    #-----------------------------------------------------------------------#

    def test_base_modbus_client(self):
        """ Test the base class for all the clients """

        client = BaseModbusClient(None)
        client.transaction = None
        self.assertRaises(NotImplementedError, lambda: client.connect())
        self.assertRaises(NotImplementedError, lambda: client.send(None))
        self.assertRaises(NotImplementedError, lambda: client.receive(None))
        self.assertRaises(NotImplementedError, lambda: client.__enter__())
        self.assertRaises(NotImplementedError, lambda: client.execute())
        self.assertEquals("Null Transport", str(client))
        client.close()
        client.__exit__(0, 0, 0)

        # a successful execute
        client.connect = lambda: True
        client.transaction = Mock(**{'execute.return_value': True})
        self.assertEqual(client, client.__enter__())
        self.assertTrue(client.execute())

        # a unsuccessful connect
        client.connect = lambda: False
        self.assertRaises(ConnectionException, lambda: client.__enter__())
        self.assertRaises(ConnectionException, lambda: client.execute())

    #-----------------------------------------------------------------------#
    # Test UDP Client
    #-----------------------------------------------------------------------#

    def test_sync_udp_client_instantiation(self):
        client = ModbusUdpClient()
        self.assertNotEqual(client, None)

    def test_basic_sync_udp_client(self):
        """ Test the basic methods for the udp sync client"""

        # receive/send
        client = ModbusUdpClient()
        client.socket = MockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(1, client.send('\x00'))
        self.assertEqual('\x00', client.receive(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("127.0.0.1:502", str(client))

    def test_udp_client_address_family(self):
        """ Test the Udp client get address family method"""
        client = ModbusUdpClient()
        self.assertEqual(socket.AF_INET, client._get_address_family('127.0.0.1'))
        self.assertEqual(socket.AF_INET6, client._get_address_family('::1'))

    def test_udp_client_connect(self):
        """ Test the Udp client connection method"""
        with patch.object(socket, 'socket') as mock_method:
            mock_method.return_value = object()
            client = ModbusUdpClient()
            self.assertTrue(client.connect())

        with patch.object(socket, 'socket') as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusUdpClient()
            self.assertFalse(client.connect())

    def test_udp_client_send(self):
        """ Test the udp client send method"""
        client = ModbusUdpClient()
        self.assertRaises(ConnectionException, lambda: client.send(None))

        client.socket = MockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(4, client.send('1234'))

    def test_udp_client_recv(self):
        """ Test the udp client receive method"""
        client = ModbusUdpClient()
        self.assertRaises(ConnectionException, lambda: client.receive(1024))

        client.socket = MockSocket()
        self.assertEqual('', client.receive(0))
        self.assertEqual('\x00'*4, client.receive(4))

    #-----------------------------------------------------------------------#
    # Test TCP Client
    #-----------------------------------------------------------------------#
    
    def test_sync_tcp_client_instantiation(self):
        client = ModbusTcpClient()
        self.assertNotEqual(client, None)

    def test_basic_sync_tcp_client(self):
        """ Test the basic methods for the tcp sync client"""

        # receive/send
        client = ModbusTcpClient()
        client.socket = MockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(1, client.send('\x00'))
        self.assertEqual('\x00', client.receive(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual("127.0.0.1:502", str(client))

    def test_tcp_client_connect(self):
        """ Test the tcp client connection method"""
        with patch.object(socket, 'create_connection') as mock_method:
            mock_method.return_value = object()
            client = ModbusTcpClient()
            self.assertTrue(client.connect())

        with patch.object(socket, 'create_connection') as mock_method:
            mock_method.side_effect = socket.error()
            client = ModbusTcpClient()
            self.assertFalse(client.connect())

    def test_tcp_client_send(self):
        """ Test the tcp client send method"""
        client = ModbusTcpClient()
        self.assertRaises(ConnectionException, lambda: client.send(None))

        client.socket = MockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(4, client.send('1234'))

    def test_tcp_client_recv(self):
        """ Test the tcp client receive method"""
        client = ModbusTcpClient()
        self.assertRaises(ConnectionException, lambda: client.receive(1024))

        client.socket = MockSocket()
        self.assertEqual('', client.receive(0))
        self.assertEqual('\x00'*4, client.receive(4))
    
    #-----------------------------------------------------------------------#
    # Test Serial Client
    #-----------------------------------------------------------------------#

    def test_sync_serial_client_instantiation(self):
        client = ModbusSerialClient()
        self.assertNotEqual(client, None)
        self.assertTrue(isinstance(ModbusSerialClient(method='ascii').framer, ModbusAsciiFramer))
        self.assertTrue(isinstance(ModbusSerialClient(method='rtu').framer, ModbusRtuFramer))
        self.assertTrue(isinstance(ModbusSerialClient(method='binary').framer, ModbusBinaryFramer))
        self.assertRaises(ParameterException, lambda: ModbusSerialClient(method='something'))

    def test_basic_sync_serial_client(self):
        """ Test the basic methods for the serial sync client"""

        # receive/send
        client = ModbusSerialClient()
        client.socket = MockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(1, client.send('\x00'))
        self.assertEqual('\x00', client.receive(1))

        # connect/disconnect
        self.assertTrue(client.connect())
        client.close()

        # already closed socket
        client.socket = False
        client.close()

        self.assertEqual('ascii baud[19200]', str(client))

    def test_serial_client_connect(self):
        """ Test the serial client connection method"""
        with patch.object(serial, 'Serial') as mock_method:
            mock_method.return_value = object()
            client = ModbusSerialClient()
            self.assertTrue(client.connect())

        with patch.object(serial, 'Serial') as mock_method:
            mock_method.side_effect = serial.SerialException()
            client = ModbusSerialClient()
            self.assertFalse(client.connect())

    def test_serial_client_send(self):
        """ Test the serial client send method"""
        client = ModbusSerialClient()
        self.assertRaises(ConnectionException, lambda: client.send(None))

        client.socket = MockSocket()
        self.assertEqual(0, client.send(None))
        self.assertEqual(4, client.send('1234'))

    def test_serial_client_receive(self):
        """ Test the serial client receive method"""
        client = ModbusSerialClient()
        self.assertRaises(ConnectionException, lambda: client.receive(1024))

        client.socket = MockSocket()
        self.assertEqual('', client.receive(0))
        self.assertEqual('\x00'*4, client.receive(4))

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
