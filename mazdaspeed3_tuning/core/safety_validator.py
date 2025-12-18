#!/usr/bin/env python3
"""
SAFETY VALIDATOR MODULE
Configurable safety system for tuning parameters and real-time monitoring
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import os

class SafetyLevel(Enum):
    """Safety violation severity levels"""
    SAFE = "safe"
    WARNING = "warning"  # Can continue with reduced performance
    CRITICAL = "critical"  # Requires immediate action
    EMERGENCY = "emergency"  # Requires shutdown

@dataclass
class SafetyResult:
    """Safety validation result"""
    level: SafetyLevel
    message: str
    parameter: str
    current_value: float
    limit_value: float
    timestamp: float = 0.0

class SafetyValidator:
    """
    Configurable safety validator for Mazdaspeed 3 tuning
    Loads limits from config and validates both parameters and sensor data
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config/safety_limits.json"
        self.safety_limits = self._load_safety_limits()
        self.last_validation_time = 0.0
        self.validation_history = []
        
    def _load_safety_limits(self) -> Dict[str, Dict]:
        """Load safety limits from configuration file"""
        # Default safety limits based on Mazdaspeed 3 specifications
        default_limits = {
            "hard_limits": {
                "max_boost_psi": {"value": 22.0, "severity": "critical"},
                "max_engine_rpm": {"value": 7200, "severity": "emergency"},
                "max_exhaust_temp": {"value": 950.0, "severity": "critical"},
                "max_intake_temp": {"value": 60.0, "severity": "warning"},
                "max_coolant_temp": {"value": 105.0, "severity": "critical"},
                "min_afr": {"value": 10.8, "severity": "critical"},
                "max_afr": {"value": 12.5, "severity": "warning"},
                "max_ignition_timing": {"value": 12.0, "severity": "critical"},
                "min_ignition_timing": {"value": -8.0, "severity": "critical"},
                "max_injector_duty": {"value": 85.0, "severity": "critical"},
                "max_knock_retard": {"value": -8.0, "severity": "critical"},
                "max_manifold_pressure": {"value": 250.0, "severity": "critical"},
                "min_battery_voltage": {"value": 11.0, "severity": "warning"},
                "max_turbo_rpm": {"value": 220000, "severity": "emergency"}
            },
            "soft_limits": {
                "preferred_boost_range": {"min": 12.0, "max": 20.0, "severity": "warning"},
                "preferred_afr_range": {"min": 11.2, "max": 12.5, "severity": "warning"},
                "preferred_timing_range": {"min": 8.0, "max": 20.0, "severity": "warning"},
                "max_boost_variance": {"value": 2.0, "severity": "warning"},
                "max_afr_variance": {"value": 0.5, "severity": "warning"}
            },
            "rate_limits": {
                "max_boost_rate_change": {"value": 5.0, "severity": "warning"},  # PSI per second
                "max_rpm_rate_change": {"value": 1000.0, "severity": "warning"},  # RPM per second
                "max_temp_rate_change": {"value": 50.0, "severity": "warning"}  # °C per second
            }
        }
        
        # Try to load from file, fallback to defaults
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_limits = json.load(f)
                    # Merge with defaults
                    for category in default_limits:
                        if category in loaded_limits:
                            default_limits[category].update(loaded_limits[category])
            except Exception:
                pass  # Use defaults if file loading fails
        
        return default_limits
    
    def validate_tuning_parameters(self, parameters: Dict[str, float]) -> List[SafetyResult]:
        """Validate tuning parameters against safety limits"""
        results = []
        current_time = time.time()
        
        for param_name, value in parameters.items():
            result = self._validate_parameter(param_name, value, current_time)
            if result:
                results.append(result)
        
        self.last_validation_time = current_time
        self.validation_history.extend(results)
        
        # Keep only recent history (last 100 validations)
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]
        
        return results
    
    def validate_sensor_data(self, sensor_data: Dict[str, float], 
                           previous_data: Dict[str, float] = None) -> List[SafetyResult]:
        """Validate real-time sensor data"""
        results = []
        current_time = time.time()
        
        # Check hard limits
        for param_name, limit_config in self.safety_limits["hard_limits"].items():
            if param_name in sensor_data:
                value = sensor_data[param_name]
                result = self._check_hard_limit(param_name, value, limit_config, current_time)
                if result:
                    results.append(result)
        
        # Check soft limits
        for param_name, limit_config in self.safety_limits["soft_limits"].items():
            if param_name in sensor_data:
                value = sensor_data[param_name]
                result = self._check_soft_limit(param_name, value, limit_config, current_time)
                if result:
                    results.append(result)
        
        # Check rate limits if previous data available
        if previous_data:
            for param_name, limit_config in self.safety_limits["rate_limits"].items():
                if param_name in sensor_data and param_name.replace("max_", "").replace("_rate_change", "") in previous_data:
                    current_value = sensor_data[param_name.replace("max_", "").replace("_rate_change", "")]
                    previous_value = previous_data[param_name.replace("max_", "").replace("_rate_change", "")]
                    
                    if current_time > self.last_validation_time:
                        rate_change = abs(current_value - previous_value) / (current_time - self.last_validation_time)
                        result = self._check_rate_limit(param_name, rate_change, limit_config, current_time)
                        if result:
                            results.append(result)
        
        return results
    
    def _validate_parameter(self, param_name: str, value: float, timestamp: float) -> Optional[SafetyResult]:
        """Validate a single parameter"""
        # Check hard limits first
        if param_name in self.safety_limits["hard_limits"]:
            limit_config = self.safety_limits["hard_limits"][param_name]
            return self._check_hard_limit(param_name, value, limit_config, timestamp)
        
        # Check soft limits
        if param_name in self.safety_limits["soft_limits"]:
            limit_config = self.safety_limits["soft_limits"][param_name]
            return self._check_soft_limit(param_name, value, limit_config, timestamp)
        
        return None
    
    def _check_hard_limit(self, param_name: str, value: float, limit_config: Dict, timestamp: float) -> SafetyResult:
        """Check hard limit violation"""
        limit_value = limit_config["value"]
        severity = SafetyLevel(limit_config["severity"])
        
        if "max_" in param_name or "min_" in param_name:
            if "max_" in param_name and value > limit_value:
                return SafetyResult(
                    level=severity,
                    message=f"{param_name} exceeds maximum limit",
                    parameter=param_name,
                    current_value=value,
                    limit_value=limit_value,
                    timestamp=timestamp
                )
            elif "min_" in param_name and value < limit_value:
                return SafetyResult(
                    level=severity,
                    message=f"{param_name} below minimum limit",
                    parameter=param_name,
                    current_value=value,
                    limit_value=limit_value,
                    timestamp=timestamp
                )
        else:
            # For parameters without max/min prefix, assume it's a maximum
            if value > limit_value:
                return SafetyResult(
                    level=severity,
                    message=f"{param_name} exceeds limit",
                    parameter=param_name,
                    current_value=value,
                    limit_value=limit_value,
                    timestamp=timestamp
                )
        
        return SafetyResult(
            level=SafetyLevel.SAFE,
            message=f"{param_name} within limits",
            parameter=param_name,
            current_value=value,
            limit_value=limit_value,
            timestamp=timestamp
        )
    
    def _check_soft_limit(self, param_name: str, value: float, limit_config: Dict, timestamp: float) -> Optional[SafetyResult]:
        """Check soft limit violation"""
        severity = SafetyLevel(limit_config["severity"])
        
        if "range" in param_name:
            # Handle range-based limits
            if "min" in limit_config and value < limit_config["min"]:
                return SafetyResult(
                    level=severity,
                    message=f"{param_name} below preferred range",
                    parameter=param_name,
                    current_value=value,
                    limit_value=limit_config["min"],
                    timestamp=timestamp
                )
            elif "max" in limit_config and value > limit_config["max"]:
                return SafetyResult(
                    level=severity,
                    message=f"{param_name} above preferred range",
                    parameter=param_name,
                    current_value=value,
                    limit_value=limit_config["max"],
                    timestamp=timestamp
                )
        else:
            # Handle single value limits
            limit_value = limit_config["value"]
            if "variance" in param_name:
                # Variance limits are more complex - would need reference value
                pass
            elif value > limit_value:
                return SafetyResult(
                    level=severity,
                    message=f"{param_name} exceeds preferred limit",
                    parameter=param_name,
                    current_value=value,
                    limit_value=limit_value,
                    timestamp=timestamp
                )
        
        return None
    
    def _check_rate_limit(self, param_name: str, rate_change: float, limit_config: Dict, timestamp: float) -> Optional[SafetyResult]:
        """Check rate limit violation"""
        limit_value = limit_config["value"]
        severity = SafetyLevel(limit_config["severity"])
        
        if rate_change > limit_value:
            return SafetyResult(
                level=severity,
                message=f"{param_name} rate of change too rapid",
                parameter=param_name,
                current_value=rate_change,
                limit_value=limit_value,
                timestamp=timestamp
            )
        
        return None
    
    def get_overall_safety_level(self, results: List[SafetyResult]) -> SafetyLevel:
        """Determine overall safety level from validation results"""
        if not results:
            return SafetyLevel.SAFE
        
        # Return the highest severity level found
        severity_order = [SafetyLevel.SAFE, SafetyLevel.WARNING, SafetyLevel.CRITICAL, SafetyLevel.EMERGENCY]
        
        for severity in reversed(severity_order):
            if any(result.level == severity for result in results):
                return severity
        
        return SafetyLevel.SAFE
    
    def should_shutdown(self, results: List[SafetyResult]) -> bool:
        """Determine if system should shutdown based on safety violations"""
        return any(result.level == SafetyLevel.EMERGENCY for result in results)
    
    def should_reduce_performance(self, results: List[SafetyResult]) -> bool:
        """Determine if performance should be reduced"""
        return any(result.level in [SafetyLevel.CRITICAL, SafetyLevel.WARNING] for result in results)
    
    def get_safety_adjustments(self, results: List[SafetyResult]) -> Dict[str, float]:
        """Get recommended adjustments based on safety violations"""
        adjustments = {}
        
        for result in results:
            if result.level == SafetyLevel.CRITICAL:
                if "boost" in result.parameter.lower():
                    # Reduce boost if over limit
                    adjustments["boost_reduction"] = 2.0
                elif "timing" in result.parameter.lower():
                    # Retard timing if over limit
                    adjustments["timing_retard"] = -2.0
                elif "afr" in result.parameter.lower():
                    # Enrich mixture if too lean
                    adjustments["fuel_enrichment"] = 0.5
        
        return adjustments

def get_safety_validator(config_path: str = None) -> SafetyValidator:
    """Factory function to get safety validator instance"""
    return SafetyValidator(config_path)