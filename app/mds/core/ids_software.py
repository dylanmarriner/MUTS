#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDA IDS/M-MDS REVERSE ENGINEERED SOFTWARE
Complete diagnostic and programming system for Mazda vehicles
"""

import logging
import sys
import argparse
from typing import Dict, List, Any, Optional

# Import our modules
from ..protocols.diagnostic_protocols import MazdaDiagnosticProtocol, DiagnosticSession
from ..security.security_algorithms import MazdaSecurityAccess, MazdaSecurityAlgorithm
from ..diagnostics.diagnostic_database import MazdaDTCDatabase
from ..calibration.calibration_files import MazdaCalibrationDatabase
from ..programming.programming_routines import MazdaProgrammingService
from ..interface.j2534_interface import J2534Interface

class MazdaIDS:
    """
    Complete Mazda IDS/M-MDS Software Implementation
    Main application class combining all components
    """
    
    def __init__(self):
        self.setup_logging()
        
        # Initialize components
        self.diagnostic_protocol = MazdaDiagnosticProtocol()
        self.security_access = MazdaSecurityAccess()
        self.dtc_database = MazdaDTCDatabase()
        self.calibration_database = MazdaCalibrationDatabase()
        self.programming_service = MazdaProgrammingService(self.diagnostic_protocol)
        self.j2534_interface = J2534Interface()
        
        self.vehicle_connected = False
        self.current_vehicle_info = {}
        
        logger.info("Mazda IDS/M-MDS Software Initialized")
    
    def setup_logging(self):
        """Setup application logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mazda_ids.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        global logger
        logger = logging.getLogger(__name__)
    
    def connect_to_vehicle(self) -> bool:
        """Connect to vehicle using J2534 interface"""
        try:
            logger.info("Connecting to vehicle...")
            
            # Connect J2534 device
            if not self.j2534_interface.pass_thru_open():
                logger.error("Failed to connect J2534 device")
                return False
            
            # Connect to vehicle channel (CAN protocol)
            if not self.j2534_interface.pass_thru_connect(
                protocol=self.j2534_interface.J2534Protocol.ISO15765,
                baudrate=500000
            ):
                logger.error("Failed to connect to vehicle channel")
                return False
            
            # Initialize diagnostic protocol with J2534 interface
            self.diagnostic_protocol.j2534_interface = self.j2534_interface
            
            # Test vehicle communication
            if not self.diagnostic_protocol.connect_to_vehicle():
                logger.error("Failed to establish vehicle communication")
                return False
            
            # Read vehicle identification
            vehicle_info = self.read_vehicle_information()
            if vehicle_info:
                self.current_vehicle_info = vehicle_info
                logger.info(f"Connected to vehicle: {vehicle_info.get('vin', 'Unknown')}")
                self.vehicle_connected = True
                return True
            else:
                logger.error("Failed to read vehicle information")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to vehicle: {e}")
            return False
    
    def read_vehicle_information(self) -> Optional[Dict[str, Any]]:
        """Read complete vehicle information"""
        try:
            vehicle_info = {}
            
            # Read VIN
            vin_data = self.diagnostic_protocol.read_data_by_identifier(0xF190)
            if vin_data:
                vehicle_info['vin'] = vin_data.decode('ascii', errors='ignore').strip()
            
            # Read ECU part number
            ecu_data = self.diagnostic_protocol.read_data_by_identifier(0xF18C)
            if ecu_data:
                vehicle_info['ecu_part_number'] = ecu_data.decode('ascii', errors='ignore').strip()
            
            # Read software version
            sw_data = self.diagnostic_protocol.read_data_by_identifier(0xF195)
            if sw_data:
                vehicle_info['software_version'] = sw_data.decode('ascii', errors='ignore').strip()
            
            # Read calibration ID
            calib_data = self.diagnostic_protocol.read_data_by_identifier(0xF186)
            if calib_data:
                vehicle_info['calibration_id'] = calib_data.decode('ascii', errors='ignore').strip()
            
            return vehicle_info if vehicle_info else None
            
        except Exception as e:
            logger.error(f"Error reading vehicle information: {e}")
            return None
    
    def disconnect_from_vehicle(self):
        """Disconnect from vehicle"""
        try:
            if self.vehicle_connected:
                # Disconnect diagnostic protocol
                self.diagnostic_protocol.disconnect()
                
                # Disconnect J2534 channel
                self.j2534_interface.pass_thru_disconnect()
                
                # Close J2534 device
                self.j2534_interface.pass_thru_close()
                
                self.vehicle_connected = False
                self.current_vehicle_info = {}
                logger.info("Disconnected from vehicle")
                
        except Exception as e:
            logger.error(f"Error disconnecting from vehicle: {e}")
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """Run complete vehicle diagnostic"""
        try:
            if not self.vehicle_connected:
                logger.error("Vehicle not connected")
                return {}
            
            diagnostic_results = {
                'timestamp': None,
                'dtcs': [],
                'freeze_frames': [],
                'readiness_status': {},
                'live_data': {}
            }
            
            # Read DTCs
            dtc_info = self.diagnostic_protocol.read_dtc_information(0x02)
            if dtc_info:
                diagnostic_results['dtcs'] = dtc_info.get('dtc_list', [])
            
            # Read readiness status
            readiness_data = self.diagnostic_protocol.read_data_by_identifier(0x0101)
            if readiness_data:
                diagnostic_results['readiness_status'] = self._parse_readiness_status(readiness_data)
            
            # Read live data
            diagnostic_results['live_data'] = self._read_live_data()
            
            diagnostic_results['timestamp'] = sys.time.time()
            
            return diagnostic_results
            
        except Exception as e:
            logger.error(f"Error running diagnostic: {e}")
            return {}
    
    def _parse_readiness_status(self, data: bytes) -> Dict[str, bool]:
        """Parse readiness status from data"""
        readiness = {}
        
        # Define monitor bits
        monitors = {
            'misfire': 0,
            'fuel_system': 1,
            'components': 2,
            'catalyst': 3,
            'heated_catalyst': 4,
            'evap_system': 5,
            'secondary_air': 6,
            'ac_system': 7,
            'oxygen_sensor': 8,
            'oxygen_sensor_heater': 9,
            'egr_system': 10
        }
        
        if len(data) >= 2:
            status_byte = data[0]
            for monitor, bit in monitors.items():
                readiness[monitor] = bool(status_byte & (1 << bit))
        
        return readiness
    
    def _read_live_data(self) -> Dict[str, float]:
        """Read live data from vehicle"""
        live_data = {}
        
        # Define PIDs to read
        pids = {
            'engine_rpm': 0x0C,
            'vehicle_speed': 0x0D,
            'throttle_position': 0x11,
            'engine_load': 0x04,
            'coolant_temp': 0x05,
            'intake_air_temp': 0x0F,
            'maf_flow': 0x10,
            'map_pressure': 0x0B,
            'fuel_pressure': 0x0A,
            'timing_advance': 0x0E
        }
        
        for name, pid in pids.items():
            try:
                data = self.diagnostic_protocol.read_data_by_identifier(pid)
                if data:
                    live_data[name] = self._convert_pid_value(pid, data)
            except Exception as e:
                logger.warning(f"Failed to read {name}: {e}")
        
        return live_data
    
    def _convert_pid_value(self, pid: int, data: bytes) -> float:
        """Convert raw PID data to engineering units"""
        if len(data) < 2:
            return 0.0
        
        # Standard SAE J1979 conversions
        value = (data[0] << 8) | data[1]
        
        if pid == 0x0C:  # Engine RPM
            return value / 4.0
        elif pid == 0x0D:  # Vehicle Speed
            return value
        elif pid == 0x11:  # Throttle Position
            return value * 100 / 255.0
        elif pid == 0x04:  # Engine Load
            return value * 100 / 255.0
        elif pid == 0x05:  # Coolant Temperature
            return value - 40.0
        elif pid == 0x0F:  # Intake Air Temperature
            return value - 40.0
        elif pid == 0x10:  # MAF Flow
            return value / 100.0
        elif pid == 0x0B:  # MAP Pressure
            return value
        elif pid == 0x0A:  # Fuel Pressure
            return value * 3.0
        elif pid == 0x0E:  # Timing Advance
            return value / 2.0 - 64.0
        
        return float(value)
    
    def clear_dtcs(self) -> bool:
        """Clear all diagnostic trouble codes"""
        try:
            if not self.vehicle_connected:
                logger.error("Vehicle not connected")
                return False
            
            result = self.diagnostic_protocol.clear_diagnostic_information()
            if result:
                logger.info("DTCs cleared successfully")
            else:
                logger.error("Failed to clear DTCs")
            
            return result
            
        except Exception as e:
            logger.error(f"Error clearing DTCs: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return {
            'vehicle_connected': self.vehicle_connected,
            'vehicle_info': self.current_vehicle_info,
            'j2534_connected': self.j2534_interface.is_connected,
            'j2534_device_id': self.j2534_interface.device_id,
            'j2534_channel_id': self.j2534_interface.channel_id,
            'diagnostic_protocol': self.diagnostic_protocol.protocol.name,
            'current_session': self.diagnostic_protocol.current_session.name
        }

def main():
    """Main entry point for Mazda IDS software"""
    parser = argparse.ArgumentParser(description='Mazda IDS/M-MDS Software')
    parser.add_argument('--connect', action='store_true', help='Connect to vehicle')
    parser.add_argument('--diagnostic', action='store_true', help='Run full diagnostic')
    parser.add_argument('--clear-dtcs', action='store_true', help='Clear DTCs')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    # Initialize IDS software
    ids = MazdaIDS()
    
    try:
        if args.connect:
            if ids.connect_to_vehicle():
                print("Successfully connected to vehicle")
            else:
                print("Failed to connect to vehicle")
                return 1
        
        if args.diagnostic:
            results = ids.run_full_diagnostic()
            print(f"Diagnostic Results: {results}")
        
        if args.clear_dtcs:
            if ids.clear_dtcs():
                print("DTCs cleared successfully")
            else:
                print("Failed to clear DTCs")
        
        if args.status:
            status = ids.get_system_status()
            print(f"System Status: {status}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        ids.disconnect_from_vehicle()

if __name__ == '__main__':
    sys.exit(main())
