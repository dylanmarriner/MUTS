#!/usr/bin/env python3
"""
Unit Tests for ECU Communication Module
Comprehensive testing of all ECU communication functionality
"""

import unittest
import can
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.versa.core.ecu_communication import ECUCommunicator, ECUResponse
from app.versa.core.security_access import SecurityManager
from app.versa.core.rom_operations import ROMOperations

class TestECUCommunication(unittest.TestCase):
    """Test cases for ECU communication functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock CAN bus to avoid hardware dependency
        self.can_bus_mock = Mock(spec=can.Bus)
        self.can_bus_mock.recv.return_value = None
        
        # Patch can.interface.Bus to return our mock
        self.bus_patcher = patch('can.interface.Bus')
        self.mock_bus_class = self.bus_patcher.start()
        self.mock_bus_class.return_value = self.can_bus_mock
        
        # Create ECU communicator instance
        self.ecu_comm = ECUCommunicator()
        
    def tearDown(self):
        """Tear down test fixtures"""
        self.bus_patcher.stop()
        if hasattr(self.ecu_comm, 'bus') and self.ecu_comm.bus:
            self.ecu_comm.disconnect()
    
    def test_initialization(self):
        """Test ECUCommunicator initialization"""
        self.assertEqual(self.ecu_comm.interface, 'can0')
        self.assertEqual(self.ecu_comm.bitrate, 500000)
        self.assertFalse(self.ecu_comm.is_connected)
        self.assertIsNotNone(self.ecu_comm.logger)
    
    def test_connect_success(self):
        """Test successful connection to ECU"""
        # Mock VIN read to simulate successful communication
        with patch.object(self.ecu_comm, 'read_vin', return_value='JM1BK143141123456'):
            result = self.ecu_comm.connect()
            
            self.assertTrue(result)
            self.assertTrue(self.ecu_comm.is_connected)
            self.mock_bus_class.assert_called_once_with(
                channel='can0',
                bustype='socketcan',
                bitrate=500000
            )
    
    def test_connect_failure(self):
        """Test failed connection to ECU"""
        # Mock bus creation to raise exception
        self.mock_bus_class.side_effect = Exception("CAN bus error")
        
        result = self.ecu_comm.connect()
        
        self.assertFalse(result)
        self.assertFalse(self.ecu_comm.is_connected)
    
    def test_send_request_success(self):
        """Test successful message sending"""
        # Setup mock response
        response_data = bytes([0x7E, 0x8, 0x62, 0xF1, 0x86, 0x4A, 0x31, 0x42, 0x4B, 0x31, 0x34, 0x33, 0x31, 0x34, 0x31, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36])
        response_message = can.Message(
            arbitration_id=0x7E8,
            data=response_data,
            is_extended_id=False
        )
        
        # Mock bus send and receive
        self.can_bus_mock.send.return_value = None
        self.can_bus_mock.recv.side_effect = [response_message, None]
        
        # Connect first
        with patch.object(self.ecu_comm, 'read_vin', return_value='TESTVIN123456789'):
            self.ecu_comm.connect()
        
        # Send request
        response = self.ecu_comm.send_request(0x22, 0xF186)  # Read VIN
        
        self.assertTrue(response.success)
        self.assertEqual(response.data, response_data)
        self.can_bus_mock.send.assert_called_once()
    
    def test_send_request_timeout(self):
        """Test request timeout handling"""
        # Mock bus to return no response (timeout)
        self.can_bus_mock.recv.return_value = None
        
        # Connect first
        with patch.object(self.ecu_comm, 'read_vin', return_value='TESTVIN123456789'):
            self.ecu_comm.connect()
        
        # Send request
        response = self.ecu_comm.send_request(0x22, 0xF186)
        
        self.assertFalse(response.success)
        self.assertEqual(response.error_code, 0x78)  # Timeout error code
    
    def test_read_vin_success(self):
        """Test successful VIN reading"""
        # Mock VIN response
        vin_response = bytes([0x7E, 0x8, 0x62, 0xF1, 0x89, 0x4A, 0x31, 0x42, 0x4B, 0x31, 0x34, 0x33, 0x31, 0x34, 0x31, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36])
        
        with patch.object(self.ecu_comm, 'send_request') as mock_send:
            mock_send.return_value = ECUResponse(True, vin_response, 1234567890.0)
            
            # Connect first
            with patch.object(self.ecu_comm, 'read_vin', return_value='TESTVIN123456789'):
                self.ecu_comm.connect()
            
            vin = self.ecu_comm.read_vin()
            
            self.assertEqual(vin, 'JM1BK143141123456')
            mock_send.assert_called_once_with(0x22, 0xF189)
    
    def test_read_dtcs(self):
        """Test DTC reading functionality"""
        # Mock DTC response with P0301 and P0420 codes
        dtc_response = bytes([0x7E, 0x8, 0x62, 0x02, 0x01, 0x03, 0x01, 0x04, 0x20, 0x00, 0x00, 0x00, 0x00])
        
        with patch.object(self.ecu_comm, 'send_request') as mock_send:
            mock_send.return_value = ECUResponse(True, dtc_response, 1234567890.0)
            
            # Connect first
            with patch.object(self.ecu_comm, 'read_vin', return_value='TESTVIN123456789'):
                self.ecu_comm.connect()
            
            dtcs = self.ecu_comm.read_dtcs()
            
            self.assertEqual(len(dtcs), 2)
            self.assertEqual(dtcs[0]['code'], 'P0301')
            self.assertEqual(dtcs[0]['description'], 'Cylinder 1 Misfire Detected')
            self.assertEqual(dtcs[1]['code'], 'P0420')
            self.assertEqual(dtcs[1]['description'], 'Catalyst System Efficiency Below Threshold')
    
    def test_clear_dtcs(self):
        """Test DTC clearing functionality"""
        with patch.object(self.ecu_comm, 'send_request') as mock_send:
            mock_send.return_value = ECUResponse(True, bytes([0x54]), 1234567890.0)
            
            # Connect first
            with patch.object(self.ecu_comm, 'read_vin', return_value='TESTVIN123456789'):
                self.ecu_comm.connect()
            
            result = self.ecu_comm.clear_dtcs()
            
            self.assertTrue(result)
            mock_send.assert_called_once_with(0x14, 0xFF)
    
    def test_read_live_data(self):
        """Test live data parameter reading"""
        # Mock RPM response (0x0C = 3000 RPM)
        rpm_response = bytes([0x7E, 0x8, 0x62, 0x0C, 0x2E, 0xE0])
        
        with patch.object(self.ecu_comm, 'send_request') as mock_send:
            mock_send.return_value = ECUResponse(True, rpm_response, 1234567890.0)
            
            # Connect first
            with patch.object(self.ecu_comm, 'read_vin', return_value='TESTVIN123456789'):
                self.ecu_comm.connect()
            
            rpm = self.ecu_comm.read_live_data(0x0C)  # RPM PID
            
            self.assertEqual(rpm, 3000.0)  # (0x2E * 256 + 0xE0) / 4 = 3000
    
    def test_parse_dtc_code(self):
        """Test DTC code parsing from bytes"""
        # Test P0301 code
        dtc_bytes = bytes([0x03, 0x01])
        dtc_code = self.ecu_comm._parse_dtc_code(dtc_bytes)
        self.assertEqual(dtc_code, 'P0301')
        
        # Test C0034 code  
        dtc_bytes = bytes([0x43, 0x34])
        dtc_code = self.ecu_comm._parse_dtc_code(dtc_bytes)
        self.assertEqual(dtc_code, 'C0034')
        
        # Test invalid length
        dtc_code = self.ecu_comm._parse_dtc_code(bytes([0x03]))
        self.assertIsNone(dtc_code)
    
    def test_message_listener_stop(self):
        """Test message listener stop functionality"""
        # Connect first
        with patch.object(self.ecu_comm, 'read_vin', return_value='TESTVIN123456789'):
            self.ecu_comm.connect()
        
        # Set stop flag and verify listener stops
        self.ecu_comm._stop_listener = True
        # This should return quickly since stop flag is set
        self.ecu_comm._message_listener()

class TestSecurityAccess(unittest.TestCase):
    """Test cases for security access functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ecu_comm_mock = Mock(spec=ECUCommunicator)
        self.security_mgr = SecurityManager(self.ecu_comm_mock)
    
    def test_security_level_1_algorithm(self):
        """Test level 1 security algorithm"""
        seed = bytes([0x12, 0x34, 0x56, 0x78])
        seed_int = int.from_bytes(seed, 'big')
        
        key = self.security_mgr._level1_algorithm(seed_int)
        
        # Verify key is 4 bytes
        self.assertEqual(len(key), 4)
        # Verify algorithm produces consistent results
        key_again = self.security_mgr._level1_algorithm(seed_int)
        self.assertEqual(key, key_again)
    
    def test_unlock_ecu_success(self):
        """Test successful ECU unlock"""
        # Mock seed and key responses
        seed_response = ECUResponse(True, bytes([0x67, 0x01, 0x12, 0x34, 0x56, 0x78]), 1234567890.0)
        key_response = ECUResponse(True, bytes([0x67, 0x02]), 1234567890.0)
        
        self.ecu_comm_mock.send_request.side_effect = [seed_response, key_response]
        
        result = self.security_mgr._unlock_security_level(1)
        
        self.assertTrue(result)
        self.assertEqual(self.ecu_comm_mock.send_request.call_count, 2)
    
    def test_unlock_ecu_failure(self):
        """Test failed ECU unlock"""
        # Mock seed response but key rejection
        seed_response = ECUResponse(True, bytes([0x67, 0x01, 0x12, 0x34, 0x56, 0x78]), 1234567890.0)
        key_response = ECUResponse(False, bytes([0x7F, 0x27, 0x35]), 1234567890.0)  # Negative response
        
        self.ecu_comm_mock.send_request.side_effect = [seed_response, key_response]
        
        result = self.security_mgr._unlock_security_level(1)
        
        self.assertFalse(result)

class TestROMOperations(unittest.TestCase):
    """Test cases for ROM operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ecu_comm_mock = Mock(spec=ECUCommunicator)
        self.rom_ops = ROMOperations(self.ecu_comm_mock)
    
    def test_rom_structure_definition(self):
        """Test ROM structure definitions"""
        structure = self.rom_ops.ROM_STRUCTURE
        
        # Verify main sectors exist
        self.assertIn('boot_sector', structure)
        self.assertIn('calibration_a', structure)
        self.assertIn('operating_system', structure)
        
        # Verify sector sizes
        self.assertEqual(structure['boot_sector'].size, 0x010000)
        self.assertEqual(structure['calibration_a'].size, 0x080000)
    
    def test_checksum_calculation(self):
        """Test checksum calculation algorithms"""
        test_data = b'TEST_DATA_FOR_CHECKSUM_CALCULATION' * 100  # Some test data
        
        # Test CRC32
        crc32_result = self.rom_ops.crc32_func(test_data)
        self.assertIsInstance(crc32_result, int)
        self.assertEqual(crc32_result, 0x5B04C3D1)  # Pre-calculated value
        
        # Test SUM16
        sum16_result = self.rom_ops._calculate_sum16(test_data)
        self.assertIsInstance(sum16_result, int)
        self.assertLessEqual(sum16_result, 0xFFFF)
    
    def test_verify_checksums(self):
        """Test ROM checksum verification"""
        # Create mock ROM data with valid checksums
        rom_data = bytearray(0x200000)  # 2MB ROM
        
        # Calculate and set calibration CRC32
        calibration_data = rom_data[0x010000:0x090000]
        crc32 = self.rom_ops.crc32_func(calibration_data)
        rom_data[0x1FFFF0:0x1FFFF4] = crc32.to_bytes(4, 'big')
        
        # Calculate and set boot sector SUM16
        boot_data = rom_data[0x000000:0x00FFFC]
        sum16 = self.rom_ops._calculate_sum16(boot_data)
        rom_data[0x00FFFC:0x00FFFE] = sum16.to_bytes(2, 'big')
        
        results = self.rom_ops.verify_checksums(bytes(rom_data))
        
        self.assertTrue(results['calibration_crc32'])
        self.assertTrue(results['boot_sector_sum16'])

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
