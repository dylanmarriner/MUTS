"""Tests for core ecu_communication module."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import struct

from core.ecu_communication import (
    ECUCommunicator, ECUState, ECUResponse
)


class TestECUState(unittest.TestCase):
    """Test ECUState enum."""
    
    def test_ecu_state_values(self):
        """Test ECUState enum values."""
        self.assertEqual(ECUState.DISCONNECTED.value, "disconnected")
        self.assertEqual(ECUState.CONNECTING.value, "connecting")
        self.assertEqual(ECUState.CONNECTED.value, "connected")
        self.assertEqual(ECUState.AUTHENTICATED.value, "authenticated")
        self.assertEqual(ECUState.ERROR.value, "error")


class TestECUResponse(unittest.TestCase):
    """Test ECUResponse dataclass."""
    
    def test_ecu_response_creation(self):
        """Test ECUResponse creation."""
        response = ECUResponse(
            success=True,
            data=b'\x01\x02\x03',
            timestamp=1234567890.0,
            error_code=None,
            service_id=0x22
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.data, b'\x01\x02\x03')
        self.assertEqual(response.timestamp, 1234567890.0)
        self.assertIsNone(response.error_code)
        self.assertEqual(response.service_id, 0x22)


class TestECUCommunicator(unittest.TestCase):
    """Test ECUCommunicator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        with patch('core.ecu_communication.get_safety_validator'):
            with patch('can.interface.Bus'):
                self.communicator = ECUCommunicator('vcan0', 500000)
    
    def test_initialization(self):
        """Test ECUCommunicator initialization."""
        self.assertEqual(self.communicator.interface, 'vcan0')
        self.assertEqual(self.communicator.bitrate, 500000)
        self.assertEqual(self.communicator.state, ECUState.DISCONNECTED)
        self.assertEqual(self.communicator.security_level, 0)
        self.assertFalse(self.communicator.session_active)
        self.assertIsNotNone(self.communicator.stats)
    
    def test_services_constants(self):
        """Test SERVICE constants."""
        self.assertEqual(ECUCommunicator.ECU_REQUEST_ID, 0x7E0)
        self.assertEqual(ECUCommunicator.ECU_RESPONSE_ID, 0x7E8)
        self.assertEqual(ECUCommunicator.BROADCAST_ID, 0x7DF)
        self.assertIn('DIAGNOSTIC_SESSION', ECUCommunicator.SERVICES)
        self.assertIn('READ_DATA', ECUCommunicator.SERVICES)
        self.assertIn('WRITE_DATA', ECUCommunicator.SERVICES)
    
    @patch('can.interface.Bus')
    def test_connect_success(self, mock_bus):
        """Test connect method with successful connection."""
        mock_bus_instance = MagicMock()
        mock_bus.return_value = mock_bus_instance
        
        # Mock _test_connection to return True
        with patch.object(self.communicator, '_test_connection', return_value=True):
            result = self.communicator.connect()
            
            self.assertTrue(result)
            self.assertEqual(self.communicator.state, ECUState.CONNECTED)
            mock_bus.assert_called_once()
    
    @patch('can.interface.Bus')
    def test_connect_failure(self, mock_bus):
        """Test connect method with connection failure."""
        mock_bus.side_effect = Exception("Connection failed")
        
        result = self.communicator.connect()
        
        self.assertFalse(result)
        self.assertEqual(self.communicator.state, ECUState.ERROR)
        self.assertGreater(self.communicator.stats['errors'], 0)
    
    @patch('can.interface.Bus')
    def test_connect_already_connected(self, mock_bus):
        """Test connect when already connected."""
        self.communicator.state = ECUState.CONNECTED
        
        result = self.communicator.connect()
        
        self.assertTrue(result)
    
    def test_disconnect(self):
        """Test disconnect method."""
        mock_bus = MagicMock()
        self.communicator.bus = mock_bus
        
        self.communicator.disconnect()
        
        mock_bus.shutdown.assert_called_once()
        self.assertIsNone(self.communicator.bus)
        self.assertEqual(self.communicator.state, ECUState.DISCONNECTED)
        self.assertFalse(self.communicator.session_active)
    
    def test_disconnect_no_bus(self):
        """Test disconnect when no bus is connected."""
        self.communicator.bus = None
        
        # Should not raise exception
        self.communicator.disconnect()
        
        self.assertEqual(self.communicator.state, ECUState.DISCONNECTED)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_test_connection_success(self, mock_send_request):
        """Test _test_connection with successful response."""
        mock_response = ECUResponse(True, b'\x50\x01', time.time())
        mock_send_request.return_value = mock_response
        
        result = self.communicator._test_connection()
        
        self.assertTrue(result)
        mock_send_request.assert_called_once()
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_test_connection_failure(self, mock_send_request):
        """Test _test_connection with failed response."""
        mock_response = ECUResponse(False, b'', time.time())
        mock_send_request.return_value = mock_response
        
        result = self.communicator._test_connection()
        
        self.assertFalse(result)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_test_connection_exception(self, mock_send_request):
        """Test _test_connection with exception."""
        mock_send_request.side_effect = Exception("Test failed")
        
        result = self.communicator._test_connection()
        
        self.assertFalse(result)
    
    def test_validate_safety_before_write_read_service(self):
        """Test _validate_safety_before_write with read service."""
        # Read services should always pass
        result = self.communicator._validate_safety_before_write(
            ECUCommunicator.SERVICES['READ_DATA'],
            b'\x01\x02\x03'
        )
        
        self.assertTrue(result)
    
    @patch.object(ECUCommunicator, 'safety_validator')
    def test_validate_safety_before_write_safe(self, mock_validator):
        """Test _validate_safety_before_write with safe parameters."""
        import struct
        mock_validator.validate_tuning_parameters.return_value = (True, [])
        
        # Create valid float bytes: boost=15.0, timing=12.0, afr=12.5
        safe_data = struct.pack('>fff', 15.0, 12.0, 12.5)
        
        result = self.communicator._validate_safety_before_write(
            ECUCommunicator.SERVICES['WRITE_DATA'],
            safe_data
        )
        
        self.assertTrue(result)
    
    @patch.object(ECUCommunicator, 'safety_validator')
    def test_validate_safety_before_write_unsafe(self, mock_validator):
        """Test _validate_safety_before_write with unsafe parameters."""
        import struct
        from core.safety_validator import SafetyViolation, SafetyLevel
        
        violations = [
            SafetyViolation('boost_target', 30.0, 25.0, SafetyLevel.CRITICAL, 'Too high', time.time())
        ]
        mock_validator.validate_tuning_parameters.return_value = (False, violations)
        
        # Create valid float bytes: boost=30.0 (dangerous), timing=35.0, afr=10.0
        dangerous_data = struct.pack('>fff', 30.0, 35.0, 10.0)
        
        result = self.communicator._validate_safety_before_write(
            ECUCommunicator.SERVICES['WRITE_DATA'],
            dangerous_data
        )
        
        self.assertFalse(result)
        self.assertGreater(self.communicator.stats['safety_blocks'], 0)
    
    def test_get_state(self):
        """Test get_state method."""
        state = self.communicator.get_state()
        
        self.assertIsInstance(state, ECUState)
        self.assertEqual(state, ECUState.DISCONNECTED)
    
    def test_get_statistics(self):
        """Test get_statistics method."""
        stats = self.communicator.get_statistics()
        
        self.assertIn('messages_sent', stats)
        self.assertIn('messages_received', stats)
        self.assertIn('errors', stats)
        self.assertIn('safety_blocks', stats)
        self.assertEqual(stats['messages_sent'], 0)
        self.assertEqual(stats['errors'], 0)
    
    def test_stats_tracking(self):
        """Test statistics tracking."""
        initial_sent = self.communicator.stats['messages_sent']
        
        # Stats should be tracked when operations occur
        stats = self.communicator.get_statistics()
        self.assertIn('messages_sent', stats)
        self.assertIn('safety_blocks', stats)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_read_vin_success(self, mock_send_request):
        """Test read_vin method with successful response."""
        # Mock VIN response: 17 bytes ASCII
        vin_data = b'JM1BK123456789012'  # 17 bytes
        mock_response = ECUResponse(True, vin_data, time.time())
        mock_send_request.return_value = mock_response
        
        vin = self.communicator.read_vin()
        
        self.assertIsNotNone(vin)
        self.assertEqual(vin, 'JM1BK123456789012')
        mock_send_request.assert_called_once()
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_read_vin_failure(self, mock_send_request):
        """Test read_vin method with failed response."""
        mock_response = ECUResponse(False, b'', time.time())
        mock_send_request.return_value = mock_response
        
        vin = self.communicator.read_vin()
        
        self.assertIsNone(vin)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_read_dtcs_success(self, mock_send_request):
        """Test read_dtcs method with successful response."""
        # Mock DTC data: P0301 (0x0301) = bytes([0x03, 0x01])
        dtc_data = bytes([0x03, 0x01, 0x02, 0x34])  # P0301 and P0234
        mock_response = ECUResponse(True, dtc_data, time.time())
        mock_send_request.return_value = mock_response
        
        dtcs = self.communicator.read_dtcs()
        
        self.assertIsInstance(dtcs, list)
        self.assertGreater(len(dtcs), 0)
        self.assertIn('code', dtcs[0])
        self.assertIn('status', dtcs[0])
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_read_dtcs_no_dtcs(self, mock_send_request):
        """Test read_dtcs method with no DTCs."""
        # Empty DTC data or all zeros
        dtc_data = bytes([0x00, 0x00, 0x00, 0x00])
        mock_response = ECUResponse(True, dtc_data, time.time())
        mock_send_request.return_value = mock_response
        
        dtcs = self.communicator.read_dtcs()
        
        self.assertIsInstance(dtcs, list)
        # Should return empty list if no valid DTCs
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_clear_dtcs_success(self, mock_send_request):
        """Test clear_dtcs method with successful response."""
        mock_response = ECUResponse(True, b'', time.time())
        mock_send_request.return_value = mock_response
        
        result = self.communicator.clear_dtcs()
        
        self.assertTrue(result)
        mock_send_request.assert_called_once()
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_clear_dtcs_failure(self, mock_send_request):
        """Test clear_dtcs method with failed response."""
        mock_response = ECUResponse(False, b'', time.time())
        mock_send_request.return_value = mock_response
        
        result = self.communicator.clear_dtcs()
        
        self.assertFalse(result)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_read_live_data_rpm(self, mock_send_request):
        """Test read_live_data for RPM (PID 0x0C)."""
        # RPM: value * 0.25, so for 2000 RPM: 2000 / 0.25 = 8000 = 0x1F40
        rpm_data = struct.pack('>H', 8000)
        mock_response = ECUResponse(True, rpm_data, time.time())
        mock_send_request.return_value = mock_response
        
        rpm = self.communicator.read_live_data(0x0C)
        
        self.assertIsNotNone(rpm)
        self.assertEqual(rpm, 2000.0)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_read_live_data_map(self, mock_send_request):
        """Test read_live_data for MAP (PID 0x0B)."""
        map_data = struct.pack('>H', 100)  # 100 kPa
        mock_response = ECUResponse(True, map_data, time.time())
        mock_send_request.return_value = mock_response
        
        map_value = self.communicator.read_live_data(0x0B)
        
        self.assertIsNotNone(map_value)
        self.assertEqual(map_value, 100.0)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_read_live_data_failure(self, mock_send_request):
        """Test read_live_data with failed response."""
        mock_response = ECUResponse(False, b'', time.time())
        mock_send_request.return_value = mock_response
        
        result = self.communicator.read_live_data(0x0C)
        
        self.assertIsNone(result)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_unlock_security_success(self, mock_send_request):
        """Test unlock_security method with successful unlock."""
        import struct
        
        # First call: seed response
        # Second call: key response (success)
        seed_response = ECUResponse(True, struct.pack('>I', 0x12345678), time.time())
        key_response = ECUResponse(True, b'', time.time())
        mock_send_request.side_effect = [seed_response, key_response]
        
        result = self.communicator.unlock_security(level=3)
        
        self.assertTrue(result)
        self.assertEqual(self.communicator.security_level, 3)
        self.assertEqual(mock_send_request.call_count, 2)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_unlock_security_seed_failure(self, mock_send_request):
        """Test unlock_security when seed request fails."""
        mock_response = ECUResponse(False, b'', time.time())
        mock_send_request.return_value = mock_response
        
        result = self.communicator.unlock_security(level=3)
        
        self.assertFalse(result)
        self.assertEqual(self.communicator.security_level, 0)
    
    @patch.object(ECUCommunicator, 'send_request')
    def test_unlock_security_key_failure(self, mock_send_request):
        """Test unlock_security when key send fails."""
        import struct
        
        seed_response = ECUResponse(True, struct.pack('>I', 0x12345678), time.time())
        key_response = ECUResponse(False, b'', time.time())
        mock_send_request.side_effect = [seed_response, key_response]
        
        result = self.communicator.unlock_security(level=3)
        
        self.assertFalse(result)
        self.assertEqual(self.communicator.security_level, 0)
    
    def test_calculate_security_key(self):
        """Test _calculate_security_key method."""
        seed = 0x12345678
        level = 3
        
        key = self.communicator._calculate_security_key(seed, level)
        
        self.assertIsInstance(key, int)
        self.assertLessEqual(key, 0xFFFFFFFF)
        # Same seed should produce same key
        key2 = self.communicator._calculate_security_key(seed, level)
        self.assertEqual(key, key2)
    
    def test_is_connected(self):
        """Test is_connected method."""
        # Not connected
        self.communicator.state = ECUState.DISCONNECTED
        self.assertFalse(self.communicator.is_connected())
        
        # Connected
        self.communicator.state = ECUState.CONNECTED
        self.assertTrue(self.communicator.is_connected())
        
        # Authenticated (also connected)
        self.communicator.state = ECUState.AUTHENTICATED
        self.assertTrue(self.communicator.is_connected())


if __name__ == '__main__':
    unittest.main()

