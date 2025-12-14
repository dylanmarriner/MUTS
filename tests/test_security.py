"""Tests for utils security module."""
import unittest
from unittest.mock import patch, Mock
import time
import json
import base64
import sys
from pathlib import Path

# Add utils to path to avoid muts package import (which imports torch)
sys.path.insert(0, str(Path(__file__).parent.parent / 'muts' / 'utils'))
from security import SecurityManager, SecurityError


class TestSecurityManager(unittest.TestCase):
    """Test SecurityManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use a fixed key for reproducible tests
        self.manager = SecurityManager(master_key="test_master_key_12345678901234567890")
    
    def test_initialization(self):
        """Test SecurityManager initialization."""
        self.assertIsNotNone(self.manager.master_key)
        self.assertIsNotNone(self.manager.fernet)
        self.assertEqual(self.manager.key_derivation_iterations, 100000)
        self.assertEqual(self.manager.token_expiry_hours, 24)
    
    def test_generate_master_key(self):
        """Test _generate_master_key method."""
        key = self.manager._generate_master_key()
        
        self.assertIsNotNone(key)
        self.assertIsInstance(key, str)
        self.assertGreater(len(key), 0)
    
    def test_derive_encryption_key(self):
        """Test _derive_encryption_key method."""
        key = self.manager._derive_encryption_key("test_password")
        
        self.assertIsNotNone(key)
        self.assertIsInstance(key, bytes)
        self.assertGreater(len(key), 0)
    
    def test_encrypt_calibration_data(self):
        """Test encrypt_calibration_data method."""
        calibration_data = {
            'boost_target': 20.0,
            'timing_base': 15.0,
            'afr_target': 12.5
        }
        
        encrypted = self.manager.encrypt_calibration_data(calibration_data)
        
        self.assertIsNotNone(encrypted)
        self.assertIsInstance(encrypted, str)
        # Should be base64-like string
        self.assertGreater(len(encrypted), 0)
    
    def test_decrypt_calibration_data(self):
        """Test decrypt_calibration_data method."""
        calibration_data = {
            'boost_target': 20.0,
            'timing_base': 15.0,
            'afr_target': 12.5
        }
        
        encrypted = self.manager.encrypt_calibration_data(calibration_data)
        decrypted = self.manager.decrypt_calibration_data(encrypted)
        
        self.assertEqual(decrypted, calibration_data)
    
    def test_generate_vehicle_signature(self):
        """Test generate_vehicle_signature method."""
        vin = "JMZBK18Z801234567"
        calibration_id = "CAL001"
        
        signature = self.manager.generate_vehicle_signature(vin, calibration_id)
        
        self.assertIsNotNone(signature)
        self.assertIsInstance(signature, str)
    
    def test_verify_vehicle_signature_valid(self):
        """Test verify_vehicle_signature with valid signature."""
        vin = "JMZBK18Z801234567"
        calibration_id = "CAL001"
        
        signature = self.manager.generate_vehicle_signature(vin, calibration_id)
        is_valid = self.manager.verify_vehicle_signature(signature, vin, calibration_id)
        
        self.assertTrue(is_valid)
    
    def test_verify_vehicle_signature_invalid_vin(self):
        """Test verify_vehicle_signature with invalid VIN."""
        vin = "JMZBK18Z801234567"
        calibration_id = "CAL001"
        
        signature = self.manager.generate_vehicle_signature(vin, calibration_id)
        is_valid = self.manager.verify_vehicle_signature(signature, "WRONG_VIN", calibration_id)
        
        self.assertFalse(is_valid)
    
    def test_verify_vehicle_signature_invalid_calibration(self):
        """Test verify_vehicle_signature with invalid calibration ID."""
        vin = "JMZBK18Z801234567"
        calibration_id = "CAL001"
        
        signature = self.manager.generate_vehicle_signature(vin, calibration_id)
        is_valid = self.manager.verify_vehicle_signature(signature, vin, "WRONG_ID")
        
        self.assertFalse(is_valid)
    
    @patch('time.time')
    def test_verify_vehicle_signature_expired(self, mock_time):
        """Test verify_vehicle_signature with expired signature."""
        # Set initial time
        mock_time.return_value = 1000.0
        
        vin = "JMZBK18Z801234567"
        calibration_id = "CAL001"
        signature = self.manager.generate_vehicle_signature(vin, calibration_id)
        
        # Advance time by more than expiry (25 hours)
        mock_time.return_value = 1000.0 + (25 * 3600)
        
        is_valid = self.manager.verify_vehicle_signature(signature, vin, calibration_id)
        
        self.assertFalse(is_valid)
    
    def test_protect_ai_model(self):
        """Test protect_ai_model method."""
        model_data = b'\x01\x02\x03\x04\x05' * 100  # 500 bytes of model data
        
        protected = self.manager.protect_ai_model(model_data)
        
        self.assertIsNotNone(protected)
        self.assertIsInstance(protected, bytes)
        self.assertNotEqual(protected, model_data)  # Should be different
    
    def test_unprotect_ai_model(self):
        """Test unprotect_ai_model method."""
        model_data = b'\x01\x02\x03\x04\x05' * 100  # 500 bytes of model data
        
        protected = self.manager.protect_ai_model(model_data)
        unprotected = self.manager.unprotect_ai_model(protected)
        
        self.assertEqual(unprotected, model_data)
    
    def test_secure_communication_channel(self):
        """Test secure_communication_channel method."""
        data = {
            'command': 'read_data',
            'did': 0x1234,
            'value': 42
        }
        session_key = "test_session_key_123"
        
        secure_data = self.manager.secure_communication_channel(data, session_key)
        
        self.assertIsNotNone(secure_data)
        self.assertIsInstance(secure_data, str)
        
        # Should be base64 decodable
        try:
            decoded = base64.urlsafe_b64decode(secure_data.encode())
            package = json.loads(decoded.decode())
            self.assertIn('session_id', package)
            self.assertIn('data', package)
            self.assertIn('timestamp', package)
        except Exception:
            self.fail("secure_communication_channel did not return valid base64/json")


class TestSecurityError(unittest.TestCase):
    """Test SecurityError exception."""
    
    def test_security_error_creation(self):
        """Test SecurityError can be created and raised."""
        with self.assertRaises(SecurityError):
            raise SecurityError("Test security error")


if __name__ == '__main__':
    unittest.main()
