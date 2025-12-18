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
    
    def _read_calibration_identification(self) -> Optional[Dict[str, str]]:
        """Read calibration identification"""
        try:
            identification = {}
            
            # Read calibration ID
            calib_id_data = self.diagnostic_protocol.read_data_by_identifier(0xF186)
            if calib_id_data:
                identification['calibration_id'] = calib_id_data.decode('ascii', errors='ignore').strip()
            
            # Read ECU part number
            part_num_data = self.diagnostic_protocol.read_data_by_identifier(0xF18C)
            if part_num_data:
                identification['ecu_part_number'] = part_num_data.decode('ascii', errors='ignore').strip()
            
            # Read software version
            sw_version_data = self.diagnostic_protocol.read_data_by_identifier(0xF195)
            if sw_version_data:
                identification['software_version'] = sw_version_data.decode('ascii', errors='ignore').strip()
            
            return identification if identification else None
            
        except Exception as e:
            logger.error(f"Error reading calibration identification: {e}")
            return None
    
    def _read_all_calibration_maps(self) -> Dict[str, Any]:
        """Read all calibration maps from ECU"""
        try:
            maps = {}
            
            if not self.calibration_database:
                logger.warning("No calibration database available")
                return maps
            
            # Get calibration ID to determine which maps to read
            calib_id = self._read_calibration_identification()
            if not calib_id:
                return maps
            
            # Get calibration definition from database
            calibration = self.calibration_database.get_calibration(calib_id.get('calibration_id', ''))
            if not calibration:
                logger.warning(f"Calibration {calib_id.get('calibration_id')} not found in database")
                return maps
            
            # Read each map
            for map_name, map_def in calibration.maps.items():
                try:
                    map_data = self._read_calibration_map(map_def)
                    if map_data:
                        maps[map_name] = {
                            'definition': map_def,
                            'data': map_data,
                            'raw_data': self._read_raw_map_data(map_def)
                        }
                except Exception as e:
                    logger.error(f"Error reading map {map_name}: {e}")
            
            return maps
            
        except Exception as e:
            logger.error(f"Error reading calibration maps: {e}")
            return {}
    
    def _read_calibration_map(self, map_def) -> Optional[np.ndarray]:
        """Read and decode a calibration map"""
        try:
            # Read raw data from ECU
            raw_data = self._read_raw_map_data(map_def)
            if not raw_data:
                return None
            
            # Convert to numpy array
            if len(map_def.axis_y) > 0:
                # 2D map
                array = np.array(raw_data).reshape(len(map_def.axis_y), len(map_def.axis_x))
            else:
                # 1D map
                array = np.array(raw_data)
            
            # Apply scaling
            scaled_array = array * map_def.scaling_factor
            
            return scaled_array
            
        except Exception as e:
            logger.error(f"Error reading calibration map: {e}")
            return None
    
    def _read_raw_map_data(self, map_def) -> Optional[bytes]:
        """Read raw map data from ECU memory"""
        try:
            return self.diagnostic_protocol.read_memory_by_address(
                address=map_def.address,
                size=map_def.size
            )
        except Exception as e:
            logger.error(f"Error reading raw map data: {e}")
            return None
    
    def _read_calibration_parameters(self) -> Dict[str, Any]:
        """Read calibration parameters"""
        try:
            parameters = {}
            
            # Define parameter addresses (these would be from calibration database)
            parameter_addresses = {
                'max_boost': 0xFFD000,
                'rev_limit': 0xFFD004,
                'idle_rpm': 0xFFD008,
                'fuel_pressure_target': 0xFFD00C,
                'timing_limit': 0xFFD010
            }
            
            for param_name, address in parameter_addresses.items():
                try:
                    data = self.diagnostic_protocol.read_memory_by_address(address, 4)
                    if data:
                        value = struct.unpack('>f', data)[0]
                        parameters[param_name] = value
                except Exception as e:
                    logger.error(f"Error reading parameter {param_name}: {e}")
            
            return parameters
            
        except Exception as e:
            logger.error(f"Error reading calibration parameters: {e}")
            return {}
    
    def _calculate_calibration_checksum(self, calibration_data: Dict[str, Any]) -> str:
        """Calculate checksum for calibration data"""
        try:
            # Combine all data for checksum
            checksum_data = b''
            
            # Add identification data
            if 'identification' in calibration_data:
                for value in calibration_data['identification'].values():
                    checksum_data += value.encode('ascii')
            
            # Add map data
            if 'maps' in calibration_data:
                for map_info in calibration_data['maps'].values():
                    if 'raw_data' in map_info:
                        checksum_data += map_info['raw_data']
            
            # Add parameters
            if 'parameters' in calibration_data:
                for value in calibration_data['parameters'].values():
                    checksum_data += struct.pack('>f', value)
            
            # Calculate SHA-256 checksum
            checksum = hashlib.sha256(checksum_data).hexdigest()
            return checksum.upper()
            
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return ""
    
    def write_calibration(self, calibration_data: Dict[str, Any]) -> bool:
        """
        Write calibration data to ECU
        
        Args:
            calibration_data: Calibration data to write
            
        Returns:
            True if successful
        """
        try:
            logger.info("Writing calibration to ECU...")
            
            # Enter programming mode
            if not self.programming_service.enter_programming_mode():
                logger.error("Failed to enter programming mode")
                return False
            
            try:
                # Write maps
                if 'maps' in calibration_data:
                    for map_name, map_info in calibration_data['maps'].items():
                        if not self._write_calibration_map(map_info):
                            logger.error(f"Failed to write map {map_name}")
                            return False
                
                # Write parameters
                if 'parameters' in calibration_data:
                    for param_name, value in calibration_data['parameters'].items():
                        if not self._write_calibration_parameter(param_name, value):
                            logger.error(f"Failed to write parameter {param_name}")
                            return False
                
                # Verify calibration
                if not self._verify_calibration(calibration_data):
                    logger.error("Calibration verification failed")
                    return False
                
                logger.info("Calibration written successfully")
                return True
                
            finally:
                self.programming_service.exit_programming_mode()
                
        except Exception as e:
            logger.error(f"Error writing calibration: {e}")
            return False
    
    def _write_calibration_map(self, map_info: Dict[str, Any]) -> bool:
        """Write a calibration map to ECU"""
        try:
            map_def = map_info['definition']
            map_data = map_info['data']
            
            # Scale data back to raw values
            raw_data = (map_data / map_def.scaling_factor).astype('>H').tobytes()
            
            # Write to ECU memory
            return self.diagnostic_protocol.write_memory_by_address(
                address=map_def.address,
                data=raw_data
            )
            
        except Exception as e:
            logger.error(f"Error writing calibration map: {e}")
            return False
    
    def _write_calibration_parameter(self, param_name: str, value: float) -> bool:
        """Write a calibration parameter to ECU"""
        try:
            # Define parameter addresses
            parameter_addresses = {
                'max_boost': 0xFFD000,
                'rev_limit': 0xFFD004,
                'idle_rpm': 0xFFD008,
                'fuel_pressure_target': 0xFFD00C,
                'timing_limit': 0xFFD010
            }
            
            if param_name not in parameter_addresses:
                logger.error(f"Unknown parameter: {param_name}")
                return False
            
            # Convert to bytes
            data = struct.pack('>f', value)
            
            # Write to ECU memory
            return self.diagnostic_protocol.write_memory_by_address(
                address=parameter_addresses[param_name],
                data=data
            )
            
        except Exception as e:
            logger.error(f"Error writing calibration parameter: {e}")
            return False
    
    def _verify_calibration(self, calibration_data: Dict[str, Any]) -> bool:
        """Verify calibration was written correctly"""
        try:
            # Read back calibration
            read_data = self.read_full_calibration()
            if not read_data:
                return False
            
            # Compare checksums
            if read_data.get('checksum') != calibration_data.get('checksum'):
                logger.error("Checksum mismatch after writing")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying calibration: {e}")
            return False
    
    def adjust_map(self, map_name: str, adjustment: MapAdjustment) -> bool:
        """
        Adjust a calibration map
        
        Args:
            map_name: Name of map to adjust
            adjustment: Adjustment to apply
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Adjusting map {map_name}...")
            
            # Read current calibration
            calibration = self.read_full_calibration()
            if not calibration or 'maps' not in calibration:
                logger.error("Failed to read calibration")
                return False
            
            if map_name not in calibration['maps']:
                logger.error(f"Map {map_name} not found")
                return False
            
            # Get map data
            map_info = calibration['maps'][map_name]
            map_data = map_info['data'].copy()
            
            # Apply adjustment
            if adjustment.adjustment_type == MapAdjustmentType.OFFSET:
                offset = adjustment.values.get('offset', 0.0)
                map_data += offset
                
            elif adjustment.adjustment_type == MapAdjustmentType.SCALING:
                scale = adjustment.values.get('scale', 1.0)
                map_data *= scale
                
            elif adjustment.adjustment_type == MapAdjustmentType.INTERPOLATION:
                # Linear interpolation between points
                points = adjustment.values.get('points', [])
                if len(points) >= 2:
                    map_data = self._interpolate_map(map_data, points)
            
            # Update calibration data
            calibration['maps'][map_name]['data'] = map_data
            
            # Write modified calibration
            return self.write_calibration(calibration)
            
        except Exception as e:
            logger.error(f"Error adjusting map: {e}")
            return False
    
    def _interpolate_map(self, map_data: np.ndarray, points: List[Tuple[float, float]]) -> np.ndarray:
        """Interpolate map values based on control points"""
        try:
            # Simple linear interpolation
            result = map_data.copy()
            
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                
                # Find indices for interpolation
                idx1 = int(x1 * len(result) / 100)
                idx2 = int(x2 * len(result) / 100)
                
                if idx1 < len(result) and idx2 < len(result):
                    # Linear interpolation between points
                    for j in range(idx1, idx2 + 1):
                        t = (j - idx1) / (idx2 - idx1) if idx2 != idx1 else 0
                        result.flat[j] = y1 + t * (y2 - y1)
            
            return result
            
        except Exception as e:
            logger.error(f"Error interpolating map: {e}")
            return map_data
    
    def create_calibration_backup(self, filename: str) -> bool:
        """
        Create backup of current calibration
        
        Args:
            filename: Backup filename
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Creating calibration backup: {filename}")
            
            # Read current calibration
            calibration = self.read_full_calibration()
            if not calibration:
                logger.error("Failed to read calibration for backup")
                return False
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(calibration, f, indent=2, default=str)
            
            logger.info(f"Calibration backup saved to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating calibration backup: {e}")
            return False
    
    def restore_calibration_backup(self, filename: str) -> bool:
        """
        Restore calibration from backup
        
        Args:
            filename: Backup filename
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Restoring calibration from backup: {filename}")
            
            # Load backup
            with open(filename, 'r') as f:
                calibration = json.load(f)
            
            # Write calibration
            return self.write_calibration(calibration)
            
        except Exception as e:
            logger.error(f"Error restoring calibration backup: {e}")
            return False
