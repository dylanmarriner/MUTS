#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DATA CONVERTERS - Complete Data Conversion Utilities
Conversion functions for Mazda-specific data formats
"""

import struct
import math
from typing import Dict, List, Any, Optional, Union
from enum import IntEnum

class SecretAccessCodes:
    """
    Complete Mazda Data Conversion Utilities
    Handles all Mazda-specific data format conversions
    """
    
    # Mazda-specific conversion constants
    MAZDA_SCALING_FACTORS = {
        'rpm': 1.0,
        'temperature': 1.0,
        'pressure': 0.1,
        'voltage': 0.001,
        'current': 0.001,
        'angle': 0.1,
        'flow': 0.01
    }
    
    @staticmethod
    def bytes_to_uint8(data: bytes, offset: int = 0) -> int:
        """Convert bytes to unsigned 8-bit integer"""
        if len(data) < offset + 1:
            raise ValueError("Insufficient data for uint8 conversion")
        return data[offset]
    
    @staticmethod
    def bytes_to_int8(data: bytes, offset: int = 0) -> int:
        """Convert bytes to signed 8-bit integer"""
        if len(data) < offset + 1:
            raise ValueError("Insufficient data for int8 conversion")
        value = data[offset]
        if value > 127:
            return value - 256
        return value
    
    @staticmethod
    def bytes_to_uint16(data: bytes, offset: int = 0, big_endian: bool = True) -> int:
        """Convert bytes to unsigned 16-bit integer"""
        if len(data) < offset + 2:
            raise ValueError("Insufficient data for uint16 conversion")
        
        if big_endian:
            return (data[offset] << 8) | data[offset + 1]
        else:
            return data[offset] | (data[offset + 1] << 8)
    
    @staticmethod
    def bytes_to_int16(data: bytes, offset: int = 0, big_endian: bool = True) -> int:
        """Convert bytes to signed 16-bit integer"""
        value = SecretAccessCodes.bytes_to_uint16(data, offset, big_endian)
        if value > 32767:
            return value - 65536
        return value
    
    @staticmethod
    def bytes_to_uint32(data: bytes, offset: int = 0, big_endian: bool = True) -> int:
        """Convert bytes to unsigned 32-bit integer"""
        if len(data) < offset + 4:
            raise ValueError("Insufficient data for uint32 conversion")
        
        if big_endian:
            return (data[offset] << 24) | (data[offset + 1] << 16) | \
                   (data[offset + 2] << 8) | data[offset + 3]
        else:
            return data[offset] | (data[offset + 1] << 8) | \
                   (data[offset + 2] << 16) | (data[offset + 3] << 24)
    
    @staticmethod
    def bytes_to_float(data: bytes, offset: int = 0, big_endian: bool = True) -> float:
        """Convert bytes to float"""
        if len(data) < offset + 4:
            raise ValueError("Insufficient data for float conversion")
        
        format_char = '>' if big_endian else '<'
        return struct.unpack_from(f'{format_char}f', data, offset)[0]
    
    @staticmethod
    def mazda_rpm_to_bytes(rpm: float) -> bytes:
        """Convert RPM to Mazda format bytes"""
        # Mazda RPM is typically 2 bytes, scaled by 4
        rpm_int = int(rpm * 4)
        return struct.pack('>H', rpm_int)
    
    @staticmethod
    def bytes_to_mazda_rpm(data: bytes, offset: int = 0) -> float:
        """Convert Mazda RPM bytes to value"""
        rpm_int = SecretAccessCodes.bytes_to_uint16(data, offset)
        return rpm_int / 4.0
    
    @staticmethod
    def mazda_temperature_to_bytes(temp: float) -> bytes:
        """Convert temperature to Mazda format bytes"""
        # Mazda temperature is offset by 40
        temp_int = int(temp + 40)
        return struct.pack('>B', temp_int)
    
    @staticmethod
    def bytes_to_mazda_temperature(data: bytes, offset: int = 0) -> float:
        """Convert Mazda temperature bytes to value"""
        temp_int = SecretAccessCodes.bytes_to_uint8(data, offset)
        return temp_int - 40.0
    
    @staticmethod
    def mazda_pressure_to_bytes(pressure: float) -> bytes:
        """Convert pressure to Mazda format bytes"""
        # Mazda pressure is typically scaled by 0.1
        pressure_int = int(pressure * 10)
        return struct.pack('>H', pressure_int)
    
    @staticmethod
    def bytes_to_mazda_pressure(data: bytes, offset: int = 0) -> float:
        """Convert Mazda pressure bytes to value"""
        pressure_int = SecretAccessCodes.bytes_to_uint16(data, offset)
        return pressure_int / 10.0
    
    @staticmethod
    def mazda_angle_to_bytes(angle: float) -> bytes:
        """Convert angle to Mazda format bytes"""
        # Mazda angle is typically scaled by 0.1
        angle_int = int(angle * 10)
        return struct.pack('>H', angle_int)
    
    @staticmethod
    def bytes_to_mazda_angle(data: bytes, offset: int = 0) -> float:
        """Convert Mazda angle bytes to value"""
        angle_int = SecretAccessCodes.bytes_to_uint16(data, offset)
        return angle_int / 10.0
    
    @staticmethod
    def mazda_load_to_bytes(load: float) -> bytes:
        """Convert engine load to Mazda format bytes"""
        # Mazda load is percentage scaled to 0-255
        load_int = int(load * 255 / 100)
        return struct.pack('>B', load_int)
    
    @staticmethod
    def bytes_to_mazda_load(data: bytes, offset: int = 0) -> float:
        """Convert Mazda load bytes to value"""
        load_int = SecretAccessCodes.bytes_to_uint8(data, offset)
        return load_int * 100 / 255
    
    @staticmethod
    def mazda_timing_to_bytes(timing: float) -> bytes:
        """Convert timing advance to Mazda format bytes"""
        # Mazda timing is offset by 64 and scaled by 2
        timing_int = int((timing + 64) * 2)
        return struct.pack('>B', timing_int)
    
    @staticmethod
    def bytes_to_mazda_timing(data: bytes, offset: int = 0) -> float:
        """Convert Mazda timing bytes to value"""
        timing_int = SecretAccessCodes.bytes_to_uint8(data, offset)
        return timing_int / 2.0 - 64.0
    
    @staticmethod
    def mazda_flow_to_bytes(flow: float) -> bytes:
        """Convert MAF flow to Mazda format bytes"""
        # Mazda MAF flow is scaled by 100
        flow_int = int(flow * 100)
        return struct.pack('>H', flow_int)
    
    @staticmethod
    def bytes_to_mazda_flow(data: bytes, offset: int = 0) -> float:
        """Convert Mazda flow bytes to value"""
        flow_int = SecretAccessCodes.bytes_to_uint16(data, offset)
        return flow_int / 100.0
    
    @staticmethod
    def mazda_fuel_pressure_to_bytes(pressure: float) -> bytes:
        """Convert fuel pressure to Mazda format bytes"""
        # Mazda fuel pressure is scaled by 3
        pressure_int = int(pressure / 3)
        return struct.pack('>B', pressure_int)
    
    @staticmethod
    def bytes_to_mazda_fuel_pressure(data: bytes, offset: int = 0) -> float:
        """Convert Mazda fuel pressure bytes to value"""
        pressure_int = SecretAccessCodes.bytes_to_uint8(data, offset)
        return pressure_int * 3.0
    
    @staticmethod
    def mazda_vehicle_speed_to_bytes(speed: float) -> bytes:
        """Convert vehicle speed to Mazda format bytes"""
        # Mazda vehicle speed is direct km/h
        speed_int = int(speed)
        return struct.pack('>B', speed_int)
    
    @staticmethod
    def bytes_to_mazda_vehicle_speed(data: bytes, offset: int = 0) -> float:
        """Convert Mazda vehicle speed bytes to value"""
        return SecretAccessCodes.bytes_to_uint8(data, offset)
    
    @staticmethod
    def mazda_throttle_to_bytes(throttle: float) -> bytes:
        """Convert throttle position to Mazda format bytes"""
        # Mazda throttle is percentage scaled to 0-255
        throttle_int = int(throttle * 255 / 100)
        return struct.pack('>B', throttle_int)
    
    @staticmethod
    def bytes_to_mazda_throttle(data: bytes, offset: int = 0) -> float:
        """Convert Mazda throttle bytes to value"""
        throttle_int = SecretAccessCodes.bytes_to_uint8(data, offset)
        return throttle_int * 100 / 255
    
    @staticmethod
    def convert_map_data(raw_data: bytes, map_def: Dict[str, Any]) -> List[List[float]]:
        """
        Convert raw map data to engineering units
        
        Args:
            raw_data: Raw map data bytes
            map_def: Map definition with scaling info
            
        Returns:
            2D array of converted values
        """
        try:
            if not raw_data:
                return []
            
            # Get map dimensions
            x_size = map_def.get('x_size', 16)
            y_size = map_def.get('y_size', 16)
            
            # Get scaling factor
            scaling = map_def.get('scaling_factor', 1.0)
            
            # Convert bytes to 16-bit values
            values = []
            for i in range(0, min(len(raw_data), x_size * y_size * 2), 2):
                if i + 1 < len(raw_data):
                    raw_value = SecretAccessCodes.bytes_to_uint16(raw_data, i)
                    scaled_value = raw_value * scaling
                    values.append(scaled_value)
            
            # Reshape to 2D array
            if len(values) == x_size * y_size:
                return [values[i:i+x_size] for i in range(0, len(values), x_size)]
            else:
                return [values]
                
        except Exception as e:
            raise ValueError(f"Error converting map data: {e}")
    
    @staticmethod
    def convert_map_to_raw(map_data: List[List[float]], map_def: Dict[str, Any]) -> bytes:
        """
        Convert map data from engineering units to raw bytes
        
        Args:
            map_data: 2D array of map values
            map_def: Map definition with scaling info
            
        Returns:
            Raw data bytes
        """
        try:
            # Get scaling factor
            scaling = map_def.get('scaling_factor', 1.0)
            
            # Flatten and convert to raw values
            raw_values = []
            for row in map_data:
                for value in row:
                    raw_value = int(value / scaling)
                    raw_value = max(0, min(65535, raw_value))  # Clamp to 16-bit range
                    raw_values.append(raw_value)
            
            # Convert to bytes
            raw_data = b''
            for value in raw_values:
                raw_data += struct.pack('>H', value)
            
            return raw_data
            
        except Exception as e:
            raise ValueError(f"Error converting map to raw: {e}")
    
    @staticmethod
    def apply_deadband(value: float, deadband: float) -> float:
        """Apply deadband to value"""
        if abs(value) < deadband:
            return 0.0
        return value
    
    @staticmethod
    def apply_hysteresis(value: float, previous: float, hysteresis: float) -> float:
        """Apply hysteresis to value"""
        if abs(value - previous) < hysteresis:
            return previous
        return value
    
    @staticmethod
    def filter_noise(values: List[float], window_size: int = 5) -> List[float]:
        """Apply moving average filter to reduce noise"""
        if not values or window_size <= 0:
            return values
        
        filtered = []
        for i in range(len(values)):
            start = max(0, i - window_size // 2)
            end = min(len(values), i + window_size // 2 + 1)
            avg = sum(values[start:end]) / (end - start)
            filtered.append(avg)
        
        return filtered
