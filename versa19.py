#!/usr/bin/env python3
"""
Unit Tests for Map Operations
Comprehensive testing of map editing and manipulation functionality
"""

import unittest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tuning.map_definitions import MapDefinitionManager, MapDefinition
from src.tuning.map_editor import MapEditor, MapData
from src.core.rom_operations import ROMOperations
from unittest.mock import Mock, patch

class TestMapDefinitions(unittest.TestCase):
    """Test cases for map definition management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.map_manager = MapDefinitionManager()
    
    def test_map_definitions_loaded(self):
        """Test that map definitions are properly loaded"""
        definitions = self.map_manager.map_definitions
        
        # Verify we have maps in major categories
        self.assertIn('ignition_primary', definitions)
        self.assertIn('fuel_primary', definitions)
        self.assertIn('boost_target', definitions)
        self.assertIn('vvt_intake_advance', definitions)
        
        # Verify map properties
        ignition_map = definitions['ignition_primary']
        self.assertEqual(ignition_map.name, 'Primary Ignition Timing')
        self.assertEqual(ignition_map.address, 0x012000)
        self.assertEqual(ignition_map.type, '2D_16x16')
        self.assertEqual(ignition_map.units, 'degrees')
    
    def test_get_maps_by_category(self):
        """Test retrieving maps by category"""
        ignition_maps = self.map_manager.get_maps_by_category('Ignition')
        
        # Should have multiple ignition maps
        self.assertGreater(len(ignition_maps), 3)
        
        # All should be ignition-related
        for map_def in ignition_maps:
            self.assertEqual(map_def.category, 'Ignition')
    
    def test_validate_map_value(self):
        """Test map value validation"""
        # Test valid value
        self.assertTrue(self.map_manager.validate_map_value('ignition_primary', 15.0))
        
        # Test value below minimum
        self.assertFalse(self.map_manager.validate_map_value('ignition_primary', -5.0))
        
        # Test value above maximum
        self.assertFalse(self.map_manager.validate_map_value('ignition_primary', 30.0))
        
        # Test unknown map
        self.assertFalse(self.map_manager.validate_map_value('unknown_map', 10.0))

class TestMapEditor(unittest.TestCase):
    """Test cases for map editing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rom_ops_mock = Mock(spec=ROMOperations)
        self.map_editor = MapEditor(self.rom_ops_mock)
        
        # Create sample ROM data
        self.sample_rom = self._create_sample_rom_data()
    
    def _create_sample_rom_data(self) -> bytes:
        """Create sample ROM data for testing"""
        # Create 2MB ROM filled with zeros
        rom_data = bytearray(0x200000)
        
        # Add some test map data at known addresses
        # Ignition map at 0x012000 (16x16, 2 bytes per value)
        ignition_data = bytearray()
        for i in range(16*16):
            value = 150 + i  # 15.0 degrees in 0.1 units
            ignition_data.extend(value.to_bytes(2, 'big'))
        rom_data[0x012000:0x012000+len(ignition_data)] = ignition_data
        
        # Boost map at 0x014000 (16x16, 2 bytes per value)
        boost_data = bytearray()
        for i in range(16*16):
            value = 180 + i  # 18.0 PSI in 0.1 units
            boost_data.extend(value.to_bytes(2, 'big'))
        rom_data[0x014000:0x014000+len(boost_data)] = boost_data
        
        return bytes(rom_data)
    
    def test_load_map_from_rom(self):
        """Test loading map data from ROM"""
        map_data = self.map_editor.load_map_from_rom('ignition_primary', self.sample_rom)
        
        self.assertIsNotNone(map_data)
        self.assertEqual(map_data.definition.name, 'Primary Ignition Timing')
        self.assertEqual(map_data.data.shape, (16, 16))
        
        # Verify data was converted correctly (150 = 15.0 degrees)
        self.assertAlmostEqual(map_data.data[0, 0], 15.0)
    
    def test_modify_map_value(self):
        """Test modifying individual map values"""
        # Load a map first
        map_data = self.map_editor.load_map_from_rom('ignition_primary', self.sample_rom)
        original_value = map_data.data[0, 0]
        
        # Modify a value
        success = self.map_editor.modify_map_value('ignition_primary', 0, 0, 18.0)
        
        self.assertTrue(success)
        self.assertEqual(map_data.data[0, 0], 18.0)
    
    def test_modify_map_value_validation(self):
        """Test map value modification with validation"""
        # Load a map first
        self.map_editor.load_map_from_rom('ignition_primary', self.sample_rom)
        
        # Try to set value outside valid range
        success = self.map_editor.modify_map_value('ignition_primary', 0, 0, 30.0)
        
        # Should fail due to validation
        self.assertFalse(success)
    
    def test_apply_global_adjustment(self):
        """Test applying global adjustments to maps"""
        # Load a map first
        self.map_editor.load_map_from_rom('ignition_primary', self.sample_rom)
        map_data = self.map_editor.loaded_maps['ignition_primary']
        original_values = map_data.data.copy()
        
        # Apply global adjustment
        success = self.map_editor.apply_global_adjustment('ignition_primary', 2.0)
        
        self.assertTrue(success)
        
        # Verify all values were adjusted
        for i in range(map_data.data.shape[0]):
            for j in range(map_data.data.shape[1]):
                self.assertEqual(map_data.data[i, j], original_values[i, j] + 2.0)
    
    def test_generate_patch_rom(self):
        """Test generating patched ROM with modified maps"""
        # Load and modify a map
        self.map_editor.load_map_from_rom('ignition_primary', self.sample_rom)
        self.map_editor.modify_map_value('ignition_primary', 0, 0, 18.0)
        
        # Generate patched ROM
        patched_rom = self.map_editor.generate_patch_rom(self.sample_rom)
        
        # Verify ROM was modified
        self.assertNotEqual(patched_rom, self.sample_rom)
        
        # Load the map from patched ROM to verify changes
        new_map_data = self.map_editor.load_map_from_rom('ignition_primary', patched_rom)
        self.assertEqual(new_map_data.data[0, 0], 18.0)
    
    def test_create_performance_tune(self):
        """Test creating performance tunes"""
        # Create stage 1 tune
        tuned_rom = self.map_editor.create_performance_tune(self.sample_rom, 30)
        
        self.assertIsNotNone(tuned_rom)
        self.assertNotEqual(tuned_rom, self.sample_rom)
        
        # Load tuned maps to verify changes
        self.map_editor.load_map_from_rom('ignition_primary', tuned_rom)
        self.map_editor.load_map_from_rom('boost_target', tuned_rom)
        
        # Verify adjustments were applied
        ignition_data = self.map_editor.loaded_maps['ignition_primary']
        boost_data = self.map_editor.loaded_maps['boost_target']
        
        # Should have increased values for performance
        self.assertGreater(np.mean(ignition_data.data), 15.0)
        self.assertGreater(np.mean(boost_data.data), 18.0)

class TestMapDataConversion(unittest.TestCase):
    """Test cases for map data conversion between bytes and arrays"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rom_ops_mock = Mock(spec=ROMOperations)
        self.map_editor = MapEditor(self.rom_ops_mock)
    
    def test_16x16_conversion(self):
        """Test 16x16 map conversion to and from bytes"""
        # Create test array
        test_array = np.array([[i + j * 0.1 for i in range(16)] for j in range(16)])
        
        # Convert to bytes
        map_def = MapDefinition(
            name='test_map', address=0x1000, size=512, type='2D_16x16',
            description='Test map', units='test', conversion_factor=0.1,
            min_value=0.0, max_value=20.0
        )
        
        bytes_data = self.map_editor._convert_16x16_array(test_array, map_def)
        
        # Convert back to array
        new_array = self.map_editor._convert_16x16_bytes(bytes_data, map_def)
        
        # Should be approximately equal (within conversion precision)
        np.testing.assert_array_almost_equal(test_array, new_array, decimal=1)
    
    def test_1d_conversion(self):
        """Test 1D map conversion to and from bytes"""
        # Create test array
        test_array = np.array([i * 0.5 for i in range(8)])
        
        # Convert to bytes
        map_def = MapDefinition(
            name='test_1d_map', address=0x2000, size=16, type='1D',
            description='Test 1D map', units='test', conversion_factor=0.1,
            min_value=0.0, max_value=10.0
        )
        
        bytes_data = self.map_editor._convert_1d_array(test_array, map_def)
        
        # Convert back to array
        new_array = self.map_editor._convert_1d_bytes(bytes_data, map_def)
        
        # Should be approximately equal
        np.testing.assert_array_almost_equal(test_array, new_array, decimal=1)

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)