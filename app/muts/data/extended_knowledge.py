#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3_EXTENDED_KNOWLEDGE_BASE.py
ADDITIONAL KNOWLEDGE AND REFERENCE DATA
"""

from typing import Dict, List, Any, Optional
import json

# Extended vehicle specifications
VEHICLE_SPECIFICATIONS = {
    'engine': {
        'type': 'MZR 2.3L DISI Turbo',
        'displacement': 2261,  # cc
        'compression_ratio': 9.5:1,
        'max_boost_stock': 15.5,  # psi
        'max_power_stock': 263,  # bhp at 5500 rpm
        'max_torque_stock': 280,  # lb-ft at 3000 rpm
        'redline': 6500,  # rpm
        'fuel_type': 'Premium Unleaded (91+ octane)',
        'oil_capacity': 4.8,  # quarts
        'cooling_capacity': 7.4,  # quarts
    },
    'transmission': {
        'type': '6-speed Manual',
        'gear_ratios': [3.818, 2.263, 1.545, 1.171, 0.957, 0.826],
        'final_drive': 4.105,
        'differential_type': 'Helical Limited Slip',
    },
    'dimensions': {
        'wheelbase': 2640,  # mm
        'length': 4580,  # mm
        'width': 1795,  # mm
        'height': 1470,  # mm
        'curb_weight': 1450,  # kg
        'fuel_tank_capacity': 55,  # liters
    },
    'suspension': {
        'front': 'MacPherson Strut',
        'rear': 'Multi-link',
        'front_spring_rate': 3.2,  # kg/mm
        'rear_spring_rate': 4.1,  # kg/mm
        'front_diameter': 320,  # mm
        'rear_diameter': 330,  # mm
    },
    'brakes': {
        'front': 'Ventilated Disc - 320mm',
        'rear': 'Solid Disc - 280mm',
        'calipers_front': '2-piston',
        'calipers_rear': '1-piston',
    }
}

# ECU pinout reference
ECU_PINOUT = {
    'power': {
        '1D': 'Battery (+12V)',
        '1E': 'Ignition Switch (+12V)',
        '2A': 'Ground',
        '2B': 'Ground',
    },
    'sensors': {
        '1A': 'MAF Sensor Signal',
        '1B': 'IAT Sensor Signal',
        '1C': 'MAP Sensor Signal',
        '1F': 'TPS Signal',
        '2C': 'O2 Sensor Front',
        '2D': 'O2 Sensor Rear',
        '2E': 'Coolant Temp Sensor',
        '2F': 'Knock Sensor',
    },
    'actuators': {
        '3A': 'Fuel Injector 1',
        '3B': 'Fuel Injector 2',
        '3C': 'Fuel Injector 3',
        '3D': 'Fuel Injector 4',
        '3E': 'Ignition Coil 1',
        '3F': 'Ignition Coil 2',
        '4A': 'Ignition Coil 3',
        '4B': 'Ignition Coil 4',
    },
    'communication': {
        '4C': 'CAN High',
        '4D': 'CAN Low',
        '4E': 'K-Line',
        '4F': 'L-Line',
    }
}

# Diagnostic trouble code database
DTC_DATABASE = {
    'P0000': {'description': 'No fault detected', 'severity': 'NONE'},
    'P0101': {'description': 'MAF sensor range/performance', 'severity': 'MEDIUM'},
    'P0102': {'description': 'MAF sensor circuit low', 'severity': 'HIGH'},
    'P0103': {'description': 'MAF sensor circuit high', 'severity': 'HIGH'},
    'P0111': {'description': 'IAT sensor range/performance', 'severity': 'MEDIUM'},
    'P0112': {'description': 'IAT sensor circuit low', 'severity': 'MEDIUM'},
    'P0113': {'description': 'IAT sensor circuit high', 'severity': 'MEDIUM'},
    'P0117': {'description': 'Coolant temp sensor low', 'severity': 'HIGH'},
    'P0118': {'description': 'Coolant temp sensor high', 'severity': 'HIGH'},
    'P0121': {'description': 'TPS range/performance', 'severity': 'MEDIUM'},
    'P0122': {'description': 'TPS circuit low', 'severity': 'MEDIUM'},
    'P0123': {'description': 'TPS circuit high', 'severity': 'MEDIUM'},
    'P0131': {'description': 'O2 sensor circuit low', 'severity': 'MEDIUM'},
    'P0132': {'description': 'O2 sensor circuit high', 'severity': 'MEDIUM'},
    'P0133': {'description': 'O2 sensor slow response', 'severity': 'LOW'},
    'P0171': {'description': 'System too lean', 'severity': 'HIGH'},
    'P0172': {'description': 'System too rich', 'severity': 'HIGH'},
    'P0300': {'description': 'Random/multiple cylinder misfire', 'severity': 'CRITICAL'},
    'P0301': {'description': 'Cylinder 1 misfire', 'severity': 'CRITICAL'},
    'P0302': {'description': 'Cylinder 2 misfire', 'severity': 'CRITICAL'},
    'P0303': {'description': 'Cylinder 3 misfire', 'severity': 'CRITICAL'},
    'P0304': {'description': 'Cylinder 4 misfire', 'severity': 'CRITICAL'},
    'P0325': {'description': 'Knock sensor circuit', 'severity': 'MEDIUM'},
    'P0335': {'description': 'Crankshaft position sensor', 'severity': 'CRITICAL'},
    'P0340': {'description': 'Camshaft position sensor', 'severity': 'CRITICAL'},
    'P0420': {'description': 'Catalyst efficiency below threshold', 'severity': 'MEDIUM'},
    'P0441': {'description': 'Evaporative system incorrect flow', 'severity': 'LOW'},
    'P0446': {'description': 'Vent control circuit', 'severity': 'LOW'},
    'P0455': {'description': 'Evaporative system leak detected', 'severity': 'LOW'},
    'P0500': {'description': 'Vehicle speed sensor', 'severity': 'MEDIUM'},
    'P0506': {'description': 'Idle speed too low', 'severity': 'MEDIUM'},
    'P0507': {'description': 'Idle speed too high', 'severity': 'MEDIUM'},
    'P0562': {'description': 'System voltage low', 'severity': 'HIGH'},
    'P0563': {'description': 'System voltage high', 'severity': 'HIGH'},
    'P0600': {'description': 'Serial communication link', 'severity': 'MEDIUM'},
    'P0601': {'description': 'ECU memory check sum error', 'severity': 'CRITICAL'},
    'P0603': {'description': 'ECU keep alive memory error', 'severity': 'HIGH'},
    'P0604': {'description': 'ECU RAM error', 'severity': 'HIGH'},
    'P0605': {'description': 'ECU ROM error', 'severity': 'CRITICAL'},
    'P0606': {'description': 'ECU processor fault', 'severity': 'CRITICAL'},
    'P0610': {'description': 'ECU vehicle options not programmed', 'severity': 'MEDIUM'},
    'P0661': {'description': 'Intake manifold tuning valve', 'severity': 'MEDIUM'},
    'P0662': {'description': 'Intake manifold tuning valve', 'severity': 'MEDIUM'},
    'P0700': {'description': 'Transmission control system', 'severity': 'HIGH'},
    'P2009': {'description': 'Intake manifold runner control', 'severity': 'MEDIUM'},
    'P2070': {'description': 'Intake manifold runner stuck open', 'severity': 'MEDIUM'},
    'P2071': {'description': 'Intake manifold runner stuck closed', 'severity': 'MEDIUM'},
    'P2227': {'description': 'Barometric pressure circuit', 'severity': 'LOW'},
    'P2228': {'description': 'Barometric pressure circuit low', 'severity': 'LOW'},
    'P2229': {'description': 'Barometric pressure circuit high', 'severity': 'LOW'},
    'P2503': {'description': 'Charging system voltage low', 'severity': 'HIGH'},
    'P2504': {'description': 'Charging system voltage high', 'severity': 'HIGH'},
    'U0001': {'description': 'CAN communication bus error', 'severity': 'HIGH'},
    'U0073': {'description': 'Control module communication bus off', 'severity': 'HIGH'},
    'U0100': {'description': 'Lost communication with ECM/PCM', 'severity': 'CRITICAL'},
    'U0121': {'description': 'Lost communication with ABS module', 'severity': 'MEDIUM'},
    'U0155': {'description': 'Lost communication with instrument cluster', 'severity': 'MEDIUM'},
}

# Performance modification database
MODIFICATION_DATABASE = {
    'intake': {
        'short_ram': {
            'power_gain': 5,  # bhp
            'torque_gain': 3,  # lb-ft
            'description': 'Short ram intake',
            'notes': 'Improved throttle response, louder induction noise'
        },
        'cold_air': {
            'power_gain': 8,
            'torque_gain': 5,
            'description': 'Cold air intake',
            'notes': 'Best power gains, requires relocation'
        }
    },
    'exhaust': {
        'cat_back': {
            'power_gain': 10,
            'torque_gain': 8,
            'description': 'Cat-back exhaust system',
            'notes': 'Improved sound, moderate power gain'
        },
        'turbo_back': {
            'power_gain': 20,
            'torque_gain': 15,
            'description': 'Turbo-back exhaust with high-flow cat',
            'notes': 'Significant power gain, louder exhaust'
        },
        'downpipe': {
            'power_gain': 25,
            'torque_gain': 20,
            'description': 'High-flow downpipe',
            'notes': 'Max power gain, may not be street legal'
        }
    },
    'intercooler': {
        'front_mount': {
            'power_gain': 15,
            'torque_gain': 10,
            'description': 'Front mount intercooler',
            'notes': 'Better cooling, reduced heat soak'
        },
        'top_mount': {
            'power_gain': 8,
            'torque_gain': 5,
            'description': 'Top mount intercooler',
            'notes': 'Easier installation, moderate gains'
        }
    },
    'fuel_system': {
        'high_flow_pump': {
            'power_gain': 0,
            'torque_gain': 0,
            'description': 'High flow fuel pump',
            'notes': 'Required for high boost applications'
        },
        'larger_injectors': {
            'power_gain': 0,
            'torque_gain': 0,
            'description': 'Larger fuel injectors',
            'notes': 'Required for high boost applications'
        }
    },
    'engine_internal': {
        'forged_pistons': {
            'power_gain': 0,
            'torque_gain': 0,
            'description': 'Forged pistons',
            'notes': 'Increased reliability, required for high boost'
        },
        'forged_rods': {
            'power_gain': 0,
            'torque_gain': 0,
            'description': 'Forged connecting rods',
            'notes': 'Increased reliability, required for high boost'
        }
    }
}

# Tuning reference data
TUNING_REFERENCE = {
    'fuel_targets': {
        'stoich': 14.7,  # AFR
        'light_boost': 13.5,
        'medium_boost': 12.5,
        'high_boost': 11.5,
        'race': 11.0
    },
    'timing_targets': {
        'stock': 15,  # degrees BTDC
        'mild': 18,
        'aggressive': 22,
        'race': 25
    },
    'boost_targets': {
        'stock': 15.5,  # psi
        'stage_1': 18.0,
        'stage_2': 22.0,
        'stage_3': 25.0,
        'race': 28.0
    },
    'rev_limits': {
        'stock': 6500,  # rpm
        'mild': 6800,
        'aggressive': 7200,
        'race': 7500
    }
}

# Maintenance intervals
MAINTENANCE_SCHEDULE = {
    'oil_change': 5000,  # miles
    'oil_filter': 10000,  # miles
    'spark_plugs': 30000,  # miles
    'air_filter': 15000,  # miles
    'fuel_filter': 30000,  # miles
    'coolant_flush': 40000,  # miles
    'brake_fluid': 20000,  # miles
    'transmission_fluid': 60000,  # miles
    'differential_fluid': 60000,  # miles
    'timing_chain': 100000,  # miles
}

# Utility functions
def get_vehicle_specifications() -> Dict:
    """Get complete vehicle specifications"""
    return VEHICLE_SPECIFICATIONS.copy()

def get_ecu_pinout() -> Dict:
    """Get ECU pinout reference"""
    return ECU_PINOUT.copy()

def get_dtc_info(code: str) -> Optional[Dict]:
    """Get DTC information"""
    return DTC_DATABASE.get(code.upper())

def get_modification_info(category: str, type: str) -> Optional[Dict]:
    """Get modification information"""
    return MODIFICATION_DATABASE.get(category, {}).get(type)

def get_tuning_reference() -> Dict:
    """Get tuning reference data"""
    return TUNING_REFERENCE.copy()

def get_maintenance_schedule() -> Dict:
    """Get maintenance schedule"""
    return MAINTENANCE_SCHEDULE.copy()

def calculate_power_with_mods(base_power: int, modifications: List[str]) -> int:
    """Calculate estimated power with modifications"""
    total_gain = 0
    
    for mod in modifications:
        for category, mods in MODIFICATION_DATABASE.items():
            if mod in mods:
                total_gain += mods[mod]['power_gain']
    
    return base_power + total_gain

def calculate_torque_with_mods(base_torque: int, modifications: List[str]) -> int:
    """Calculate estimated torque with modifications"""
    total_gain = 0
    
    for mod in modifications:
        for category, mods in MODIFICATION_DATABASE.items():
            if mod in mods:
                total_gain += mods[mod]['torque_gain']
    
    return base_torque + total_gain

# Export functions
def export_vehicle_specs(filename: str) -> bool:
    """Export vehicle specifications to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(VEHICLE_SPECIFICATIONS, f, indent=2)
        return True
    except:
        return False

def export_dtc_database(filename: str) -> bool:
    """Export DTC database to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(DTC_DATABASE, f, indent=2)
        return True
    except:
        return False

def export_modification_database(filename: str) -> bool:
    """Export modification database to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(MODIFICATION_DATABASE, f, indent=2)
        return True
    except:
        return False
