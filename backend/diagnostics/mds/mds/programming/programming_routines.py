#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDA PROGRAMMING SERVICES - Complete ECU Programming Implementation
Reverse engineered from IDS/M-MDS programming routines
"""

import struct
import time
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum, IntEnum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ProgrammingSession(IntEnum):
    """ECU Programming Session Types"""
    BOOTLOADER_ENTER = 0x01
    BOOTLOADER_EXIT = 0x02
    DOWNLOAD_REQUEST = 0x03
    DOWNLOAD_TRANSFER = 0x04
    DOWNLOAD_EXIT = 0x05
    UPLOAD_REQUEST = 0x06
    UPLOAD_TRANSFER = 0x07
    UPLOAD_EXIT = 0x08
    ROUTINE_CONTROL = 0x09

class ProgrammingState(IntEnum):
    """ECU Programming States"""
    IDLE = 0x00
    BOOTLOADER_ACTIVE = 0x01
    DOWNLOAD_ACTIVE = 0x02
    UPLOAD_ACTIVE = 0x03
    VERIFICATION_ACTIVE = 0x04
    PROGRAMMING_ACTIVE = 0x05
    COMPLETED = 0x06
    ERROR = 0x07

@dataclass
class ProgrammingBlock:
    """ECU Programming Data Block"""
    address: int
    data: bytes
    checksum: int
    block_number: int
    total_blocks: int

class MazdaProgrammingService:
    """
    Complete Mazda ECU Programming Service
    Handles all ECU programming and calibration flashing operations
    """
    
    def __init__(self, diagnostic_protocol):
        self.diagnostic_protocol = diagnostic_protocol
        self.current_state = ProgrammingState.IDLE
        self.programming_session = None
        self.security_access = None
        
    def enter_programming_mode(self) -> bool:
        """
        Enter ECU programming mode
        This switches the ECU to bootloader for programming
        """
        try:
            logger.info("Entering ECU programming mode...")
            
            # Step 1: Start extended diagnostic session
            if not self.diagnostic_protocol.start_diagnostic_session(
                self.diagnostic_protocol.DiagnosticSession.PROGRAMMING
            ):
                logger.error("Failed to start programming session")
                return False
            
            # Step 2: Security access for programming
            if not self._perform_programming_security_access():
                logger.error("Failed security access for programming")
                return False
            
            # Step 3: Request programming mode
            routine_response = self.diagnostic_protocol.routine_control(
                routine_id=0xFF00,  # Enter programming routine
                control_type=0x01,   # Start routine
                data=b'\x01'         # Programming mode
            )
            
            if not routine_response:
                logger.error("Failed to enter programming mode")
                return False
            
            self.current_state = ProgrammingState.BOOTLOADER_ACTIVE
            logger.info("Successfully entered programming mode")
            return True
            
        except Exception as e:
            logger.error(f"Error entering programming mode: {e}")
            self.current_state = ProgrammingState.ERROR
            return False
    
    def exit_programming_mode(self) -> bool:
        """
        Exit ECU programming mode and return to normal operation
        """
        try:
            logger.info("Exiting ECU programming mode...")
            
            # Exit bootloader routine
            routine_response = self.diagnostic_protocol.routine_control(
                routine_id=0xFF00,  # Exit programming routine
                control_type=0x02,   # Stop routine
                data=b'\x00'         # Exit mode
            )
            
            if not routine_response:
                logger.error("Failed to exit programming mode")
                return False
            
            # Return to default diagnostic session
            if not self.diagnostic_protocol.start_diagnostic_session(
                self.diagnostic_protocol.DiagnosticSession.DEFAULT
            ):
                logger.error("Failed to return to default session")
                return False
            
            self.current_state = ProgrammingState.IDLE
            logger.info("Successfully exited programming mode")
            return True
            
        except Exception as e:
            logger.error(f"Error exiting programming mode: {e}")
            self.current_state = ProgrammingState.ERROR
            return False
    
    def _perform_programming_security_access(self) -> bool:
        """
        Perform security access for programming operations
        """
        try:
            # Import here to avoid circular imports
            from ..security.security_algorithms import MazdaSecurityAccess, MazdaSecurityAlgorithm
            
            if not self.security_access:
                self.security_access = MazdaSecurityAccess()
            
            # Request seed for programming level
            seed = self.security_access.request_seed(
                ecu_address=0x7E0,
                security_level=2  # Programming level
            )
            
            if not seed:
                logger.error("Failed to request programming seed")
                return False
            
            # Calculate key using enhanced algorithm
            key = self.security_access.calculate_seed_key(
                seed=seed,
                algorithm=MazdaSecurityAlgorithm.ALGORITHM_27_ENHANCED
            )
            
            if not key:
                logger.error("Failed to calculate programming key")
                return False
            
            # Send key to ECU
            if not self.security_access.send_key(
                ecu_address=0x7E0,
                security_level=2,
                key=key
            ):
                logger.error("Failed to send programming key")
                return False
            
            logger.info("Programming security access successful")
            return True
            
        except Exception as e:
            logger.error(f"Error in programming security access: {e}")
            return False
    
    def download_calibration(self, calibration_data: bytes, 
                           start_address: int = 0x000000) -> bool:
        """
        Download calibration data to ECU
        
        Args:
            calibration_data: Calibration data to flash
            start_address: Starting address for programming
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Downloading calibration data ({len(calibration_data)} bytes)...")
            
            if self.current_state != ProgrammingState.BOOTLOADER_ACTIVE:
                logger.error("ECU not in programming mode")
                return False
            
            self.current_state = ProgrammingState.DOWNLOAD_ACTIVE
            
            # Calculate block size (typically 256 bytes for Mazda)
            block_size = 256
            total_blocks = (len(calibration_data) + block_size - 1) // block_size
            
            logger.info(f"Programming {total_blocks} blocks of {block_size} bytes each")
            
            # Program each block
            for block_num in range(total_blocks):
                offset = block_num * block_size
                end_offset = min(offset + block_size, len(calibration_data))
                
                block_data = calibration_data[offset:end_offset]
                
                # Create programming block
                block = ProgrammingBlock(
                    address=start_address + offset,
                    data=block_data,
                    checksum=self._calculate_block_checksum(block_data),
                    block_number=block_num + 1,
                    total_blocks=total_blocks
                )
                
                # Send block to ECU
                if not self._send_programming_block(block):
                    logger.error(f"Failed to program block {block_num + 1}")
                    self.current_state = ProgrammingState.ERROR
                    return False
                
                # Progress update
                progress = ((block_num + 1) / total_blocks) * 100
                logger.info(f"Programming progress: {progress:.1f}%")
                
                # Small delay to avoid overwhelming ECU
                time.sleep(0.01)
            
            logger.info("Calibration download completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading calibration: {e}")
            self.current_state = ProgrammingState.ERROR
            return False
    
    def _send_programming_block(self, block: ProgrammingBlock) -> bool:
        """
        Send a programming block to the ECU
        
        Args:
            block: Programming block to send
            
        Returns:
            True if successful
        """
        try:
            # Build programming request
            request_data = struct.pack('>I', block.address)  # 4-byte address
            request_data += struct.pack('>H', len(block.data))  # 2-byte length
            request_data += block.data  # Block data
            request_data += struct.pack('>H', block.checksum)  # 2-byte checksum
            
            # Send programming request
            response = self.diagnostic_protocol.routine_control(
                routine_id=0xFF01,  # Programming transfer routine
                control_type=0x03,   # Transfer data
                data=request_data
            )
            
            if not response:
                logger.error("No response to programming block")
                return False
            
            # Check response status
            if len(response) >= 1:
                status = response[0]
                if status == 0x00:
                    return True  # Success
                elif status == 0x01:
                    logger.warning("Programming block checksum error")
                    return False
                elif status == 0x02:
                    logger.error("Programming block address error")
                    return False
                elif status == 0x03:
                    logger.error("Programming block sequence error")
                    return False
            
            logger.error("Invalid programming response")
            return False
            
        except Exception as e:
            logger.error(f"Error sending programming block: {e}")
            return False
    
    def _calculate_block_checksum(self, data: bytes) -> int:
        """
        Calculate checksum for programming block
        
        Args:
            data: Block data
            
        Returns:
            Checksum value
        """
        # Mazda uses simple 16-bit checksum
        checksum = 0
        for byte in data:
            checksum = (checksum + byte) & 0xFFFF
        return checksum
    
    def verify_calibration(self, calibration_data: bytes,
                         start_address: int = 0x000000) -> bool:
        """
        Verify calibration data was programmed correctly
        
        Args:
            calibration_data: Original calibration data
            start_address: Starting address of programmed data
            
        Returns:
            True if verification successful
        """
        try:
            logger.info("Verifying programmed calibration...")
            
            self.current_state = ProgrammingState.VERIFICATION_ACTIVE
            
            # Read back programmed data
            read_data = self.diagnostic_protocol.read_memory_by_address(
                address=start_address,
                size=len(calibration_data)
            )
            
            if not read_data:
                logger.error("Failed to read back programmed data")
                return False
            
            # Compare data
            if read_data != calibration_data:
                logger.error("Verification failed - data mismatch")
                
                # Find first mismatch
                for i, (original, read) in enumerate(zip(calibration_data, read_data)):
                    if original != read:
                        logger.error(f"First mismatch at offset 0x{i:06X}: "
                                   f"expected 0x{original:02X}, got 0x{read:02X}")
                        break
                
                return False
            
            logger.info("Calibration verification successful")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying calibration: {e}")
            return False
    
    def upload_calibration(self, start_address: int, size: int) -> Optional[bytes]:
        """
        Upload calibration data from ECU
        
        Args:
            start_address: Starting address to read from
            size: Number of bytes to read
            
        Returns:
            Uploaded data or None if failed
        """
        try:
            logger.info(f"Uploading calibration data from 0x{start_address:06X} ({size} bytes)...")
            
            if self.current_state != ProgrammingState.BOOTLOADER_ACTIVE:
                logger.error("ECU not in programming mode")
                return None
            
            self.current_state = ProgrammingState.UPLOAD_ACTIVE
            
            # Read data from ECU
            data = self.diagnostic_protocol.read_memory_by_address(
                address=start_address,
                size=size
            )
            
            if not data:
                logger.error("Failed to upload calibration data")
                return None
            
            logger.info(f"Successfully uploaded {len(data)} bytes")
            return data
            
        except Exception as e:
            logger.error(f"Error uploading calibration: {e}")
            return None
    
    def reset_ecu(self) -> bool:
        """
        Reset ECU after programming
        """
        try:
            logger.info("Resetting ECU...")
            
            # Send ECU reset command
            response = self.diagnostic_protocol.routine_control(
                routine_id=0xFF02,  # ECU reset routine
                control_type=0x01,   # Start routine
                data=b'\x01'         # Reset command
            )
            
            if not response:
                logger.error("Failed to reset ECU")
                return False
            
            # Wait for ECU to reset
            time.sleep(2.0)
            
            logger.info("ECU reset successful")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting ECU: {e}")
            return False
    
    def get_programming_status(self) -> Dict[str, Any]:
        """
        Get current programming status
        
        Returns:
            Dictionary with programming status information
        """
        return {
            "state": self.current_state.name,
            "session": self.programming_session,
            "security_granted": self.security_access is not None
        }
