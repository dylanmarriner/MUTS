#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3_CHECKSUM_CALCULATOR.py
DEDICATED CHECKSUM CALCULATION AND VERIFICATION
"""

import struct
import zlib
import crcmod
import hashlib
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

@dataclass
class ChecksumRegion:
    """CHECKSUM REGION DEFINITION"""
    name: str
    start: int
    end: int
    checksum_offset: int
    algorithm: str
    description: str

class ChecksumCalculator:
    """DEDICATED CHECKSUM CALCULATION FOR MAZDA ECU ROMS"""
    
    def __init__(self):
        self.regions = self._define_checksum_regions()
        self.algorithms = {
            'CRC32': self._calculate_crc32,
            'CRC16': self._calculate_crc16,
            'CRC16_CCITT': self._calculate_crc16_ccitt,
            'SUM16': self._calculate_sum16,
            'SUM32': self._calculate_sum32,
            'MD5': self._calculate_md5,
            'SHA1': self._calculate_sha1,
            'SHA256': self._calculate_sha256
        }
    
    def _define_checksum_regions(self) -> List[ChecksumRegion]:
        """DEFINE ALL CHECKSUM REGIONS IN THE ROM"""
        return [
            ChecksumRegion(
                name='boot_sector',
                start=0x000000,
                end=0x010000,
                checksum_offset=0x00FFFC,
                algorithm='CRC16_CCITT',
                description='Bootloader and security sector'
            ),
            ChecksumRegion(
                name='calibration_primary',
                start=0x010000,
                end=0x090000,
                checksum_offset=0x1FFFF0,
                algorithm='CRC32',
                description='Primary calibration tables'
            ),
            ChecksumRegion(
                name='calibration_backup',
                start=0x090000,
                end=0x110000,
                checksum_offset=0x1FFFF4,
                algorithm='CRC32',
                description='Backup calibration tables'
            ),
            ChecksumRegion(
                name='operating_system',
                start=0x110000,
                end=0x150000,
                checksum_offset=0x14FFFC,
                algorithm='CRC16_CCITT',
                description='ECU operating system'
            ),
            ChecksumRegion(
                name='fault_codes',
                start=0x150000,
                end=0x170000,
                checksum_offset=0x16FFFC,
                algorithm='SUM16',
                description='DTC storage area'
            ),
            ChecksumRegion(
                name='adaptation_data',
                start=0x170000,
                end=0x190000,
                checksum_offset=0x18FFFC,
                algorithm='SUM16',
                description='Adaptive learning data'
            ),
            ChecksumRegion(
                name='vin_storage',
                start=0x190000,
                end=0x191000,
                checksum_offset=0x190FFC,
                algorithm='CRC16',
                description='VIN and vehicle identification'
            ),
            ChecksumRegion(
                name='security_keys',
                start=0x191000,
                end=0x192000,
                checksum_offset=0x191FFC,
                algorithm='CRC16',
                description='Security keys and access codes'
            ),
            ChecksumRegion(
                name='entire_rom',
                start=0x000000,
                end=0x200000,
                checksum_offset=0x1FFFF8,
                algorithm='SHA256',
                description='Entire ROM image'
            )
        ]
    
    def calculate_region_checksum(self, rom_data: bytes, region_name: str) -> int:
        """CALCULATE CHECKSUM FOR SPECIFIC REGION"""
        region = None
        for r in self.regions:
            if r.name == region_name:
                region = r
                break
        
        if not region:
            raise ValueError(f"Unknown region: {region_name}")
        
        # Extract region data
        region_data = rom_data[region.start:region.end]
        
        # Calculate checksum
        if region.algorithm in self.algorithms:
            return self.algorithms[region.algorithm](region_data)
        else:
            raise ValueError(f"Unknown algorithm: {region.algorithm}")
    
    def calculate_all_checksums(self, rom_data: bytes) -> Dict[str, int]:
        """CALCULATE CHECKSUMS FOR ALL REGIONS"""
        checksums = {}
        
        for region in self.regions:
            try:
                checksums[region.name] = self.calculate_region_checksum(rom_data, region.name)
            except Exception as e:
                print(f"Error calculating checksum for {region.name}: {e}")
                checksums[region.name] = None
        
        return checksums
    
    def verify_region_checksum(self, rom_data: bytes, region_name: str) -> bool:
        """VERIFY CHECKSUM FOR SPECIFIC REGION"""
        region = None
        for r in self.regions:
            if r.name == region_name:
                region = r
                break
        
        if not region:
            raise ValueError(f"Unknown region: {region_name}")
        
        # Calculate checksum
        calculated = self.calculate_region_checksum(rom_data, region_name)
        
        # Extract stored checksum
        if region.algorithm in ['CRC32', 'SHA256']:
            stored = struct.unpack('>I', rom_data[region.checksum_offset:region.checksum_offset+4])[0]
        elif region.algorithm in ['MD5']:
            stored = rom_data[region.checksum_offset:region.checksum_offset+16]
        elif region.algorithm in ['SHA1']:
            stored = rom_data[region.checksum_offset:region.checksum_offset+20]
        else:
            stored = struct.unpack('>H', rom_data[region.checksum_offset:region.checksum_offset+2])[0]
        
        # Compare
        if isinstance(stored, bytes):
            calculated_bytes = calculated.to_bytes(len(stored), 'big')
            return calculated_bytes == stored
        else:
            return calculated == stored
    
    def verify_all_checksums(self, rom_data: bytes) -> Dict[str, bool]:
        """VERIFY ALL REGION CHECKSUMS"""
        results = {}
        
        for region in self.regions:
            try:
                results[region.name] = self.verify_region_checksum(rom_data, region.name)
            except Exception as e:
                print(f"Error verifying checksum for {region.name}: {e}")
                results[region.name] = False
        
        return results
    
    def patch_region_checksum(self, rom_data: bytes, region_name: str) -> bytes:
        """PATCH CHECKSUM FOR SPECIFIC REGION"""
        region = None
        for r in self.regions:
            if r.name == region_name:
                region = r
                break
        
        if not region:
            raise ValueError(f"Unknown region: {region_name}")
        
        # Calculate checksum
        calculated = self.calculate_region_checksum(rom_data, region_name)
        
        # Create patched ROM
        patched = bytearray(rom_data)
        
        # Write checksum
        if region.algorithm in ['CRC32', 'SHA256']:
            patched[region.checksum_offset:region.checksum_offset+4] = struct.pack('>I', calculated)
        elif region.algorithm in ['MD5']:
            if isinstance(calculated, bytes):
                patched[region.checksum_offset:region.checksum_offset+16] = calculated
            else:
                patched[region.checksum_offset:region.checksum_offset+16] = calculated.to_bytes(16, 'big')
        elif region.algorithm in ['SHA1']:
            if isinstance(calculated, bytes):
                patched[region.checksum_offset:region.checksum_offset+20] = calculated
            else:
                patched[region.checksum_offset:region.checksum_offset+20] = calculated.to_bytes(20, 'big')
        else:
            patched[region.checksum_offset:region.checksum_offset+2] = struct.pack('>H', calculated)
        
        return bytes(patched)
    
    def patch_all_checksums(self, rom_data: bytes) -> bytes:
        """PATCH ALL REGION CHECKSUMS"""
        patched = rom_data
        
        for region in self.regions:
            if region.name != 'entire_rom':  # Skip entire ROM as it's calculated last
                patched = self.patch_region_checksum(patched, region.name)
        
        # Finally patch entire ROM checksum
        patched = self.patch_region_checksum(patched, 'entire_rom')
        
        return patched
    
    def _calculate_crc32(self, data: bytes) -> int:
        """CALCULATE CRC32 CHECKSUM"""
        crc32_func = crcmod.predefined.mkCrcFun('crc-32')
        return crc32_func(data)
    
    def _calculate_crc16(self, data: bytes) -> int:
        """CALCULATE CRC16 CHECKSUM"""
        crc16_func = crcmod.predefined.mkCrcFun('crc-16')
        return crc16_func(data)
    
    def _calculate_crc16_ccitt(self, data: bytes) -> int:
        """CALCULATE CRC16-CCITT CHECKSUM"""
        crc16_func = crcmod.predefined.mkCrcFun('crc-ccitt-false')
        return crc16_func(data)
    
    def _calculate_sum16(self, data: bytes) -> int:
        """CALCULATE 16-BIT SUM CHECKSUM"""
        checksum = 0
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                word = struct.unpack('>H', data[i:i+2])[0]
            else:
                word = data[i] << 8
            checksum = (checksum + word) & 0xFFFF
        return checksum
    
    def _calculate_sum32(self, data: bytes) -> int:
        """CALCULATE 32-BIT SUM CHECKSUM"""
        checksum = 0
        for i in range(0, len(data), 4):
            if i + 3 < len(data):
                dword = struct.unpack('>I', data[i:i+4])[0]
            elif i + 2 < len(data):
                dword = struct.unpack('>I', data[i:i+3] + b'\x00')[0]
            elif i + 1 < len(data):
                dword = struct.unpack('>I', data[i:i+2] + b'\x00\x00')[0]
            else:
                dword = data[i] << 24
            checksum = (checksum + dword) & 0xFFFFFFFF
        return checksum
    
    def _calculate_md5(self, data: bytes) -> bytes:
        """CALCULATE MD5 HASH"""
        return hashlib.md5(data).digest()
    
    def _calculate_sha1(self, data: bytes) -> bytes:
        """CALCULATE SHA1 HASH"""
        return hashlib.sha1(data).digest()
    
    def _calculate_sha256(self, data: bytes) -> bytes:
        """CALCULATE SHA256 HASH"""
        return hashlib.sha256(data).digest()
    
    def generate_checksum_report(self, rom_data: bytes) -> str:
        """GENERATE DETAILED CHECKSUM REPORT"""
        report = []
        report.append("=" * 60)
        report.append("MAZDASPEED 3 ROM CHECKSUM REPORT")
        report.append("=" * 60)
        
        # Calculate all checksums
        checksums = self.calculate_all_checksums(rom_data)
        
        # Verify all checksums
        verification = self.verify_all_checksums(rom_data)
        
        report.append("\nCHECKSUM VERIFICATION:")
        report.append("-" * 40)
        
        for region in self.regions:
            name = region.name.upper()
            status = "✓ VALID" if verification.get(region.name, False) else "✗ INVALID"
            
            if checksums.get(region.name) is not None:
                if isinstance(checksums[region.name], bytes):
                    checksum_str = checksums[region.name].hex().upper()
                else:
                    checksum_str = f"0x{checksums[region.name]:08X}"
                
                report.append(f"{name:20} {status:10} {checksum_str}")
                report.append(f"{'':20} {region.description}")
                report.append("")
        
        # Summary
        valid_count = sum(1 for v in verification.values() if v)
        total_count = len(verification)
        
        report.append("-" * 40)
        report.append(f"SUMMARY: {valid_count}/{total_count} regions valid")
        
        if valid_count < total_count:
            report.append("\n⚠️  WARNING: Some checksums are invalid!")
            report.append("This may indicate:")
            report.append("  - Modified ROM without proper checksum patching")
            report.append("  - Corrupted ROM data")
            report.append("  - Incompatible ROM version")
        
        return "\n".join(report)
    
    def analyze_checksum_changes(self, original: bytes, modified: bytes) -> Dict[str, Dict[str, Any]]:
        """ANALYZE CHECKSUM CHANGES BETWEEN ROMS"""
        analysis = {}
        
        for region in self.regions:
            region_name = region.name
            
            # Extract region data
            orig_region = original[region.start:region.end]
            mod_region = modified[region.start:region.end]
            
            # Check if data changed
            data_changed = orig_region != mod_region
            
            # Calculate checksums
            orig_checksum = self.calculate_region_checksum(original, region_name)
            mod_checksum = self.calculate_region_checksum(modified, region_name)
            
            analysis[region_name] = {
                'data_changed': data_changed,
                'original_checksum': orig_checksum,
                'modified_checksum': mod_checksum,
                'checksum_changed': orig_checksum != mod_checksum,
                'needs_patch': data_changed and orig_checksum != mod_checksum
            }
        
        return analysis

# Utility functions
def quick_verify_rom(rom_data: bytes) -> bool:
    """QUICK ROM VERIFICATION - MAIN CHECKSUMS ONLY"""
    calculator = ChecksumCalculator()
    
    # Check main regions
    critical_regions = ['boot_sector', 'calibration_primary', 'operating_system']
    
    for region in critical_regions:
        if not calculator.verify_region_checksum(rom_data, region):
            return False
    
    return True

def create_checksum_patch(rom_data: bytes) -> bytes:
    """CREATE CHECKSUM PATCH FOR MODIFIED ROM"""
    calculator = ChecksumCalculator()
    return calculator.patch_all_checksums(rom_data)

# Demonstration
def demonstrate_checksum_calculation():
    """DEMONSTRATE CHECKSUM CALCULATION CAPABILITIES"""
    print("MAZDASPEED 3 CHECKSUM CALCULATION DEMONSTRATION")
    print("=" * 50)
    
    calculator = ChecksumCalculator()
    
    # Create dummy ROM data for demonstration
    dummy_rom = bytearray(0x200000)  # 2MB ROM
    
    # Add some test data
    dummy_rom[0x010000:0x010010] = b'TEST_CALIBRATION_DATA'
    dummy_rom[0x110000:0x110010] = b'TEST_OS_DATA'
    
    # Calculate checksums
    checksums = calculator.calculate_all_checksums(bytes(dummy_rom))
    
    print("\nCalculated Checksums:")
    for name, checksum in checksums.items():
        if checksum is not None:
            if isinstance(checksum, bytes):
                print(f"  {name}: {checksum.hex().upper()}")
            else:
                print(f"  {name}: 0x{checksum:08X}")
    
    # Generate report
    report = calculator.generate_checksum_report(bytes(dummy_rom))
    print("\n" + report)
    
    # Patch checksums
    patched = calculator.patch_all_checksums(bytes(dummy_rom))
    print(f"\nROM patched with correct checksums")
    
    print("\nChecksum calculation demonstration complete!")

if __name__ == "__main__":
    demonstrate_checksum_calculation()
