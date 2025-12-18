#!/usr/bin/env python3
"""
Map Editor Module - Advanced map editing and manipulation tools
Provides VersaTuner-like map editing capabilities for Mazdaspeed 3
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from .map_definitions import MapDefinition, MapDefinitionManager
from ..core.rom_operations import ROMOperations
from ..utils.logger import VersaLogger

@dataclass
class MapData:
    """Container for map data and metadata"""
    definition: MapDefinition
    data: np.ndarray
    raw_bytes: bytes

class MapEditor:
    """
    Advanced map editor with VersaTuner-like functionality
    Provides map extraction, modification, and ROM patching capabilities
    """
    
    def __init__(self, rom_operations: ROMOperations):
        """
        Initialize Map Editor
        
        Args:
            rom_operations: ROMOperations instance for ROM access
        """
        self.rom_ops = rom_operations
        self.map_manager = MapDefinitionManager()
        self.logger = VersaLogger(__name__)
        self.loaded_maps: Dict[str, MapData] = {}
    
    def load_map_from_rom(self, map_name: str, rom_data: bytes) -> Optional[MapData]:
        """
        Load map data from ROM
        
        Args:
            map_name: Name of map to load
            rom_data: Complete ROM data
            
        Returns:
            MapData object or None if failed
        """
        map_def = self.map_manager.get_map(map_name)
        if not map_def:
            self.logger.error(f"Map definition not found: {map_name}")
            return None
        
        try:
            # Extract map data from ROM
            start_addr = map_def.address
            end_addr = start_addr + map_def.size
            
            if end_addr > len(rom_data):
                self.logger.error(f"Map address out of ROM bounds: {map_name}")
                return None
            
            raw_data = rom_data[start_addr:end_addr]
            
            # Convert to appropriate data structure
            map_array = self._bytes_to_array(raw_data, map_def)
            
            map_data = MapData(
                definition=map_def,
                data=map_array,
                raw_bytes=raw_data
            )
            
            self.loaded_maps[map_name] = map_data
            self.logger.info(f"Loaded map: {map_name}")
            return map_data
            
        except Exception as e:
            self.logger.error(f"Failed to load map {map_name}: {e}")
            return None
    
    def _bytes_to_array(self, raw_data: bytes, map_def: MapDefinition) -> np.ndarray:
        """Convert raw bytes to appropriate array type"""
        if map_def.type == '2D_16x16':
            return self._convert_16x16_bytes(raw_data, map_def)
        elif map_def.type == '2D_8x8':
            return self._convert_8x8_bytes(raw_data, map_def)
        elif map_def.type == '1D':
            return self._convert_1d_bytes(raw_data, map_def)
        elif map_def.type == 'Single':
            return self._convert_single_bytes(raw_data, map_def)
        else:
            raise ValueError(f"Unknown map type: {map_def.type}")
    
    def _convert_16x16_bytes(self, raw_data: bytes, map_def: MapDefinition) -> np.ndarray:
        """Convert bytes to 16x16 2D array"""
        values = []
        for i in range(0, len(raw_data), 2):
            if i + 1 < len(raw_data):
                # 16-bit values, big endian
                value = (raw_data[i] << 8) | raw_data[i + 1]
                values.append(value * map_def.conversion_factor)
        
        array = np.array(values, dtype=np.float32)
        return array.reshape(16, 16)
    
    def _convert_8x8_bytes(self, raw_data: bytes, map_def: MapDefinition) -> np.ndarray:
        """Convert bytes to 8x8 2D array"""
        values = []
        for i in range(0, len(raw_data), 2):
            if i + 1 < len(raw_data):
                # 16-bit values, big endian
                value = (raw_data[i] << 8) | raw_data[i + 1]
                values.append(value * map_def.conversion_factor)
        
        array = np.array(values, dtype=np.float32)
        return array.reshape(8, 8)
    
    def _convert_1d_bytes(self, raw_data: bytes, map_def: MapDefinition) -> np.ndarray:
        """Convert bytes to 1D array"""
        values = []
        for i in range(0, len(raw_data), 2):
            if i + 1 < len(raw_data):
                # 16-bit values, big endian
                value = (raw_data[i] << 8) | raw_data[i + 1]
                values.append(value * map_def.conversion_factor)
        
        return np.array(values, dtype=np.float32)
    
    def _convert_single_bytes(self, raw_data: bytes, map_def: MapDefinition) -> np.ndarray:
        """Convert bytes to single value"""
        if len(raw_data) >= 2:
            value = (raw_data[0] << 8) | raw_data[1]
            return np.array([value * map_def.conversion_factor], dtype=np.float32)
        return np.array([0.0], dtype=np.float32)
    
    def save_map_to_rom(self, map_name: str, rom_data: bytes) -> Optional[bytes]:
        """
        Save modified map data back to ROM
        
        Args:
            map_name: Name of map to save
            rom_data: ROM data to modify
            
        Returns:
            Modified ROM data or None if failed
        """
        if map_name not in self.loaded_maps:
            self.logger.error(f"Map not loaded: {map_name}")
            return None
        
        map_data = self.loaded_maps[map_name]
        
        try:
            # Convert array back to bytes
            new_raw_data = self._array_to_bytes(map_data.data, map_data.definition)
            
            # Update ROM data
            rom_bytes = bytearray(rom_data)
            start_addr = map_data.definition.address
            end_addr = start_addr + map_data.definition.size
            
            if end_addr > len(rom_bytes):
                self.logger.error("Map address exceeds ROM size")
                return None
            
            rom_bytes[start_addr:end_addr] = new_raw_data
            
            self.logger.info(f"Saved map to ROM: {map_name}")
            return bytes(rom_bytes)
            
        except Exception as e:
            self.logger.error(f"Failed to save map {map_name}: {e}")
            return None
    
    def _array_to_bytes(self, array: np.ndarray, map_def: MapDefinition) -> bytes:
        """Convert array back to raw bytes"""
        # Convert to engineering values
        values = array / map_def.conversion_factor
        values = np.round(values).astype(np.uint16)
        
        # Convert to bytes (big endian)
        raw_bytes = bytearray()
        for value in values.flat:
            raw_bytes.extend([(value >> 8) & 0xFF, value & 0xFF])
        
        return bytes(raw_bytes)
    
    def modify_map_value(self, map_name: str, x: int, y: int, new_value: float) -> bool:
        """
        Modify a single value in a map
        
        Args:
            map_name: Name of map
            x: X coordinate (index)
            y: Y coordinate (index)
            new_value: New value to set
            
        Returns:
            True if successful, False otherwise
        """
        if map_name not in self.loaded_maps:
            self.logger.error(f"Map not loaded: {map_name}")
            return False
        
        map_data = self.loaded_maps[map_name]
        
        try:
            # Validate coordinates
            if y >= map_data.data.shape[0] or x >= map_data.data.shape[1]:
                self.logger.error(f"Invalid coordinates for map {map_name}")
                return False
            
            # Validate value
            if new_value < map_data.definition.min_value or new_value > map_data.definition.max_value:
                self.logger.warning(f"Value {new_value} outside map limits for {map_name}")
            
            # Set value
            old_value = map_data.data[y, x]
            map_data.data[y, x] = new_value
            
            self.logger.debug(f"Modified {map_name}[{x},{y}]: {old_value} -> {new_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to modify map {map_name}: {e}")
            return False
    
    def apply_map_function(self, map_name: str, func: Callable[[float], float]) -> bool:
        """
        Apply a function to all values in a map
        
        Args:
            map_name: Name of map
            func: Function to apply to each value
            
        Returns:
            True if successful, False otherwise
        """
        if map_name not in self.loaded_maps:
            self.logger.error(f"Map not loaded: {map_name}")
            return False
        
        map_data = self.loaded_maps[map_name]
        
        try:
            # Apply function to all values
            vectorized_func = np.vectorize(func)
            map_data.data = vectorized_func(map_data.data)
            
            # Clamp values to valid range
            map_data.data = np.clip(map_data.data, 
                                   map_data.definition.min_value,
                                   map_data.definition.max_value)
            
            self.logger.info(f"Applied function to map: {map_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply function to map {map_name}: {e}")
            return False
    
    def interpolate_map(self, map_name: str, smooth_factor: float = 1.0) -> bool:
        """
        Apply smoothing interpolation to a map
        
        Args:
            map_name: Name of map to interpolate
            smooth_factor: Smoothing factor (0-1, higher = smoother)
            
        Returns:
            True if successful, False otherwise
        """
        if map_name not in self.loaded_maps:
            self.logger.error(f"Map not loaded: {map_name}")
            return False
        
        map_data = self.loaded_maps[map_name]
        
        try:
            from scipy import ndimage
            
            # Apply Gaussian smoothing
            smoothed = ndimage.gaussian_filter(map_data.data, sigma=smooth_factor)
            
            # Blend original and smoothed based on factor
            map_data.data = (map_data.data * (1 - smooth_factor) + smoothed * smooth_factor)
            
            self.logger.info(f"Interpolated map: {map_name}")
            return True
            
        except ImportError:
            self.logger.warning("scipy not available - skipping interpolation")
            return False
        except Exception as e:
            self.logger.error(f"Failed to interpolate map {map_name}: {e}")
            return False
    
    def compare_maps(self, map1_name: str, map2_name: str) -> Optional[Dict[str, Any]]:
        """
        Compare two maps and return differences
        
        Args:
            map1_name: First map name
            map2_name: Second map name
            
        Returns:
            Dictionary with comparison results or None if failed
        """
        if map1_name not in self.loaded_maps or map2_name not in self.loaded_maps:
            self.logger.error("One or both maps not loaded")
            return None
        
        map1 = self.loaded_maps[map1_name]
        map2 = self.loaded_maps[map2_name]
        
        if map1.data.shape != map2.data.shape:
            self.logger.error("Maps have different shapes")
            return None
        
        try:
            diff = map2.data - map1.data
            max_diff = np.max(np.abs(diff))
            mean_diff = np.mean(np.abs(diff))
            
            # Find locations with significant differences
            significant_diffs = np.where(np.abs(diff) > map1.definition.conversion_factor)
            
            result = {
                'map1': map1_name,
                'map2': map2_name,
                'max_difference': max_diff,
                'mean_difference': mean_diff,
                'significant_changes': len(significant_diffs[0]),
                'difference_array': diff
            }
            
            self.logger.info(f"Compared maps: {map1_name} vs {map2_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to compare maps: {e}")
            return None
    
    def export_map(self, map_name: str, filename: str, format: str = 'csv') -> bool:
        """
        Export map data to file
        
        Args:
            map_name: Name of map to export
            filename: Output filename
            format: Export format ('csv', 'json', 'txt')
            
        Returns:
            True if successful, False otherwise
        """
        if map_name not in self.loaded_maps:
            self.logger.error(f"Map not loaded: {map_name}")
            return False
        
        map_data = self.loaded_maps[map_name]
        
        try:
            if format == 'csv':
                import csv
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    if map_data.definition.x_axis:
                        writer.writerow([''] + map_data.definition.x_axis)
                    
                    # Write data
                    for i, row in enumerate(map_data.data):
                        if map_data.definition.y_axis:
                            writer.writerow([map_data.definition.y_axis[i]] + list(row))
                        else:
                            writer.writerow(list(row))
            
            elif format == 'json':
                import json
                export_data = {
                    'definition': {
                        'name': map_data.definition.name,
                        'description': map_data.definition.description,
                        'units': map_data.definition.units,
                        'x_axis': map_data.definition.x_axis,
                        'y_axis': map_data.definition.y_axis
                    },
                    'data': map_data.data.tolist()
                }
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            elif format == 'txt':
                with open(filename, 'w') as f:
                    f.write(f"Map: {map_data.definition.name}\n")
                    f.write(f"Description: {map_data.definition.description}\n")
                    f.write(f"Units: {map_data.definition.units}\n\n")
                    
                    for i, row in enumerate(map_data.data):
                        f.write(' '.join(f"{val:8.2f}" for val in row) + '\n')
            
            else:
                self.logger.error(f"Unknown export format: {format}")
                return False
            
            self.logger.info(f"Exported map {map_name} to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export map {map_name}: {e}")
            return False
