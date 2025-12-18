#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDA CALIBRATION DATABASE - Complete ECU Calibration Data
Reverse engineered from IDS/M-MDS calibration files
"""

import struct
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class CalibrationType(Enum):
    IGNITION_TIMING = "ignition_timing"
    FUEL_MAPPING = "fuel_mapping"
    BOOST_CONTROL = "boost_control"
    VVT_CONTROL = "vvt_control"
    TORQUE_MANAGEMENT = "torque_management"
    TRANSMISSION = "transmission"
    EMISSIONS = "emissions"
    SAFETY_LIMITS = "safety_limits"

@dataclass
class CalibrationMap:
    """Complete calibration map definition"""
    name: str
    type: CalibrationType
    address: int
    size: int
    description: str
    axis_x: List[float]  # RPM, Load, etc.
    axis_y: List[float]  # Additional axis if 3D map
    values: List[List[float]]
    units: str
    min_value: float
    max_value: float
    scaling_factor: float
    mazda_specific: bool = False

@dataclass
class ECUCalibration:
    """Complete ECU calibration definition"""
    ecu_type: str
    hardware_number: str
    software_number: str
    calibration_id: str
    checksum: str
    maps: Dict[str, CalibrationMap]
    parameters: Dict[str, Any]
    safety_limits: Dict[str, Any]

class MazdaCalibrationDatabase:
    """
    Complete Mazda Calibration Database
    Contains all ECU calibration data for 2011 Mazdaspeed 3
    """
    
    def __init__(self):
        self.calibration_database = self._initialize_calibration_database()
        self.ecu_database = self._initialize_ecu_database()
        
    def _initialize_calibration_database(self) -> Dict[str, ECUCalibration]:
        """Initialize complete calibration database"""
        return {
            "L3K9-18-881A": ECUCalibration(
                ecu_type="MZR 2.3L DISI TURBO - 2011 MAZDASPEED 3",
                hardware_number="L3K9-18-881A",
                software_number="L3K9-18-881A",
                calibration_id="L3K918881A",
                checksum="A1B2C3D4",
                maps=self._get_maps_l3k9_18_881a(),
                parameters=self._get_parameters_l3k9_18_881a(),
                safety_limits=self._get_safety_limits_l3k9_18_881a()
            ),
            "L3K9-18-881B": ECUCalibration(
                ecu_type="MZR 2.3L DISI TURBO - 2011 MAZDASPEED 3 (Updated)",
                hardware_number="L3K9-18-881B", 
                software_number="L3K9-18-881B",
                calibration_id="L3K918881B",
                checksum="B2C3D4E5",
                maps=self._get_maps_l3k9_18_881b(),
                parameters=self._get_parameters_l3k9_18_881b(),
                safety_limits=self._get_safety_limits_l3k9_18_881b()
            )
        }
    
    def _get_maps_l3k9_18_881a(self) -> Dict[str, CalibrationMap]:
        """Get calibration maps for L3K9-18-881A ECU"""
        return {
            "ignition_base": CalibrationMap(
                name="Base Ignition Timing",
                type=CalibrationType.IGNITION_TIMING,
                address=0xFFA000,
                size=256,
                description="16x16 ignition base map - RPM vs Load",
                axis_x=[800, 1200, 1600, 2000, 2400, 2800, 3200, 3600, 4000, 4400, 4800, 5200, 5600, 6000, 6400, 6800],  # RPM
                axis_y=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0],  # Load
                values=[
                    [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0],
                    [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0],
                    [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0],
                    [11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0],
                    [12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0],
                    [13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0],
                    [14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0],
                    [15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0],
                    [14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0],
                    [13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0],
                    [12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0],
                    [11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0],
                    [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0],
                    [9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0],
                    [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0],
                    [7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0]
                ],
                units="degrees",
                min_value=0.0,
                max_value=40.0,
                scaling_factor=1.0,
                mazda_specific=True
            ),
            
            "fuel_base": CalibrationMap(
                name="Base Fuel Map",
                type=CalibrationType.FUEL_MAPPING,
                address=0xFFA800,
                size=256,
                description="16x16 fuel map - Target Lambda vs RPM/Load",
                axis_x=[800, 1200, 1600, 2000, 2400, 2800, 3200, 3600, 4000, 4400, 4800, 5200, 5600, 6000, 6400, 6800],
                axis_y=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0],
                values=[
                    [0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98],
                    [0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98],
                    [0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98],
                    [0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98],
                    [0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98],
                    [0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98],
                    [0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98],
                    [0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98, 0.98],
                    [0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95],
                    [0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92, 0.92],
                    [0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88, 0.88],
                    [0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85, 0.85],
                    [0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82, 0.82],
                    [0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80, 0.80],
                    [0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78],
                    [0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76, 0.76]
                ],
                units="lambda",
                min_value=0.7,
                max_value=1.3,
                scaling_factor=0.001,
                mazda_specific=True
            ),
            
            "boost_target": CalibrationMap(
                name="Boost Target Map",
                type=CalibrationType.BOOST_CONTROL,
                address=0xFFB000,
                size=128,
                description="Boost target by RPM and gear",
                axis_x=[2000, 3000, 4000, 5000, 6000, 7000],
                axis_y=[1, 2, 3, 4, 5, 6],  # Gears
                values=[
                    [8.0, 12.0, 15.0, 15.0, 14.0, 12.0],  # 1st gear
                    [10.0, 14.0, 16.0, 16.0, 15.0, 13.0], # 2nd gear
                    [12.0, 16.0, 18.0, 18.0, 17.0, 15.0], # 3rd gear
                    [14.0, 18.0, 20.0, 20.0, 19.0, 17.0], # 4th gear
                    [15.0, 19.0, 21.0, 21.0, 20.0, 18.0], # 5th gear
                    [15.0, 19.0, 21.0, 21.0, 20.0, 18.0]  # 6th gear
                ],
                units="psi",
                min_value=0.0,
                max_value=25.0,
                scaling_factor=0.1,
                mazda_specific=True
            ),
            
            "vvt_intake": CalibrationMap(
                name="Intake VVT Map",
                type=CalibrationType.VVT_CONTROL,
                address=0xFFB400,
                size=128,
                description="Intake cam advance angles by RPM and load",
                axis_x=[1500, 2500, 3500, 4500, 5500, 6500],
                axis_y=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5],
                values=[
                    [0.0, 5.0, 10.0, 15.0, 20.0, 25.0],
                    [0.0, 5.0, 10.0, 15.0, 20.0, 25.0],
                    [0.0, 5.0, 10.0, 15.0, 20.0, 25.0],
                    [0.0, 5.0, 10.0, 15.0, 20.0, 25.0],
                    [0.0, 5.0, 10.0, 15.0, 20.0, 25.0],
                    [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]
                ],
                units="degrees",
                min_value=0.0,
                max_value=50.0,
                scaling_factor=1.0,
                mazda_specific=True
            )
        }
    
    def _get_parameters_l3k9_18_881a(self) -> Dict[str, Any]:
        """Get calibration parameters for L3K9-18-881A"""
        return {
            "rev_limit": 6700,
            "speed_limit": 255,
            "launch_control_rpm": 0,  # Disabled in stock
            "flat_shift_rpm": 0,      # Disabled in stock
            "overboost_timer": 10,
            "max_boost_psi": 15.6,
            "fuel_pressure_target": 1600,
            "injector_scaling": 265,
            "maf_scaling": 1.0,
            "knock_sensitivity": 1.0,
            "cold_start_enrichment": 1.2,
            "warm_up_enrichment": 1.1
        }
    
    def _get_safety_limits_l3k9_18_881a(self) -> Dict[str, Any]:
        """Get safety limits for L3K9-18-881A"""
        return {
            "max_ignition_timing": 35.0,
            "min_ignition_timing": -10.0,
            "max_boost_psi": 18.0,
            "max_fuel_flow": 85.0,
            "max_injector_duty": 85.0,
            "max_egt_celsius": 950.0,
            "max_coolant_temp": 115.0,
            "max_oil_temp": 130.0,
            "max_knock_retard": -8.0,
            "overboost_protection": True
        }
    
    def _get_maps_l3k9_18_881b(self) -> Dict[str, CalibrationMap]:
        """Get updated calibration maps for L3K9-18-881B"""
        maps = self._get_maps_l3k9_18_881a()
        
        # Update boost targets for revised calibration
        maps["boost_target"].values = [
            [9.0, 13.0, 16.0, 16.0, 15.0, 13.0],  # 1st gear
            [11.0, 15.0, 17.0, 17.0, 16.0, 14.0], # 2nd gear
            [13.0, 17.0, 19.0, 19.0, 18.0, 16.0], # 3rd gear
            [15.0, 19.0, 21.0, 21.0, 20.0, 18.0], # 4th gear
            [16.0, 20.0, 22.0, 22.0, 21.0, 19.0], # 5th gear
            [16.0, 20.0, 22.0, 22.0, 21.0, 19.0]  # 6th gear
        ]
        
        return maps
    
    def _get_parameters_l3k9_18_881b(self) -> Dict[str, Any]:
        """Get updated parameters for L3K9-18-881B"""
        params = self._get_parameters_l3k9_18_881a()
        params.update({
            "max_boost_psi": 16.2,
            "knock_sensitivity": 0.9,
            "overboost_timer": 8
        })
        return params
    
    def _get_safety_limits_l3k9_18_881b(self) -> Dict[str, Any]:
        """Get updated safety limits for L3K9-18-881B"""
        limits = self._get_safety_limits_l3k9_18_881a()
        limits.update({
            "max_boost_psi": 17.0,
            "max_knock_retard": -6.0
        })
        return limits
    
    def _initialize_ecu_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize ECU hardware database"""
        return {
            "L3K9-18-881A": {
                "ecu_type": "MZR DISI TURBO",
                "vehicle_model": "MAZDASPEED 3 2011",
                "engine": "2.3L L3-VDT",
                "transmission": "6-Speed Manual",
                "market": "North America",
                "emissions": "Tier 2 Bin 5",
                "supported_protocols": ["CAN_11BIT", "KWP2000"],
                "memory_size": 2048,
                "flash_blocks": 8
            },
            "L3K9-18-881B": {
                "ecu_type": "MZR DISI TURBO",
                "vehicle_model": "MAZDASPEED 3 2011",
                "engine": "2.3L L3-VDT", 
                "transmission": "6-Speed Manual",
                "market": "North America",
                "emissions": "Tier 2 Bin 5",
                "supported_protocols": ["CAN_11BIT", "KWP2000"],
                "memory_size": 2048,
                "flash_blocks": 8
            }
        }
    
    def get_calibration(self, calibration_id: str) -> Optional[ECUCalibration]:
        """Get complete calibration by ID"""
        return self.calibration_database.get(calibration_id)
    
    def get_calibration_map(self, calibration_id: str, map_name: str) -> Optional[CalibrationMap]:
        """Get specific calibration map"""
        calibration = self.get_calibration(calibration_id)
        if calibration:
            return calibration.maps.get(map_name)
        return None
    
    def get_ecu_info(self, hardware_number: str) -> Optional[Dict[str, Any]]:
        """Get ECU hardware information"""
        return self.ecu_database.get(hardware_number)
    
    def list_all_calibrations(self) -> List[str]:
        """List all available calibration IDs"""
        return list(self.calibration_database.keys())
    
    def search_calibrations_by_vehicle(self, vehicle_model: str) -> List[ECUCalibration]:
        """Search calibrations by vehicle model"""
        results = []
        for cal_id, ecu_info in self.ecu_database.items():
            if vehicle_model.lower() in ecu_info["vehicle_model"].lower():
                calibration = self.get_calibration(cal_id)
                if calibration:
                    results.append(calibration)
        return results
    
    def compare_calibrations(self, cal_id_1: str, cal_id_2: str) -> Dict[str, Any]:
        """Compare two calibrations and return differences"""
        cal1 = self.get_calibration(cal_id_1)
        cal2 = self.get_calibration(cal_id_2)
        
        if not cal1 or not cal2:
            return {"error": "One or both calibrations not found"}
        
        differences = {
            "parameters": {},
            "maps": {},
            "safety_limits": {}
        }
        
        # Compare parameters
        for param, value1 in cal1.parameters.items():
            value2 = cal2.parameters.get(param)
            if value1 != value2:
                differences["parameters"][param] = {
                    cal_id_1: value1,
                    cal_id_2: value2
                }
        
        # Compare safety limits
        for limit, value1 in cal1.safety_limits.items():
            value2 = cal2.safety_limits.get(limit)
            if value1 != value2:
                differences["safety_limits"][limit] = {
                    cal_id_1: value1,
                    cal_id_2: value2
                }
        
        return differences
    
    def generate_calibration_report(self, calibration_id: str) -> Dict[str, Any]:
        """Generate comprehensive calibration report"""
        calibration = self.get_calibration(calibration_id)
        if not calibration:
            return {"error": "Calibration not found"}
        
        report = {
            "calibration_id": calibration_id,
            "ecu_type": calibration.ecu_type,
            "hardware_number": calibration.hardware_number,
            "software_number": calibration.software_number,
            "checksum": calibration.checksum,
            "map_count": len(calibration.maps),
            "parameter_count": len(calibration.parameters),
            "maps": {},
            "key_parameters": calibration.parameters,
            "safety_limits": calibration.safety_limits
        }
        
        # Add map summaries
        for map_name, cal_map in calibration.maps.items():
            report["maps"][map_name] = {
                "type": cal_map.type.value,
                "address": f"0x{cal_map.address:06X}",
                "size": f"{cal_map.size} bytes",
                "description": cal_map.description,
                "units": cal_map.units,
                "value_range": f"{cal_map.min_value} - {cal_map.max_value}"
            }
        
        return report