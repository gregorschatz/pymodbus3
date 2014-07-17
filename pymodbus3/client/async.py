# -*- coding: utf-8 -*-

"""
Implementation of a Modbus Client Using Twisted
--------------------------------------------------

Example run::

    from twisted.internet import reactor, protocol
    from pymodbus3.client.async import ModbusClientProtocol

    def printResult(result):
        print "Result: %d" % result.bits[0]

    def process(client):
        result = client.write_coil(1, True)
        result.addCallback(printResult)
        reactor.callLater(1, reactor.stop)

    defer = protocol.ClientCreator(reactor, ModbusClientProtocol
            ).connectTCP("localhost", 502)
    defer.addCallback(process)

Another example::

    from twisted.internet import reactor
    from pymodbus3.client.async import ModbusClientFactory

    def process():
        factory = reactor.connectTCP("localhost", 502, ModbusClientFactory())
        reactor.stop()

    if __name__ == "__main__":
       reactor.callLater(1, process)
       reactor.run()
"""
from twisted.internet import defer, protocol
from pymodbus3.factory import ClientDecoder
from pymodbus3.exceptions import ConnectionException
from pymodbus3.transaction import ModbusSocketFramer
from pymodbus3.transaction import FifoTransactionManager
from pymodbus3.transaction import DictTransactionManager
from pymodbus3.client.common import ModbusClientMixin
from twisted.python.failure import Failure

# Logging
import logging
_logger = logging.getLogger(__name__)


class ModbusClientProtocol(protocol.Protocol, ModbusClientMixin):
    """
    This represents the base modbus client protocol.  All the application
    layer code is deferred to a higher level wrapper.
    """

    def __init__(self, framer=None, **kwargs):
        """ Initializes the framer module

        :param framer: The framer to use for the protocol
        """
        self._connected = False
        self.framer = framer or ModbusSocketFramer(ClientDecoder())
        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self, **kwargs)
        else:
            self.transaction = FifoTransactionManager(self, **kwargs)

    def connection_made(self):
        """ Called upon a successful client connection.
        """
        _logger.debug('Client connected to modbus server')
        self._connected = True

    def connection_lost(self, reason):
        """ Called upon a client disconnect

        :param reason: The reason for the disconnect
        """
        _logger.debug('Client disconnected from modbus server: ' + str(reason))
        self._connected = False
        for tid in list(self.transaction):
            self.transaction.get_transaction(tid).errback(
                Failure(ConnectionException('Connection lost during request'))
            )

    def data_received(self, data):
        """ Get response, check for valid message, decode result

        :param data: The data returned from the server
        """
        self.framer.process_incoming_packet(data, self._handle_response)

    def execute(self, request):
        """ Starts the producer to send the next request to
        consumer.write(Frame(request))
        """
        request.transaction_id = self.transaction.get_next_tid()
        packet = self.framer.build_packet(request)
        self.transport.write(packet)
        return self._build_response(request.transaction_id)

    def _handle_response(self, reply):
        """ Handle the processed response and link to correct deferred

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.get_transaction(tid)
            if handler:
                handler.callback(reply)
            else:
                _logger.debug('Unrequested message: ' + str(reply))

    def _build_response(self, tid):
        """ Helper method to return a deferred response
        for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        if not self._connected:
            return defer.fail(Failure(
                ConnectionException('Client is not connected')))

        d = defer.Deferred()
        self.transaction.add_transaction(d, tid)
        return d


class ModbusUdpClientProtocol(protocol.DatagramProtocol, ModbusClientMixin):
    """
    This represents the base modbus client protocol.  All the application
    layer code is deferred to a higher level wrapper.
    """

    def __init__(self, framer=None, **kwargs):
        """ Initializes the framer module

        :param framer: The framer to use for the protocol
        """
        self.framer = framer or ModbusSocketFramer(ClientDecoder())
        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self, **kwargs)
        else:
            self.transaction = FifoTransactionManager(self, **kwargs)

    def datagram_received(self, data, params):
        """ Get response, check for valid message, decode result

        :param data: The data returned from the server
        :param params: The host parameters sending the datagram
        """
        _logger.debug('Datagram from: {0}:{1}'.format(*params))
        self.framer.process_incoming_packet(data, self._handle_response)

    def execute(self, request):
        """ Starts the producer to send the next request to
        consumer.write(Frame(request))
        """
        request.transaction_id = self.transaction.get_next_tid()
        packet = self.framer.build_packet(request)
        self.transport.write(packet)
        return self._build_response(request.transaction_id)

    def _handle_response(self, reply):
        """ Handle the processed response and link to correct deferred

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.get_transaction(tid)
            if handler:
                handler.callback(reply)
            else:
                _logger.debug('Unrequested message: ' + str(reply))

    def _build_response(self, tid):
        """ Helper method to return a deferred response
        for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
        d = defer.Deferred()
        self.transaction.add_transaction(d, tid)
        return d


class ModbusClientFactory(protocol.ReconnectingClientFactory):
    """ Simple client protocol factory """

    protocol = ModbusClientProtocol


# Exported symbols

__all__ = [
    'ModbusClientProtocol',
    'ModbusUdpClientProtocol',
    'ModbusClientFactory',
]
