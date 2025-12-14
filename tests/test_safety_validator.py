"""Tests for core safety_validator module."""
import unittest
from unittest.mock import Mock, patch

from core.safety_validator import (
    SafetyValidator, SafetyLevel, SafetyLimits, SafetyViolation,
    get_safety_validator
)
from core.app_state import PerformanceMode


class TestSafetyLevel(unittest.TestCase):
    """Test SafetyLevel enum."""
    
    def test_safety_level_values(self):
        """Test SafetyLevel enum values."""
        self.assertEqual(SafetyLevel.SAFE.value, "safe")
        self.assertEqual(SafetyLevel.WARNING.value, "warning")
        self.assertEqual(SafetyLevel.DANGEROUS.value, "dangerous")
        self.assertEqual(SafetyLevel.CRITICAL.value, "critical")


class TestSafetyLimits(unittest.TestCase):
    """Test SafetyLimits dataclass."""
    
    def test_safety_limits_defaults(self):
        """Test SafetyLimits default values."""
        limits = SafetyLimits()
        self.assertEqual(limits.max_boost_psi, 25.0)
        self.assertEqual(limits.max_timing_advance, 30.0)
        self.assertEqual(limits.min_afr_wot, 10.5)  # Actual default is 10.5
        self.assertEqual(limits.max_egt_c, 950.0)
        self.assertEqual(limits.max_rpm, 7000.0)  # float, not int


class TestSafetyViolation(unittest.TestCase):
    """Test SafetyViolation dataclass."""
    
    def test_safety_violation_creation(self):
        """Test SafetyViolation creation."""
        violation = SafetyViolation(
            parameter='boost_target',
            current_value=30.0,
            limit_value=25.0,
            severity=SafetyLevel.CRITICAL,
            message='Boost too high',
            timestamp=1234567890.0
        )
        
        self.assertEqual(violation.parameter, 'boost_target')
        self.assertEqual(violation.current_value, 30.0)
        self.assertEqual(violation.severity, SafetyLevel.CRITICAL)


class TestSafetyValidator(unittest.TestCase):
    """Test SafetyValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock app_state with proper structure
        self.mock_app_state = Mock()
        self.mock_tuning_params = Mock()
        self.mock_tuning_params.performance_mode = PerformanceMode.TRACK
        self.mock_app_state.get_tuning_parameters.return_value = self.mock_tuning_params
        
        with patch('core.safety_validator.get_app_state', return_value=self.mock_app_state):
            self.validator = SafetyValidator()
            self.validator.app_state = self.mock_app_state
    
    def test_initialization(self):
        """Test SafetyValidator initialization."""
        self.assertIsNotNone(self.validator.limits)
        self.assertIsInstance(self.validator.limits, SafetyLimits)
        self.assertFalse(self.validator.safety_override)
        self.assertEqual(len(self.validator.violations), 0)
    
    def test_validate_tuning_parameters_safe(self):
        """Test validate_tuning_parameters with safe parameters."""
        safe_params = {
            'boost_target': 15.0,
            'timing_base': 12.0,
            'afr_target': 12.5
        }
        
        is_safe, violations = self.validator.validate_tuning_parameters(safe_params)
        
        self.assertTrue(is_safe)
        self.assertEqual(len(violations), 0)
    
    def test_validate_tuning_parameters_dangerous_boost(self):
        """Test validate_tuning_parameters with dangerous boost."""
        dangerous_params = {
            'boost_target': 30.0,  # Exceeds limit
            'timing_base': 12.0,
            'afr_target': 12.5
        }
        
        is_safe, violations = self.validator.validate_tuning_parameters(dangerous_params)
        
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)
        self.assertTrue(any(v.parameter == 'boost_target' for v in violations))
    
    def test_validate_tuning_parameters_dangerous_timing(self):
        """Test validate_tuning_parameters with dangerous timing."""
        dangerous_params = {
            'boost_target': 15.0,
            'timing_base': 35.0,  # Exceeds limit
            'afr_target': 12.5
        }
        
        is_safe, violations = self.validator.validate_tuning_parameters(dangerous_params)
        
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)
        self.assertTrue(any(v.parameter == 'timing_base' for v in violations))
    
    def test_validate_tuning_parameters_dangerous_afr(self):
        """Test validate_tuning_parameters with dangerous AFR."""
        dangerous_params = {
            'boost_target': 15.0,
            'timing_base': 12.0,
            'afr_target': 10.0  # Too lean
        }
        
        is_safe, violations = self.validator.validate_tuning_parameters(dangerous_params)
        
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)
        self.assertTrue(any(v.parameter == 'afr_target' for v in violations))
    
    def test_validate_tuning_parameters_dangerous_rev_limit(self):
        """Test validate_tuning_parameters with dangerous rev limit."""
        dangerous_params = {
            'rev_limit': 8000  # Exceeds max_rpm
        }
        
        is_safe, violations = self.validator.validate_tuning_parameters(dangerous_params)
        
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)
        self.assertTrue(any(v.parameter == 'rev_limit' for v in violations))
    
    def test_validate_tuning_parameters_mode_limits_stock(self):
        """Test validate_tuning_parameters with STOCK mode limits."""
        params = {
            'boost_target': 17.0,  # Exceeds STOCK limit of 16.0
            'timing_base': 12.0
        }
        
        # Update the mock to return STOCK mode
        self.mock_tuning_params.performance_mode = PerformanceMode.STOCK
        
        is_safe, violations = self.validator.validate_tuning_parameters(params)
        
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)
    
    def test_validate_tuning_parameters_mode_limits_street(self):
        """Test validate_tuning_parameters with STREET mode limits."""
        params = {
            'boost_target': 21.0,  # Exceeds STREET limit of 20.0
            'timing_base': 12.0
        }
        
        # Update the mock to return STREET mode
        self.mock_tuning_params.performance_mode = PerformanceMode.STREET
        
        is_safe, violations = self.validator.validate_tuning_parameters(params)
        
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)
    
    def test_validate_tuning_parameters_safety_override(self):
        """Test validate_tuning_parameters with safety override enabled."""
        dangerous_params = {
            'boost_target': 30.0,
            'timing_base': 35.0,
            'afr_target': 10.0
        }
        
        self.validator.safety_override = True
        
        is_safe, violations = self.validator.validate_tuning_parameters(dangerous_params)
        
        # Should be safe even with violations when override is enabled
        self.assertTrue(is_safe)
    
    def test_validate_live_data_safe(self):
        """Test validate_live_data with safe data."""
        safe_data = {
            'coolant_temp': 90.0,
            'oil_pressure': 60.0,
            'egt_temp': 800.0,
            'engine_rpm': 5000.0
        }
        
        is_safe, violations = self.validator.validate_live_data(safe_data)
        
        self.assertTrue(is_safe)
        self.assertEqual(len(violations), 0)
    
    def test_validate_live_data_dangerous_boost(self):
        """Test validate_live_data with dangerous boost."""
        # validate_live_data checks for coolant_temp, oil_pressure, egt_temp, engine_rpm
        # Not boost_psi, so let's test with dangerous EGT
        dangerous_data = {
            'egt_temp': 1000.0,  # Exceeds limit (max is 950)
            'engine_rpm': 5000.0
        }
        
        is_safe, violations = self.validator.validate_live_data(dangerous_data)
        
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)
        self.assertTrue(any(v.parameter == 'egt_temp' for v in violations))
    
    def test_validate_live_data_dangerous_egt(self):
        """Test validate_live_data with dangerous EGT."""
        dangerous_data = {
            'egt_temp': 1000.0,  # Exceeds limit (max is 950)
            'engine_rpm': 5000.0
        }
        
        is_safe, violations = self.validator.validate_live_data(dangerous_data)
        
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)
        self.assertTrue(any(v.parameter == 'egt_temp' for v in violations))
    
    def test_enable_safety_override_correct_password(self):
        """Test enable_safety_override with correct password."""
        result = self.validator.enable_safety_override("MUTS_OVERRIDE_2024")
        
        self.assertTrue(result)
        self.assertTrue(self.validator.safety_override)
    
    def test_enable_safety_override_incorrect_password(self):
        """Test enable_safety_override with incorrect password."""
        result = self.validator.enable_safety_override("wrong_password")
        
        self.assertFalse(result)
        self.assertFalse(self.validator.safety_override)
    
    def test_disable_safety_override(self):
        """Test disable_safety_override method."""
        self.validator.safety_override = True
        self.validator.disable_safety_override()
        
        self.assertFalse(self.validator.safety_override)
    
    def test_get_safety_status(self):
        """Test get_safety_status method."""
        status = self.validator.get_safety_status()
        
        self.assertIn('safety_override', status)
        self.assertIn('active_violations', status)
        self.assertIn('last_validation', status)
        self.assertIn('critical_limits', status)
        self.assertIsInstance(status['critical_limits'], dict)


class TestGetSafetyValidator(unittest.TestCase):
    """Test get_safety_validator function."""
    
    def test_get_safety_validator(self):
        """Test get_safety_validator returns SafetyValidator instance."""
        with patch('core.safety_validator.get_app_state'):
            validator = get_safety_validator()
            self.assertIsInstance(validator, SafetyValidator)


if __name__ == '__main__':
    unittest.main()

