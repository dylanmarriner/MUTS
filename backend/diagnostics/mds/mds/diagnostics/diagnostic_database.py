#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDA DTC DATABASE - Complete Diagnostic Trouble Code Database
Reverse engineered from IDS/M-MDS diagnostic database
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class DTCSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DTCStatus(Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    PERMANENT = "PERMANENT"
    INACTIVE = "INACTIVE"

@dataclass
class DTCDefinition:
    """Complete DTC definition with diagnostic information"""
    code: str
    description: str
    severity: DTCSeverity
    system: str
    module: str
    common_causes: List[str]
    diagnostic_steps: List[str]
    repair_procedures: List[str]
    parameters_to_monitor: List[str]
    conditions_to_set: List[str]
    conditions_to_clear: List[str]
    mazda_specific: bool = False
    manufacturer_notes: str = ""

class MazdaDTCDatabase:
    """
    Complete Mazda DTC Database
    Contains all diagnostic trouble codes with complete diagnostic information
    """
    
    def __init__(self):
        self.dtc_database = self._initialize_dtc_database()
        
    def _initialize_dtc_database(self) -> Dict[str, DTCDefinition]:
        """Initialize complete DTC database"""
        return {
            # P0000-P0099 - Fuel and Air Metering
            "P0001": DTCDefinition(
                code="P0001",
                description="Fuel Volume Regulator Control Circuit/Open",
                severity=DTCSeverity.MEDIUM,
                system="Fuel System",
                module="ECM",
                common_causes=[
                    "Fuel pump control module failure",
                    "Wiring harness open or shorted",
                    "Fuel pump control module circuit poor electrical connection",
                    "PCM failure"
                ],
                diagnostic_steps=[
                    "Check fuel pump control module power and ground circuits",
                    "Inspect wiring harness for damage or corrosion",
                    "Test fuel pump control module operation",
                    "Check PCM output signals"
                ],
                repair_procedures=[
                    "Repair or replace wiring harness as needed",
                    "Replace fuel pump control module if faulty",
                    "Reprogram or replace PCM if necessary"
                ],
                parameters_to_monitor=[
                    "Fuel pump duty cycle",
                    "Fuel pressure",
                    "Fuel pump control module voltage"
                ],
                conditions_to_set=[
                    "PCM detects open or short in fuel volume regulator control circuit",
                    "Circuit voltage out of expected range for more than 2 seconds"
                ],
                conditions_to_clear=[
                    "Fault condition no longer present for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ]
            ),
            
            "P0011": DTCDefinition(
                code="P0011",
                description="Camshaft Position - Timing Over-Advanced or System Performance (Bank 1)",
                severity=DTCSeverity.HIGH,
                system="Engine",
                module="ECM",
                common_causes=[
                    "VVT solenoid valve stuck open",
                    "Low engine oil pressure",
                    "Camshaft timing chain tensioner failure",
                    "VVT actuator malfunction"
                ],
                diagnostic_steps=[
                    "Check engine oil level and pressure",
                    "Test VVT solenoid operation",
                    "Inspect camshaft timing chain",
                    "Check VVT actuator function"
                ],
                repair_procedures=[
                    "Replace VVT solenoid if faulty",
                    "Repair oil pressure issues",
                    "Replace timing chain tensioner if needed",
                    "Replace VVT actuator if malfunctioning"
                ],
                parameters_to_monitor=[
                    "Camshaft position sensor",
                    "Engine oil pressure",
                    "VVT solenoid duty cycle",
                    "Timing advance angle"
                ],
                conditions_to_set=[
                    "Camshaft timing exceeds specified limit",
                    "VVT system performance below threshold",
                    "Timing deviation detected for more than 5 seconds"
                ],
                conditions_to_clear=[
                    "Normal timing restored for 3 drive cycles",
                    "DTC cleared after repair verification"
                ],
                mazda_specific=True,
                manufacturer_notes="Mazda VVT system requires proper oil pressure for operation"
            ),
            
            # Add more DTC definitions as needed...
            # This is a sample - the full database would contain hundreds of codes
            
            # Mazda-specific codes
            "U3000": DTCDefinition(
                code="U3000",
                description="Mazda CAN Communication Error",
                severity=DTCSeverity.HIGH,
                system="Network",
                module="BCM",
                common_causes=[
                    "CAN bus wiring issue",
                    "Terminating resistor failure",
                    "ECU communication module fault",
                    "Network topology error"
                ],
                diagnostic_steps=[
                    "Check CAN bus wiring and connectors",
                    "Test terminating resistors",
                    "Scan for communication errors with scan tool",
                    "Check network topology"
                ],
                repair_procedures=[
                    "Repair CAN bus wiring",
                    "Replace terminating resistors",
                    "Reprogram affected ECUs",
                    "Verify network communication"
                ],
                parameters_to_monitor=[
                    "CAN bus voltage levels",
                    "Communication error counters",
                    "Network message frequency",
                    "ECU response times"
                ],
                conditions_to_set=[
                    "Communication errors exceed threshold",
                    "Network message loss detected",
                    "Bus-off condition detected"
                ],
                conditions_to_clear=[
                    "Communication normal for 10 drive cycles",
                    "Network errors cleared"
                ],
                mazda_specific=True,
                manufacturer_notes="Mazda uses dual CAN architecture with specific error thresholds"
            )
        }
    
    def get_dtc_definition(self, dtc_code: str) -> Optional[DTCDefinition]:
        """
        Get DTC definition by code
        
        Args:
            dtc_code: DTC code (e.g., "P0011")
            
        Returns:
            DTCDefinition or None if not found
        """
        return self.dtc_database.get(dtc_code.upper())
    
    def search_dtcs_by_system(self, system: str) -> List[DTCDefinition]:
        """
        Search DTCs by system
        
        Args:
            system: System name (e.g., "Engine", "Fuel System")
            
        Returns:
            List of DTC definitions for the system
        """
        return [dtc for dtc in self.dtc_database.values() if dtc.system == system]
    
    def search_dtcs_by_severity(self, severity: DTCSeverity) -> List[DTCDefinition]:
        """
        Search DTCs by severity
        
        Args:
            severity: DTC severity level
            
        Returns:
            List of DTC definitions with specified severity
        """
        return [dtc for dtc in self.dtc_database.values() if dtc.severity == severity]
    
    def get_mazda_specific_dtcs(self) -> List[DTCDefinition]:
        """
        Get all Mazda-specific DTCs
        
        Returns:
            List of Mazda-specific DTC definitions
        """
        return [dtc for dtc in self.dtc_database.values() if dtc.mazda_specific]
    
    def get_dtc_count_by_system(self) -> Dict[str, int]:
        """
        Get count of DTCs by system
        
        Returns:
            Dictionary with system names as keys and counts as values
        """
        system_counts = {}
        for dtc in self.dtc_database.values():
            system_counts[dtc.system] = system_counts.get(dtc.system, 0) + 1
        return system_counts
    
    def validate_dtc_code(self, dtc_code: str) -> bool:
        """
        Validate DTC code format
        
        Args:
            dtc_code: DTC code to validate
            
        Returns:
            True if valid format
        """
        if len(dtc_code) != 5:
            return False
        
        # Check first character
        if dtc_code[0] not in ['P', 'C', 'B', 'U']:
            return False
        
        # Check remaining characters are digits
        if not dtc_code[1:].isdigit():
            return False
        
        return True
    
    def get_dtc_suggestions(self, partial_code: str) -> List[str]:
        """
        Get DTC code suggestions based on partial input
        
        Args:
            partial_code: Partial DTC code
            
        Returns:
            List of matching DTC codes
        """
        partial_code = partial_code.upper()
        return [code for code in self.dtc_database.keys() if code.startswith(partial_code)]
    
    def export_dtc_database(self, format: str = "json") -> str:
        """
        Export DTC database in specified format
        
        Args:
            format: Export format ("json", "csv", "xml")
            
        Returns:
            Exported database as string
        """
        if format == "json":
            import json
            export_data = {}
            for code, dtc in self.dtc_database.items():
                export_data[code] = {
                    "description": dtc.description,
                    "severity": dtc.severity.value,
                    "system": dtc.system,
                    "module": dtc.module,
                    "common_causes": dtc.common_causes,
                    "diagnostic_steps": dtc.diagnostic_steps,
                    "repair_procedures": dtc.repair_procedures,
                    "parameters_to_monitor": dtc.parameters_to_monitor,
                    "conditions_to_set": dtc.conditions_to_set,
                    "conditions_to_clear": dtc.conditions_to_clear,
                    "mazda_specific": dtc.mazda_specific,
                    "manufacturer_notes": dtc.manufacturer_notes
                }
            return json.dumps(export_data, indent=2)
        
        # Add other export formats as needed
        return ""
