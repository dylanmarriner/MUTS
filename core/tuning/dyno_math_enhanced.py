#!/usr/bin/env python3
"""
Enhanced DynoMath Physics Engine with Constants Enforcement
Calculates vehicle power and performance metrics with strict validation
"""

import logging
import math
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

from core.tuning.vehicle_constants import VehicleConstants, ConstantsError

logger = logging.getLogger(__name__)

class Unit(Enum):
    """Measurement units"""
    METRIC = 0  # kW, Nm, km/h
    IMPERIAL = 1  # hp, ft-lb, mph

@dataclass
class PowerMeasurement:
    """Power measurement at a specific RPM"""
    rpm: float
    torque: float  # Nm
    power: float  # kW
    wheel_power: float  # kW
    wheel_torque: float  # Nm
    timestamp: Optional[float] = None
    gear: Optional[int] = None

@dataclass
class DynoRun:
    """Complete dyno run results"""
    measurements: List[PowerMeasurement]
    max_power: float  # kW
    max_torque: float  # Nm
    power_curve: np.ndarray
    torque_curve: np.ndarray
    unit: Unit
    constants_version: int
    telemetry_source: str
    timestamp: datetime
    simulation: bool = False
    calculation_trace: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class DynoConfig:
    """Configuration for dyno run"""
    min_rpm: float = 1000
    max_rpm: float = 7000
    min_speed: float = 5.0  # m/s
    max_speed: float = 70.0  # m/s
    smoothing_window: int = 3
    correction_factor: float = 1.0  # SAE/STD correction

class ConstantsRequiredError(Exception):
    """Raised when vehicle constants are required but not provided"""
    pass

class DynoMathEnhanced:
    """
    Enhanced physics engine with strict constants enforcement
    
    This class implements mathematical models for power calculation
    with mandatory vehicle constants and full audit trail.
    """
    
    # Physical constants
    GRAVITY = 9.80665  # m/s²
    AIR_DENSITY_SEA_LEVEL = 1.225  # kg/m³
    
    def __init__(self, constants: VehicleConstants):
        """Initialize with vehicle constants - REQUIRED"""
        if not isinstance(constants, VehicleConstants):
            raise ConstantsRequiredError("VehicleConstants instance required")
        
        # Validate constants
        errors = constants.validate()
        if errors:
            raise ConstantsError(f"Invalid constants: {'; '.join(errors)}")
        
        self.constants = constants
        self._calculation_trace: List[Dict[str, Any]] = []
        
        logger.info(f"DynoMathEnhanced initialized with constants v{constants.version}")
        
        # Store initial constants in trace
        self._trace("init", {
            "constants_version": constants.version,
            "vehicle_mass": constants.vehicle_mass,
            "total_mass": constants.get_total_mass(),
            "drag_coefficient": constants.drag_coefficient,
            "gear_count": len(constants.gear_ratios)
        })
    
    def calculate_power_from_acceleration(self, speed_data: List[float], 
                                       time_data: List[float],
                                       config: Optional[DynoConfig] = None,
                                       telemetry_source: str = "unknown",
                                       simulation: bool = False) -> DynoRun:
        """
        Calculate power from acceleration data with full validation
        
        Args:
            speed_data: Vehicle speed over time (m/s)
            time_data: Corresponding timestamps (s)
            config: Dyno configuration
            telemetry_source: Source of telemetry data
            simulation: True if this is simulated data
            
        Returns:
            DynoRun with calculated power and torque
            
        Raises:
            ConstantsRequiredError: If constants are invalid
            ValueError: If input data is invalid
        """
        self._calculation_trace = []  # Reset trace for this run
        
        # Validate inputs
        self._validate_inputs(speed_data, time_data, config)
        
        self._trace("input_validation", {
            "data_points": len(speed_data),
            "time_span": time_data[-1] - time_data[0] if time_data else 0,
            "speed_range": [min(speed_data), max(speed_data)] if speed_data else [0, 0],
            "telemetry_source": telemetry_source,
            "simulation": simulation
        })
        
        try:
            # Convert to metric if needed
            if config and config.correction_factor != 1.0:
                self._trace("correction_factor", {
                    "factor": config.correction_factor,
                    "reason": "SAE/STD correction applied"
                })
            
            # Calculate acceleration
            acceleration = self._calculate_acceleration(speed_data, time_data)
            self._trace("acceleration_calculation", {
                "method": "numerical_differentiation",
                "max_acceleration": max(acceleration) if acceleration else 0,
                "samples": len(acceleration)
            })
            
            # Calculate forces
            forces = self._calculate_forces(speed_data, acceleration)
            self._trace("force_calculation", {
                "method": "F_total = F_acceleration + F_drag + F_rolling",
                "max_force": max(forces) if forces else 0,
                "components": {
                    "mass": self.constants.get_total_mass(),
                    "drag_coefficient": self.constants.drag_coefficient,
                    "rolling_resistance": self.constants.rolling_resistance
                }
            })
            
            # Calculate power at wheels
            wheel_power = []
            for i, (speed, force) in enumerate(zip(speed_data, forces)):
                if i < len(forces):
                    power = speed * force
                    wheel_power.append(power)
                else:
                    wheel_power.append(0)
            
            self._trace("wheel_power_calculation", {
                "method": "P = F × v",
                "max_wheel_power": max(wheel_power) if wheel_power else 0
            })
            
            # Estimate engine RPM from speed using gear ratios
            rpm_data, gear_data = self._speed_to_rpm_with_gears(speed_data)
            self._trace("rpm_estimation", {
                "method": "RPM = (v × 60) / (π × r) × gear_ratio × final_drive",
                "gear_ratios_used": self.constants.gear_ratios,
                "final_drive": self.constants.final_drive_ratio,
                "tire_radius": self.constants.tire_radius
            })
            
            # Calculate engine power (accounting for drivetrain loss)
            engine_power = []
            for wp in wheel_power:
                ep = wp / self.constants.drivetrain_efficiency
                if config and config.correction_factor != 1.0:
                    ep *= config.correction_factor
                engine_power.append(ep)
            
            self._trace("engine_power_calculation", {
                "method": "P_engine = P_wheel / η_drivetrain",
                "drivetrain_efficiency": self.constants.drivetrain_efficiency,
                "max_engine_power": max(engine_power) if engine_power else 0
            })
            
            # Calculate torque
            torque = []
            for power, rpm in zip(engine_power, rpm_data):
                if rpm > 0:
                    t = self._power_to_torque(power, rpm)
                    torque.append(t)
                else:
                    torque.append(0)
            
            self._trace("torque_calculation", {
                "method": "T = P / ω",
                "max_torque": max(torque) if torque else 0
            })
            
            # Apply smoothing if configured
            if config and config.smoothing_window > 1:
                engine_power = self._smooth_data(engine_power, config.smoothing_window)
                torque = self._smooth_data(torque, config.smoothing_window)
                self._trace("smoothing_applied", {
                    "window_size": config.smoothing_window,
                    "method": "moving_average"
                })
            
            # Create measurements
            measurements = []
            for i in range(len(rpm_data)):
                if i < len(engine_power) and i < len(torque) and rpm_data[i] > 0:
                    measurements.append(PowerMeasurement(
                        rpm=rpm_data[i],
                        torque=torque[i],
                        power=engine_power[i],
                        wheel_power=wheel_power[i] if i < len(wheel_power) else 0,
                        wheel_torque=torque[i] * self.constants.drivetrain_efficiency,
                        timestamp=time_data[i] if i < len(time_data) else None,
                        gear=gear_data[i] if i < len(gear_data) else None
                    ))
            
            # Filter by RPM range if configured
            if config:
                measurements = [m for m in measurements 
                              if config.min_rpm <= m.rpm <= config.max_rpm]
            
            # Create curves
            rpm_values = [m.rpm for m in measurements]
            power_values = [m.power for m in measurements]
            torque_values = [m.torque for m in measurements]
            
            power_curve = self._create_curve(rpm_values, power_values)
            torque_curve = self._create_curve(rpm_values, torque_values)
            
            # Find max values
            max_power = max(power_values) if power_values else 0
            max_torque = max(torque_values) if torque_values else 0
            
            # Create result
            result = DynoRun(
                measurements=measurements,
                max_power=max_power,
                max_torque=max_torque,
                power_curve=power_curve,
                torque_curve=torque_curve,
                unit=Unit.METRIC,
                constants_version=self.constants.version,
                telemetry_source=telemetry_source,
                timestamp=datetime.utcnow(),
                simulation=simulation,
                calculation_trace=self._calculation_trace.copy()
            )
            
            self._trace("result_summary", {
                "max_power_kw": max_power,
                "max_torque_nm": max_torque,
                "measurement_count": len(measurements),
                "constants_version": self.constants.version
            })
            
            logger.info(f"Power calculation complete: {max_power:.1f} kW, {max_torque:.1f} Nm")
            return result
            
        except Exception as e:
            self._trace("error", {"error": str(e), "type": type(e).__name__})
            logger.error(f"Power calculation failed: {e}")
            raise
    
    def _validate_inputs(self, speed_data: List[float], time_data: List[float], 
                        config: Optional[DynoConfig]) -> None:
        """Validate input data"""
        if not speed_data or not time_data:
            raise ValueError("Speed and time data cannot be empty")
        
        if len(speed_data) != len(time_data):
            raise ValueError("Speed and time data must have same length")
        
        if len(speed_data) < 10:
            raise ValueError("Need at least 10 data points for calculation")
        
        # Check time progression
        for i in range(1, len(time_data)):
            if time_data[i] <= time_data[i-1]:
                raise ValueError("Time data must be strictly increasing")
        
        # Check for reasonable speeds
        if max(speed_data) > 100:  # > 360 km/h
            raise ValueError("Speed values seem unrealistic (>100 m/s)")
        
        if min(speed_data) < 0:
            raise ValueError("Speed cannot be negative")
    
    def _calculate_acceleration(self, speed: List[float], time: List[float]) -> List[float]:
        """Calculate acceleration from speed data"""
        acceleration = []
        for i in range(1, len(speed)):
            dv = speed[i] - speed[i-1]
            dt = time[i] - time[i-1]
            if dt > 0:
                accel = dv / dt
                # Filter unrealistic acceleration
                if abs(accel) < 20:  # < 2g
                    acceleration.append(accel)
                else:
                    acceleration.append(0)  # Cap to reasonable value
        return acceleration
    
    def _calculate_forces(self, speed: List[float], acceleration: List[float]) -> List[float]:
        """Calculate total forces acting on vehicle"""
        forces = []
        total_mass = self.constants.get_total_mass()
        
        for i in range(len(acceleration)):
            # Acceleration force (F = ma)
            accel_force = total_mass * acceleration[i]
            
            # Drag force (F = 0.5 * ρ * Cd * A * v²)
            if i < len(speed):
                drag_force = (0.5 * self.constants.air_density * 
                            self.constants.drag_coefficient * 
                            self.constants.frontal_area * 
                            speed[i] ** 2)
            else:
                drag_force = 0
            
            # Rolling resistance (F = Cr * m * g)
            rolling_force = (self.constants.rolling_resistance * 
                           total_mass * 
                           self.constants.gravity)
            
            # Grade force (if not flat)
            grade_force = 0
            if self.constants.road_grade != 0:
                grade_force = total_mass * self.constants.gravity * \
                            math.sin(math.radians(self.constants.road_grade))
            
            # Total force
            total_force = accel_force + drag_force + rolling_force + grade_force
            forces.append(total_force)
        
        return forces
    
    def _speed_to_rpm_with_gears(self, speed: List[float]) -> Tuple[List[float], List[int]]:
        """Convert vehicle speed to engine RPM with gear estimation"""
        rpm_data = []
        gear_data = []
        
        for v in speed:
            # Calculate wheel RPM
            wheel_rpm = (v * 60) / (2 * math.pi * self.constants.tire_radius)
            
            # Estimate gear based on speed
            # Simplified: assume optimal shift points
            estimated_gear = 0
            for i, gear_ratio in enumerate(self.constants.gear_ratios):
                engine_rpm = wheel_rpm * gear_ratio * self.constants.final_drive_ratio
                if 1000 <= engine_rpm <= 6500:  # Reasonable RPM range
                    estimated_gear = i + 1
                    rpm_data.append(engine_rpm)
                    gear_data.append(estimated_gear)
                    break
            else:
                # Use highest gear if out of range
                gear_ratio = self.constants.gear_ratios[-1]
                engine_rpm = wheel_rpm * gear_ratio * self.constants.final_drive_ratio
                rpm_data.append(engine_rpm)
                gear_data.append(len(self.constants.gear_ratios))
        
        return rpm_data, gear_data
    
    def _power_to_torque(self, power: float, rpm: float) -> float:
        """Convert power to torque"""
        if rpm <= 0:
            return 0
        # Torque (Nm) = Power (W) / Angular velocity (rad/s)
        # Power (kW) to W: multiply by 1000
        # RPM to rad/s: multiply by 2π/60
        return (power * 1000) / (rpm * 2 * math.pi / 60)
    
    def _smooth_data(self, data: List[float], window: int) -> List[float]:
        """Apply moving average smoothing"""
        if not data or window <= 1:
            return data
        
        smoothed = []
        half_window = window // 2
        
        for i in range(len(data)):
            start = max(0, i - half_window)
            end = min(len(data), i + half_window + 1)
            avg = sum(data[start:end]) / (end - start)
            smoothed.append(avg)
        
        return smoothed
    
    def _create_curve(self, x_data: List[float], y_data: List[float]) -> np.ndarray:
        """Create a smooth curve from data points"""
        if len(x_data) != len(y_data) or len(x_data) < 2:
            return np.array([])
        
        # Sort by x values
        sorted_data = sorted(zip(x_data, y_data))
        x_sorted, y_sorted = zip(*sorted_data)
        
        # Interpolate to create smooth curve
        x_new = np.linspace(min(x_sorted), max(x_sorted), 100)
        y_new = np.interp(x_new, x_sorted, y_sorted)
        
        return np.column_stack((x_new, y_new))
    
    def _trace(self, step: str, data: Dict[str, Any]) -> None:
        """Add calculation step to trace"""
        trace_entry = {
            "step": step,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        self._calculation_trace.append(trace_entry)
    
    def get_calculation_trace(self) -> List[Dict[str, Any]]:
        """Get the full calculation trace"""
        return self._calculation_trace.copy()
    
    def export_trace(self, filepath: str) -> None:
        """Export calculation trace to file"""
        with open(filepath, 'w') as f:
            json.dump({
                "constants": self.constants.to_dict(),
                "trace": self._calculation_trace,
                "exported_at": datetime.utcnow().isoformat()
            }, f, indent=2)
        logger.info(f"Calculation trace exported to {filepath}")
