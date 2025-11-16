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

class MazdaDataConverter:
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
        value = MazdaDataConverter.bytes_to_uint16(data, offset, big_endian)
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
        rpm_int = MazdaDataConverter.bytes_to_uint16(data, offset)
        return rpm_int / 4.0
    
    @staticmethod
    def mazda_temperature_to_bytes(temp: float) -> bytes:
        """Convert temperature to Mazda format bytes"""
        # Mazda temperature is typically offset by 40°C
        temp_int = int(temp + 40)
        return struct.pack('B', temp_int)
    
    @staticmethod
    def bytes_to_mazda_temperature(data: bytes, offset: int = 0) -> float:
        """Convert Mazda temperature bytes to value"""
        temp_int = MazdaDataConverter.bytes_to_uint8(data, offset)
        return temp_int - 40.0
    
    @staticmethod
    def mazda_pressure_to_bytes(pressure: float, scaling: float = 0.1) -> bytes:
        """Convert pressure to Mazda format bytes"""
        pressure_int = int(pressure / scaling)
        return struct.pack('>H', pressure_int)
    
    @staticmethod
    def bytes_to_mazda_pressure(data: bytes, offset: int = 0, scaling: float = 0.1) -> float:
        """Convert Mazda pressure bytes to value"""
        pressure_int = MazdaDataConverter.bytes_to_uint16(data, offset)
        return pressure_int * scaling
    
    @staticmethod
    def mazda_voltage_to_bytes(voltage: float, scaling: float = 0.001) -> bytes:
        """Convert voltage to Mazda format bytes"""
        voltage_int = int(voltage / scaling)
        return struct.pack('>H', voltage_int)
    
    @staticmethod
    def bytes_to_mazda_voltage(data: bytes, offset: int = 0, scaling: float = 0.001) -> float:
        """Convert Mazda voltage bytes to value"""
        voltage_int = MazdaDataConverter.bytes_to_uint16(data, offset)
        return voltage_int * scaling
    
    @staticmethod
    def mazda_angle_to_bytes(angle: float, scaling: float = 0.1) -> bytes:
        """Convert angle to Mazda format bytes"""
        angle_int = int(angle / scaling)
        return struct.pack('>h', angle_int)
    
    @staticmethod
    def bytes_to_mazda_angle(data: bytes, offset: int = 0, scaling: float = 0.1) -> float:
        """Convert Mazda angle bytes to value"""
        angle_int = MazdaDataConverter.bytes_to_int16(data, offset)
        return angle_int * scaling
    
    @staticmethod
    def decode_maf_signal(voltage: float, maf_type: str = "HOT_WIRE") -> float:
        """
        Decode MAF sensor signal to airflow
        
        Args:
            voltage: MAF sensor voltage
            maf_type: Type of MAF sensor
            
        Returns:
            Airflow in g/s
        """
        # Mazda-specific MAF transfer functions
        maf_transfer_functions = {
            "HOT_WIRE": lambda v: 120.0 * v - 60.0,  # Typical hot-wire MAF
            "VANE": lambda v: 80.0 * v ** 2 + 20.0 * v,  # Vane-type MAF
            "MAP_BASED": lambda v: 150.0 * math.sqrt(v)  # Speed-density estimation
        }
        
        transfer_func = maf_transfer_functions.get(maf_type, maf_transfer_functions["HOT_WIRE"])
        return max(0.0, transfer_func(voltage))
    
    @staticmethod
    def decode_map_signal(voltage: float, sensor_range: tuple = (0, 255)) -> float:
        """
        Decode MAP sensor signal to pressure
        
        Args:
            voltage: MAP sensor voltage (0-5V)
            sensor_range: Sensor pressure range in kPa
            
        Returns:
            Pressure in kPa
        """
        min_pressure, max_pressure = sensor_range
        pressure_range = max_pressure - min_pressure
        
        # Convert voltage to pressure (assuming linear relationship)
        pressure = min_pressure + (voltage / 5.0) * pressure_range
        return pressure
    
    @staticmethod
    def decode_tps_signal(voltage: float, tps_type: str = "POTENTIOMETER") -> float:
        """
        Decode throttle position sensor signal
        
        Args:
            voltage: TPS voltage (0-5V)
            tps_type: Type of TPS sensor
            
        Returns:
            Throttle position percentage (0-100%)
        """
        # Mazda-specific TPS calibration
        tps_calibrations = {
            "POTENTIOMETER": lambda v: (v / 5.0) * 100.0,  # Standard potentiometer
            "HALL_EFFECT": lambda v: 25.0 * v - 12.5,  # Hall effect sensor
            "DUAL_POT": lambda v: (v / 2.5) * 100.0  # Dual potentiometer (half range)
        }
        
        calibration_func = tps_calibrations.get(tps_type, tps_calibrations["POTENTIOMETER"])
        position = calibration_func(voltage)
        return max(0.0, min(100.0, position))
    
    @staticmethod
    def decode_oxygen_sensor_signal(voltage: float, sensor_type: str = "ZIRCONIA") -> float:
        """
        Decode oxygen sensor signal to air-fuel ratio
        
        Args:
            voltage: O2 sensor voltage
            sensor_type: Type of oxygen sensor
            
        Returns:
            Air-fuel ratio
        """
        # Mazda-specific O2 sensor calibrations
        o2_calibrations = {
            "ZIRCONIA": lambda v: 14.7 + (v - 0.45) * 10.0,  # Narrowband zirconia
            "TITANIA": lambda v: 14.7 + (v - 2.5) * 2.0,  # Titania sensor
            "WIDEBAND": lambda v: 7.35 + (v * 8.0)  # Wideband sensor (0-5V = 7.35-22.39 AFR)
        }
        
        calibration_func = o2_calibrations.get(sensor_type, o2_calibrations["ZIRCONIA"])
        afr = calibration_func(voltage)
        return max(7.0, min(23.0, afr))
    
    @staticmethod
    def calculate_injector_pulse_width(rpm: float, load: float, 
                                     base_pulse: float = 2.5) -> float:
        """
        Calculate fuel injector pulse width
        
        Args:
            rpm: Engine RPM
            load: Engine load (0-1)
            base_pulse: Base pulse width in ms
            
        Returns:
            Injector pulse width in milliseconds
        """
        # Mazda-specific injector calculation
        # Based on engine speed and load
        pulse_width = base_pulse * load
        
        # Adjust for engine speed
        if rpm > 0:
            # Longer pulse at lower RPM for same load
            rpm_factor = 6000.0 / max(rpm, 1000.0)
            pulse_width *= rpm_factor
        
        return max(1.0, min(20.0, pulse_width))
    
    @staticmethod
    def calculate_ignition_timing(base_timing: float, rpm: float, load: float,
                                coolant_temp: float, intake_temp: float) -> float:
        """
        Calculate ignition timing advance
        
        Args:
            base_timing: Base timing advance
            rpm: Engine RPM
            load: Engine load (0-1)
            coolant_temp: Coolant temperature (°C)
            intake_temp: Intake air temperature (°C)
            
        Returns:
            Ignition timing advance in degrees
        """
        # Mazda-specific timing calculation
        
        # RPM compensation
        rpm_timing = 0.0
        if rpm < 2000:
            rpm_timing = 5.0  # More advance at low RPM
        elif rpm > 6000:
            rpm_timing = -3.0  # Less advance at high RPM
        
        # Load compensation
        load_timing = load * 8.0  # More advance at higher load
        
        # Temperature compensation
        temp_timing = 0.0
        if coolant_temp < 70:
            temp_timing = -2.0  # Less advance when cold
        elif coolant_temp > 100:
            temp_timing = -1.0  # Less advance when hot
        
        if intake_temp > 40:
            temp_timing -= 1.0  # Less advance with hot intake air
        
        total_timing = base_timing + rpm_timing + load_timing + temp_timing
        
        return max(0.0, min(35.0, total_timing))
    
    @staticmethod
    def calculate_boost_target(rpm: float, gear: int, 
                             performance_mode: str = "NORMAL") -> float:
        """
        Calculate boost target based on conditions
        
        Args:
            rpm: Engine RPM
            gear: Current gear
            performance_mode: Performance mode setting
            
        Returns:
            Boost target in PSI
        """
        # Mazda-specific boost control logic
        
        base_boost = {
            "NORMAL": 15.0,
            "SPORT": 18.0,
            "RACE": 21.0
        }.get(performance_mode, 15.0)
        
        # RPM-based boost adjustment
        rpm_factor = 1.0
        if rpm < 3000:
            rpm_factor = 0.7  # Less boost at low RPM
        elif rpm > 6000:
            rpm_factor = 0.9  # Slightly less boost at very high RPM
        
        # Gear-based boost adjustment
        gear_factor = {
            1: 0.8,   # Less boost in 1st gear
            2: 0.9,   # Slightly less in 2nd
            3: 1.0,   # Full boost from 3rd up
            4: 1.0,
            5: 1.0,
            6: 1.0
        }.get(gear, 1.0)
        
        target_boost = base_boost * rpm_factor * gear_factor
        
        return max(8.0, min(25.0, target_boost))
    
    @staticmethod
    def convert_afr_to_lambda(afr: float, fuel_type: str = "GASOLINE") -> float:
        """
        Convert air-fuel ratio to lambda
        
        Args:
            afr: Air-fuel ratio
            fuel_type: Type of fuel
            
        Returns:
            Lambda value
        """
        # Stoichiometric AFR for different fuels
        stoichiometric_afr = {
            "GASOLINE": 14.7,
            "E85": 9.76,
            "DIESEL": 14.5,
            "METHANOL": 6.4
        }.get(fuel_type, 14.7)
        
        return afr / stoichiometric_afr
    
    @staticmethod
    def convert_lambda_to_afr(lambda_val: float, fuel_type: str = "GASOLINE") -> float:
        """
        Convert lambda to air-fuel ratio
        
        Args:
            lambda_val: Lambda value
            fuel_type: Type of fuel
            
        Returns:
            Air-fuel ratio
        """
        stoichiometric_afr = {
            "GASOLINE": 14.7,
            "E85": 9.76,
            "DIESEL": 14.5,
            "METHANOL": 6.4
        }.get(fuel_type, 14.7)
        
        return lambda_val * stoichiometric_afr
    
    @staticmethod
    def calculate_horsepower(torque: float, rpm: float) -> float:
        """
        Calculate horsepower from torque and RPM
        
        Args:
            torque: Torque in lb-ft
            rpm: Engine RPM
            
        Returns:
            Horsepower
        """
        return (torque * rpm) / 5252.0
    
    @staticmethod
    def calculate_torque(horsepower: float, rpm: float) -> float:
        """
        Calculate torque from horsepower and RPM
        
        Args:
            horsepower: Horsepower
            rpm: Engine RPM
            
        Returns:
            Torque in lb-ft
        """
        if rpm == 0:
            return 0.0
        return (horsepower * 5252.0) / rpm
    
    @staticmethod
    def psi_to_kpa(psi: float) -> float:
        """Convert PSI to kPa"""
        return psi * 6.89476
    
    @staticmethod
    def kpa_to_psi(kpa: float) -> float:
        """Convert kPa to PSI"""
        return kpa / 6.89476
    
    @staticmethod
    def celsius_to_fahrenheit(celsius: float) -> float:
        """Convert Celsius to Fahrenheit"""
        return (celsius * 9/5) + 32
    
    @staticmethod
    def fahrenheit_to_celsius(fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius"""
        return (fahrenheit - 32) * 5/9
    
    @staticmethod
    def decode_mazda_vin(vin: str) -> Dict[str, str]:
        """
        Decode Mazda VIN information
        
        Args:
            vin: 17-character VIN
            
        Returns:
            VIN decoding results
        """
        if len(vin) != 17:
            return {"error": "Invalid VIN length"}
        
        vin_info = {
            "vin": vin,
            "wmi": vin[:3],  # World Manufacturer Identifier
            "vds": vin[3:9], # Vehicle Descriptor Section
            "vis": vin[9:]   # Vehicle Identifier Section
        }
        
        # Decode WMI (World Manufacturer Identifier)
        wmi = vin[:3]
        if wmi.startswith("JM"):
            vin_info["manufacturer"] = "Mazda Motor Corporation"
            vin_info["country"] = "Japan"
        elif wmi.startswith("1YV"):
            vin_info["manufacturer"] = "Mazda Motor Manufacturing USA"
            vin_info["country"] = "United States"
        else:
            vin_info["manufacturer"] = "Unknown"
            vin_info["country"] = "Unknown"
        
        # Decode vehicle attributes (simplified)
        model_year_char = vin[9]
        year_codes = {
            'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014,
            'F': 2015, 'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019,
            'L': 2020, 'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024
        }
        vin_info["model_year"] = year_codes.get(model_year_char, "Unknown")
        
        # Decode plant code
        plant_code = vin[10]
        plant_codes = {
            '0': "Hiroshima, Japan",
            '1': "Hofu, Japan", 
            'A': "AutoAlliance, Thailand",
            'U': "Mazda USA"
        }
        vin_info["assembly_plant"] = plant_codes.get(plant_code, "Unknown")
        
        return vin_info
    
    @staticmethod
    def encode_calibration_map(values: List[List[float]], data_type: str = "uint8",
                             scaling: float = 1.0) -> bytes:
        """
        Encode calibration map to bytes
        
        Args:
            values: 2D list of map values
            data_type: Data type for encoding
            scaling: Scaling factor
            
        Returns:
            Encoded map data
        """
        encoded_data = bytearray()
        
        for row in values:
            for value in row:
                scaled_value = value / scaling
                
                if data_type == "uint8":
                    int_value = int(round(scaled_value))
                    encoded_data.append(max(0, min(255, int_value)))
                elif data_type == "int8":
                    int_value = int(round(scaled_value))
                    encoded_data.append(max(-128, min(127, int_value)) & 0xFF)
                elif data_type == "uint16":
                    int_value = int(round(scaled_value))
                    encoded_data.extend(struct.pack('>H', max(0, min(65535, int_value))))
                elif data_type == "int16":
                    int_value = int(round(scaled_value))
                    encoded_data.extend(struct.pack('>h', max(-32768, min(32767, int_value))))
        
        return bytes(encoded_data)
    
    @staticmethod
    def decode_calibration_map(data: bytes, width: int, height: int,
                             data_type: str = "uint8", scaling: float = 1.0) -> List[List[float]]:
        """
        Decode calibration map from bytes
        
        Args:
            data: Map data bytes
            width: Map width
            height: Map height
            data_type: Data type for decoding
            scaling: Scaling factor
            
        Returns:
            2D list of map values
        """
        values = []
        bytes_per_value = 1 if data_type in ["uint8", "int8"] else 2
        
        if len(data) < width * height * bytes_per_value:
            raise ValueError("Insufficient data for map decoding")
        
        for y in range(height):
            row = []
            for x in range(width):
                offset = (y * width + x) * bytes_per_value
                
                if data_type == "uint8":
                    value = data[offset] * scaling
                elif data_type == "int8":
                    value = struct.unpack_from('b', data, offset)[0] * scaling
                elif data_type == "uint16":
                    value = struct.unpack_from('>H', data, offset)[0] * scaling
                elif data_type == "int16":
                    value = struct.unpack_from('>h', data, offset)[0] * scaling
                else:
                    value = 0.0
                
                row.append(value)
            values.append(row)
        
        return values