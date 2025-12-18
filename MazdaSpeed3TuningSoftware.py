"""
MazdaSpeed3TuningSoftware - Core tuning software for Mazdaspeed 3 vehicles.

This module integrates all the components of the Mazda Universal Tuning System (MUTS)
to provide a complete tuning solution for Mazdaspeed 3 vehicles.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

# Import core components
from MazdaOBDService import OBDService, OBDProtocol
from MazdaCANEngine import MazdaCANEngine, CANMessageID
from MazdaSecurityCore import SecurityAlgorithm, SecurityLevel, SecurityCredentials, MazdaSecurityCore

# Configure logging
logger = logging.getLogger('MazdaSpeed3Tuning')

class TuningMode(Enum):
    """Available tuning modes."""
    STREET = "Street"
    TRACK = "Track"
    ECONOMY = "Economy"
    CUSTOM = "Custom"

class TuningParameter(Enum):
    """Tunable parameters."""
    BOOST_TARGET = "boost_target"
    FUEL_PRESSURE = "fuel_pressure"
    IGNITION_TIMING = "ignition_timing"
    FUEL_TABLE = "fuel_table"
    TORQUE_LIMIT = "torque_limit"
    REV_LIMIT = "rev_limit"
    SPEED_LIMIT = "speed_limit"
    THROTTLE_MAPPING = "throttle_mapping"
    POP_BANG_ENABLED = "pop_bang_enabled"
    LAUNCH_CONTROL_ENABLED = "launch_control_enabled"
    FLAT_SHIFT_ENABLED = "flat_shift_enabled"

@dataclass
class TuneProfile:
    """Container for tuning parameters."""
    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_read_only: bool = False
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    
    def update_parameter(self, param: TuningParameter, value: Any) -> None:
        """Update a tuning parameter."""
        if self.is_read_only:
            raise ValueError("Cannot modify a read-only tune profile")
        self.parameters[param.value] = value
        self.modified_at = time.time()
    
    def get_parameter(self, param: TuningParameter, default: Any = None) -> Any:
        """Get a tuning parameter value."""
        return self.parameters.get(param.value, default)

class MazdaSpeed3TuningSoftware:
    """
    Main class for MazdaSpeed 3 tuning software.
    
    Integrates OBD, CAN, and security components to provide
    a complete tuning solution for Mazdaspeed 3 vehicles.
    """
    
    def __init__(self):
        """Initialize the tuning software."""
        # Core components
        self.obd_service = OBDService()
        self.can_engine = MazdaCANEngine(self.obd_service)
        self.security_core = MazdaSecurityCore()
        
        # State
        self.connected = False
        self.vehicle_vin: Optional[str] = None
        self.ecu_serial: Optional[bytes] = None
        self.security_level: SecurityLevel = SecurityLevel.LEVEL_0
        self.current_tune: Optional[TuneProfile] = None
        self.available_tunes: Dict[str, TuneProfile] = {}
        self.active_features: Dict[str, bool] = {
            'launch_control': False,
            'flat_shift': False,
            'pop_bang': False,
            'rolling_anti_lag': False,
            'two_step': False,
            'stealth_mode': False
        }
        
        # Default tuning profiles
        self._initialize_default_profiles()
        
        # Callbacks
        self._callbacks: Dict[str, List[Callable]] = {
            'on_connect': [],
            'on_disconnect': [],
            'on_error': [],
            'on_tune_loaded': [],
            'on_tune_saved': [],
            'on_parameter_changed': [],
            'on_security_level_changed': []
        }
        
        logger.info("MazdaSpeed3TuningSoftware initialized")
    
    def _initialize_default_profiles(self) -> None:
        """Initialize default tuning profiles."""
        # Stock tune
        stock_tune = TuneProfile(
            name="Stock",
            description="Factory default settings",
            is_read_only=True
        )
        stock_tune.parameters = {
            TuningParameter.BOOST_TARGET.value: 15.6,  # psi
            TuningParameter.FUEL_PRESSURE.value: 1600,  # psi
            TuningParameter.IGNITION_TIMING.value: 0.0,  # degrees
            TuningParameter.REV_LIMIT.value: 6750,  # RPM
            TuningParameter.SPEED_LIMIT.value: 250,  # km/h
            TuningParameter.POP_BANG_ENABLED.value: False,
            TuningParameter.LAUNCH_CONTROL_ENABLED.value: False,
            TuningParameter.FLAT_SHIFT_ENABLED.value: False
        }
        
        # Street tune
        street_tune = TuneProfile(
            name="Stage 1",
            description="Mild performance tune for 91-93 octane"
        )
        street_tune.parameters = {
            TuningParameter.BOOST_TARGET.value: 18.0,
            TuningParameter.FUEL_PRESSURE.value: 1700,
            TuningParameter.IGNITION_TIMING.value: 1.5,
            TuningParameter.REV_LIMIT.value: 7000,
            TuningParameter.SPEED_LIMIT.value: 250,
            TuningParameter.POP_BANG_ENABLED.value: False,
            TuningParameter.LAUNCH_CONTROL_ENABLED.value: True,
            TuningParameter.FLAT_SHIFT_ENABLED.value: True
        }
        
        # Track tune
        track_tune = TuneProfile(
            name="Stage 2",
            description="Aggressive tune for 93+ octane and track use"
        )
        track_tune.parameters = {
            TuningParameter.BOOST_TARGET.value: 20.0,
            TuningParameter.FUEL_PRESSURE.value: 1800,
            TuningParameter.IGNITION_TIMING.value: 2.5,
            TuningParameter.REV_LIMIT.value: 7200,
            TuningParameter.SPEED_LIMIT.value: 250,
            TuningParameter.POP_BANG_ENABLED.value: True,
            TuningParameter.LAUNCH_CONTROL_ENABLED.value: True,
            TuningParameter.FLAT_SHIFT_ENABLED.value: True
        }
        
        # Economy tune
        economy_tune = TuneProfile(
            name="Economy",
            description="Optimized for maximum fuel efficiency"
        )
        economy_tune.parameters = {
            TuningParameter.BOOST_TARGET.value: 12.0,
            TuningParameter.FUEL_PRESSURE.value: 1500,
            TuningParameter.IGNITION_TIMING.value: -1.0,
            TuningParameter.REV_LIMIT.value: 6500,
            TuningParameter.SPEED_LIMIT.value: 250,
            TuningParameter.POP_BANG_ENABLED.value: False,
            TuningParameter.LAUNCH_CONTROL_ENABLED.value: False,
            TuningParameter.FLAT_SHIFT_ENABLED.value: False
        }
        
        self.available_tunes = {
            stock_tune.name: stock_tune,
            street_tune.name: street_tune,
            track_tune.name: track_tune,
            economy_tune.name: economy_tune
        }
        
        # Set stock as current tune
        self.current_tune = stock_tune
    
    async def connect(self) -> bool:
        """
        Connect to the vehicle.
        
        Returns:
            bool: True if connection was successful
        """
        try:
            # Initialize OBD service
            if not self.obd_service.connect():
                logger.error("Failed to connect to OBD service")
                return False
            
            # Initialize CAN engine
            if not self.can_engine.connect():
                logger.error("Failed to connect to CAN bus")
                return False
            
            # Start monitoring CAN bus
            self.can_engine.start_monitoring()
            
            # Read VIN and other vehicle info
            self.vehicle_vin = await self._read_vin()
            
            # Initialize security
            await self._initialize_security()
            
            self.connected = True
            self._trigger_callbacks('on_connect')
            logger.info(f"Connected to vehicle: {self.vehicle_vin}")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            self._trigger_callbacks('on_error', str(e))
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the vehicle."""
        try:
            # Stop monitoring
            self.can_engine.stop_monitoring()
            
            # Disconnect OBD
            self.obd_service.disconnect()
            
            # Reset state
            self.connected = False
            self.vehicle_vin = None
            self.security_level = SecurityLevel.LEVEL_0
            
            self._trigger_callbacks('on_disconnect')
            logger.info("Disconnected from vehicle")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            self._trigger_callbacks('on_error', str(e))
    
    async def _read_vin(self) -> str:
        """Read vehicle VIN."""
        try:
            # Try standard OBD-II VIN request
            success, response, _ = self.obd_service.send_command(b"09 02")
            if success and response:
                # Parse VIN from response
                # Format: 49 02 01 [VIN bytes] ...
                vin_bytes = response[3:]  # Skip header and mode
                vin = bytes(vin_bytes).decode('ascii', errors='ignore')
                return vin.strip('\x00')
        except Exception as e:
            logger.warning(f"Failed to read VIN: {e}")
        
        # Fallback to default
        return "UNKNOWN_VIN"
    
    async def _initialize_security(self) -> None:
        """Initialize security access."""
        try:
            # Create security credentials
            credentials = SecurityCredentials(
                algorithm=SecurityAlgorithm.M12R_V3_4,
                level=SecurityLevel.LEVEL_1,
                vin=self.vehicle_vin,
                ecu_serial=self.ecu_serial
            )
            
            # Request seed from ECU
            success, seed = await self._request_seed(credentials.level)
            if not success or not seed:
                logger.warning("Failed to get security seed")
                return
            
            # Compute key
            credentials.seed = seed
            key = self.security_core.compute_key(credentials)
            if not key:
                logger.warning("Failed to compute security key")
                return
            
            # Send key to ECU
            success = await self._send_key(credentials.level, key)
            if success:
                self.security_level = credentials.level
                self._trigger_callbacks('on_security_level_changed', self.security_level)
                logger.info(f"Security level upgraded to {credentials.level}")
            
        except Exception as e:
            logger.error(f"Security initialization failed: {e}")
            self._trigger_callbacks('on_error', f"Security error: {e}")
    
    async def _request_seed(self, level: SecurityLevel) -> Tuple[bool, Optional[bytes]]:
        """Request a security seed from the ECU."""
        try:
            # Format: 0x27 [level] 0x01
            command = bytes([0x27, level.value, 0x01])
            success, response, _ = self.obd_service.send_command(command.hex().encode())
            
            if success and response and len(response) >= 4:
                # Response format: 0x67 [level] [seed...]
                if response[0] == 0x67 and response[1] == level.value:
                    seed = response[2:]
                    return True, seed
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error requesting seed: {e}")
            return False, None
    
    async def _send_key(self, level: SecurityLevel, key: bytes) -> bool:
        """Send a security key to the ECU."""
        try:
            # Format: 0x27 [level] 0x02 [key...]
            command = bytes([0x27, level.value, 0x02]) + key
            success, response, _ = self.obd_service.send_command(command.hex().encode())
            
            # Check for positive response (0x67 [level] 0x02)
            if success and response and len(response) >= 3:
                return response[0] == 0x67 and response[1] == level.value and response[2] == 0x02
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending key: {e}")
            return False
    
    def load_tune(self, tune_name: str) -> bool:
        """
        Load a tuning profile.
        
        Args:
            tune_name: Name of the tune to load
            
        Returns:
            bool: True if tune was loaded successfully
        """
        if tune_name not in self.available_tunes:
            logger.error(f"Tune not found: {tune_name}")
            return False
        
        self.current_tune = self.available_tunes[tune_name]
        self._trigger_callbacks('on_tune_loaded', self.current_tune)
        logger.info(f"Loaded tune: {tune_name}")
        return True
    
    def save_tune(self, tune_name: str, description: str = "") -> bool:
        """
        Save the current tune to a new profile.
        
        Args:
            tune_name: Name for the new tune
            description: Optional description
            
        Returns:
            bool: True if tune was saved successfully
        """
        if not self.current_tune:
            logger.error("No active tune to save")
            return False
        
        if tune_name in self.available_tunes and self.available_tunes[tune_name].is_read_only:
            logger.error("Cannot overwrite a read-only tune")
            return False
        
        # Create a copy of the current tune
        new_tune = TuneProfile(
            name=tune_name,
            description=description or self.current_tune.description,
            parameters=self.current_tune.parameters.copy(),
            is_read_only=False
        )
        
        self.available_tunes[tune_name] = new_tune
        self.current_tune = new_tune
        
        self._trigger_callbacks('on_tune_saved', new_tune)
        logger.info(f"Saved tune: {tune_name}")
        return True
    
    def update_parameter(self, param: TuningParameter, value: Any) -> bool:
        """
        Update a tuning parameter.
        
        Args:
            param: Parameter to update
            value: New value
            
        Returns:
            bool: True if parameter was updated successfully
        """
        if not self.current_tune or self.current_tune.is_read_only:
            logger.error("Cannot update parameters of read-only tune")
            return False
        
        # Validate parameter value
        if not self._validate_parameter(param, value):
            logger.error(f"Invalid value for {param}: {value}")
            return False
        
        # Update parameter
        old_value = self.current_tune.get_parameter(param)
        self.current_tune.update_parameter(param, value)
        
        # Apply change to ECU if connected
        if self.connected:
            self._apply_parameter_change(param, value)
        
        self._trigger_callbacks('on_parameter_changed', param, old_value, value)
        logger.debug(f"Updated {param} from {old_value} to {value}")
        return True
    
    def _validate_parameter(self, param: TuningParameter, value: Any) -> bool:
        """Validate a parameter value."""
        # TODO: Implement proper validation for each parameter type
        if param == TuningParameter.BOOST_TARGET:
            return isinstance(value, (int, float)) and 0 <= value <= 30.0  # psi
        elif param == TuningParameter.FUEL_PRESSURE:
            return isinstance(value, (int, float)) and 500 <= value <= 3000  # psi
        elif param == TuningParameter.IGNITION_TIMING:
            return isinstance(value, (int, float)) and -10.0 <= value <= 10.0  # degrees
        elif param == TuningParameter.REV_LIMIT:
            return isinstance(value, int) and 1000 <= value <= 9000  # RPM
        elif param == TuningParameter.SPEED_LIMIT:
            return isinstance(value, int) and 0 <= value <= 400  # km/h
        elif param in (TuningParameter.POP_BANG_ENABLED, 
                      TuningParameter.LAUNCH_CONTROL_ENABLED,
                      TuningParameter.FLAT_SHIFT_ENABLED):
            return isinstance(value, bool)
        
        return True  # Default validation passes
    
    def _apply_parameter_change(self, param: TuningParameter, value: Any) -> None:
        """Apply a parameter change to the ECU."""
        try:
            if param == TuningParameter.BOOST_TARGET:
                # Convert PSI to KPA (1 PSI ≈ 6.89476 KPA)
                kpa = int(value * 6.89476)
                self._write_ecu_parameter(0x1234, kpa)  # Example address
                
            elif param == TuningParameter.FUEL_PRESSURE:
                self._write_ecu_parameter(0x1235, int(value))
                
            elif param == TuningParameter.IGNITION_TIMING:
                # Convert degrees to ECU units (0.75° per bit, offset by 64)
                timing = int((value / 0.75) + 64)
                self._write_ecu_parameter(0x1236, timing)
                
            elif param == TuningParameter.REV_LIMIT:
                # Convert RPM to 16-bit value (RPM / 0.25)
                rpm_value = int(value / 0.25)
                self._write_ecu_parameter(0x1237, rpm_value)
                
            elif param == TuningParameter.SPEED_LIMIT:
                # Convert km/h to 16-bit value (km/h * 100)
                speed_value = value * 100
                self._write_ecu_parameter(0x1238, speed_value)
                
            elif param == TuningParameter.POP_BANG_ENABLED:
                self.can_engine.enable_pop_bang(value)
                self.active_features['pop_bang'] = value
                
            elif param == TuningParameter.LAUNCH_CONTROL_ENABLED:
                if value:
                    self.can_engine.enable_launch_control(4000)  # Default 4000 RPM
                else:
                    self.can_engine.disable_launch_control()
                self.active_features['launch_control'] = value
                
            elif param == TuningParameter.FLAT_SHIFT_ENABLED:
                if value:
                    self.can_engine.enable_flat_shift(7000)  # Default 7000 RPM
                else:
                    self.can_engine.disable_flat_shift()
                self.active_features['flat_shift'] = value
                
        except Exception as e:
            logger.error(f"Failed to apply parameter change: {e}")
            self._trigger_callbacks('on_error', f"Failed to apply {param}: {e}")
    
    def _write_ecu_parameter(self, address: int, value: int) -> None:
        """Write a parameter to the ECU."""
        # Format: 0x2E [address] [value]
        # Convert address to 2-byte big-endian
        addr_bytes = address.to_bytes(2, 'big')
        # Convert value to appropriate number of bytes based on size
        if 0 <= value <= 0xFF:
            val_bytes = bytes([value])
        else:
            val_bytes = value.to_bytes((value.bit_length() + 7) // 8, 'big')
        
        command = b"2E " + addr_bytes.hex().encode() + b" " + val_bytes.hex().encode()
        success, response, _ = self.obd_service.send_command(command)
        
        if not success or not response or response[0] != 0x6E:
            raise Exception(f"Failed to write to ECU address 0x{address:04X}")
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Register a callback for an event.
        
        Args:
            event: Event name ('on_connect', 'on_disconnect', 'on_error', etc.)
            callback: Callback function
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, *args, **kwargs) -> None:
        """Trigger all callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {event} callback: {e}")
    
    def get_vehicle_info(self) -> Dict[str, Any]:
        """Get vehicle information."""
        return {
            'vin': self.vehicle_vin,
            'connected': self.connected,
            'security_level': self.security_level.name,
            'current_tune': self.current_tune.name if self.current_tune else None,
            'active_features': self.active_features
        }
    
    async def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information."""
        if not self.connected:
            return {}
        
        try:
            # Read DTCs (Diagnostic Trouble Codes)
            success, dtc_response, _ = self.obd_service.send_command(b"03")
            dtcs = []
            if success and dtc_response:
                # Parse DTCs from response (simplified)
                # Format: 43 [count] [DTC1] [DTC2] ...
                if dtc_response[0] == 0x43 and len(dtc_response) > 1:
                    count = dtc_response[1]
                    for i in range(count):
                        if 2 + i * 2 + 1 < len(dtc_response):
                            dtc_bytes = dtc_response[2 + i * 2:2 + i * 2 + 2]
                            dtc = self._parse_dtc(dtc_bytes)
                            if dtc:
                                dtcs.append(dtc)
            
            # Get freeze frame data
            freeze_frame = {}
            success, ff_response, _ = self.obd_service.send_command(b"02")
            if success and ff_response and ff_response[0] == 0x42:
                # Parse freeze frame data (simplified)
                freeze_frame = self._parse_freeze_frame(ff_response[1:])
            
            return {
                'dtcs': dtcs,
                'freeze_frame': freeze_frame,
                'status': 'ok'
            }
            
        except Exception as e:
            logger.error(f"Diagnostics error: {e}")
            return {
                'error': str(e),
                'status': 'error'
            }
    
    def _parse_dtc(self, dtc_bytes: bytes) -> Optional[str]:
        """Parse a DTC from bytes to string format (e.g., 'P0101')."""
        if len(dtc_bytes) != 2:
            return None
        
        # Extract DTC components
        byte1, byte2 = dtc_bytes
        
        # First two bits of first byte determine the DTC type
        dtc_type = (byte1 >> 6) & 0x03
        
        # Remaining bits form the DTC code
        code = ((byte1 & 0x3F) << 8) | byte2
        
        # Map type to prefix
        type_map = {
            0: 'P',  # Powertrain
            1: 'C',  # Chassis
            2: 'B',  # Body
            3: 'U'   # Network
        }
        
        prefix = type_map.get(dtc_type, 'P')
        return f"{prefix}{code:04X}"
    
    def _parse_freeze_frame(self, data: bytes) -> Dict[str, Any]:
        """Parse freeze frame data."""
        # This is a simplified implementation
        # A real implementation would parse all PID values according to OBD-II specs
        result = {}
        
        if not data:
            return result
        
        try:
            # First byte is the DTC that triggered the freeze frame
            dtc_bytes = data[:2]
            result['dtc'] = self._parse_dtc(dtc_bytes)
            
            # Remaining data contains parameter values
            # Format: [PID] [Value] [PID] [Value] ...
            i = 2
            while i + 1 < len(data):
                pid = data[i]
                value = data[i + 1]
                
                # Map PID to parameter name (simplified)
                pid_map = {
                    0x04: 'engine_load',
                    0x05: 'coolant_temp',
                    0x0A: 'fuel_pressure',
                    0x0B: 'map',
                    0x0C: 'rpm',
                    0x0D: 'speed',
                    0x0F: 'intake_temp',
                    0x10: 'maf_flow',
                    0x11: 'throttle_pos',
                    0x1F: 'runtime_since_start',
                    0x21: 'distance_with_mil',
                    0x2F: 'fuel_level',
                    0x31: 'distance_since_codes_clear',
                    0x42: 'control_module_voltage'
                }
                
                param_name = pid_map.get(pid, f'unknown_{pid:02X}')
                result[param_name] = value
                
                i += 2
                
        except Exception as e:
            logger.error(f"Error parsing freeze frame: {e}")
        
        return result

# Example usage
async def example_usage():
    """Example usage of the MazdaSpeed3TuningSoftware class."""
    # Create instance
    tuner = MazdaSpeed3TuningSoftware()
    
    # Register callbacks
    def on_connect():
        print("Connected to vehicle!")
    
    def on_disconnect():
        print("Disconnected from vehicle")
    
    def on_error(error: str):
        print(f"Error: {error}")
    
    def on_tune_loaded(tune: TuneProfile):
        print(f"Loaded tune: {tune.name}")
    
    def on_parameter_changed(param: TuningParameter, old_value: Any, new_value: Any):
        print(f"Parameter changed: {param.value} from {old_value} to {new_value}")
    
    tuner.register_callback('on_connect', on_connect)
    tuner.register_callback('on_disconnect', on_disconnect)
    tuner.register_callback('on_error', on_error)
    tuner.register_callback('on_tune_loaded', on_tune_loaded)
    tuner.register_callback('on_parameter_changed', on_parameter_changed)
    
    try:
        # Connect to vehicle
        print("Connecting to vehicle...")
        if not await tuner.connect():
            print("Failed to connect to vehicle")
            return
        
        # Print vehicle info
        info = tuner.get_vehicle_info()
        print(f"Connected to vehicle: VIN={info['vin']}")
        
        # Load a tune
        tuner.load_tune("Stage 1")
        
        # Update some parameters
        tuner.update_parameter(TuningParameter.BOOST_TARGET, 18.5)
        tuner.update_parameter(TuningParameter.POP_BANG_ENABLED, True)
        
        # Get diagnostics
        print("Running diagnostics...")
        diag = await tuner.get_diagnostics()
        if diag.get('dtcs'):
            print(f"Found DTCs: {', '.join(diag['dtc'])}")
        else:
            print("No DTCs found")
        
        # Keep running for a while
        print("Monitoring vehicle for 30 seconds...")
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Clean up
        await tuner.disconnect()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run example
    asyncio.run(example_usage())
