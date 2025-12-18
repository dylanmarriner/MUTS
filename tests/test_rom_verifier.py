"""Tests for core rom_verifier module."""
import unittest
from unittest.mock import patch

from core.rom_verifier import (
    ROMChecksumVerifier, ChecksumType, ChecksumInfo, get_rom_verifier
)


class TestChecksumType(unittest.TestCase):
    """Test ChecksumType enum."""
    
    def test_checksum_type_values(self):
        """Test ChecksumType enum values."""
        self.assertEqual(ChecksumType.CRC16.value, "crc16")
        self.assertEqual(ChecksumType.CRC32.value, "crc32")
        self.assertEqual(ChecksumType.MD5.value, "md5")
        self.assertEqual(ChecksumType.SHA256.value, "sha256")
        self.assertEqual(ChecksumType.MAZDA_PROPRIETARY.value, "mazda_proprietary")


class TestChecksumInfo(unittest.TestCase):
    """Test ChecksumInfo dataclass."""
    
    def test_checksum_info_creation(self):
        """Test ChecksumInfo creation."""
        info = ChecksumInfo(
            offset=0x0000,
            size=0x8000,
            checksum_type=ChecksumType.CRC16
        )
        
        self.assertEqual(info.offset, 0x0000)
        self.assertEqual(info.size, 0x8000)
        self.assertEqual(info.checksum_type, ChecksumType.CRC16)
        self.assertIsNone(info.expected_checksum)
        self.assertIsNone(info.calculated_checksum)
        self.assertFalse(info.is_valid)


class TestROMChecksumVerifier(unittest.TestCase):
    """Test ROMChecksumVerifier class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.verifier = ROMChecksumVerifier()
    
    def test_initialization(self):
        """Test ROMChecksumVerifier initialization."""
        self.assertIsNotNone(self.verifier.checksum_regions)
        self.assertGreater(len(self.verifier.checksum_regions), 0)
    
    def test_calculate_checksum_crc16(self):
        """Test _calculate_checksum with CRC16."""
        data = b'\x01\x02\x03\x04'
        checksum = self.verifier._calculate_checksum(data, ChecksumType.CRC16)
        
        self.assertIsNotNone(checksum)
        self.assertIsInstance(checksum, bytes)
        self.assertEqual(len(checksum), 2)  # CRC16 is 2 bytes
    
    def test_calculate_checksum_crc32(self):
        """Test _calculate_checksum with CRC32."""
        data = b'\x01\x02\x03\x04'
        checksum = self.verifier._calculate_checksum(data, ChecksumType.CRC32)
        
        self.assertIsNotNone(checksum)
        self.assertIsInstance(checksum, bytes)
        self.assertEqual(len(checksum), 4)  # CRC32 is 4 bytes
    
    def test_calculate_checksum_md5(self):
        """Test _calculate_checksum with MD5."""
        data = b'\x01\x02\x03\x04'
        checksum = self.verifier._calculate_checksum(data, ChecksumType.MD5)
        
        self.assertIsNotNone(checksum)
        self.assertIsInstance(checksum, bytes)
        self.assertEqual(len(checksum), 16)  # MD5 is 16 bytes
    
    def test_calculate_checksum_sha256(self):
        """Test _calculate_checksum with SHA256."""
        data = b'\x01\x02\x03\x04'
        checksum = self.verifier._calculate_checksum(data, ChecksumType.SHA256)
        
        self.assertIsNotNone(checksum)
        self.assertIsInstance(checksum, bytes)
        self.assertEqual(len(checksum), 32)  # SHA256 is 32 bytes
    
    def test_calculate_checksum_mazda_proprietary(self):
        """Test _calculate_checksum with MAZDA_PROPRIETARY."""
        data = b'\x01\x02\x03\x04'
        checksum = self.verifier._calculate_checksum(data, ChecksumType.MAZDA_PROPRIETARY)
        
        self.assertIsNotNone(checksum)
        self.assertIsInstance(checksum, bytes)
    
    def test_verify_rom_integrity_too_small(self):
        """Test verify_rom_integrity with ROM data that's too small."""
        small_rom = b'\xFF' * (1 * 1024 * 1024)  # 1MB - too small
        
        is_valid, results = self.verifier.verify_rom_integrity(small_rom)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(results), 0)
    
    def test_verify_rom_integrity_valid(self):
        """Test verify_rom_integrity with valid ROM data."""
        valid_rom = b'\xFF' * (2 * 1024 * 1024)  # 2MB - minimum size
        
        is_valid, results = self.verifier.verify_rom_integrity(valid_rom)
        
        # Should return results even if checksums don't match expected
        self.assertGreater(len(results), 0)
    
    def test_verify_before_flash(self):
        """Test verify_before_flash method."""
        test_rom = b'\xFF' * (2 * 1024 * 1024)  # 2MB
        
        is_safe = self.verifier.verify_before_flash(test_rom)
        
        # Should return boolean
        self.assertIsInstance(is_safe, bool)
    
    def test_verify_after_flash(self):
        """Test verify_after_flash method."""
        test_rom = b'\xFF' * (2 * 1024 * 1024)  # 2MB
        
        is_valid, results = self.verifier.verify_after_flash(test_rom)
        
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(results, list)
    
    def test_mazda_proprietary_checksum(self):
        """Test _mazda_proprietary_checksum method."""
        data = b'\x01\x02\x03\x04\x05\x06\x07\x08'
        checksum = self.verifier._mazda_proprietary_checksum(data)
        
        self.assertIsNotNone(checksum)
        self.assertIsInstance(checksum, bytes)
        self.assertEqual(len(checksum), 4)  # Should be 4 bytes
    
    def test_patch_checksums(self):
        """Test patch_checksums method."""
        test_rom = b'\xFF' * (2 * 1024 * 1024)  # 2MB minimum
        
        patched_rom, checksum_info = self.verifier.patch_checksums(test_rom)
        
        self.assertIsInstance(patched_rom, bytes)
        self.assertIsInstance(checksum_info, list)
        self.assertEqual(len(patched_rom), len(test_rom))
    
    def test_calculate_checksum_invalid_type(self):
        """Test _calculate_checksum with invalid type."""
        data = b'\x01\x02\x03\x04'
        
        # Create a mock invalid checksum type
        class InvalidChecksumType:
            pass
        
        with self.assertRaises(ValueError):
            self.verifier._calculate_checksum(data, InvalidChecksumType())


class TestGetROMVerifier(unittest.TestCase):
    """Test get_rom_verifier function."""
    
    def test_get_rom_verifier(self):
        """Test get_rom_verifier returns ROMChecksumVerifier instance."""
        verifier = get_rom_verifier()
        self.assertIsInstance(verifier, ROMChecksumVerifier)


if __name__ == '__main__':
    unittest.main()

