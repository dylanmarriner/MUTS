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
    
    def start_adaptive_tuning(self):
        """Start adaptive tuning based on monitored parameters"""
        if not self.is_monitoring:
            self.logger.warning("Must start monitoring before adaptive tuning")
            return
        
        self.is_adaptive_tuning = True
        self.logger.info("Adaptive tuning enabled")
    
    def stop_adaptive_tuning(self):
        """Stop adaptive tuning"""
        self.is_adaptive_tuning = False
        self.logger.info("Adaptive tuning disabled")
    
    def _monitoring_loop(self, update_interval: float):
        """Main monitoring loop"""
        while not self._stop_monitor:
            try:
                # Read all monitored parameters
                sensor_data = self._read_sensors()
                
                if sensor_data:
                    # Process data for tuning decisions
                    if self.is_adaptive_tuning:
                        self._process_adaptive_tuning(sensor_data)
                
                time.sleep(update_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(1.0)
    
    def _read_sensors(self) -> Optional[Dict[str, float]]:
        """Read all monitored sensor values"""
        data = {}
        
        for pid in self.monitored_pids:
            value = self.ecu.read_live_data(pid)
            if value is not None:
                data[pid] = value
        
        return data if data else None
    
    def _process_adaptive_tuning(self, sensor_data: Dict[str, float]):
        """Process sensor data and make tuning adjustments"""
        rpm = sensor_data.get(0x0C, 0)
        boost = sensor_data.get(0x223365, 0)
        knock = sensor_data.get(0x223456, 0)
        
        # Only tune at operating temperature
        coolant_temp = sensor_data.get(0x05, -40)
        if coolant_temp < 70:
            return
        
        # Check for knock and retard timing if needed
        if knock < self.knock_threshold:
            self._adjust_for_knock(rpm, knock)
        
        # Check boost control
        if boost > 0:  # Only in boost
            self._adjust_boost_control(rpm, boost)
    
    def _adjust_for_knock(self, rpm: float, knock: float):
        """Adjust ignition timing based on knock"""
        try:
            # Find appropriate ignition map cell
            rpm_index = self._find_rpm_index(rpm)
            load_index = self._find_load_index(0.8)  # Assume high load for knock
            
            if rpm_index is not None and load_index is not None:
                # Retard timing by knock amount + safety margin
                adjustment = abs(knock) + 1.0
                
                # Apply adjustment to ignition map
                self._make_ram_adjustment(
                    'ignition_primary',
                    rpm_index,
                    load_index,
                    -adjustment,
                    f"Knock correction: {knock:.1f}°"
                )
        
        except Exception as e:
            self.logger.error(f"Knock adjustment failed: {e}")
    
    def _adjust_boost_control(self, rpm: float, boost: float):
        """Adjust boost control based on performance"""
        try:
            # Simple boost limiting logic
            if boost > 20.0:  # Over boost
                rpm_index = self._find_rpm_index(rpm)
                load_index = self._find_load_index(1.0)
                
                if rpm_index is not None and load_index is not None:
                    # Reduce wastegate duty to lower boost
                    self._make_ram_adjustment(
                        'boost_wg_duty',
                        rpm_index,
                        load_index,
                        -5.0,
                        f"Boost limiting: {boost:.1f} psi"
                    )
        
        except Exception as e:
            self.logger.error(f"Boost adjustment failed: {e}")
    
    def _find_rpm_index(self, rpm: float) -> Optional[int]:
        """Find RPM index in map arrays"""
        rpm_ranges = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 
                     4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000]
        
        for i, rpm_point in enumerate(rpm_ranges):
            if rpm <= rpm_point:
                return i
        
        return len(rpm_ranges) - 1
    
    def _find_load_index(self, load: float) -> Optional[int]:
        """Find load index in map arrays"""
        load_ranges = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 
                      0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        
        for i, load_point in enumerate(load_ranges):
            if load <= load_point:
                return i
        
        return len(load_ranges) - 1
    
    def _make_ram_adjustment(self, map_name: str, x: int, y: int, 
                           adjustment: float, reason: str):
        """
        Make a live RAM adjustment to ECU
        
        Args:
            map_name: Name of map to adjust
            x: X index in map
            y: Y index in map
            adjustment: Adjustment amount
            reason: Reason for adjustment
        """
        try:
            map_def = self.map_manager.get_map(map_name)
            if not map_def:
                return
            
            # Calculate RAM address for map cell
            cell_address = map_def.address + (y * 16 + x) * 2
            
            # Read current value
            response = self.ecu.read_memory(cell_address, 2)
            if not response.success:
                return
            
            current_raw = int.from_bytes(response.data[1:3], 'big')
            current_value = current_raw * map_def.conversion_factor
            
            # Calculate new value
            new_value = current_value + adjustment
            new_value = max(map_def.min_value, min(map_def.max_value, new_value))
            new_raw = int(new_value / map_def.conversion_factor)
            
            # Write new value to RAM
            new_bytes = new_raw.to_bytes(2, 'big')
            write_response = self.ecu.send_request(0x3D, 0x00, 
                                                cell_address.to_bytes(3, 'big') + 
                                                bytes([2]) + new_bytes)
            
            if write_response.success:
                # Record adjustment
                adjustment_record = TuningAdjustment(
                    timestamp=time.time(),
                    map_name=map_name,
                    x_index=x,
                    y_index=y,
                    old_value=current_value,
                    new_value=new_value,
                    reason=reason
                )
                self.adjustment_history.append(adjustment_record)
                
                self.logger.debug(f"RAM adjustment: {map_name}[{x},{y}] "
                                f"{current_value:.2f} -> {new_value:.2f} ({reason})")
        
        except Exception as e:
            self.logger.error(f"RAM adjustment failed: {e}")
    
    def get_adjustment_history(self, limit: int = 100) -> List[TuningAdjustment]:
        """Get recent adjustment history"""
        return self.adjustment_history[-limit:]
    
    def clear_adjustment_history(self):
        """Clear adjustment history"""
        self.adjustment_history.clear()
        self.logger.info("Adjustment history cleared")
    
    def save_tuning_session(self, filename: str):
        """Save current tuning session to file"""
        try:
            import json
            
            session_data = {
                'timestamp': time.time(),
                'adjustments': [
                    {
                        'timestamp': adj.timestamp,
                        'map_name': adj.map_name,
                        'x_index': adj.x_index,
                        'y_index': adj.y_index,
                        'old_value': adj.old_value,
                        'new_value': adj.new_value,
                        'reason': adj.reason
                    }
                    for adj in self.adjustment_history
                ],
                'tuning_parameters': {
                    'knock_threshold': self.knock_threshold,
                    'boost_overshoot_threshold': self.boost_overshoot_threshold,
                    'afr_safe_range': self.afr_safe_range
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            self.logger.info(f"Tuning session saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save tuning session: {e}")
    
    def load_tuning_session(self, filename: str):
        """Load tuning session from file"""
        try:
            import json
            
            with open(filename, 'r') as f:
                session_data = json.load(f)
            
            # Load adjustment history
            self.adjustment_history = []
            for adj_data in session_data.get('adjustments', []):
                adjustment = TuningAdjustment(**adj_data)
                self.adjustment_history.append(adjustment)
            
            # Load tuning parameters
            params = session_data.get('tuning_parameters', {})
            self.knock_threshold = params.get('knock_threshold', -2.0)
            self.boost_overshoot_threshold = params.get('boost_overshoot_threshold', 1.0)
            self.afr_safe_range = tuple(params.get('afr_safe_range', (10.8, 12.2)))
            
            self.logger.info(f"Tuning session loaded from {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to load tuning session: {e}")
