from core.ecu_communication import ECUCommunicator, ECUResponse, ECUState
from core.safety_validator import get_safety_validator
from utils.logger import get_logger
#!/usr/bin/env python3
"""
Security Access Module - Handles ECU security access and authentication
Reverse engineered from Mazda security algorithms used in VersaTuner
"""

import hashlib
import struct
from typing import Optional, Dict, Any
from .ecu_communication import ECUCommunicator, ECUResponse
from ..utils.logger import VersaLogger

class SecurityManager:
    """
    Manages ECU security access using reverse engineered algorithms
    from Mazda factory tools and VersaTuner
    """
    
    # Security access levels
    ACCESS_LEVELS = {
        'DEFAULT': 0x01,      # Basic diagnostic access
        'EXTENDED': 0x03,     # Extended diagnostics
        'PROGRAMMING': 0x05,  # ECU programming access
        'MANUFACTURER': 0x07  # Manufacturer level
    }
    
    def __init__(self, ecu_communicator: ECUCommunicator):
        """
        Initialize Security Manager
        
        Args:
            ecu_communicator: ECUCommunicator instance for communication
        """
        self.ecu = ecu_communicator
        self.logger = VersaLogger(__name__)
        self.security_unlocked = False
        self.current_level = 0
        
        # Security algorithm constants (reverse engineered)
        self.ALGORITHM_CONSTANTS = {
            'LEVEL_1': {
                'XOR_KEY': 0x7382A91F,
                'ADD_VALUE': 0x1F47A2B8,
                'ROTATE_BITS': 3
            },
            'LEVEL_2': {
                'XOR_KEY': 0xA5C7E93D,
                'ADD_VALUE': 0x2B8E47F1,
                'ROTATE_BITS': 7
            },
            'LEVEL_3': {
                'XOR_KEY': 0x1F4A7C3E,
                'ADD_CONST': 0x8D3A2F47,
                'XOR_CONST': 0xB5E8C91A,
                'ROTATE_BITS': 11
            }
        }
    
    def unlock_ecu(self, target_level: int = ACCESS_LEVELS['PROGRAMMING']) -> bool:
        """
        Unlock ECU security access for programming
        
        Args:
            target_level: Desired security access level
            
        Returns:
            bool: True if security access granted, False otherwise
        """
        self.logger.info(f"Attempting security unlock to level {target_level:02X}")
        
        # Step through security levels
        for level in [0x01, 0x03, 0x05]:
            if level > target_level:
                break
                
            if not self._unlock_security_level(level):
                self.logger.error(f"Failed to unlock security level {level:02X}")
                return False
                
            self.logger.info(f"Security level {level:02X} unlocked")
        
        self.security_unlocked = True
        self.current_level = target_level
        self.logger.info("ECU security fully unlocked")
        return True
    
    def _unlock_security_level(self, level: int) -> bool:
        """
        Unlock specific security level using seed-key algorithm
        
        Args:
            level: Security level to unlock
            
        Returns:
            bool: True if level unlocked successfully
        """
        # Request seed from ECU
        seed_response = self.ecu.send_request(0x27, level)
        
        if not seed_response.success:
            self.logger.error(f"Failed to request seed for level {level:02X}")
            return False
        
        # Extract seed from response (typically bytes 2-5)
        if len(seed_response.data) < 6:
            self.logger.error("Invalid seed response length")
            return False
            
        seed = seed_response.data[2:6]
        self.logger.debug(f"Received seed: {seed.hex().upper()}")
        
        # Calculate key using reverse engineered algorithm
        key = self._calculate_security_key(seed, level)
        self.logger.debug(f"Calculated key: {key.hex().upper()}")
        
        # Send key to ECU
        key_response = self.ecu.send_request(0x27, level + 1, key)
        
        if (key_response.success and len(key_response.data) >= 2 and
            key_response.data[1] == 0x67):  # Positive response
            return True
            
        self.logger.error(f"Key rejection for level {level:02X}")
        return False
    
    def _calculate_security_key(self, seed: bytes, level: int) -> bytes:
        """
        Calculate security key from seed using reverse engineered algorithms
        
        Args:
            seed: 4-byte seed from ECU
            level: Security level
            
        Returns:
            bytes: 4-byte calculated key
        """
        seed_int = int.from_bytes(seed, 'big')
        
        if level == 0x01:
            return self._level1_algorithm(seed_int)
        elif level == 0x03:
            return self._level2_algorithm(seed_int)
        elif level == 0x05:
            return self._level3_algorithm(seed_int)
        else:
            # Default to level 1 for unknown levels
            return self._level1_algorithm(seed_int)
    
    def _level1_algorithm(self, seed: int) -> bytes:
        """Level 1 security algorithm - basic diagnostic access"""
        constants = self.ALGORITHM_CONSTANTS['LEVEL_1']
        
        key = seed ^ constants['XOR_KEY']
        key = (key + constants['ADD_VALUE']) & 0xFFFFFFFF
        key = ((key >> constants['ROTATE_BITS']) | (key << (32 - constants['ROTATE_BITS']))) & 0xFFFFFFFF
        
        return key.to_bytes(4, 'big')
    
    def _level2_algorithm(self, seed: int) -> bytes:
        """Level 2 security algorithm - extended diagnostics"""
        constants = self.ALGORITHM_CONSTANTS['LEVEL_2']
        
        key = seed ^ constants['XOR_KEY']
        key = ((key << constants['ROTATE_BITS']) | (key >> (32 - constants['ROTATE_BITS']))) & 0xFFFFFFFF
        key = (key + constants['ADD_VALUE']) & 0xFFFFFFFF
        
        return key.to_bytes(4, 'big')
    
    def _level3_algorithm(self, seed: int) -> bytes:
        """Level 3 security algorithm - programming access"""
        constants = self.ALGORITHM_CONSTANTS['LEVEL_3']
        
        key = seed ^ constants['XOR_KEY']
        key = (key + constants['ADD_CONST']) & 0xFFFFFFFF
        key = key ^ constants['XOR_CONST']
        key = ((key << constants['ROTATE_BITS']) | (key >> (32 - constants['ROTATE_BITS']))) & 0xFFFFFFFF
        
        return key.to_bytes(4, 'big')
    
    def enter_programming_mode(self) -> bool:
        """
        Enter ECU programming mode for ROM flashing
        
        Returns:
            bool: True if programming mode entered successfully
        """
        if not self.security_unlocked:
            self.logger.error("Security not unlocked - cannot enter programming mode")
            return False
        
        # Request programming session
        response = self.ecu.send_request(0x10, 0x02)  # ProgrammingSession
        
        if response.success and len(response.data) >= 2 and response.data[1] == 0x50:
            self.logger.info("Programming mode entered successfully")
            return True
            
        self.logger.error("Failed to enter programming mode")
        return False
    
    def exit_programming_mode(self) -> bool:
        """
        Exit ECU programming mode
        
        Returns:
            bool: True if programming mode exited successfully
        """
        response = self.ecu.send_request(0x10, 0x01)  # DefaultSession
        
        if response.success:
            self.logger.info("Programming mode exited")
            self.security_unlocked = False
            self.current_level = 0
            return True
            
        return False
    
    def check_security_status(self) -> Dict[str, Any]:
        """
        Check current security status of ECU
        
        Returns:
            Dict containing security status information
        """
        status = {
            'unlocked': self.security_unlocked,
            'current_level': self.current_level,
            'level_description': self._get_level_description(self.current_level)
        }
        
        # Try to read security related DIDs
        try:
            # Read security access counter if available
            counter_response = self.ecu.send_request(0x22, 0x0202)
            if counter_response.success and len(counter_response.data) >= 4:
                status['access_counter'] = int.from_bytes(counter_response.data[2:4], 'big')
        except:
            status['access_counter'] = 'Unknown'
        
        return status
    
    def _get_level_description(self, level: int) -> str:
        """Get description for security level"""
        level_descriptions = {
            0x00: 'No Access',
            0x01: 'Default Session', 
            0x03: 'Extended Diagnostics',
            0x05: 'Programming Access',
            0x07: 'Manufacturer Level'
        }
        return level_descriptions.get(level, 'Unknown Level')