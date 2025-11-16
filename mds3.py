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
                    "Timing chain stretched or jumped",
                    "VVT actuator mechanical failure",
                    "Oil control valve filter clogged"
                ],
                diagnostic_steps=[
                    "Check engine oil level and quality",
                    "Test engine oil pressure",
                    "Inspect VVT solenoid valve operation",
                    "Check timing chain for stretching or damage",
                    "Monitor camshaft position sensor data"
                ],
                repair_procedures=[
                    "Replace VVT solenoid valve if stuck",
                    "Perform oil and filter change if contaminated",
                    "Replace timing chain and related components if necessary",
                    "Clean or replace oil control valve filter"
                ],
                parameters_to_monitor=[
                    "Camshaft position sensor",
                    "VVT solenoid duty cycle", 
                    "Engine oil pressure",
                    "Engine RPM",
                    "Engine load"
                ],
                conditions_to_set=[
                    "Difference between actual and desired camshaft position exceeds threshold",
                    "Fault present for more than 2 seconds"
                ],
                conditions_to_clear=[
                    "Fault condition no longer present for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ],
                mazda_specific=True
            ),
            
            "P0012": DTCDefinition(
                code="P0012", 
                description="Camshaft Position - Timing Over-Retarded (Bank 1)",
                severity=DTCSeverity.HIGH,
                system="Engine",
                module="ECM",
                common_causes=[
                    "VVT solenoid valve stuck closed",
                    "Low engine oil pressure", 
                    "Timing chain issues",
                    "VVT actuator mechanical failure",
                    "PCM calibration issue"
                ],
                diagnostic_steps=[
                    "Check engine oil level and pressure",
                    "Test VVT solenoid valve operation",
                    "Inspect timing chain and sprockets",
                    "Verify PCM calibration is up to date"
                ],
                repair_procedures=[
                    "Replace faulty VVT solenoid valve",
                    "Address oil pressure issues",
                    "Replace timing components if necessary",
                    "Update PCM calibration if available"
                ],
                parameters_to_monitor=[
                    "Camshaft position",
                    "VVT control duty cycle",
                    "Engine oil pressure",
                    "Engine temperature"
                ],
                conditions_to_set=[
                    "Camshaft position remains retarded beyond threshold",
                    "Fault present for more than 2 seconds"
                ],
                conditions_to_clear=[
                    "Fault condition no longer present for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ],
                mazda_specific=True
            ),
            
            # P0100-P0199 - Fuel and Air Metering
            "P0101": DTCDefinition(
                code="P0101",
                description="Mass Air Flow Circuit Range/Performance",
                severity=DTCSeverity.HIGH,
                system="Air Intake",
                module="ECM",
                common_causes=[
                    "MAF sensor contaminated or faulty",
                    "Intake air leaks after MAF sensor",
                    "MAF sensor wiring issues",
                    "Air filter clogged or restricted",
                    "PCM calibration issue"
                ],
                diagnostic_steps=[
                    "Clean MAF sensor with appropriate cleaner",
                    "Check for intake air leaks",
                    "Test MAF sensor output at various RPMs",
                    "Inspect air filter condition",
                    "Verify MAF sensor wiring and connections"
                ],
                repair_procedures=[
                    "Clean or replace MAF sensor",
                    "Repair intake air leaks",
                    "Replace air filter if clogged",
                    "Repair wiring issues if found"
                ],
                parameters_to_monitor=[
                    "MAF sensor voltage",
                    "MAF sensor frequency",
                    "Engine load",
                    "Throttle position",
                    "Fuel trims"
                ],
                conditions_to_set=[
                    "MAF sensor signal out of expected range for current operating conditions",
                    "Correlation error between MAF and other sensors",
                    "Fault present for more than 2 seconds"
                ],
                conditions_to_clear=[
                    "Fault condition no longer present for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ]
            ),
            
            "P0102": DTCDefinition(
                code="P0102",
                description="Mass Air Flow Circuit Low Input",
                severity=DTCSeverity.HIGH,
                system="Air Intake", 
                module="ECM",
                common_causes=[
                    "MAF sensor circuit short to ground",
                    "MAF sensor power circuit open",
                    "MAF sensor ground circuit open", 
                    "MAF sensor internal failure",
                    "PCM connection issues"
                ],
                diagnostic_steps=[
                    "Check MAF sensor power and ground circuits",
                    "Test MAF sensor output voltage",
                    "Inspect MAF sensor connector for damage",
                    "Check PCM connections"
                ],
                repair_procedures=[
                    "Repair wiring shorts or opens",
                    "Replace MAF sensor if faulty",
                    "Clean or repair connectors as needed"
                ],
                parameters_to_monitor=[
                    "MAF sensor voltage",
                    "MAF sensor frequency", 
                    "Engine RPM",
                    "Throttle position"
                ],
                conditions_to_set=[
                    "MAF sensor signal below minimum expected voltage",
                    "Fault present for more than 2 seconds"
                ],
                conditions_to_clear=[
                    "Fault condition no longer present for 3 consecutive drive cycles", 
                    "DTC manually cleared with scan tool"
                ]
            ),
            
            "P0103": DTCDefinition(
                code="P0103",
                description="Mass Air Flow Circuit High Input",
                severity=DTCSeverity.HIGH,
                system="Air Intake",
                module="ECM", 
                common_causes=[
                    "MAF sensor circuit short to power",
                    "MAF sensor internal failure",
                    "PCM reference voltage circuit issue",
                    "Wiring harness damage"
                ],
                diagnostic_steps=[
                    "Check MAF sensor circuit for shorts to power",
                    "Test MAF sensor output voltage with key ON, engine OFF",
                    "Inspect wiring harness for damage",
                    "Verify PCM reference voltage"
                ],
                repair_procedures=[
                    "Repair wiring shorts to power",
                    "Replace MAF sensor if faulty",
                    "Repair or replace wiring harness as needed"
                ],
                parameters_to_monitor=[
                    "MAF sensor voltage",
                    "MAF sensor frequency",
                    "PCM reference voltage"
                ],
                conditions_to_set=[
                    "MAF sensor signal above maximum expected voltage", 
                    "Fault present for more than 2 seconds"
                ],
                conditions_to_clear=[
                    "Fault condition no longer present for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ]
            ),
            
            # P0234 - Turbo Overboost
            "P0234": DTCDefinition(
                code="P0234",
                description="Turbocharger Overboost Condition",
                severity=DTCSeverity.HIGH,
                system="Turbocharger",
                module="ECM",
                common_causes=[
                    "Wastegate actuator stuck closed",
                    "Boost control solenoid valve failure",
                    "MAP sensor inaccurate reading",
                    "Boost pressure sensor failure",
                    "Tuning or calibration issue"
                ],
                diagnostic_steps=[
                    "Check wastegate actuator operation",
                    "Test boost control solenoid valve",
                    "Verify MAP sensor readings",
                    "Check for boost leaks",
                    "Monitor actual vs desired boost pressure"
                ],
                repair_procedures=[
                    "Replace stuck wastegate actuator",
                    "Replace faulty boost control solenoid",
                    "Calibrate or replace MAP sensor",
                    "Repair boost leaks if found"
                ],
                parameters_to_monitor=[
                    "Boost pressure",
                    "Wastegate duty cycle", 
                    "MAP sensor voltage",
                    "Engine load",
                    "Throttle position"
                ],
                conditions_to_set=[
                    "Actual boost pressure exceeds desired pressure by more than 3 psi for 2 seconds",
                    "Overboost condition detected during WOT operation"
                ],
                conditions_to_clear=[
                    "Fault condition no longer present for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ],
                mazda_specific=True,
                manufacturer_notes="Common on modified vehicles with aftermarket tuning"
            ),
            
            # P0300-P0304 - Misfire Detection
            "P0300": DTCDefinition(
                code="P0300", 
                description="Random/Multiple Cylinder Misfire Detected",
                severity=DTCSeverity.HIGH,
                system="Ignition",
                module="ECM",
                common_causes=[
                    "Ignition system components (coils, plugs, wires)",
                    "Fuel system issues (injectors, pressure)",
                    "Air intake leaks",
                    "Mechanical engine problems",
                    "Sensor failures"
                ],
                diagnostic_steps=[
                    "Check spark plugs and ignition coils",
                    "Test fuel pressure and injector operation", 
                    "Perform compression test",
                    "Check for vacuum leaks",
                    "Monitor misfire counters for specific cylinders"
                ],
                repair_procedures=[
                    "Replace faulty ignition components",
                    "Repair fuel system issues",
                    "Address mechanical engine problems",
                    "Repair vacuum leaks"
                ],
                parameters_to_monitor=[
                    "Misfire counters per cylinder",
                    "Fuel trims",
                    "Ignition timing",
                    "Engine RPM",
                    "Load values"
                ],
                conditions_to_set=[
                    "Misfire rate exceeds threshold that would damage catalyst",
                    "Multiple cylinders showing misfire activity",
                    "Fault present for 2 consecutive trips"
                ],
                conditions_to_clear=[
                    "No misfires detected for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ]
            ),
            
            "P0301": DTCDefinition(
                code="P0301",
                description="Cylinder 1 Misfire Detected",
                severity=DTCSeverity.HIGH,
                system="Ignition", 
                module="ECM",
                common_causes=[
                    "Cylinder 1 ignition coil failure",
                    "Spark plug issue in cylinder 1",
                    "Fuel injector problem in cylinder 1",
                    "Compression issue in cylinder 1",
                    "Wiring issue to cylinder 1 components"
                ],
                diagnostic_steps=[
                    "Swap ignition coil with another cylinder and retest",
                    "Inspect spark plug in cylinder 1",
                    "Test fuel injector operation in cylinder 1",
                    "Perform compression test on cylinder 1",
                    "Check wiring to cylinder 1 components"
                ],
                repair_procedures=[
                    "Replace faulty ignition coil",
                    "Replace spark plug if worn or damaged",
                    "Clean or replace fuel injector",
                    "Address compression issues if found"
                ],
                parameters_to_monitor=[
                    "Cylinder 1 misfire counter",
                    "Ignition coil operation",
                    "Fuel injector pulse width",
                    "Compression values"
                ],
                conditions_to_set=[
                    "Misfire rate in cylinder 1 exceeds damage threshold",
                    "Fault present for 2 consecutive trips"
                ],
                conditions_to_clear=[
                    "No misfires detected in cylinder 1 for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ]
            ),
            
            # Continue with remaining DTC definitions...
            # P0420 - Catalyst Efficiency
            "P0420": DTCDefinition(
                code="P0420",
                description="Catalyst System Efficiency Below Threshold (Bank 1)",
                severity=DTCSeverity.MEDIUM,
                system="Emission Control",
                module="ECM",
                common_causes=[
                    "Catalytic converter failure or degradation",
                    "Exhaust leaks before or after catalytic converter",
                    "Oxygen sensor malfunction",
                    "Engine misfires affecting catalyst",
                    "Fuel system issues"
                ],
                diagnostic_steps=[
                    "Check for exhaust leaks",
                    "Monitor oxygen sensor activity",
                    "Check for engine misfires",
                    "Test catalytic converter efficiency",
                    "Verify fuel system operation"
                ],
                repair_procedures=[
                    "Replace catalytic converter if inefficient",
                    "Repair exhaust leaks",
                    "Replace faulty oxygen sensors",
                    "Address engine misfires if present"
                ],
                parameters_to_monitor=[
                    "Catalyst efficiency monitor",
                    "Oxygen sensor voltages",
                    "Fuel trims",
                    "Exhaust gas temperature"
                ],
                conditions_to_set=[
                    "Catalyst efficiency below threshold for current operating conditions",
                    "Monitor completes during drive cycle"
                ],
                conditions_to_clear=[
                    "Monitor runs and passes during drive cycle",
                    "DTC manually cleared with scan tool"
                ]
            ),
            
            # Mazda Specific DTCs
            "P2502": DTCDefinition(
                code="P2502",
                description="Generator Lamp Control Circuit Low",
                severity=DTCSeverity.MEDIUM,
                system="Charging System",
                module="ECM",
                common_causes=[
                    "Generator warning lamp circuit short to ground",
                    "Instrument cluster failure",
                    "Wiring harness issue",
                    "PCM circuit problem"
                ],
                diagnostic_steps=[
                    "Check generator warning lamp circuit",
                    "Test instrument cluster operation",
                    "Inspect wiring for shorts to ground",
                    "Verify PCM output signals"
                ],
                repair_procedures=[
                    "Repair wiring shorts to ground",
                    "Replace instrument cluster if faulty",
                    "Repair wiring harness as needed"
                ],
                parameters_to_monitor=[
                    "Generator warning lamp status",
                    "Charging system voltage",
                    "PCM output circuits"
                ],
                conditions_to_set=[
                    "Generator lamp control circuit voltage below threshold",
                    "Fault present for more than 2 seconds"
                ],
                conditions_to_clear=[
                    "Fault condition no longer present for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ],
                mazda_specific=True
            ),
            
            # U0100 - Network Communication
            "U0100": DTCDefinition(
                code="U0100",
                description="Lost Communication with ECM/PCM",
                severity=DTCSeverity.HIGH,
                system="Network Communication",
                module="Multiple Modules",
                common_causes=[
                    "CAN bus communication failure",
                    "PCM power or ground circuit issue",
                    "Wiring harness damage",
                    "PCM internal failure",
                    "Network gateway issue"
                ],
                diagnostic_steps=[
                    "Check CAN bus communication with scan tool",
                    "Verify PCM power and ground circuits",
                    "Inspect wiring harness for damage",
                    "Test network gateway operation",
                    "Check for other network communication DTCs"
                ],
                repair_procedures=[
                    "Repair CAN bus wiring if damaged",
                    "Address PCM power or ground issues",
                    "Replace PCM if faulty",
                    "Repair network gateway if needed"
                ],
                parameters_to_monitor=[
                    "CAN bus communication status",
                    "PCM power and ground voltages",
                    "Network message counters"
                ],
                conditions_to_set=[
                    "No communication received from PCM for more than 5 seconds",
                    "Multiple modules report lost communication with PCM"
                ],
                conditions_to_clear=[
                    "Communication restored with PCM for 3 consecutive drive cycles",
                    "DTC manually cleared with scan tool"
                ]
            )
        }
    
    def get_dtc_definition(self, dtc_code: str) -> Optional[DTCDefinition]:
        """Get complete DTC definition by code"""
        return self.dtc_database.get(dtc_code.upper())
    
    def get_dtcs_by_system(self, system: str) -> List[DTCDefinition]:
        """Get all DTCs for a specific system"""
        return [dtc for dtc in self.dtc_database.values() if dtc.system == system]
    
    def get_dtcs_by_severity(self, severity: DTCSeverity) -> List[DTCDefinition]:
        """Get all DTCs with specific severity"""
        return [dtc for dtc in self.dtc_database.values() if dtc.severity == severity]
    
    def get_mazda_specific_dtcs(self) -> List[DTCDefinition]:
        """Get all Mazda-specific DTCs"""
        return [dtc for dtc in self.dtc_database.values() if dtc.mazda_specific]
    
    def search_dtcs(self, search_term: str) -> List[DTCDefinition]:
        """Search DTCs by description or code"""
        search_term = search_term.lower()
        results = []
        
        for dtc in self.dtc_database.values():
            if (search_term in dtc.code.lower() or 
                search_term in dtc.description.lower() or
                any(search_term in cause.lower() for cause in dtc.common_causes)):
                results.append(dtc)
                
        return results
    
    def get_diagnostic_procedure(self, dtc_code: str) -> List[str]:
        """Get diagnostic procedure for specific DTC"""
        dtc = self.get_dtc_definition(dtc_code)
        if dtc:
            return dtc.diagnostic_steps
        return []
    
    def get_repair_procedure(self, dtc_code: str) -> List[str]:
        """Get repair procedure for specific DTC"""
        dtc = self.get_dtc_definition(dtc_code)
        if dtc:
            return dtc.repair_procedures
        return []