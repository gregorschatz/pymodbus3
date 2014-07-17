import unittest
from pymodbus3.pdu import *


class SimplePduTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.pdu module
    """

    def setUp(self):
        """ Initializes the test environment """
        self.badRequests = (
            #ModbusPDU(),
            ModbusRequest(),
            ModbusResponse(),
        )
        self.illegal = IllegalFunctionRequest(1)
        self.exception = ExceptionResponse(1, 1)

    def tearDown(self):
        """ Cleans up the test environment """
        del self.badRequests
        del self.illegal
        del self.exception

    def test_not_implemented(self):
        """ Test a base classes for not implemented functions """
        for r in self.badRequests:
            self.assertRaises(NotImplementedError, r.encode)

        for r in self.badRequests:
            self.assertRaises(NotImplementedError, r.decode, None)

    def test_error_methods(self):
        """ Test all error methods """
        self.illegal.decode("12345")
        self.illegal.execute(None)

        result = self.exception.encode()
        self.exception.decode(result)
        self.assertEqual(result, '\x01')
        self.assertEqual(self.exception.exception_code, 1)

    def test_request_exception_factory(self):
        """ Test all error methods """
        request = ModbusRequest()
        request.function_code = 1
        errors = dict((ModbusExceptions.decode(c), c) for c in range(1, 20))
        for error, code in errors.items():
            result = request.do_exception(code)
            self.assertEqual(str(result), "Exception Response(129, 1, {0})".format(error))

    def test_calculate_rtu_frame_size(self):
        """ Test the calculation of Modbus/RTU frame sizes """
        self.assertRaises(
            NotImplementedError,
            ModbusRequest.calculate_rtu_frame_size, ""
        )
        ModbusRequest._rtu_frame_size = 5
        self.assertEqual(ModbusRequest.calculate_rtu_frame_size(""), 5)
        del ModbusRequest._rtu_frame_size

        ModbusRequest._rtu_byte_count_pos = 2
        self.assertEqual(
            ModbusRequest.calculate_rtu_frame_size("\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6"),
            0x05 + 5
        )
        del ModbusRequest._rtu_byte_count_pos
        
        self.assertRaises(
            NotImplementedError,
            ModbusResponse.calculate_rtu_frame_size, ""
        )
        ModbusResponse._rtu_frame_size = 12
        self.assertEqual(ModbusResponse.calculate_rtu_frame_size(""), 12)
        del ModbusResponse._rtu_frame_size
        ModbusResponse._rtu_byte_count_pos = 2
        self.assertEqual(
            ModbusResponse.calculate_rtu_frame_size("\x11\x01\x05\xcd\x6b\xb2\x0e\x1b\x45\xe6"),
            0x05 + 5
        )
        del ModbusResponse._rtu_byte_count_pos


#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
