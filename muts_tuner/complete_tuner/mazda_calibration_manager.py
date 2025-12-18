#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDA CALIBRATION MANAGEMENT SYSTEM
Complete calibration operations using MDS components
Integrates with ECU core and advanced access modules
"""

import logging
import time
import struct
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import IntEnum
import numpy as np

# Import MDS components with compatibility layer
import mds_compatibility
from mds8 import MazdaCalibrationService, MapAdjustment
from mds4 import MazdaCalibrationDatabase
from mds9 import MazdaChecksumCalculator
from mds14 import MazdaDataConverter

# Use compatibility layer classes
CalibrationValidationResult = mds_compatibility.CalibrationValidationResult
ChecksumType = mds_compatibility.ChecksumType

logger = logging.getLogger(__name__)

class CalibrationType(IntEnum):
    """Calibration Types"""
    IGNITION_TIMING = 1
    FUEL_INJECTION = 2
    BOOST_CONTROL = 3
    VVT_TIMING = 4
    REV_LIMITER = 5
    SPEED_LIMITER = 6
    KNOCK_CONTROL = 7
    FUEL_TRIMS = 8

class CalibrationStatus(IntEnum):
    """Calibration Status"""
    VALID = 1
    INVALID_CHECKSUM = 2
    OUT_OF_RANGE = 3
    CORRUPTED = 4
    SECURITY_LOCKED = 5

@dataclass
class CalibrationMap:
    """Calibration Map Definition"""
    name: str
    type: CalibrationType
    address: int
    size: int
    rows: int
    columns: int
    x_axis: List[float]
    y_axis: List[float]
    data: np.ndarray
    description: str
    units: str
    min_value: float
    max_value: float
    modified: bool = False
    original_data: Optional[np.ndarray] = None

@dataclass
class CalibrationFile:
    """Complete Calibration File"""
    vehicle_info: Dict[str, str]
    calibration_data: Dict[str, CalibrationMap]
    checksums: Dict[str, int]
    timestamp: str
    version: str
    modified: bool = False

class MazdaCalibrationManager:
    """
    Complete Mazda Calibration Management System
    Handles reading, editing, validating, and writing calibrations
    """
    
    def __init__(self, ecu_core, advanced_access=None):
        self.ecu_core = ecu_core
        self.advanced_access = advanced_access
        self.calibration_database = MazdaCalibrationDatabase()
        self.checksum_calculator = MazdaChecksumCalculator()
        self.data_converter = MazdaDataConverter()
        
        # Current calibration state
        self.current_calibration = None
        self.original_calibration = None
        self.modified_maps = set()
        
        # Calibration definitions for MZR DISI engine
        self.calibration_definitions = self._initialize_calibration_definitions()
        
        logger.info("Mazda Calibration Manager initialized")
    
    def _initialize_calibration_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize calibration map definitions for MZR DISI"""
        definitions = {
            'ignition_timing_base': {
                'type': CalibrationType.IGNITION_TIMING,
                'address': 0xFFA000,
                'size': 0x800,
                'rows': 16,
                'columns': 16,
                'description': 'Base ignition timing map',
                'units': 'degrees BTDC',
                'min_value': -20.0,
                'max_value': 60.0,
                'x_axis_label': 'RPM',
                'y_axis_label': 'Load'
            },
            'ignition_timing_advance': {
                'type': CalibrationType.IGNITION_TIMING,
                'address': 0xFFA800,
                'size': 0x800,
                'rows': 16,
                'columns': 16,
                'description': 'Ignition timing advance map',
                'units': 'degrees BTDC',
                'min_value': 0.0,
                'max_value': 40.0,
                'x_axis_label': 'RPM',
                'y_axis_label': 'Load'
            },
            'fuel_injection_base': {
                'type': CalibrationType.FUEL_INJECTION,
                'address': 0xFFB000,
                'size': 0x800,
                'rows': 16,
                'columns': 16,
                'description': 'Base fuel injection map',
                'units': 'ms',
                'min_value': 0.0,
                'max_value': 50.0,
                'x_axis_label': 'RPM',
                'y_axis_label': 'Load'
            },
            'fuel_injection_compensation': {
                'type': CalibrationType.FUEL_INJECTION,
                'address': 0xFFB800,
                'size': 0x400,
                'rows': 8,
                'columns': 16,
                'description': 'Fuel injection compensation map',
                'units': 'ms',
                'min_value': -10.0,
                'max_value': 10.0,
                'x_axis_label': 'RPM',
                'y_axis_label': 'Temperature'
            },
            'boost_target': {
                'type': CalibrationType.BOOST_CONTROL,
                'address': 0xFFBC00,
                'size': 0x400,
                'rows': 8,
                'columns': 16,
                'description': 'Target boost pressure map',
                'units': 'psi',
                'min_value': 0.0,
                'max_value': 30.0,
                'x_axis_label': 'RPM',
                'y_axis_label': 'Throttle'
            },
            'boost_wastegate': {
                'type': CalibrationType.BOOST_CONTROL,
                'address': 0xFFC000,
                'size': 0x200,
                'rows': 4,
                'columns': 16,
                'description': 'Wastegate duty cycle map',
                'units': '%',
                'min_value': 0.0,
                'max_value': 100.0,
                'x_axis_label': 'RPM',
                'y_axis_label': 'Boost Error'
            },
            'vvt_intake': {
                'type': CalibrationType.VVT_TIMING,
                'address': 0xFFC200,
                'size': 0x400,
                'rows': 8,
                'columns': 16,
                'description': 'Intake VVT timing map',
                'units': 'degrees',
                'min_value': -20.0,
                'max_value': 60.0,
                'x_axis_label': 'RPM',
                'y_axis_label': 'Load'
            },
            'vvt_exhaust': {
                'type': CalibrationType.VVT_TIMING,
                'address': 0xFFC600,
                'size': 0x400,
                'rows': 8,
                'columns': 16,
                'description': 'Exhaust VVT timing map',
                'units': 'degrees',
                'min_value': -20.0,
                'max_value': 60.0,
                'x_axis_label': 'RPM',
                'y_axis_label': 'Load'
            },
            'rev_limiter': {
                'type': CalibrationType.REV_LIMITER,
                'address': 0xFFCA00,
                'size': 0x100,
                'rows': 1,
                'columns': 4,
                'description': 'RPM limiter settings',
                'units': 'RPM',
                'min_value': 1000.0,
                'max_value': 8000.0,
                'x_axis_label': 'Setting',
                'y_axis_label': 'Value'
            },
            'speed_limiter': {
                'type': CalibrationType.SPEED_LIMITER,
                'address': 0xFFCB00,
                'size': 0x100,
                'rows': 1,
                'columns': 4,
                'description': 'Speed limiter settings',
                'units': 'km/h',
                'min_value': 0.0,
                'max_value': 300.0,
                'x_axis_label': 'Setting',
                'y_axis_label': 'Value'
            }
        }
        
        logger.debug(f"Initialized {len(definitions)} calibration definitions")
        return definitions
    
    def read_full_calibration(self) -> Optional[CalibrationFile]:
        """
        Read complete calibration from ECU
        
        Returns:
            CalibrationFile object or None if failed
        """
        try:
            logger.info("Reading full calibration from ECU")
            
            if not self.ecu_core.current_connection:
                logger.error("No ECU connection available")
                return None
            
            # Read vehicle information
            vehicle_info = self.ecu_core.read_vehicle_identification()
            if not vehicle_info:
                logger.error("Failed to read vehicle information")
                return None
            
            # Read all calibration maps
            calibration_data = {}
            checksums = {}
            
            for map_name, definition in self.calibration_definitions.items():
                try:
                    logger.debug(f"Reading calibration map: {map_name}")
                    
                    # Read map data
                    map_data = self._read_calibration_map(definition)
                    if map_data:
                        calibration_data[map_name] = map_data
                        
                        # Calculate checksum for validation
                        checksums[map_name] = self._calculate_map_checksum(map_data)
                    else:
                        logger.warning(f"Failed to read calibration map: {map_name}")
                        
                except Exception as e:
                    logger.error(f"Error reading map {map_name}: {e}")
                    continue
            
            if not calibration_data:
                logger.error("No calibration data read successfully")
                return None
            
            # Create calibration file
            calibration_file = CalibrationFile(
                vehicle_info=vehicle_info,
                calibration_data=calibration_data,
                checksums=checksums,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                version="1.0",
                modified=False
            )
            
            # Store current calibration
            self.current_calibration = calibration_file
            self.original_calibration = self._deep_copy_calibration(calibration_file)
            self.modified_maps.clear()
            
            logger.info(f"Successfully read calibration with {len(calibration_data)} maps")
            return calibration_file
            
        except Exception as e:
            logger.error(f"Error reading full calibration: {e}")
            return None
    
    def _read_calibration_map(self, definition: Dict[str, Any]) -> Optional[CalibrationMap]:
        """Read individual calibration map from ECU"""
        try:
            address = definition['address']
            size = definition['size']
            rows = definition['rows']
            columns = definition['columns']
            
            # Read raw data from ECU
            if self.advanced_access:
                # Use advanced memory access
                raw_data = self.advanced_access.dump_memory_region(f"map_{address:06X}")
            else:
                # Use standard diagnostic read
                raw_data = self._read_memory_by_address(address, size)
            
            if not raw_data or len(raw_data) != size:
                logger.error(f"Failed to read map data at 0x{address:06X}")
                return None
            
            # Parse map data
            map_data = self._parse_map_data(raw_data, definition)
            if not map_data:
                return None
            
            # Create calibration map object
            calibration_map = CalibrationMap(
                name=definition['description'],
                type=definition['type'],
                address=address,
                size=size,
                rows=rows,
                columns=columns,
                x_axis=map_data['x_axis'],
                y_axis=map_data['y_axis'],
                data=map_data['data'],
                description=definition['description'],
                units=definition['units'],
                min_value=definition['min_value'],
                max_value=definition['max_value'],
                modified=False,
                original_data=map_data['data'].copy()
            )
            
            return calibration_map
            
        except Exception as e:
            logger.error(f"Error reading calibration map: {e}")
            return None
    
    def _read_memory_by_address(self, address: int, length: int) -> Optional[bytes]:
        """Read memory by address using standard diagnostics"""
        try:
            # Service 0x23 - ReadMemoryByAddress
            payload = bytearray()
            payload.extend(address.to_bytes(3, 'big'))
            payload.extend(length.to_bytes(3, 'big'))
            
            response = self.ecu_core.send_diagnostic_message('engine', 0x23, payload)
            
            if response and response[0] == 0x63:
                return response[1:]
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading memory by address: {e}")
            return None
    
    def _parse_map_data(self, raw_data: bytes, definition: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse raw map data into structured format"""
        try:
            rows = definition['rows']
            columns = definition['columns']
            map_type = definition['type']
            
            # Parse axis values
            x_axis = self._parse_axis_values(raw_data, 'x', columns)
            y_axis = self._parse_axis_values(raw_data, 'y', rows)
            
            # Parse map data
            map_data = self._parse_map_values(raw_data, map_type, rows, columns)
            
            return {
                'x_axis': x_axis,
                'y_axis': y_axis,
                'data': map_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing map data: {e}")
            return None
    
    def _parse_axis_values(self, raw_data: bytes, axis: str, count: int) -> List[float]:
        """Parse axis values from raw data"""
        try:
            # Axis values are typically stored as 16-bit integers
            axis_data = []
            
            if axis == 'x':
                # X-axis (RPM) - typically at the beginning of each row
                offset = 0
                for i in range(count):
                    value = struct.unpack('>H', raw_data[offset:offset+2])[0]
                    axis_data.append(float(value))
                    offset += 2
            else:
                # Y-axis (Load) - typically at the beginning of the data
                offset = count * 2  # Skip X-axis
                for i in range(count):
                    value = struct.unpack('>H', raw_data[offset:offset+2])[0]
                    axis_data.append(float(value))
                    offset += 2
            
            return axis_data
            
        except Exception as e:
            logger.error(f"Error parsing {axis} axis values: {e}")
            return [0.0] * count
    
    def _parse_map_values(self, raw_data: bytes, map_type: CalibrationType, 
                         rows: int, columns: int) -> np.ndarray:
        """Parse map values from raw data"""
        try:
            # Map data is typically stored as 16-bit integers
            # Skip axis data (assuming 2 bytes per axis point)
            axis_offset = (columns + rows) * 2
            
            map_data = []
            offset = axis_offset
            
            for i in range(rows * columns):
                if offset + 2 <= len(raw_data):
                    value = struct.unpack('>H', raw_data[offset:offset+2])[0]
                    
                    # Convert based on map type
                    if map_type == CalibrationType.IGNITION_TIMING:
                        # Convert to degrees BTDC
                        converted_value = float(value) / 10.0 - 20.0
                    elif map_type == CalibrationType.FUEL_INJECTION:
                        # Convert to milliseconds
                        converted_value = float(value) / 100.0
                    elif map_type == CalibrationType.BOOST_CONTROL:
                        # Convert to PSI
                        converted_value = float(value) / 10.0
                    elif map_type == CalibrationType.VVT_TIMING:
                        # Convert to degrees
                        converted_value = float(value) / 10.0 - 20.0
                    else:
                        # Default conversion
                        converted_value = float(value)
                    
                    map_data.append(converted_value)
                    offset += 2
            
            # Reshape to 2D array
            return np.array(map_data).reshape(rows, columns)
            
        except Exception as e:
            logger.error(f"Error parsing map values: {e}")
            return np.zeros((rows, columns))
    
    def _calculate_map_checksum(self, calibration_map: CalibrationMap) -> int:
        """Calculate checksum for calibration map"""
        try:
            # Convert map data back to raw format for checksum calculation
            raw_data = self._map_to_raw_data(calibration_map)
            
            # Use Mazda checksum calculator
            checksum = self.checksum_calculator.calculate_checksum(
                raw_data, ChecksumType.MAZDA_PROPRIETARY,
                calibration_map.address, calibration_map.size
            )
            
            return checksum
            
        except Exception as e:
            logger.error(f"Error calculating map checksum: {e}")
            return 0
    
    def _map_to_raw_data(self, calibration_map: CalibrationMap) -> bytes:
        """Convert calibration map back to raw data format"""
        try:
            raw_data = bytearray()
            
            # Add X-axis values
            for x_value in calibration_map.x_axis:
                raw_data.extend(struct.pack('>H', int(x_value)))
            
            # Add Y-axis values
            for y_value in calibration_map.y_axis:
                raw_data.extend(struct.pack('>H', int(y_value)))
            
            # Add map data
            flat_data = calibration_map.data.flatten()
            for value in flat_data:
                # Convert back based on map type
                if calibration_map.type == CalibrationType.IGNITION_TIMING:
                    raw_value = int((value + 20.0) * 10.0)
                elif calibration_map.type == CalibrationType.FUEL_INJECTION:
                    raw_value = int(value * 100.0)
                elif calibration_map.type == CalibrationType.BOOST_CONTROL:
                    raw_value = int(value * 10.0)
                elif calibration_map.type == CalibrationType.VVT_TIMING:
                    raw_value = int((value + 20.0) * 10.0)
                else:
                    raw_value = int(value)
                
                raw_data.extend(struct.pack('>H', raw_value))
            
            # Pad to expected size
            while len(raw_data) < calibration_map.size:
                raw_data.append(0x00)
            
            return bytes(raw_data[:calibration_map.size])
            
        except Exception as e:
            logger.error(f"Error converting map to raw data: {e}")
            return b'\x00' * calibration_map.size
    
    def modify_calibration_map(self, map_name: str, adjustments: Dict[str, Any]) -> bool:
        """
        Modify calibration map with specified adjustments
        
        Args:
            map_name: Name of map to modify
            adjustments: Adjustment parameters
            
        Returns:
            True if modification successful
        """
        try:
            if not self.current_calibration:
                logger.error("No calibration loaded")
                return False
            
            if map_name not in self.current_calibration.calibration_data:
                logger.error(f"Calibration map not found: {map_name}")
                return False
            
            calibration_map = self.current_calibration.calibration_data[map_name]
            
            # Apply adjustments based on type
            if 'offset' in adjustments:
                self._apply_offset_adjustment(calibration_map, adjustments['offset'])
            
            if 'scaling' in adjustments:
                self._apply_scaling_adjustment(calibration_map, adjustments['scaling'])
            
            if 'interpolation' in adjustments:
                self._apply_interpolation_adjustment(calibration_map, adjustments['interpolation'])
            
            if 'custom_values' in adjustments:
                self._apply_custom_values(calibration_map, adjustments['custom_values'])
            
            # Validate modified map
            validation_result = self._validate_calibration_map(calibration_map)
            if validation_result.status != CalibrationStatus.VALID:
                logger.error(f"Modified map validation failed: {validation_result.message}")
                return False
            
            # Update map status
            calibration_map.modified = True
            self.modified_maps.add(map_name)
            self.current_calibration.modified = True
            
            logger.info(f"Successfully modified calibration map: {map_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error modifying calibration map {map_name}: {e}")
            return False
    
    def _apply_offset_adjustment(self, calibration_map: CalibrationMap, offset: float):
        """Apply offset adjustment to map values"""
        try:
            calibration_map.data += offset
            
            # Clamp to valid range
            calibration_map.data = np.clip(
                calibration_map.data,
                calibration_map.min_value,
                calibration_map.max_value
            )
            
        except Exception as e:
            logger.error(f"Error applying offset adjustment: {e}")
    
    def _apply_scaling_adjustment(self, calibration_map: CalibrationMap, scaling: float):
        """Apply scaling adjustment to map values"""
        try:
            calibration_map.data *= scaling
            
            # Clamp to valid range
            calibration_map.data = np.clip(
                calibration_map.data,
                calibration_map.min_value,
                calibration_map.max_value
            )
            
        except Exception as e:
            logger.error(f"Error applying scaling adjustment: {e}")
    
    def _apply_interpolation_adjustment(self, calibration_map: CalibrationMap, 
                                      interpolation_points: List[Tuple[float, float, float]]):
        """Apply interpolation-based adjustment"""
        try:
            for rpm, load, value in interpolation_points:
                # Find nearest grid point and adjust
                rpm_idx = self._find_nearest_axis_index(calibration_map.x_axis, rpm)
                load_idx = self._find_nearest_axis_index(calibration_map.y_axis, load)
                
                if 0 <= rpm_idx < calibration_map.columns and 0 <= load_idx < calibration_map.rows:
                    calibration_map.data[load_idx, rpm_idx] = value
            
        except Exception as e:
            logger.error(f"Error applying interpolation adjustment: {e}")
    
    def _apply_custom_values(self, calibration_map: CalibrationMap, 
                           custom_values: np.ndarray):
        """Apply custom values to map"""
        try:
            if custom_values.shape == calibration_map.data.shape:
                calibration_map.data = custom_values.copy()
            else:
                logger.error("Custom values array shape mismatch")
            
        except Exception as e:
            logger.error(f"Error applying custom values: {e}")
    
    def _find_nearest_axis_index(self, axis: List[float], value: float) -> int:
        """Find nearest index in axis array"""
        try:
            return min(range(len(axis)), key=lambda i: abs(axis[i] - value))
        except:
            return 0
    
    def _validate_calibration_map(self, calibration_map: CalibrationMap) -> CalibrationValidationResult:
        """Validate calibration map"""
        try:
            # Check for NaN or infinite values
            if np.any(np.isnan(calibration_map.data)) or np.any(np.isinf(calibration_map.data)):
                return CalibrationValidationResult(
                    status=CalibrationStatus.CORRUPTED,
                    message="Map contains invalid values (NaN or infinite)"
                )
            
            # Check value ranges
            if np.any(calibration_map.data < calibration_map.min_value) or \
               np.any(calibration_map.data > calibration_map.max_value):
                return CalibrationValidationResult(
                    status=CalibrationStatus.OUT_OF_RANGE,
                    message=f"Values exceed valid range [{calibration_map.min_value}, {calibration_map.max_value}]"
                )
            
            # Check for reasonable gradients (no sudden jumps)
            if calibration_map.rows > 1 and calibration_map.columns > 1:
                gradients = np.gradient(calibration_map.data)
                max_gradient = np.max(np.abs(gradients))
                
                # Define reasonable max gradient based on map type
                if calibration_map.type == CalibrationType.IGNITION_TIMING:
                    max_allowed = 15.0  # degrees per cell
                elif calibration_map.type == CalibrationType.FUEL_INJECTION:
                    max_allowed = 10.0  # ms per cell
                elif calibration_map.type == CalibrationType.BOOST_CONTROL:
                    max_allowed = 5.0   # psi per cell
                else:
                    max_allowed = 20.0
                
                if max_gradient > max_allowed:
                    return CalibrationValidationResult(
                        status=CalibrationStatus.OUT_OF_RANGE,
                        message=f"Excessive gradient detected: {max_gradient:.2f} (max: {max_allowed})"
                    )
            
            return CalibrationValidationResult(
                status=CalibrationStatus.VALID,
                message="Map validation passed"
            )
            
        except Exception as e:
            logger.error(f"Error validating calibration map: {e}")
            return CalibrationValidationResult(
                status=CalibrationStatus.CORRUPTED,
                message=f"Validation error: {str(e)}"
            )
    
    def write_calibration_to_ecu(self) -> bool:
        """
        Write modified calibration back to ECU
        
        Returns:
            True if write successful
        """
        try:
            if not self.current_calibration:
                logger.error("No calibration loaded")
                return False
            
            if not self.modified_maps:
                logger.info("No modifications to write")
                return True
            
            logger.info(f"Writing {len(self.modified_maps)} modified maps to ECU")
            
            # Check security access
            if self.advanced_access:
                if self.advanced_access.current_security_level < 3:
                    logger.info("Requesting programming security access")
                    if not self.advanced_access.request_security_access(SecurityLevel.LEVEL_3):
                        logger.error("Failed to obtain programming security access")
                        return False
            
            # Write each modified map
            for map_name in self.modified_maps:
                calibration_map = self.current_calibration.calibration_data[map_name]
                
                logger.info(f"Writing map: {map_name}")
                
                # Convert map to raw data
                raw_data = self._map_to_raw_data(calibration_map)
                
                # Write to ECU
                if self.advanced_access:
                    success = self.advanced_access.write_memory_region(
                        f"map_{calibration_map.address:06X}", raw_data
                    )
                else:
                    success = self._write_memory_by_address(
                        calibration_map.address, raw_data
                    )
                
                if not success:
                    logger.error(f"Failed to write map: {map_name}")
                    return False
                
                # Update checksum
                if not self._update_map_checksum(calibration_map):
                    logger.error(f"Failed to update checksum for: {map_name}")
                    return False
            
            # Clear modified maps
            self.modified_maps.clear()
            self.current_calibration.modified = False
            
            logger.info("Calibration successfully written to ECU")
            return True
            
        except Exception as e:
            logger.error(f"Error writing calibration to ECU: {e}")
            return False
    
    def _write_memory_by_address(self, address: int, data: bytes) -> bool:
        """Write memory by address using standard diagnostics"""
        try:
            # Service 0x3D - WriteMemoryByAddress
            payload = bytearray()
            payload.extend(address.to_bytes(3, 'big'))
            payload.extend(len(data).to_bytes(3, 'big'))
            payload.extend(data)
            
            response = self.ecu_core.send_diagnostic_message('engine', 0x3D, payload)
            
            if response and response[0] == 0x7D:
                return response[1] == 0x00
            
            return False
            
        except Exception as e:
            logger.error(f"Error writing memory by address: {e}")
            return False
    
    def _update_map_checksum(self, calibration_map: CalibrationMap) -> bool:
        """Update checksum for modified map"""
        try:
            # Calculate new checksum
            new_checksum = self._calculate_map_checksum(calibration_map)
            
            # Write checksum to ECU
            checksum_address = 0xFFFFF0  # Checksum area
            checksum_data = struct.pack('>I', new_checksum)
            
            if self.advanced_access:
                success = self.advanced_access.write_memory_region(
                    'checksum_area', checksum_data
                )
            else:
                success = self._write_memory_by_address(checksum_address, checksum_data)
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating map checksum: {e}")
            return False
    
    def _deep_copy_calibration(self, calibration: CalibrationFile) -> CalibrationFile:
        """Create deep copy of calibration"""
        try:
            # Deep copy calibration data
            new_calibration_data = {}
            for name, map_obj in calibration.calibration_data.items():
                new_map = CalibrationMap(
                    name=map_obj.name,
                    type=map_obj.type,
                    address=map_obj.address,
                    size=map_obj.size,
                    rows=map_obj.rows,
                    columns=map_obj.columns,
                    x_axis=map_obj.x_axis.copy(),
                    y_axis=map_obj.y_axis.copy(),
                    data=map_obj.data.copy(),
                    description=map_obj.description,
                    units=map_obj.units,
                    min_value=map_obj.min_value,
                    max_value=map_obj.max_value,
                    modified=map_obj.modified,
                    original_data=map_obj.original_data.copy() if map_obj.original_data is not None else None
                )
                new_calibration_data[name] = new_map
            
            return CalibrationFile(
                vehicle_info=calibration.vehicle_info.copy(),
                calibration_data=new_calibration_data,
                checksums=calibration.checksums.copy(),
                timestamp=calibration.timestamp,
                version=calibration.version,
                modified=calibration.modified
            )
            
        except Exception as e:
            logger.error(f"Error creating deep copy of calibration: {e}")
            return None
    
    def generate_performance_tune(self, stage: str = "1") -> Dict[str, Any]:
        """
        Generate performance tune based on stage
        
        Args:
            stage: Tune stage ("1", "2", "3")
            
        Returns:
            Dictionary of map adjustments
        """
        try:
            if not self.current_calibration:
                logger.error("No calibration loaded")
                return {}
            
            logger.info(f"Generating Stage {stage} performance tune")
            
            adjustments = {}
            
            if stage == "1":
                # Stage 1: Conservative increases
                adjustments.update({
                    'ignition_timing_base': {'offset': 2.0},
                    'boost_target': {'offset': 2.0},
                    'fuel_injection_base': {'scaling': 1.05}
                })
            elif stage == "2":
                # Stage 2: Moderate increases
                adjustments.update({
                    'ignition_timing_base': {'offset': 4.0},
                    'boost_target': {'offset': 4.0},
                    'fuel_injection_base': {'scaling': 1.10},
                    'rev_limiter': {'custom_values': np.array([[7000, 7200, 7400, 7500]])}
                })
            elif stage == "3":
                # Stage 3: Aggressive increases
                adjustments.update({
                    'ignition_timing_base': {'offset': 6.0},
                    'boost_target': {'offset': 6.0},
                    'fuel_injection_base': {'scaling': 1.15},
                    'rev_limiter': {'custom_values': np.array([[7500, 7700, 7900, 8000]])},
                    'speed_limiter': {'custom_values': np.array([[0, 0, 0, 0]])}  # Remove speed limiter
                })
            
            logger.info(f"Generated Stage {stage} tune with {len(adjustments)} adjustments")
            return adjustments
            
        except Exception as e:
            logger.error(f"Error generating performance tune: {e}")
            return {}
    
    def get_calibration_summary(self) -> Dict[str, Any]:
        """Get summary of current calibration"""
        try:
            if not self.current_calibration:
                return {}
            
            summary = {
                'vehicle_info': self.current_calibration.vehicle_info,
                'total_maps': len(self.current_calibration.calibration_data),
                'modified_maps': len(self.modified_maps),
                'timestamp': self.current_calibration.timestamp,
                'version': self.current_calibration.version,
                'maps': {}
            }
            
            for name, map_obj in self.current_calibration.calibration_data.items():
                summary['maps'][name] = {
                    'name': map_obj.name,
                    'type': map_obj.type.name,
                    'size': map_obj.size,
                    'rows': map_obj.rows,
                    'columns': map_obj.columns,
                    'units': map_obj.units,
                    'modified': map_obj.modified,
                    'min_value': float(np.min(map_obj.data)),
                    'max_value': float(np.max(map_obj.data)),
                    'avg_value': float(np.mean(map_obj.data))
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting calibration summary: {e}")
            return {}
    
    def save_calibration_to_file(self, filename: str) -> bool:
        """Save calibration to file"""
        try:
            if not self.current_calibration:
                logger.error("No calibration to save")
                return False
            
            # Convert calibration to serializable format
            calibration_dict = {
                'vehicle_info': self.current_calibration.vehicle_info,
                'checksums': self.current_calibration.checksums,
                'timestamp': self.current_calibration.timestamp,
                'version': self.current_calibration.version,
                'modified': self.current_calibration.modified,
                'maps': {}
            }
            
            for name, map_obj in self.current_calibration.calibration_data.items():
                calibration_dict['maps'][name] = {
                    'name': map_obj.name,
                    'type': map_obj.type.value,
                    'address': map_obj.address,
                    'size': map_obj.size,
                    'rows': map_obj.rows,
                    'columns': map_obj.columns,
                    'x_axis': map_obj.x_axis.tolist(),
                    'y_axis': map_obj.y_axis.tolist(),
                    'data': map_obj.data.tolist(),
                    'description': map_obj.description,
                    'units': map_obj.units,
                    'min_value': map_obj.min_value,
                    'max_value': map_obj.max_value,
                    'modified': map_obj.modified
                }
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(calibration_dict, f, indent=2)
            
            logger.info(f"Calibration saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving calibration to file: {e}")
            return False
    
    def load_calibration_from_file(self, filename: str) -> bool:
        """Load calibration from file"""
        try:
            with open(filename, 'r') as f:
                calibration_dict = json.load(f)
            
            # Reconstruct calibration objects
            calibration_data = {}
            
            for name, map_dict in calibration_dict['maps'].items():
                calibration_map = CalibrationMap(
                    name=map_dict['name'],
                    type=CalibrationType(map_dict['type']),
                    address=map_dict['address'],
                    size=map_dict['size'],
                    rows=map_dict['rows'],
                    columns=map_dict['columns'],
                    x_axis=map_dict['x_axis'],
                    y_axis=map_dict['y_axis'],
                    data=np.array(map_dict['data']),
                    description=map_dict['description'],
                    units=map_dict['units'],
                    min_value=map_dict['min_value'],
                    max_value=map_dict['max_value'],
                    modified=map_dict['modified'],
                    original_data=np.array(map_dict['data'])
                )
                calibration_data[name] = calibration_map
            
            # Create calibration file
            calibration_file = CalibrationFile(
                vehicle_info=calibration_dict['vehicle_info'],
                calibration_data=calibration_data,
                checksums=calibration_dict['checksums'],
                timestamp=calibration_dict['timestamp'],
                version=calibration_dict['version'],
                modified=calibration_dict['modified']
            )
            
            self.current_calibration = calibration_file
            self.original_calibration = self._deep_copy_calibration(calibration_file)
            
            # Update modified maps
            self.modified_maps.clear()
            for name, map_obj in calibration_data.items():
                if map_obj.modified:
                    self.modified_maps.add(name)
            
            logger.info(f"Calibration loaded from {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading calibration from file: {e}")
            return False
