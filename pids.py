#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3_COMPLETE_DIAGNOSTIC_DATABASE.py
FULL PID, DTC, AND DIAGNOSTIC CODE DATABASE FOR 2011 MAZDASPEED 3
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class ServiceType(Enum):
    """OBD2 SERVICE TYPES"""
    CURRENT_DATA = 0x01
    FREEZE_FRAME_DATA = 0x02
    DIAGNOSTIC_TROUBLE_CODES = 0x03
    CLEAR_DTCS = 0x04
    OXYGEN_SENSOR_TEST = 0x05
    ONBOARD_MONITORING = 0x06
    PENDING_DTCS = 0x07
    CONTROL_OPERATION = 0x08
    VEHICLE_INFO = 0x09
    PERMANENT_DTCS = 0x0A

@dataclass
class PIDDefinition:
    """COMPLETE PID DEFINITION"""
    pid: str
    description: str
    formula: str
    units: str
    min_value: float
    max_value: float
    byte_length: int
    mazda_specific: bool = False

@dataclass
class DTCDefinition:
    """COMPLETE DTC DEFINITION"""
    code: str
    description: str
    severity: str
    common_causes: List[str]
    diagnostic_steps: List[str]
    mazda_specific: bool = False

class Mazdaspeed3DiagnosticDatabase:
    """
    COMPLETE DIAGNOSTIC DATABASE FOR 2011 MAZDASPEED 3
    """
    
    # STANDARD OBD2 PIDS
    STANDARD_PIDS = {
        # ENGINE PIDS
        "0100": PIDDefinition("0100", "Supported PIDs 01-20", "Bit encoded", "N/A", 0, 0, 4),
        "0101": PIDDefinition("0101", "Monitor Status Since DTC Cleared", "Bit encoded", "N/A", 0, 0, 4),
        "0102": PIDDefinition("0102", "Freeze DTC", "Hex encoded", "N/A", 0, 0, 2),
        "0103": PIDDefinition("0103", "Fuel System Status", "Bit encoded", "N/A", 0, 0, 2),
        "0104": PIDDefinition("0104", "Calculated Engine Load", "A*100/255", "%", 0, 100, 1),
        "0105": PIDDefinition("0105", "Engine Coolant Temperature", "A-40", "°C", -40, 215, 1),
        "0106": PIDDefinition("0106", "Short Term Fuel Trim Bank 1", "(A-128)*100/128", "%", -100, 99.2, 1),
        "0107": PIDDefinition("0107", "Long Term Fuel Trim Bank 1", "(A-128)*100/128", "%", -100, 99.2, 1),
        "0108": PIDDefinition("0108", "Short Term Fuel Trim Bank 2", "(A-128)*100/128", "%", -100, 99.2, 1),
        "0109": PIDDefinition("0109", "Long Term Fuel Trim Bank 2", "(A-128)*100/128", "%", -100, 99.2, 1),
        "010A": PIDDefinition("010A", "Fuel Pressure", "A*3", "kPa", 0, 765, 1),
        "010B": PIDDefinition("010B", "Intake Manifold Pressure", "A", "kPa", 0, 255, 1),
        "010C": PIDDefinition("010C", "Engine RPM", "(256*A+B)/4", "RPM", 0, 16383.75, 2),
        "010D": PIDDefinition("010D", "Vehicle Speed", "A", "km/h", 0, 255, 1),
        "010E": PIDDefinition("010E", "Timing Advance", "(A/2)-64", "°", -64, 63.5, 1),
        "010F": PIDDefinition("010F", "Intake Air Temperature", "A-40", "°C", -40, 215, 1),
        "0110": PIDDefinition("0110", "MAF Air Flow Rate", "(256*A+B)/100", "g/s", 0, 655.35, 2),
        "0111": PIDDefinition("0111", "Throttle Position", "A*100/255", "%", 0, 100, 1),
        "0112": PIDDefinition("0112", "Commanded Secondary Air Status", "Bit encoded", "N/A", 0, 0, 1),
        "0113": PIDDefinition("0113", "Oxygen Sensors Present", "Bit encoded", "N/A", 0, 0, 1),
        "0114": PIDDefinition("0114", "Bank 1 Sensor 1 Oxygen Sensor Voltage", "A/200", "V", 0, 1.275, 1),
        "0115": PIDDefinition("0115", "Bank 1 Sensor 1 Short Term Fuel Trim", "(A-128)*100/128", "%", -100, 99.2, 1),
        
        # MAZDA-SPECIFIC PIDS
        "0121": PIDDefinition("0121", "Distance Traveled with MIL On", "256*A+B", "km", 0, 65535, 2, True),
        "012F": PIDDefinition("012F", "Fuel Level Input", "A*100/255", "%", 0, 100, 1),
        "0130": PIDDefinition("0130", "Warm-ups Since Codes Cleared", "A", "count", 0, 255, 1),
        "0131": PIDDefinition("0131", "Distance Since Codes Cleared", "256*A+B", "km", 0, 65535, 2),
        "0133": PIDDefinition("0133", "Barometric Pressure", "A", "kPa", 0, 255, 1),
        "0142": PIDDefinition("0142", "Control Module Voltage", "(256*A+B)/1000", "V", 0, 65.535, 2),
        "0143": PIDDefinition("0143", "Absolute Load Value", "(256*A+B)*100/255", "%", 0, 25700, 2),
        "0144": PIDDefinition("0144", "Commanded Equivalence Ratio", "(256*A+B)/32768", "ratio", 0, 2, 2),
        "0145": PIDDefinition("0145", "Relative Throttle Position", "A*100/255", "%", 0, 100, 1),
        "0146": PIDDefinition("0146", "Ambient Air Temperature", "A-40", "°C", -40, 215, 1),
        "0147": PIDDefinition("0147", "Absolute Throttle Position B", "A*100/255", "%", 0, 100, 1),
        "0148": PIDDefinition("0148", "Absolute Throttle Position C", "A*100/255", "%", 0, 100, 1),
        "0149": PIDDefinition("0149", "Accelerator Pedal Position D", "A*100/255", "%", 0, 100, 1),
        "014A": PIDDefinition("014A", "Accelerator Pedal Position E", "A*100/255", "%", 0, 100, 1),
        "014B": PIDDefinition("014B", "Accelerator Pedal Position F", "A*100/255", "%", 0, 100, 1),
        "014C": PIDDefinition("014C", "Commanded Throttle Actuator", "A*100/255", "%", 0, 100, 1),
        "014D": PIDDefinition("014D", "Time Run with MIL On", "256*A+B", "minutes", 0, 65535, 2),
        "014E": PIDDefinition("014E", "Time Since Trouble Codes Cleared", "256*A+B", "minutes", 0, 65535, 2),
        
        # MAZDA PROPRIETARY PIDS (22xx range)
        "220101": PIDDefinition("220101", "Mazda Engine Load", "A*100/255", "%", 0, 100, 1, True),
        "220102": PIDDefinition("220102", "Mazda Injector Pulse Width", "(256*A+B)/1000", "ms", 0, 65.535, 2, True),
        "220103": PIDDefinition("220103", "Mazda Ignition Timing Advance", "(A/2)-64", "°", -64, 63.5, 1, True),
        "220104": PIDDefinition("220104", "Mazda Intake Air Temperature", "A-40", "°C", -40, 215, 1, True),
        "220105": PIDDefinition("220105", "Mazda Air Flow Rate", "(256*A+B)/100", "g/s", 0, 655.35, 2, True),
        "220106": PIDDefinition("220106", "Mazda Throttle Position Sensor", "A*100/255", "%", 0, 100, 1, True),
        "220107": PIDDefinition("220107", "Mazda Engine RPM", "(256*A+B)/4", "RPM", 0, 16383.75, 2, True),
        "220108": PIDDefinition("220108", "Mazda Vehicle Speed", "A", "km/h", 0, 255, 1, True),
        "220109": PIDDefinition("220109", "Mazda Boost Pressure", "A-100", "kPa", -100, 155, 1, True),
        "22010A": PIDDefinition("22010A", "Mazda Fuel Pressure", "A*10", "kPa", 0, 2550, 1, True),
        "22010B": PIDDefinition("22010B", "Mazda Camshaft Position", "A-128", "°", -128, 127, 1, True),
        "22010C": PIDDefinition("22010C", "Mazda Knock Sensor", "A", "count", 0, 255, 1, True),
        "22010D": PIDDefinition("22010D", "Mazda Fuel Trim Learn Value", "(A-128)*100/128", "%", -100, 99.2, 1, True),
        "22010E": PIDDefinition("22010E", "Mazda Wastegate Duty Cycle", "A*100/255", "%", 0, 100, 1, True),
        "22010F": PIDDefinition("22010F", "Mazda VVT Advance Angle", "A-128", "°", -128, 127, 1, True),
        
        # MAZDA ENHANCED DIAGNOSTIC PIDS
        "220201": PIDDefinition("220201", "Mazda Turbo Boost Solenoid Duty", "A*100/255", "%", 0, 100, 1, True),
        "220202": PIDDefinition("220202", "Mazda Variable Tumble Solenoid Status", "Bit encoded", "N/A", 0, 0, 1, True),
        "220203": PIDDefinition("220203", "Mazda Purge Solenoid Duty", "A*100/255", "%", 0, 100, 1, True),
        "220204": PIDDefinition("220204", "Mazda EGR Solenoid Duty", "A*100/255", "%", 0, 100, 1, True),
        "220205": PIDDefinition("220205", "Mazda A/C Compressor Status", "Bit encoded", "N/A", 0, 0, 1, True),
        "220206": PIDDefinition("220206", "Mazda Cooling Fan Status", "Bit encoded", "N/A", 0, 0, 1, True),
        "220207": PIDDefinition("220207", "Mazda Brake Switch Status", "Bit encoded", "N/A", 0, 0, 1, True),
        "220208": PIDDefinition("220208", "Mazda Clutch Switch Status", "Bit encoded", "N/A", 0, 0, 1, True),
        "220209": PIDDefinition("220209", "Mazda Power Steering Pressure Switch", "Bit encoded", "N/A", 0, 0, 1, True),
        
        # TRANSMISSION PIDS
        "220301": PIDDefinition("220301", "Mazda Transmission Fluid Temp", "A-40", "°C", -40, 215, 1, True),
        "220302": PIDDefinition("220302", "Mazda TCM Selected Gear", "A", "gear", 0, 255, 1, True),
        "220303": PIDDefinition("220303", "Mazda TCM Shift Solenoid A", "Bit encoded", "N/A", 0, 0, 1, True),
        "220304": PIDDefinition("220304", "Mazda TCM Shift Solenoid B", "Bit encoded", "N/A", 0, 0, 1, True),
        "220305": PIDDefinition("220305", "Mazda TCM Torque Converter Clutch", "Bit encoded", "N/A", 0, 0, 1, True),
        "220306": PIDDefinition("220306", "Mazda TCM Line Pressure Solenoid", "A*100/255", "%", 0, 100, 1, True),
        
        # ABS/STABILITY CONTROL PIDS
        "220401": PIDDefinition("220401", "Mazda ABS Wheel Speed FL", "A", "km/h", 0, 255, 1, True),
        "220402": PIDDefinition("220402", "Mazda ABS Wheel Speed FR", "A", "km/h", 0, 255, 1, True),
        "220403": PIDDefinition("220403", "Mazda ABS Wheel Speed RL", "A", "km/h", 0, 255, 1, True),
        "220404": PIDDefinition("220404", "Mazda ABS Wheel Speed RR", "A", "km/h", 0, 255, 1, True),
        "220405": PIDDefinition("220405", "Mazda Steering Angle Sensor", "(256*A+B)-32768", "°", -32768, 32767, 2, True),
        "220406": PIDDefinition("220406", "Mazda Lateral Acceleration", "A-128", "g", -1.28, 1.27, 1, True),
        "220407": PIDDefinition("220407", "Mazda Yaw Rate Sensor", "A-128", "°/sec", -128, 127, 1, True),
    }
    
    # COMPLETE DTC DATABASE
    DIAGNOSTIC_TROUBLE_CODES = {
        # P-CODES (POWERTRAIN)
        "P0001": DTCDefinition("P0001", "Fuel Volume Regulator Control Circuit/Open", "MEDIUM",
            ["Fuel pump control module failure", "Wiring harness issue", "PCM failure"],
            ["Check fuel pump control module power and ground", "Inspect wiring harness for damage", "Test fuel pump operation"]),
        
        "P0011": DTCDefinition("P0011", "Camshaft Position - Timing Over-Advanced", "HIGH",
            ["VVT solenoid stuck open", "Oil pressure issues", "Timing chain stretched", "VVT actuator failure"],
            ["Check engine oil level and quality", "Test VVT solenoid operation", "Inspect timing chain", "Check oil pressure"]),
        
        "P0012": DTCDefinition("P0012", "Camshaft Position - Timing Over-Retarded", "HIGH",
            ["VVT solenoid stuck closed", "Low oil pressure", "Timing chain issues", "PCM calibration"],
            ["Test VVT solenoid", "Verify oil pressure", "Inspect timing components", "Check for PCM updates"]),
        
        "P0031": DTCDefinition("P0031", "HO2S Heater Control Circuit Low", "MEDIUM",
            ["O2 sensor heater circuit short to ground", "Wiring harness damage", "PCM failure"],
            ["Check O2 sensor heater resistance", "Inspect wiring for shorts", "Test PCM output"]),
        
        "P0032": DTCDefinition("P0032", "HO2S Heater Control Circuit High", "MEDIUM",
            ["O2 sensor heater circuit short to power", "Wiring harness issue", "PCM failure"],
            ["Check O2 sensor heater circuit voltage", "Inspect wiring for shorts", "Test PCM output"]),
        
        "P0037": DTCDefinition("P0037", "HO2S Heater Control Circuit Low (Bank 1 Sensor 2)", "MEDIUM",
            ["Downstream O2 sensor heater circuit issue", "Wiring damage", "PCM failure"],
            ["Check downstream O2 sensor heater", "Inspect wiring harness", "Test PCM circuits"]),
        
        "P0101": DTCDefinition("P0101", "Mass Air Flow Circuit Range/Performance", "HIGH",
            ["MAF sensor contamination", "Intake air leaks", "MAF sensor failure", "PCM issue"],
            ["Clean MAF sensor", "Check for intake leaks", "Test MAF sensor output", "Inspect air filter"]),
        
        "P0102": DTCDefinition("P0102", "Mass Air Flow Circuit Low Input", "HIGH",
            ["MAF sensor circuit short to ground", "Wiring harness issue", "MAF sensor failure"],
            ["Check MAF sensor wiring", "Test MAF sensor output voltage", "Inspect connectors"]),
        
        "P0103": DTCDefinition("P0103", "Mass Air Flow Circuit High Input", "HIGH",
            ["MAF sensor circuit short to power", "Wiring harness issue", "MAF sensor failure"],
            ["Check MAF sensor wiring", "Test MAF sensor output voltage", "Inspect connectors"]),
        
        "P0113": DTCDefinition("P0113", "Intake Air Temperature Circuit High Input", "MEDIUM",
            ["IAT sensor circuit open", "IAT sensor failure", "Wiring harness issue"],
            ["Test IAT sensor resistance", "Check wiring continuity", "Inspect connectors"]),
        
        "P0116": DTCDefinition("P0116", "Engine Coolant Temperature Circuit Range/Performance", "MEDIUM",
            ["ECT sensor out of range", "Cooling system issues", "PCM calibration"],
            ["Test ECT sensor resistance", "Check cooling system operation", "Verify PCM calibration"]),
        
        "P0117": DTCDefinition("P0117", "Engine Coolant Temperature Circuit Low Input", "MEDIUM",
            ["ECT sensor circuit short to ground", "ECT sensor failure", "Wiring issue"],
            ["Test ECT sensor resistance", "Check wiring for shorts", "Inspect connectors"]),
        
        "P0118": DTCDefinition("P0118", "Engine Coolant Temperature Circuit High Input", "MEDIUM",
            ["ECT sensor circuit open", "ECT sensor failure", "Wiring issue"],
            ["Test ECT sensor resistance", "Check wiring continuity", "Inspect connectors"]),
        
        "P0121": DTCDefinition("P0121", "Throttle/Pedal Position Sensor Circuit Range/Performance", "HIGH",
            ["Throttle position sensor failure", "Wiring harness issue", "PCM calibration"],
            ["Test throttle position sensor", "Check wiring harness", "Perform throttle relearn"]),
        
        "P0122": DTCDefinition("P0122", "Throttle/Pedal Position Sensor Circuit Low Input", "HIGH",
            ["TPS circuit short to ground", "TPS sensor failure", "Wiring issue"],
            ["Test TPS voltage output", "Check wiring for shorts", "Inspect connectors"]),
        
        "P0123": DTCDefinition("P0123", "Throttle/Pedal Position Sensor Circuit High Input", "HIGH",
            ["TPS circuit open or short to power", "TPS sensor failure", "Wiring issue"],
            ["Test TPS voltage output", "Check wiring continuity", "Inspect connectors"]),
        
        "P0128": DTCDefinition("P0128", "Coolant Thermostat Rationality", "MEDIUM",
            ["Thermostat stuck open", "ECT sensor inaccuracy", "PCM calibration"],
            ["Test thermostat operation", "Verify ECT sensor accuracy", "Check cooling system"]),
        
        "P0131": DTCDefinition("P0131", "O2 Sensor Circuit Low Voltage (Bank 1 Sensor 1)", "HIGH",
            ["O2 sensor circuit short to ground", "O2 sensor failure", "Wiring issue", "Fuel system problem"],
            ["Test O2 sensor voltage", "Check wiring for shorts", "Inspect fuel pressure", "Check for exhaust leaks"]),
        
        "P0132": DTCDefinition("P0132", "O2 Sensor Circuit High Voltage (Bank 1 Sensor 1)", "HIGH",
            ["O2 sensor circuit short to power", "O2 sensor failure", "Wiring issue", "Rich condition"],
            ["Test O2 sensor voltage", "Check wiring for shorts", "Check fuel pressure", "Inspect injectors"]),
        
        "P0133": DTCDefinition("P0133", "O2 Sensor Circuit Slow Response (Bank 1 Sensor 1)", "HIGH",
            ["O2 sensor aging", "Exhaust leaks", "Fuel system issues", "PCM calibration"],
            ["Test O2 sensor response time", "Check for exhaust leaks", "Verify fuel pressure", "Check air intake"]),
        
        "P0134": DTCDefinition("P0134", "O2 Sensor Circuit No Activity Detected (Bank 1 Sensor 1)", "HIGH",
            ["O2 sensor heater failure", "O2 sensor circuit open", "O2 sensor failure"],
            ["Check O2 sensor heater operation", "Test O2 sensor circuit", "Replace O2 sensor if needed"]),
        
        "P0137": DTCDefinition("P0137", "O2 Sensor Circuit Low Voltage (Bank 1 Sensor 2)", "MEDIUM",
            ["Downstream O2 sensor circuit issue", "Catalyst efficiency", "Wiring problem"],
            ["Test downstream O2 sensor", "Check catalyst condition", "Inspect wiring"]),
        
        "P0138": DTCDefinition("P0138", "O2 Sensor Circuit High Voltage (Bank 1 Sensor 2)", "MEDIUM",
            ["Downstream O2 sensor circuit issue", "Catalyst efficiency", "Wiring problem"],
            ["Test downstream O2 sensor", "Check catalyst condition", "Inspect wiring"]),
        
        "P0141": DTCDefinition("P0141", "O2 Sensor Heater Circuit Malfunction (Bank 1 Sensor 2)", "MEDIUM",
            ["Downstream O2 sensor heater failure", "Wiring issue", "PCM circuit"],
            ["Check O2 sensor heater resistance", "Test wiring continuity", "Inspect PCM circuits"]),
        
        "P0171": DTCDefinition("P0171", "System Too Lean (Bank 1)", "HIGH",
            ["Vacuum leaks", "Fuel delivery issues", "MAF sensor problem", "Exhaust leaks"],
            ["Smoke test intake system", "Check fuel pressure", "Test MAF sensor", "Inspect for exhaust leaks"]),
        
        "P0172": DTCDefinition("P0172", "System Too Rich (Bank 1)", "HIGH",
            ["Fuel pressure too high", "Injector leakage", "MAF sensor over-reading", "EVAP system issue"],
            ["Check fuel pressure", "Test injector operation", "Verify MAF sensor reading", "Inspect EVAP system"]),
        
        "P0221": DTCDefinition("P0221", "Throttle/Pedal Position Sensor Circuit Range/Performance", "HIGH",
            ["Throttle position sensor 2 failure", "Wiring harness issue", "PCM problem"],
            ["Test secondary TPS circuit", "Check wiring harness", "Inspect throttle body"]),
        
        "P0222": DTCDefinition("P0222", "Throttle/Pedal Position Sensor Circuit Low Input", "HIGH",
            ["TPS 2 circuit short to ground", "TPS sensor failure", "Wiring issue"],
            ["Test secondary TPS voltage", "Check wiring for shorts", "Inspect connectors"]),
        
        "P0223": DTCDefinition("P0223", "Throttle/Pedal Position Sensor Circuit High Input", "HIGH",
            ["TPS 2 circuit open or short to power", "TPS sensor failure", "Wiring issue"],
            ["Test secondary TPS voltage", "Check wiring continuity", "Inspect connectors"]),
        
        "P0234": DTCDefinition("P0234", "Turbocharger Overboost Condition", "HIGH",
            ["Wastegate stuck closed", "Boost control solenoid failure", "MAP sensor issue", "Tuning problem"],
            ["Check wastegate operation", "Test boost control solenoid", "Verify MAP sensor reading", "Check tune parameters"]),
        
        "P0236": DTCDefinition("P0236", "Turbocharger Boost Sensor Circuit Range/Performance", "HIGH",
            ["MAP sensor failure", "Wiring harness issue", "PCM calibration"],
            ["Test MAP sensor operation", "Check wiring harness", "Verify PCM calibration"]),
        
        "P0237": DTCDefinition("P0237", "Turbocharger Boost Sensor Circuit Low Input", "HIGH",
            ["MAP sensor circuit short to ground", "MAP sensor failure", "Wiring issue"],
            ["Test MAP sensor voltage", "Check wiring for shorts", "Inspect connectors"]),
        
        "P0238": DTCDefinition("P0238", "Turbocharger Boost Sensor Circuit High Input", "HIGH",
            ["MAP sensor circuit open or short to power", "MAP sensor failure", "Wiring issue"],
            ["Test MAP sensor voltage", "Check wiring continuity", "Inspect connectors"]),
        
        "P0299": DTCDefinition("P0299", "Turbocharger Underboost Condition", "MEDIUM",
            ["Wastegate stuck open", "Boost leaks", "Turbocharger failure", "Boost control issue"],
            ["Check wastegate operation", "Pressure test intake system", "Inspect turbocharger", "Test boost control"]),
        
        "P0300": DTCDefinition("P0300", "Random/Multiple Cylinder Misfire Detected", "HIGH",
            ["Ignition system issues", "Fuel system problems", "Compression issues", "Vacuum leaks"],
            ["Check spark plugs and coils", "Test fuel pressure", "Perform compression test", "Check for vacuum leaks"]),
        
        "P0301": DTCDefinition("P0301", "Cylinder 1 Misfire Detected", "HIGH",
            ["Cylinder 1 ignition coil", "Spark plug", "Fuel injector", "Compression issue"],
            ["Swap coil with another cylinder", "Inspect spark plug", "Test fuel injector", "Check compression"]),
        
        "P0302": DTCDefinition("P0302", "Cylinder 2 Misfire Detected", "HIGH",
            ["Cylinder 2 ignition coil", "Spark plug", "Fuel injector", "Compression issue"],
            ["Swap coil with another cylinder", "Inspect spark plug", "Test fuel injector", "Check compression"]),
        
        "P0303": DTCDefinition("P0303", "Cylinder 3 Misfire Detected", "HIGH",
            ["Cylinder 3 ignition coil", "Spark plug", "Fuel injector", "Compression issue"],
            ["Swap coil with another cylinder", "Inspect spark plug", "Test fuel injector", "Check compression"]),
        
        "P0304": DTCDefinition("P0304", "Cylinder 4 Misfire Detected", "HIGH",
            ["Cylinder 4 ignition coil", "Spark plug", "Fuel injector", "Compression issue"],
            ["Swap coil with another cylinder", "Inspect spark plug", "Test fuel injector", "Check compression"]),
        
        "P0327": DTCDefinition("P0327", "Knock Sensor Circuit Low Input", "HIGH",
            ["Knock sensor circuit short to ground", "Knock sensor failure", "Wiring issue"],
            ["Test knock sensor resistance", "Check wiring for shorts", "Inspect sensor mounting"]),
        
        "P0328": DTCDefinition("P0328", "Knock Sensor Circuit High Input", "HIGH",
            ["Knock sensor circuit open", "Knock sensor failure", "Wiring issue"],
            ["Test knock sensor resistance", "Check wiring continuity", "Inspect sensor mounting"]),
        
        "P0335": DTCDefinition("P0335", "Crankshaft Position Sensor Circuit Malfunction", "HIGH",
            ["CKP sensor failure", "Wiring harness issue", "Sensor gap incorrect", "PCM problem"],
            ["Test CKP sensor signal", "Check wiring harness", "Verify sensor gap", "Inspect tone ring"]),
        
        "P0336": DTCDefinition("P0336", "Crankshaft Position Sensor Circuit Range/Performance", "HIGH",
            ["CKP sensor signal erratic", "Wiring harness issue", "Sensor contamination"],
            ["Test CKP sensor signal pattern", "Check wiring connections", "Clean sensor area"]),
        
        "P0340": DTCDefinition("P0340", "Camshaft Position Sensor Circuit Malfunction", "HIGH",
            ["CMP sensor failure", "Wiring harness issue", "Sensor gap incorrect"],
            ["Test CMP sensor signal", "Check wiring harness", "Verify sensor gap"]),
        
        "P0341": DTCDefinition("P0341", "Camshaft Position Sensor Circuit Range/Performance", "HIGH",
            ["CMP sensor signal erratic", "Timing chain issues", "Sensor contamination"],
            ["Test CMP sensor signal pattern", "Check timing chain", "Clean sensor area"]),
        
        "P0351": DTCDefinition("P0351", "Ignition Coil A Primary/Secondary Circuit", "HIGH",
            ["Cylinder 1 ignition coil failure", "Wiring harness issue", "PCM driver circuit"],
            ["Test ignition coil primary circuit", "Check wiring harness", "Test PCM driver"]),
        
        "P0352": DTCDefinition("P0352", "Ignition Coil B Primary/Secondary Circuit", "HIGH",
            ["Cylinder 2 ignition coil failure", "Wiring harness issue", "PCM driver circuit"],
            ["Test ignition coil primary circuit", "Check wiring harness", "Test PCM driver"]),
        
        "P0353": DTCDefinition("P0353", "Ignition Coil C Primary/Secondary Circuit", "HIGH",
            ["Cylinder 3 ignition coil failure", "Wiring harness issue", "PCM driver circuit"],
            ["Test ignition coil primary circuit", "Check wiring harness", "Test PCM driver"]),
        
        "P0354": DTCDefinition("P0354", "Ignition Coil D Primary/Secondary Circuit", "HIGH",
            ["Cylinder 4 ignition coil failure", "Wiring harness issue", "PCM driver circuit"],
            ["Test ignition coil primary circuit", "Check wiring harness", "Test PCM driver"]),
        
        "P0420": DTCDefinition("P0420", "Catalyst System Efficiency Below Threshold", "MEDIUM",
            ["Catalytic converter failure", "Exhaust leaks", "O2 sensor issues", "Engine misfires"],
            ["Test catalyst efficiency", "Check for exhaust leaks", "Verify O2 sensor operation", "Check for misfires"]),
        
        "P0442": DTCDefinition("P0442", "Evaporative Emission Control System Leak Detected (Small Leak)", "MEDIUM",
            ["Loose gas cap", "EVAP system hose leaks", "Purge valve issue", "Vent valve problem"],
            ["Check gas cap seal", "Smoke test EVAP system", "Test purge valve operation", "Check vent valve"]),
        
        "P0443": DTCDefinition("P0443", "Evaporative Emission Control System Purge Control Valve Circuit", "MEDIUM",
            ["Purge valve circuit issue", "Wiring harness problem", "PCM driver circuit"],
            ["Test purge valve operation", "Check wiring continuity", "Test PCM driver circuit"]),
        
        "P0455": DTCDefinition("P0455", "Evaporative Emission Control System Leak Detected (Gross Leak)", "MEDIUM",
            ["Gas cap missing or damaged", "Large EVAP system leak", "Fuel filler neck issue"],
            ["Check gas cap", "Smoke test EVAP system", "Inspect fuel filler neck", "Check EVAP hoses"]),
        
        "P0500": DTCDefinition("P0500", "Vehicle Speed Sensor Circuit Malfunction", "MEDIUM",
            ["Vehicle speed sensor failure", "Wiring harness issue", "PCM calibration"],
            ["Test VSS signal", "Check wiring harness", "Verify PCM calibration"]),
        
        "P0501": DTCDefinition("P0501", "Vehicle Speed Sensor Circuit Range/Performance", "MEDIUM",
            ["Vehicle speed sensor erratic signal", "Wiring harness issue", "Sensor contamination"],
            ["Test VSS signal pattern", "Check wiring connections", "Clean sensor area"]),
        
        "P0562": DTCDefinition("P0562", "System Voltage Low", "MEDIUM",
            ["Charging system issue", "Battery problem", "Alternator failure", "Wiring harness issue"],
            ["Test charging system voltage", "Check battery condition", "Test alternator output", "Inspect wiring"]),
        
        "P0563": DTCDefinition("P0563", "System Voltage High", "HIGH",
            ["Voltage regulator failure", "Alternator overcharging", "Wiring harness issue"],
            ["Test charging system voltage", "Check voltage regulator", "Test alternator output", "Inspect wiring"]),
        
        "P0601": DTCDefinition("P0601", "Internal Control Module Memory Check Sum Error", "HIGH",
            ["PCM internal memory failure", "PCM programming issue", "Power interruption during programming"],
            ["Check PCM power and ground", "Attempt PCM reprogramming", "Replace PCM if necessary"]),
        
        "P0602": DTCDefinition("P0602", "Control Module Programming Error", "HIGH",
            ["PCM programming corruption", "Incorrect calibration file", "Power loss during programming"],
            ["Re-flash PCM with correct calibration", "Verify programming equipment", "Check battery voltage during programming"]),
        
        "P0606": DTCDefinition("P0606", "PCM Processor Fault", "HIGH",
            ["PCM internal processor failure", "PCM internal circuit issue"],
            ["Check PCM power and ground circuits", "Replace PCM if necessary"]),
        
        "P0610": DTCDefinition("P0610", "Control Module Vehicle Options Error", "MEDIUM",
            ["PCM configuration incorrect", "VIN mismatch", "Programming error"],
            ["Verify PCM configuration", "Check VIN programming", "Re-program PCM with correct options"]),
        
        "P062F": DTCDefinition("P062F", "Internal Control Module EEPROM Error", "HIGH",
            ["PCM internal memory corruption", "Power interruption issue"],
            ["Attempt PCM reprogramming", "Replace PCM if memory cannot be written"]),
        
        "P0630": DTCDefinition("P0630", "VIN Not Programmed or Mismatch", "MEDIUM",
            ["PCM replacement without VIN programming", "Incorrect VIN programmed"],
            ["Program correct VIN to PCM", "Verify VIN matches vehicle"]),
        
        "P0641": DTCDefinition("P0641", "Sensor Reference Voltage Circuit/Open", "HIGH",
            ["5V reference circuit open", "Multiple sensor circuit issue", "PCM internal problem"],
            ["Check 5V reference circuit", "Test sensors using reference voltage", "Inspect PCM circuits"]),
        
        "P0651": DTCDefinition("P0651", "Sensor Reference Voltage Circuit/Open", "HIGH",
            ["5V reference circuit open", "Multiple sensor circuit issue", "PCM internal problem"],
            ["Check 5V reference circuit", "Test sensors using reference voltage", "Inspect PCM circuits"]),
        
        "P0685": DTCDefinition("P0685", "ECM/PCM Power Relay Control Circuit/Open", "HIGH",
            ["Main relay circuit issue", "Wiring harness problem", "PCM driver circuit failure"],
            ["Test main relay operation", "Check relay control circuit", "Test PCM driver"]),
        
        "P2100": DTCDefinition("P2100", "Throttle Actuator Control Motor Circuit/Open", "HIGH",
            ["Throttle body motor circuit open", "Throttle body failure", "Wiring harness issue"],
            ["Test throttle body motor", "Check wiring continuity", "Inspect throttle body connector"]),
        
        "P2101": DTCDefinition("P2101", "Throttle Actuator Control Motor Circuit Range/Performance", "HIGH",
            ["Throttle body motor circuit issue", "Throttle body mechanical problem", "PCM calibration"],
            ["Test throttle body operation", "Check for mechanical binding", "Perform throttle relearn"]),
        
        "P2111": DTCDefinition("P2111", "Throttle Actuator Control System - Stuck Open", "HIGH",
            ["Throttle body stuck open", "Throttle body motor failure", "Return spring issue"],
            ["Inspect throttle plate movement", "Test throttle body motor", "Check for mechanical binding"]),
        
        "P2112": DTCDefinition("P2112", "Throttle Actuator Control System - Stuck Closed", "HIGH",
            ["Throttle body stuck closed", "Throttle body motor failure", "Mechanical binding"],
            ["Inspect throttle plate movement", "Test throttle body motor", "Check for mechanical binding"]),
        
        "P2119": DTCDefinition("P2119", "Throttle Actuator Control Throttle Body Range/Performance", "HIGH",
            ["Throttle body mechanical issue", "Throttle position sensor problem", "PCM calibration"],
            ["Test throttle body operation", "Verify TPS signals", "Perform throttle relearn"]),
        
        "P2122": DTCDefinition("P2122", "Throttle/Pedal Position Sensor/Switch D Circuit Low Input", "HIGH",
            ["Accelerator pedal sensor circuit low", "Wiring harness issue", "Pedal sensor failure"],
            ["Test accelerator pedal sensor", "Check wiring for shorts", "Inspect connectors"]),
        
        "P2123": DTCDefinition("P2123", "Throttle/Pedal Position Sensor/Switch D Circuit High Input", "HIGH",
            ["Accelerator pedal sensor circuit high", "Wiring harness issue", "Pedal sensor failure"],
            ["Test accelerator pedal sensor", "Check wiring continuity", "Inspect connectors"]),
        
        "P2127": DTCDefinition("P2127", "Throttle/Pedal Position Sensor/Switch E Circuit Low Input", "HIGH",
            ["Accelerator pedal sensor 2 circuit low", "Wiring harness issue", "Pedal sensor failure"],
            ["Test secondary accelerator pedal sensor", "Check wiring for shorts", "Inspect connectors"]),
        
        "P2128": DTCDefinition("P2128", "Throttle/Pedal Position Sensor/Switch E Circuit High Input", "HIGH",
            ["Accelerator pedal sensor 2 circuit high", "Wiring harness issue", "Pedal sensor failure"],
            ["Test secondary accelerator pedal sensor", "Check wiring continuity", "Inspect connectors"]),
        
        "P2135": DTCDefinition("P2135", "Throttle/Pedal Position Sensor/Switch A/B Voltage Correlation", "HIGH",
            ["Throttle position sensor correlation error", "TPS sensor failure", "Wiring harness issue"],
            ["Test both TPS sensor signals", "Check wiring harness", "Verify sensor correlation"]),
        
        "P2138": DTCDefinition("P2138", "Throttle/Pedal Position Sensor/Switch D/E Voltage Correlation", "HIGH",
            ["Accelerator pedal sensor correlation error", "Pedal sensor failure", "Wiring harness issue"],
            ["Test both accelerator pedal sensor signals", "Check wiring harness", "Verify sensor correlation"]),
        
        "P2181": DTCDefinition("P2181", "Cooling System Performance", "MEDIUM",
            ["Cooling system restriction", "Thermostat issue", "Water pump problem", "Radiator blockage"],
            ["Test cooling system flow", "Check thermostat operation", "Inspect water pump", "Check radiator"]),
        
        # MAZDA-SPECIFIC DTCS
        "P2502": DTCDefinition("P2502", "Generator Lamp Control Circuit Low", "MEDIUM", 
            ["Generator warning lamp circuit issue", "Instrument cluster problem", "Wiring harness issue"],
            ["Check generator warning lamp circuit", "Test instrument cluster", "Inspect wiring"], True),
        
        "P2503": DTCDefinition("P2503", "Generator Lamp Control Circuit High", "MEDIUM",
            ["Generator warning lamp circuit issue", "Instrument cluster problem", "Wiring harness issue"],
            ["Check generator warning lamp circuit", "Test instrument cluster", "Inspect wiring"], True),
        
        # U-CODES (NETWORK COMMUNICATION)
        "U0100": DTCDefinition("U0100", "Lost Communication with ECM/PCM", "HIGH",
            ["CAN bus communication failure", "PCM power issue", "Wiring harness problem"],
            ["Check CAN bus communication", "Verify PCM power and ground", "Inspect wiring harness"]),
        
        "U0101": DTCDefinition("U0101", "Lost Communication with TCM", "HIGH",
            ["CAN bus communication failure", "TCM power issue", "Wiring harness problem"],
            ["Check CAN bus communication", "Verify TCM power and ground", "Inspect wiring harness"]),
        
        "U0121": DTCDefinition("U0121", "Lost Communication with ABS Control Module", "MEDIUM",
            ["CAN bus communication failure", "ABS module power issue", "Wiring harness problem"],
            ["Check CAN bus communication", "Verify ABS module power and ground", "Inspect wiring harness"]),
        
        "U0140": DTCDefinition("U0140", "Lost Communication with Body Control Module", "MEDIUM",
            ["CAN bus communication failure", "BCM power issue", "Wiring harness problem"],
            ["Check CAN bus communication", "Verify BCM power and ground", "Inspect wiring harness"]),
        
        "U0401": DTCDefinition("U0401", "Invalid Data Received from ECM/PCM", "HIGH",
            ["CAN bus communication corruption", "PCM internal issue", "Wiring harness problem"],
            ["Check CAN bus signals", "Test PCM operation", "Inspect wiring harness"]),
        
        "U0415": DTCDefinition("U0415", "Invalid Data Received from ABS Control Module", "MEDIUM",
            ["CAN bus communication corruption", "ABS module internal issue", "Wiring harness problem"],
            ["Check CAN bus signals", "Test ABS module operation", "Inspect wiring harness"]),
        
        # C-CODES (CHASSIS)
        "C0031": DTCDefinition("C0031", "Left Front Wheel Speed Sensor Circuit", "MEDIUM",
            ["Left front wheel speed sensor failure", "Wiring harness issue", "Sensor contamination"],
            ["Test wheel speed sensor signal", "Check wiring continuity", "Clean sensor area"]),
        
        "C0032": DTCDefinition("C0032", "Left Front Wheel Speed Sensor Circuit Range/Performance", "MEDIUM",
            ["Left front wheel speed sensor erratic signal", "Tone ring damage", "Sensor gap incorrect"],
            ["Test wheel speed sensor signal pattern", "Inspect tone ring", "Verify sensor gap"]),
        
        "C0035": DTCDefinition("C0035", "Right Front Wheel Speed Sensor Circuit", "MEDIUM",
            ["Right front wheel speed sensor failure", "Wiring harness issue", "Sensor contamination"],
            ["Test wheel speed sensor signal", "Check wiring continuity", "Clean sensor area"]),
        
        "C0036": DTCDefinition("C0036", "Right Front Wheel Speed Sensor Circuit Range/Performance", "MEDIUM",
            ["Right front wheel speed sensor erratic signal", "Tone ring damage", "Sensor gap incorrect"],
            ["Test wheel speed sensor signal pattern", "Inspect tone ring", "Verify sensor gap"]),
        
        "C0039": DTCDefinition("C0039", "Left Rear Wheel Speed Sensor Circuit", "MEDIUM",
            ["Left rear wheel speed sensor failure", "Wiring harness issue", "Sensor contamination"],
            ["Test wheel speed sensor signal", "Check wiring continuity", "Clean sensor area"]),
        
        "C0040": DTCDefinition("C0040", "Left Rear Wheel Speed Sensor Circuit Range/Performance", "MEDIUM",
            ["Left rear wheel speed sensor erratic signal", "Tone ring damage", "Sensor gap incorrect"],
            ["Test wheel speed sensor signal pattern", "Inspect tone ring", "Verify sensor gap"]),
        
        "C0043": DTCDefinition("C0043", "Right Rear Wheel Speed Sensor Circuit", "MEDIUM",
            ["Right rear wheel speed sensor failure", "Wiring harness issue", "Sensor contamination"],
            ["Test wheel speed sensor signal", "Check wiring continuity", "Clean sensor area"]),
        
        "C0044": DTCDefinition("C0044", "Right Rear Wheel Speed Sensor Circuit Range/Performance", "MEDIUM",
            ["Right rear wheel speed sensor erratic signal", "Tone ring damage", "Sensor gap incorrect"],
            ["Test wheel speed sensor signal pattern", "Inspect tone ring", "Verify sensor gap"]),
        
        "C0051": DTCDefinition("C0051", "Steering Angle Sensor Circuit", "MEDIUM",
            ["Steering angle sensor failure", "Wiring harness issue", "Sensor calibration needed"],
            ["Test steering angle sensor signal", "Check wiring continuity", "Perform steering angle sensor calibration"]),
        
        "C0052": DTCDefinition("C0052", "Steering Angle Sensor Circuit Range/Performance", "MEDIUM",
            ["Steering angle sensor erratic signal", "Sensor mechanical issue", "Clock spring problem"],
            ["Test steering angle sensor signal pattern", "Inspect clock spring", "Check sensor mounting"]),
        
        "C0061": DTCDefinition("C0061", "Lateral Acceleration Sensor Circuit", "MEDIUM",
            ["Lateral acceleration sensor failure", "Wiring harness issue", "Sensor calibration needed"],
            ["Test lateral acceleration sensor signal", "Check wiring continuity", "Perform sensor calibration"]),
        
        "C0062": DTCDefinition("C0062", "Lateral Acceleration Sensor Circuit Range/Performance", "MEDIUM",
            ["Lateral acceleration sensor erratic signal", "Sensor mounting issue", "Internal sensor failure"],
            ["Test lateral acceleration sensor signal pattern", "Check sensor mounting", "Verify calibration"]),
        
        "C0071": DTCDefinition("C0071", "Yaw Rate Sensor Circuit", "MEDIUM",
            ["Yaw rate sensor failure", "Wiring harness issue", "Sensor calibration needed"],
            ["Test yaw rate sensor signal", "Check wiring continuity", "Perform sensor calibration"]),
        
        "C0072": DTCDefinition("C0072", "Yaw Rate Sensor Circuit Range/Performance", "MEDIUM",
            ["Yaw rate sensor erratic signal", "Sensor mounting issue", "Internal sensor failure"],
            ["Test yaw rate sensor signal pattern", "Check sensor mounting", "Verify calibration"]),
        
        # B-CODES (BODY)
        "B1000": DTCDefinition("B1000", "ECU Failure", "HIGH",
            ["Airbag control module internal failure", "Module power issue", "Wiring harness problem"],
            ["Check airbag module power and ground", "Test module communication", "Replace module if necessary"]),
        
        "B1342": DTCDefinition("B1342", "ECU is Defective", "HIGH",
            ["Airbag control module internal failure", "Module internal circuit issue"],
            ["Check airbag module power and ground", "Replace module if necessary"]),
        
        "B1876": DTCDefinition("B1876", "Buckle Switch Circuit Short to Ground", "MEDIUM",
            ["Seat belt buckle switch circuit short", "Wiring harness issue", "Buckle switch failure"],
            ["Test seat belt buckle switch", "Check wiring for shorts", "Inspect connectors"]),
        
        "B1877": DTCDefinition("B1877", "Buckle Switch Circuit Open", "MEDIUM",
            ["Seat belt buckle switch circuit open", "Wiring harness issue", "Buckle switch failure"],
            ["Test seat belt buckle switch", "Check wiring continuity", "Inspect connectors"]),
        
        "B2296": DTCDefinition("B2296", "Occupant Classification System Fault", "MEDIUM",
            ["Occupant classification sensor failure", "Wiring harness issue", "Sensor calibration needed"],
            ["Test occupant classification system", "Check wiring continuity", "Perform system calibration"]),
        
        "B2477": DTCDefinition("B2477", "Module Configuration Failure", "MEDIUM",
            ["Module configuration error", "Module programming issue", "VIN mismatch"],
            ["Check module configuration", "Re-program module if necessary", "Verify VIN programming"]),
    }
    
    # DIAGNOSTIC SERVICE CODES
    DIAGNOSTIC_SERVICES = {
        "10": "Initiate Diagnostic Operation",
        "11": "ECU Reset",
        "14": "Clear Diagnostic Information",
        "19": "Read DTC Information",
        "22": "Read Data By Identifier",
        "23": "Read Memory By Address",
        "27": "Security Access",
        "28": "Communication Control",
        "2E": "Write Data By Identifier",
        "2F": "Input Output Control By Identifier",
        "31": "Routine Control",
        "34": "Request Download",
        "35": "Request Upload",
        "36": "Transfer Data",
        "37": "Request Transfer Exit",
        "3D": "Write Memory By Address",
        "3E": "Tester Present",
        "85": "Control DTC Setting",
    }
    
    # MAZDA-SPECIFIC DIAGNOSTIC IDENTIFIERS
    MAZDA_DATA_IDENTIFIERS = {
        "F101": "VIN Information",
        "F102": "Calibration ID",
        "F103": "Calibration Verification Numbers",
        "F104": "ECU Serial Number",
        "F105": "ECU Hardware Number",
        "F106": "ECU Software Number",
        "F107": "System Name",
        "F108": "Engine Type",
        "F109": "Manufacturer Name",
        "F10A": "Program Date",
        "F110": "ECU Security Access Seed",
        "F111": "ECU Security Access Key",
        "F112": "Security Access Level",
        "F113": "Security Access Attempts",
        "F114": "Security Access Timer",
        "F120": "DTC Status Information",
        "F121": "DTC Severity Information",
        "F122": "DTC Snapshot Data",
        "F123": "DTC Extended Data",
        "F124": "DTC Environmental Data",
        "F125": "DTC Freeze Frame Data",
        "F130": "Readiness Monitor Status",
        "F131": "Readiness Monitor Results",
        "F132": "Readiness Monitor Conditions",
        "F140": "OBD Requirements",
        "F141": "OBD Monitor Conditions",
        "F142": "OBD Monitor Results",
        "F143": "OBD Monitor Ratios",
        "F144": "OBD Monitor Thresholds",
        "F150": "Vehicle Information",
        "F151": "Vehicle Options",
        "F152": "Vehicle Configuration",
        "F153": "Vehicle Identification",
        "F160": "ECU Internal Data",
        "F161": "ECU Memory Data",
        "F162": "ECU Status Information",
        "F163": "ECU Diagnostic Information",
        "F164": "ECU Programming Information",
        "F170": "Network Configuration",
        "F171": "Network Node Information",
        "F172": "Network Communication Data",
        "F173": "Network Diagnostic Data",
        "F180": "Sensor Data",
        "F181": "Actuator Data",
        "F182": "System Status Data",
        "F183": "Control Module Data",
        "F184": "Adaptation Data",
        "F185": "Learning Data",
        "F186": "Calibration Data",
        "F187": "Programming Data",
        "F188": "Security Data",
        "F189": "Diagnostic Data",
        "F190": "Vehicle Data",
        "F191": "Engine Data",
        "F192": "Transmission Data",
        "F193": "Chassis Data",
        "F194": "Body Data",
        "F195": "Network Data",
        "F196": "System Data",
        "F197": "Component Data",
        "F198": "Subsystem Data",
        "F199": "Module Data",
    }

    def get_pid_definition(self, pid: str) -> PIDDefinition:
        """Get complete PID definition"""
        return self.STANDARD_PIDS.get(pid.upper())
    
    def get_dtc_definition(self, dtc: str) -> DTCDefinition:
        """Get complete DTC definition with diagnostic steps"""
        return self.DIAGNOSTIC_TROUBLE_CODES.get(dtc.upper())
    
    def get_all_pids(self) -> Dict[str, PIDDefinition]:
        """Get all available PIDs"""
        return self.STANDARD_PIDS
    
    def get_all_dtcs(self) -> Dict[str, DTCDefinition]:
        """Get all available DTCs"""
        return self.DIAGNOSTIC_TROUBLE_CODES
    
    def get_mazda_specific_pids(self) -> Dict[str, PIDDefinition]:
        """Get only Mazda-specific PIDs"""
        return {pid: definition for pid, definition in self.STANDARD_PIDS.items() 
                if definition.mazda_specific}
    
    def get_diagnostic_service(self, service_id: str) -> str:
        """Get diagnostic service description"""
        return self.DIAGNOSTIC_SERVICES.get(service_id.upper(), "Unknown Service")
    
    def get_data_identifier(self, data_id: str) -> str:
        """Get Mazda data identifier description"""
        return self.MAZDA_DATA_IDENTIFIERS.get(data_id.upper(), "Unknown Data Identifier")

# USAGE EXAMPLES
def main():
    """DEMONSTRATE COMPLETE DIAGNOSTIC DATABASE"""
    db = Mazdaspeed3DiagnosticDatabase()
    
    print("MAZDASPEED 3 COMPLETE DIAGNOSTIC DATABASE")
    print("=" * 70)
    
    # DEMONSTRATE PID ACCESS
    print("\n1. STANDARD PIDS AVAILABLE")
    print("-" * 40)
    all_pids = db.get_all_pids()
    print(f"Total PIDs: {len(all_pids)}")
    
    # Show some important PIDs
    important_pids = ["010C", "010D", "0104", "0105", "0111", "220109"]
    for pid in important_pids:
        definition = db.get_pid_definition(pid)
        if definition:
            print(f"{pid}: {definition.description} ({definition.units})")
    
    # DEMONSTRATE DTC ACCESS
    print("\n2. COMMON DTCS WITH DIAGNOSTIC STEPS")
    print("-" * 40)
    common_dtcs = ["P0300", "P0171", "P0420", "P0234", "P0011"]
    for dtc in common_dtcs:
        definition = db.get_dtc_definition(dtc)
        if definition:
            print(f"\n{dtc}: {definition.description}")
            print(f"Severity: {definition.severity}")
            print(f"Common Causes: {', '.join(definition.common_causes[:2])}")
            print(f"Diagnostic Steps: {len(definition.diagnostic_steps)} steps available")
    
    # DEMONSTRATE MAZDA-SPECIFIC FEATURES
    print("\n3. MAZDA-SPECIFIC DIAGNOSTIC FEATURES")
    print("-" * 40)
    mazda_pids = db.get_mazda_specific_pids()
    print(f"Mazda-specific PIDs: {len(mazda_pids)}")
    
    # Show some Mazda-specific PIDs
    for pid, definition in list(mazda_pids.items())[:5]:
        print(f"{pid}: {definition.description}")
    
    # DEMONSTRATE DIAGNOSTIC SERVICES
    print("\n4. DIAGNOSTIC SERVICES")
    print("-" * 40)
    important_services = ["27", "19", "22", "2E", "31"]
    for service in important_services:
        description = db.get_diagnostic_service(service)
        print(f"Service 0x{service}: {description}")
    
    print("\n" + "=" * 70)
    print("DATABASE READY FOR SOFTWARE INTEGRATION")
    print("=" * 70)

if __name__ == "__main__":
    main()