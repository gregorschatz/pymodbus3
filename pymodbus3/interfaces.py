# -*- coding: utf-8 -*-

"""
Pymodbus3 Interfaces
---------------------

A collection of base classes that are used throughout
the pymodbus3 library.
"""

from abc import ABCMeta, abstractmethod
from pymodbus3.exceptions import ModbusIOException


class Singleton(object):
    """
    Singleton base class
    http://mail.python.org/pipermail/python-list/2007-July/450681.html
    """
    def __new__(cls, *args, **kwargs):
        """ Create a new instance
        """
        if '_inst' not in vars(cls):
            cls._inst = object.__new__(cls)
        return cls._inst


class IModbusDecoder(metaclass=ABCMeta):
    """ Modbus Decoder Base Class

    This interface must be implemented by a modbus message
    decoder factory. These factories are responsible for
    abstracting away converting a raw packet into a request / response
    message object.
    """

    @abstractmethod
    def decode(self, message):
        """ Wrapper to decode a given packet

        :param message: The raw modbus request packet
        :return: The decoded modbus message or None if error
        """
        raise NotImplementedError('Method not implemented by derived class')

    @abstractmethod
    def lookup_pdu_class(self, function_code):
        """ Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        """
        raise NotImplementedError('Method not implemented by derived class')


class IModbusFramer(metaclass=ABCMeta):
    """
    A framer strategy interface. The idea is that we abstract away all the
    detail about how to detect if a current message frame exists, decoding
    it, sending it, etc so that we can plug in a new Framer object (tcp,
    rtu, ascii).
    """

    # region initialization

    def __init__(self, decoder):
        self.__buffer = None
        self.__header = None
        self.__header_size = None
        self.__decoder = None
        self.decoder = decoder

    # endregion

    # region properties

    @property
    def buffer(self):
        return self.__buffer

    @buffer.setter
    def buffer(self, value):
        self.__buffer = value

    @property
    def header(self):
        return self.__header

    @header.setter
    def header(self, value):
        self.__header = value

    @property
    def header_size(self):
        return self.__header_size

    @header_size.setter
    def header_size(self, value):
        self.__header_size = value

    @property
    def decoder(self):
        return self.__decoder

    @decoder.setter
    def decoder(self, value):
        self.__decoder = value

    # endregion

    # region abstract methods

    @abstractmethod
    def check_frame(self):
        """ Check and decode the next frame

        :returns: True if we successful, False otherwise
        """
        raise NotImplementedError('Method not implemented by derived class')

    @abstractmethod
    def advance_frame(self):
        """ Skip over the current framed message
        This allows us to skip over the current message after we have processed
        it or determined that it contains an error. It also has to reset the
        current frame header handle
        """
        raise NotImplementedError('Method not implemented by derived class')

    @abstractmethod
    def reset_frame(self):
        """ Reset the entire message frame.
        This allows us to skip over errors that may be in the stream.
        It is hard to know if we are simply out of sync or if there is
        an error in the stream as we have no way to check the start or
        end of the message (python just doesn't have the resolution to
        check for millisecond delays).
        """
        raise NotImplementedError('Method not implemented by derived class')

    @abstractmethod
    def add_to_frame(self, message):
        """ Add the next message to the frame buffer

        This should be used before the decoding while loop to add the received
        data to the buffer handle.

        :param message: The most recent packet
        """
        raise NotImplementedError('Method not implemented by derived class')

    @abstractmethod
    def is_frame_ready(self):
        """ Check if we should continue decode logic

        This is meant to be used in a while loop in the decoding phase to let
        the decoder know that there is still data in the buffer.

        :returns: True if ready, False otherwise
        """
        raise NotImplementedError('Method not implemented by derived class')

    @abstractmethod
    def get_frame_size(self):
        """ Return to the framer's current knowledge
        the total size of the frame

        :returns: The current size of the frame
        """
        raise NotImplementedError('Method not implemented by derived class')

    @abstractmethod
    def get_frame(self):
        """ Get the next frame from the buffer

        :returns: The frame data or ''
        """
        raise NotImplementedError('Method not implemented by derived class')

    @abstractmethod
    def populate_result(self, result):
        """ Populates the modbus result with current frame header

        We basically copy the data back over from the current header
        to the result header. This may not be needed for serial messages.

        :param result: The response packet
        """
        raise NotImplementedError('Method not implemented by derived class')

    @abstractmethod
    def build_packet(self, message):
        """ Creates a ready to send modbus packet

        The raw packet is built off of a fully populated modbus
        request / response message.

        :param message: The request/response to send
        :returns: The built packet
        """
        raise NotImplementedError('Method not implemented by derived class')

    # endregion

    # region realized methods

    def process_incoming_packet(self, data, callback):
        """ The new packet processing pattern

        This takes in a new request packet, adds it to the current
        packet stream, and performs framing on it. That is, checks
        for complete messages, and once found, will process all that
        exist.  This handles the case when we read N + 1 or 1 / N
        messages at a time instead of 1.

        The processed and decoded messages are pushed to the callback
        function to process and send.

        :param data: The new packet data
        :param callback: The function to send results to
        """
        if data:
            self.add_to_frame(data)
        while self.is_frame_ready():
            if self.check_frame():
                result = self.decoder.decode(self.get_frame())
                if result is None:
                    raise ModbusIOException('Unable to decode request')
                self.populate_result(result)
                self.advance_frame()
                callback(result)  # defer or push to a thread?
            else:
                break

    # endregion

    pass


class IModbusSlaveContext(metaclass=ABCMeta):
    """
    Interface for a modbus slave data context

    Derived classes must implemented the following methods:
            reset(self)
            validate(self, fx, address, count=1)
            get_values(self, fx, address, count=1)
            set_values(self, fx, address, values)
    """
    __fx_mapper = {2: 'd', 4: 'i'}
    __fx_mapper.update([(i, 'h') for i in [3, 6, 16, 22, 23]])
    __fx_mapper.update([(i, 'c') for i in [1, 5, 15]])

    def decode(self, fx):
        """ Converts the function code to the datastore to

        :param fx: The function we are working with
        :returns: one of [d(iscretes),i(inputs),h(oliding),c(oils)
        """
        return self.__fx_mapper[fx]

    @abstractmethod
    def reset(self):
        """ Resets all the datastores to their default values
        """
        raise NotImplementedError('Context Reset')

    @abstractmethod
    def validate(self, fx, address, count=1):
        """ Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to test
        :returns: True if the request in within range, False otherwise
        """
        raise NotImplementedError('validate context values')

    @abstractmethod
    def get_values(self, fx, address, count=1):
        """ Validates the request to make sure it is in range

        :param fx: The function we are working with
        :param address: The starting address
        :param count: The number of values to retrieve
        :returns: The requested values from a:a+c
        """
        raise NotImplementedError('get context values')

    @abstractmethod
    def set_values(self, fx, address, values):
        """ Sets the datastore with the supplied values

        :param fx: The function we are working with
        :param address: The starting address
        :param values: The new values to be set
        """
        raise NotImplementedError('set context values')


class IPayloadBuilder(metaclass=ABCMeta):
    """
    This is an interface to a class that can build a payload
    for a modbus register write command. It should abstract
    the codec for encoding data to the required format
    (bcd, binary, char, etc).
    """

    @abstractmethod
    def build(self):
        """ Return the payload buffer as a list

        This list is two bytes per element and can
        thus be treated as a list of registers.

        :returns: The payload buffer as a list
        """
        raise NotImplementedError('set context values')


# Exported symbols
__all__ = [
    'Singleton',
    'IModbusDecoder',
    'IModbusFramer',
    'IModbusSlaveContext',
    'IPayloadBuilder',
]
