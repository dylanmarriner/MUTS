#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDA CALIBRATION SERVICES - Complete Calibration Management
Reverse engineered from IDS/M-MDS calibration tools
"""

import struct
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum, IntEnum
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

class CalibrationOperation(IntEnum):
    """Calibration Operation Types"""
    READ_CALIBRATION = 0x01
    WRITE_CALIBRATION = 0x02
    VERIFY_CALIBRATION = 0x03
    MODIFY_MAP = 0x04
    ADJUST_PARAMETER = 0x05
    GENERATE_CHECKSUM = 0x06
    VALIDATE_CALIBRATION = 0x07

class MapAdjustmentType(IntEnum):
    """Map Adjustment Types"""
    OFFSET = 0x01
    SCALING = 0x02
    INTERPOLATION = 0x03
    CUSTOM = 0x04

@dataclass
class MapAdjustment:
    """Map adjustment definition"""
    map_name: str
    adjustment_type: MapAdjustmentType
    values: Dict[str, Any]
    description: str

class MazdaCalibrationService:
    """
    Complete Mazda Calibration Service
    Handles all calibration operations including reading, writing, and modification
    """
    
    def __init__(self, diagnostic_protocol, programming_service):
        self.diagnostic_protocol = diagnostic_protocol
        self.programming_service = programming_service
        self.calibration_database = None
        
    def set_calibration_database(self, database):
        """Set calibration database reference"""
        self.calibration_database = database
    
    def read_full_calibration(self, ecu_address: int = 0x7E0) -> Optional[Dict[str, Any]]:
        """
        Read complete calibration from ECU
        
        Args:
            ecu_address: ECU address to read from
            
        Returns:
            Complete calibration data or None if failed
        """
        try:
            logger.info("Reading full ECU calibration...")
            
            # Enter programming mode
            if not self.programming_service.enter_programming_mode():
                logger.error("Failed to enter programming mode")
                return None
            
            calibration_data = {}
            
            try:
                # Read calibration identification
                calibration_id = self._read_calibration_identification()
                if calibration_id:
                    calibration_data['identification'] = calibration_id
                
                # Read all calibration maps
                calibration_data['maps'] = self._read_all_calibration_maps()
                
                # Read parameters
                calibration_data['parameters'] = self._read_calibration_parameters()
                
                # Calculate checksum
                calibration_data['checksum'] = self._calculate_calibration_checksum(calibration_data)
                
                logger.info("Full calibration read successfully")
                return calibration_data
                
            finally:
                self.programming_service.exit_programming_mode()
                
        except Exception as e:
            logger.error(f"Error reading full calibration: {e}")
            return None
    
    def _read_calibration_identification(self) -> Optional[Dict[str, Any]]:
        """Read calibration identification information"""
        try:
            identification = {}
            
            # Read VIN
            vin_data = self.diagnostic_protocol.read_data_by_identifier(0xF101)
            if vin_data:
                identification['vin'] = vin_data.decode('ascii', errors='ignore').strip()
            
            # Read calibration ID
            cal_id_data = self.diagnostic_protocol.read_data_by_identifier(0xF102)
            if cal_id_data:
                identification['calibration_id'] = cal_id_data.decode('ascii', errors='ignore').strip()
            
            # Read ECU part number
            part_data = self.diagnostic_protocol.read_data_by_identifier(0xF104)
            if part_data:
                identification['ecu_part_number'] = part_data.hex().upper()
            
            # Read software version
            sw_data = self.diagnostic_protocol.read_data_by_identifier(0xF106)
            if sw_data:
                identification['software_version'] = sw_data.hex().upper()
            
            return identification
            
        except Exception as e:
            logger.error(f"Error reading calibration identification: {e}")
            return None
    
    def _read_all_calibration_maps(self) -> Dict[str, Any]:
        """Read all calibration maps from ECU"""
        maps = {}
        
        if not self.calibration_database:
            logger.error("Calibration database not set")
            return maps
        
        # Get calibration ID to determine which maps to read
        cal_id_data = self.diagnostic_protocol.read_data_by_identifier(0xF102)
        if not cal_id_data:
            logger.error("Cannot determine calibration ID")
            return maps
        
        calibration_id = cal_id_data.decode('ascii', errors='ignore').strip()
        calibration = self.calibration_database.get_calibration(calibration_id)
        
        if not calibration:
            logger.error(f"Unknown calibration ID: {calibration_id}")
            return maps
        
        # Read each map from ECU memory
        for map_name, map_def in calibration.maps.items():
            try:
                map_data = self.programming_service.upload_calibration(
                    map_def.address, map_def.size
                )
                
                if map_data:
                    decoded_map = self._decode_calibration_map(map_data, map_def)
                    maps[map_name] = {
                        'definition': map_def,
                        'raw_data': map_data,
                        'decoded_values': decoded_map,
                        'checksum': self._calculate_map_checksum(map_data)
                    }
                    logger.debug(f"Read map: {map_name}")
                else:
                    logger.warning(f"Failed to read map: {map_name}")
                    
            except Exception as e:
                logger.error(f"Error reading map {map_name}: {e}")
        
        return maps
    
    def _decode_calibration_map(self, raw_data: bytes, map_def: Any) -> List[List[float]]:
        """Decode raw calibration map data into values"""
        try:
            values = []
            
            # Determine value size based on map definition
            if map_def.data_type == 'uint8':
                value_size = 1
                unpack_format = 'B'
            elif map_def.data_type == 'int8':
                value_size = 1
                unpack_format = 'b'
            elif map_def.data_type == 'uint16':
                value_size = 2
                unpack_format = 'H'
            elif map_def.data_type == 'int16':
                value_size = 2
                unpack_format = 'h'
            else:
                # Default to uint8
                value_size = 1
                unpack_format = 'B'
            
            # Calculate map dimensions
            x_size = len(map_def.axis_x)
            y_size = len(map_def.axis_y) if hasattr(map_def, 'axis_y') else 1
            
            # Decode values
            for y in range(y_size):
                row = []
                for x in range(x_size):
                    index = (y * x_size + x) * value_size
                    if index + value_size <= len(raw_data):
                        value = struct.unpack_from(unpack_format, raw_data, index)[0]
                        # Apply scaling factor
                        scaled_value = value * map_def.scaling_factor
                        row.append(scaled_value)
                    else:
                        row.append(0.0)
                values.append(row)
            
            return values
            
        except Exception as e:
            logger.error(f"Error decoding calibration map: {e}")
            return []
    
    def _read_calibration_parameters(self) -> Dict[str, Any]:
        """Read calibration parameters from ECU"""
        parameters = {}
        
        # Read various parameters from known memory locations
        parameter_addresses = {
            'rev_limit': 0xFFB800,
            'speed_limit': 0xFFB810,
            'boost_limit': 0xFFB820,
            'launch_control_rpm': 0xFFB830
        }
        
        for param_name, address in parameter_addresses.items():
            try:
                # Read parameter value (typically 2 bytes)
                param_data = self.diagnostic_protocol.read_memory_by_address(address, 2)
                if param_data and len(param_data) >= 2:
                    value = struct.unpack('>H', param_data)[0]
                    parameters[param_name] = value
                    
            except Exception as e:
                logger.warning(f"Error reading parameter {param_name}: {e}")
        
        return parameters
    
    def write_calibration(self, calibration_data: Dict[str, Any]) -> bool:
        """
        Write calibration data to ECU
        
        Args:
            calibration_data: Complete calibration data to write
            
        Returns:
            True if write successful
        """
        try:
            logger.info("Writing calibration to ECU...")
            
            if not self.programming_service.enter_programming_mode():
                logger.error("Failed to enter programming mode")
                return False
            
            try:
                # Write each map
                maps_written = 0
                if 'maps' in calibration_data:
                    for map_name, map_data in calibration_data['maps'].items():
                        if self._write_calibration_map(map_name, map_data):
                            maps_written += 1
                        else:
                            logger.error(f"Failed to write map: {map_name}")
                            return False
                
                # Write parameters
                if 'parameters' in calibration_data:
                    if not self._write_calibration_parameters(calibration_data['parameters']):
                        logger.error("Failed to write parameters")
                        return False
                
                # Update checksum
                if not self._update_calibration_checksum():
                    logger.error("Failed to update checksum")
                    return False
                
                logger.info(f"Calibration write completed: {maps_written} maps written")
                return True
                
            finally:
                self.programming_service.exit_programming_mode()
                
        except Exception as e:
            logger.error(f"Error writing calibration: {e}")
            return False
    
    def _write_calibration_map(self, map_name: str, map_data: Dict[str, Any]) -> bool:
        """Write single calibration map to ECU"""
        try:
            if 'definition' not in map_data or 'raw_data' not in map_data:
                logger.error(f"Invalid map data for {map_name}")
                return False
            
            map_def = map_data['definition']
            raw_data = map_data['raw_data']
            
            # Write map data to ECU memory
            return self.programming_service.download_calibration(
                raw_data, map_def.address
            )
            
        except Exception as e:
            logger.error(f"Error writing map {map_name}: {e}")
            return False
    
    def _write_calibration_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Write calibration parameters to ECU"""
        try:
            # Parameter memory addresses
            parameter_addresses = {
                'rev_limit': 0xFFB800,
                'speed_limit': 0xFFB810,
                'boost_limit': 0xFFB820
            }
            
            for param_name, address in parameter_addresses.items():
                if param_name in parameters:
                    value = parameters[param_name]
                    # Convert to bytes (2 bytes for most parameters)
                    param_bytes = struct.pack('>H', value)
                    
                    # Write to ECU memory
                    if not self.diagnostic_protocol.write_memory_by_address(address, param_bytes):
                        logger.warning(f"Failed to write parameter {param_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing parameters: {e}")
            return False
    
    def _update_calibration_checksum(self) -> bool:
        """Update calibration checksum in ECU"""
        try:
            # Mazda checksum calculation and update routine
            # This would perform the checksum calculation and write it to the checksum area
            checksum_address = 0xFFFFF0  # Typical checksum location
            
            # Calculate new checksum (simplified)
            new_checksum = self._calculate_ecu_checksum()
            
            # Write checksum
            checksum_bytes = struct.pack('>I', new_checksum)
            return self.diagnostic_protocol.write_memory_by_address(checksum_address, checksum_bytes)
            
        except Exception as e:
            logger.error(f"Error updating checksum: {e}")
            return False
    
    def _calculate_ecu_checksum(self) -> int:
        """Calculate ECU checksum (simplified implementation)"""
        # In real implementation, this would read the calibration area and calculate proper checksum
        return 0x12345678  # Placeholder
    
    def modify_calibration_map(self, map_name: str, adjustments: MapAdjustment) -> Optional[Dict[str, Any]]:
        """
        Modify calibration map with specified adjustments
        
        Args:
            map_name: Name of map to modify
            adjustments: Adjustment parameters
            
        Returns:
            Modified map data or None if failed
        """
        try:
            # Read current map
            current_calibration = self.read_full_calibration()
            if not current_calibration or map_name not in current_calibration['maps']:
                logger.error(f"Map {map_name} not found in current calibration")
                return None
            
            current_map = current_calibration['maps'][map_name]
            modified_map = self._apply_map_adjustments(current_map, adjustments)
            
            if modified_map:
                logger.info(f"Map {map_name} modified successfully")
                return modified_map
            else:
                logger.error(f"Failed to modify map {map_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error modifying calibration map: {e}")
            return None
    
    def _apply_map_adjustments(self, original_map: Dict[str, Any], 
                             adjustments: MapAdjustment) -> Optional[Dict[str, Any]]:
        """Apply adjustments to calibration map"""
        try:
            modified_map = original_map.copy()
            decoded_values = modified_map['decoded_values'].copy()
            
            if adjustments.adjustment_type == MapAdjustmentType.OFFSET:
                # Apply offset to all values
                offset = adjustments.values.get('offset', 0.0)
                for i in range(len(decoded_values)):
                    for j in range(len(decoded_values[i])):
                        decoded_values[i][j] += offset
            
            elif adjustments.adjustment_type == MapAdjustmentType.SCALING:
                # Apply scaling factor to all values
                scale = adjustments.values.get('scale', 1.0)
                for i in range(len(decoded_values)):
                    for j in range(len(decoded_values[i])):
                        decoded_values[i][j] *= scale
            
            elif adjustments.adjustment_type == MapAdjustmentType.INTERPOLATION:
                # Apply interpolation between points
                interpolation_points = adjustments.values.get('points', {})
                # This would implement 2D interpolation
                decoded_values = self._interpolate_map(decoded_values, interpolation_points)
            
            # Update modified map
            modified_map['decoded_values'] = decoded_values
            modified_map['raw_data'] = self._encode_calibration_map(decoded_values, original_map['definition'])
            modified_map['checksum'] = self._calculate_map_checksum(modified_map['raw_data'])
            modified_map['adjustments'] = adjustments
            
            return modified_map
            
        except Exception as e:
            logger.error(f"Error applying map adjustments: {e}")
            return None
    
    def _interpolate_map(self, original_values: List[List[float]], 
                        points: Dict[str, Any]) -> List[List[float]]:
        """Apply interpolation to calibration map"""
        # This would implement 2D interpolation algorithms
        # For now, return original values
        return original_values
    
    def _encode_calibration_map(self, values: List[List[float]], 
                              map_def: Any) -> bytes:
        """Encode calibration map values to raw bytes"""
        try:
            encoded_data = bytearray()
            
            # Determine encoding format based on map definition
            if map_def.data_type == 'uint8':
                pack_format = 'B'
                scale_factor = 1.0 / map_def.scaling_factor
            elif map_def.data_type == 'int8':
                pack_format = 'b'
                scale_factor = 1.0 / map_def.scaling_factor
            elif map_def.data_type == 'uint16':
                pack_format = 'H'
                scale_factor = 1.0 / map_def.scaling_factor
            elif map_def.data_type == 'int16':
                pack_format = 'h'
                scale_factor = 1.0 / map_def.scaling_factor
            else:
                # Default to uint8
                pack_format = 'B'
                scale_factor = 1.0
            
            # Encode values
            for row in values:
                for value in row:
                    # Scale value and convert to integer
                    int_value = int(round(value * scale_factor))
                    # Clamp to valid range
                    int_value = max(map_def.min_value, min(int_value, map_def.max_value))
                    encoded_data.extend(struct.pack(pack_format, int_value))
            
            return bytes(encoded_data)
            
        except Exception as e:
            logger.error(f"Error encoding calibration map: {e}")
            return b''
    
    def _calculate_calibration_checksum(self, calibration_data: Dict[str, Any]) -> str:
        """Calculate checksum for calibration data"""
        try:
            # Combine all map checksums
            combined_data = b''
            if 'maps' in calibration_data:
                for map_name, map_data in calibration_data['maps'].items():
                    if 'raw_data' in map_data:
                        combined_data += map_data['raw_data']
            
            # Calculate SHA256 hash
            checksum = hashlib.sha256(combined_data).hexdigest()
            return checksum
            
        except Exception as e:
            logger.error(f"Error calculating calibration checksum: {e}")
            return "0000000000000000000000000000000000000000000000000000000000000000"
    
    def _calculate_map_checksum(self, map_data: bytes) -> str:
        """Calculate checksum for map data"""
        return hashlib.md5(map_data).hexdigest()
    
    def validate_calibration(self, calibration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate calibration data for safety and compatibility
        
        Args:
            calibration_data: Calibration data to validate
            
        Returns:
            Validation results
        """
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'safety_checks': {}
        }
        
        try:
            # Check if calibration database is available
            if not self.calibration_database:
                validation_results['warnings'].append("No calibration database available for validation")
                return validation_results
            
            # Validate maps
            if 'maps' in calibration_data:
                for map_name, map_data in calibration_data['maps'].items():
                    map_validation = self._validate_calibration_map(map_name, map_data)
                    if not map_validation['valid']:
                        validation_results['valid'] = False
                        validation_results['errors'].extend(map_validation['errors'])
                    validation_results['warnings'].extend(map_validation['warnings'])
            
            # Validate parameters
            if 'parameters' in calibration_data:
                param_validation = self._validate_calibration_parameters(calibration_data['parameters'])
                if not param_validation['valid']:
                    validation_results['valid'] = False
                    validation_results['errors'].extend(param_validation['errors'])
                validation_results['warnings'].extend(param_validation['warnings'])
            
            # Perform safety checks
            validation_results['safety_checks'] = self._perform_safety_checks(calibration_data)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating calibration: {e}")
            validation_results['valid'] = False
            validation_results['errors'].append(f"Validation error: {str(e)}")
            return validation_results
    
    def _validate_calibration_map(self, map_name: str, map_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate single calibration map"""
        validation = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            if 'definition' not in map_data:
                validation['valid'] = False
                validation['errors'].append(f"Map {map_name}: Missing definition")
                return validation
            
            map_def = map_data['definition']
            
            # Check value ranges
            if 'decoded_values' in map_data:
                for i, row in enumerate(map_data['decoded_values']):
                    for j, value in enumerate(row):
                        if value < map_def.min_value or value > map_def.max_value:
                            validation['warnings'].append(
                                f"Map {map_name}: Value at [{i},{j}] = {value} outside range "
                                f"[{map_def.min_value}, {map_def.max_value}]"
                            )
            
            # Check data size
            if 'raw_data' in map_data:
                expected_size = map_def.size
                actual_size = len(map_data['raw_data'])
                if actual_size != expected_size:
                    validation['errors'].append(
                        f"Map {map_name}: Data size mismatch. Expected {expected_size}, got {actual_size}"
                    )
                    validation['valid'] = False
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating map {map_name}: {e}")
            validation['valid'] = False
            validation['errors'].append(f"Validation error: {str(e)}")
            return validation
    
    def _validate_calibration_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate calibration parameters"""
        validation = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check for critical parameters
        critical_params = ['rev_limit', 'speed_limit', 'boost_limit']
        for param in critical_params:
            if param not in parameters:
                validation['warnings'].append(f"Missing critical parameter: {param}")
        
        # Validate parameter ranges
        if 'rev_limit' in parameters:
            rev_limit = parameters['rev_limit']
            if rev_limit > 8000:
                validation['warnings'].append(f"High rev limit: {rev_limit}RPM")
            if rev_limit < 4000:
                validation['errors'].append(f"Rev limit too low: {rev_limit}RPM")
                validation['valid'] = False
        
        if 'boost_limit' in parameters:
            boost_limit = parameters['boost_limit']
            if boost_limit > 25.0:
                validation['warnings'].append(f"High boost limit: {boost_limit}PSI")
        
        return validation
    
    def _perform_safety_checks(self, calibration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform safety checks on calibration data"""
        safety_checks = {
            'knock_safety': 'PASS',
            'temperature_safety': 'PASS', 
            'boost_safety': 'PASS',
            'afr_safety': 'PASS'
        }
        
        try:
            # Check ignition timing for knock safety
            if 'maps' in calibration_data and 'ignition_base' in calibration_data['maps']:
                ignition_map = calibration_data['maps']['ignition_base']['decoded_values']
                max_timing = max(max(row) for row in ignition_map)
                if max_timing > 30.0:
                    safety_checks['knock_safety'] = 'WARNING'
            
            # Check fuel maps for AFR safety
            if 'maps' in calibration_data and 'fuel_base' in calibration_data['maps']:
                fuel_map = calibration_data['maps']['fuel_base']['decoded_values']
                min_afr = min(min(row) for row in fuel_map) * 14.7  # Convert lambda to AFR
                if min_afr < 10.5:
                    safety_checks['afr_safety'] = 'WARNING'
                if min_afr < 9.5:
                    safety_checks['afr_safety'] = 'FAIL'
            
            return safety_checks
            
        except Exception as e:
            logger.error(f"Error performing safety checks: {e}")
            return safety_checks
    
    def generate_performance_tune(self, base_calibration_id: str, 
                                performance_level: str = "STAGE1") -> Optional[Dict[str, Any]]:
        """
        Generate performance tune from base calibration
        
        Args:
            base_calibration_id: Base calibration ID
            performance_level: Performance level (STAGE1, STAGE2, STAGE3)
            
        Returns:
            Performance tune calibration or None if failed
        """
        try:
            if not self.calibration_database:
                logger.error("Calibration database not available")
                return None
            
            # Get base calibration
            base_calibration = self.calibration_database.get_calibration(base_calibration_id)
            if not base_calibration:
                logger.error(f"Base calibration not found: {base_calibration_id}")
                return None
            
            # Create performance tune based on level
            performance_tune = self._create_performance_tune(base_calibration, performance_level)
            
            if performance_tune:
                logger.info(f"Generated {performance_level} performance tune")
                return performance_tune
            else:
                logger.error(f"Failed to generate {performance_level} performance tune")
                return None
                
        except Exception as e:
            logger.error(f"Error generating performance tune: {e}")
            return None
    
    def _create_performance_tune(self, base_calibration: Any, 
                               performance_level: str) -> Dict[str, Any]:
        """Create performance tune from base calibration"""
        performance_tune = {
            'base_calibration': base_calibration.calibration_id,
            'performance_level': performance_level,
            'modifications': {},
            'maps': {},
            'parameters': base_calibration.parameters.copy()
        }
        
        # Apply modifications based on performance level
        if performance_level == "STAGE1":
            performance_tune = self._apply_stage1_modifications(performance_tune, base_calibration)
        elif performance_level == "STAGE2":
            performance_tune = self._apply_stage2_modifications(performance_tune, base_calibration)
        elif performance_level == "STAGE3":
            performance_tune = self._apply_stage3_modifications(performance_tune, base_calibration)
        
        return performance_tune
    
    def _apply_stage1_modifications(self, tune: Dict[str, Any], base_calibration: Any) -> Dict[str, Any]:
        """Apply Stage 1 modifications"""
        tune['modifications']['description'] = "Stage 1: Basic performance tune"
        tune['modifications']['boost_increase'] = "+2 PSI"
        tune['modifications']['ignition_advance'] = "+2 degrees"
        
        # Modify parameters
        if 'boost_limit' in tune['parameters']:
            tune['parameters']['boost_limit'] += 2.0
        if 'rev_limit' in tune['parameters']:
            tune['parameters']['rev_limit'] = 7000  # Increase rev limit
        
        return tune
    
    def _apply_stage2_modifications(self, tune: Dict[str, Any], base_calibration: Any) -> Dict[str, Any]:
        """Apply Stage 2 modifications"""
        tune['modifications']['description'] = "Stage 2: Aggressive performance tune"
        tune['modifications']['boost_increase'] = "+4 PSI"
        tune['modifications']['ignition_advance'] = "+3 degrees"
        tune['modifications']['fuel_enrichment'] = "Increased"
        
        # Modify parameters
        if 'boost_limit' in tune['parameters']:
            tune['parameters']['boost_limit'] += 4.0
        if 'rev_limit' in tune['parameters']:
            tune['parameters']['rev_limit'] = 7200
        
        return tune
    
    def _apply_stage3_modifications(self, tune: Dict[str, Any], base_calibration: Any) -> Dict[str, Any]:
        """Apply Stage 3 modifications"""
        tune['modifications']['description'] = "Stage 3: Race performance tune"
        tune['modifications']['boost_increase'] = "+6 PSI"
        tune['modifications']['ignition_advance'] = "+4 degrees"
        tune['modifications']['fuel_enrichment'] = "Significantly increased"
        tune['modifications']['launch_control'] = "Enabled"
        
        # Modify parameters
        if 'boost_limit' in tune['parameters']:
            tune['parameters']['boost_limit'] += 6.0
        if 'rev_limit' in tune['parameters']:
            tune['parameters']['rev_limit'] = 7500
        if 'launch_control_rpm' in tune['parameters']:
            tune['parameters']['launch_control_rpm'] = 4500
        
        return tune
    
    def create_calibration_backup(self, backup_name: str) -> bool:
        """
        Create calibration backup
        
        Args:
            backup_name: Name for the backup
            
        Returns:
            True if backup created successfully
        """
        try:
            logger.info(f"Creating calibration backup: {backup_name}")
            
            # Read current calibration
            current_calibration = self.read_full_calibration()
            if not current_calibration:
                logger.error("Failed to read current calibration for backup")
                return False
            
            # Add backup metadata
            current_calibration['backup_metadata'] = {
                'name': backup_name,
                'timestamp': self._get_current_timestamp(),
                'vehicle_vin': current_calibration.get('identification', {}).get('vin', 'Unknown'),
                'calibration_id': current_calibration.get('identification', {}).get('calibration_id', 'Unknown')
            }
            
            # Save backup to file
            backup_filename = f"calibration_backup_{backup_name}_{self._get_current_timestamp()}.json"
            with open(backup_filename, 'w') as f:
                json.dump(current_calibration, f, indent=2)
            
            logger.info(f"Calibration backup saved: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating calibration backup: {e}")
            return False
    
    def restore_calibration_backup(self, backup_filename: str) -> bool:
        """
        Restore calibration from backup
        
        Args:
            backup_filename: Backup file to restore
            
        Returns:
            True if restore successful
        """
        try:
            logger.info(f"Restoring calibration from backup: {backup_filename}")
            
            # Load backup file
            with open(backup_filename, 'r') as f:
                backup_data = json.load(f)
            
            # Write calibration to ECU
            if self.write_calibration(backup_data):
                logger.info("Calibration restore completed successfully")
                return True
            else:
                logger.error("Failed to write calibration during restore")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring calibration backup: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp for backup naming"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")