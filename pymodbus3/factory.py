# -*- coding: utf-8 -*-

"""
Modbus Request/Response Decoder Factories
-------------------------------------------

The following factories make it easy to decode request/response messages.
To add a new request/response pair to be decodeable by the library, simply
add them to the respective function lookup table (order doesn't matter, but
it does help keep things organized).

Regardless of how many functions are added to the lookup, O(1) behavior is
kept as a result of a pre-computed lookup dictionary.
"""

from pymodbus3.pdu import IllegalFunctionRequest
from pymodbus3.pdu import ExceptionResponse
from pymodbus3.pdu import ModbusExceptions
from pymodbus3.interfaces import IModbusDecoder
from pymodbus3.exceptions import ModbusException
import pymodbus3.bit_read_message as bit_read_msg
import pymodbus3.bit_write_message as bit_write_msg
import pymodbus3.diag_message as diag_msg
import pymodbus3.file_message as file_msg
import pymodbus3.other_message as other_msg
import pymodbus3.mei_message as mei_msg
import pymodbus3.register_read_message as reg_read_msg
import pymodbus3.register_write_message as reg_write_msg

# Logging
import logging
_logger = logging.getLogger(__name__)


class ServerDecoder(IModbusDecoder):
    """ Request Message Factory (Server)

    To add more implemented functions, simply add them to the list
    """
    __function_table = [
        reg_read_msg.ReadHoldingRegistersRequest,
        bit_read_msg.ReadDiscreteInputsRequest,
        reg_read_msg.ReadInputRegistersRequest,
        bit_read_msg.ReadCoilsRequest,
        bit_write_msg.WriteMultipleCoilsRequest,
        reg_write_msg.WriteMultipleRegistersRequest,
        reg_write_msg.WriteSingleRegisterRequest,
        bit_write_msg.WriteSingleCoilRequest,
        reg_read_msg.ReadWriteMultipleRegistersRequest,

        diag_msg.DiagnosticStatusRequest,

        other_msg.ReadExceptionStatusRequest,
        other_msg.GetCommEventCounterRequest,
        other_msg.GetCommEventLogRequest,
        other_msg.ReportSlaveIdRequest,

        file_msg.ReadFileRecordRequest,
        file_msg.WriteFileRecordRequest,
        file_msg.MaskWriteRegisterRequest,
        file_msg.ReadFifoQueueRequest,

        mei_msg.ReadDeviceInformationRequest,
    ]
    __sub_function_table = [
        diag_msg.ReturnQueryDataRequest,
        diag_msg.RestartCommunicationsOptionRequest,
        diag_msg.ReturnDiagnosticRegisterRequest,
        diag_msg.ChangeAsciiInputDelimiterRequest,
        diag_msg.ForceListenOnlyModeRequest,
        diag_msg.ClearCountersRequest,
        diag_msg.ReturnBusMessageCountRequest,
        diag_msg.ReturnBusCommunicationErrorCountRequest,
        diag_msg.ReturnBusExceptionErrorCountRequest,
        diag_msg.ReturnSlaveMessageCountRequest,
        diag_msg.ReturnSlaveNoResponseCountRequest,
        diag_msg.ReturnSlaveNAKCountRequest,
        diag_msg.ReturnSlaveBusyCountRequest,
        diag_msg.ReturnSlaveBusCharacterOverrunCountRequest,
        diag_msg.ReturnIopOverrunCountRequest,
        diag_msg.ClearOverrunCountRequest,
        diag_msg.GetClearModbusPlusRequest,

        mei_msg.ReadDeviceInformationRequest,
    ]

    def __init__(self):
        """ Initializes the client lookup tables
        """
        functions = set(f.function_code for f in self.__function_table)
        self.__lookup = dict()
        for f in self.__function_table:
            self.__lookup[f.function_code] = f
        self.__sub_lookup = dict((f, {}) for f in functions)
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f

    def decode(self, message):
        """ Wrapper to decode a request packet

        :param message: The raw modbus request packet
        :return: The decoded modbus message or None if error
        """
        try:
            return self._helper(message)
        except ModbusException as er:
            _logger.warn('Unable to decode request ' + str(er))
        return None

    def lookup_pdu_class(self, function_code):
        """ Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        """
        return self.__lookup.get(function_code, ExceptionResponse)

    def _helper(self, data):
        """
        This factory is used to generate the correct request object
        from a valid request packet. This decodes from a list of the
        currently implemented request types.

        :param data: The request packet to decode
        :returns: The decoded request or illegal function request object
        """
        function_code = data[0]
        _logger.debug('Factory Request[{0}]'.format(function_code))
        request = self.__lookup.get(function_code, lambda: None)()
        if not request:
            request = IllegalFunctionRequest(function_code)
        request.decode(data[1:])

        if hasattr(request, 'sub_function_code'):
            lookup = self.__sub_lookup.get(request.function_code, {})
            subtype = lookup.get(request.sub_function_code, None)
            if subtype:
                request.__class__ = subtype

        return request


class ClientDecoder(IModbusDecoder):
    """ Response Message Factory (Client)

    To add more implemented functions, simply add them to the list
    """
    __function_table = [
        reg_read_msg.ReadHoldingRegistersResponse,
        bit_read_msg.ReadDiscreteInputsResponse,
        reg_read_msg.ReadInputRegistersResponse,
        bit_read_msg.ReadCoilsResponse,
        bit_write_msg.WriteMultipleCoilsResponse,
        reg_write_msg.WriteMultipleRegistersResponse,
        reg_write_msg.WriteSingleRegisterResponse,
        bit_write_msg.WriteSingleCoilResponse,
        reg_read_msg.ReadWriteMultipleRegistersResponse,

        diag_msg.DiagnosticStatusResponse,

        other_msg.ReadExceptionStatusResponse,
        other_msg.GetCommEventCounterResponse,
        other_msg.GetCommEventLogResponse,
        other_msg.ReportSlaveIdResponse,

        file_msg.ReadFileRecordResponse,
        file_msg.WriteFileRecordResponse,
        file_msg.MaskWriteRegisterResponse,
        file_msg.ReadFifoQueueResponse,

        mei_msg.ReadDeviceInformationResponse,
    ]
    __sub_function_table = [
        diag_msg.ReturnQueryDataResponse,
        diag_msg.RestartCommunicationsOptionResponse,
        diag_msg.ReturnDiagnosticRegisterResponse,
        diag_msg.ChangeAsciiInputDelimiterResponse,
        diag_msg.ForceListenOnlyModeResponse,
        diag_msg.ClearCountersResponse,
        diag_msg.ReturnBusMessageCountResponse,
        diag_msg.ReturnBusCommunicationErrorCountResponse,
        diag_msg.ReturnBusExceptionErrorCountResponse,
        diag_msg.ReturnSlaveMessageCountResponse,
        diag_msg.ReturnSlaveNoResponseCountResponse,
        diag_msg.ReturnSlaveNAKCountResponse,
        diag_msg.ReturnSlaveBusyCountResponse,
        diag_msg.ReturnSlaveBusCharacterOverrunCountResponse,
        diag_msg.ReturnIopOverrunCountResponse,
        diag_msg.ClearOverrunCountResponse,
        diag_msg.GetClearModbusPlusResponse,
        mei_msg.ReadDeviceInformationResponse,
    ]

    def __init__(self):
        """ Initializes the client lookup tables
        """
        functions = set(f.function_code for f in self.__function_table)
        self.__lookup = dict()
        for f in self.__function_table:
            self.__lookup[f.function_code] = f
        self.__sub_lookup = dict((f, {}) for f in functions)
        for f in self.__sub_function_table:
            self.__sub_lookup[f.function_code][f.sub_function_code] = f

    def lookup_pdu_class(self, function_code):
        """ Use `function_code` to determine the class of the PDU.

        :param function_code: The function code specified in a frame.
        :returns: The class of the PDU that has a matching `function_code`.
        """
        return self.__lookup.get(function_code, ExceptionResponse)

    def decode(self, message):
        """ Wrapper to decode a response packet

        :param message: The raw packet to decode
        :return: The decoded modbus message or None if error
        """
        try:
            return self._helper(message)
        except ModbusException as er:
            _logger.error('Unable to decode response ' + str(er))
        return None

    def _helper(self, data):
        """
        This factory is used to generate the correct response object
        from a valid response packet. This decodes from a list of the
        currently implemented request types.

        :param data: The response packet to decode
        :returns: The decoded request or an exception response object
        """
        function_code = data[0]
        _logger.debug('Factory Response[{0}]'.format(function_code))
        response = self.__lookup.get(function_code, lambda: None)()
        if function_code > 0x80:
            code = function_code & 0x7f  # strip error portion
            response = ExceptionResponse(
                code, ModbusExceptions.IllegalFunction
            )
        if not response:
            raise ModbusException('Unknown response ' + str(function_code))
        response.decode(data[1:])

        if hasattr(response, 'sub_function_code'):
            lookup = self.__sub_lookup.get(response.function_code, {})
            subtype = lookup.get(response.sub_function_code, None)
            if subtype:
                response.__class__ = subtype

        return response


# Exported symbols
__all__ = ['ServerDecoder', 'ClientDecoder']
