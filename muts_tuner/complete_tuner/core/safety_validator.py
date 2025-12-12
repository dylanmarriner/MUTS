#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAFETY VALIDATOR MODULE
Mock implementation for core.safety_validator
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class SafetyValidator:
    """Safety parameter validation for ECU tuning"""
    
    def __init__(self):
        self.limits = {
            # Engine limits
            'max_rpm': 8000,
            'min_rpm': 1000,
            'max_boost_psi': 30.0,
            'min_boost_psi': 0.0,
            'max_ignition_timing': 60.0,
            'min_ignition_timing': -20.0,
            'max_fuel_pulse_width': 50.0,
            'min_fuel_pulse_width': 0.0,
            
            # Temperature limits
            'max_coolant_temp': 120.0,
            'max_intake_temp': 80.0,
            'max_oil_temp': 150.0,
            
            # Pressure limits
            'max_oil_pressure': 100.0,
            'min_oil_pressure': 10.0,
            'max_fuel_pressure': 80.0,
            
            # Air-fuel ratio limits
            'max_afr': 18.0,
            'min_afr': 10.0,
            'max_lambda': 1.22,
            'min_lambda': 0.68
        }
        
        self.validation_rules = {
            'ignition_timing': self._validate_ignition_timing,
            'fuel_injection': self._validate_fuel_injection,
            'boost_control': self._validate_boost_control,
            'rpm_limiter': self._validate_rpm_limiter,
            'vvt_timing': self._validate_vvt_timing
        }
        
        logger.debug("SafetyValidator initialized with comprehensive limits")
    
    def validate_parameter(self, parameter: str, value: float) -> bool:
        """Validate single parameter against safety limits"""
        try:
            if parameter in self.limits:
                if parameter.startswith('max_'):
                    return value <= self.limits[parameter]
                elif parameter.startswith('min_'):
                    return value >= self.limits[parameter]
                else:
                    # For parameters without max/min prefix, check against both
                    max_key = f'max_{parameter}'
                    min_key = f'min_{parameter}'
                    
                    if max_key in self.limits and value > self.limits[max_key]:
                        return False
                    if min_key in self.limits and value < self.limits[min_key]:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Parameter validation error: {e}")
            return False
    
    def validate_map(self, map_type: str, map_data: np.ndarray) -> Tuple[bool, List[str]]:
        """Validate calibration map data"""
        try:
            errors = []
            
            if map_type not in self.validation_rules:
                logger.warning(f"No validation rule for map type: {map_type}")
                return True, errors
            
            # Check for invalid values
            if np.any(np.isnan(map_data)):
                errors.append("Map contains NaN values")
            
            if np.any(np.isinf(map_data)):
                errors.append("Map contains infinite values")
            
            # Apply specific validation rules
            validator = self.validation_rules[map_type]
            is_valid, rule_errors = validator(map_data)
            errors.extend(rule_errors)
            
            return is_valid and len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Map validation error: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    def _validate_ignition_timing(self, map_data: np.ndarray) -> Tuple[bool, List[str]]:
        """Validate ignition timing map"""
        errors = []
        
        # Check timing range
        if np.any(map_data < self.limits['min_ignition_timing']):
            errors.append(f"Ignition timing below minimum: {self.limits['min_ignition_timing']}°")
        
        if np.any(map_data > self.limits['max_ignition_timing']):
            errors.append(f"Ignition timing above maximum: {self.limits['max_ignition_timing']}°")
        
        # Check for reasonable gradients (no sudden jumps > 15°)
        if map_data.ndim == 2 and map_data.shape[0] > 1 and map_data.shape[1] > 1:
            gradients = np.gradient(map_data)
            max_gradient = np.max(np.abs(gradients))
            if max_gradient > 15.0:
                errors.append(f"Excessive ignition timing gradient: {max_gradient:.1f}°")
        
        return len(errors) == 0, errors
    
    def _validate_fuel_injection(self, map_data: np.ndarray) -> Tuple[bool, List[str]]:
        """Validate fuel injection map"""
        errors = []
        
        # Check pulse width range
        if np.any(map_data < self.limits['min_fuel_pulse_width']):
            errors.append(f"Fuel pulse width below minimum: {self.limits['min_fuel_pulse_width']}ms")
        
        if np.any(map_data > self.limits['max_fuel_pulse_width']):
            errors.append(f"Fuel pulse width above maximum: {self.limits['max_fuel_pulse_width']}ms")
        
        # Check for reasonable gradients
        if map_data.ndim == 2 and map_data.shape[0] > 1 and map_data.shape[1] > 1:
            gradients = np.gradient(map_data)
            max_gradient = np.max(np.abs(gradients))
            if max_gradient > 10.0:
                errors.append(f"Excessive fuel gradient: {max_gradient:.1f}ms")
        
        return len(errors) == 0, errors
    
    def _validate_boost_control(self, map_data: np.ndarray) -> Tuple[bool, List[str]]:
        """Validate boost control map"""
        errors = []
        
        # Check boost range
        if np.any(map_data < self.limits['min_boost_psi']):
            errors.append(f"Boost pressure below minimum: {self.limits['min_boost_psi']}psi")
        
        if np.any(map_data > self.limits['max_boost_psi']):
            errors.append(f"Boost pressure above maximum: {self.limits['max_boost_psi']}psi")
        
        # Check for reasonable gradients
        if map_data.ndim == 2 and map_data.shape[0] > 1 and map_data.shape[1] > 1:
            gradients = np.gradient(map_data)
            max_gradient = np.max(np.abs(gradients))
            if max_gradient > 5.0:
                errors.append(f"Excessive boost gradient: {max_gradient:.1f}psi")
        
        return len(errors) == 0, errors
    
    def _validate_rpm_limiter(self, map_data: np.ndarray) -> Tuple[bool, List[str]]:
        """Validate RPM limiter settings"""
        errors = []
        
        # Check RPM range
        if np.any(map_data < self.limits['min_rpm']):
            errors.append(f"RPM limiter below minimum: {self.limits['min_rpm']}")
        
        if np.any(map_data > self.limits['max_rpm']):
            errors.append(f"RPM limiter above maximum: {self.limits['max_rpm']}")
        
        return len(errors) == 0, errors
    
    def _validate_vvt_timing(self, map_data: np.ndarray) -> Tuple[bool, List[str]]:
        """Validate VVT timing map"""
        errors = []
        
        # Check VVT range (typically -20 to +60 degrees)
        vvt_min = -20.0
        vvt_max = 60.0
        
        if np.any(map_data < vvt_min):
            errors.append(f"VVT timing below minimum: {vvt_min}°")
        
        if np.any(map_data > vvt_max):
            errors.append(f"VVT timing above maximum: {vvt_max}°")
        
        return len(errors) == 0, errors
    
    def get_limits(self) -> Dict[str, float]:
        """Get all safety limits"""
        return self.limits.copy()
    
    def set_limit(self, parameter: str, value: float):
        """Update safety limit"""
        self.limits[parameter] = value
        logger.info(f"Safety limit updated: {parameter} = {value}")
    
    def validate_calibration_package(self, calibration_data: Dict[str, np.ndarray]) -> Tuple[bool, List[str]]:
        """Validate complete calibration package"""
        all_errors = []
        overall_valid = True
        
        for map_name, map_data in calibration_data.items():
            is_valid, errors = self.validate_map(map_name, map_data)
            if not is_valid:
                overall_valid = False
                all_errors.extend([f"{map_name}: {error}" for error in errors])
        
        return overall_valid, all_errors

# Global safety validator instance
_safety_validator = SafetyValidator()

def get_safety_validator() -> SafetyValidator:
    """Get global safety validator instance"""
    return _safety_validator

def create_safety_validator() -> SafetyValidator:
    """Create new safety validator instance"""
    return SafetyValidator()

logger.info("Safety validator module loaded")
