"""
Bit Message Test Fixture
--------------------------------
This fixture tests the functionality of all the 
bit based request/response messages:

* Read/Write Discretes
* Read Coils
"""
import unittest
import struct
from pymodbus3.bit_read_message import *
from pymodbus3.bit_read_message import ReadBitsRequestBase
from pymodbus3.bit_read_message import ReadBitsResponseBase
from pymodbus3.pdu import ModbusExceptions
from .modbus_mocks import MockContext

#---------------------------------------------------------------------------#
# Fixture
#---------------------------------------------------------------------------#


class ModbusBitMessageTests(unittest.TestCase):

    #-----------------------------------------------------------------------#
    # Setup/TearDown
    #-----------------------------------------------------------------------#

    def setUp(self):
        """
        Initializes the test environment and builds request/result
        encoding pairs
        """
        pass

    def tearDown(self):
        """ Cleans up the test environment """
        pass

    def test_read_bit_base_class_methods(self):
        """ Test basic bit message encoding/decoding """
        handle = ReadBitsRequestBase(1, 1)
        msg = "ReadBitRequest(1,1)"
        self.assertEqual(msg, str(handle))
        handle = ReadBitsResponseBase([1, 1])
        msg = "ReadBitResponse(2)"
        self.assertEqual(msg, str(handle))

    def test_read_bit_base_request_encoding(self):
        """ Test basic bit message encoding/decoding """
        for i in range(20):
            handle = ReadBitsRequestBase(i, i)
            result = struct.pack('>HH', i, i)
            self.assertEqual(handle.encode(), result)
            handle.decode(result)
            self.assertEqual((handle.address, handle.count), (i, i))

    def test_read_bit_base_response_encoding(self):
        """ Test basic bit message encoding/decoding """
        for i in range(20):
            input_val = [True] * i
            handle = ReadBitsResponseBase(input_val)
            result = handle.encode()
            handle.decode(result)
            self.assertEqual(handle.bits[:i], input_val)

    def test_read_bit_base_response_helper_methods(self):
        """ Test the extra methods on a ReadBitsResponseBase """
        input_val = [False] * 8
        handle = ReadBitsResponseBase(input_val)
        for i in [1, 3, 5]:
            handle.set_bit(i, True)
        for i in [1, 3, 5]:
            handle.reset_bit(i)
        for i in range(8):
            self.assertEqual(handle.get_bit(i), False)

    def test_bit_read_base_requests(self):
        """ Test bit read request encoding """
        messages = {
            ReadBitsRequestBase(12, 14): '\x00\x0c\x00\x0e',
            ReadBitsResponseBase([1, 0, 1, 1, 0]): '\x01\x0d',
        }
        for request, expected in messages.items():
            self.assertEqual(request.encode(), expected)

    def test_bit_read_message_execute_value_errors(self):
        """ Test bit read request encoding """
        context = MockContext()
        requests = [
            ReadCoilsRequest(1, 0x800),
            ReadDiscreteInputsRequest(1, 0x800),
        ]
        for request in requests:
            result = request.execute(context)
            self.assertEqual(
                ModbusExceptions.IllegalValue,
                result.exception_code
            )

    def test_bit_read_message_execute_address_errors(self):
        """ Test bit read request encoding """
        context = MockContext()
        requests = [
            ReadCoilsRequest(1, 5),
            ReadDiscreteInputsRequest(1, 5),
        ]
        for request in requests:
            result = request.execute(context)
            self.assertEqual(ModbusExceptions.IllegalAddress, result.exception_code)

    def test_bit_read_message_execute_success(self):
        """ Test bit read request encoding """
        context = MockContext()
        context.validate = lambda a, b, c: True
        requests = [
            ReadCoilsRequest(1, 5),
            ReadDiscreteInputsRequest(1, 5),
        ]
        for request in requests:
            result = request.execute(context)
            self.assertEqual(result.bits, [True] * 5)

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
