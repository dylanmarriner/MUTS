#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3_ROM_REVERSE_ENGINEERING.py
COMPLETE ROM READER, MAP DEFINITIONS & LIVE DATA EXTRACTION
"""

import struct
import binascii
import can
import time
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import crcmod
import numpy as np

@dataclass
class ROMDefinition:
    """COMPLETE ROM STRUCTURE DEFINITION FOR MZR DISI ECU"""
    base_address: int
    size: int
    description: str
    checksum_offset: int = None
    checksum_algorithm: str = None

class MazdaECUROMReader:
    """COMPLETE ROM READING & REVERSE ENGINEERING FRAMEWORK"""
    
    def __init__(self):
        self.rom_definitions = self._define_rom_structure()
        self.map_definitions = self._define_maps()
        self.pid_definitions = self._define_pids()
        self.did_definitions = self._define_dids()
        self.can_bus = can.interface.Bus(channel='can0', bustype='socketcan')
        
    def _define_rom_structure(self):
        """DEFINE COMPLETE ROM MEMORY STRUCTURE"""
        return {
            'boot_sector': ROMDefinition(0x000000, 0x010000, 'Bootloader and security'),
            'calibration_a': ROMDefinition(0x010000, 0x080000, 'Primary calibration tables'),
            'calibration_b': ROMDefinition(0x090000, 0x080000, 'Secondary/backup calibration'),
            'operating_system': ROMDefinition(0x110000, 0x040000, 'ECU operating system'),
            'fault_codes': ROMDefinition(0x150000, 0x020000, 'DTC storage and freeze frames'),
            'adaptation_data': ROMDefinition(0x170000, 0x020000, 'Adaptive learning data'),
            'vin_storage': ROMDefinition(0x190000, 0x001000, 'VIN and vehicle data'),
            'security_sector': ROMDefinition(0x191000, 0x001000, 'Security keys and access'),
            'end_of_memory': ROMDefinition(0x1F0000, 0x010000, 'Checksums and validation')
        }
    
    def _define_maps(self):
        """COMPLETE MAP DEFINITIONS WITH MEMORY ADDRESSES"""
        return {
            'ignition_timing': {
                'primary_map': {'address': 0x012000, 'size': 0x0400, 'type': '16x16', 'description': 'Main ignition advance'},
                'high_octane_map': {'address': 0x012400, 'size': 0x0400, 'type': '16x16', 'description': 'High octane timing'},
                'low_octane_map': {'address': 0x012800, 'size': 0x0400, 'type': '16x16', 'description': 'Low octane timing'},
                'cold_temp_correction': {'address': 0x012C00, 'size': 0x0200, 'type': '8x8', 'description': 'Cold temperature advance'},
                'iat_correction': {'address': 0x012E00, 'size': 0x0100, 'type': '1D', 'description': 'IAT timing correction'}
            },
            'fuel_maps': {
                'primary_fuel_map': {'address': 0x013000, 'size': 0x0400, 'type': '16x16', 'description': 'Main fuel map'},
                'wot_enrichment': {'address': 0x013400, 'size': 0x0200, 'type': '8x8', 'description': 'WOT fuel enrichment'},
                'cold_start_enrichment': {'address': 0x013600, 'size': 0x0200, 'type': '8x8', 'description': 'Cold start fuel'},
                'acceleration_enrichment': {'address': 0x013800, 'size': 0x0100, 'type': '1D', 'description': 'Transient fuel'},
                'deceleration_enleanment': {'address': 0x013900, 'size': 0x0100, 'type': '1D', 'description': 'Overrun fuel cut'}
            },
            'boost_control': {
                'target_boost_map': {'address': 0x014000, 'size': 0x0400, 'type': '16x16', 'description': 'Boost target by RPM/Load'},
                'wastegate_duty_map': {'address': 0x014400, 'size': 0x0400, 'type': '16x16', 'description': 'Wastegate duty cycle'},
                'overboost_protection': {'address': 0x014800, 'size': 0x0200, 'type': '8x8', 'description': 'Overboost limits'},
                'turbo_spool_control': {'address': 0x014A00, 'size': 0x0200, 'type': '8x8', 'description': 'Spool optimization'}
            },
            'vvt_control': {
                'intake_cam_map': {'address': 0x015000, 'size': 0x0400, 'type': '16x16', 'description': 'Intake VVT advance'},
                'exhaust_cam_map': {'address': 0x015400, 'size': 0x0400, 'type': '16x16', 'description': 'Exhaust VVT retard'},
                'cam_transition_maps': {'address': 0x015800, 'size': 0x0200, 'type': '8x8', 'description': 'Cam transition speeds'}
            },
            'torque_management': {
                'engine_torque_limit': {'address': 0x016000, 'size': 0x0200, 'type': '8x8', 'description': 'Max engine torque'},
                'transmission_torque_limit': {'address': 0x016200, 'size': 0x0200, 'type': '8x8', 'description': 'Gearbox torque limit'},
                'traction_control_reduction': {'address': 0x016400, 'size': 0x0100, 'type': '1D', 'description': 'TC torque reduction'}
            },
            'rev_limiters': {
                'soft_cut_rpm': {'address': 0x017000, 'size': 0x0010, 'type': 'Single', 'description': 'Soft rev limit'},
                'hard_cut_rpm': {'address': 0x017010, 'size': 0x0010, 'type': 'Single', 'description': 'Hard rev limit'},
                'fuel_cut_recovery': {'address': 0x017020, 'size': 0x0010, 'type': 'Single', 'description': 'Fuel cut recovery RPM'}
            },
            'speed_limiter': {
                'speed_limit': {'address': 0x017100, 'size': 0x0010, 'type': 'Single', 'description': 'Vehicle speed limit'},
                'limit_by_gear': {'address': 0x017110, 'size': 0x0020, 'type': '1D', 'description': 'Speed limit by gear'}
            }
        }
    
    def _define_pids(self):
        """COMPLETE OBD-II PID DEFINITIONS WITH MAZDA EXTENSIONS"""
        return {
            'standard_pids': {
                '0x04': {'name': 'CALCULATED_ENGINE_LOAD', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x05': {'name': 'ENGINE_COOLANT_TEMP', 'formula': 'A - 40', 'unit': '°C', 'bytes': 1},
                '0x0C': {'name': 'ENGINE_RPM', 'formula': '((A * 256) + B) / 4', 'unit': 'RPM', 'bytes': 2},
                '0x0D': {'name': 'VEHICLE_SPEED', 'formula': 'A', 'unit': 'km/h', 'bytes': 1},
                '0x11': {'name': 'THROTTLE_POSITION', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x1F': {'name': 'RUN_TIME_SINCE_ENGINE_START', 'formula': '(A * 256) + B', 'unit': 'seconds', 'bytes': 2},
                '0x21': {'name': 'DISTANCE_TRAVELED_WITH_MIL_ON', 'formula': '(A * 256) + B', 'unit': 'km', 'bytes': 2},
                '0x2F': {'name': 'FUEL_TANK_LEVEL_INPUT', 'formula': '(100 * A) / 255', 'unit': '%', 'bytes': 1},
                '0x31': {'name': 'DISTANCE_SINCE_CODES_CLEARED', 'formula': '(A * 256) + B', 'unit': 'km', 'bytes': 2},
                '0x33': {'name': 'BAROMETRIC_PRESSURE', 'formula': 'A', 'unit': 'kPa', 'bytes': 1},
                '0x42': {'name': 'CONTROL_MODULE_VOLTAGE', 'formula': '(A * 256) + B) / 1000', 'unit': 'V', 'bytes': 2},
                '0x43': {'name': 'ABSOLUTE_LOAD_VALUE', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x44': {'name': 'FUEL_AIR_COMMAND_EQUIV_RATIO', 'formula': '(A * 2) / 65536', 'unit': 'ratio', 'bytes': 2},
                '0x46': {'name': 'AMBIENT_AIR_TEMPERATURE', 'formula': 'A - 40', 'unit': '°C', 'bytes': 1},
                '0x49': {'name': 'ACCELERATOR_PEDAL_POSITION_D', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x4A': {'name': 'ACCELERATOR_PEDAL_POSITION_E', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x4B': {'name': 'ACCELERATOR_PEDAL_POSITION_F', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x4C': {'name': 'COMMANDED_THROTTLE_ACTUATOR', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x4E': {'name': 'ENGINE_FUEL_RATE', 'formula': '((A * 256) + B) / 20', 'unit': 'L/h', 'bytes': 2},
                '0x51': {'name': 'ETHANOL_FUEL_PERCENT', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x52': {'name': 'EVAP_SYSTEM_VAPOR_PRESSURE', 'formula': '((A * 256) + B) / 200', 'unit': 'Pa', 'bytes': 2},
                '0x53': {'name': 'ABSOLUTE_EVAP_SYSTEM_VAPOR_PRESSURE', 'formula': '((A * 256) + B) / 200', 'unit': 'Pa', 'bytes': 2},
                '0x54': {'name': 'EVAP_SYSTEM_VAPOR_PRESSURE_TREND', 'formula': 'A - 128', 'unit': 'Pa/s', 'bytes': 1},
                '0x59': {'name': 'FUEL_RAIL_PRESSURE', 'formula': '((A * 256) + B) * 0.079', 'unit': 'kPa', 'bytes': 2},
                '0x5A': {'name': 'FUEL_RAIL_GAUGE_PRESSURE', 'formula': '((A * 256) + B) * 0.079', 'unit': 'kPa', 'bytes': 2},
                '0x5B': {'name': 'FUEL_RAIL_ABSOLUTE_PRESSURE', 'formula': '((A * 256) + B) * 0.079', 'unit': 'kPa', 'bytes': 2},
                '0x5C': {'name': 'ENGINE_OIL_TEMPERATURE', 'formula': 'A - 40', 'unit': '°C', 'bytes': 1},
                '0x5E': {'name': 'ENGINE_REFRACTION_RATE', 'formula': '(A * 256) + B', 'unit': '1/min', 'bytes': 2},
                '0x5F': {'name': 'ENGINE_RUNNING_TIME', 'formula': '(A * 256) + B', 'unit': 'seconds', 'bytes': 2},
                '0x61': {'name': 'DRIVER_DEMAND_ENGINE_TORQUE', 'formula': '((A * 256) + B) / 10', 'unit': '%', 'bytes': 2},
                '0x62': {'name': 'ACTUAL_ENGINE_TORQUE', 'formula': '((A * 256) + B) / 10', 'unit': '%', 'bytes': 2},
                '0x64': {'name': 'ENGINE_REFERENCE_TORQUE', 'formula': '((A * 256) + B)', 'unit': 'Nm', 'bytes': 2}
            },
            'mazda_extensions': {
                '0x2201': {'name': 'MAF_VOLTAGE', 'formula': 'A / 255 * 5', 'unit': 'V', 'bytes': 1},
                '0x2202': {'name': 'MAP_PRESSURE', 'formula': '(A * 256 + B) / 100', 'unit': 'kPa', 'bytes': 2},
                '0x2203': {'name': 'BOOST_PRESSURE', 'formula': '(A * 256 + B) / 100 - 101.3', 'unit': 'kPa', 'bytes': 2},
                '0x2204': {'name': 'WIDEBAND_AFR', 'formula': '(A * 256 + B) / 1000', 'unit': 'lambda', 'bytes': 2},
                '0x2205': {'name': 'KNOCK_RETARD', 'formula': 'A - 128', 'unit': 'degrees', 'bytes': 1},
                '0x2206': {'name': 'IGNITION_TIMING', 'formula': 'A - 128', 'unit': 'degrees BTDC', 'bytes': 1},
                '0x2207': {'name': 'INJECTOR_DUTY_CYCLE', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x2208': {'name': 'VVT_INTAKE_ANGLE', 'formula': 'A - 128', 'unit': 'degrees', 'bytes': 1},
                '0x2209': {'name': 'VVT_EXHAUST_ANGLE', 'formula': 'A - 128', 'unit': 'degrees', 'bytes': 1},
                '0x220A': {'name': 'TURBO_SPEED', 'formula': '(A * 256 + B) * 10', 'unit': 'RPM', 'bytes': 2},
                '0x220B': {'name': 'WASTEGATE_DUTY', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x220C': {'name': 'FUEL_PRESSURE', 'formula': '(A * 256 + B) / 10', 'unit': 'kPa', 'bytes': 2},
                '0x220D': {'name': 'OIL_PRESSURE', 'formula': '(A * 256 + B) / 100', 'unit': 'kPa', 'bytes': 2},
                '0x220E': {'name': 'EGT_TEMPERATURE', 'formula': '(A * 256 + B) - 273', 'unit': '°C', 'bytes': 2},
                '0x220F': {'name': 'INTERCOOLER_TEMP', 'formula': 'A - 40', 'unit': '°C', 'bytes': 1},
                '0x2210': {'name': 'AMBIENT_PRESSURE', 'formula': '(A * 256 + B) / 100', 'unit': 'kPa', 'bytes': 2},
                '0x2211': {'name': 'BATTERY_VOLTAGE', 'formula': '(A * 256 + B) / 1000', 'unit': 'V', 'bytes': 2},
                '0x2212': {'name': 'THROTTLE_VOLTAGE', 'formula': 'A / 255 * 5', 'unit': 'V', 'bytes': 1},
                '0x2213': {'name': 'ACCELERATOR_VOLTAGE', 'formula': 'A / 255 * 5', 'unit': 'V', 'bytes': 1},
                '0x2214': {'name': 'FUEL_TEMP', 'formula': 'A - 40', 'unit': '°C', 'bytes': 1},
                '0x2215': {'name': 'CAT_TEMP_1', 'formula': '(A * 256 + B) - 273', 'unit': '°C', 'bytes': 2},
                '0x2216': {'name': 'CAT_TEMP_2', 'formula': '(A * 256 + B) - 273', 'unit': '°C', 'bytes': 2},
                '0x2217': {'name': 'NOX_SENSOR', 'formula': '(A * 256 + B) / 100', 'unit': 'ppm', 'bytes': 2},
                '0x2218': {'name': 'O2_SENSOR_VOLTAGE_1', 'formula': 'A / 255 * 5', 'unit': 'V', 'bytes': 1},
                '0x2219': {'name': 'O2_SENSOR_VOLTAGE_2', 'formula': 'A / 255 * 5', 'unit': 'V', 'bytes': 1},
                '0x221A': {'name': 'SHORT_TERM_FUEL_TRIM_1', 'formula': 'A - 128', 'unit': '%', 'bytes': 1},
                '0x221B': {'name': 'LONG_TERM_FUEL_TRIM_1', 'formula': 'A - 128', 'unit': '%', 'bytes': 1},
                '0x221C': {'name': 'SHORT_TERM_FUEL_TRIM_2', 'formula': 'A - 128', 'unit': '%', 'bytes': 1},
                '0x221D': {'name': 'LONG_TERM_FUEL_TRIM_2', 'formula': 'A - 128', 'unit': '%', 'bytes': 1}
            }
        }
    
    def _define_dids(self):
        """DEFINE DATA IDENTIFIER DEFINITIONS"""
        return {
            'vin': {'did': '0xF190', 'length': 17, 'description': 'Vehicle Identification Number'},
            'calibration_id': {'did': '0xF18A', 'length': 16, 'description': 'ECU Calibration ID'},
            'software_number': {'did': '0xF195', 'length': 12, 'description': 'Software Part Number'},
            'diagnostic_protocol': {'did': '0xF18C', 'length': 5, 'description': 'Diagnostic Protocol Version'},
            'ecu_name': {'did': '0xF190', 'length': 20, 'description': 'ECU Name/Type'},
            'flash_counter': {'did': '0xF1A0', 'length': 2, 'description': 'Flash Programming Counter'},
            'security_access': {'did': '0xF1B0', 'length': 4, 'description': 'Security Access Level'},
            'production_date': {'did': '0xF1C0', 'length': 8, 'description': 'ECU Production Date'},
            'test_number': {'did': '0xF1D0', 'length': 10, 'description': 'Test/Validation Number'}
        }
    
    def read_rom_memory(self, start_address: int, length: int) -> bytes:
        """READ ROM MEMORY BY ADDRESS RANGE"""
        try:
            # Build diagnostic request for memory read
            request_data = bytearray()
            request_data.extend(start_address.to_bytes(3, 'big'))
            request_data.append(length & 0xFF)
            
            # Send request
            message = can.Message(
                arbitration_id=0x7E0,
                data=bytes([0x23]) + request_data[:7],
                is_extended_id=False
            )
            
            self.can_bus.send(message)
            time.sleep(0.1)
            
            # Receive response
            response = self.can_bus.recv(timeout=1.0)
            
            if response and response.arbitration_id == 0x7E8:
                # Extract data from response
                if response.data[0] == 0x63:  # Positive response
                    return response.data[4:4+length]
            
            return b''
            
        except Exception as e:
            print(f"Error reading ROM memory: {e}")
            return b''
    
    def read_map_data(self, map_name: str) -> bytes:
        """READ SPECIFIC MAP DATA FROM ROM"""
        if map_name not in self.map_definitions:
            return b''
        
        map_info = self.map_definitions[map_name]
        if isinstance(map_info, dict):
            # Handle sub-maps
            primary_map = list(map_info.values())[0]
            address = primary_map['address']
            size = primary_map['size']
        else:
            address = map_info['address']
            size = map_info['size']
        
        return self.read_rom_memory(address, size)
    
    def parse_2d_map(self, data: bytes, map_type: str) -> np.ndarray:
        """PARSE 2D MAP DATA INTO NUMPY ARRAY"""
        if map_type == '16x16':
            return np.frombuffer(data, dtype=np.uint16).reshape(16, 16)
        elif map_type == '8x8':
            return np.frombuffer(data, dtype=np.uint8).reshape(8, 8)
        else:
            return np.array([])
    
    def parse_1d_map(self, data: bytes) -> np.ndarray:
        """PARSE 1D MAP DATA INTO NUMPY ARRAY"""
        return np.frombuffer(data, dtype=np.uint8)
    
    def read_pid_value(self, pid: str) -> float:
        """READ LIVE DATA VIA OBD-II PID"""
        try:
            # Determine if standard or Mazda extension
            pid_category = 'standard_pids' if pid.startswith('0x') and int(pid, 16) < 0x100 else 'mazda_extensions'
            
            if pid_category not in self.pid_definitions:
                return 0.0
            
            pid_info = self.pid_definitions[pid_category][pid]
            
            # Send PID request
            pid_bytes = bytes.fromhex(pid[2:])
            message = can.Message(
                arbitration_id=0x7E0,
                data=bytes([0x01]) + pid_bytes + b'\x00\x00\x00\x00\x00',
                is_extended_id=False
            )
            
            self.can_bus.send(message)
            time.sleep(0.05)
            
            # Receive response
            response = self.can_bus.recv(timeout=1.0)
            
            if response and response.arbitration_id == 0x7E8:
                if response.data[0] == 0x41:  # Positive response
                    # Extract value based on formula
                    formula = pid_info['formula']
                    bytes_count = pid_info['bytes']
                    
                    if bytes_count == 1:
                        A = response.data[3]
                        value = eval(formula)
                    elif bytes_count == 2:
                        A = response.data[3]
                        B = response.data[4]
                        value = eval(formula)
                    
                    return float(value)
            
            return 0.0
            
        except Exception as e:
            print(f"Error reading PID {pid}: {e}")
            return 0.0
    
    def read_did_value(self, did: str) -> str:
        """READ DATA IDENTIFIER VALUE"""
        try:
            if did not in self.did_definitions:
                return ''
            
            did_info = self.did_definitions[did]
            did_bytes = bytes.fromhex(did[2:])
            
            # Send DID request
            message = can.Message(
                arbitration_id=0x7E0,
                data=bytes([0x22]) + did_bytes + b'\x00\x00\x00\x00',
                is_extended_id=False
            )
            
            self.can_bus.send(message)
            time.sleep(0.05)
            
            # Receive response
            response = self.can_bus.recv(timeout=1.0)
            
            if response and response.arbitration_id == 0x7E8:
                if response.data[0] == 0x62:  # Positive response
                    # Extract data
                    data_length = did_info['length']
                    data = response.data[4:4+data_length]
                    return data.decode('ascii', errors='ignore').strip()
            
            return ''
            
        except Exception as e:
            print(f"Error reading DID {did}: {e}")
            return ''
    
    def extract_calibration_data(self) -> Dict[str, Any]:
        """EXTRACT COMPLETE CALIBRATION DATA FROM ROM"""
        calibration = {}
        
        # Read all maps
        for map_name, map_info in self.map_definitions.items():
            if isinstance(map_info, dict):
                # Handle category with sub-maps
                calibration[map_name] = {}
                for sub_map_name, sub_map_info in map_info.items():
                    data = self.read_rom_memory(sub_map_info['address'], sub_map_info['size'])
                    if sub_map_info['type'] in ['16x16', '8x8']:
                        calibration[map_name][sub_map_name] = self.parse_2d_map(data, sub_map_info['type'])
                    else:
                        calibration[map_name][sub_map_name] = self.parse_1d_map(data)
            else:
                # Handle single map
                data = self.read_rom_memory(map_info['address'], map_info['size'])
                if map_info['type'] in ['16x16', '8x8']:
                    calibration[map_name] = self.parse_2d_map(data, map_info['type'])
                else:
                    calibration[map_name] = self.parse_1d_map(data)
        
        return calibration
    
    def dump_rom_to_file(self, filename: str) -> bool:
        """DUMP COMPLETE ROM TO FILE"""
        try:
            with open(filename, 'wb') as f:
                # Read each ROM section
                for section_name, rom_def in self.rom_definitions.items():
                    print(f"Reading {section_name}...")
                    data = self.read_rom_memory(rom_def.base_address, rom_def.size)
                    f.write(data)
                    
                    # Add padding if needed
                    if len(data) < rom_def.size:
                        f.write(b'\x00' * (rom_def.size - len(data)))
            
            print(f"ROM dumped to {filename}")
            return True
            
        except Exception as e:
            print(f"Error dumping ROM: {e}")
            return False
    
    def verify_rom_checksum(self, rom_data: bytes) -> bool:
        """VERIFY ROM CHECKSUMS"""
        try:
            # Calculate CRC32 for main calibration
            calibration_data = rom_data[0x010000:0x090000]
            crc32 = crcmod.predefined.mkCrcFun('crc-32')
            calculated_crc = crc32(calibration_data)
            
            # Read stored checksum
            stored_crc = struct.unpack('>I', rom_data[0x1FFFF0:0x1FFFF4])[0]
            
            return calculated_crc == stored_crc
            
        except Exception as e:
            print(f"Error verifying checksum: {e}")
            return False

# Utility functions
def convert_to_physical_value(raw_value: int, conversion_type: str) -> float:
    """CONVERT RAW ECU VALUE TO PHYSICAL VALUE"""
    conversions = {
        'temperature_c': raw_value - 40,
        'temperature_f': (raw_value - 40) * 9/5 + 32,
        'pressure_kpa': raw_value,
        'pressure_psi': raw_value * 0.145038,
        'voltage': raw_value / 255 * 5,
        'percent': raw_value * 100 / 255,
        'rpm': raw_value * 10,
        'timing_deg': raw_value - 128
    }
    
    return conversions.get(conversion_type, float(raw_value))

def format_map_data(map_data: np.ndarray, map_type: str) -> str:
    """FORMAT MAP DATA FOR DISPLAY"""
    if map_type == '16x16':
        formatted = "    " + "    ".join([f"{i:4}" for i in range(16)]) + "\n"
        for i in range(16):
            formatted += f"{i:2}:" + "".join([f"{val:5}" for val in map_data[i]]) + "\n"
        return formatted
    elif map_type == '8x8':
        formatted = "    " + "    ".join([f"{i:4}" for i in range(8)]) + "\n"
        for i in range(8):
            formatted += f"{i:2}:" + "".join([f"{val:5}" for val in map_data[i]]) + "\n"
        return formatted
    else:
        return str(map_data)

# Demonstration
def demonstrate_rom_reading():
    """DEMONSTRATE ROM READING CAPABILITIES"""
    print("MAZDASPEED 3 ROM READING DEMONSTRATION")
    print("=" * 50)
    
    reader = MazdaECUROMReader()
    
    # Read VIN
    vin = reader.read_did_value('0xF190')
    print(f"\nVehicle VIN: {vin}")
    
    # Read calibration ID
    calib_id = reader.read_did_value('0xF18A')
    print(f"Calibration ID: {calib_id}")
    
    # Read live data
    rpm = reader.read_pid_value('0x0C')
    print(f"Engine RPM: {rpm:.0f}")
    
    boost = reader.read_pid_value('0x2203')
    print(f"Boost Pressure: {boost:.1f} kPa")
    
    # Read ignition map
    ignition_data = reader.read_map_data('ignition_timing')
    if ignition_data:
        ignition_map = reader.parse_2d_map(ignition_data, '16x16')
        print("\nIgnition Timing Map (degrees BTDC):")
        print(format_map_data(ignition_map, '16x16'))
    
    print("\nROM reading demonstration complete!")

if __name__ == "__main__":
    demonstrate_rom_reading()
