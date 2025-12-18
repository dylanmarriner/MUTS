"""
ECU Flash Management System
Handles reading, writing, and verifying ECU flash memory
Includes brick protection and recovery mechanisms
"""

import struct
import hashlib
import crcmod
import time
from typing import Optional, Tuple

class FlashManager:
    """
    ECU Flash Memory Management
    Handles complete flash operations with safety checks
    """
    
    def __init__(self, ecu):
        self.ecu = ecu
        self.flash_in_progress = False
        self.verify_checksums = True
        self.backup_before_flash = True
        
        # CRC function for flash verification
        self.crc16 = crcmod.predefined.mkCrcFun('crc-16')
        
    def read_entire_rom(self, output_file: str) -> bool:
        """
        Read entire ECU ROM to file
        Useful for backup and reverse engineering
        """
        try:
            with open(output_file, 'wb') as f:
                # Read ROM in chunks
                chunk_size = 256
                total_size = 0x80000  # 512KB ROM
                
                for address in range(0, total_size, chunk_size):
                    data = self.ecu.can.read_memory(address, chunk_size)
                    if data:
                        f.write(data)
                    else:
                        print(f"Failed to read at address {hex(address)}")
                        return False
                        
                    # Progress indicator
                    if address % 0x4000 == 0:
                        progress = (address / total_size) * 100
                        print(f"Reading ROM: {progress:.1f}%")
                        
            print(f"[+] ROM dumped to {output_file}")
            return True
            
        except Exception as e:
            print(f"ROM dump failed: {e}")
            return False
    
    def flash_calibration_file(self, calibration_file: str, verify: bool = True) -> bool:
        """
        Flash calibration file to ECU with safety checks
        """
        if self.flash_in_progress:
            print("Flash already in progress")
            return False
            
        self.flash_in_progress = True
        
        try:
            # Step 1: Backup current calibration
            if self.backup_before_flash:
                backup_file = f"backup_{int(time.time())}.bin"
                if not self._backup_calibration(backup_file):
                    print("Backup failed - aborting flash")
                    return False
            
            # Step 2: Enter flash mode
            if not self._enter_flash_mode():
                print("Failed to enter flash mode")
                return False
            
            # Step 3: Parse and validate calibration file
            calibration_blocks = self._parse_calibration_file(calibration_file)
            if not calibration_blocks:
                print("Invalid calibration file")
                return False
            
            # Step 4: Flash each block
            total_blocks = len(calibration_blocks)
            for i, block in enumerate(calibration_blocks):
                print(f"Flashing block {i+1}/{total_blocks}...")
                
                if not self._flash_block(block['address'], block['data']):
                    print(f"Failed to flash block at {hex(block['address'])}")
                    return False
                
                # Step 5: Verify block if requested
                if verify and not self._verify_block(block['address'], block['data']):
                    print(f"Verification failed for block at {hex(block['address'])}")
                    return False
            
            # Step 6: Exit flash mode
            if not self._exit_flash_mode():
                print("Warning: Failed to exit flash mode cleanly")
            
            print("[+] Calibration flash completed successfully")
            return True
            
        except Exception as e:
            print(f"Flash operation failed: {e}")
            return False
            
        finally:
            self.flash_in_progress = False
    
    def _enter_flash_mode(self) -> bool:
        """Enter ECU flash programming mode"""
        # Send flash mode entry sequence
        entry_sequence = [
            bytes([0x10, 0x02]),  # Start diagnostic session
            bytes([0x27, 0x05]),  # Security access level 5
            bytes([0x31, 0x01, 0xFF, 0x00]),  # Start routine
        ]
        
        for cmd in entry_sequence:
            self.ecu.can.send_can_message(0x7E0, cmd)
            response = self.ecu.can.receive_can_message(1.0)
            
            if not response or response.data[0] != 0x7F:
                return False
                
            time.sleep(0.1)
            
        return True
    
    def _exit_flash_mode(self) -> bool:
        """Exit ECU flash programming mode"""
        exit_sequence = [
            bytes([0x31, 0x02]),  # Stop routine
            bytes([0x10, 0x01]),  # Return to default session
        ]
        
        for cmd in exit_sequence:
            self.ecu.can.send_can_message(0x7E0, cmd)
            time.sleep(0.1)
            
        return True
    
    def _backup_calibration(self, backup_file: str) -> bool:
        """Backup current calibration to file"""
        try:
            calibration_dump = self.ecu.dump_full_calibration()
            
            with open(backup_file, 'wb') as f:
                # Write backup header
                header = struct.pack('<8sII', b'MS3BACKUP', 0x01, len(calibration_dump))
                f.write(header)
                
                # Write each calibration table
                for table_name, data in calibration_dump.items():
                    table_header = struct.pack('<32sI', table_name.encode('ascii'), len(data))
                    f.write(table_header)
                    f.write(data)
            
            print(f"[+] Calibration backed up to {backup_file}")
            return True
            
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
    
    def _parse_calibration_file(self, filename: str) -> list:
        """Parse calibration file format"""
        try:
            with open(filename, 'rb') as f:
                data = f.read()
                
            # Check file format
            if data[:4] == b'CTM1':
                return self._parse_ctm_format(data)
            elif data[:8] == b'MS3BACKUP':
                return self._parse_backup_format(data)
            else:
                # Assume raw binary with embedded addresses
                return self._parse_raw_binary(data)
                
        except Exception as e:
            print(f"File parsing failed: {e}")
            return []
    
    def _parse_ctm_format(self, data: bytes) -> list:
        """Parse Cobb CTM file format"""
        blocks = []
        offset = 4  # Skip CTM1 header
        
        while offset < len(data):
            if offset + 8 > len(data):
                break
                
            address, block_size = struct.unpack('>II', data[offset:offset+8])
            offset += 8
            
            if offset + block_size > len(data):
                break
                
            block_data = data[offset:offset+block_size]
            offset += block_size
            
            blocks.append({
                'address': address,
                'data': block_data,
                'checksum': self.crc16(block_data)
            })
            
        return blocks
    
    def _parse_backup_format(self, data: bytes) -> list:
        """Parse backup file format"""
        blocks = []
        offset = 16  # Skip header
        
        while offset < len(data):
            if offset + 36 > len(data):
                break
                
            table_name = data[offset:offset+32].decode('ascii').strip('\x00')
            block_size = struct.unpack('<I', data[offset+32:offset+36])[0]
            offset += 36
            
            if offset + block_size > len(data):
                break
                
            block_data = data[offset:offset+block_size]
            offset += block_size
            
            # Convert table name to address
            address = self.ecu.CALIBRATION_TABLES.get(table_name, 0)
            if address:
                blocks.append({
                    'address': address,
                    'data': block_data,
                    'checksum': self.crc16(block_data)
                })
                
        return blocks
    
    def _flash_block(self, address: int, data: bytes) -> bool:
        """Flash a single memory block"""
        # Split large blocks into smaller chunks
        chunk_size = 128
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            
            if not self.ecu.can.write_memory(address + i, chunk):
                return False
                
            # Small delay between chunks
            time.sleep(0.01)
            
        return True
    
    def _verify_block(self, address: int, expected_data: bytes) -> bool:
        """Verify flashed block matches expected data"""
        read_data = self.ecu.can.read_memory(address, len(expected_data))
        
        if not read_data:
            return False
            
        # Compare data
        if read_data != expected_data:
            print(f"Data mismatch at {hex(address)}")
            return False
            
        # Verify checksum
        if self.verify_checksums:
            expected_crc = self.crc16(expected_data)
            actual_crc = self.crc16(read_data)
            
            if expected_crc != actual_crc:
                print(f"Checksum mismatch at {hex(address)}")
                return False
                
        return True
    
    def recover_bricked_ecu(self, backup_file: str) -> bool:
        """
        Attempt to recover a bricked ECU using backup file
        Uses bootloader recovery mode
        """
        print("[*] Attempting ECU recovery...")
        
        # Force bootloader mode
        recovery_sequence = [
            bytes([0x10, 0x02]),  # Diagnostic session
            bytes([0x11, 0x01]),  # ECU reset
        ]
        
        for cmd in recovery_sequence:
            self.ecu.can.send_can_message(0x7E0, cmd)
            time.sleep(1.0)
            
        # Try to flash backup
        return self.flash_calibration_file(backup_file, verify=True)
