"""
MazdaOBDService - OBD-II communication protocols for Mazda vehicles.
Primary focus on ISO-15765-4 (CAN) protocol with abstraction for other protocols.
Handles standard and Mazda-specific PIDs, diagnostic services, and communication.
"""

import time
import struct
import logging
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio

from models import (
    OBDProtocol, OBDPacket, TelemetryData, DiagnosticTroubleCode,
    SecurityLevel, SecurityCredentials, LogEntry
)


class OBDCommandMode(Enum):
    """OBD command modes."""
    DEFAULT = "01"  # Show current data
    FREEZE_FRAME = "02"  # Show freeze frame data
    DTC = "03"  # Show stored DTCs
    CLEAR_DTC = "04"  # Clear DTCs
    OXYGEN_SENSOR = "05"  # Oxygen sensor test
    MONITOR_RESULTS = "06"  # On-board monitoring results
    PENDING_DTC = "07"  # Show pending DTCs
    CONTROL_SYSTEM = "08"  # Control system test
    VEHICLE_INFO = "09"  # Vehicle information
    PERMANENT_DTC = "0A"  # Permanent DTCs


class OBDResponseCode(Enum):
    """OBD response codes."""
    POSITIVE = "40"  # Positive response (mode + 0x40)
    NEGATIVE = "7F"  # Negative response
    GENERAL_REJECT = "10"
    SERVICE_NOT_SUPPORTED = "11"
    SUB_FUNCTION_NOT_SUPPORTED = "12"
    CONDITIONS_NOT_CORRECT = "22"
    REQUEST_SEQUENCE_ERROR = "24"
    SECURITY_ACCESS_DENIED = "33"


@dataclass
class OBDPID:
    """OBD Parameter ID definition."""
    pid: str  # Hex string
    name: str
    description: str
    units: str
    min_value: float
    max_value: float
    formula: str  # Formula to parse raw data
    data_type: str = "float"  # float, int, bool, string
    mazda_specific: bool = False
    security_level: SecurityLevel = SecurityLevel.READ_ONLY
    
    def parse_value(self, data: bytes) -> Union[float, int, bool, str]:
        """
        Parse raw data according to PID formula.
        
        Args:
            data: Raw data bytes from ECU
            
        Returns:
            Parsed value
        """
        if not data:
            return 0.0
        
        try:
            if self.data_type == "float":
                if self.formula == "A":
                    return float(data[0])
                elif self.formula == "A*256+B":
                    return float(data[0] * 256 + data[1])
                elif self.formula == "A/200":
                    return float(data[0]) / 200.0
                elif self.formula == "A-40":
                    return float(data[0]) - 40.0
                elif self.formula == "A*100/255":
                    return float(data[0]) * 100.0 / 255.0
                elif self.formula == "A*256+B/4":
                    return float(data[0] * 256 + data[1]) / 4.0
                else:
                    return float(data[0])
            
            elif self.data_type == "int":
                if self.formula == "A":
                    return int(data[0])
                elif self.formula == "A*256+B":
                    return int(data[0] * 256 + data[1])
                else:
                    return int(data[0])
            
            elif self.data_type == "bool":
                return bool(data[0] & 0x01)
            
            elif self.data_type == "string":
                return data.decode('ascii', errors='ignore').strip()
            
            else:
                return float(data[0])
                
        except (IndexError, ValueError, struct.error):
            return 0.0


class OBDError(Exception):
    """OBD communication errors."""
    pass


class OBDTimeoutError(OBDError):
    """Operation timeout."""
    pass


class OBDProtocolError(OBDError):
    """Protocol error."""
    pass


class MazdaPIDRegistry:
    """Registry of standard and Mazda-specific PIDs."""
    
    # Standard OBD-II PIDs
    STANDARD_PIDS = {
        "00": OBDPID("00", "PIDs Supported", "List of supported PIDs 01-20", "", 0, 0xFFFFFFFF, "A*256+B", "int"),
        "01": OBDPID("01", "Monitor Status", "Since DTCs cleared", "", 0, 0xFFFFFFFF, "A*256+B", "int"),
        "03": OBDPID("03", "Fuel System Status", "Fuel system status", "", 0, 0, "A", "int"),
        "04": OBDPID("04", "Calculated Engine Load", "Engine load percentage", "%", 0, 100, "A*100/255", "float"),
        "05": OBDPID("05", "Engine Coolant Temperature", "Engine coolant temperature", "°C", -40, 215, "A-40", "float"),
        "06": OBDPID("06", "Short Term Fuel Trim - Bank 1", "Short term fuel trim", "%", -100, 99.2, "A*100/128-100", "float"),
        "07": OBDPID("07", "Long Term Fuel Trim - Bank 1", "Long term fuel trim", "%", -100, 99.2, "A*100/128-100", "float"),
        "08": OBDPID("08", "Short Term Fuel Trim - Bank 2", "Short term fuel trim", "%", -100, 99.2, "A*100/128-100", "float"),
        "09": OBDPID("09", "Long Term Fuel Trim - Bank 2", "Long term fuel trim", "%", -100, 99.2, "A*100/128-100", "float"),
        "0A": OBDPID("0A", "Fuel Pressure", "Fuel pressure", "kPa", 0, 765, "A*3", "float"),
        "0B": OBDPID("0B", "Intake Manifold Absolute Pressure", "MAP sensor reading", "kPa", 0, 255, "A", "float"),
        "0C": OBDPID("0C", "Engine RPM", "Engine revolutions per minute", "RPM", 0, 16383.75, "A*256+B/4", "float"),
        "0D": OBDPID("0D", "Vehicle Speed", "Vehicle speed sensor", "km/h", 0, 255, "A", "float"),
        "0E": OBDPID("0E", "Timing Advance", "Ignition timing advance", "°", -64, 63.5, "A/2-64", "float"),
        "0F": OBDPID("0F", "Intake Air Temperature", "Intake air temperature", "°C", -40, 215, "A-40", "float"),
        "10": OBDPID("10", "MAF Air Flow Rate", "Mass air flow sensor", "g/s", 0, 655.35, "A*256+B/100", "float"),
        "11": OBDPID("11", "Throttle Position", "Throttle position", "%", 0, 100, "A*100/255", "float"),
        "13": OBDPID("13", "O2 Sensor Present", "O2 sensors present", "", 0, 0, "A", "int"),
        "14": OBDPID("14", "O2 Sensor 1", "Short term fuel trim", "%", -100, 99.2, "A*100/128-100", "float"),
        "15": OBDPID("15", "O2 Sensor 2", "Short term fuel trim", "%", -100, 99.2, "A*100/128-100", "float"),
        "1C": OBDPID("1C", "OBD Standards", "OBD standards this vehicle conforms to", "", 0, 0, "A", "int"),
        "1F": OBDPID("1F", "Runtime Since Engine Start", "Time since engine start", "seconds", 0, 65535, "A*256+B", "int"),
        "21": OBDPID("21", "Distance Traveled with MIL On", "Distance with MIL on", "km", 0, 65535, "A*256+B", "int"),
        "22": OBDPID("22", "Fuel Rail Pressure", "Fuel rail pressure", "kPa", 0, 65535, "A*256+B*0.079", "float"),
        "23": OBDPID("23", "Fuel Rail Gauge Pressure", "Fuel rail gauge pressure", "kPa", 0, 65535, "A*256+B", "int"),
        "24": OBDPID("24", "O2 Sensor 1", "Air-fuel ratio", "", 0, 0, "A*256+B/32768", "float"),
        "25": OBDPID("25", "O2 Sensor 2", "Air-fuel ratio", "", 0, 0, "A*256+B/32768", "float"),
        "2C": OBDPID("2C", "ECU Name", "ECU identification", "", 0, 0, "string", "string"),
        "2D": OBDPID("2D", "VIN Number", "Vehicle identification number", "", 0, 0, "string", "string"),
        "2E": OBDPID("2E", "Calibration ID", "ECU calibration identification", "", 0, 0, "string", "string"),
        "2F": OBDPID("2F", "Calibration Verification", "Calibration verification number", "", 0, 0, "A*256+B", "int"),
        "31": OBDPID("31", "Distance Traveled Since Codes Cleared", "Distance since DTC clear", "km", 0, 65535, "A*256+B", "int"),
        "33": OBDPID("33", "Absolute Barometric Pressure", "Barometric pressure", "kPa", 0, 255, "A", "float"),
        "42": OBDPID("42", "Control Module Voltage", "Control module voltage", "V", 0, 65.535, "A*256+B/1000", "float"),
        "43": OBDPID("43", "Absolute Load Value", "Absolute engine load", "%", 0, 25700, "A*100/255", "float"),
        "44": OBDPID("44", "Commanded Air-Fuel Ratio", "Commanded air-fuel ratio", "", 0, 0, "A*256+B/32768", "float"),
        "45": OBDPID("45", "Relative Throttle Position", "Relative throttle position", "%", 0, 100, "A*100/255", "float"),
        "46": OBDPID("46", "Ambient Air Temperature", "Ambient air temperature", "°C", -40, 215, "A-40", "float"),
        "47": OBDPID("47", "Absolute Throttle Position B", "Absolute throttle position B", "%", 0, 100, "A*100/255", "float"),
        "48": OBDPID("48", "Absolute Throttle Position C", "Absolute throttle position C", "%", 0, 100, "A*100/255", "float"),
        "49": OBDPID("49", "Accelerator Pedal Position D", "Accelerator pedal position D", "%", 0, 100, "A*100/255", "float"),
        "4A": OBDPID("4A", "Accelerator Pedal Position E", "Accelerator pedal position E", "%", 0, 100, "A*100/255", "float"),
        "4B": OBDPID("4B", "Accelerator Pedal Position F", "Accelerator pedal position F", "%", 0, 100, "A*100/255", "float"),
        "4C": OBDPID("4C", "Commanded Throttle Actuator", "Commanded throttle actuator", "%", 0, 100, "A*100/255", "float"),
        "4E": OBDPID("4E", "Engine Oil Temperature", "Engine oil temperature", "°C", -40, 210, "A-40", "float"),
        "51": OBDPID("51", "Fuel Type", "Fuel type designation", "", 0, 0, "A", "int"),
        "52": OBDPID("52", "Ethanol Fuel %", "Ethanol fuel percentage", "%", 0, 100, "A*100/255", "float"),
        "53": OBDPID("53", "Absolute Evap System Vapor Pressure", "Evap system vapor pressure", "kPa", 0, 327.675, "A*256+B/200", "float"),
        "54": OBDPID("54", "Evap System Vapor Pressure", "Evap vapor pressure", "Pa", -32768, 32767, "A*256+B", "int"),
        "5A": OBDPID("5A", "Relative Accelerator Pedal Position", "Relative accelerator pedal position", "%", 0, 100, "A*100/255", "float"),
        "5B": OBDPID("5B", "Hybrid Battery Pack Remaining Life", "Hybrid battery remaining life", "%", 0, 100, "A", "float"),
        "5C": OBDPID("5C", "Engine Oil Temperature", "Engine oil temperature", "°C", -40, 215, "A-40", "float"),
        "5D": OBDPID("5D", "Fuel Injection Timing", "Fuel injection timing", "°", -210, 301.992, "A*256+B/128-210", "float"),
        "5E": OBDPID("5E", "Engine Fuel Rate", "Engine fuel rate", "L/h", 0, 3212.75, "A*256+B/20", "float"),
        "5F": OBDPID("5F", "Emission Requirements", "Emission requirements", "", 0, 0, "A", "int"),
        "61": OBDPID("61", "Driver's Demand Engine - Percent Torque", "Driver's demand torque", "%", -125, 125, "A-125", "float"),
        "62": OBDPID("62", "Actual Engine - Percent Torque", "Actual engine torque", "%", -125, 125, "A-125", "float"),
        "63": OBDPID("63", "Engine Reference Torque", "Engine reference torque", "Nm", 0, 65535, "A*256+B", "int"),
        "64": OBDPID("64", "Engine Percent Torque Data", "Engine percent torque", "%", -125, 125, "A-125", "float"),
        "65": OBDPID("65", "Auxiliary Input/Output Supported", "Aux I/O supported", "", 0, 0, "A", "int"),
        "66": OBDPID("66", "Mass Air Flow Sensor", "MAF sensor", "g/s", 0, 65535, "A*256+B", "int"),
        "67": OBDPID("67", "Engine Coolant Temperature", "Engine coolant temperature", "°C", -40, 215, "A-40", "float"),
        "68": OBDPID("68", "Intake Air Temperature Sensor", "Intake air temperature", "°C", -40, 215, "A-40", "float"),
        "69": OBDPID("69", "Commanded EGR and EGR Error", "Commanded EGR", "%", -100, 100, "A-100", "float"),
        "6A": OBDPID("6A", "Commanded Intake Manifold Runner Control", "IMRC command", "%", -100, 100, "A-100", "float"),
        "6B": OBDPID("6B", "Fuel Rail Pressure", "Fuel rail pressure", "kPa", 0, 65535, "A*256+B*0.1", "float"),
        "6C": OBDPID("6C", "Fuel Pressure", "Fuel pressure", "kPa", 0, 65535, "A*256+B*0.1", "float"),
        "6D": OBDPID("6D", "Injector Pressure", "Injector pressure", "kPa", 0, 65535, "A*256+B*0.1", "float"),
        "6E": OBDPID("6E", "Fuel Rail Absolute Pressure", "Fuel rail absolute pressure", "kPa", 0, 65535, "A*256+B*0.1", "float"),
        "6F": OBDPID("6F", "Engine Friction Torque", "Engine friction torque", "Nm", 0, 65535, "A*256+B", "int"),
        "70": OBDPID("70", "PM Sensor", "Particulate matter sensor", "", 0, 0, "A", "int"),
        "71": OBDPID("71", "Boost Pressure Control", "Boost pressure control", "%", 0, 100, "A", "float"),
        "72": OBDPID("72", "Variable Geometry Turbo Control", "VGT control", "%", 0, 100, "A", "float"),
        "73": OBDPID("73", "Wastegate Control", "Wastegate control", "%", 0, 100, "A", "float"),
        "74": OBDPID("74", "Exhaust Pressure", "Exhaust pressure", "kPa", 0, 65535, "A*256+B", "int"),
        "75": OBDPID("75", "Turbocharger RPM", "Turbocharger RPM", "RPM", 0, 65535, "A*256+B", "int"),
        "76": OBDPID("76", "Turbocharger Temperature", "Turbocharger temperature", "°C", -40, 215, "A-40", "float"),
        "77": OBDPID("77", "Turbocharger Temperature", "Turbocharger temperature", "°C", -40, 215, "A-40", "float"),
        "78": OBDPID("78", "Turbocharger Ratio", "Turbocharger ratio", "", 0, 0, "A*256+B", "int"),
        "79": OBDPID("79", "Charge Air Cooler Temperature", "Charge air cooler temperature", "°C", -40, 215, "A-40", "float"),
        "7A": OBDPID("7A", "Exhaust Gas Temperature", "Exhaust gas temperature", "°C", -40, 215, "A-40", "float"),
        "7B": OBDPID("7B", "Diesel Particulate Filter", "DPF status", "", 0, 0, "A", "int"),
        "7C": OBDPID("7C", "Diesel Particulate Filter", "DPF status", "", 0, 0, "A", "int"),
        "7D": OBDPID("7D", "Diesel Particulate Filter", "DPF status", "", 0, 0, "A", "int"),
        "7E": OBDPID("7E", "Diesel Particulate Filter", "DPF status", "", 0, 0, "A", "int"),
        "7F": OBDPID("7F", "Diesel Particulate Filter", "DPF status", "", 0, 0, "A", "int"),
    }
    
    # Mazda-specific PIDs (proprietary)
    MAZDA_SPECIFIC_PIDS = {
        "A0": OBDPID("A0", "Mazda Boost Target", "Target boost pressure", "psi", 0, 30, "A*0.145", "float", True, SecurityLevel.DIAGNOSTIC),
        "A1": OBDPID("A1", "Mazda Boost Actual", "Actual boost pressure", "psi", 0, 30, "A*0.145", "float", True, SecurityLevel.DIAGNOSTIC),
        "A2": OBDPID("A2", "Mazda Wastegate Duty", "Wastegate duty cycle", "%", 0, 100, "A*100/255", "float", True, SecurityLevel.DIAGNOSTIC),
        "A3": OBDPID("A3", "Mazda Ignition Timing", "Ignition timing advance", "°", -20, 60, "A-20", "float", True, SecurityLevel.DIAGNOSTIC),
        "A4": OBDPID("A4", "Mazda Fuel Pressure", "High pressure fuel pump", "MPa", 0, 200, "A*0.1", "float", True, SecurityLevel.DIAGNOSTIC),
        "A5": OBDPID("A5", "Mazda Knock Retard", "Knock retard", "°", 0, 20, "A*0.25", "float", True, SecurityLevel.DIAGNOSTIC),
        "A6": OBDPID("A6", "Mazda Oil Pressure", "Oil pressure", "psi", 0, 100, "A*0.5", "float", True, SecurityLevel.DIAGNOSTIC),
        "A7": OBDPID("A7", "Mazda Transmission Gear", "Current gear", "", 0, 6, "A", "int", True, SecurityLevel.DIAGNOSTIC),
        "A8": OBDPID("A8", "Mazda Torque Request", "Torque request", "Nm", 0, 400, "A*2", "float", True, SecurityLevel.DIAGNOSTIC),
        "A9": OBDPID("A9", "Mazda Torque Actual", "Actual torque", "Nm", 0, 400, "A*2", "float", True, SecurityLevel.DIAGNOSTIC),
        "AA": OBDPID("AA", "Mazda AFR Target", "Target AFR", "", 10, 20, "A*0.1+10", "float", True, SecurityLevel.DIAGNOSTIC),
        "AB": OBDPID("AB", "Mazda AFR Actual", "Actual AFR", "", 10, 20, "A*0.1+10", "float", True, SecurityLevel.DIAGNOSTIC),
        "AC": OBDPID("AC", "Mazda Dwell Time", "Ignition coil dwell", "ms", 0, 10, "A*0.04", "float", True, SecurityLevel.DIAGNOSTIC),
        "AD": OBDPID("AD", "Mazda Valve Timing", "Valve timing advance", "°", -20, 60, "A-20", "float", True, SecurityLevel.DIAGNOSTIC),
        "AE": OBDPID("AE", "Mazda Throttle Desired", "Desired throttle position", "%", 0, 100, "A*100/255", "float", True, SecurityLevel.DIAGNOSTIC),
        "AF": OBDPID("AF", "Mazda Fuel Trim Bank 1", "Bank 1 fuel trim", "%", -25, 25, "A*0.5-25", "float", True, SecurityLevel.DIAGNOSTIC),
        "B0": OBDPID("B0", "Mazda Fuel Trim Bank 2", "Bank 2 fuel trim", "%", -25, 25, "A*0.5-25", "float", True, SecurityLevel.DIAGNOSTIC),
        "B1": OBDPID("B1", "Mazda ECU Temperature", "ECU internal temperature", "°C", -40, 125, "A-40", "float", True, SecurityLevel.DIAGNOSTIC),
        "B2": OBDPID("B2", "Mazda Battery Voltage", "Battery voltage", "V", 0, 20, "A*0.08", "float", True, SecurityLevel.DIAGNOSTIC),
        "B3": OBDPID("B3", "Mazda Load Absolute", "Absolute engine load", "%", 0, 100, "A*100/255", "float", True, SecurityLevel.DIAGNOSTIC),
        "B4": OBDPID("B4", "Mazda Acceleration Enrichment", "Acceleration enrichment", "%", 0, 50, "A*0.2", "float", True, SecurityLevel.DIAGNOSTIC),
        "B5": OBDPID("B5", "Mazda Deceleration Fuel Cut", "Deceleration fuel cut status", "", 0, 1, "A&0x01", "bool", True, SecurityLevel.DIAGNOSTIC),
        "B6": OBDPID("B6", "Mazda Boost Control Mode", "Boost control mode", "", 0, 3, "A", "int", True, SecurityLevel.DIAGNOSTIC),
        "B7": OBDPID("B7", "Mazda Wastegate Mode", "Wastegate control mode", "", 0, 2, "A", "int", True, SecurityLevel.DIAGNOSTIC),
        "B8": OBDPID("B8", "Mazda TCS Status", "Traction control status", "", 0, 1, "A&0x01", "bool", True, SecurityLevel.DIAGNOSTIC),
        "B9": OBDPID("B9", "Mazda ABS Status", "ABS system status", "", 0, 1, "A&0x01", "bool", True, SecurityLevel.DIAGNOSTIC),
        "BA": OBDPID("BA", "Mazda Cruise Control", "Cruise control status", "", 0, 1, "A&0x01", "bool", True, SecurityLevel.DIAGNOSTIC),
        "BB": OBDPID("BB", "Mazda AC Compressor", "AC compressor status", "", 0, 1, "A&0x01", "bool", True, SecurityLevel.DIAGNOSTIC),
        "BC": OBDPID("BC", "Mazda Radiator Fan", "Radiator fan status", "", 0, 3, "A", "int", True, SecurityLevel.DIAGNOSTIC),
        "BD": OBDPID("BD", "Mazda Fuel Pump", "Fuel pump status", "", 0, 1, "A&0x01", "bool", True, SecurityLevel.DIAGNOSTIC),
        "BE": OBDPID("BE", "Mazda Check Engine", "Check engine light status", "", 0, 1, "A&0x80", "bool", True, SecurityLevel.DIAGNOSTIC),
        "BF": OBDPID("BF", "Mazda Security Light", "Security indicator status", "", 0, 1, "A&0x01", "bool", True, SecurityLevel.DIAGNOSTIC),
    }
    
    @classmethod
    def get_pid(cls, pid: str, mazda_specific: bool = False) -> Optional[OBDPID]:
        """Get PID definition."""
        if mazda_specific:
            return cls.MAZDA_SPECIFIC_PIDS.get(pid.upper())
        return cls.STANDARD_PIDS.get(pid.upper())
    
    @classmethod
    def get_all_pids(cls, mazda_specific: bool = False) -> Dict[str, OBDPID]:
        """Get all PIDs."""
        if mazda_specific:
            return cls.MAZDA_SPECIFIC_PIDS.copy()
        return cls.STANDARD_PIDS.copy()
    
    @classmethod
    def search_pids(cls, search_term: str, mazda_specific: bool = False) -> List[OBDPID]:
        """Search PIDs by name or description."""
        pids = cls.get_all_pids(mazda_specific)
        results = []
        
        search_lower = search_term.lower()
        for pid in pids.values():
            if (search_term.lower() in pid.name.lower() or 
                search_term.lower() in pid.description.lower()):
                results.append(pid)
        
        return results


class MazdaOBDService:
    """
    OBD-II service for Mazda vehicles with primary focus on ISO-15765-4 (CAN).
    Provides communication abstraction and PID handling.
    """
    
    def __init__(self, protocol: OBDProtocol = OBDProtocol.ISO_15765_4):
        """
        Initialize OBD service.
        
        Args:
            protocol: OBD protocol to use
        """
        self.logger = logging.getLogger(__name__)
        self.protocol = protocol
        self.pid_registry = MazdaPIDRegistry()
        
        # Communication state
        self.is_connected = False
        self.interface = None  # Will be injected or set separately
        self.current_session = None
        
        # Timing and performance
        self.default_timeout = 2.0  # seconds
        self.max_retries = 3
        self.response_times = []
        
        # Protocol-specific configuration
        self.protocol_config = {
            OBDProtocol.ISO_15765_4: {
                "can_id_request": 0x7DF,
                "can_id_response": 0x7E8,
                "header_size": 3,
                "max_message_size": 4095,
                "st_min": 0,  # Minimum separation time
                "bs": 8,      # Block size
            },
            OBDProtocol.ISO_9141_2: {
                "baud_rate": 10400,
                "init_bytes": [0x33, 0x01, 0x8D],
                "kb1": 0x01,
                "kb2": 0x8D,
            },
            OBDProtocol.ISO_14230_4: {
                "baud_rate": 10400,
                "fast_init": True,
                "header_format": "functional",
            },
        }
        
        self.logger.info(f"MazdaOBDService initialized with protocol: {protocol.value}")
    
    def set_interface(self, interface) -> None:
        """Set communication interface (CAN adapter, serial port, etc.)."""
        self.interface = interface
        self.logger.info(f"Communication interface set: {type(interface).__name__}")
    
    async def connect(self) -> bool:
        """
        Establish OBD connection.
        
        Returns:
            True if connection successful
        """
        if not self.interface:
            raise OBDError("No communication interface set")
        
        try:
            # Protocol-specific initialization
            if self.protocol == OBDProtocol.ISO_15765_4:
                success = await self._connect_can()
            elif self.protocol == OBDProtocol.ISO_9141_2:
                success = await self._connect_iso9141()
            elif self.protocol == OBDProtocol.ISO_14230_4:
                success = await self._connect_kwp2000()
            else:
                raise OBDProtocolError(f"Unsupported protocol: {self.protocol}")
            
            if success:
                self.is_connected = True
                self.logger.info(f"OBD connection established using {self.protocol.value}")
                return True
            else:
                self.logger.error("Failed to establish OBD connection")
                return False
                
        except Exception as e:
            self.logger.error(f"OBD connection failed: {e}")
            raise OBDError(f"Connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close OBD connection."""
        if self.is_connected and self.interface:
            try:
                # Protocol-specific disconnection
                if hasattr(self.interface, 'close'):
                    await self.interface.close()
            except Exception as e:
                self.logger.warning(f"Error during disconnection: {e}")
        
        self.is_connected = False
        self.logger.info("OBD connection closed")
    
    async def _connect_can(self) -> bool:
        """Connect using ISO-15765-4 (CAN) protocol."""
        config = self.protocol_config[self.protocol]
        
        # Initialize CAN interface
        if hasattr(self.interface, 'connect'):
            return await self.interface.connect(
                can_id_request=config["can_id_request"],
                can_id_response=config["can_id_response"]
            )
        return True  # Assume connected if no specific method
    
    async def _connect_iso9141(self) -> bool:
        """Connect using ISO-9141-2 protocol."""
        config = self.protocol_config[self.protocol]
        
        # Implementation for ISO-9141-2 initialization
        if hasattr(self.interface, 'init_iso9141'):
            return await self.interface.init_iso9141(
                baud_rate=config["baud_rate"],
                init_bytes=config["init_bytes"]
            )
        return False
    
    async def _connect_kwp2000(self) -> bool:
        """Connect using ISO-14230-4 (KWP2000) protocol."""
        config = self.protocol_config[self.protocol]
        
        # Implementation for KWP2000 initialization
        if hasattr(self.interface, 'init_kwp2000'):
            return await self.interface.init_kwp2000(
                baud_rate=config["baud_rate"],
                fast_init=config["fast_init"]
            )
        return False
    
    async def send_command(self, mode: OBDCommandMode, pid: str = "", 
                          data: Optional[bytes] = None,
                          credentials: Optional[SecurityCredentials] = None) -> OBDPacket:
        """
        Send OBD command and receive response.
        
        Args:
            mode: OBD command mode
            pid: Parameter ID (hex string)
            data: Additional data bytes
            credentials: Security credentials for authorization
            
        Returns:
            Response packet
        """
        if not self.is_connected:
            raise OBDError("Not connected to OBD interface")
        
        # Check security for Mazda-specific PIDs
        if credentials and pid.upper() in self.pid_registry.MAZDA_SPECIFIC_PIDS:
            mazda_pid = self.pid_registry.get_pid(pid, mazda_specific=True)
            if mazda_pid and not self._check_security(credentials, mazda_pid):
                raise OBDError(f"Insufficient security level for PID {pid}")
        
        # Build command packet
        command_data = bytes.fromhex(mode.value)
        if pid:
            command_data += bytes.fromhex(pid)
        if data:
            command_data += data
        
        packet = OBDPacket(
            service_id=int(mode.value, 16),
            data=command_data,
            protocol=self.protocol,
            response_expected=True
        )
        
        # Send command with retries
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                response = await self._send_packet_with_retry(packet)
                response_time = time.time() - start_time
                self.response_times.append(response_time)
                
                # Keep response time history manageable
                if len(self.response_times) > 100:
                    self.response_times = self.response_times[-50:]
                
                return response
                
            except OBDTimeoutError:
                self.logger.warning(f"Command timeout, attempt {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(0.1 * (attempt + 1))
            
            except Exception as e:
                self.logger.error(f"Command failed on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    raise OBDError(f"Command failed after {self.max_retries} attempts: {e}")
                await asyncio.sleep(0.1 * (attempt + 1))
    
    async def _send_packet_with_retry(self, packet: OBDPacket) -> OBDPacket:
        """Send packet and wait for response."""
        if not self.interface:
            raise OBDError("No communication interface available")
        
        # Protocol-specific packet sending
        if self.protocol == OBDProtocol.ISO_15765_4:
            return await self._send_can_packet(packet)
        elif self.protocol in [OBDProtocol.ISO_9141_2, OBDProtocol.ISO_14230_4]:
            return await self._send_serial_packet(packet)
        else:
            raise OBDProtocolError(f"Unsupported protocol: {self.protocol}")
    
    async def _send_can_packet(self, packet: OBDPacket) -> OBDPacket:
        """Send packet using CAN protocol."""
        config = self.protocol_config[self.protocol]
        
        # Build CAN message
        can_data = self._build_can_message(packet)
        
        # Send via CAN interface
        if hasattr(self.interface, 'send_can_message'):
            response_data = await asyncio.wait_for(
                self.interface.send_can_message(
                    arbitration_id=config["can_id_request"],
                    data=can_data
                ),
                timeout=self.default_timeout
            )
        else:
            raise OBDError("CAN interface does not support send_can_message")
        
        # Parse response
        return self._parse_can_response(response_data, packet)
    
    async def _send_serial_packet(self, packet: OBDPacket) -> OBDPacket:
        """Send packet using serial protocol."""
        # Implementation for serial protocols (ISO-9141-2, KWP2000)
        if hasattr(self.interface, 'send_serial_packet'):
            response_data = await asyncio.wait_for(
                self.interface.send_serial_packet(packet.data),
                timeout=self.default_timeout
            )
        else:
            raise OBDError("Serial interface does not support send_serial_packet")
        
        return self._parse_serial_response(response_data, packet)
    
    def _build_can_message(self, packet: OBDPacket) -> bytes:
        """Build CAN message from OBD packet."""
        config = self.protocol_config[self.protocol]
        
        # ISO-TP single frame
        can_data = bytes([0x00])  # Single frame, length
        can_data += packet.data
        
        return can_data
    
    def _parse_can_response(self, response_data: bytes, 
                           original_packet: OBDPacket) -> OBDPacket:
        """Parse CAN response data."""
        if not response_data:
            raise OBDError("Empty response received")
        
        # Remove ISO-TP header if present
        if len(response_data) > 3 and response_data[0] == 0x00:
            data = response_data[1:]
        else:
            data = response_data
        
        return OBDPacket(
            service_id=data[0] if data else 0,
            data=data,
            protocol=self.protocol,
            response_expected=False
        )
    
    def _parse_serial_response(self, response_data: bytes,
                              original_packet: OBDPacket) -> OBDPacket:
        """Parse serial protocol response."""
        # Implementation for serial response parsing
        return OBDPacket(
            service_id=response_data[0] if response_data else 0,
            data=response_data,
            protocol=self.protocol,
            response_expected=False
        )
    
    def _check_security(self, credentials: SecurityCredentials, pid: OBDPID) -> bool:
        """Check if user has sufficient security level for PID."""
        if not credentials:
            return pid.security_level == SecurityLevel.NONE
        
        return credentials.security_level.value >= pid.security_level.value
    
    async def read_pid(self, pid: str, mazda_specific: bool = False,
                      credentials: Optional[SecurityCredentials] = None) -> Union[float, int, bool, str]:
        """
        Read specific PID value.
        
        Args:
            pid: PID to read (hex string)
            mazda_specific: Whether to read Mazda-specific PID
            credentials: Security credentials
            
        Returns:
            Parsed PID value
        """
        pid_def = self.pid_registry.get_pid(pid, mazda_specific)
        if not pid_def:
            raise OBDError(f"Unknown PID: {pid}")
        
        # Send command
        response = await self.send_command(
            OBDCommandMode.DEFAULT, pid, credentials=credentials
        )
        
        # Parse response
        if len(response.data) < 2:
            raise OBDError(f"Invalid response for PID {pid}")
        
        # Remove service byte and PID byte
        data_bytes = response.data[2:]
        return pid_def.parse_value(data_bytes)
    
    async def get_telemetry_snapshot(self, 
                                    credentials: Optional[SecurityCredentials] = None) -> TelemetryData:
        """
        Get complete telemetry snapshot.
        
        Args:
            credentials: Security credentials
            
        Returns:
            TelemetryData object with current values
        """
        telemetry = TelemetryData()
        
        # Define PIDs to read for complete snapshot
        pid_mappings = {
            "0C": "rpm",
            "04": "load", 
            "0B": "map",
            "10": "maf",
            "0F": "iat",
            "05": "ect",
            "11": "throttle_position",
            "0D": "vehicle_speed",
            "0E": "timing_advance",
            "0A": "fuel_pressure",
        }
        
        # Add Mazda-specific PIDs if credentials allow
        mazda_mappings = {
            "A0": "boost_target",
            "A1": "boost_pressure", 
            "A2": "wastegate_duty",
            "A3": "timing_advance",
            "A5": "knock_retard",
            "A6": "oil_pressure",
            "A7": "gear",
        }
        
        # Read standard PIDs
        for pid, attr in pid_mappings.items():
            try:
                value = await self.read_pid(pid, credentials=credentials)
                setattr(telemetry, attr, value)
            except Exception as e:
                self.logger.warning(f"Failed to read PID {pid}: {e}")
        
        # Read Mazda-specific PIDs if authorized
        if credentials and credentials.security_level.value >= SecurityLevel.DIAGNOSTIC.value:
            for pid, attr in mazda_mappings.items():
                try:
                    value = await self.read_pid(pid, mazda_specific=True, credentials=credentials)
                    setattr(telemetry, attr, value)
                except Exception as e:
                    self.logger.warning(f"Failed to read Mazda PID {pid}: {e}")
        
        return telemetry
    
    async def get_supported_pids(self, credentials: Optional[SecurityCredentials] = None) -> List[str]:
        """
        Get list of supported PIDs.
        
        Args:
            credentials: Security credentials
            
        Returns:
            List of supported PID hex strings
        """
        response = await self.send_command(OBDCommandMode.DEFAULT, "00", credentials=credentials)
        
        if len(response.data) < 6:
            return []
        
        # Parse PID support bitmap (bytes 3-6)
        support_bytes = response.data[2:6]
        supported_pids = []
        
        for i, byte in enumerate(support_bytes):
            for bit in range(8):
                if byte & (1 << bit):
                    pid_num = i * 8 + bit + 1
                    if pid_num <= 0x20:  # PIDs 01-20
                        pid_hex = f"{pid_num:02X}"
                        supported_pids.append(pid_hex)
        
        return supported_pids
    
    async def clear_dtc(self, credentials: Optional[SecurityCredentials] = None) -> bool:
        """
        Clear diagnostic trouble codes.
        
        Args:
            credentials: Security credentials (requires DIAGNOSTIC level)
            
        Returns:
            True if DTCs cleared successfully
        """
        if credentials:
            # This operation requires diagnostic security level
            from mazda_security_core import MazdaSecurityCore
            security = MazdaSecurityCore()
            security.authorize_operation(credentials, SecurityLevel.DIAGNOSTIC, "clear DTCs")
        
        response = await self.send_command(OBDCommandMode.CLEAR_DTC, credentials=credentials)
        
        # Check for positive response
        if len(response.data) >= 1 and response.data[0] == 0x44:  # 0x04 + 0x40
            self.logger.info("DTCs cleared successfully")
            return True
        else:
            self.logger.error("Failed to clear DTCs")
            return False
    
    async def get_vin(self, credentials: Optional[SecurityCredentials] = None) -> str:
        """
        Get Vehicle Identification Number.
        
        Args:
            credentials: Security credentials
            
        Returns:
            VIN string
        """
        response = await self.send_command(OBDCommandMode.VEHICLE_INFO, "2", credentials=credentials)
        
        if len(response.data) < 4:
            raise OBDError("Invalid VIN response")
        
        # VIN is in data bytes after service and PID
        vin_data = response.data[3:]
        try:
            return vin_data.decode('ascii', errors='ignore').strip()
        except UnicodeDecodeError:
            return ""
    
    async def get_ecu_info(self, credentials: Optional[SecurityCredentials] = None) -> Dict[str, str]:
        """
        Get ECU identification information.
        
        Args:
            credentials: Security credentials
            
        Returns:
            Dictionary with ECU info
        """
        info = {}
        
        # Get calibration ID
        try:
            response = await self.send_command(OBDCommandMode.VEHICLE_INFO, "6", credentials=credentials)
            if len(response.data) > 3:
                cal_data = response.data[3:]
                info["calibration_id"] = cal_data.decode('ascii', errors='ignore').strip()
        except Exception as e:
            self.logger.warning(f"Failed to get calibration ID: {e}")
        
        # Get ECU name
        try:
            response = await self.send_command(OBDCommandMode.VEHICLE_INFO, "12", credentials=credentials)
            if len(response.data) > 3:
                ecu_data = response.data[3:]
                info["ecu_name"] = ecu_data.decode('ascii', errors='ignore').strip()
        except Exception as e:
            self.logger.warning(f"Failed to get ECU name: {e}")
        
        return info
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get communication performance statistics."""
        if not self.response_times:
            return {"avg_response_time": 0, "min_response_time": 0, "max_response_time": 0}
        
        return {
            "avg_response_time": sum(self.response_times) / len(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "total_requests": len(self.response_times),
            "protocol": self.protocol.value,
            "connected": self.is_connected,
        }
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.is_connected:
            self.logger.warning("OBDService deleted while still connected")
