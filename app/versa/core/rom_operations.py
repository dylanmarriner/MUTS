#!/usr/bin/env python3
"""
ROM Operations Module - Handles ECU ROM reading, writing, and verification
Reverse engineered from VersaTuner ROM handling procedures
"""

import struct
import crcmod
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from .ecu_communication import ECUCommunicator, ECUResponse
from ..utils.logger import VersaLogger

@dataclass
class ROMDefinition:
    """Definition of ROM memory sectors and structure"""
    start_address: int
    size: int
    description: str
    checksum_algorithm: Optional[str] = None
    checksum_address: Optional[int] = None

class ROMOperations:
    """
    Handles all ROM-related operations including reading, writing,
    checksum calculation, and verification for Mazdaspeed 3 ECU
    """
    
    # Mazdaspeed 3 ROM structure (reverse engineered)
    ROM_STRUCTURE = {
        'boot_sector': ROMDefinition(0x000000, 0x010000, 'Bootloader and security'),
        'calibration_a': ROMDefinition(0x010000, 0x080000, 'Primary calibration tables'),
        'calibration_b': ROMDefinition(0x090000, 0x080000, 'Secondary calibration backup'),
        'operating_system': ROMDefinition(0x110000, 0x040000, 'ECU operating system'),
        'fault_memory': ROMDefinition(0x150000, 0x020000, 'DTC and freeze frame storage'),
        'adaptation_data': ROMDefinition(0x170000, 0x020000, 'Adaptive learning data'),
        'vehicle_data': ROMDefinition(0x190000, 0x001000, 'VIN and vehicle information'),
        'security_data': ROMDefinition(0x191000, 0x001000, 'Security keys and access'),
        'end_sector': ROMDefinition(0x1F0000, 0x010000, 'Checksums and validation data')
    }
    
    # Checksum algorithms
    CHECKSUM_ALGORITHMS = {
        'CRC32': {
            'polynomial': 0x04C11DB7,
            'init_value': 0xFFFFFFFF,
            'xor_out': 0xFFFFFFFF,
            'reflected': False
        },
        'CRC16_CCITT': {
            'polynomial': 0x1021,
            'init_value': 0xFFFF,
            'xor_out': 0x0000,
            'reflected': False
        },
        'SUM16': {
            'algorithm': 'sum16'
        }
    }
    
    def __init__(self, ecu_communicator: ECUCommunicator):
        """
        Initialize ROM Operations
        
        Args:
            ecu_communicator: ECUCommunicator instance for communication
        """
        self.ecu = ecu_communicator
        self.logger = VersaLogger(__name__)
        
        # Initialize checksum functions
        self.crc32_func = crcmod.mkCrcFun(
            self.CHECKSUM_ALGORITHMS['CRC32']['polynomial'],
            initCrc=self.CHECKSUM_ALGORITHMS['CRC32']['init_value'],
            xorOut=self.CHECKSUM_ALGORITHMS['CRC32']['xor_out'],
            rev=self.CHECKSUM_ALGORITHMS['CRC32']['reflected']
        )
        
        self.crc16_func = crcmod.mkCrcFun(
            self.CHECKSUM_ALGORITHMS['CRC16_CCITT']['polynomial'],
            initCrc=self.CHECKSUM_ALGORITHMS['CRC16_CCITT']['init_value'],
            xorOut=self.CHECKSUM_ALGORITHMS['CRC16_CCITT']['xor_out'],
            rev=self.CHECKSUM_ALGORITHMS['CRC16_CCITT']['reflected']
        )
    
    def read_complete_rom(self, progress_callback: Optional[callable] = None) -> Optional[bytes]:
        """
        Read complete ECU ROM to memory
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            bytes: Complete ROM data or None if failed
        """
        self.logger.info("Starting complete ROM read")
        
        rom_data = bytearray()
        total_size = sum(sector.size for sector in self.ROM_STRUCTURE.values())
        bytes_read = 0
        
        for sector_name, sector_def in self.ROM_STRUCTURE.items():
            self.logger.info(f"Reading sector: {sector_name}")
            
            sector_data = self.read_memory_range(
                sector_def.start_address, 
                sector_def.size,
                progress_callback=lambda current, total: (
                    progress_callback(bytes_read + current, total_size) 
                    if progress_callback else None
                )
            )
            
            if sector_data is None:
                self.logger.error(f"Failed to read sector: {sector_name}")
                return None
                
            rom_data.extend(sector_data)
            bytes_read += len(sector_data)
            
            if progress_callback:
                progress_callback(bytes_read, total_size)
        
        self.logger.info(f"ROM read complete: {len(rom_data)} bytes")
        return bytes(rom_data)
    
    def read_memory_range(self, start_address: int, size: int, 
                         progress_callback: Optional[callable] = None) -> Optional[bytes]:
        """
        Read memory range from ECU
        
        Args:
            start_address: Starting memory address
            size: Number of bytes to read
            progress_callback: Optional progress callback
            
        Returns:
            bytes: Memory data or None if failed
        """
        data = bytearray()
        current_address = start_address
        remaining = size
        
        # Read in chunks (ECU typically limits to 256 bytes per request)
        chunk_size = 256
        
        while remaining > 0:
            current_chunk_size = min(remaining, chunk_size)
            
            response = self.ecu.read_memory(current_address, current_chunk_size)
            
            if not response.success:
                self.logger.error(f"Failed to read memory at 0x{current_address:06X}")
                return None
                
            # Extract data from response (skip service header)
            if len(response.data) >= current_chunk_size + 1:
                chunk_data = response.data[1:1 + current_chunk_size]
                data.extend(chunk_data)
            else:
                self.logger.error(f"Invalid response length from memory read")
                return None
            
            current_address += current_chunk_size
            remaining -= current_chunk_size
            
            if progress_callback:
                progress_callback(size - remaining, size)
            
            # Small delay to avoid overwhelming ECU
            time.sleep(0.01)
        
        return bytes(data)
    
    def write_memory_range(self, start_address: int, data: bytes,
                          progress_callback: Optional[callable] = None) -> bool:
        """
        Write data to ECU memory
        
        Args:
            start_address: Starting memory address
            data: Data to write
            progress_callback: Optional progress callback
            
        Returns:
            bool: True if write successful, False otherwise
        """
        self.logger.info(f"Writing {len(data)} bytes to 0x{start_address:06X}")
        
        current_address = start_address
        bytes_written = 0
        total_bytes = len(data)
        
        # Write in chunks (ECU typically limits to 256 bytes per request)
        chunk_size = 256
        
        while bytes_written < total_bytes:
            current_chunk_size = min(total_bytes - bytes_written, chunk_size)
            chunk_data = data[bytes_written:bytes_written + current_chunk_size]
            
            # Build write request
            address_bytes = current_address.to_bytes(3, 'big')
            data_bytes = bytes([current_chunk_size]) + chunk_data
            
            response = self.ecu.send_request(0x3D, 0x00, address_bytes + data_bytes)
            
            if not response.success:
                self.logger.error(f"Failed to write memory at 0x{current_address:06X}")
                return False
            
            current_address += current_chunk_size
            bytes_written += current_chunk_size
            
            if progress_callback:
                progress_callback(bytes_written, total_bytes)
            
            # Delay to allow ECU processing
            time.sleep(0.02)
        
        self.logger.info("Memory write completed successfully")
        return True
    
    def write_complete_rom(self, rom_data: bytes, 
                          progress_callback: Optional[callable] = None) -> bool:
        """
        Write complete ROM to ECU
        
        Args:
            rom_data: Complete ROM data to write
            progress_callback: Optional progress callback
            
        Returns:
            bool: True if write successful, False otherwise
        """
        self.logger.info("Starting complete ROM write")
        
        total_size = len(rom_data)
        bytes_written = 0
        
        for sector_name, sector_def in self.ROM_STRUCTURE.items():
            self.logger.info(f"Writing sector: {sector_name}")
            
            # Extract sector data from ROM
            sector_start = sector_def.start_address
            sector_end = sector_start + sector_def.size
            
            if sector_end > total_size:
                self.logger.error(f"Sector {sector_name} exceeds ROM data size")
                return False
            
            sector_data = rom_data[sector_start:sector_end]
            
            # Write sector
            if not self.write_memory_range(sector_start, sector_data,
                                         progress_callback=lambda current, total: (
                                             progress_callback(bytes_written + current, total_size)
                                             if progress_callback else None
                                         )):
                self.logger.error(f"Failed to write sector: {sector_name}")
                return False
            
            bytes_written += len(sector_data)
        
        self.logger.info("Complete ROM write finished successfully")
        return True
    
    def verify_rom_integrity(self, rom_data: bytes) -> Dict[str, Any]:
        """
        Verify ROM integrity including checksums
        
        Args:
            rom_data: ROM data to verify
            
        Returns:
            Dict containing verification results
        """
        self.logger.info("Verifying ROM integrity")
        
        results = {
            'overall_valid': True,
            'checksums': {},
            'sector_sizes': {},
            'errors': []
        }
        
        # Verify sector sizes
        for sector_name, sector_def in self.ROM_STRUCTURE.items():
            sector_start = sector_def.start_address
            sector_end = sector_start + sector_def.size
            
            if sector_end > len(rom_data):
                results['errors'].append(f"Sector {sector_name} exceeds ROM bounds")
                results['overall_valid'] = False
            else:
                results['sector_sizes'][sector_name] = sector_def.size
        
        # Verify checksums if algorithms defined
        checksum_results = self.verify_checksums(rom_data)
        results['checksums'] = checksum_results
        
        for checksum_name, checksum_valid in checksum_results.items():
            if not checksum_valid:
                results['errors'].append(f"Checksum failed: {checksum_name}")
                results['overall_valid'] = False
        
        if results['overall_valid']:
            self.logger.info("ROM integrity verification passed")
        else:
            self.logger.warning("ROM integrity verification failed")
        
        return results
    
    def verify_checksums(self, rom_data: bytes) -> Dict[str, bool]:
        """
        Verify all checksums in ROM
        
        Args:
            rom_data: ROM data to verify
            
        Returns:
            Dict mapping checksum names to verification results
        """
        results = {}
        
        # Main calibration checksum (typically CRC32)
        calibration_data = rom_data[0x010000:0x090000]
        calculated_crc32 = self.crc32_func(calibration_data)
        
        # Read stored CRC32 from ROM
        stored_crc32 = struct.unpack('>I', rom_data[0x1FFFF0:0x1FFFF4])[0]
        results['calibration_crc32'] = (calculated_crc32 == stored_crc32)
        
        # Boot sector checksum (typically SUM16)
        boot_data = rom_data[0x000000:0x00FFFC]
        calculated_sum16 = self._calculate_sum16(boot_data)
        stored_sum16 = struct.unpack('>H', rom_data[0x00FFFC:0x00FFFE])[0]
        results['boot_sector_sum16'] = (calculated_sum16 == stored_sum16)
        
        return results
    
    def _calculate_sum16(self, data: bytes) -> int:
        """Calculate 16-bit sum checksum"""
        total = 0
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                value = (data[i] << 8) | data[i + 1]
                total = (total + value) & 0xFFFF
        return total
    
    def patch_checksums(self, rom_data: bytes) -> bytes:
        """
        Patch all checksums in ROM after modifications
        
        Args:
            rom_data: ROM data to patch
            
        Returns:
            bytes: ROM data with updated checksums
        """
        self.logger.info("Patching ROM checksums")
        
        rom_data = bytearray(rom_data)
        
        # Patch calibration CRC32
        calibration_data = rom_data[0x010000:0x090000]
        new_crc32 = self.crc32_func(calibration_data)
        rom_data[0x1FFFF0:0x1FFFF4] = struct.pack('>I', new_crc32)
        
        # Patch boot sector SUM16
        boot_data = rom_data[0x000000:0x00FFFC]
        new_sum16 = self._calculate_sum16(boot_data)
        rom_data[0x00FFFC:0x00FFFE] = struct.pack('>H', new_sum16)
        
        self.logger.info("Checksums patched successfully")
        return bytes(rom_data)
    
    def read_ecu_info(self) -> Dict[str, Any]:
        """
        Read ECU information including part numbers and calibration IDs
        
        Returns:
            Dict containing ECU information
        """
        info = {}
        
        # Read VIN
        vin = self.ecu.read_vin()
        info['vin'] = vin if vin else 'Unknown'
        
        # Read ECU part number
        part_response = self.ecu.send_request(0x22, 0xF187)
        if part_response.success and len(part_response.data) >= 19:
            info['ecu_part_number'] = part_response.data[3:19].decode('ascii', errors='ignore').strip()
        else:
            info['ecu_part_number'] = 'Unknown'
        
        # Read calibration ID
        cal_response = self.ecu.send_request(0x22, 0xF18A)
        if cal_response.success and len(cal_response.data) >= 19:
            info['calibration_id'] = cal_response.data[3:19].decode('ascii', errors='ignore').strip()
        else:
            info['calibration_id'] = 'Unknown'
        
        # Read software version
        sw_response = self.ecu.send_request(0x22, 0xF188)
        if sw_response.success and len(sw_response.data) >= 11:
            info['software_version'] = sw_response.data[3:11].decode('ascii', errors='ignore').strip()
        else:
            info['software_version'] = 'Unknown'
        
        return info
