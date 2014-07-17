import unittest
from binascii import a2b_hex
from pymodbus3.pdu import *
from pymodbus3.factory import ServerDecoder
import pymodbus3.transaction


class ModbusTransactionTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus3.transaction module
    """

    #---------------------------------------------------------------------------#
    # Test Construction
    #---------------------------------------------------------------------------#
    def setUp(self):
        """ Sets up the test environment """
        self.client = None
        self.decoder = ServerDecoder()
        self._tcp = pymodbus3.transaction.ModbusSocketFramer(decoder=self.decoder)
        self._rtu = pymodbus3.transaction.ModbusRtuFramer(decoder=self.decoder)
        self._ascii = pymodbus3.transaction.ModbusAsciiFramer(decoder=self.decoder)
        self._binary = pymodbus3.transaction.ModbusBinaryFramer(decoder=self.decoder)
        self._manager = pymodbus3.transaction.DictTransactionManager(self.client)
        self._queue_manager = pymodbus3.transaction.FifoTransactionManager(self.client)

    def tearDown(self):
        """ Cleans up the test environment """
        del self._manager
        del self._tcp
        del self._rtu
        del self._ascii

    #---------------------------------------------------------------------------# 
    # Dictionary based transaction manager
    #---------------------------------------------------------------------------# 
    def test_dict_transaction_manager_tid(self):
        """ Test the dict transaction manager TID """
        for tid in range(1, self._manager.get_next_tid() + 10):
            self.assertEqual(tid+1, self._manager.get_next_tid())
        self._manager.reset()
        self.assertEqual(1, self._manager.get_next_tid())

    def test_get_dict_transaction_manager_transaction(self):
        """ Test the dict transaction manager """
        class Request:
            pass
        self._manager.reset()
        handle = Request()
        handle.transaction_id = self._manager.get_next_tid()
        handle.message = "testing"
        self._manager.add_transaction(handle)
        result = self._manager.get_transaction(handle.transaction_id)
        self.assertEqual(handle.message, result.message)

    def test_delete_dict_transaction_manager_transaction(self):
        """ Test the dict transaction manager """
        class Request:
            pass
        self._manager.reset()
        handle = Request()
        handle.transaction_id = self._manager.get_next_tid()
        handle.message = "testing"
        self._manager.add_transaction(handle)
        self._manager.del_transaction(handle.transaction_id)
        self.assertEqual(None, self._manager.get_transaction(handle.transaction_id))

    #---------------------------------------------------------------------------# 
    # Queue based transaction manager
    #---------------------------------------------------------------------------# 
    def test_fifo_transaction_manager_tid(self):
        """ Test the fifo transaction manager TID """
        for tid in range(1, self._queue_manager.get_next_tid() + 10):
            self.assertEqual(tid+1, self._queue_manager.get_next_tid())
        self._queue_manager.reset()
        self.assertEqual(1, self._queue_manager.get_next_tid())

    def test_get_fifo_transaction_manager_transaction(self):
        """ Test the fifo transaction manager """
        class Request:
            pass
        self._queue_manager.reset()
        handle = Request()
        handle.transaction_id = self._queue_manager.get_next_tid()
        handle.message = "testing"
        self._queue_manager.add_transaction(handle)
        result = self._queue_manager.get_transaction(handle.transaction_id)
        self.assertEqual(handle.message, result.message)

    def test_delete_fifo_transaction_manager_transaction(self):
        """ Test the fifo transaction manager """
        class Request:
            pass
        self._queue_manager.reset()
        handle = Request()
        handle.transaction_id = self._queue_manager.get_next_tid()
        handle.message = "testing"
        self._queue_manager.add_transaction(handle)
        self._queue_manager.del_transaction(handle.transaction_id)
        self.assertEqual(None, self._queue_manager.get_transaction(handle.transaction_id))

    #---------------------------------------------------------------------------# 
    # TCP tests
    #---------------------------------------------------------------------------#
    def test_tcp_framer_transaction_ready(self):
        """ Test a tcp frame transaction """
        msg = "\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self.assertFalse(self._tcp.is_frame_ready())
        self.assertFalse(self._tcp.check_frame())
        self._tcp.add_to_frame(msg)
        self.assertTrue(self._tcp.is_frame_ready())
        self.assertTrue(self._tcp.check_frame())
        self._tcp.advance_frame()
        self.assertFalse(self._tcp.is_frame_ready())
        self.assertFalse(self._tcp.check_frame())
        self.assertEqual('', self._ascii.get_frame())

    def test_tcp_framer_transaction_full(self):
        """ Test a full tcp frame transaction """
        msg = "\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.add_to_frame(msg)
        self.assertTrue(self._tcp.check_frame())
        result = self._tcp.get_frame()
        self.assertEqual(msg[7:], result)
        self._tcp.advance_frame()

    def test_tcp_framer_transaction_half(self):
        """ Test a half completed tcp frame transaction """
        msg1 = "\x00\x01\x12\x34\x00"
        msg2 = "\x04\xff\x02\x12\x34"
        self._tcp.add_to_frame(msg1)
        self.assertFalse(self._tcp.check_frame())
        result = self._tcp.get_frame()
        self.assertEqual('', result)
        self._tcp.add_to_frame(msg2)
        self.assertTrue(self._tcp.check_frame())
        result = self._tcp.get_frame()
        self.assertEqual(msg2[2:], result)
        self._tcp.advance_frame()

    def test_tcp_framer_transaction_half2(self):
        """ Test a half completed tcp frame transaction """
        msg1 = "\x00\x01\x12\x34\x00\x04\xff"
        msg2 = "\x02\x12\x34"
        self._tcp.add_to_frame(msg1)
        self.assertFalse(self._tcp.check_frame())
        result = self._tcp.get_frame()
        self.assertEqual('', result)
        self._tcp.add_to_frame(msg2)
        self.assertTrue(self._tcp.check_frame())
        result = self._tcp.get_frame()
        self.assertEqual(msg2, result)
        self._tcp.advance_frame()

    def test_tcp_framer_transaction_half3(self):
        """ Test a half completed tcp frame transaction """
        msg1 = "\x00\x01\x12\x34\x00\x04\xff\x02\x12"
        msg2 = "\x34"
        self._tcp.add_to_frame(msg1)
        self.assertFalse(self._tcp.check_frame())
        result = self._tcp.get_frame()
        self.assertEqual(msg1[7:], result)
        self._tcp.add_to_frame(msg2)
        self.assertTrue(self._tcp.check_frame())
        result = self._tcp.get_frame()
        self.assertEqual(msg1[7:] + msg2, result)
        self._tcp.advance_frame()

    def test_tcp_framer_transaction_short(self):
        """ Test that we can get back on track after an invalid message """
        msg1 = "\x99\x99\x99\x99\x00\x01\x00\x01"
        msg2 = "\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.add_to_frame(msg1)
        self.assertFalse(self._tcp.check_frame())
        result = self._tcp.get_frame()
        self.assertEqual('', result)
        self._tcp.advance_frame()
        self._tcp.add_to_frame(msg2)
        self.assertEqual(10, len(self._tcp._ModbusSocketFramer__buffer))
        self.assertTrue(self._tcp.check_frame())
        result = self._tcp.get_frame()
        self.assertEqual(msg2[7:], result)
        self._tcp.advance_frame()

    def test_tcp_framer_populate(self):
        """ Test a tcp frame packet build """
        expected = ModbusRequest()
        expected.transaction_id = 0x0001
        expected.protocol_id = 0x1234
        expected.unit_id = 0xff
        msg = "\x00\x01\x12\x34\x00\x04\xff\x02\x12\x34"
        self._tcp.add_to_frame(msg)
        self.assertTrue(self._tcp.check_frame())
        actual = ModbusRequest()
        self._tcp.populate_result(actual)
        for name in ['transaction_id', 'protocol_id', 'unit_id']:
            self.assertEqual(getattr(expected, name), getattr(actual, name))
        self._tcp.advance_frame()

    def test_tcp_framer_packet(self):
        """ Test a tcp frame packet build """
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: ''
        message = ModbusRequest()
        message.transaction_id = 0x0001
        message.protocol_id = 0x1234
        message.unit_id = 0xff
        message.function_code = 0x01
        expected = "\x00\x01\x12\x34\x00\x02\xff\x01"
        actual = self._tcp.build_packet(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    #---------------------------------------------------------------------------#
    # RTU tests
    #---------------------------------------------------------------------------#
    def test_rtu_framer_transaction_ready(self):
        """ Test if the checks for a complete frame work """
        self.assertFalse(self._rtu.is_frame_ready())

        msg_parts = ["\x00\x01\x00", "\x00\x00\x01\xfc\x1b"]
        self._rtu.add_to_frame(msg_parts[0])
        self.assertTrue(self._rtu.is_frame_ready())
        self.assertFalse(self._rtu.check_frame())

        self._rtu.add_to_frame(msg_parts[1])
        self.assertTrue(self._rtu.is_frame_ready())
        self.assertTrue(self._rtu.check_frame())

    def test_rtu_framer_transaction_full(self):
        """ Test a full rtu frame transaction """
        msg = "\x00\x01\x00\x00\x00\x01\xfc\x1b"
        stripped_msg = msg[1:-2]
        self._rtu.add_to_frame(msg)
        self.assertTrue(self._rtu.check_frame())
        result = self._rtu.get_frame()
        self.assertEqual(stripped_msg, result)
        self._rtu.advance_frame()

    def test_rtu_framer_transaction_half(self):
        """ Test a half completed rtu frame transaction """
        msg_parts = ["\x00\x01\x00", "\x00\x00\x01\xfc\x1b"]
        stripped_msg = "".join(msg_parts)[1:-2]
        self._rtu.add_to_frame(msg_parts[0])
        self.assertFalse(self._rtu.check_frame())
        self._rtu.add_to_frame(msg_parts[1])
        self.assertTrue(self._rtu.is_frame_ready())
        self.assertTrue(self._rtu.check_frame())
        result = self._rtu.get_frame()
        self.assertEqual(stripped_msg, result)
        self._rtu.advance_frame()

    def test_rtu_framer_populate(self):
        """ Test a rtu frame packet build """
        request = ModbusRequest()
        msg = "\x00\x01\x00\x00\x00\x01\xfc\x1b"
        self._rtu.add_to_frame(msg)
        self._rtu.populate_header()
        self._rtu.populate_result(request)
        header_dict = self._rtu._ModbusRtuFramer__header
        self.assertEqual(len(msg), header_dict['len'])
        self.assertEqual(ord(msg[0]), header_dict['uid'])
        self.assertEqual(msg[-2:], header_dict['crc'])
        self.assertEqual(0x00, request.unit_id)

    def test_rtu_framer_packet(self):
        """ Test a rtu frame packet build """
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: ''
        message = ModbusRequest()
        message.unit_id = 0xff
        message.function_code = 0x01
        expected = "\xff\x01\x81\x80"  # only header + CRC - no data
        actual = self._rtu.build_packet(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    def test_rtu_decode_exception(self):
        """ Test that the RTU framer can decode errors """
        message = "\x00\x90\x02\x9c\x01"
        actual = self._rtu.add_to_frame(message)
        result = self._rtu.check_frame()
        self.assertTrue(result)

    #---------------------------------------------------------------------------#
    # ASCII tests
    #---------------------------------------------------------------------------#
    def test_ascii_framer_transaction_ready(self):
        """ Test a ascii frame transaction """
        msg = ':F7031389000A60\r\n'
        self.assertFalse(self._ascii.is_frame_ready())
        self.assertFalse(self._ascii.check_frame())
        self._ascii.add_to_frame(msg)
        self.assertTrue(self._ascii.is_frame_ready())
        self.assertTrue(self._ascii.check_frame())
        self._ascii.advance_frame()
        self.assertFalse(self._ascii.is_frame_ready())
        self.assertFalse(self._ascii.check_frame())
        self.assertEqual('', self._ascii.get_frame())

    def test_ascii_framer_transaction_full(self):
        """ Test a full ascii frame transaction """
        msg = 'sss:F7031389000A60\r\n'
        pack = a2b_hex(msg[6:-4])
        self._ascii.add_to_frame(msg)
        self.assertTrue(self._ascii.check_frame())
        result = self._ascii.get_frame()
        self.assertEqual(pack, result)
        self._ascii.advance_frame()

    def test_ascii_framer_transaction_half(self):
        """ Test a half completed ascii frame transaction """
        msg1 = 'sss:F7031389'
        msg2 = '000A60\r\n'
        pack = a2b_hex(msg1[6:] + msg2[:-4])
        self._ascii.add_to_frame(msg1)
        self.assertFalse(self._ascii.check_frame())
        result = self._ascii.get_frame()
        self.assertEqual('', result)
        self._ascii.add_to_frame(msg2)
        self.assertTrue(self._ascii.check_frame())
        result = self._ascii.get_frame()
        self.assertEqual(pack, result)
        self._ascii.advance_frame()

    def test_ascii_framer_populate(self):
        """ Test a ascii frame packet build """
        request = ModbusRequest()
        self._ascii.populate_result(request)
        self.assertEqual(0x00, request.unit_id)

    def test_ascii_framer_packet(self):
        """ Test a ascii frame packet build """
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: ''
        message = ModbusRequest()
        message.unit_id = 0xff
        message.function_code = 0x01
        expected = ":FF0100\r\n"
        actual = self._ascii.build_packet(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

    #---------------------------------------------------------------------------#
    # Binary tests
    #---------------------------------------------------------------------------#
    def test_binary_framer_transaction_ready(self):
        """ Test a binary frame transaction """
        msg = '\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d'
        self.assertFalse(self._binary.is_frame_ready())
        self.assertFalse(self._binary.check_frame())
        self._binary.add_to_frame(msg)
        self.assertTrue(self._binary.is_frame_ready())
        self.assertTrue(self._binary.check_frame())
        self._binary.advance_frame()
        self.assertFalse(self._binary.is_frame_ready())
        self.assertFalse(self._binary.check_frame())
        self.assertEqual('', self._binary.get_frame())

    def test_binary_framer_transaction_full(self):
        """ Test a full binary frame transaction """
        msg = '\x7b\x01\x03\x00\x00\x00\x05\x85\xC9\x7d'
        pack = msg[3:-3]
        self._binary.add_to_frame(msg)
        self.assertTrue(self._binary.check_frame())
        result = self._binary.get_frame()
        self.assertEqual(pack, result)
        self._binary.advance_frame()

    def test_binary_framer_transaction_half(self):
        """ Test a half completed binary frame transaction """
        msg1 = '\x7b\x01\x03\x00'
        msg2 = '\x00\x00\x05\x85\xC9\x7d'
        pack = msg1[3:] + msg2[:-3]
        self._binary.add_to_frame(msg1)
        self.assertFalse(self._binary.check_frame())
        result = self._binary.get_frame()
        self.assertEqual('', result)
        self._binary.add_to_frame(msg2)
        self.assertTrue(self._binary.check_frame())
        result = self._binary.get_frame()
        self.assertEqual(pack, result)
        self._binary.advance_frame()

    def test_binary_framer_populate(self):
        """ Test a binary frame packet build """
        request = ModbusRequest()
        self._binary.populate_result(request)
        self.assertEqual(0x00, request.unit_id)

    def test_binary_framer_packet(self):
        """ Test a binary frame packet build """
        old_encode = ModbusRequest.encode
        ModbusRequest.encode = lambda self: ''
        message = ModbusRequest()
        message.unit_id = 0xff
        message.function_code = 0x01
        expected = '\x7b\xff\x01\x81\x80\x7d'
        actual = self._binary.build_packet(message)
        self.assertEqual(expected, actual)
        ModbusRequest.encode = old_encode

#---------------------------------------------------------------------------#
# Main
#---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
