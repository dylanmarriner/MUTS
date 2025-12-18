#!/usr/bin/env python3
"""
DTC Handler Module - Complete Diagnostic Trouble Code management
Provides comprehensive DTC reading, clearing, and analysis for Mazdaspeed 3
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from ..core.ecu_communication import ECUCommunicator
from ..utils.logger import VersaLogger

@dataclass
class DTCInfo:
    """Complete DTC information container"""
    code: str
    description: str
    status: str  # Active, Pending, Permanent
    severity: str  # Low, Medium, High, Critical
    frequency: int  # Occurrence count
    first_detected: Optional[float] = None
    last_detected: Optional[float] = None
    freeze_frame: Optional[Dict[str, Any]] = None

class DTCHandler:
    """
    Comprehensive DTC management for Mazdaspeed 3
    Handles reading, clearing, and analyzing diagnostic trouble codes
    """
    
    # Mazdaspeed 3 specific DTC database
    DTC_DATABASE = {
        # Powertrain DTCs (P0xxx, P1xxx)
        'P0101': {'description': 'Mass Air Flow Circuit Range/Performance', 'severity': 'Medium'},
        'P0102': {'description': 'Mass Air Flow Circuit Low Input', 'severity': 'High'},
        'P0103': {'description': 'Mass Air Flow Circuit High Input', 'severity': 'High'},
        'P0234': {'description': 'Turbocharger Overboost Condition', 'severity': 'Critical'},
        'P0300': {'description': 'Random/Multiple Cylinder Misfire Detected', 'severity': 'High'},
        'P0301': {'description': 'Cylinder 1 Misfire Detected', 'severity': 'High'},
        'P0302': {'description': 'Cylinder 2 Misfire Detected', 'severity': 'High'},
        'P0303': {'description': 'Cylinder 3 Misfire Detected', 'severity': 'High'},
        'P0304': {'description': 'Cylinder 4 Misfire Detected', 'severity': 'High'},
        'P0420': {'description': 'Catalyst System Efficiency Below Threshold', 'severity': 'Medium'},
        'P0611': {'description': 'ECU Internal Control Module Memory Error', 'severity': 'Critical'},
        'P2187': {'description': 'Fuel System Too Lean at Idle', 'severity': 'Medium'},
        'P2188': {'description': 'Fuel System Too Rich at Idle', 'severity': 'Medium'},
        
        # Chassis DTCs (C0xxx)
        'C0034': {'description': 'Left Front Wheel Speed Sensor Circuit', 'severity': 'Medium'},
        'C0035': {'description': 'Left Front Wheel Speed Sensor Range/Performance', 'severity': 'Medium'},
        
        # Body DTCs (B0xxx)
        'B1000': {'description': 'ECU Malfunction', 'severity': 'Critical'},
        'B1342': {'description': 'ECU Is Defective', 'severity': 'Critical'},
        
        # Network DTCs (U0xxx)
        'U0100': {'description': 'Lost Communication With ECM', 'severity': 'High'},
        'U0101': {'description': 'Lost Communication With TCM', 'severity': 'High'},
        'U0121': {'description': 'Lost Communication With Anti-Lock Brake System Control Module', 'severity': 'Medium'},
    }
    
    def __init__(self, ecu_communicator: ECUCommunicator):
        """
        Initialize DTC Handler
        
        Args:
            ecu_communicator: ECUCommunicator instance
        """
        self.ecu = ecu_communicator
        self.logger = VersaLogger(__name__)
        self.dtc_history: List[DTCInfo] = []
    
    def read_all_dtcs(self) -> List[DTCInfo]:
        """
        Read all Diagnostic Trouble Codes from ECU
        
        Returns:
            List of DTCInfo objects
        """
        self.logger.info("Reading all DTCs from ECU")
        
        dtcs = []
        
        try:
            # Read current DTCs (active)
            current_dtcs = self._read_dtc_type(0x01)  # Current DTCs
            for dtc_data in current_dtcs:
                dtc_info = self._create_dtc_info(dtc_data, 'Active')
                dtcs.append(dtc_info)
            
            # Read pending DTCs
            pending_dtcs = self._read_dtc_type(0x02)  # Pending DTCs
            for dtc_data in pending_dtcs:
                dtc_info = self._create_dtc_info(dtc_data, 'Pending')
                dtcs.append(dtc_info)
            
            # Read permanent DTCs
            permanent_dtcs = self._read_dtc_type(0x0A)  # Permanent DTCs
            for dtc_data in permanent_dtcs:
                dtc_info = self._create_dtc_info(dtc_data, 'Permanent')
                dtcs.append(dtc_info)
            
            # Read freeze frame data for active DTCs
            for dtc in dtcs:
                if dtc.status == 'Active':
                    freeze_frame = self._read_freeze_frame(dtc.code)
                    if freeze_frame:
                        dtc.freeze_frame = freeze_frame
            
            # Update history
            self._update_dtc_history(dtcs)
            
            self.logger.info(f"Read {len(dtcs)} DTCs from ECU")
            return dtcs
            
        except Exception as e:
            self.logger.error(f"Failed to read DTCs: {e}")
            return []
    
    def _read_dtc_type(self, dtc_type: int) -> List[Dict[str, Any]]:
        """
        Read specific type of DTCs
        
        Args:
            dtc_type: DTC type identifier
            
        Returns:
            List of DTC data dictionaries
        """
        dtcs = []
        
        try:
            # Request DTCs by type
            response = self.ecu.send_request(0x19, dtc_type)
            
            if response.success and len(response.data) >= 4:
                # Parse DTC data (starts at byte 3)
                dtc_data = response.data[3:]
                
                # Each DTC is 2 bytes
                for i in range(0, len(dtc_data) - 1, 2):
                    dtc_bytes = dtc_data[i:i+2]
                    
                    # Skip empty slots (0x0000)
                    if dtc_bytes[0] == 0x00 and dtc_bytes[1] == 0x00:
                        continue
                    
                    dtc_code = self._parse_dtc_bytes(dtc_bytes)
                    if dtc_code:
                        dtcs.append({
                            'code': dtc_code,
                            'raw_bytes': dtc_bytes,
                            'type': dtc_type
                        })
            
        except Exception as e:
            self.logger.error(f"Failed to read DTC type {dtc_type:02X}: {e}")
        
        return dtcs
    
    def _parse_dtc_bytes(self, dtc_bytes: bytes) -> Optional[str]:
        """
        Parse 2-byte DTC data into standard code format
        
        Args:
            dtc_bytes: 2-byte DTC data
            
        Returns:
            str: Standard DTC code or None if invalid
        """
        if len(dtc_bytes) != 2:
            return None
        
        first_byte = dtc_bytes[0]
        second_byte = dtc_bytes[1]
        
        # Extract DTC components
        dtc_type = (first_byte >> 6) & 0x03
        digit1 = (first_byte >> 4) & 0x03
        digit2 = first_byte & 0x0F
        digit3 = (second_byte >> 4) & 0x0F
        digit4 = second_byte & 0x0F
        
        # Map type to letter
        type_map = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
        type_char = type_map.get(dtc_type, 'P')
        
        return f"{type_char}{digit1}{digit2}{digit3}{digit4}"
    
    def _create_dtc_info(self, dtc_data: Dict[str, Any], status: str) -> DTCInfo:
        """
        Create DTCInfo object from raw DTC data
        
        Args:
            dtc_data: Raw DTC data
            status: DTC status
            
        Returns:
            DTCInfo object
        """
        code = dtc_data['code']
        db_info = self.DTC_DATABASE.get(code, {
            'description': 'Unknown DTC',
            'severity': 'Medium'
        })
        
        return DTCInfo(
            code=code,
            description=db_info['description'],
            status=status,
            severity=db_info['severity'],
            frequency=1,
            first_detected=time.time(),
            last_detected=time.time()
        )
    
    def _read_freeze_frame(self, dtc_code: str) -> Optional[Dict[str, Any]]:
        """
        Read freeze frame data for specific DTC
        
        Args:
            dtc_code: DTC code to read freeze frame for
            
        Returns:
            Dict containing freeze frame data or None
        """
        try:
            # Convert DTC code to bytes for request
            dtc_bytes = self._dtc_code_to_bytes(dtc_code)
            if not dtc_bytes:
                return None
            
            # Request freeze frame data
            response = self.ecu.send_request(0x12, 0x00, dtc_bytes)
            
            if response.success and len(response.data) >= 10:
                return self._parse_freeze_frame_data(response.data)
            
        except Exception as e:
            self.logger.error(f"Failed to read freeze frame for {dtc_code}: {e}")
        
        return None
    
    def _dtc_code_to_bytes(self, dtc_code: str) -> Optional[bytes]:
        """
        Convert DTC code string to 2-byte format
        
        Args:
            dtc_code: DTC code string (e.g., 'P0301')
            
        Returns:
            bytes: 2-byte DTC representation or None
        """
        if len(dtc_code) != 5:
            return None
        
        # Parse DTC components
        type_char = dtc_code[0]
        digit1 = int(dtc_code[1])
        digit2 = int(dtc_code[2])
        digit3 = int(dtc_code[3])
        digit4 = int(dtc_code[4])
        
        # Map type character to numeric value
        type_map = {'P': 0, 'C': 1, 'B': 2, 'U': 3}
        dtc_type = type_map.get(type_char, 0)
        
        # Construct bytes
        first_byte = (dtc_type << 6) | (digit1 << 4) | digit2
        second_byte = (digit3 << 4) | digit4
        
        return bytes([first_byte, second_byte])
    
    def _parse_freeze_frame_data(self, data: bytes) -> Dict[str, Any]:
        """
        Parse freeze frame data from response
        
        Args:
            data: Freeze frame response data
            
        Returns:
            Dict containing parsed freeze frame data
        """
        frame = {}
        
        try:
            # Basic freeze frame structure (varies by ECU)
            if len(data) >= 14:
                frame.update({
                    'dtc': f"{data[3]:02X}{data[4]:02X}",
                    'engine_rpm': ((data[7] << 8) | data[8]) / 4,  # RPM
                    'vehicle_speed': data[9],  # km/h
                    'coolant_temp': data[10] - 40,  # °C
                    'engine_load': (data[11] * 100) / 255,  # %
                    'throttle_position': (data[12] * 100) / 255,  # %
                    'intake_air_temp': data[13] - 40,  # °C
                })
            
            if len(data) >= 18:
                frame.update({
                    'maf_flow': ((data[14] << 8) | data[15]) / 100,  # g/s
                    'fuel_trim': (data[16] - 128) * 100 / 128,  # %
                    'ignition_timing': data[17] - 64,  # degrees
                })
        
        except Exception as e:
            self.logger.error(f"Failed to parse freeze frame: {e}")
        
        return frame
    
    def clear_all_dtcs(self) -> bool:
        """
        Clear all Diagnostic Trouble Codes
        
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Clearing all DTCs")
        
        try:
            response = self.ecu.send_request(0x14, 0xFF)  # Clear all DTCs
            
            if response.success:
                # Update history
                for dtc in self.dtc_history:
                    dtc.status = 'Cleared'
                    dtc.last_detected = time.time()
                
                self.logger.info("All DTCs cleared successfully")
                return True
            else:
                self.logger.error("Failed to clear DTCs")
                return False
                
        except Exception as e:
            self.logger.error(f"DTC clear error: {e}")
            return False
    
    def clear_specific_dtc(self, dtc_code: str) -> bool:
        """
        Clear specific DTC
        
        Args:
            dtc_code: DTC code to clear
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info(f"Clearing DTC: {dtc_code}")
        
        try:
            dtc_bytes = self._dtc_code_to_bytes(dtc_code)
            if not dtc_bytes:
                return False
            
            response = self.ecu.send_request(0x14, 0x00, dtc_bytes)
            
            if response.success:
                # Update history
                for dtc in self.dtc_history:
                    if dtc.code == dtc_code:
                        dtc.status = 'Cleared'
                        dtc.last_detected = time.time()
                
                self.logger.info(f"DTC {dtc_code} cleared successfully")
                return True
            else:
                self.logger.error(f"Failed to clear DTC {dtc_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"DTC clear error: {e}")
            return False
    
    def _update_dtc_history(self, current_dtcs: List[DTCInfo]):
        """
        Update DTC history with current DTCs
        
        Args:
            current_dtcs: List of current DTCs
        """
        current_time = time.time()
        
        for current_dtc in current_dtcs:
            # Check if DTC exists in history
            existing_dtc = None
            for hist_dtc in self.dtc_history:
                if hist_dtc.code == current_dtc.code:
                    existing_dtc = hist_dtc
                    break
            
            if existing_dtc:
                # Update existing DTC
                existing_dtc.status = current_dtc.status
                existing_dtc.last_detected = current_time
                existing_dtc.frequency += 1
                if current_dtc.freeze_frame:
                    existing_dtc.freeze_frame = current_dtc.freeze_frame
            else:
                # Add new DTC to history
                current_dtc.first_detected = current_time
                self.dtc_history.append(current_dtc)
    
    def get_dtc_statistics(self) -> Dict[str, Any]:
        """
        Get DTC statistics and analysis
        
        Returns:
            Dict containing DTC statistics
        """
        stats = {
            'total_dtcs': len(self.dtc_history),
            'active_dtcs': 0,
            'pending_dtcs': 0,
            'permanent_dtcs': 0,
            'cleared_dtcs': 0,
            'by_severity': {},
            'by_system': {},
            'most_frequent': [],
            'recent_dtcs': []
        }
        
        # Count by status and severity
        for dtc in self.dtc_history:
            # Status counts
            if dtc.status == 'Active':
                stats['active_dtcs'] += 1
            elif dtc.status == 'Pending':
                stats['pending_dtcs'] += 1
            elif dtc.status == 'Permanent':
                stats['permanent_dtcs'] += 1
            elif dtc.status == 'Cleared':
                stats['cleared_dtcs'] += 1
            
            # Severity counts
            stats['by_severity'][dtc.severity] = stats['by_severity'].get(dtc.severity, 0) + 1
            
            # System counts (based on first character of DTC code)
            system = dtc.code[0]
            stats['by_system'][system] = stats['by_system'].get(system, 0) + 1
        
        # Most frequent DTCs
        frequent_dtcs = sorted(self.dtc_history, key=lambda x: x.frequency, reverse=True)[:5]
        stats['most_frequent'] = [
            {'code': dtc.code, 'frequency': dtc.frequency, 'description': dtc.description}
            for dtc in frequent_dtcs
        ]
        
        # Recent DTCs (last 7 days)
        week_ago = time.time() - (7 * 24 * 60 * 60)
        recent_dtcs = [dtc for dtc in self.dtc_history 
                      if dtc.last_detected and dtc.last_detected > week_ago]
        stats['recent_dtcs'] = [
            {'code': dtc.code, 'last_detected': dtc.last_detected, 'status': dtc.status}
            for dtc in recent_dtcs
        ]
        
        return stats
    
    def generate_dtc_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive DTC report
        
        Returns:
            Dict containing complete DTC report
        """
        current_dtcs = self.read_all_dtcs()
        statistics = self.get_dtc_statistics()
        
        report = {
            'generated_at': time.time(),
            'summary': {
                'total_current_dtcs': len(current_dtcs),
                'active_dtcs': len([d for d in current_dtcs if d.status == 'Active']),
                'overall_health': 'Good' if len(current_dtcs) == 0 else 'Needs Attention'
            },
            'current_dtcs': [
                {
                    'code': dtc.code,
                    'description': dtc.description,
                    'status': dtc.status,
                    'severity': dtc.severity,
                    'freeze_frame': dtc.freeze_frame
                }
                for dtc in current_dtcs
            ],
            'statistics': statistics,
            'recommendations': self._generate_recommendations(current_dtcs)
        }
        
        return report
    
    def _generate_recommendations(self, current_dtcs: List[DTCInfo]) -> List[str]:
        """
        Generate recommendations based on current DTCs
        
        Args:
            current_dtcs: List of current DTCs
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check for critical DTCs
        critical_dtcs = [dtc for dtc in current_dtcs if dtc.severity == 'Critical']
        if critical_dtcs:
            recommendations.append("Critical DTCs detected - immediate attention required")
        
        # Check for multiple misfire DTCs
        misfire_dtcs = [dtc for dtc in current_dtcs if 'Misfire' in dtc.description]
        if len(misfire_dtcs) >= 2:
            recommendations.append("Multiple misfire DTCs - check ignition system and fuel delivery")
        
        # Check for turbo-related DTCs
        turbo_dtcs = [dtc for dtc in current_dtcs if 'Turbo' in dtc.description or dtc.code == 'P0234']
        if turbo_dtcs:
            recommendations.append("Turbo system DTCs - inspect turbocharger and boost control system")
        
        # Check for fuel system DTCs
        fuel_dtcs = [dtc for dtc in current_dtcs if 'Fuel' in dtc.description or 'Lean' in dtc.description or 'Rich' in dtc.description]
        if fuel_dtcs:
            recommendations.append("Fuel system DTCs - check fuel pressure, injectors, and sensors")
        
        # General maintenance recommendation
        if not recommendations and current_dtcs:
            recommendations.append("Non-critical DTCs present - schedule diagnostic service")
        
        return recommendations
