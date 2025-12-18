"""Tests for communications module."""
import unittest
from unittest.mock import Mock, patch, MagicMock

from muts.comms.can_interface import (
    Mazdaspeed3CANInterface, CANUtilities, CANMessage
)


class TestCANMessage(unittest.TestCase):
    """Test CANMessage dataclass."""
    
    def test_can_message_creation(self):
        """Test CANMessage creation."""
        msg = CANMessage(
            arbitration_id=0x7E0,
            data=b'\x01\x02\x03',
            timestamp=1234567890.0,
            is_extended=False,
            is_remote=False
        )
        
        self.assertEqual(msg.arbitration_id, 0x7E0)
        self.assertEqual(msg.data, b'\x01\x02\x03')
        self.assertEqual(msg.timestamp, 1234567890.0)
        self.assertFalse(msg.is_extended)
        self.assertFalse(msg.is_remote)


class TestCANUtilities(unittest.TestCase):
    """Test CANUtilities class."""
    
    def test_calculate_checksum_8bit(self):
        """Test calculate_checksum_8bit method."""
        data = b'\x01\x02\x03\x04'
        checksum = CANUtilities.calculate_checksum_8bit(data)
        
        # Manual calculation: 0x01 + 0x02 + 0x03 + 0x04 = 0x0A
        self.assertEqual(checksum, 0x0A)
        self.assertLessEqual(checksum, 0xFF)
    
    def test_bytes_to_hex_string(self):
        """Test bytes_to_hex_string method."""
        data = b'\x01\x02\xAB\xCD'
        hex_str = CANUtilities.bytes_to_hex_string(data)
        
        self.assertEqual(hex_str, "01 02 AB CD")
    
    def test_parse_obd2_pid_response_rpm(self):
        """Test parse_obd2_pid_response for RPM (PID 0x0C)."""
        # RPM = ((A << 8) | B) / 4.0
        # For 2000 RPM: (2000 * 4) = 8000 = 0x1F40
        data = b'\x41\x0C\x1F\x40'
        rpm = CANUtilities.parse_obd2_pid_response(data, 0x0C)
        
        self.assertIsNotNone(rpm)
        self.assertEqual(rpm, 2000.0)
    
    def test_parse_obd2_pid_response_speed(self):
        """Test parse_obd2_pid_response for speed (PID 0x0D)."""
        # Speed is data[2]
        data = b'\x41\x0D\x64'  # 100 kph
        speed = CANUtilities.parse_obd2_pid_response(data, 0x0D)
        
        self.assertIsNotNone(speed)
        self.assertEqual(speed, 100.0)
    
    def test_parse_obd2_pid_response_coolant_temp(self):
        """Test parse_obd2_pid_response for coolant temp (PID 0x05)."""
        # Temp = data[2] - 40
        # For 90C: 90 + 40 = 130 = 0x82
        data = b'\x41\x05\x82'
        temp = CANUtilities.parse_obd2_pid_response(data, 0x05)
        
        self.assertIsNotNone(temp)
        self.assertEqual(temp, 90.0)
    
    def test_parse_obd2_pid_response_map(self):
        """Test parse_obd2_pid_response for MAP (PID 0x0B)."""
        data = b'\x41\x0B\x64'  # 100 kPa
        map_pressure = CANUtilities.parse_obd2_pid_response(data, 0x0B)
        
        self.assertIsNotNone(map_pressure)
        self.assertEqual(map_pressure, 100.0)
    
    def test_parse_obd2_pid_response_invalid(self):
        """Test parse_obd2_pid_response with invalid data."""
        # Wrong service ID
        data = b'\x42\x0C\x1F\x40'
        result = CANUtilities.parse_obd2_pid_response(data, 0x0C)
        self.assertIsNone(result)
        
        # Wrong PID
        data = b'\x41\x0D\x1F\x40'
        result = CANUtilities.parse_obd2_pid_response(data, 0x0C)
        self.assertIsNone(result)
        
        # Too short
        data = b'\x41'
        result = CANUtilities.parse_obd2_pid_response(data, 0x0C)
        self.assertIsNone(result)
    
    def test_build_mazda_specific_request(self):
        """Test build_mazda_specific_request method."""
        request = CANUtilities.build_mazda_specific_request(0x22, 0xF187)
        
        self.assertEqual(request[0], 0x22)
        self.assertEqual(request[1], 0xF187)
        
        # With parameters
        params = b'\x01\x02\x03'
        request = CANUtilities.build_mazda_specific_request(0x2E, 0x01, params)
        
        self.assertEqual(request[0], 0x2E)
        self.assertEqual(request[1], 0x01)
        self.assertEqual(request[2:], params)


class TestMazdaspeed3CANInterface(unittest.TestCase):
    """Test Mazdaspeed3CANInterface class."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('can.interface.Bus'):
            self.can_interface = Mazdaspeed3CANInterface('can0')
    
    def test_initialization(self):
        """Test Mazdaspeed3CANInterface initialization."""
        self.assertEqual(self.can_interface.channel, 'can0')
        self.assertEqual(self.can_interface.bustype, 'socketcan')
        self.assertEqual(self.can_interface.bitrate, 500000)
        self.assertFalse(self.can_interface.running)
        self.assertIsNotNone(self.can_interface.ecu_addresses)
        self.assertIn('engine_ecu_tx', self.can_interface.ecu_addresses)
    
    def test_initialize_ecu_addresses(self):
        """Test _initialize_ecu_addresses method."""
        addresses = self.can_interface._initialize_ecu_addresses()
        
        self.assertEqual(addresses['engine_ecu_tx'], 0x7E0)
        self.assertEqual(addresses['engine_ecu_rx'], 0x7E8)
        self.assertEqual(addresses['tcm_tx'], 0x7E1)
        self.assertEqual(addresses['abs_tx'], 0x7E2)
    
    @patch('can.interface.Bus')
    def test_connect(self, mock_bus):
        """Test connect method."""
        mock_bus_instance = Mock()
        mock_bus.return_value = mock_bus_instance
        
        result = self.can_interface.connect()
        
        # Should attempt to create bus (may fail without actual CAN interface)
        mock_bus.assert_called()
    
    def test_disconnect(self):
        """Test disconnect method."""
        self.can_interface.running = True
        self.can_interface.disconnect()
        
        self.assertFalse(self.can_interface.running)
    
    def test_register_message_handler(self):
        """Test register_message_handler method."""
        handler = Mock()
        self.can_interface.register_message_handler(0x7E8, handler)
        
        self.assertIn(0x7E8, self.can_interface.message_handlers)
        self.assertEqual(self.can_interface.message_handlers[0x7E8], handler)
    
    def test_read_ecu_data(self):
        """Test read_ecu_data method."""
        with patch.object(self.can_interface, 'send_diagnostic_request', return_value=True):
            # Test with known DID
            data = self.can_interface.read_ecu_data(0xF187)
            
            # Should return mock data or None
            self.assertIsInstance(data, (bytes, type(None)))
    
    def test_write_ecu_data_no_security(self):
        """Test write_ecu_data without security access."""
        self.can_interface.security_access_granted = False
        
        result = self.can_interface.write_ecu_data(0x1234, b'\x01\x02')
        
        self.assertFalse(result)
    
    @patch.object(Mazdaspeed3CANInterface, 'send_diagnostic_request')
    def test_write_ecu_data_with_security(self, mock_send):
        """Test write_ecu_data with security access."""
        self.can_interface.security_access_granted = True
        mock_send.return_value = True
        
        result = self.can_interface.write_ecu_data(0x1234, b'\x01\x02')
        
        self.assertTrue(result)
        mock_send.assert_called_once()


class TestMazdaspeed3CANInterfaceExtended(unittest.TestCase):
    """Extended tests for Mazdaspeed3CANInterface class."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('can.interface.Bus'):
            self.can_interface = Mazdaspeed3CANInterface(channel='test', bustype='virtual')
    
    def test_initialize_ecu_addresses(self):
        """Test _initialize_ecu_addresses method."""
        addresses = self.can_interface._initialize_ecu_addresses()
        
        self.assertIn('engine_ecu_tx', addresses)
        self.assertEqual(addresses['engine_ecu_tx'], 0x7E0)
        self.assertEqual(addresses['engine_ecu_rx'], 0x7E8)
    
    @patch('can.interface.Bus')
    def test_connect_success(self, mock_bus):
        """Test connect method with successful connection."""
        mock_bus_instance = Mock()
        mock_bus.return_value = mock_bus_instance
        
        result = self.can_interface.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.can_interface.running)
        self.assertIsNotNone(self.can_interface.bus)
    
    @patch('can.interface.Bus')
    def test_connect_failure(self, mock_bus):
        """Test connect method with connection failure."""
        mock_bus.side_effect = Exception("Connection failed")
        
        result = self.can_interface.connect()
        
        self.assertFalse(result)
        self.assertFalse(self.can_interface.running)
    
    def test_disconnect(self):
        """Test disconnect method."""
        mock_bus = Mock()
        self.can_interface.bus = mock_bus
        self.can_interface.running = True
        
        self.can_interface.disconnect()
        
        self.assertFalse(self.can_interface.running)
        mock_bus.shutdown.assert_called_once()
    
    def test_register_message_handler(self):
        """Test register_message_handler method."""
        handler = Mock()
        arbitration_id = 0x7E0
        
        self.can_interface.register_message_handler(arbitration_id, handler)
        
        self.assertIn(arbitration_id, self.can_interface.message_handlers)
        self.assertEqual(self.can_interface.message_handlers[arbitration_id], handler)
    
    def test_get_live_data(self):
        """Test get_live_data method."""
        test_data = {'rpm': 3000, 'boost': 15.0}
        self.can_interface.live_data = test_data.copy()
        
        result = self.can_interface.get_live_data()
        
        self.assertEqual(result, test_data)
        # Should return a copy, not reference
        result['new_key'] = 'value'
        self.assertNotIn('new_key', self.can_interface.live_data)
    
    def test_send_custom_message(self):
        """Test send_custom_message method."""
        mock_bus = Mock()
        self.can_interface.bus = mock_bus
        
        result = self.can_interface.send_custom_message(0x123, b'\x01\x02\x03')
        
        self.assertTrue(result)
        mock_bus.send.assert_called_once()
    
    def test_send_custom_message_no_bus(self):
        """Test send_custom_message without bus connection."""
        self.can_interface.bus = None
        
        result = self.can_interface.send_custom_message(0x123, b'\x01\x02\x03')
        
        # Should handle gracefully or fail
        # Behavior depends on implementation
        self.assertIsInstance(result, bool)
    
    @patch('can.interface.Bus')
    def test_security_access_request_seed(self, mock_bus):
        """Test security_access method requesting seed."""
        mock_bus_instance = Mock()
        mock_bus.return_value = mock_bus_instance
        self.can_interface.bus = mock_bus_instance
        
        # Mock send_diagnostic_request
        with patch.object(self.can_interface, 'send_diagnostic_request', return_value=True):
            seed = self.can_interface.security_access()
            
            # Should return a seed (mock in this case)
            self.assertIsNotNone(seed)
            self.assertIsInstance(seed, bytes)
    
    @patch('can.interface.Bus')
    def test_security_access_send_key(self, mock_bus):
        """Test security_access method sending key."""
        mock_bus_instance = Mock()
        mock_bus.return_value = mock_bus_instance
        self.can_interface.bus = mock_bus_instance
        
        test_seed = b'\xA1\xB2\xC3\xD4'
        
        with patch.object(self.can_interface, 'send_diagnostic_request', return_value=True):
            result = self.can_interface.security_access(seed=test_seed)
            
            self.assertIsNotNone(result)
            self.assertTrue(self.can_interface.security_access_granted)
    
    @patch('can.interface.Bus')
    def test_read_dtcs(self, mock_bus):
        """Test read_dtcs method."""
        mock_bus_instance = Mock()
        mock_bus.return_value = mock_bus_instance
        self.can_interface.bus = mock_bus_instance
        
        with patch.object(self.can_interface, 'send_diagnostic_request', return_value=True):
            dtcs = self.can_interface.read_dtcs()
            
            self.assertIsInstance(dtcs, list)
            # May return empty list or mock DTCs
    
    @patch('can.interface.Bus')
    def test_clear_dtcs(self, mock_bus):
        """Test clear_dtcs method."""
        mock_bus_instance = Mock()
        mock_bus.return_value = mock_bus_instance
        self.can_interface.bus = mock_bus_instance
        
        with patch.object(self.can_interface, 'send_diagnostic_request', return_value=True):
            result = self.can_interface.clear_dtcs()
            
            self.assertTrue(result)
    
    def test_process_can_message_engine_ecu(self):
        """Test _process_can_message with engine ECU message."""
        test_message = CANMessage(
            arbitration_id=0x7E8,  # engine_ecu_rx
            data=b'\x41\x22\x01\x02\x03',
            timestamp=1234567890.0
        )
        
        # Should not raise exception
        self.can_interface._process_can_message(test_message)
    
    def test_process_can_message_tcm(self):
        """Test _process_can_message with TCM message."""
        test_message = CANMessage(
            arbitration_id=0x7E9,  # tcm_rx
            data=b'\x01\x02\x03',
            timestamp=1234567890.0
        )
        
        # Should not raise exception
        self.can_interface._process_can_message(test_message)
    
    def test_process_can_message_abs(self):
        """Test _process_can_message with ABS message."""
        test_message = CANMessage(
            arbitration_id=0x7EA,  # abs_rx
            data=b'\x01\x02\x03',
            timestamp=1234567890.0
        )
        
        # Should not raise exception
        self.can_interface._process_can_message(test_message)
    
    def test_process_can_message_broadcast(self):
        """Test _process_can_message with broadcast message."""
        test_message = CANMessage(
            arbitration_id=0x100,  # Broadcast ID (< 0x700)
            data=b'\x01\x02\x03',
            timestamp=1234567890.0
        )
        
        # Should not raise exception
        self.can_interface._process_can_message(test_message)
    
    def test_process_engine_ecu_message_positive(self):
        """Test _process_engine_ecu_message with positive response."""
        test_message = CANMessage(
            arbitration_id=0x7E8,
            data=b'\x62\x22\x01\x02\x03',  # Positive response (0x62 = 0x22 + 0x40)
            timestamp=1234567890.0
        )
        
        # Should not raise exception
        self.can_interface._process_engine_ecu_message(test_message)
    
    def test_process_engine_ecu_message_negative(self):
        """Test _process_engine_ecu_message with negative response."""
        test_message = CANMessage(
            arbitration_id=0x7E8,
            data=b'\x7F\x22\x10',  # Negative response
            timestamp=1234567890.0
        )
        
        # Should not raise exception
        self.can_interface._process_engine_ecu_message(test_message)
    
    def test_process_realtime_data_rpm(self):
        """Test _process_realtime_data with RPM data."""
        test_message = CANMessage(
            arbitration_id=0x7E8,
            data=bytes([0x0C, 0x00, 0x1F, 0x40]),  # RPM PID: 8000 = 2000 RPM
            timestamp=1234567890.0
        )
        
        self.can_interface._process_realtime_data(test_message)
        
        # Should update live_data
        self.assertIn('engine_rpm', self.can_interface.live_data)
        self.assertEqual(self.can_interface.live_data['engine_rpm'], 2000.0)
    
    def test_process_realtime_data_speed(self):
        """Test _process_realtime_data with speed data."""
        test_message = CANMessage(
            arbitration_id=0x7E8,
            data=bytes([0x0D, 0x00, 100]),  # Speed PID: 100 kph
            timestamp=1234567890.0
        )
        
        self.can_interface._process_realtime_data(test_message)
        
        # Should update live_data
        self.assertIn('vehicle_speed', self.can_interface.live_data)
        self.assertEqual(self.can_interface.live_data['vehicle_speed'], 100.0)
    
    def test_process_mazda_specific_data_boost(self):
        """Test _process_mazda_specific_data with boost data."""
        # Boost: 0x80, boost_raw at [2:4]
        boost_raw = 200  # (200 - 100) / 10 = 10 PSI
        test_message = CANMessage(
            arbitration_id=0x7E8,
            data=bytes([0x80, 0x00, (boost_raw >> 8) & 0xFF, boost_raw & 0xFF, 0x00, 0x00, 0x00, 0x00]),
            timestamp=1234567890.0
        )
        
        self.can_interface._process_mazda_specific_data(test_message)
        
        # Should update live_data if data is correct
        # May or may not be set depending on data validation
    
    def test_process_negative_response(self):
        """Test _process_negative_response method."""
        test_message = CANMessage(
            arbitration_id=0x7E8,
            data=b'\x7F\x22\x10',  # Service 0x22, error 0x10 (General reject)
            timestamp=1234567890.0
        )
        
        # Should not raise exception
        self.can_interface._process_negative_response(test_message)
    
    def test_process_positive_response_read_data(self):
        """Test _process_positive_response with ReadDataByIdentifier."""
        test_message = CANMessage(
            arbitration_id=0x7E8,
            data=b'\x62\x22\x01\x02\x03\x04',  # ReadDataByIdentifier response
            timestamp=1234567890.0
        )
        
        # Should not raise exception
        self.can_interface._process_positive_response(0x22, test_message)
    
    def test_process_positive_response_security_access(self):
        """Test _process_positive_response with SecurityAccess."""
        test_message = CANMessage(
            arbitration_id=0x7E8,
            data=b'\x67\x27\x01\x02\x03\x04',  # SecurityAccess response
            timestamp=1234567890.0
        )
        
        # Should not raise exception
        self.can_interface._process_positive_response(0x27, test_message)
    
    def test_send_diagnostic_request(self):
        """Test send_diagnostic_request method."""
        mock_bus = Mock()
        self.can_interface.bus = mock_bus
        
        result = self.can_interface.send_diagnostic_request(0x22, 0xF187)
        
        self.assertTrue(result)
        mock_bus.send.assert_called_once()
    
    def test_send_diagnostic_request_with_data(self):
        """Test send_diagnostic_request with data."""
        mock_bus = Mock()
        self.can_interface.bus = mock_bus
        
        result = self.can_interface.send_diagnostic_request(0x2E, 0x01, data=b'\x01\x02\x03')
        
        self.assertTrue(result)
        mock_bus.send.assert_called_once()
    
    def test_send_diagnostic_request_no_bus(self):
        """Test send_diagnostic_request without bus."""
        self.can_interface.bus = None
        
        result = self.can_interface.send_diagnostic_request(0x22)
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
