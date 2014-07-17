import unittest
from mock import Mock
from pymodbus3.client.async import ModbusClientProtocol, ModbusUdpClientProtocol
from pymodbus3.client.async import ModbusClientFactory
from pymodbus3.exceptions import ConnectionException
from pymodbus3.transaction import ModbusSocketFramer
from pymodbus3.bit_read_message import ReadCoilsRequest, ReadCoilsResponse

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#


class AsynchronousClientTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.client.async module
    """

    #-----------------------------------------------------------------------#
    # Test Client Protocol
    #-----------------------------------------------------------------------#

    def test_client_protocol_init(self):
        """ Test the client protocol initialize """
        protocol = ModbusClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))
        self.assertFalse(protocol._connected)
        self.assertTrue(isinstance(protocol.framer, ModbusSocketFramer))

        framer = object()
        protocol = ModbusClientProtocol(framer=framer)
        self.assertEqual(0, len(list(protocol.transaction)))
        self.assertFalse(protocol._connected)
        self.assertTrue(framer is protocol.framer)

    def test_client_protocol_connect(self):
        """ Test the client protocol connect """
        protocol = ModbusClientProtocol()
        self.assertFalse(protocol._connected)
        protocol.connectionMade()
        self.assertTrue(protocol._connected)

    def test_client_protocol_disconnect(self):
        """ Test the client protocol disconnect """
        protocol = ModbusClientProtocol()
        protocol.connectionMade()

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.value, ConnectionException))
        d = protocol._buildResponse(0x00)
        d.addErrback(handle_failure)

        self.assertTrue(protocol._connected)
        protocol.connectionLost('because')
        self.assertFalse(protocol._connected)

    def test_client_protocol_data_received(self):
        """ Test the client protocol data received """
        protocol = ModbusClientProtocol()
        protocol.connectionMade()
        out = []
        data = '\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04'

        # setup existing request
        d = protocol._buildResponse(0x00)
        d.addCallback(lambda v: out.append(v))

        protocol.dataReceived(data)
        self.assertTrue(isinstance(out[0], ReadCoilsResponse))

    def test_client_protocol_execute(self):
        """ Test the client protocol execute method """
        protocol = ModbusClientProtocol()
        protocol.connectionMade()
        protocol.transport = Mock()
        protocol.transport.write = Mock()

        request = ReadCoilsRequest(1, 1)
        d = protocol.execute(request)
        tid = request.transaction_id
        self.assertEqual(d, protocol.transaction.getTransaction(tid))

    def test_client_protocol_handle_response(self):
        """ Test the client protocol handles responses """
        protocol = ModbusClientProtocol()
        protocol.connectionMade()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        protocol._handleResponse(None)
        protocol._handleResponse(reply)

        # handle existing cases
        d = protocol._buildResponse(0x00)
        d.addCallback(lambda v: out.append(v))
        protocol._handleResponse(reply)
        self.assertEqual(out[0], reply)

    def test_client_protocol_build_response(self):
        """ Test the udp client protocol builds responses """
        protocol = ModbusClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.value, ConnectionException))
        d = protocol._buildResponse(0x00)
        d.addErrback(handle_failure)
        self.assertEqual(0, len(list(protocol.transaction)))

        protocol._connected = True
        d = protocol._buildResponse(0x00)
        self.assertEqual(1, len(list(protocol.transaction)))

    #-----------------------------------------------------------------------#
    # Test Udp Client Protocol
    #-----------------------------------------------------------------------#

    def test_udp_client_protocol_init(self):
        """ Test the udp client protocol initialize """
        protocol = ModbusUdpClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))
        self.assertTrue(isinstance(protocol.framer, ModbusSocketFramer))

        framer = object()
        protocol = ModbusClientProtocol(framer=framer)
        self.assertTrue(framer is protocol.framer)

    def test_udp_client_protocol_data_received(self):
        """ Test the udp client protocol data received """
        protocol = ModbusUdpClientProtocol()
        out = []
        data = '\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04'
        server = ('127.0.0.1', 12345)

        # setup existing request
        d = protocol._buildResponse(0x00)
        d.addCallback(lambda v: out.append(v))

        protocol.datagramReceived(data, server)
        self.assertTrue(isinstance(out[0], ReadCoilsResponse))

    def test_udp_client_protocol_execute(self):
        """ Test the udp client protocol execute method """
        protocol = ModbusUdpClientProtocol()
        protocol.transport = Mock()
        protocol.transport.write = Mock()

        request = ReadCoilsRequest(1, 1)
        d = protocol.execute(request)
        tid = request.transaction_id
        self.assertEqual(d, protocol.transaction.getTransaction(tid))

    def test_udp_client_protocol_handle_response(self):
        """ Test the udp client protocol handles responses """
        protocol = ModbusUdpClientProtocol()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        protocol._handleResponse(None)
        protocol._handleResponse(reply)

        # handle existing cases
        d = protocol._buildResponse(0x00)
        d.addCallback(lambda v: out.append(v))
        protocol._handleResponse(reply)
        self.assertEqual(out[0], reply)

    def test_udp_client_protocol_build_response(self):
        """ Test the udp client protocol builds responses """
        protocol = ModbusUdpClientProtocol()
        self.assertEqual(0, len(list(protocol.transaction)))

        d = protocol._buildResponse(0x00)
        self.assertEqual(1, len(list(protocol.transaction)))

    #-----------------------------------------------------------------------#
    # Test Client Factories
    #-----------------------------------------------------------------------#

    def test_modbus_client_factory(self):
        """ Test the base class for all the clients """
        factory = ModbusClientFactory()
        self.assertTrue(factory is not None)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
