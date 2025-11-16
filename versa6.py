#!/usr/bin/env python3
"""
Real-time Tuning Module - Live map adjustment and adaptive tuning
Reverse engineered from VersaTuner's real-time tuning capabilities
"""

import threading
import time
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from ..core.ecu_communication import ECUCommunicator
from .map_definitions import MapDefinitionManager
from ..utils.logger import VersaLogger

@dataclass
class TuningAdjustment:
    """Single tuning adjustment record"""
    timestamp: float
    map_name: str
    x_index: int
    y_index: int
    old_value: float
    new_value: float
    reason: str

class RealTimeTuner:
    """
    Real-time tuning controller with adaptive learning
    Monitors engine parameters and makes live adjustments to optimize performance
    """
    
    def __init__(self, ecu_communicator: ECUCommunicator):
        """
        Initialize Real-time Tuner
        
        Args:
            ecu_communicator: ECUCommunicator instance for live data
        """
        self.ecu = ecu_communicator
        self.map_manager = MapDefinitionManager()
        self.logger = VersaLogger(__name__)
        
        # Tuning state
        self.is_monitoring = False
        self.is_adaptive_tuning = False
        self.adjustment_history: List[TuningAdjustment] = []
        
        # Monitoring parameters
        self.monitored_pids = [
            0x0C,  # RPM
            0x0D,  # Vehicle Speed
            0x11,  # Throttle Position
            0x05,  # Coolant Temp
            0x0F,  # Intake Air Temp
            0x223365,  # Boost Pressure
            0x223456,  # Knock Correction
        ]
        
        # Adaptive tuning parameters
        self.knock_threshold = -2.0  # Degrees of retard before adjustment
        self.boost_overshoot_threshold = 1.0  # PSI over target
        self.afr_safe_range = (10.8, 12.2)  # Safe AFR range
        
        # Threading
        self._monitor_thread = None
        self._stop_monitor = False
    
    def start_monitoring(self, update_interval: float = 0.1):
        """
        Start real-time monitoring of engine parameters
        
        Args:
            update_interval: Time between updates in seconds
        """
        if self.is_monitoring:
            self.logger.warning("Monitoring already active")
            return
        
        self.is_monitoring = True
        self._stop_monitor = False
        
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(update_interval,)
        )
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        self.logger.info("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        self._stop_monitor = True
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
        
        self.logger.info("Real-time monitoring stopped")
    
    def _monitoring_loop(self, update_interval: float):
        """Main monitoring loop"""
        while not self._stop_monitor:
            try:
                # Read current engine parameters
                current_data = self._read_engine_parameters()
                
                # Perform adaptive tuning if enabled
                if self.is_adaptive_tuning:
                    self._perform_adaptive_adjustments(current_data)
                
                # Log data for analysis
                self._log_monitoring_data(current_data)
                
                time.sleep(update_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(1.0)
    
    def _read_engine_parameters(self) -> Dict[str, float]:
        """Read current engine parameters from ECU"""
        data = {}
        
        for pid in self.monitored_pids:
            value = self.ecu.read_live_data(pid)
            pid_name = self._get_pid_name(pid)
            data[pid_name] = value
        
        return data
    
    def _get_pid_name(self, pid: int) -> str:
        """Get human-readable name for PID"""
        pid_names = {
            0x0C: 'rpm',
            0x0D: 'speed',
            0x11: 'throttle',
            0x05: 'coolant_temp',
            0x0F: 'intake_temp',
            0x223365: 'boost',
            0x223456: 'knock_correction'
        }
        return pid_names.get(pid, f'pid_{pid:04X}')
    
    def _perform_adaptive_adjustments(self, current_data: Dict[str, float]):
        """Perform adaptive tuning adjustments based on current conditions"""
        # Check for knock and adjust timing
        if (current_data.get('knock_correction', 0) < self.knock_threshold and
            current_data.get('throttle', 0) > 80):
            self._adjust_for_knock(current_data)
        
        # Check boost control
        if current_data.get('boost', 0) > 20.0:  # High boost condition
            self._adjust_boost_control(current_data)
        
        # Check for lean condition
        afr = current_data.get('commanded_afr', 14.7)
        if not self.afr_safe_range[0] <= afr <= self.afr_safe_range[1]:
            self._adjust_fueling(current_data)
    
    def _adjust_for_knock(self, current_data: Dict[str, float]):
        """Adjust ignition timing in response to knock"""
        knock_amount = current_data.get('knock_correction', 0)
        rpm = current_data.get('rpm', 0)
        load = current_data.get('throttle', 0) / 100.0
        
        # Calculate timing reduction (more reduction for severe knock)
        timing_reduction = abs(knock_amount) * 0.5
        
        self.logger.warning(
            f"Knock detected: {knock_amount:.1f}° retard at {rpm} RPM. "
            f"Reducing timing by {timing_reduction:.1f}°"
        )
        
        # In a real implementation, this would modify the active maps
        # For now, we just log the recommended adjustment
        adjustment = TuningAdjustment(
            timestamp=time.time(),
            map_name='ignition_primary',
            x_index=self._rpm_to_index(rpm),
            y_index=self._load_to_index(load),
            old_value=0.0,  # Would be actual current value
            new_value=-timing_reduction,  # Reduction amount
            reason=f"Knock correction: {knock_amount:.1f}° retard"
        )
        
        self.adjustment_history.append(adjustment)
    
    def _adjust_boost_control(self, current_data: Dict[str, float]):
        """Adjust boost control for overboost conditions"""
        boost = current_data.get('boost', 0)
        target_boost = 18.0  # Would come from boost target map
        
        if boost > target_boost + self.boost_overshoot_threshold:
            boost_reduction = (boost - target_boost) * 0.1
            
            self.logger.warning(
                f"Overboost condition: {boost:.1f} PSI (target: {target_boost} PSI). "
                f"Reducing WGDC by {boost_reduction:.1f}%"
            )
    
    def _adjust_fueling(self, current_data: Dict[str, float]):
        """Adjust fueling for AFR outside safe range"""
        afr = current_data.get('commanded_afr', 14.7)
        
        if afr > self.afr_safe_range[1]:  # Too lean
            fuel_increase = (afr - self.afr_safe_range[1]) * 0.1
            
            self.logger.warning(
                f"Lean condition: AFR {afr:.1f}. "
                f"Increasing fuel by {fuel_increase:.2f} lambda"
            )
        
        elif afr < self.afr_safe_range[0]:  # Too rich
            fuel_decrease = (self.afr_safe_range[0] - afr) * 0.1
            
            self.logger.warning(
                f"Rich condition: AFR {afr:.1f}. "
                f"Decreasing fuel by {fuel_decrease:.2f} lambda"
            )
    
    def _rpm_to_index(self, rpm: float) -> int:
        """Convert RPM value to map index"""
        rpm_ranges = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 
                      4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000]
        
        for i, range_rpm in enumerate(rpm_ranges):
            if rpm <= range_rpm:
                return i
        
        return len(rpm_ranges) - 1
    
    def _load_to_index(self, load: float) -> int:
        """Convert load value to map index"""
        load_ranges = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 
                       0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        
        for i, range_load in enumerate(load_ranges):
            if load <= range_load:
                return i
        
        return len(load_ranges) - 1
    
    def _log_monitoring_data(self, data: Dict[str, float]):
        """Log monitoring data for analysis"""
        # In production, this would write to a log file or database
        if data.get('rpm', 0) > 3000 and data.get('throttle', 0) > 50:
            self.logger.debug(
                f"High load: {data.get('rpm', 0)} RPM, "
                f"{data.get('throttle', 0):.1f}% throttle, "
                f"{data.get('boost', 0):.1f} PSI, "
                f"{data.get('knock_correction', 0):.1f}° knock correction"
            )
    
    def enable_adaptive_tuning(self):
        """Enable adaptive tuning mode"""
        self.is_adaptive_tuning = True
        self.logger.info("Adaptive tuning enabled")
    
    def disable_adaptive_tuning(self):
        """Disable adaptive tuning mode"""
        self.is_adaptive_tuning = False
        self.logger.info("Adaptive tuning disabled")
    
    def get_tuning_history(self) -> List[TuningAdjustment]:
        """Get history of all tuning adjustments"""
        return self.adjustment_history.copy()
    
    def clear_tuning_history(self):
        """Clear tuning adjustment history"""
        self.adjustment_history.clear()
        self.logger.info("Tuning history cleared")
    
    def generate_tuning_report(self) -> Dict[str, Any]:
        """Generate tuning performance report"""
        report = {
            'monitoring_duration': self._get_monitoring_duration(),
            'total_adjustments': len(self.adjustment_history),
            'knock_events': self._count_knock_events(),
            'boost_events': self._count_boost_events(),
            'recent_adjustments': self._get_recent_adjustments(10)
        }
        
        return report
    
    def _get_monitoring_duration(self) -> float:
        """Calculate total monitoring duration"""
        if not self.adjustment_history:
            return 0.0
        
        first_time = self.adjustment_history[0].timestamp
        last_time = self.adjustment_history[-1].timestamp
        return last_time - first_time
    
    def _count_knock_events(self) -> int:
        """Count number of knock-related adjustments"""
        return len([adj for adj in self.adjustment_history if 'knock' in adj.reason.lower()])
    
    def _count_boost_events(self) -> int:
        """Count number of boost-related adjustments"""
        return len([adj for adj in self.adjustment_history if 'boost' in adj.reason.lower()])
    
    def _get_recent_adjustments(self, count: int) -> List[TuningAdjustment]:
        """Get most recent tuning adjustments"""
        return self.adjustment_history[-count:] if self.adjustment_history else []