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
from core.diagnostic_protocols import MazdaDiagnosticProtocol, DiagnosticSession
from core.security_access import MazdaSecurityAccess, MazdaSecurityAlgorithm
from databases.dtc_database import MazdaDTCDatabase
from databases.calibration_database import MazdaCalibrationDatabase
from services.programming_services import MazdaProgrammingService
from interfaces.j2534_interface import J2534Interface

class MazdaIDSSoftware:
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
            if not self.j2534_interface.connect():
                logger.error("Failed to connect J2534 device")
                return False
            
            # Connect to vehicle channel (CAN protocol)
            if not self.j2534_interface.connect_channel(
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
            
            # Start diagnostic session
            if not self.diagnostic_protocol.start_diagnostic_session(DiagnosticSession.DEFAULT):
                logger.error("Failed to start diagnostic session")
                return None
            
            # Read VIN
            vin_data = self.diagnostic_protocol.read_data_by_identifier(0xF101)
            if vin_data:
                vehicle_info['vin'] = vin_data.decode('ascii', errors='ignore').strip()
            
            # Read ECU part number
            part_data = self.diagnostic_protocol.read_data_by_identifier(0xF104)
            if part_data:
                vehicle_info['ecu_part_number'] = part_data.hex().upper()
            
            # Read calibration ID
            cal_data = self.diagnostic_protocol.read_data_by_identifier(0xF102)
            if cal_data:
                vehicle_info['calibration_id'] = cal_data.decode('ascii', errors='ignore').strip()
            
            # Read software version
            sw_data = self.diagnostic_protocol.read_data_by_identifier(0xF106)
            if sw_data:
                vehicle_info['software_version'] = sw_data.hex().upper()
            
            return vehicle_info if vehicle_info else None
            
        except Exception as e:
            logger.error(f"Error reading vehicle information: {e}")
            return None
    
    def read_diagnostic_trouble_codes(self) -> Optional[Dict[str, Any]]:
        """Read all diagnostic trouble codes"""
        try:
            if not self.vehicle_connected:
                logger.error("Vehicle not connected")
                return None
            
            logger.info("Reading diagnostic trouble codes...")
            
            # Read DTC information
            dtc_info = self.diagnostic_protocol.read_dtc_information(0x02)  # Read by status
            
            if dtc_info:
                # Enhance with database information
                for dtc in dtc_info.get('dtc_list', []):
                    dtc_definition = self.dtc_database.get_dtc_definition(dtc['code'])
                    if dtc_definition:
                        dtc['full_description'] = dtc_definition.description
                        dtc['severity'] = dtc_definition.severity.value
                        dtc['common_causes'] = dtc_definition.common_causes
                        dtc['diagnostic_steps'] = dtc_definition.diagnostic_steps
            
            return dtc_info
            
        except Exception as e:
            logger.error(f"Error reading DTCs: {e}")
            return None
    
    def clear_diagnostic_trouble_codes(self) -> bool:
        """Clear all diagnostic trouble codes"""
        try:
            if not self.vehicle_connected:
                logger.error("Vehicle not connected")
                return False
            
            logger.info("Clearing diagnostic trouble codes...")
            
            result = self.diagnostic_protocol.clear_diagnostic_information()
            
            if result:
                logger.info("Diagnostic trouble codes cleared successfully")
            else:
                logger.error("Failed to clear diagnostic trouble codes")
            
            return result
            
        except Exception as e:
            logger.error(f"Error clearing DTCs: {e}")
            return False
    
    def read_live_data(self, pids: List[str]) -> Optional[Dict[str, Any]]:
        """Read live data parameters"""
        try:
            if not self.vehicle_connected:
                logger.error("Vehicle not connected")
                return None
            
            live_data = {}
            
            for pid in pids:
                # Convert PID to service format and read
                # This would use the appropriate diagnostic service
                # For now, simulate reading
                value = self.diagnostic_protocol.read_data_by_identifier(int(pid, 16))
                if value:
                    live_data[pid] = {
                        'raw_value': value.hex().upper(),
                        'decoded_value': self._decode_pid_value(pid, value)
                    }
            
            return live_data
            
        except Exception as e:
            logger.error(f"Error reading live data: {e}")
            return None
    
    def _decode_pid_value(self, pid: str, value: bytes) -> Any:
        """Decode PID value based on PID definition"""
        # This would use the PID database to decode the value
        # For now, return raw value
        return value.hex().upper()
    
    def read_ecu_calibration(self) -> Optional[Dict[str, Any]]:
        """Read current ECU calibration"""
        try:
            if not self.vehicle_connected:
                logger.error("Vehicle not connected")
                return None
            
            logger.info("Reading ECU calibration...")
            
            # Enter programming mode
            if not self.programming_service.enter_programming_mode():
                logger.error("Failed to enter programming mode")
                return None
            
            try:
                # Read calibration from ECU memory
                calibration_data = self.programming_service.upload_calibration(
                    start_address=0xFFA000,  # Start of calibration area
                    length=0x8000  # Typical calibration size
                )
                
                if calibration_data:
                    calibration_info = {
                        'data_size': len(calibration_data),
                        'checksum': self.programming_service.calculate_checksum(calibration_data),
                        'raw_data': calibration_data.hex().upper()
                    }
                    
                    logger.info(f"Read calibration: {len(calibration_data)} bytes")
                    return calibration_info
                else:
                    logger.error("Failed to read calibration data")
                    return None
                    
            finally:
                # Exit programming mode
                self.programming_service.exit_programming_mode()
            
        except Exception as e:
            logger.error(f"Error reading ECU calibration: {e}")
            return None
    
    def program_ecu_calibration(self, calibration_data: bytes) -> bool:
        """Program new calibration to ECU"""
        try:
            if not self.vehicle_connected:
                logger.error("Vehicle not connected")
                return False
            
            logger.info("Programming ECU calibration...")
            
            # Verify calibration data
            if not calibration_data or len(calibration_data) == 0:
                logger.error("Invalid calibration data")
                return False
            
            # Enter programming mode
            if not self.programming_service.enter_programming_mode():
                logger.error("Failed to enter programming mode")
                return False
            
            try:
                # Download calibration to ECU
                if not self.programming_service.download_calibration(
                    calibration_data, start_address=0xFFA000
                ):
                    logger.error("Failed to download calibration")
                    return False
                
                # Verify calibration
                if not self.programming_service.verify_calibration(
                    calibration_data, start_address=0xFFA000
                ):
                    logger.error("Calibration verification failed")
                    return False
                
                logger.info("ECU calibration programmed successfully")
                return True
                
            finally:
                # Exit programming mode and reset ECU
                self.programming_service.exit_programming_mode()
                self.programming_service.reset_ecu()
            
        except Exception as e:
            logger.error(f"Error programming ECU calibration: {e}")
            return False
    
    def perform_ecu_reset(self) -> bool:
        """Perform ECU reset"""
        try:
            if not self.vehicle_connected:
                logger.error("Vehicle not connected")
                return False
            
            logger.info("Performing ECU reset...")
            
            result = self.programming_service.reset_ecu()
            
            if result:
                logger.info("ECU reset completed successfully")
            else:
                logger.error("ECU reset failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing ECU reset: {e}")
            return False
    
    def generate_diagnostic_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report"""
        report = {
            'vehicle_information': self.current_vehicle_info,
            'connection_status': self.vehicle_connected,
            'diagnostic_data': {}
        }
        
        try:
            # Read DTCs
            dtc_info = self.read_diagnostic_trouble_codes()
            if dtc_info:
                report['diagnostic_data']['dtcs'] = dtc_info
            
            # Read live data for key parameters
            key_pids = ['010C', '010D', '0104', '0105', '0111']  # RPM, Speed, Load, Coolant Temp, Throttle
            live_data = self.read_live_data(key_pids)
            if live_data:
                report['diagnostic_data']['live_data'] = live_data
            
            # System status
            report['diagnostic_data']['system_status'] = {
                'communication_quality': 'Good' if self.vehicle_connected else 'Poor',
                'voltage': self.j2534_interface.read_vehicle_voltage(),
                'protocol': 'ISO15765 CAN'
            }
            
        except Exception as e:
            logger.error(f"Error generating diagnostic report: {e}")
            report['error'] = str(e)
        
        return report
    
    def disconnect(self):
        """Disconnect from vehicle and cleanup"""
        try:
            if self.vehicle_connected:
                self.j2534_interface.disconnect()
                self.vehicle_connected = False
                logger.info("Disconnected from vehicle")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Mazda IDS/M-MDS Reverse Engineered Software')
    parser.add_argument('--connect', action='store_true', help='Connect to vehicle')
    parser.add_argument('--read-dtcs', action='store_true', help='Read diagnostic trouble codes')
    parser.add_argument('--clear-dtcs', action='store_true', help='Clear diagnostic trouble codes')
    parser.add_argument('--live-data', action='store_true', help='Read live data')
    parser.add_argument('--diagnostic-report', action='store_true', help='Generate diagnostic report')
    parser.add_argument('--read-calibration', action='store_true', help='Read ECU calibration')
    parser.add_argument('--reset-ecu', action='store_true', help='Reset ECU')
    
    args = parser.parse_args()
    
    # Create software instance
    software = MazdaIDSSoftware()
    
    try:
        if args.connect:
            if software.connect_to_vehicle():
                print("Successfully connected to vehicle")
            else:
                print("Failed to connect to vehicle")
                return
        
        if args.read_dtcs:
            if not software.vehicle_connected:
                print("Vehicle not connected - use --connect first")
                return
            
            dtc_info = software.read_diagnostic_trouble_codes()
            if dtc_info:
                print("\nDiagnostic Trouble Codes:")
                for dtc in dtc_info.get('dtc_list', []):
                    print(f"  {dtc['code']}: {dtc.get('full_description', 'Unknown')}")
            else:
                print("No DTCs found or error reading DTCs")
        
        if args.clear_dtcs:
            if not software.vehicle_connected:
                print("Vehicle not connected - use --connect first")
                return
            
            if software.clear_diagnostic_trouble_codes():
                print("DTCs cleared successfully")
            else:
                print("Failed to clear DTCs")
        
        if args.live_data:
            if not software.vehicle_connected:
                print("Vehicle not connected - use --connect first")
                return
            
            live_data = software.read_live_data(['010C', '010D', '0104', '0105'])
            if live_data:
                print("\nLive Data:")
                for pid, data in live_data.items():
                    print(f"  PID {pid}: {data['decoded_value']}")
        
        if args.diagnostic_report:
            if not software.vehicle_connected:
                print("Vehicle not connected - use --connect first")
                return
            
            report = software.generate_diagnostic_report()
            print("\nDiagnostic Report:")
            print(f"VIN: {report['vehicle_information'].get('vin', 'Unknown')}")
            print(f"Calibration: {report['vehicle_information'].get('calibration_id', 'Unknown')}")
            
            if 'diagnostic_data' in report and 'dtcs' in report['diagnostic_data']:
                dtc_count = len(report['diagnostic_data']['dtcs'].get('dtc_list', []))
                print(f"DTC Count: {dtc_count}")
        
        if args.read_calibration:
            if not software.vehicle_connected:
                print("Vehicle not connected - use --connect first")
                return
            
            calibration = software.read_ecu_calibration()
            if calibration:
                print(f"\nCalibration Read: {calibration['data_size']} bytes")
                print(f"Checksum: {calibration['checksum']:04X}")
            else:
                print("Failed to read calibration")
        
        if args.reset_ecu:
            if not software.vehicle_connected:
                print("Vehicle not connected - use --connect first")
                return
            
            if software.perform_ecu_reset():
                print("ECU reset completed")
            else:
                print("ECU reset failed")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        software.disconnect()

if __name__ == "__main__":
    main()