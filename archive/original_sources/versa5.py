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
                raw_value = struct.unpack('>H', raw_data[i:i+2])[0]
                physical_value = raw_value * map_def.conversion_factor
                values.append(physical_value)
        
        return np.array(values).reshape(16, 16)
    
    def _convert_8x8_bytes(self, raw_data: bytes, map_def: MapDefinition) -> np.ndarray:
        """Convert bytes to 8x8 2D array"""
        values = []
        for i in range(0, len(raw_data), 2):
            if i + 1 < len(raw_data):
                raw_value = struct.unpack('>H', raw_data[i:i+2])[0]
                physical_value = raw_value * map_def.conversion_factor
                values.append(physical_value)
        
        return np.array(values).reshape(8, 8)
    
    def _convert_1d_bytes(self, raw_data: bytes, map_def: MapDefinition) -> np.ndarray:
        """Convert bytes to 1D array"""
        values = []
        for i in range(0, len(raw_data), 2):
            if i + 1 < len(raw_data):
                raw_value = struct.unpack('>H', raw_data[i:i+2])[0]
                physical_value = raw_value * map_def.conversion_factor
                values.append(physical_value)
        
        return np.array(values)
    
    def _convert_single_bytes(self, raw_data: bytes, map_def: MapDefinition) -> np.ndarray:
        """Convert bytes to single value array"""
        if len(raw_data) >= 2:
            raw_value = struct.unpack('>H', raw_data[:2])[0]
            physical_value = raw_value * map_def.conversion_factor
            return np.array([physical_value])
        return np.array([0.0])
    
    def modify_map_value(self, map_name: str, x_index: int, y_index: int, 
                        new_value: float, validate: bool = True) -> bool:
        """
        Modify a single value in a map
        
        Args:
            map_name: Name of map to modify
            x_index: X-axis index
            y_index: Y-axis index (for 2D maps)
            new_value: New value to set
            validate: Whether to validate value range
            
        Returns:
            bool: True if modification successful
        """
        if map_name not in self.loaded_maps:
            self.logger.error(f"Map not loaded: {map_name}")
            return False
        
        map_data = self.loaded_maps[map_name]
        
        # Validate value range
        if validate and not self.map_manager.validate_map_value(map_name, new_value):
            self.logger.error(f"Value {new_value} outside valid range for {map_name}")
            return False
        
        try:
            # Update the value
            if len(map_data.data.shape) == 2:  # 2D map
                map_data.data[y_index, x_index] = new_value
            elif len(map_data.data.shape) == 1:  # 1D map
                map_data.data[x_index] = new_value
            else:  # Single value
                map_data.data[0] = new_value
            
            self.logger.debug(f"Modified {map_name}[{x_index},{y_index}] = {new_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to modify map value: {e}")
            return False
    
    def apply_global_adjustment(self, map_name: str, adjustment: float, 
                              condition: Optional[Callable] = None) -> bool:
        """
        Apply global adjustment to map values
        
        Args:
            map_name: Name of map to adjust
            adjustment: Value to add to all elements
            condition: Optional condition function to filter which values to adjust
            
        Returns:
            bool: True if adjustment successful
        """
        if map_name not in self.loaded_maps:
            self.logger.error(f"Map not loaded: {map_name}")
            return False
        
        map_data = self.loaded_maps[map_name]
        
        try:
            # Apply adjustment with optional condition
            if condition:
                mask = condition(map_data.data)
                map_data.data[mask] += adjustment
            else:
                map_data.data += adjustment
            
            # Clamp to valid range
            map_def = map_data.definition
            map_data.data = np.clip(map_data.data, map_def.min_value, map_def.max_value)
            
            self.logger.info(f"Applied global adjustment of {adjustment} to {map_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply global adjustment: {e}")
            return False
    
    def interpolate_map(self, map_name: str, new_x_axis: List[float], 
                       new_y_axis: List[float]) -> bool:
        """
        Interpolate map to new axis scales
        
        Args:
            map_name: Name of map to interpolate
            new_x_axis: New x-axis values
            new_y_axis: New y-axis values
            
        Returns:
            bool: True if interpolation successful
        """
        if map_name not in self.loaded_maps:
            self.logger.error(f"Map not loaded: {map_name}")
            return False
        
        map_data = self.loaded_maps[map_name]
        map_def = map_data.definition
        
        if len(map_data.data.shape) != 2:
            self.logger.error("Interpolation only supported for 2D maps")
            return False
        
        try:
            from scipy.interpolate import interp2d
            import scipy
            
            # Create interpolation function
            old_x = map_def.x_axis if map_def.x_axis else list(range(map_data.data.shape[1]))
            old_y = map_def.y_axis if map_def.y_axis else list(range(map_data.data.shape[0]))
            
            interp_func = interp2d(old_x, old_y, map_data.data, kind='linear')
            
            # Interpolate to new grid
            new_data = interp_func(new_x_axis, new_y_axis)
            map_data.data = new_data
            
            # Update axis definitions
            map_def.x_axis = new_x_axis
            map_def.y_axis = new_y_axis
            
            self.logger.info(f"Interpolated {map_name} to new axis scales")
            return True
            
        except ImportError:
            self.logger.error("Scipy required for map interpolation")
            return False
        except Exception as e:
            self.logger.error(f"Map interpolation failed: {e}")
            return False
    
    def generate_patch_rom(self, rom_data: bytes) -> bytes:
        """
        Generate patched ROM with all modified maps
        
        Args:
            rom_data: Original ROM data
            
        Returns:
            bytes: Patched ROM data
        """
        self.logger.info("Generating patched ROM with modified maps")
        
        patched_rom = bytearray(rom_data)
        
        for map_name, map_data in self.loaded_maps.items():
            if not self._has_map_changed(map_data):
                continue
            
            # Convert modified data back to bytes
            new_bytes = self._array_to_bytes(map_data)
            
            # Patch into ROM
            start_addr = map_data.definition.address
            patched_rom[start_addr:start_addr + len(new_bytes)] = new_bytes
            
            self.logger.info(f"Patched {map_name} into ROM")
        
        return bytes(patched_rom)
    
    def _has_map_changed(self, map_data: MapData) -> bool:
        """Check if map data has been modified"""
        current_bytes = self._array_to_bytes(map_data)
        return current_bytes != map_data.raw_bytes
    
    def _array_to_bytes(self, map_data: MapData) -> bytes:
        """Convert array back to bytes for ROM patching"""
        map_def = map_data.definition
        data_array = map_data.data
        
        if map_def.type == '2D_16x16':
            return self._convert_16x16_array(data_array, map_def)
        elif map_def.type == '2D_8x8':
            return self._convert_8x8_array(data_array, map_def)
        elif map_def.type == '1D':
            return self._convert_1d_array(data_array, map_def)
        elif map_def.type == 'Single':
            return self._convert_single_array(data_array, map_def)
        else:
            raise ValueError(f"Unknown map type: {map_def.type}")
    
    def _convert_16x16_array(self, data_array: np.ndarray, map_def: MapDefinition) -> bytes:
        """Convert 16x16 array to bytes"""
        bytes_data = bytearray()
        flat_data = data_array.flatten()
        
        for value in flat_data:
            raw_value = int(value / map_def.conversion_factor)
            raw_value = max(0, min(0xFFFF, raw_value))  # Clamp to 16-bit range
            bytes_data.extend(struct.pack('>H', raw_value))
        
        return bytes(bytes_data)
    
    def _convert_8x8_array(self, data_array: np.ndarray, map_def: MapDefinition) -> bytes:
        """Convert 8x8 array to bytes"""
        bytes_data = bytearray()
        flat_data = data_array.flatten()
        
        for value in flat_data:
            raw_value = int(value / map_def.conversion_factor)
            raw_value = max(0, min(0xFFFF, raw_value))
            bytes_data.extend(struct.pack('>H', raw_value))
        
        return bytes(bytes_data)
    
    def _convert_1d_array(self, data_array: np.ndarray, map_def: MapDefinition) -> bytes:
        """Convert 1D array to bytes"""
        bytes_data = bytearray()
        
        for value in data_array:
            raw_value = int(value / map_def.conversion_factor)
            raw_value = max(0, min(0xFFFF, raw_value))
            bytes_data.extend(struct.pack('>H', raw_value))
        
        return bytes(bytes_data)
    
    def _convert_single_array(self, data_array: np.ndarray, map_def: MapDefinition) -> bytes:
        """Convert single value array to bytes"""
        value = data_array[0]
        raw_value = int(value / map_def.conversion_factor)
        raw_value = max(0, min(0xFFFF, raw_value))
        return struct.pack('>H', raw_value)
    
    def create_performance_tune(self, rom_data: bytes, power_target: int) -> bytes:
        """
        Create performance tune based on power target
        
        Args:
            rom_data: Original ROM data
            power_target: Target horsepower increase
            
        Returns:
            bytes: Tuned ROM data
        """
        self.logger.info(f"Creating performance tune for +{power_target}HP target")
        
        # Load key performance maps
        key_maps = [
            'ignition_primary', 'ignition_high_octane',
            'boost_target', 'fuel_primary'
        ]
        
        for map_name in key_maps:
            self.load_map_from_rom(map_name, rom_data)
        
        # Apply tune based on power target
        if power_target <= 50:
            self._apply_stage1_tune()
        elif power_target <= 100:
            self._apply_stage2_tune()
        else:
            self._apply_stage3_tune()
        
        # Generate patched ROM
        tuned_rom = self.generate_patch_rom(rom_data)
        tuned_rom = self.rom_ops.patch_checksums(tuned_rom)
        
        self.logger.info("Performance tune created successfully")
        return tuned_rom
    
    def _apply_stage1_tune(self):
        """Apply Stage 1 tune (mild performance)"""
        # Slightly increased boost
        self.apply_global_adjustment('boost_target', 2.0)  # +2 PSI
        
        # Mild ignition advance
        self.apply_global_adjustment('ignition_primary', 1.0)
        self.apply_global_adjustment('ignition_high_octane', 1.5)
        
        # Slightly richer WOT
        self.modify_map_value('fuel_primary', 12, 12, 0.82)  # Richer at high load/RPM
    
    def _apply_stage2_tune(self):
        """Apply Stage 2 tune (medium performance)"""
        # Moderate boost increase
        self.apply_global_adjustment('boost_target', 4.0)  # +4 PSI
        
        # Aggressive ignition advance
        self.apply_global_adjustment('ignition_primary', 2.0)
        self.apply_global_adjustment('ignition_high_octane', 3.0)
        
        # Richer mixture for safety
        self.modify_map_value('fuel_primary', 12, 12, 0.80)
        
        # Increase rev limit
        rev_limit_data = self.load_map_from_rom('rev_limit_soft', b'')
        if rev_limit_data:
            self.modify_map_value('rev_limit_soft', 0, 0, 7200)
    
    def _apply_stage3_tune(self):
        """Apply Stage 3 tune (high performance)"""
        # High boost levels
        self.apply_global_adjustment('boost_target', 6.0)  # +6 PSI
        
        # Maximum safe ignition advance
        self.apply_global_adjustment('ignition_primary', 3.0)
        self.apply_global_adjustment('ignition_high_octane', 4.0)
        
        # Aggressive fueling
        self.modify_map_value('fuel_primary', 12, 12, 0.78)
        
        # Higher rev limit
        rev_limit_data = self.load_map_from_rom('rev_limit_soft', b'')
        if rev_limit_data:
            self.modify_map_value('rev_limit_soft', 0, 0, 7500)
        
        # Remove speed limiter
        speed_limit_data = self.load_map_from_rom('speed_limit', b'')
        if speed_limit_data:
            self.modify_map_value('speed_limit', 0, 0, 300)