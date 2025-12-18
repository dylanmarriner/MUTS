"""Tests for core versa_tuning_core module."""
import unittest
from unittest.mock import Mock, patch, MagicMock

from core.versa_tuning_core import (
    VersaTuningCore, get_versa_core, RUST_AVAILABLE,
    MapChange, PatchResult, ValidationResult, ApplyResult
)


class TestVersaTuningCore(unittest.TestCase):
    """Test VersaTuningCore class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.core = VersaTuningCore()
    
    def test_initialization(self):
        """Test VersaTuningCore initialization."""
        self.assertIsNotNone(self.core.safety_limits)
        self.assertIn('max_boost_psi', self.core.safety_limits)
        self.assertIn('max_timing_degrees', self.core.safety_limits)
    
    def test_load_default_safety_limits(self):
        """Test _load_default_safety_limits method."""
        limits = self.core._load_default_safety_limits()
        
        self.assertIsInstance(limits, dict)
        self.assertEqual(limits['max_boost_psi'], 22.0)
        self.assertEqual(limits['max_timing_degrees'], 25.0)
        self.assertEqual(limits['max_rpm'], 7200)
    
    def test_build_patch_from_changeset(self):
        """Test build_patch_from_changeset method."""
        base_rom = b'\xFF' * 0x1000  # 4KB test ROM
        
        changeset = {
            'changes': [
                {
                    'address': 0x100,
                    'size': 4,
                    'oldData': 'FFFFFFFF',
                    'newData': '00000000',
                    'mapType': 'TEST'
                }
            ]
        }
        
        result = self.core.build_patch_from_changeset(base_rom, changeset)
        
        self.assertIsInstance(result, PatchResult)
        self.assertIsInstance(result.success, bool)
        self.assertIsInstance(result.patch_data, bytes)
    
    def test_build_patch_from_changeset_empty(self):
        """Test build_patch_from_changeset with empty changeset."""
        base_rom = b'\xFF' * 0x1000
        
        changeset = {'changes': []}
        
        result = self.core.build_patch_from_changeset(base_rom, changeset)
        
        self.assertIsInstance(result, PatchResult)
    
    def test_validate_patch_safety(self):
        """Test validate_patch_safety method."""
        original_rom = b'\xFF' * 0x1000
        patch_data = b'\x00' * 0x1000
        
        result = self.core.validate_patch_safety(patch_data, original_rom)
        
        self.assertIsInstance(result, ValidationResult)
        self.assertIsInstance(result.valid, bool)
        self.assertIsInstance(result.risk_score, int)
    
    def test_apply_live_changes(self):
        """Test apply_live_changes method."""
        vehicle_session = 'test_session_123'
        
        changeset = {
            'changes': [
                {
                    'address': 0x100,
                    'size': 4,
                    'oldData': 'FFFFFFFF',
                    'newData': '00000000',
                    'mapType': 'TEST'
                }
            ]
        }
        
        result = self.core.apply_live_changes(vehicle_session, changeset, timeout_minutes=10)
        
        self.assertIsInstance(result, ApplyResult)
        self.assertIsInstance(result.success, bool)
    
    def test_revert_live_changes(self):
        """Test revert_live_changes method."""
        vehicle_session = 'test_session_123'
        applied_changes = [
            {
                'address': 0x100,
                'size': 4,
                'oldData': 'FFFFFFFF',
                'newData': '00000000',
                'mapType': 'TEST'
            }
        ]
        
        result = self.core.revert_live_changes(vehicle_session, applied_changes)
        
        self.assertIsInstance(result, ApplyResult)
        self.assertIsInstance(result.success, bool)
    
    def test_get_safety_status(self):
        """Test get_safety_status method."""
        status = self.core.get_safety_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('rustCoreAvailable', status)
        self.assertEqual(status['rustCoreAvailable'], RUST_AVAILABLE)
        self.assertIn('safetyLimits', status)


class TestGetVersaCore(unittest.TestCase):
    """Test get_versa_core function."""
    
    def test_get_versa_core_singleton(self):
        """Test get_versa_core returns singleton instance."""
        core1 = get_versa_core()
        core2 = get_versa_core()
        
        # Should return the same instance (singleton pattern)
        self.assertIs(core1, core2)
        self.assertIsInstance(core1, VersaTuningCore)


class TestDataClasses(unittest.TestCase):
    """Test dataclass definitions."""
    
    def test_map_change(self):
        """Test MapChange dataclass."""
        change = MapChange(
            address=0x100,
            size=4,
            old_data=b'\xFF\xFF\xFF\xFF',
            new_data=b'\x00\x00\x00\x00',
            map_type='TEST'
        )
        
        self.assertEqual(change.address, 0x100)
        self.assertEqual(change.size, 4)
        self.assertEqual(change.map_type, 'TEST')
    
    def test_patch_result(self):
        """Test PatchResult dataclass."""
        result = PatchResult(
            success=True,
            patch_data=b'\x00\x01\x02\x03',
            checksum=0x12345678,
            size=4,
            warnings=[],
            errors=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.size, 4)
    
    def test_validation_result(self):
        """Test ValidationResult dataclass."""
        result = ValidationResult(
            valid=True,
            risk_score=10,
            warnings=[],
            errors=[],
            safety_violations=[]
        )
        
        self.assertTrue(result.valid)
        self.assertEqual(result.risk_score, 10)
    
    def test_apply_result(self):
        """Test ApplyResult dataclass."""
        result = ApplyResult(
            success=True,
            ecu_verified=True,
            applied_changes=1,
            failed_changes=[],
            message='Success'
        )
        
        self.assertTrue(result.success)
        self.assertTrue(result.ecu_verified)
        self.assertEqual(result.applied_changes, 1)


if __name__ == '__main__':
    unittest.main()

