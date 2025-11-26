#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3 ECU COMMUNICATION MODULE
Core ECU communication interface compatible with all platforms
"""

import can
import time
import struct
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging

from utils.logger import get_logger

logger = get_logger(__name__)

class ECUState(Enum):
    """ECU connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"

@dataclass
class ECUResponse:
    """Container for ECU response data"""
    success: bool
    data: bytes
    timestamp: float
    error_code: Optional[int] = None
    service_id: Optional[int] = None

class ECUCommunicator:
    """
    MAIN ECU COMMUNICATION CLASS
    Universal ECU communication for all MUTS platforms
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
            interface: CAN interface name
            bitrate: CAN bus bitrate
        """
        self.interface = interface
        self.bitrate = bitrate
        self.bus = None
        self.state = ECUState.DISCONNECTED
        self.security_level = 0
        self.session_active = False
        
        # Threading
        self._lock = threading.RLock()
        self._response_handlers = {}
        self._pending_requests = {}
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'last_activity': 0
        }
        
        logger.info(f"ECU Communicator initialized for interface {interface}")
    
    def connect(self) -> bool:
        """
        Connect to CAN bus and initialize ECU communication
        
        Returns:
            bool: True if connection successful
        """
        try:
            with self._lock:
                if self.state != ECUState.DISCONNECTED:
                    logger.warning(f"ECU already connected, state: {self.state}")
                    return True
                
                self.state = ECUState.CONNECTING
                logger.info(f"Connecting to CAN interface {self.interface}...")
                
                # Initialize CAN bus
                self.bus = can.interface.Bus(
                    channel=self.interface,
                    bustype='socketcan',
                    bitrate=self.bitrate
                )
                
                # Test connection with diagnostic session
                if self._test_connection():
                    self.state = ECUState.CONNECTED
                    logger.info("ECU connection established successfully")
                    return True
                else:
                    self.state = ECUState.ERROR
                    logger.error("ECU connection test failed")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to connect to ECU: {e}")
            self.state = ECUState.ERROR
            self.stats['errors'] += 1
            return False
    
    def disconnect(self):
        """Disconnect from CAN bus"""
        try:
            with self._lock:
                if self.bus:
                    self.bus.shutdown()
                    self.bus = None
                
                self.state = ECUState.DISCONNECTED
                self.session_active = False
                logger.info("ECU disconnected")
                
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def _test_connection(self) -> bool:
        """Test ECU connection with diagnostic session"""
        try:
            # Send diagnostic session request
            response = self.send_request(
                self.SERVICES['DIAGNOSTIC_SESSION'],
                0x01,  # Default session
                timeout=1.0
            )
            
            return response.success and len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def send_request(self, service: int, subfunction: int = 0, 
                    data: bytes = b'', timeout: float = 2.0) -> ECUResponse:
        """
        Send diagnostic request to ECU
        
        Args:
            service: Service ID
            subfunction: Subfunction ID
            data: Additional data
            timeout: Response timeout in seconds
            
        Returns:
            ECUResponse: Response from ECU
        """
        try:
            with self._lock:
                if self.state == ECUState.DISCONNECTED:
                    raise ConnectionError("ECU not connected")
                
                # Construct message
                message_data = bytes([service, subfunction]) + data
                
                # Send CAN message
                can_msg = can.Message(
                    arbitration_id=self.ECU_REQUEST_ID,
                    data=message_data,
                    is_extended_id=False
                )
                
                self.bus.send(can_msg)
                self.stats['messages_sent'] += 1
                self.stats['last_activity'] = time.time()
                
                logger.debug(f"Sent request: 0x{service:02X} 0x{subfunction:02X}")
                
                # Wait for response
                response = self._wait_for_response(service, timeout)
                self.stats['messages_received'] += 1
                
                return response
                
        except Exception as e:
            logger.error(f"Failed to send request: {e}")
            self.stats['errors'] += 1
            return ECUResponse(False, b'', time.time(), error_code=-1)
    
    def _wait_for_response(self, expected_service: int, timeout: float) -> ECUResponse:
        """Wait for ECU response"""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                message = self.bus.recv(timeout=0.1)
                
                if message and message.arbitration_id == self.ECU_RESPONSE_ID:
                    if len(message.data) >= 1:
                        response_service = message.data[0] | 0x40  # Response ID = Service + 0x40
                        
                        if response_service == expected_service | 0x40:
                            logger.debug(f"Received response: 0x{response_service:02X}")
                            return ECUResponse(
                                True,
                                message.data[1:],  # Remove service byte
                                time.time(),
                                service_id=response_service
                            )
            
            logger.warning(f"Timeout waiting for response to service 0x{expected_service:02X}")
            return ECUResponse(False, b'', time.time(), error_code=-2)
            
        except Exception as e:
            logger.error(f"Error waiting for response: {e}")
            return ECUResponse(False, b'', time.time(), error_code=-3)
    
    def read_vin(self) -> Optional[str]:
        """
        Read Vehicle Identification Number
        
        Returns:
            str: VIN if successful, None otherwise
        """
        try:
            # Request VIN using PID 0x90
            response = self.send_request(
                self.SERVICES['READ_DATA'],
                0x90
            )
            
            if response.success and len(response.data) >= 17:
                vin = response.data[:17].decode('ascii', errors='ignore')
                logger.info(f"VIN read: {vin}")
                return vin
            
            logger.error("Failed to read VIN")
            return None
            
        except Exception as e:
            logger.error(f"Error reading VIN: {e}")
            return None
    
    def read_dtcs(self) -> List[Dict]:
        """
        Read Diagnostic Trouble Codes
        
        Returns:
            List of DTC dictionaries
        """
        try:
            dtcs = []
            
            # Request DTCs
            response = self.send_request(
                self.SERVICES['READ_DATA'],
                0x13
            )
            
            if response.success:
                # Parse DTC data
                dtc_data = response.data
                for i in range(0, len(dtc_data), 2):
                    if i + 1 < len(dtc_data):
                        dtc_code = (dtc_data[i] << 8) | dtc_data[i + 1]
                        if dtc_code != 0x0000:
                            dtcs.append({
                                'code': f"P{dtc_code:04X}",
                                'status': 'Active',
                                'timestamp': time.time()
                            })
            
            logger.info(f"Read {len(dtcs)} DTCs")
            return dtcs
            
        except Exception as e:
            logger.error(f"Error reading DTCs: {e}")
            return []
    
    def clear_dtcs(self) -> bool:
        """
        Clear all Diagnostic Trouble Codes
        
        Returns:
            bool: True if successful
        """
        try:
            response = self.send_request(
                self.SERVICES['ECU_RESET'],
                0x04  # Clear DTCs
            )
            
            success = response.success
            logger.info(f"DTC clear: {'Success' if success else 'Failed'}")
            return success
            
        except Exception as e:
            logger.error(f"Error clearing DTCs: {e}")
            return False
    
    def read_live_data(self, pid: int) -> Optional[float]:
        """
        Read live data parameter
        
        Args:
            pid: Parameter ID to read
            
        Returns:
            float: Parameter value if successful, None otherwise
        """
        try:
            response = self.send_request(
                self.SERVICES['READ_DATA'],
                pid
            )
            
            if response.success and len(response.data) >= 2:
                # Convert raw data to float (implementation depends on PID)
                raw_value = struct.unpack('>H', response.data[:2])[0]
                
                # Basic conversion for common PIDs
                if pid == 0x0C:  # Engine RPM
                    return raw_value * 0.25
                elif pid == 0x0B:  # MAP
                    return raw_value
                elif pid == 0x10:  # MAF
                    return raw_value * 0.01
                else:
                    return float(raw_value)
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading live data PID 0x{pid:02X}: {e}")
            return None
    
    def unlock_security(self, level: int = 3) -> bool:
        """
        Unlock ECU security access
        
        Args:
            level: Security level to unlock
            
        Returns:
            bool: True if successful
        """
        try:
            # Request seed
            seed_response = self.send_request(
                self.SERVICES['SECURITY_ACCESS'],
                level * 2 - 1  # Request seed
            )
            
            if not seed_response.success:
                logger.error("Failed to request security seed")
                return False
            
            # Calculate key (simplified implementation)
            seed = struct.unpack('>I', seed_response.data[:4])[0]
            key = self._calculate_security_key(seed, level)
            
            # Send key
            key_response = self.send_request(
                self.SERVICES['SECURITY_ACCESS'],
                level * 2,  # Send key
                struct.pack('>I', key)
            )
            
            if key_response.success:
                self.security_level = level
                logger.info(f"Security unlocked to level {level}")
                return True
            else:
                logger.error("Security unlock failed")
                return False
                
        except Exception as e:
            logger.error(f"Error unlocking security: {e}")
            return False
    
    def _calculate_security_key(self, seed: int, level: int) -> int:
        """
        Calculate security key from seed
        
        Args:
            seed: Security seed from ECU
            level: Security level
            
        Returns:
            int: Calculated key
        """
        # Simplified key calculation - real implementation would use
        # manufacturer-specific algorithms
        key = seed
        for _ in range(16):
            key = ((key << 1) | (key >> 31)) ^ 0x12345678
        
        return key & 0xFFFFFFFF
    
    def get_statistics(self) -> Dict:
        """Get communication statistics"""
        with self._lock:
            return self.stats.copy()
    
    def is_connected(self) -> bool:
        """Check if ECU is connected"""
        return self.state in [ECUState.CONNECTED, ECUState.AUTHENTICATED]
    
    def get_state(self) -> ECUState:
        """Get current ECU state"""
        return self.state
