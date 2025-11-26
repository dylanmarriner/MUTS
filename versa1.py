#!/usr/bin/env python3
"""
ECU Communication Module - Handles all CAN bus and diagnostic communication
with the Mazdaspeed 3 ECU. Reverse engineered from VersaTuner protocols.
"""

import can
import time
import struct
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from core.ecu_communication import ECUCommunicator
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ECUResponse:
    """Container for ECU response data"""
    success: bool
    data: bytes
    timestamp: float
    error_code: Optional[int] = None

# VersaTuner specific extensions to the core ECUCommunicator
class VersaTunerECU(ECUCommunicator):
    """
    VersaTuner specific ECU communication extensions
    Builds on the core ECUCommunicator with VersaTuner protocols
    """
    
    # Mazdaspeed 3 specific CAN IDs
    ECU_REQUEST_ID = 0x7E0
    ECU_RESPONSE_ID = 0x7E8
    BROADCAST_ID = 0x7DF
    
    # Service identifiers
    SERVICES = {
        'DIAGNOSTIC_SESSION': 0x10,
        'ECU_RESET': 0x11,
        'READ_DATA': 0x22,
        'READ_MEMORY': 0x23,
        'SECURITY_ACCESS': 0x27,
        'ROUTINE_CONTROL': 0x31,
        'WRITE_DATA': 0x2E,
        'WRITE_MEMORY': 0x3D
    }
    
    def __init__(self, interface: str = 'can0', bitrate: int = 500000):
        """
        Initialize ECU communicator
        
        Args:
            interface: CAN interface name (can0, vcan0, etc.)
            bitrate: CAN bus bitrate in bits per second
        """
        self.interface = interface
        self.bitrate = bitrate
        self.bus = None
        self.is_connected = False
        self.session_control = 0x01  # Default session
        self.security_level = 0
        self.response_callbacks = {}
        self.logger = VersaLogger(__name__)
        
        # Threading controls
        self._listener_thread = None
        self._stop_listener = False
        
    def connect(self) -> bool:
        """
        Connect to CAN bus and initialize communication
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.bus = can.interface.Bus(
                channel=self.interface,
                bustype='socketcan',
                bitrate=self.bitrate
            )
            
            # Start background listener
            self._stop_listener = False
            self._listener_thread = threading.Thread(target=self._message_listener)
            self._listener_thread.daemon = True
            self._listener_thread.start()
            
            # Test communication
            if self._test_connection():
                self.is_connected = True
                self.logger.info(f"Connected to ECU on {self.interface}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to connect to CAN bus: {e}")
            
        return False
    
    def disconnect(self):
        """Disconnect from CAN bus and cleanup resources"""
        self._stop_listener = True
        if self._listener_thread:
            self._listener_thread.join(timeout=2.0)
        
        if self.bus:
            self.bus.shutdown()
            self.bus = None
            
        self.is_connected = False
        self.logger.info("Disconnected from ECU")
    
    def _test_connection(self) -> bool:
        """Test ECU communication by reading VIN"""
        try:
            vin = self.read_vin()
            return vin is not None and len(vin) == 17
        except:
            return False
    
    def send_request(self, service: int, subfunction: int, data: bytes = b'') -> ECUResponse:
        """
        Send diagnostic request to ECU and wait for response
        
        Args:
            service: Service identifier
            subfunction: Service subfunction
            data: Additional data payload
            
        Returns:
            ECUResponse: Response from ECU
        """
        if not self.is_connected:
            return ECUResponse(False, b'', time.time(), error_code=0xFF)
        
        # Build request payload
        payload = bytes([service, subfunction]) + data
        
        # Create CAN message
        message = can.Message(
            arbitration_id=self.ECU_REQUEST_ID,
            data=payload,
            is_extended_id=False
        )
        
        # Generate unique identifier for this request
        request_id = f"{service:02X}{subfunction:02X}"
        
        # Set up response tracking
        response_event = threading.Event()
        response_data = None
        
        def response_callback(received_data: bytes):
            nonlocal response_data
            response_data = received_data
            response_event.set()
        
        self.response_callbacks[request_id] = response_callback
        
        try:
            # Send request
            self.bus.send(message)
            self.logger.debug(f"Sent request: {payload.hex().upper()}")
            
            # Wait for response with timeout
            if response_event.wait(timeout=2.0):
                if response_data:
                    return ECUResponse(True, response_data, time.time())
            
            return ECUResponse(False, b'', time.time(), error_code=0x78)  # Timeout
            
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return ECUResponse(False, b'', time.time(), error_code=0xFF)
        
        finally:
            # Clean up callback
            if request_id in self.response_callbacks:
                del self.response_callbacks[request_id]
    
    def _message_listener(self):
        """Background thread to listen for ECU responses"""
        while not self._stop_listener and self.bus:
            try:
                message = self.bus.recv(timeout=0.1)
                
                if (message and message.arbitration_id == self.ECU_RESPONSE_ID and
                    len(message.data) >= 3):
                    
                    # Extract service and subfunction from response
                    service_response = message.data[0]
                    service_request = message.data[1] if service_response == 0x7F else message.data[0] - 0x40
                    subfunction = message.data[2] if service_response == 0x7F else message.data[1]
                    
                    request_id = f"{service_request:02X}{subfunction:02X}"
                    
                    # Trigger callback if exists
                    if request_id in self.response_callbacks:
                        self.response_callbacks[request_id](message.data)
                        
            except can.CanError:
                continue
            except Exception as e:
                self.logger.debug(f"Listener error: {e}")
    
    def read_vin(self) -> Optional[str]:
        """
        Read Vehicle Identification Number from ECU
        
        Returns:
            str: VIN string or None if failed
        """
        response = self.send_request(self.SERVICES['READ_DATA'], 0xF189)
        
        if response.success and len(response.data) >= 20:
            # VIN is typically at offset 3-19 in response
            vin_bytes = response.data[3:20]
            try:
                return vin_bytes.decode('ascii').strip()
            except:
                pass
                
        return None
    
    def read_ecu_part_number(self) -> Optional[str]:
        """Read ECU part number"""
        response = self.send_request(self.SERVICES['READ_DATA'], 0xF187)
        
        if response.success and len(response.data) >= 19:
            part_bytes = response.data[3:19]
            try:
                return part_bytes.decode('ascii').strip()
            except:
                pass
                
        return None
    
    def read_memory(self, address: int, length: int) -> ECUResponse:
        """
        Read memory from ECU using ReadMemoryByAddress service (0x23)
        
        Args:
            address: Memory address to read from
            length: Number of bytes to read
            
        Returns:
            ECUResponse: Response containing memory data
        """
        # Build address and length bytes (3 bytes each for Mazda)
        address_bytes = address.to_bytes(3, 'big')
        length_bytes = length.to_bytes(3, 'big')
        
        return self.send_request(
            self.SERVICES['READ_MEMORY'], 
            0x00,  # No subfunction
            address_bytes + length_bytes
        )
    
    def read_dtcs(self) -> List[Dict[str, Any]]:
        """
        Read Diagnostic Trouble Codes from ECU
        
        Returns:
            List of DTC dictionaries with code and description
        """
        dtcs = []
        
        # Read current DTCs
        response = self.send_request(self.SERVICES['READ_DATA'], 0x0201)
        
        if response.success and len(response.data) > 3:
            dtc_data = response.data[3:]
            
            # Parse DTC data (each DTC is 2 bytes)
            for i in range(0, len(dtc_data) - 1, 2):
                if dtc_data[i] == 0x00 and dtc_data[i+1] == 0x00:
                    continue  # Skip empty slots
                    
                dtc_bytes = dtc_data[i:i+2]
                dtc_code = self._parse_dtc_code(dtc_bytes)
                
                if dtc_code:
                    dtcs.append({
                        'code': dtc_code,
                        'description': self._get_dtc_description(dtc_code),
                        'status': 'Active'
                    })
        
        return dtcs
    
    def _parse_dtc_code(self, dtc_bytes: bytes) -> Optional[str]:
        """Parse 2-byte DTC data into standard code format"""
        if len(dtc_bytes) != 2:
            return None
            
        # Extract DTC components
        first_byte = dtc_bytes[0]
        second_byte = dtc_bytes[1]
        
        # Decode DTC type and number
        dtc_type = (first_byte >> 6) & 0x03
        digit1 = (first_byte >> 4) & 0x03
        digit2 = first_byte & 0x0F
        digit3 = (second_byte >> 4) & 0x0F
        digit4 = second_byte & 0x0F
        
        # Map type to letter
        type_map = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
        type_char = type_map.get(dtc_type, 'P')
        
        return f"{type_char}{digit1}{digit2}{digit3}{digit4}"
    
    def _get_dtc_description(self, dtc_code: str) -> str:
        """Get description for DTC code (Mazdaspeed 3 specific)"""
        dtc_descriptions = {
            'P0101': 'Mass Air Flow Circuit Range/Performance',
            'P0102': 'Mass Air Flow Circuit Low Input',
            'P0103': 'Mass Air Flow Circuit High Input',
            'P0234': 'Turbocharger Overboost Condition',
            'P0300': 'Random/Multiple Cylinder Misfire Detected',
            'P0301': 'Cylinder 1 Misfire Detected',
            'P0302': 'Cylinder 2 Misfire Detected', 
            'P0303': 'Cylinder 3 Misfire Detected',
            'P0304': 'Cylinder 4 Misfire Detected',
            'P0420': 'Catalyst System Efficiency Below Threshold',
            'P0611': 'ECU Internal Control Module Memory Error',
            'P2187': 'Fuel System Too Lean at Idle',
            'P2188': 'Fuel System Too Rich at Idle',
        }
        
        return dtc_descriptions.get(dtc_code, 'Unknown DTC')
    
    def clear_dtcs(self) -> bool:
        """
        Clear all Diagnostic Trouble Codes
        
        Returns:
            bool: True if successful, False otherwise
        """
        response = self.send_request(0x14, 0xFF)  # ClearDTCInformation
        
        return response.success and response.data[0] == 0x54
    
    def read_live_data(self, pid: int) -> Optional[float]:
        """
        Read live data parameter using PID
        
        Args:
            pid: Parameter ID to read
            
        Returns:
            float: Parameter value or None if failed
        """
        response = self.send_request(self.SERVICES['READ_DATA'], pid)
        
        if response.success and len(response.data) >= 4:
            return self._parse_pid_value(pid, response.data[3:])
            
        return None
    
    def _parse_pid_value(self, pid: int, data: bytes) -> Optional[float]:
        """Parse PID response data into physical value"""
        pid_formulas = {
            # Standard PIDs
            0x04: lambda d: (d[0] * 100) / 255,  # Engine Load
            0x05: lambda d: d[0] - 40,           # Coolant Temp
            0x0C: lambda d: ((d[0] * 256) + d[1]) / 4,  # RPM
            0x0D: lambda d: d[0],                # Vehicle Speed
            0x0F: lambda d: d[0] - 40,           # Intake Air Temp
            0x11: lambda d: (d[0] * 100) / 255,  # Throttle Position
            
            # Mazda Specific PIDs
            0x223365: lambda d: ((d[0] * 256) + d[1] - 1000) / 10,  # Boost Pressure
            0x22345C: lambda d: (d[0] - 128) / 2,  # VVT Angle
        }
        
        if pid in pid_formulas and len(data) >= 2:
            try:
                return pid_formulas[pid](data)
            except:
                pass
                
        return None