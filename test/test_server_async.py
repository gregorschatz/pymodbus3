import unittest
from mock import patch, Mock
from pymodbus3.device import ModbusDeviceIdentification
from pymodbus3.server.async import ModbusTcpProtocol, ModbusUdpProtocol
from pymodbus3.server.async import ModbusServerFactory
from pymodbus3.server.async import StartTcpServer, StartUdpServer, StartSerialServer

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#


class AsynchronousServerTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.server.async module
    """

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def setUp(self):
        """
        Initializes the test environment
        """
        values = dict((i, '') for i in range(10))
        identity = ModbusDeviceIdentification(info=values)

    def tearDown(self):
        """ Cleans up the test environment """
        pass

    #-----------------------------------------------------------------------#
    # Test Modbus Server Factory
    #-----------------------------------------------------------------------#

    def test_modbus_server_factory(self):
        """ Test the base class for all the clients """
        factory = ModbusServerFactory(store=None)
        self.assertEqual(factory.control.Identity.VendorName, '')

        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        factory = ModbusServerFactory(store=None, identity=identity)
        self.assertEqual(factory.control.Identity.VendorName, 'VendorName')

    #-----------------------------------------------------------------------#
    # Test Modbus TCP Server
    #-----------------------------------------------------------------------#
    def test_tcp_server_disconnect(self):
        protocol = ModbusTcpProtocol()
        protocol.connectionLost('because of an error')

    #-----------------------------------------------------------------------#
    # Test Modbus UDP Server
    #-----------------------------------------------------------------------#
    def test_udp_server_initialize(self):
        protocol = ModbusUdpProtocol(store=None)
        self.assertEqual(protocol.control.Identity.VendorName, '')

        identity = ModbusDeviceIdentification(info={0x00: 'VendorName'})
        protocol = ModbusUdpProtocol(store=None, identity=identity)
        self.assertEqual(protocol.control.Identity.VendorName, 'VendorName')

    #-----------------------------------------------------------------------#
    # Test Modbus Server Startups
    #-----------------------------------------------------------------------#

    def test_tcp_server_startup(self):
        """ Test that the modbus tcp async server starts correctly """
        with patch('twisted.internet.reactor') as mock_reactor:
            StartTcpServer(context=None, console=True)
            self.assertEqual(mock_reactor.listenTCP.call_count, 2)
            self.assertEqual(mock_reactor.run.call_count, 1)

    def test_udp_server_startup(self):
        """ Test that the modbus udp async server starts correctly """
        with patch('twisted.internet.reactor') as mock_reactor:
            StartUdpServer(context=None)
            self.assertEqual(mock_reactor.listenUDP.call_count, 1)
            self.assertEqual(mock_reactor.run.call_count, 1)

    def test_serial_server_startup(self):
        """ Test that the modbus serial async server starts correctly """
        with patch('twisted.internet.reactor') as mock_reactor:
            StartSerialServer(context=None, port='/dev/ptmx')
            self.assertEqual(mock_reactor.run.call_count, 1)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
