#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3 APPLICATION STATE MANAGER
Centralized state management for the entire MUTS system
"""

import threading
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class SystemState(Enum):
    """System operational states"""
    INITIALIZING = "initializing"
    READY = "ready"
    CONNECTING = "connecting"
    TUNING = "tuning"
    DIAGNOSTIC = "diagnostic"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class PerformanceMode(Enum):
    """Performance tuning modes"""
    STOCK = "stock"
    STREET = "street"
    TRACK = "track"
    DRAG = "drag"
    ECO = "eco"
    SAFE = "safe"

@dataclass
class ECUData:
    """Real-time ECU sensor data"""
    engine_rpm: float = 0.0
    boost_psi: float = 0.0
    manifold_pressure: float = 101.3
    ignition_timing: float = 0.0
    afr: float = 14.7
    coolant_temp: float = 90.0
    intake_temp: float = 25.0
    throttle_position: float = 0.0
    vehicle_speed: float = 0.0
    knock_retard: float = 0.0
    injector_duty: float = 0.0
    maf_voltage: float = 0.0
    map_voltage: float = 0.0
    o2_voltage: float = 0.0
    fuel_pressure: float = 0.0
    oil_pressure: float = 0.0
    egt_temp: float = 0.0
    timestamp: float = field(default_factory=time.time)

@dataclass
class TuningParameters:
    """Active tuning parameters"""
    boost_target: float = 15.0
    timing_base: float = 10.0
    fuel_base: float = 0.0
    vvt_target: float = 0.0
    boost_limit: float = 20.0
    timing_limit: float = 25.0
    fuel_limit: float = 20.0
    afr_target: float = 11.5
    boost_cut: float = 22.0
    rev_limit: float = 6500
    speed_limit: float = 180
    performance_mode: PerformanceMode = PerformanceMode.STOCK

@dataclass
class SystemStatus:
    """System health and status"""
    can_connected: bool = False
    ecu_connected: bool = False
    security_unlocked: bool = False
    tuning_active: bool = False
    data_logging: bool = True
    safety_override: bool = False
    error_count: int = 0
    last_error: Optional[str] = None
    uptime: float = field(default_factory=time.time)

class AppStateManager:
    """
    CENTRALIZED APPLICATION STATE MANAGER
    Manages all system state, data, and configuration
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._state = SystemState.INITIALIZING
        self._ecu_data = ECUData()
        self._tuning_params = TuningParameters()
        self._system_status = SystemStatus()
        self._config = {}
        self._callbacks = {}
        self._data_history = []
        self._max_history = 1000
        
        # Initialize system
        self._initialize_state()
        
    def _initialize_state(self):
        """Initialize the application state"""
        try:
            logger.info("Initializing application state manager...")
            
            # Load configuration
            self._load_configuration()
            
            # Set initial state
            self.set_state(SystemState.READY)
            
            logger.info("Application state manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application state: {e}")
            self.set_state(SystemState.ERROR)
            self.set_error(f"Initialization failed: {e}")
    
    def _load_configuration(self):
        """Load system configuration"""
        try:
            # Default configuration
            self._config = {
                'can_interface': 'can0',
                'can_bitrate': 500000,
                'update_interval': 0.1,
                'log_level': 'INFO',
                'safety_limits': {
                    'max_boost': 25.0,
                    'max_timing': 30.0,
                    'max_egt': 950,
                    'min_afr': 11.0,
                    'max_rpm': 7000
                },
                'performance_modes': {
                    'stock': {'boost': 15.0, 'timing': 10.0},
                    'street': {'boost': 18.0, 'timing': 15.0},
                    'track': {'boost': 22.0, 'timing': 20.0},
                    'drag': {'boost': 24.0, 'timing': 25.0},
                    'eco': {'boost': 14.0, 'timing': 8.0},
                    'safe': {'boost': 16.0, 'timing': 12.0}
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def set_state(self, new_state: SystemState):
        """Set system state"""
        with self._lock:
            old_state = self._state
            self._state = new_state
            logger.info(f"State changed: {old_state.value} -> {new_state.value}")
            self._notify_callbacks('state_change', {'old': old_state, 'new': new_state})
    
    def get_state(self) -> SystemState:
        """Get current system state"""
        with self._lock:
            return self._state
    
    def update_ecu_data(self, **kwargs):
        """Update ECU sensor data"""
        with self._lock:
            try:
                # Update provided fields
                for key, value in kwargs.items():
                    if hasattr(self._ecu_data, key):
                        setattr(self._ecu_data, key, value)
                
                # Update timestamp
                self._ecu_data.timestamp = time.time()
                
                # Add to history
                self._add_to_history('ecu_data', self._ecu_data)
                
                # Notify callbacks
                self._notify_callbacks('ecu_data_update', self._ecu_data)
                
            except Exception as e:
                logger.error(f"Failed to update ECU data: {e}")
                self.set_error(f"ECU data update failed: {e}")
    
    def get_ecu_data(self) -> ECUData:
        """Get current ECU data"""
        with self._lock:
            return self._ecu_data
    
    def update_tuning_parameters(self, **kwargs):
        """Update tuning parameters"""
        with self._lock:
            try:
                # Update provided fields
                for key, value in kwargs.items():
                    if hasattr(self._tuning_params, key):
                        setattr(self._tuning_params, key, value)
                
                # Add to history
                self._add_to_history('tuning_params', self._tuning_params)
                
                # Notify callbacks
                self._notify_callbacks('tuning_update', self._tuning_params)
                
            except Exception as e:
                logger.error(f"Failed to update tuning parameters: {e}")
                self.set_error(f"Tuning parameter update failed: {e}")
    
    def get_tuning_parameters(self) -> TuningParameters:
        """Get current tuning parameters"""
        with self._lock:
            return self._tuning_params
    
    def update_system_status(self, **kwargs):
        """Update system status"""
        with self._lock:
            try:
                # Update provided fields
                for key, value in kwargs.items():
                    if hasattr(self._system_status, key):
                        setattr(self._system_status, key, value)
                
                # Notify callbacks
                self._notify_callbacks('status_update', self._system_status)
                
            except Exception as e:
                logger.error(f"Failed to update system status: {e}")
                self.set_error(f"System status update failed: {e}")
    
    def get_system_status(self) -> SystemStatus:
        """Get current system status"""
        with self._lock:
            return self._system_status
    
    def set_performance_mode(self, mode: PerformanceMode):
        """Set performance mode"""
        with self._lock:
            try:
                if mode.value in self._config['performance_modes']:
                    mode_config = self._config['performance_modes'][mode.value]
                    self._tuning_params.performance_mode = mode
                    self._tuning_params.boost_target = mode_config['boost']
                    self._tuning_params.timing_base = mode_config['timing']
                    
                    logger.info(f"Performance mode set to: {mode.value}")
                    self._notify_callbacks('performance_mode_change', mode)
                else:
                    raise ValueError(f"Unsupported performance mode: {mode}")
                    
            except Exception as e:
                logger.error(f"Failed to set performance mode: {e}")
                self.set_error(f"Performance mode change failed: {e}")
    
    def set_error(self, error_message: str):
        """Set system error"""
        with self._lock:
            self._system_status.last_error = error_message
            self._system_status.error_count += 1
            logger.error(f"System error: {error_message}")
            self._notify_callbacks('error', error_message)
    
    def clear_error(self):
        """Clear system error"""
        with self._lock:
            self._system_status.last_error = None
            logger.info("System error cleared")
            self._notify_callbacks('error_cleared', None)
    
    def register_callback(self, event: str, callback: Callable):
        """Register event callback"""
        with self._lock:
            if event not in self._callbacks:
                self._callbacks[event] = []
            self._callbacks[event].append(callback)
            logger.debug(f"Registered callback for event: {event}")
    
    def unregister_callback(self, event: str, callback: Callable):
        """Unregister event callback"""
        with self._lock:
            if event in self._callbacks:
                try:
                    self._callbacks[event].remove(callback)
                    logger.debug(f"Unregistered callback for event: {event}")
                except ValueError:
                    pass
    
    def _notify_callbacks(self, event: str, data: Any):
        """Notify registered callbacks"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Callback error for event {event}: {e}")
    
    def _add_to_history(self, data_type: str, data: Any):
        """Add data to history"""
        try:
            history_entry = {
                'type': data_type,
                'data': data,
                'timestamp': time.time()
            }
            self._data_history.append(history_entry)
            
            # Limit history size
            if len(self._data_history) > self._max_history:
                self._data_history.pop(0)
                
        except Exception as e:
            logger.error(f"Failed to add to history: {e}")
    
    def get_history(self, data_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get data history"""
        with self._lock:
            if data_type:
                history = [h for h in self._data_history if h['type'] == data_type]
            else:
                history = self._data_history.copy()
            
            return history[-limit:] if limit > 0 else history
    
    def get_config(self, key: Optional[str] = None) -> Any:
        """Get configuration value"""
        with self._lock:
            if key:
                return self._config.get(key)
            return self._config.copy()
    
    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        with self._lock:
            self._config[key] = value
            logger.info(f"Configuration updated: {key} = {value}")
    
    def export_state(self) -> Dict:
        """Export complete system state"""
        with self._lock:
            return {
                'state': self._state.value,
                'ecu_data': self._ecu_data.__dict__,
                'tuning_params': self._tuning_params.__dict__,
                'system_status': self._system_status.__dict__,
                'config': self._config,
                'timestamp': time.time()
            }
    
    def import_state(self, state_data: Dict):
        """Import system state"""
        with self._lock:
            try:
                if 'state' in state_data:
                    self._state = SystemState(state_data['state'])
                
                if 'ecu_data' in state_data:
                    for key, value in state_data['ecu_data'].items():
                        if hasattr(self._ecu_data, key):
                            setattr(self._ecu_data, key, value)
                
                if 'tuning_params' in state_data:
                    for key, value in state_data['tuning_params'].items():
                        if hasattr(self._tuning_params, key):
                            setattr(self._tuning_params, key, value)
                
                if 'system_status' in state_data:
                    for key, value in state_data['system_status'].items():
                        if hasattr(self._system_status, key):
                            setattr(self._system_status, key, value)
                
                if 'config' in state_data:
                    self._config.update(state_data['config'])
                
                logger.info("System state imported successfully")
                
            except Exception as e:
                logger.error(f"Failed to import state: {e}")
                raise

# Global instance
app_state = AppStateManager()

def get_app_state() -> AppStateManager:
    """Get global application state instance"""
    return app_state
