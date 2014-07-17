# -*- coding: utf-8 -*-

"""
Collection of transaction based abstractions
"""
import struct
import socket
from binascii import b2a_hex, a2b_hex
from pymodbus3.exceptions import ModbusIOException
from pymodbus3.constants import Defaults, FramerState
from pymodbus3.interfaces import IModbusFramer
from pymodbus3.utilities import check_crc, compute_crc
from pymodbus3.utilities import check_lrc, compute_lrc

# Logging
import logging
_logger = logging.getLogger(__name__)


# region The Global Transaction Manager

class ModbusTransactionManager(object):
    """ Implements a transaction for a manager

    The transaction protocol can be represented by the following pseudo code::

        count = 0
        do
          result = send(message)
          if (timeout or result == bad)
             count++
          else break
        while (count < 3)

    This module helps to abstract this away from the framer and protocol.
    """

    def __init__(self, client, **kwargs):
        """ Initializes an instance of the ModbusTransactionManager

        :param client: The client socket wrapper
        :param retry_on_empty: Should the client retry on empty
        :param retries: The number of retries to allow
        """
        self.transactions = None
        self.state = None
        self.tid = Defaults.TransactionId
        self.client = client
        self.framer = client and client.framer
        self.retry_on_empty = kwargs.get(
            'retry_on_empty', Defaults.RetryOnEmpty
        )
        self.retries = kwargs.get('retries', Defaults.Retries)

    def execute(self, request):
        """ Starts the producer to send the next request to
        consumer.write(Frame(request))
        """
        retries = self.retries
        request.transaction_id = self.get_next_tid()
        _logger.debug('Running transaction ' + str(request.transaction_id))

        while retries > 0:
            try:
                self.state = FramerState.Initializing
                self.client.connect()
                self.client.send(self.client.framer.build_packet(request))
                if not self.handle_message_framing():
                    raise ModbusIOException(
                        'Server responded with bad response'
                    )
                break
            except socket.error as msg:
                self.client.close()
                _logger.debug('Transaction failed ' + str(msg))
                retries -= 1
        return self.get_transaction(request.transaction_id)

    def handle_message_framing(self):
        """ This abstracts performing all the framing logic
        using a simple state machine.

        It should be explained that the original framer design
        was intended to be used by the twisted framework and to
        respond to streams provided by a single async callback.
        That is why the design is as it is now.

        Along the way a number of users asked for a non-twisted
        version, using stock python. In order to do this I tried
        to simply reuse the existing framing code with a few hacks.
        It turned out to be poor fit.

        In order to not have to rewrite the entire framing base,
        I am simply using it to implement the following state
        machine directly which should take care of a number of
        legacy issues.

        **The Management**
        """
        retries = self.retries  # we want to allow a few errors

        while retries > 0:
            # before we start reading, we allow the framer to
            # put itself into a newly consistent state.
            if self.state == FramerState.Initializing:
                self.framer.advance_frame()  # initialize
                self.state = FramerState.ReadingHeader

            # we know how much to read for the fixed size
            # header, so we loop until we have it to guide us.
            elif self.state == FramerState.ReadingHeader:
                size = self.framer.header_size - len(self.framer.buffer)
                if size != 0:
                    result = self.client.receive(size)  # off by one on clear
                    if not result:
                        if self.retry_on_empty:
                            retries -= 1
                        else:
                            self.state = FramerState.ErrorInFrame
                    self.framer.add_to_frame(result)
                    size -= len(result)
                if size <= 0:
                    self.framer.check_frame()  # decode header
                    self.state = FramerState.ReadingContent

            # after we have the header, we know how much content
            # to read and continue until we finish or fail.
            elif self.state == FramerState.ReadingContent:
                size = self.framer.get_frame_size() - len(self.framer.buffer)
                if size != 0:
                    result = self.client.receive(size)
                    if not result:
                        if self.retry_on_empty:
                            retries -= 1
                        else:
                            self.state = FramerState.ErrorInFrame
                    self.framer.add_to_frame(result)
                    size -= len(result)
                if size <= 0:
                    self.state = FramerState.CompleteFrame

            # if we get a complete frame, we simply pass it on to
            # the application code to process. In this case, we
            # simply add it to the transaction manager.
            elif self.state == FramerState.CompleteFrame:
                self.framer.process_incoming_packet('', self.add_transaction)
                return True

            # if we get into an error state, we have to clear
            # the current frame and alert the application code
            # that there was an error.
            elif self.state == FramerState.ErrorInFrame:
                self.framer.reset_frame()
                return False

            # this shouldn't happen, but just in case
            else:
                self.state = FramerState.ErrorInFrame
        return False

    def add_transaction(self, request, tid=None):
        """ Adds a transaction to the handler

        This holds the requests in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        """
        raise NotImplementedError('add_transaction')

    def get_transaction(self, tid):
        """ Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        """
        raise NotImplementedError('get_transaction')

    def del_transaction(self, tid):
        """ Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        """
        raise NotImplementedError('del_transaction')

    def get_next_tid(self):
        """ Retrieve the next unique transaction identifier

        This handles incrementing the identifier after
        retrieval

        :returns: The next unique transaction identifier
        """
        self.tid = (self.tid + 1) & 0xffff
        return self.tid

    def reset(self):
        """ Resets the transaction identifier """
        self.tid = Defaults.TransactionId
        self.transactions = type(self.transactions)()


class DictTransactionManager(ModbusTransactionManager):
    """ Implements a transaction for a manager where the
    results are keyed based on the supplied transaction id.
    """

    def __init__(self, client, **kwargs):
        """ Initializes an instance of the ModbusTransactionManager

        :param client: The client socket wrapper
        """
        super().__init__(client, **kwargs)
        self.transactions = dict()

    def __iter__(self):
        """ Iterates over the current managed transactions

        :returns: An iterator of the managed transactions
        """
        return self.transactions.keys()

    def add_transaction(self, request, tid=None):
        """ Adds a transaction to the handler

        This holds the requests in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        """
        tid = request.transaction_id if tid is None else tid
        _logger.debug('adding transaction ' + str(tid))
        self.transactions[tid] = request

    def get_transaction(self, tid):
        """ Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        """
        _logger.debug('getting transaction ' + str(tid))
        return self.transactions.pop(tid, None)

    def del_transaction(self, tid):
        """ Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        """
        _logger.debug('deleting transaction ' + str(tid))
        self.transactions.pop(tid, None)


class FifoTransactionManager(ModbusTransactionManager):
    """ Implements a transaction for a manager where the
    results are returned in a FIFO manner.
    """

    def __init__(self, client, **kwargs):
        """ Initializes an instance of the ModbusTransactionManager

        :param client: The client socket wrapper
        """
        super().__init__(client, **kwargs)
        self.transactions = list()

    def __iter__(self):
        """ Iterates over the current managed transactions

        :returns: An iterator of the managed transactions
        """
        return iter(self.transactions)

    def add_transaction(self, request, tid=None):
        """ Adds a transaction to the handler

        This holds the requests in case it needs to be resent.
        After being sent, the request is removed.

        :param request: The request to hold on to
        :param tid: The overloaded transaction id to use
        """
        tid = request.transaction_id if tid is None else tid
        _logger.debug('adding transaction ' + str(tid))
        self.transactions.append(request)

    def get_transaction(self, tid):
        """ Returns a transaction matching the referenced tid

        If the transaction does not exist, None is returned

        :param tid: The transaction to retrieve
        """
        _logger.debug('getting transaction ' + str(tid))
        return self.transactions.pop(0) if self.transactions else None

    def del_transaction(self, tid):
        """ Removes a transaction matching the referenced tid

        :param tid: The transaction to remove
        """
        _logger.debug('deleting transaction ' + str(tid))
        if self.transactions:
            self.transactions.pop(0)

# endregion


# region Messages

class ModbusSocketFramer(IModbusFramer):
    """ Modbus Socket Frame controller

    Before each modbus TCP message is an MBAP header which is used as a
    message frame.  It allows us to easily separate messages as follows::

        [         MBAP Header         ] [ Function Code] [ Data ]
        [ tid ][ pid ][ length ][ uid ]
          2b     2b     2b        1b           1b           Nb

        while len(message) > 0:
            tid, pid, length`, uid = struct.unpack(">HHHB", message)
            request = message[0:7 + length - 1`]
            message = [7 + length - 1:]

        * length = uid + function code + data
        * The -1 is to account for the uid byte
    """

    # region initialization

    def __init__(self, decoder):
        """ Initializes a new instance of the framer

        :param decoder: The decoder factory implementation to use
        """
        super().__init__(decoder)
        self.buffer = b''
        self.header = {'tid': 0, 'pid': 0, 'len': 0, 'uid': 0}
        self.header_size = 0x07

    # endregion

    # region methods

    def check_frame(self):
        """
        Check and decode the next frame Return true if we were successful
        """
        if len(self.buffer) >= self.header_size:
            self.header['tid'], self.header['pid'], self.header['len'], self.header['uid'] =\
                struct.unpack('>HHHB', self.buffer[0:self.header_size])

            # someone sent us an error? ignore it
            if self.header['len'] < 2:
                self.advance_frame()
            # we have at least a complete message, continue
            elif len(self.buffer) - self.header_size + 1 >= self.header['len']:
                return True
        # we don't have enough of a message yet, wait
        return False

    def advance_frame(self):
        """ Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        length = self.get_frame_size()
        self.buffer = self.buffer[length:]
        self.header = {'tid': 0, 'pid': 0, 'len': 0, 'uid': 0}

    def reset_frame(self):
        """ Reset the entire message frame.
        This allows us to skip over errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        """
        self.advance_frame()

    def add_to_frame(self, message):
        """ Adds new packet data to the current frame buffer

        :param message: The most recent packet
        """
        self.buffer += message

    def is_frame_ready(self):
        """ Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder factory know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        return len(self.buffer) > self.header_size

    def get_frame_size(self):
        """ Return to the framer's current knowledge
        the total size of the frame

        :returns: The current size of the frame
        """
        return self.header_size + max(0, self.header['len'] - 1)

    def get_frame(self):
        """ Return the next frame from the buffered data

        :returns: The next full frame buffer
        """
        length = self.get_frame_size()
        return self.buffer[self.header_size:length]

    def populate_result(self, result):
        """
        Populates the modbus result with the transport specific header
        information (pid, tid, uid, checksum, etc)

        :param result: The response packet
        """
        result.transaction_id = self.header['tid']
        result.protocol_id = self.header['pid']
        result.unit_id = self.header['uid']

    def build_packet(self, message):
        """ Creates a ready to send modbus packet

        :param message: The populated request/response to send
        """
        data = message.encode()
        packet = struct.pack(
            '>HHHBB',
            message.transaction_id,
            message.protocol_id,
            len(data) + 2,
            message.unit_id,
            message.function_code
        ) + data
        return packet

    # endregion

    pass


class ModbusRtuFramer(IModbusFramer):
    """
    Modbus RTU Frame controller::

        [ Start Wait ] [Address ][ Function Code] [ Data ][ CRC ][  End Wait  ]
          3.5 chars     1b         1b               Nb      2b      3.5 chars

    Wait refers to the amount of time required to transmit at least x many
    characters.  In this case it is 3.5 characters.  Also, if we receive a
    wait of 1.5 characters at any point, we must trigger an error message.
    Also, it appears as though this message is little endian. The logic is
    simplified as the following::

        block-on-read:
            read until 3.5 delay
            check for errors
            decode

    The following table is a listing of the baud wait times for the specified
    baud rates::

        ------------------------------------------------------------------
         Baud  1.5c (18 bits)   3.5c (38 bits)
        ------------------------------------------------------------------
         1200   13333.3 us       31666.7 us
         4800    3333.3 us        7916.7 us
         9600    1666.7 us        3958.3 us
        19200     833.3 us        1979.2 us
        38400     416.7 us         989.6 us
        ------------------------------------------------------------------
        1 Byte = start + 8 bits + parity + stop = 11 bits
        (1/Baud)(bits) = delay seconds
    """

    # region initialization

    def __init__(self, decoder):
        """ Initializes a new instance of the framer

        :param decoder: The decoder factory implementation to use
        """
        super().__init__(decoder)
        self.buffer = b''
        self.header = {'lrc': '0000', 'len': 0, 'uid': 0x00}
        self.header_size = 0x01
        self.__end = b'\x0d\x0a'
        self.__min_frame_size = 4

    # endregion

    # region methods

    def check_frame(self):
        """
        Check if the next frame is available. Return True if we were
        successful.
        """
        try:
            self.populate_header()
            frame_size = self.header['len']
            data = self.buffer[:frame_size - 2]
            crc = self.buffer[frame_size - 2:frame_size]
            crc_val = (crc[0] << 8) + crc[1]
            return check_crc(data, crc_val)
        except (IndexError, KeyError):
            return False

    def advance_frame(self):
        """ Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        self.buffer = self.buffer[self.header['len']:]
        self.header = {'lrc': '0000', 'len': 0, 'uid': 0x00}

    def reset_frame(self):
        """ Reset the entire message frame.
        This allows us to skip over errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        """
        self.buffer = b''
        self.header = {'lrc': '0000', 'len': 0, 'uid': 0x00}

    def is_frame_ready(self):
        """ Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        return len(self.buffer) > self.header_size

    def get_frame_size(self):
        """ Return to the framer's current knowledge
        the total size of the frame

        :returns: The current size of the frame
        """
        size = self.header['len']
        return size if size != 0 else len(self.buffer) + 1

    def populate_header(self):
        """ Try to set the headers `uid`, `len` and `crc`.

        This method examines `self.buffer` and writes meta
        information into `self.header`. It calculates only the
        values for headers that are not already in the dictionary.

        Beware that this method will raise an IndexError if
        `self.buffer` is not yet long enough.
        """
        self.header['uid'] = self.buffer[0]
        func_code = self.buffer[1]
        pdu_class = self.decoder.lookup_pdu_class(func_code)
        size = pdu_class.calculate_rtu_frame_size(self.buffer)
        self.header['len'] = size
        self.header['crc'] = self.buffer[size - 2:size]

    def add_to_frame(self, message):
        """
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        """
        self.buffer += message

    def get_frame(self):
        """ Get the next frame from the buffer

        :returns: The frame data or ''
        """
        start = self.header_size
        end = self.header['len'] - 2
        buffer = self.buffer[start:end]
        if end > 0:
            return buffer
        return ''

    def populate_result(self, result):
        """ Populates the modbus result header

        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        """
        result.unit_id = self.header['uid']

    def build_packet(self, message):
        """ Creates a ready to send modbus packet

        :param message: The populated request/response to send
        """
        data = message.encode()
        packet = struct.pack(
            '>BB',
            message.unit_id,
            message.function_code
        ) + data
        packet += struct.pack('>H', compute_crc(packet))
        return packet

    # endregion

    pass


class ModbusAsciiFramer(IModbusFramer):
    """
    Modbus ASCII Frame Controller::

        [ Start ][Address ][ Function ][ Data ][ LRC ][ End ]
          1c        2c         2c         Nc     2c      2c

        * data can be 0 - 2x252 chars
        * end is '\\r\\n' (Carriage return line feed), however the line feed
          character can be changed via a special command
        * start is ':'

    This framer is used for serial transmission.  Unlike the RTU protocol,
    the data in this framer is transferred in plain text ascii.
    """

    # region initialization

    def __init__(self, decoder):
        """ Initializes a new instance of the framer

        :param decoder: The decoder implementation to use
        """
        super().__init__(decoder)
        self.buffer = b''
        self.header = {'lrc': '0000', 'len': 0, 'uid': 0x00}
        self.header_size = 0x02
        self.__start = b':'
        self.__end = b"\r\n"

    # endregion

    # region method

    def check_frame(self):
        """ Check and decode the next frame

        :returns: True if we successful, False otherwise
        """
        start = self.buffer.find(self.__start)
        if start == -1:
            return False
        if start > 0:  # go ahead and skip old bad data
            self.buffer = self.buffer[start:]
            start = 0

        end = self.buffer.find(self.__end)
        if end != -1:
            self.header['len'] = end
            self.header['uid'] = int(self.buffer[1:3], 16)
            self.header['lrc'] = int(self.buffer[end - 2:end], 16)
            data = a2b_hex(self.buffer[start + 1:end - 2])
            return check_lrc(data, self.header['lrc'])
        return False

    def advance_frame(self):
        """ Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        self.buffer = self.buffer[self.header['len'] + 2:]
        self.header = {'lrc': '0000', 'len': 0, 'uid': 0x00}

    def reset_frame(self):
        """ Reset the entire message frame.
        This allows us to skip over errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        """
        self.advance_frame()

    def add_to_frame(self, message):
        """ Add the next message to the frame buffer
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        """
        self.buffer += message

    def is_frame_ready(self):
        """ Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        return len(self.buffer) > self.header_size

    def get_frame_size(self):
        """ Return to the framer's current knowledge
        the total size of the frame

        :returns: The current size of the frame
        """
        size = self.header['len']
        return size if size != 0 else len(self.buffer) + 1

    def get_frame(self):
        """ Get the next frame from the buffer

        :returns: The frame data or ''
        """
        start = self.header_size + 1
        end = self.header['len'] - 2
        data = self.buffer[start:end]
        if end > 0:
            return a2b_hex(data)
        return b''

    def populate_result(self, result):
        """ Populates the modbus result header

        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        """
        result.unit_id = self.header['uid']

    def build_packet(self, message):
        """ Creates a ready to send modbus packet
        Built off of a  modbus request/response

        :param message: The request/response to send
        :return: The encoded packet
        """
        encoded = message.encode()
        data = struct.pack('>BB', message.unit_id, message.function_code)
        checksum = compute_lrc(encoded + data)

        packet = bytearray()
        params = (message.unit_id, message.function_code)
        packet.extend(self.__start)
        packet.extend(('%02x%02x' % params).encode())
        packet.extend(b2a_hex(encoded))
        packet.extend(('%02x' % checksum).encode())
        packet.extend(self.__end)
        return bytes(packet).upper()

    # endregion

    pass


class ModbusBinaryFramer(IModbusFramer):
    """
    Modbus Binary Frame Controller::

        [ Start ][Address ][ Function ][ Data ][ CRC ][ End ]
          1b        1b         1b         Nb     2b     1b

        * data can be 0 - 2x252 chars
        * end is   '}'
        * start is '{'

    The idea here is that we implement the RTU protocol, however,
    instead of using timing for message delimiting, we use start
    and end of message characters (in this case { and }). Basically,
    this is a binary framer.

    The only case we have to watch out for is when a message contains
    the { or } characters.  If we encounter these characters, we
    simply duplicate them.  Hopefully we will not encounter those
    characters that often and will save a little bit of bandwitch
    without a real-time system.

    Protocol defined by jamod.sourceforge.net.
    """

    # region initialization

    def __init__(self, decoder):
        """ Initializes a new instance of the framer

        :param decoder: The decoder implementation to use
        """
        super().__init__(decoder)
        self.buffer = b''
        self.header = {'crc': 0x0000, 'len': 0, 'uid': 0x00}
        self.header_size = 0x02
        self.__start = b'\x7b'  # {
        self.__end = b'\x7d'  # }
        self.__repeat = [b'}'[0], b'{'[0]]

    # endregion

    # region methods

    def check_frame(self):
        """ Check and decode the next frame

        :returns: True if we are successful, False otherwise
        """
        start = self.buffer.find(self.__start)
        if start == -1:
            return False
        if start > 0:  # go ahead and skip old bad data
            self.buffer = self.buffer[start:]

        end = self.buffer.find(self.__end)
        if end != -1:
            self.header['len'] = end
            self.header['uid'] = struct.unpack('>B', self.buffer[1:2])
            self.header['crc'] =\
                struct.unpack('>H', self.buffer[end - 2:end])[0]
            data = self.buffer[start + 1:end - 2]
            return check_crc(data, self.header['crc'])
        return False

    def advance_frame(self):
        """ Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        self.buffer = self.buffer[self.header['len'] + 2:]
        self.header = {'crc': 0x0000, 'len': 0, 'uid': 0x00}

    def reset_frame(self):
        """ Reset the entire message frame.
        This allows us to skip over errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        """
        self.advance_frame()

    def add_to_frame(self, message):
        """ Add the next message to the frame buffer
        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        """
        self.buffer += message

    def is_frame_ready(self):
        """ Check if we should continue decode logic
        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        return len(self.buffer) > self.header_size

    def get_frame_size(self):
        """ Return to the framer's current knowledge
        the total size of the frame

        :returns: The current size of the frame
        """
        size = self.header['len']
        return size if size != 0 else len(self.buffer) + 1

    def get_frame(self):
        """ Get the next frame from the buffer

        :returns: The frame data or ''
        """
        start = self.header_size + 1
        end = self.header['len'] - 2
        buffer = self.buffer[start:end]
        if end > 0:
            return buffer
        return b''

    def populate_result(self, result):
        """ Populates the modbus result header

        The serial packets do not have any header information
        that is copied.

        :param result: The response packet
        """
        result.unit_id = self.header['uid']

    def build_packet(self, message):
        """ Creates a ready to send modbus packet

        :param message: The request/response to send
        :returns: The encoded packet
        """
        data = self._preflight(message.encode())
        packet = struct.pack(
            '>BB',
            message.unit_id,
            message.function_code
        ) + data
        packet += struct.pack(">H", compute_crc(packet))
        packet = self.__start + packet + self.__end
        return packet

    def _preflight(self, data):
        """ Preflight buffer test

        This basically scans the buffer for start and end
        tags and if found, escapes them.

        :param data: The message to escape
        :returns: the escaped packet
        """
        array = bytearray()
        for d in data:
            if d in self.__repeat:
                array.append(d)
            array.append(d)
        return bytes(array)

    # endregion

    pass

# endregion


# Exported symbols
__all__ = [
    'FifoTransactionManager',
    'DictTransactionManager',
    'ModbusSocketFramer',
    'ModbusRtuFramer',
    'ModbusAsciiFramer',
    'ModbusBinaryFramer',
]
