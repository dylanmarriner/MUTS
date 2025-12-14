"""Tests for security seed_key module."""
import unittest
import sys
from pathlib import Path

# Import using full path
sys.path.insert(0, str(Path(__file__).parent.parent))
from muts.security.seed_key import MazdaECUType, MazdaSeedKeyDatabase, bypass_security


class TestMazdaECUType(unittest.TestCase):
    """Test MazdaECUType enum."""
    
    def test_enum_values(self):
        """Test ECU type enum values."""
        self.assertEqual(MazdaECUType.ENGINE_ECU, 0x01)
        self.assertEqual(MazdaECUType.TRANSMISSION, 0x02)
        self.assertEqual(MazdaECUType.IMMOBILIZER, 0x03)
        self.assertEqual(MazdaECUType.BODY_CONTROL, 0x04)
        self.assertEqual(MazdaECUType.ABS, 0x05)
        self.assertEqual(MazdaECUType.AIRBAG, 0x06)


class TestMazdaSeedKeyDatabase(unittest.TestCase):
    """Test MazdaSeedKeyDatabase class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.db = MazdaSeedKeyDatabase()
    
    def test_initialization(self):
        """Test MazdaSeedKeyDatabase initialization."""
        self.assertIsNotNone(self.db.algorithm_database)
        self.assertIsNotNone(self.db.ecu_database)
    
    def test_initialize_algorithm_database(self):
        """Test _initialize_algorithm_database method."""
        algorithms = self.db._initialize_algorithm_database()
        
        self.assertIn('ALG_27_STANDARD', algorithms)
        self.assertIn('ENGINE_ECU_2011', algorithms)
        self.assertIn('IMMOBILIZER_2011', algorithms)
    
    def test_initialize_ecu_database(self):
        """Test _initialize_ecu_database method."""
        ecu_db = self.db._initialize_ecu_database()
        
        self.assertIn(MazdaECUType.ENGINE_ECU, ecu_db)
        self.assertIn(MazdaECUType.IMMOBILIZER, ecu_db)
        
        # Check ENGINE_ECU info
        engine_info = ecu_db[MazdaECUType.ENGINE_ECU]
        self.assertEqual(engine_info['seed_length'], 4)
        self.assertEqual(engine_info['key_length'], 4)
        self.assertFalse(engine_info['vin_required'])
    
    def test_calculate_key_standard_algorithm(self):
        """Test calculate_key with standard algorithm."""
        seed = b'\x12\x34\x56\x78'
        key = self.db.calculate_key(seed, 'ALG_27_STANDARD')
        
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 4)
        self.assertIsInstance(key, bytes)
    
    def test_calculate_key_engine_ecu_algorithm(self):
        """Test calculate_key with engine ECU algorithm."""
        seed = b'\x12\x34\x56\x78'
        key = self.db.calculate_key(seed, 'ENGINE_ECU_2011', security_level=1)
        
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 4)
        self.assertIsInstance(key, bytes)
    
    def test_calculate_key_engine_ecu_different_levels(self):
        """Test calculate_key with different security levels."""
        seed = b'\x12\x34\x56\x78'
        
        key1 = self.db.calculate_key(seed, 'ENGINE_ECU_2011', security_level=1)
        key2 = self.db.calculate_key(seed, 'ENGINE_ECU_2011', security_level=2)
        
        self.assertIsNotNone(key1)
        self.assertIsNotNone(key2)
        # Different levels should produce different keys
        self.assertNotEqual(key1, key2)
    
    def test_calculate_key_immobilizer_algorithm(self):
        """Test calculate_key with immobilizer algorithm."""
        seed = b'\x12\x34\x56\x78\x9A\xBC\xDE\xF0'
        vin = 'JM1BK123456789012'
        
        key = self.db.calculate_key(seed, 'IMMOBILIZER_2011', vin=vin)
        
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 8)
        self.assertIsInstance(key, bytes)
    
    def test_calculate_key_invalid_algorithm(self):
        """Test calculate_key with invalid algorithm."""
        seed = b'\x12\x34\x56\x78'
        key = self.db.calculate_key(seed, 'INVALID_ALGORITHM')
        
        self.assertIsNone(key)
    
    def test_algorithm_27_standard(self):
        """Test _algorithm_27_standard method."""
        seed = b'\x12\x34\x56\x78'
        key = self.db._algorithm_27_standard(seed)
        
        self.assertEqual(len(key), 4)
        self.assertIsInstance(key, bytes)
        # Same seed should produce same key
        key2 = self.db._algorithm_27_standard(seed)
        self.assertEqual(key, key2)
    
    def test_algorithm_27_standard_invalid_seed_length(self):
        """Test _algorithm_27_standard with invalid seed length."""
        seed = b'\x12\x34'  # Only 2 bytes, needs 4
        
        with self.assertRaises(ValueError):
            self.db._algorithm_27_standard(seed)
    
    def test_algorithm_engine_ecu_2011(self):
        """Test _algorithm_engine_ecu_2011 method."""
        seed = b'\x12\x34\x56\x78'
        key = self.db._algorithm_engine_ecu_2011(seed)
        
        self.assertEqual(len(key), 4)
        self.assertIsInstance(key, bytes)
    
    def test_algorithm_engine_ecu_2011_invalid_seed_length(self):
        """Test _algorithm_engine_ecu_2011 with invalid seed length."""
        seed = b'\x12\x34'  # Only 2 bytes, needs 4
        
        with self.assertRaises(ValueError):
            self.db._algorithm_engine_ecu_2011(seed)
    
    def test_algorithm_immobilizer_2011(self):
        """Test _algorithm_immobilizer_2011 method."""
        seed = b'\x12\x34\x56\x78\x9A\xBC\xDE\xF0'
        vin = 'JM1BK123456789012'
        
        key = self.db._algorithm_immobilizer_2011(seed, vin)
        
        self.assertEqual(len(key), 8)
        self.assertIsInstance(key, bytes)
    
    def test_algorithm_immobilizer_2011_invalid_seed_length(self):
        """Test _algorithm_immobilizer_2011 with invalid seed length."""
        seed = b'\x12\x34\x56\x78'  # Only 4 bytes, needs 8
        vin = 'JM1BK123456789012'
        
        with self.assertRaises(ValueError):
            self.db._algorithm_immobilizer_2011(seed, vin)
    
    def test_bypass_security_function(self):
        """Test bypass_security function."""
        # Should not raise exception
        try:
            bypass_security()
        except Exception as e:
            # If it raises, it should be a known exception type
            self.fail(f"bypass_security raised unexpected exception: {e}")


if __name__ == '__main__':
    unittest.main()

