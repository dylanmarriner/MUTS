"""
MazdaCANEngine - Advanced CAN communication module for Mazdaspeed 3.

This module provides Mazda-specific CAN communication functionality,
extending the base OBD-II capabilities with Mazda-specific protocols
and features.
"""

import time
import logging
import struct
import threading
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from dataclasses import dataclass
from enum import Enum, IntEnum, auto

from MazdaOBDService import OBDService, OBDProtocol, OBDServiceError

# Configure logging
logger = logging.getLogger('MazdaCANEngine')

class MazdaCANError(OBDServiceError):
    """Base exception for Mazda CAN communication errors."""
    pass

class CANMessageID(IntEnum):
    """Mazda-specific CAN message IDs."""
    # Engine Control Module (ECM)
    ECM_ENGINE_DATA = 0x201
    ECM_ENGINE_DATA2 = 0x240
    ECM_ENGINE_DATA3 = 0x280
    ECM_ENGINE_DATA4 = 0x2C0
    
    # Transmission Control Module (TCM)
    TCM_DATA = 0x202
    TCM_DATA2 = 0x212
    
    # Electronic Stability Control (DSC)
    DSC_DATA = 0x215
    DSC_DATA2 = 0x217
    
    # Electric Power Steering (EPS)
    EPS_DATA = 0x220
    
    # Instrument Cluster (IC)
    IC_DATA = 0x2F0
    IC_DATA2 = 0x2F1
    
    # Body Control Module (BCM)
    BCM_DATA = 0x300
    BCM_DATA2 = 0x301
    
    # Climate Control
    CLIMATE_DATA = 0x440
    
    # Custom Tuning Frames
    TUNING_COMMAND = 0x7E0
    TUNING_RESPONSE = 0x7E8

class MazdaCANEngine:
    """
    Advanced CAN communication handler for Mazdaspeed 3.
    
    This class extends the base OBDService with Mazda-specific
    CAN communication features and protocols.
    """
    
    def __init__(self, obd_service: Optional[OBDService] = None):
        """
        Initialize the Mazda CAN engine.
        
        Args:
            obd_service: Optional pre-configured OBDService instance
        """
        self.obd = obd_service or OBDService()
        self._lock = threading.RLock()
        self._callbacks: Dict[int, List[Callable]] = {}
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._message_buffers: Dict[int, bytearray] = {}
        self._last_message_times: Dict[int, float] = {}
        
        # CAN message handlers
        self._message_handlers = {
            CANMessageID.ECM_ENGINE_DATA: self._handle_engine_data,
            CANMessageID.ECM_ENGINE_DATA2: self._handle_engine_data2,
            CANMessageID.TCM_DATA: self._handle_tcm_data,
            CANMessageID.DSC_DATA: self._handle_dsc_data,
        }
        
        # Current vehicle state
        self.vehicle_state = {
            'rpm': 0.0,
            'speed': 0.0,
            'throttle': 0.0,
            'boost': 0.0,
            'coolant_temp': 0.0,
            'intake_temp': 0.0,
            'maf': 0.0,
            'lambda': 1.0,
            'ignition_timing': 0.0,
            'battery_voltage': 12.0,
            'gear': 'N',
            'tps': 0.0,
            'fuel_pressure': 0.0,
            'oil_pressure': 0.0,
            'oil_temp': 0.0,
            'fuel_level': 0.0,
            'afr': 14.7,
            'wastegate_duty': 0.0,
            'ethanol_percent': 0.0,
            'knock_count': 0,
            'knock_retard': 0.0,
            'current_gear': 0,
            'target_gear': 0,
            'clutch_switch': False,
            'brake_switch': False,
            'cruise_control': False,
            'check_engine_light': False,
            'dsc_active': False,
            'traction_control_active': False,
            'launch_control_active': False,
            'flat_shift_active': False,
            'rolling_anti_lag_active': False,
            'pop_bang_active': False,
            'two_step_active': False,
            'stealth_mode_active': False,
            'last_update': 0.0
        }
    
    def connect(self) -> bool:
        """Connect to the vehicle's CAN bus."""
        if not self.obd.connect():
            return False
            
        # Set CAN protocol if needed
        if self.obd.connection.protocol == OBDProtocol.AUTO:
            # Try ISO 15765-4 CAN (11 bit ID, 500 Kbaud)
            if not self.obd.connection.set_protocol(OBDProtocol.ISO_15765_4_CAN_11B_500K):
                logger.error("Failed to set CAN protocol")
                return False
        
        logger.info("Connected to Mazda CAN bus")
        return True
    
    def disconnect(self) -> None:
        """Disconnect from the vehicle's CAN bus."""
        self.stop_monitoring()
        self.obd.disconnect()
    
    def start_monitoring(self) -> None:
        """Start monitoring CAN bus messages."""
        if self._running:
            return
            
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MazdaCANMonitor"
        )
        self._monitor_thread.start()
        logger.info("Started CAN bus monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring CAN bus messages."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
            self._monitor_thread = None
        logger.info("Stopped CAN bus monitoring")
    
    def register_callback(self, can_id: int, callback: Callable[[int, bytearray], None]) -> None:
        """Register a callback for a specific CAN ID."""
        with self._lock:
            if can_id not in self._callbacks:
                self._callbacks[can_id] = []
            if callback not in self._callbacks[can_id]:
                self._callbacks[can_id].append(callback)
    
    def unregister_callback(self, can_id: int, callback: Callable[[int, bytearray], None]) -> None:
        """Unregister a callback for a specific CAN ID."""
        with self._lock:
            if can_id in self._callbacks and callback in self._callbacks[can_id]:
                self._callbacks[can_id].remove(callback)
                if not self._callbacks[can_id]:
                    del self._callbacks[can_id]
    
    def send_can_message(self, can_id: int, data: bytes, extended: bool = False) -> bool:
        """
        Send a raw CAN message.
        
        Args:
            can_id: CAN message ID
            data: Data bytes (up to 8 bytes)
            extended: Whether to use extended addressing
            
        Returns:
            True if the message was sent successfully
        """
        if not self.obd.connection or not self.obd.connection.is_connected:
            raise MazdaCANError("Not connected to CAN bus")
            
        if len(data) > 8:
            raise ValueError("CAN message data cannot exceed 8 bytes")
            
        # Format the CAN message
        cmd = f"AT SH {can_id:03X}"
        if extended:
            cmd = f"AT SH {can_id:08X}"
            
        # Add data bytes
        cmd += " " + " ".join(f"{b:02X}" for b in data)
        
        # Send the message
        success, _, _ = self.obd.send_command(cmd.encode('ascii'))
        return success
    
    def _monitor_loop(self) -> None:
        """Main CAN bus monitoring loop."""
        try:
            # Send CAN flow control messages to start receiving data
            self.obd.send_command(b"AT CRA 200")
            self.obd.send_command(b"AT FC SH 7E0")
            self.obd.send_command(b"AT FC SD 30 00 00")
            self.obd.send_command(b"AT FC SM 1")
            
            # Main monitoring loop
            while self._running:
                try:
                    # Read raw CAN data
                    success, data, _ = self.obd.send_command(b"AT MA")
                    if not success or not data:
                        time.sleep(0.01)
                        continue
                    
                    # Process the received data
                    self._process_can_data(data)
                    
                except Exception as e:
                    logger.error(f"Error in CAN monitor loop: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.critical(f"Fatal error in CAN monitor loop: {e}")
            self._running = False
    
    def _process_can_data(self, data: bytes) -> None:
        """Process raw CAN data."""
        try:
            # Parse CAN message
            parts = data.strip().split(b' ')
            if len(parts) < 2:
                return
                
            # Extract CAN ID and data
            try:
                can_id = int(parts[0], 16)
                can_data = bytes(int(b, 16) for b in parts[1:1+8])  # Up to 8 data bytes
            except (ValueError, IndexError):
                return
                
            # Update message buffer
            if can_id not in self._message_buffers:
                self._message_buffers[can_id] = bytearray()
            self._message_buffers[can_id] = can_data
            self._last_message_times[can_id] = time.time()
            
            # Call registered callbacks
            with self._lock:
                for callback in self._callbacks.get(can_id, []):
                    try:
                        callback(can_id, can_data)
                    except Exception as e:
                        logger.error(f"Error in CAN callback: {e}")
            
            # Handle known message types
            if can_id in self._message_handlers:
                try:
                    self._message_handlers[can_id](can_id, can_data)
                except Exception as e:
                    logger.error(f"Error handling CAN message 0x{can_id:03X}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing CAN data: {e}")
    
    # --- Message Handlers ---
    
    def _handle_engine_data(self, can_id: int, data: bytes) -> None:
        """Handle ECM engine data messages (0x201)."""
        if len(data) < 8:
            return
            
        # Parse engine data
        self.vehicle_state['rpm'] = ((data[0] << 8) | data[1]) / 4.0
        self.vehicle_state['speed'] = data[2]  # km/h
        self.vehicle_state['throttle'] = (data[3] * 100.0) / 255.0  # %
        self.vehicle_state['coolant_temp'] = data[4] - 40.0  # °C
        self.vehicle_state['intake_temp'] = data[5] - 40.0  # °C
        self.vehicle_state['maf'] = ((data[6] << 8) | data[7]) / 100.0  # g/s
        
        # Update last update time
        self.vehicle_state['last_update'] = time.time()
    
    def _handle_engine_data2(self, can_id: int, data: bytes) -> None:
        """Handle secondary ECM engine data messages (0x240)."""
        if len(data) < 8:
            return
            
        # Parse additional engine data
        self.vehicle_state['ignition_timing'] = (data[0] / 2.0) - 64.0  # degrees
        self.vehicle_state['battery_voltage'] = data[1] / 10.0  # volts
        self.vehicle_state['afr'] = data[2] / 10.0  # AFR
        self.vehicle_state['boost'] = ((data[3] - 128) * 0.019) * 14.5038  # PSI (converted from bar)
        self.vehicle_state['wastegate_duty'] = data[4] * 0.39215686  # %
        self.vehicle_state['ethanol_percent'] = data[5]  # %
        self.vehicle_state['knock_count'] = data[6]
        self.vehicle_state['knock_retard'] = data[7] * 0.5  # degrees
    
    def _handle_tcm_data(self, can_id: int, data: bytes) -> None:
        """Handle TCM data messages (0x202)."""
        if len(data) < 4:
            return
            
        # Parse transmission data
        self.vehicle_state['current_gear'] = data[0] & 0x0F
        self.vehicle_state['target_gear'] = (data[0] >> 4) & 0x0F
        self.vehicle_state['clutch_switch'] = bool(data[1] & 0x01)
        self.vehicle_state['brake_switch'] = bool(data[1] & 0x02)
        self.vehicle_state['cruise_control'] = bool(data[1] & 0x04)
        
        # Map gear number to display string
        gear_map = {0: 'N', 1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 15: 'R'}
        self.vehicle_state['gear'] = gear_map.get(self.vehicle_state['current_gear'], '?')
    
    def _handle_dsc_data(self, can_id: int, data: bytes) -> None:
        """Handle DSC (stability control) data messages (0x215)."""
        if len(data) < 2:
            return
            
        # Parse DSC status
        self.vehicle_state['dsc_active'] = bool(data[0] & 0x01)
        self.vehicle_state['traction_control_active'] = bool(data[0] & 0x02)
    
    # --- High-Level Methods ---
    
    def get_vehicle_state(self) -> dict:
        """Get the current vehicle state."""
        with self._lock:
            return self.vehicle_state.copy()
    
    def get_engine_parameters(self) -> dict:
        """Get current engine parameters."""
        with self._lock:
            return {
                'rpm': self.vehicle_state['rpm'],
                'throttle': self.vehicle_state['throttle'],
                'boost': self.vehicle_state['boost'],
                'coolant_temp': self.vehicle_state['coolant_temp'],
                'intake_temp': self.vehicle_state['intake_temp'],
                'maf': self.vehicle_state['maf'],
                'afr': self.vehicle_state['afr'],
                'ignition_timing': self.vehicle_state['ignition_timing'],
                'knock_retard': self.vehicle_state['knock_retard'],
                'knock_count': self.vehicle_state['knock_count'],
                'ethanol_percent': self.vehicle_state['ethanol_percent'],
                'battery_voltage': self.vehicle_state['battery_voltage']
            }
    
    def get_transmission_parameters(self) -> dict:
        """Get current transmission parameters."""
        with self._lock:
            return {
                'gear': self.vehicle_state['gear'],
                'current_gear': self.vehicle_state['current_gear'],
                'target_gear': self.vehicle_state['target_gear'],
                'clutch_switch': self.vehicle_state['clutch_switch'],
                'brake_switch': self.vehicle_state['brake_switch']
            }
    
    def get_system_status(self) -> dict:
        """Get system status indicators."""
        with self._lock:
            return {
                'dsc_active': self.vehicle_state['dsc_active'],
                'traction_control_active': self.vehicle_state['traction_control_active'],
                'cruise_control': self.vehicle_state['cruise_control'],
                'check_engine_light': self.vehicle_state['check_engine_light']
            }
    
    # --- Feature Control Methods ---
    
    def enable_launch_control(self, rpm_limit: int = 4000) -> bool:
        """Enable launch control with the specified RPM limit."""
        if not 2000 <= rpm_limit <= 8000:
            raise ValueError("RPM limit must be between 2000 and 8000")
            
        # Send launch control enable command
        data = struct.pack('>BH', 0x01, rpm_limit) + bytes(5)
        return self.send_can_message(CANMessageID.TUNING_COMMAND, data)
    
    def disable_launch_control(self) -> bool:
        """Disable launch control."""
        data = bytes([0x81]) + bytes(7)
        return self.send_can_message(CANMessageID.TUNING_COMMAND, data)
    
    def enable_flat_shift(self, rpm_limit: int = 7000) -> bool:
        """Enable flat-shift with the specified RPM limit."""
        if not 4000 <= rpm_limit <= 8000:
            raise ValueError("RPM limit must be between 4000 and 8000")
            
        data = struct.pack('>BH', 0x02, rpm_limit) + bytes(5)
        return self.send_can_message(CANMessageID.TUNING_COMMAND, data)
    
    def disable_flat_shift(self) -> bool:
        """Disable flat-shift."""
        data = bytes([0x82]) + bytes(7)
        return self.send_can_message(CANMessageID.TUNING_COMMAND, data)
    
    def enable_rolling_anti_lag(self, enable: bool = True) -> bool:
        """Enable or disable rolling anti-lag."""
        data = bytes([0x03, 0x01 if enable else 0x00]) + bytes(6)
        return self.send_can_message(CANMessageID.TUNING_COMMAND, data)
    
    def enable_pop_bang(self, enable: bool = True) -> bool:
        """Enable or disable pop & bang (overrun) feature."""
        data = bytes([0x04, 0x01 if enable else 0x00]) + bytes(6)
        return self.send_can_message(CANMessageID.TUNING_COMMAND, data)
    
    def enable_two_step(self, launch_rpm: int = 4000, burnout_rpm: int = 5500) -> bool:
        """Enable two-step rev limiter with specified RPM limits."""
        if not 2000 <= launch_rpm <= 8000 or not 2000 <= burnout_rpm <= 8000:
            raise ValueError("RPM limits must be between 2000 and 8000")
            
        data = struct.pack('>BHH', 0x05, launch_rpm, burnout_rpm) + bytes(3)
        return self.send_can_message(CANMessageID.TUNING_COMMAND, data)
    
    def disable_two_step(self) -> bool:
        """Disable two-step rev limiter."""
        data = bytes([0x85]) + bytes(7)
        return self.send_can_message(CANMessageID.TUNING_COMMAND, data)
    
    def enable_stealth_mode(self, enable: bool = True) -> bool:
        """Enable or disable stealth mode (quiet exhaust)."""
        data = bytes([0x06, 0x01 if enable else 0x00]) + bytes(6)
        return self.send_can_message(CANMessageID.TUNING_COMMAND, data)

# Example usage
if __name__ == "__main__":
    import time
    import sys
    
    def can_message_callback(can_id: int, data: bytes) -> None:
        """Example callback for CAN messages."""
        print(f"CAN ID: 0x{can_id:03X}, Data: {data.hex(' ')}")
    
    try:
        # Create and connect to the vehicle
        print("Initializing Mazda CAN Engine...")
        mazda = MazdaCANEngine()
        
        print("Connecting to vehicle...")
        if not mazda.connect():
            print("Failed to connect to vehicle")
            sys.exit(1)
            
        # Register for CAN messages
        mazda.register_callback(CANMessageID.ECM_ENGINE_DATA, can_message_callback)
        mazda.register_callback(CANMessageID.ECM_ENGINE_DATA2, can_message_callback)
        
        # Start monitoring
        print("Starting CAN bus monitoring...")
        mazda.start_monitoring()
        
        # Main loop
        print("Monitoring vehicle data (press Ctrl+C to stop)...")
        while True:
            # Get and display vehicle state
            state = mazda.get_vehicle_state()
            print(f"\rRPM: {state['rpm']:6.0f} | Speed: {state['speed']:3.0f} km/h | "
                  f"Gear: {state['gear']} | Boost: {state['boost']:5.1f} psi | "
                  f"Throttle: {state['throttle']:3.0f}% | AFR: {state['afr']:4.1f}", end="")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'mazda' in locals():
            mazda.stop_monitoring()
            mazda.disconnect()
        print("Disconnected from vehicle")
