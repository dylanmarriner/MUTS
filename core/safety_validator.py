#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3 SAFETY VALIDATION SYSTEM
Critical safety layer to prevent dangerous tuning parameters
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from core.app_state import get_app_state, PerformanceMode
from utils.logger import get_logger

logger = get_logger(__name__)

class SafetyLevel(Enum):
    """Safety validation levels"""
    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"

@dataclass
class SafetyLimits:
    """Hard safety limits for ECU parameters"""
    max_boost_psi: float = 25.0
    max_timing_advance: float = 30.0
    min_afr_wot: float = 10.5
    max_egt_c: float = 950.0
    max_rpm: float = 7000.0
    max_injector_duty: float = 95.0
    max_fuel_pressure: float = 80.0
    min_oil_pressure: float = 10.0
    max_coolant_temp: float = 105.0
    max_intake_temp: float = 80.0

@dataclass
class SafetyViolation:
    """Safety violation information"""
    parameter: str
    current_value: float
    limit_value: float
    severity: SafetyLevel
    message: str
    timestamp: float

class SafetyValidator:
    """
    CRITICAL SAFETY VALIDATION LAYER
    Validates all tuning parameters before ECU writes
    """
    
    def __init__(self):
        self.app_state = get_app_state()
        self.limits = SafetyLimits()
        self.violations: List[SafetyViolation] = []
        self.safety_override = False
        self.last_validation = 0.0
        
        # Mode-specific limits
        self.mode_limits = {
            PerformanceMode.STOCK: {
                'max_boost_psi': 16.0,
                'max_timing_advance': 15.0,
                'min_afr_wot': 12.5
            },
            PerformanceMode.STREET: {
                'max_boost_psi': 20.0,
                'max_timing_advance': 20.0,
                'min_afr_wot': 11.8
            },
            PerformanceMode.TRACK: {
                'max_boost_psi': 23.0,
                'max_timing_advance': 25.0,
                'min_afr_wot': 11.5
            },
            PerformanceMode.DRAG: {
                'max_boost_psi': 24.0,
                'max_timing_advance': 27.0,
                'min_afr_wot': 11.3
            },
            PerformanceMode.SAFE: {
                'max_boost_psi': 18.0,
                'max_timing_advance': 18.0,
                'min_afr_wot': 12.0
            }
        }
        
        logger.info("Safety validator initialized")
    
    def validate_tuning_parameters(self, params: Dict[str, float]) -> Tuple[bool, List[SafetyViolation]]:
        """
        Validate tuning parameters against safety limits
        
        Args:
            params: Dictionary of tuning parameters
            
        Returns:
            Tuple of (is_safe, violations)
        """
        try:
            self.violations.clear()
            
            # Get current performance mode
            tuning = self.app_state.get_tuning_parameters()
            mode_limits = self.mode_limits.get(tuning.performance_mode, {})
            
            # Validate boost pressure
            if 'boost_target' in params:
                boost = params['boost_target']
                max_boost = mode_limits.get('max_boost_psi', self.limits.max_boost_psi)
                
                if boost > max_boost:
                    severity = SafetyLevel.CRITICAL if boost > self.limits.max_boost_psi else SafetyLevel.DANGEROUS
                    self.violations.append(SafetyViolation(
                        parameter='boost_target',
                        current_value=boost,
                        limit_value=max_boost,
                        severity=severity,
                        message=f"Boost target {boost:.1f} psi exceeds limit {max_boost:.1f} psi",
                        timestamp=time.time()
                    ))
            
            # Validate ignition timing
            if 'timing_base' in params:
                timing = params['timing_base']
                max_timing = mode_limits.get('max_timing_advance', self.limits.max_timing_advance)
                
                if timing > max_timing:
                    severity = SafetyLevel.CRITICAL if timing > self.limits.max_timing_advance else SafetyLevel.DANGEROUS
                    self.violations.append(SafetyViolation(
                        parameter='timing_base',
                        current_value=timing,
                        limit_value=max_timing,
                        severity=severity,
                        message=f"Timing advance {timing:.1f}° exceeds limit {max_timing:.1f}°",
                        timestamp=time.time()
                    ))
            
            # Validate AFR
            if 'afr_target' in params:
                afr = params['afr_target']
                min_afr = mode_limits.get('min_afr_wot', self.limits.min_afr_wot)
                
                if afr < min_afr:
                    severity = SafetyLevel.CRITICAL if afr < self.limits.min_afr_wot else SafetyLevel.DANGEROUS
                    self.violations.append(SafetyViolation(
                        parameter='afr_target',
                        current_value=afr,
                        limit_value=min_afr,
                        severity=severity,
                        message=f"AFR target {afr:.1f} too lean, minimum {min_afr:.1f}",
                        timestamp=time.time()
                    ))
            
            # Validate rev limit
            if 'rev_limit' in params:
                rev_limit = params['rev_limit']
                if rev_limit > self.limits.max_rpm:
                    self.violations.append(SafetyViolation(
                        parameter='rev_limit',
                        current_value=rev_limit,
                        limit_value=self.limits.max_rpm,
                        severity=SafetyLevel.CRITICAL,
                        message=f"Rev limit {rev_limit:.0f} RPM exceeds maximum {self.limits.max_rpm:.0f} RPM",
                        timestamp=time.time()
                    ))
            
            # Check for critical violations
            critical_violations = [v for v in self.violations if v.severity == SafetyLevel.CRITICAL]
            is_safe = len(critical_violations) == 0 or self.safety_override
            
            self.last_validation = time.time()
            
            logger.info(f"Parameter validation: {'SAFE' if is_safe else 'UNSAFE'} ({len(self.violations)} violations)")
            
            return is_safe, self.violations
            
        except Exception as e:
            logger.error(f"Error validating tuning parameters: {e}")
            return False, [SafetyViolation(
                parameter='validation_error',
                current_value=0.0,
                limit_value=0.0,
                severity=SafetyLevel.CRITICAL,
                message=f"Validation system error: {e}",
                timestamp=time.time()
            )]
    
    def validate_live_data(self, ecu_data: Dict[str, float]) -> Tuple[bool, List[SafetyViolation]]:
        """
        Validate live ECU data for dangerous conditions
        
        Args:
            ecu_data: Current ECU sensor data
            
        Returns:
            Tuple of (is_safe, violations)
        """
        try:
            live_violations = []
            
            # Check coolant temperature
            if 'coolant_temp' in ecu_data:
                coolant = ecu_data['coolant_temp']
                if coolant > self.limits.max_coolant_temp:
                    live_violations.append(SafetyViolation(
                        parameter='coolant_temp',
                        current_value=coolant,
                        limit_value=self.limits.max_coolant_temp,
                        severity=SafetyLevel.CRITICAL,
                        message=f"Coolant temperature {coolant:.1f}°C exceeds limit {self.limits.max_coolant_temp:.1f}°C",
                        timestamp=time.time()
                    ))
            
            # Check oil pressure
            if 'oil_pressure' in ecu_data:
                oil_pressure = ecu_data['oil_pressure']
                if oil_pressure < self.limits.min_oil_pressure:
                    live_violations.append(SafetyViolation(
                        parameter='oil_pressure',
                        current_value=oil_pressure,
                        limit_value=self.limits.min_oil_pressure,
                        severity=SafetyLevel.CRITICAL,
                        message=f"Oil pressure {oil_pressure:.1f} psi below minimum {self.limits.min_oil_pressure:.1f} psi",
                        timestamp=time.time()
                    ))
            
            # Check EGT
            if 'egt_temp' in ecu_data:
                egt = ecu_data['egt_temp']
                if egt > self.limits.max_egt_c:
                    live_violations.append(SafetyViolation(
                        parameter='egt_temp',
                        current_value=egt,
                        limit_value=self.limits.max_egt_c,
                        severity=SafetyLevel.CRITICAL,
                        message=f"EGT {egt:.1f}°C exceeds limit {self.limits.max_egt_c:.1f}°C",
                        timestamp=time.time()
                    ))
            
            # Check RPM
            if 'engine_rpm' in ecu_data:
                rpm = ecu_data['engine_rpm']
                if rpm > self.limits.max_rpm:
                    live_violations.append(SafetyViolation(
                        parameter='engine_rpm',
                        current_value=rpm,
                        limit_value=self.limits.max_rpm,
                        severity=SafetyLevel.CRITICAL,
                        message=f"Engine RPM {rpm:.0f} exceeds limit {self.limits.max_rpm:.0f}",
                        timestamp=time.time()
                    ))
            
            is_safe = len(live_violations) == 0
            
            if not is_safe:
                logger.warning(f"Live data safety violations detected: {len(live_violations)}")
                for violation in live_violations:
                    logger.error(f"  {violation.message}")
            
            return is_safe, live_violations
            
        except Exception as e:
            logger.error(f"Error validating live data: {e}")
            return False, []
    
    def enable_safety_override(self, password: str) -> bool:
        """
        Enable safety override (requires confirmation)
        
        Args:
            password: Override password
            
        Returns:
            bool: True if override enabled
        """
        try:
            # Simple password check (in production, use proper authentication)
            if password == "MUTS_OVERRIDE_2024":
                self.safety_override = True
                logger.warning("SAFETY OVERRIDE ENABLED - Use with extreme caution!")
                return True
            else:
                logger.error("Invalid safety override password")
                return False
                
        except Exception as e:
            logger.error(f"Error enabling safety override: {e}")
            return False
    
    def disable_safety_override(self):
        """Disable safety override"""
        self.safety_override = False
        logger.info("Safety override disabled")
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety system status"""
        return {
            'safety_override': self.safety_override,
            'active_violations': len(self.violations),
            'last_validation': self.last_validation,
            'critical_limits': {
                'max_boost_psi': self.limits.max_boost_psi,
                'max_timing_advance': self.limits.max_timing_advance,
                'min_afr_wot': self.limits.min_afr_wot,
                'max_egt_c': self.limits.max_egt_c,
                'max_rpm': self.limits.max_rpm
            }
        }

# Global safety validator instance
safety_validator = SafetyValidator()

def get_safety_validator() -> SafetyValidator:
    """Get global safety validator instance"""
    return safety_validator
