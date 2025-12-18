#!/usr/bin/env python3
"""
COMPLETE CAN BUS INTERFACE FOR MAZDASPEED 3
Real-time communication with vehicle ECU and modules using python-can
"""

import can
import time
import threading
import struct
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CANMessage:
    """CAN message structure for Mazdaspeed 3"""
    arbitration_id: int
    data: bytes
    timestamp: float
    is_extended: bool = False
    is_remote: bool = False

class Mazdaspeed3CANInterface:
    """
    COMPLETE CAN BUS INTERFACE FOR 2011 MAZDASPEED 3
    Handles all ECU communication, diagnostics, and real-time data acquisition
    """
    
    def __init__(self, channel: str = 'can0', bustype: str = 'socketcan', bitrate: int = 500000):
        self.channel = channel
        self.bustype = bustype
        self.bitrate = bitrate
        self.bus = None
        self.running = False
        self.message_handlers = {}
        self.ecu_addresses = self._initialize_ecu_addresses()
        
        # Real-time data storage
        self.live_data = {}
        self.message_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Threading
        self.receive_thread = None
        self.process_thread = None
        
        # Diagnostic session state
        self.diagnostic_session_active = False
        self.security_access_granted = False
        
    def _initialize_ecu_addresses(self) -> Dict[str, int]:
        """Initialize Mazdaspeed 3 specific ECU addresses"""
        return {
            'engine_ecu_tx': 0x7E0,      # ECU transmit
            'engine_ecu_rx': 0x7E8,      # ECU receive
            'tcm_tx': 0x7E1,             # Transmission control
            'tcm_rx': 0x7E9,
            'abs_tx': 0x7E2,             # ABS module
            'abs_rx': 0x7EA,
            'airbag_tx': 0x7E3,          # Airbag module
            'airbag_rx': 0x7EB,
            'cluster_tx': 0x7E4,         # Instrument cluster
            'cluster_rx': 0x7EC,
            'immobilizer_tx': 0x7E5,     # Immobilizer
            'immobilizer_rx': 0x7ED
        }
    
    def connect(self) -> bool:
        """Connect to CAN bus"""
        try:
            self.bus = can.interface.Bus(
                channel=self.channel,
                bustype=self.bustype,
                bitrate=self.bitrate
            )
            self.running = True
            logger.info(f"Connected to CAN bus on {self.channel}")
            return True
        except Exception as e:
            logger.error(f"CAN bus connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from CAN bus"""
        self.running = False
        if self.bus:
            self.bus.shutdown()
        logger.info("Disconnected from CAN bus")
    
    def start_receiving(self):
        """Start receiving CAN messages in background thread"""
        if not self.bus:
            raise RuntimeError("CAN bus not connected")
        
        self.receive_thread = threading.Thread(target=self._receive_loop)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        self.process_thread = threading.Thread(target=self._process_loop)
        self.process_thread.daemon = True
        self.process_thread.start()
        
        logger.info("Started CAN message receiving")
    
    def _receive_loop(self):
        """Receive CAN messages in loop"""
        while self.running:
            try:
                message = self.bus.recv(timeout=1.0)
                if message:
                    can_msg = CANMessage(
                        arbitration_id=message.arbitration_id,
                        data=message.data,
                        timestamp=message.timestamp,
                        is_extended=message.is_extended_id,
                        is_remote=message.is_remote_frame
                    )
                    
                    with self.buffer_lock:
                        self.message_buffer.append(can_msg)
                        
            except can.CanError:
                continue
            except Exception as e:
                logger.error(f"CAN receive error: {e}")
                time.sleep(0.1)
    
    def _process_loop(self):
        """Process received CAN messages"""
        while self.running:
            try:
                messages = []
                with self.buffer_lock:
                    if self.message_buffer:
                        messages = self.message_buffer.copy()
                        self.message_buffer.clear()
                
                for msg in messages:
                    self._process_message(msg)
                
                time.sleep(0.01)  # 100 Hz processing
                
            except Exception as e:
                logger.error(f"CAN process error: {e}")
                time.sleep(0.1)
    
    def _process_message(self, message: CANMessage):
        """Process individual CAN message"""
        # Update live data based on message ID
        if message.arbitration_id == 0x201:  # Engine RPM
            if len(message.data) >= 8:
                rpm = struct.unpack('>H', message.data[0:2])[0] // 4
                self.live_data['engine_rpm'] = rpm
        
        elif message.arbitration_id == 0x202:  # Vehicle speed
            if len(message.data) >= 8:
                speed = struct.unpack('>H', message.data[0:2])[0] // 100
                self.live_data['vehicle_speed'] = speed
        
        elif message.arbitration_id == 0x203:  # Throttle position
            if len(message.data) >= 8:
                throttle = struct.unpack('>H', message.data[0:2])[0] / 10
                self.live_data['throttle_position'] = throttle
        
        elif message.arbitration_id == 0x204:  # Manifold pressure
            if len(message.data) >= 8:
                pressure = struct.unpack('>H', message.data[0:2])[0] / 10
                self.live_data['manifold_pressure'] = pressure
        
        elif message.arbitration_id == 0x205:  # AFR
            if len(message.data) >= 8:
                afr = struct.unpack('>H', message.data[0:2])[0] / 10
                self.live_data['afr'] = afr
        
        elif message.arbitration_id == 0x206:  # Ignition timing
            if len(message.data) >= 8:
                timing = struct.unpack('>h', message.data[0:2])[0] / 10
                self.live_data['ignition_timing'] = timing
        
        elif message.arbitration_id == 0x207:  # Coolant temp
            if len(message.data) >= 8:
                temp = struct.unpack('>H', message.data[0:2])[0] / 10
                self.live_data['coolant_temp'] = temp
        
        elif message.arbitration_id == 0x208:  # Intake temp
            if len(message.data) >= 8:
                temp = struct.unpack('>H', message.data[0:2])[0] / 10
                self.live_data['intake_temp'] = temp
        
        # Call registered handlers
        if message.arbitration_id in self.message_handlers:
            try:
                self.message_handlers[message.arbitration_id](message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
    
    def send_diagnostic_request(self, service_id: int, data: bytes = b'') -> Optional[CANMessage]:
        """Send diagnostic request to ECU"""
        if not self.bus:
            return None
        
        # Construct diagnostic message
        message_data = bytes([service_id]) + data
        
        message = can.Message(
            arbitration_id=self.ecu_addresses['engine_ecu_tx'],
            data=message_data,
            is_extended_id=False
        )
        
        try:
            self.bus.send(message)
            
            # Wait for response
            response = self._wait_for_response(
                self.ecu_addresses['engine_ecu_rx'],
                timeout=1.0
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Diagnostic request failed: {e}")
            return None
    
    def _wait_for_response(self, arbitration_id: int, timeout: float = 1.0) -> Optional[CANMessage]:
        """Wait for specific CAN message"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self.buffer_lock:
                for msg in self.message_buffer:
                    if msg.arbitration_id == arbitration_id:
                        return msg
            
            time.sleep(0.01)
        
        return None
    
    def read_ecu_data(self, address: int, length: int) -> Optional[bytes]:
        """Read data from ECU memory"""
        # Construct read request
        request_data = bytes([
            0x22,  # Read data by identifier
            (address >> 8) & 0xFF,
            address & 0xFF,
            length
        ])
        
        response = self.send_diagnostic_request(0x22, request_data[1:])
        
        if response and len(response.data) >= 4:
            # Extract data from response
            if response.data[0] == 0x62:  # Positive response
                return response.data[3:3+length]
        
        return None
    
    def write_ecu_data(self, address: int, data: bytes) -> bool:
        """Write data to ECU memory"""
        # Construct write request
        request_data = bytes([
            0x2E,  # Write data by identifier
            (address >> 8) & 0xFF,
            address & 0xFF
        ]) + data
        
        response = self.send_diagnostic_request(0x2E, request_data[1:])
        
        if response and len(response.data) >= 3:
            return response.data[0] == 0x6E  # Positive response
        
        return False
    
    def start_diagnostic_session(self, session_type: int = 0x01) -> bool:
        """Start diagnostic session"""
        response = self.send_diagnostic_request(0x10, bytes([session_type]))
        
        if response and len(response.data) >= 2:
            if response.data[0] == 0x50:  # Positive response
                self.diagnostic_session_active = True
                logger.info(f"Diagnostic session started (type: {session_type:02X})")
                return True
        
        return False
    
    def stop_diagnostic_session(self):
        """Stop diagnostic session"""
        self.diagnostic_session_active = False
        self.security_access_granted = False
        logger.info("Diagnostic session stopped")
    
    def request_security_access(self, level: int = 0x01, key: Optional[bytes] = None) -> bool:
        """Request security access"""
        if not self.diagnostic_session_active:
            logger.error("Diagnostic session not active")
            return False
        
        # Request seed
        response = self.send_diagnostic_request(0x27, bytes([level]))
        
        if response and len(response.data) >= 3:
            if response.data[0] == 0x67:  # Positive response with seed
                seed = response.data[2:6]
                
                if key:
                    # Send key
                    key_request = bytes([level + 1]) + key
                    key_response = self.send_diagnostic_request(0x27, key_request[1:])
                    
                    if key_response and len(key_response) >= 2:
                        if key_response.data[0] == 0x67:  # Access granted
                            self.security_access_granted = True
                            logger.info("Security access granted")
                            return True
                
                else:
                    logger.info(f"Security seed received: {seed.hex()}")
                    return seed
        
        return False
    
    def read_dtc(self) -> List[Dict]:
        """Read diagnostic trouble codes"""
        response = self.send_diagnostic_request(0x19, bytes([0x02]))  # Read DTC
        
        dtc_list = []
        
        if response and len(response.data) >= 3:
            if response.data[0] == 0x59:  # Positive response
                dtc_count = response.data[1]
                dtc_data = response.data[2:]
                
                for i in range(dtc_count):
                    if i * 2 + 1 < len(dtc_data):
                        dtc_code = struct.unpack('>H', dtc_data[i*2:i*2+2])[0]
                        dtc_list.append({
                            'code': f"P{dtc_code:04X}",
                            'status': 'Active'
                        })
        
        return dtc_list
    
    def clear_dtc(self) -> bool:
        """Clear diagnostic trouble codes"""
        response = self.send_diagnostic_request(0x14, bytes([0xFF, 0xFF, 0xFF]))
        
        if response and len(response.data) >= 2:
            return response.data[0] == 0x54  # Positive response
        
        return False
    
    def get_live_data(self) -> Dict:
        """Get current live data"""
        return self.live_data.copy()
    
    def register_message_handler(self, arbitration_id: int, handler: Callable):
        """Register custom message handler"""
        self.message_handlers[arbitration_id] = handler
    
    def unregister_message_handler(self, arbitration_id: int):
        """Unregister message handler"""
        self.message_handlers.pop(arbitration_id, None)
    
    def send_custom_message(self, arbitration_id: int, data: bytes):
        """Send custom CAN message"""
        if not self.bus:
            return False
        
        message = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=False
        )
        
        try:
            self.bus.send(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

# Utility functions for common operations
def create_mazdaspeed3_interface(channel='can0', bustype='socketcan'):
    """Create and connect to Mazdaspeed 3 CAN interface"""
    interface = Mazdaspeed3CANInterface(channel=channel, bustype=bustype)
    
    if interface.connect():
        interface.start_receiving()
        return interface
    else:
        return None

def read_pid(interface: Mazdaspeed3CANInterface, pid: str) -> Optional[float]:
    """Read OBD-II PID"""
    pid_map = {
        '0C': ('engine_rpm', lambda d: struct.unpack('>H', d[3:5])[0] / 4),
        '0D': ('vehicle_speed', lambda d: struct.unpack('>H', d[3:5])[0]),
        '11': ('throttle_position', lambda d: struct.unpack('>H', d[3:5])[0] / 10),
        '0B': ('manifold_pressure', lambda d: struct.unpack('>H', d[3:5])[0] / 10),
        '14': ('oxygen_sensor', lambda d: struct.unpack('>H', d[3:5])[0] / 10),
        '10': ('maf_flow', lambda d: struct.unpack('>H', d[3:5])[0] / 100),
        '05': ('coolant_temp', lambda d: struct.unpack('>H', d[3:5])[0] / 10),
        '0F': ('intake_temp', lambda d: struct.unpack('>H', d[3:5])[0] / 10)
    }
    
    if pid not in pid_map:
        return None
    
    # Send mode 01 PID request
    response = interface.send_diagnostic_request(0x01, bytes([int(pid, 16)]))
    
    if response and len(response.data) >= 4:
        if response.data[0] == 0x41:  # Positive response
            param_name, converter = pid_map[pid]
            value = converter(response.data)
            interface.live_data[param_name] = value
            return value
    
    return None
