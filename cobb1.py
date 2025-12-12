from core.ecu_communication import ECUCommunicator, ECUResponse, ECUState
from core.safety_validator import get_safety_validator
from utils.logger import get_logger
"""
CAN Bus Protocol Implementation for Mazdaspeed 3 MZR DISI Engine
Handles direct ECU communication bypassing Cobb security
"""

import can
import struct
import time
import hashlib
from typing import List, Dict, Optional

class MZRCANProtocol:
    """
    Reverse engineered CAN protocol for Mazda MZR 2.3L DISI Turbo Engine
    Based on Cobb Access Port communication patterns
    """
    
    # CAN IDs for Mazdaspeed 3 2011
    ECU_TX_ID = 0x7E0
    ECU_RX_ID = 0x7E8
    DIAGNOSTIC_ID = 0x7DF
    BROADCAST_ID = 0x7E1
    
    # Security access levels
    SAFETY_LEVEL = 0x01
    DIAG_LEVEL = 0x03
    FLASH_LEVEL = 0x05
    TUNING_LEVEL = 0x07
    
    def __init__(self, channel: str = 'vcan0', bustype: str = 'socketcan'):
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)
        self.security_level = 0
        self.seed_key_algorithm = self._reverse_engineered_seed_algo()
        self.session_active = False
        
    def _reverse_engineered_seed_algo(self):
        """
        Reverse engineered seed-key algorithm from Cobb AP
        Mazda uses modified ISO 14230-3 security with custom twists
        """
        def algo(seed: int) -> int:
            # Phase 1: Basic transformation
            temp = ((seed >> 8) & 0xFF) ^ (seed & 0xFF)
            temp = (temp * 0x201) & 0xFFFF
            
            # Phase 2: Cobb-specific modification
            temp ^= 0x8147
            temp = (temp + 0x1A2B) & 0xFFFF
            
            # Phase 3: Final scramble
            key = ((temp << 8) | (temp >> 8)) & 0xFFFF
            return key ^ 0x55AA
            
        return algo
    
    def send_can_message(self, can_id: int, data: bytes) -> bool:
        """
        Send raw CAN message to ECU
        """
        try:
            message = can.Message(
                arbitration_id=can_id,
                data=data,
                is_extended_id=False
            )
            self.bus.send(message)
            return True
        except can.CanError:
            return False
    
    def receive_can_message(self, timeout: float = 1.0) -> Optional[can.Message]:
        """
        Receive CAN message with timeout
        """
        try:
            return self.bus.recv(timeout=timeout)
        except can.CanError:
            return None
    
    def request_seed(self, level: int) -> Optional[int]:
        """
        Request security seed from ECU for given access level
        """
        seed_request = bytes([0x27, level])
        self.send_can_message(self.ECU_TX_ID, seed_request)
        
        response = self.receive_can_message()
        if response and response.data[0] == 0x67:
            seed = (response.data[2] << 8) | response.data[3]
            return seed
        return None
    
    def send_key(self, level: int, key: int) -> bool:
        """
        Send security key to ECU to unlock access level
        """
        key_bytes = bytes([0x27, level + 1, (key >> 8) & 0xFF, key & 0xFF])
        self.send_can_message(self.ECU_TX_ID, key_bytes)
        
        response = self.receive_can_message()
        return response and response.data[0] == 0x67
    
    def unlock_ecu(self, target_level: int) -> bool:
        """
        Full security access unlock sequence
        """
        for level in range(self.security_level + 1, target_level + 1):
            seed = self.request_seed(level)
            if not seed:
                return False
                
            key = self.seed_key_algorithm(seed)
            if not self.send_key(level, key):
                return False
                
            time.sleep(0.1)
            
        self.security_level = target_level
        self.session_active = True
        return True
    
    def read_memory(self, address: int, length: int) -> Optional[bytes]:
        """
        Read ECU memory at specified address
        Used for dumping ROM and calibration data
        """
        if not self.session_active:
            return None
            
        # ISO 14230-3 read memory by address
        request_data = bytes([0x23, 
                            (address >> 16) & 0xFF,
                            (address >> 8) & 0xFF,
                            address & 0xFF,
                            length])
        
        self.send_can_message(self.ECU_TX_ID, request_data)
        
        data = bytearray()
        response = self.receive_can_message()
        
        while response and response.data[0] == 0x63:
            data.extend(response.data[1:])
            response = self.receive_can_message(0.5)
            
        return bytes(data) if data else None
    
    def write_memory(self, address: int, data: bytes) -> bool:
        """
        Write data to ECU memory address
        Used for real-time tuning parameter modification
        """
        if not self.session_active or self.security_level < self.TUNING_LEVEL:
            return False
            
        chunk_size = 4  # ECU accepts 4 bytes per write
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            request_data = bytes([0x3D]) + struct.pack('>I', address + i)[1:] + chunk
            
            self.send_can_message(self.ECU_TX_ID, request_data)
            response = self.receive_can_message()
            
            if not response or response.data[0] != 0x7D:
                return False
                
        return True
    
    def read_ecu_identification(self) -> Dict[str, str]:
        """
        Read ECU identification information
        """
        ident_data = {}
        
        # Read VIN
        self.send_can_message(self.ECU_TX_ID, bytes([0x22, 0xF1, 0x90]))
        response = self.receive_can_message()
        if response:
            ident_data['VIN'] = response.data[2:].decode('ascii', errors='ignore')
        
        # Read ECU part number
        self.send_can_message(self.ECU_TX_ID, bytes([0x22, 0xF1, 0x87]))
        response = self.receive_can_message()
        if response:
            ident_data['ECU_PN'] = response.data[2:].hex().upper()
            
        # Read calibration ID
        self.send_can_message(self.ECU_TX_ID, bytes([0x22, 0xF1, 0x85]))
        response = self.receive_can_message()
        if response:
            ident_data['CAL_ID'] = response.data[2:].hex().upper()
            
        return ident_data