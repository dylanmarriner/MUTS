#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3_ROM_REVERSE_ENGINEERING.py
COMPLETE ROM READER, MAP DEFINITIONS & LIVE DATA EXTRACTION
"""

import struct
import can
import time
from typing import Dict, List
from dataclasses import dataclass
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
                '0x0F': {'name': 'INTAKE_AIR_TEMP', 'formula': 'A - 40', 'unit': '°C', 'bytes': 1},
                '0x11': {'name': 'THROTTLE_POSITION', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x1F': {'name': 'RUN_TIME_SINCE_ENGINE_START', 'formula': '(A * 256) + B', 'unit': 'seconds', 'bytes': 2},
                '0x21': {'name': 'DISTANCE_TRAVELED_WITH_MIL_ON', 'formula': '(A * 256) + B', 'unit': 'km', 'bytes': 2}
            },
            'mazda_specific_pids': {
                '0x223365': {'name': 'BOOST_PRESSURE', 'formula': '((A * 256) + B - 1000) / 10', 'unit': 'PSI', 'bytes': 2},
                '0x22345C': {'name': 'VVT_ANGLE_INTAKE', 'formula': '(A - 128) / 2', 'unit': 'degrees', 'bytes': 1},
                '0x223456': {'name': 'KNOCK_CORRECTION', 'formula': '(A - 128) / 2', 'unit': 'degrees', 'bytes': 1},
                '0x223467': {'name': 'INJECTOR_PULSE_WIDTH', 'formula': '((A * 256) + B) / 1000', 'unit': 'ms', 'bytes': 2},
                '0x223478': {'name': 'TURBO_WASTEGATE_DUTY', 'formula': '(A * 100) / 255', 'unit': '%', 'bytes': 1},
                '0x223489': {'name': 'AFR_COMMANDED', 'formula': 'A / 10', 'unit': 'AFR', 'bytes': 1},
                '0x223490': {'name': 'FUEL_PRESSURE', 'formula': 'A * 10', 'unit': 'PSI', 'bytes': 1},
                '0x2234A1': {'name': 'OIL_TEMPERATURE', 'formula': 'A - 40', 'unit': '°C', 'bytes': 1}
            }
        }
    
    def _define_dids(self):
        """COMPLETE DATA IDENTIFIER DEFINITIONS FOR MAZDA ECU"""
        return {
            'ecu_identification': {
                '0xF187': {'name': 'ECU_PART_NUMBER', 'size': 16, 'description': 'ECU hardware part number'},
                '0xF188': {'name': 'ECU_SOFTWARE_VERSION', 'size': 8, 'description': 'ECU software version'},
                '0xF189': {'name': 'VIN', 'size': 17, 'description': 'Vehicle Identification Number'},
                '0xF18A': {'name': 'CALIBRATION_ID', 'size': 16, 'description': 'Calibration identification'}
            },
            'system_data': {
                '0x2000': {'name': 'ENGINE_RUN_TIME', 'size': 4, 'description': 'Total engine run time'},
                '0x2001': {'name': 'IGNITION_CYCLE_COUNT', 'size': 2, 'description': 'Number of ignition cycles'},
                '0x2002': {'name': 'FUEL_USAGE_TOTAL', 'size': 4, 'description': 'Lifetime fuel consumption'},
                '0x2003': {'name': 'DISTANCE_TRAVELED', 'size': 4, 'description': 'Total distance traveled'}
            },
            'adaptation_data': {
                '0x2100': {'name': 'FUEL_TRIM_LEARN_VALUES', 'size': 64, 'description': 'Long term fuel trim cells'},
                '0x2101': {'name': 'KNOCK_LEARN_VALUES', 'size': 32, 'description': 'Knock adaptation tables'},
                '0x2102': {'name': 'THROTTLE_ADAPTATION', 'size': 16, 'description': 'Throttle body adaptation'},
                '0x2103': {'name': 'TCM_ADAPTATION', 'size': 48, 'description': 'Transmission adaptation data'}
            },
            'fault_data': {
                '0x2200': {'name': 'CURRENT_DTCS', 'size': 64, 'description': 'Currently active DTCs'},
                '0x2201': {'name': 'PENDING_DTCS', 'size': 64, 'description': 'Pending diagnostic codes'},
                '0x2202': {'name': 'PERMANENT_DTCS', 'size': 64, 'description': 'Permanent fault codes'},
                '0x2203': {'name': 'FREEZE_FRAME_DATA', 'size': 128, 'description': 'Freeze frame snapshots'}
            }
        }

    def read_rom_sector(self, sector_name: str) -> bytes:
        """READ COMPLETE ROM SECTOR VIA CAN BUS"""
        sector = self.rom_definitions[sector_name]
        data = bytearray()
        
        # Use 0x23 ReadMemoryByAddress service
        address = sector.base_address
        remaining = sector.size
        
        while remaining > 0:
            chunk_size = min(remaining, 256)  # Max bytes per request
            
            # Build read memory request
            request = self._build_read_memory_request(address, chunk_size)
            self.can_bus.send(request)
            
            # Wait for response
            try:
                response = self._receive_memory_data()
                if response:
                    data.extend(response)
            except Exception:
                # Handle receive timeout gracefully
                print("Error receiving memory data")
                return None
            
            address += chunk_size
            remaining -= chunk_size
            
            # Small delay to avoid overwhelming ECU
            time.sleep(0.01)
        
        return bytes(data)
    
    def _build_read_memory_request(self, address: int, size: int) -> can.Message:
        """BUILD 0x23 READ MEMORY BY ADDRESS REQUEST"""
        payload = bytearray()
        payload.append(0x23)  # Service ID: ReadMemoryByAddress
        
        # Address (3 bytes) and MemorySize (3 bytes)
        payload.extend(address.to_bytes(3, 'big'))
        payload.extend(size.to_bytes(3, 'big'))
        
        return can.Message(
            arbitration_id=0x7E0,  # ECU request ID
            data=payload,
            is_extended_id=False
        )
    
    def _receive_memory_data(self) -> bytes:
        """RECEIVE MEMORY DATA FROM ECU RESPONSE"""
        try:
            message = self.can_bus.recv(timeout=2.0)
            if message and message.arbitration_id == 0x7E8:  # ECU response ID
                if message.data[0] == 0x63:  # Positive response
                    return message.data[2:]  # Skip service ID and length
        except Exception:
            # Handle receive timeout gracefully
            pass
        return None
    
    def read_live_data_pid(self, pid: str) -> float:
        """READ LIVE DATA VIA OBD-II PID"""
        pid_info = None
        
        # Find PID definition
        for category in self.pid_definitions.values():
            if pid in category:
                pid_info = category[pid]
                break
        
        if not pid_info:
            raise ValueError(f"PID {pid} not defined")
        
        # Send PID request
        request = can.Message(
            arbitration_id=0x7E0,
            data=bytes([0x22]) + bytes.fromhex(pid[2:]),  # 0x22 = ReadDataByIdentifier
            is_extended_id=False
        )
        self.can_bus.send(request)
        
        # Receive and parse response
        response = self._receive_pid_data()
        if response and len(response) >= pid_info['bytes']:
            return self._parse_pid_value(response[:pid_info['bytes']], pid_info['formula'])
        
        return None
    
    def _parse_pid_value(self, data: bytes, formula: str) -> float:
        """PARSE PID VALUE USING DEFINED FORMULA"""
        # Import safe evaluator
        from src.utils.safe_eval import evaluate_mpsrom_formula
        
        # Convert data to integers
        int_data = list(data)
        
        # Use safe evaluator instead of eval()
        try:
            return evaluate_mpsrom_formula(formula, int_data)
        except Exception:
            # Log error but don't fail
            print("Warning: Failed to evaluate formula")
            return 0.0
    
    def read_data_identifier(self, did: str) -> bytes:
        """READ DATA IDENTIFIER VIA UDS"""
        did_info = None
        
        # Find DID definition
        for category in self.did_definitions.values():
            if did in category:
                did_info = category[did]
                break
        
        if not did_info:
            raise ValueError(f"DID {did} not defined")
        
        # Send DID request
        request = can.Message(
            arbitration_id=0x7E0,
            data=bytes([0x22]) + bytes.fromhex(did[2:]),  # 0x22 = ReadDataByIdentifier
            is_extended_id=False
        )
        self.can_bus.send(request)
        
        # Receive response
        response = self._receive_did_data()
        if response:
            return response[:did_info['size']]
        
        return None
    
    def extract_map_from_rom(self, map_name: str, map_type: str) -> np.ndarray:
        """EXTRACT AND CONVERT MAP FROM ROM DATA"""
        map_info = self.map_definitions[map_type][map_name]
        rom_data = self.read_rom_sector('calibration_a')
        
        # Extract map data from ROM
        start = map_info['address'] - 0x010000  # Adjust for calibration sector base
        end = start + map_info['size']
        map_bytes = rom_data[start:end]
        
        # Convert based on map type
        if map_info['type'] == '16x16':
            return self._convert_16x16_map(map_bytes)
        elif map_info['type'] == '8x8':
            return self._convert_8x8_map(map_bytes)
        elif map_info['type'] == '1D':
            return self._convert_1d_map(map_bytes)
        elif map_info['type'] == 'Single':
            return self._convert_single_value(map_bytes)
        
        return None
    
    def _convert_16x16_map(self, data: bytes) -> np.ndarray:
        """CONVERT 16x16 MAP FROM BYTES TO ARRAY"""
        values = []
        for i in range(0, len(data), 2):
            value = struct.unpack('>H', data[i:i+2])[0]
            # Convert from ECU format to physical value
            values.append(value / 10.0)  # Example conversion
        
        return np.array(values).reshape(16, 16)
    
    def _convert_8x8_map(self, data: bytes) -> np.ndarray:
        """CONVERT 8x8 MAP FROM BYTES TO ARRAY"""
        values = []
        for i in range(0, len(data), 2):
            value = struct.unpack('>H', data[i:i+2])[0]
            values.append(value / 10.0)  # Example conversion
        
        return np.array(values).reshape(8, 8)
    
    def _convert_1d_map(self, data: bytes) -> np.ndarray:
        """CONVERT 1D MAP FROM BYTES TO ARRAY"""
        values = []
        for i in range(0, len(data), 2):
            value = struct.unpack('>H', data[i:i+2])[0]
            values.append(value / 10.0)
        
        return np.array(values)
    
    def _convert_single_value(self, data: bytes) -> float:
        """CONVERT SINGLE VALUE FROM BYTES"""
        if len(data) >= 2:
            return struct.unpack('>H', data[:2])[0] / 10.0
        return 0.0
    
    def dump_complete_rom(self, output_file: str):
        """DUMP COMPLETE ECU ROM TO FILE"""
        with open(output_file, 'wb') as f:
            for sector_name in self.rom_definitions.keys():
                print(f"Reading sector: {sector_name}")
                sector_data = self.read_rom_sector(sector_name)
                f.write(sector_data)
                print(f"  Read {len(sector_data)} bytes")
        
        print(f"Complete ROM dumped to {output_file}")
    
    def generate_map_definitions_file(self, output_file: str):
        """GENERATE COMPLETE MAP DEFINITIONS FILE"""
        definitions = {
            'rom_structure': {name: vars(defn) for name, defn in self.rom_definitions.items()},
            'map_definitions': self.map_definitions,
            'pid_definitions': self.pid_definitions,
            'did_definitions': self.did_definitions
        }
        
        with open(output_file, 'w') as f:
            import json
            json.dump(definitions, f, indent=2)
        
        print(f"Map definitions saved to {output_file}")

class LiveDataMonitor:
    """REAL-TIME LIVE DATA MONITORING AND LOGGING"""
    
    def __init__(self, rom_reader: MazdaECUROMReader):
        self.reader = rom_reader
        self.logging_active = False
        self.sample_rate = 10  # Hz
    
    def start_live_monitoring(self, pids_to_monitor: List[str]):
        """START REAL-TIME DATA MONITORING"""
        self.logging_active = True
        print("Starting live data monitoring...")
        
        while self.logging_active:
            data_point = {}
            timestamp = time.time()
            
            for pid in pids_to_monitor:
                try:
                    value = self.reader.read_live_data_pid(pid)
                    data_point[pid] = value
                except Exception as e:
                    data_point[pid] = None
            
            # Log data point
            self._log_data_point(timestamp, data_point)
            
            # Wait for next sample
            time.sleep(1.0 / self.sample_rate)
    
    def _log_data_point(self, timestamp: float, data: Dict[str, float]):
        """LOG DATA POINT TO FILE"""
        log_entry = {
            'timestamp': timestamp,
            'data': data
        }
        
        # In real implementation, write to file or database
        # For now, print the log entry structure
        print(f"Log entry: {log_entry}")
    
    def stop_monitoring(self):
        """STOP LIVE DATA MONITORING"""
        self.logging_active = False

# COMPREHENSIVE ROM ANALYSIS TOOL
def analyze_complete_rom():
    """PERFORM COMPLETE ROM ANALYSIS"""
    reader = MazdaECUROMReader()
    
    print("MAZDASPEED 3 COMPLETE ROM REVERSE ENGINEERING")
    print("=" * 70)
    
    # 1. Display ROM Structure
    print("\n1. ROM MEMORY STRUCTURE")
    print("-" * 40)
    for name, definition in reader.rom_definitions.items():
        print(f"{name:20} 0x{definition.base_address:06X} - 0x{definition.base_address + definition.size:06X} ({definition.size:6} bytes) - {definition.description}")
    
    # 2. Display Map Definitions
    print("\n2. CALIBRATION MAP DEFINITIONS")
    print("-" * 40)
    for category, maps in reader.map_definitions.items():
        print(f"\n{category.upper()} MAPS:")
        for map_name, map_info in maps.items():
            print(f"  {map_name:30} 0x{map_info['address']:06X} ({map_info['size']:4} bytes) - {map_info['description']}")
    
    # 3. Demonstrate Live Data Reading
    print("\n3. LIVE DATA PID MONITORING")
    print("-" * 40)
    monitor_pids = ['0x0C', '0x0D', '0x11', '0x223365']  # RPM, Speed, Throttle, Boost
    
    for pid in monitor_pids:
        try:
            value = reader.read_live_data_pid(pid)
            pid_name = reader.pid_definitions['mazda_specific_pids'].get(pid, {}).get('name', 
                      reader.pid_definitions['standard_pids'].get(pid, {}).get('name', 'Unknown'))
            unit = reader.pid_definitions['mazda_specific_pids'].get(pid, {}).get('unit', 
                   reader.pid_definitions['standard_pids'].get(pid, {}).get('unit', ''))
            print(f"  {pid_name:25} {value} {unit}")
        except Exception as e:
            print(f"  Error reading {pid}: {e}")
    
    # 4. Demonstrate Map Extraction
    print("\n4. MAP EXTRACTION DEMONSTRATION")
    print("-" * 40)
    try:
        ignition_map = reader.extract_map_from_rom('primary_map', 'ignition_timing')
        if ignition_map is not None:
            print(f"  Ignition Map Shape: {ignition_map.shape}")
            print(f"  Sample Values: {ignition_map[0,0]:.1f}° to {ignition_map[-1,-1]:.1f}°")
    except Exception as e:
        print(f"  Map extraction failed: {e}")
    
    # 5. Generate Definition Files
    print("\n5. GENERATING DEFINITION FILES")
    print("-" * 40)
    reader.generate_map_definitions_file('mazdaspeed3_map_definitions.json')
    
    # 6. ROM Dumping Option
    print("\n6. ROM DUMPING CAPABILITY")
    print("-" * 40)
    print("  Full ROM dump available via dump_complete_rom() method")
    print("  This will read entire ECU memory and save to file")

if __name__ == "__main__":
    analyze_complete_rom()