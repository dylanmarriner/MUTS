#!/usr/bin/env python3
"""
Map Definitions Module - Complete definition of all tuning maps for Mazdaspeed 3 2011
Reverse engineered from factory calibration data and VersaTuner map structures
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from ..utils.logger import VersaLogger

@dataclass
class MapDefinition:
    """Definition of a single tuning map"""
    name: str
    address: int
    size: int
    type: str  # '2D_16x16', '2D_8x8', '1D', 'Single'
    description: str
    units: str
    conversion_factor: float
    min_value: float
    max_value: float
    x_axis: Optional[List[float]] = None
    y_axis: Optional[List[float]] = None
    category: str = "Unknown"

class MapDefinitionManager:
    """
    Manages all tuning map definitions for Mazdaspeed 3 2011
    Contains complete reverse engineered map definitions from factory ROMs
    """
    
    def __init__(self):
        self.logger = VersaLogger(__name__)
        self.map_definitions = self._load_map_definitions()
        self.categories = self._organize_categories()
    
    def _load_map_definitions(self) -> Dict[str, MapDefinition]:
        """Load complete map definitions for Mazdaspeed 3 2011"""
        definitions = {}
        
        # Ignition Timing Maps
        definitions.update(self._get_ignition_maps())
        # Fuel Maps
        definitions.update(self._get_fuel_maps())
        # Boost Control Maps
        definitions.update(self._get_boost_maps())
        # VVT Maps
        definitions.update(self._get_vvt_maps())
        # Torque Management Maps
        definitions.update(self._get_torque_maps())
        # Limiters and Protections
        definitions.update(self._get_limiter_maps())
        # Corrections and Adaptations
        definitions.update(self._get_correction_maps())
        
        return definitions
    
    def _get_ignition_maps(self) -> Dict[str, MapDefinition]:
        """Ignition timing map definitions"""
        rpm_axis_16 = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000]
        load_axis_16 = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        
        return {
            'ignition_primary': MapDefinition(
                name='Primary Ignition Timing',
                address=0x012000,
                size=0x0400,
                type='2D_16x16',
                description='Main ignition advance map based on RPM and load',
                units='degrees',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=25.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='Ignition'
            ),
            'ignition_high_octane': MapDefinition(
                name='High Octane Ignition',
                address=0x012400,
                size=0x0400,
                type='2D_16x16',
                description='High octane fuel timing map (more aggressive)',
                units='degrees',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=25.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='Ignition'
            ),
            'ignition_low_octane': MapDefinition(
                name='Low Octane Ignition',
                address=0x012800,
                size=0x0400,
                type='2D_16x16',
                description='Low octane fuel timing map (less aggressive)',
                units='degrees',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=20.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='Ignition'
            ),
            'ignition_iat_correction': MapDefinition(
                name='IAT Ignition Correction',
                address=0x012E00,
                size=0x0100,
                type='1D',
                description='Ignition correction based on intake air temperature',
                units='degrees',
                conversion_factor=0.1,
                min_value=-5.0,
                max_value=2.0,
                x_axis=[-40, -20, 0, 20, 40, 60, 80, 100],  # °C
                category='Ignition Corrections'
            ),
            'ignition_ect_correction': MapDefinition(
                name='ECT Ignition Correction',
                address=0x012F00,
                size=0x0100,
                type='1D',
                description='Ignition correction based on engine coolant temperature',
                units='degrees',
                conversion_factor=0.1,
                min_value=-5.0,
                max_value=2.0,
                x_axis=[-40, -20, 0, 20, 40, 60, 80, 100, 120],  # °C
                category='Ignition Corrections'
            )
        }
    
    def _get_fuel_maps(self) -> Dict[str, MapDefinition]:
        """Fuel mapping definitions"""
        rpm_axis_16 = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000]
        load_axis_16 = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        
        return {
            'fuel_primary': MapDefinition(
                name='Primary Fuel Map',
                address=0x013000,
                size=0x0400,
                type='2D_16x16',
                description='Main fuel map (lambda values)',
                units='lambda',
                conversion_factor=0.001,
                min_value=0.7,
                max_value=1.3,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='Fuel'
            ),
            'fuel_wot_enrichment': MapDefinition(
                name='WOT Fuel Enrichment',
                address=0x013400,
                size=0x0200,
                type='2D_8x8',
                description='Wide open throttle fuel enrichment',
                units='lambda',
                conversion_factor=0.001,
                min_value=0.7,
                max_value=1.0,
                x_axis=[2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000],
                y_axis=[0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
                category='Fuel'
            ),
            'fuel_cold_start': MapDefinition(
                name='Cold Start Enrichment',
                address=0x013600,
                size=0x0200,
                type='2D_8x8',
                description='Cold start fuel enrichment based on ECT',
                units='%',
                conversion_factor=0.1,
                min_value=100.0,
                max_value=200.0,
                x_axis=[-40, -20, 0, 20, 40, 60, 80],  # °C
                y_axis=[0, 10, 20, 30, 40, 50, 60, 70],  # Seconds
                category='Fuel'
            ),
            'fuel_high_load': MapDefinition(
                name='High Load Fuel',
                address=0x013800,
                size=0x0100,
                type='1D',
                description='Fuel adjustment at high load conditions',
                units='lambda',
                conversion_factor=0.001,
                min_value=0.7,
                max_value=1.0,
                x_axis=[0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
                category='Fuel'
            )
        }
    
    def _get_boost_maps(self) -> Dict[str, MapDefinition]:
        """Boost control map definitions"""
        rpm_axis_16 = [1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000]
        load_axis_16 = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        
        return {
            'boost_target': MapDefinition(
                name='Boost Target Map',
                address=0x014000,
                size=0x0400,
                type='2D_16x16',
                description='Boost target pressure based on RPM and load',
                units='psi',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=25.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='Boost Control'
            ),
            'boost_wgdc_base': MapDefinition(
                name='Wastegate Duty Cycle Base',
                address=0x014400,
                size=0x0400,
                type='2D_16x16',
                description='Base wastegate duty cycle map',
                units='%',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=100.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='Boost Control'
            ),
            'boost_wgdc_compensation': MapDefinition(
                name='WGDC Compensation',
                address=0x014800,
                size=0x0200,
                type='2D_8x8',
                description='Wastegate duty cycle compensation factors',
                units='%',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=50.0,
                x_axis=[-40, -20, 0, 20, 40, 60, 80, 100],  # IAT °C
                y_axis=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4],  # Load
                category='Boost Control'
            ),
            'boost_overboost_limit': MapDefinition(
                name='Overboost Limit',
                address=0x014A00,
                size=0x0010,
                type='Single',
                description='Maximum allowed boost pressure',
                units='psi',
                conversion_factor=0.1,
                min_value=15.0,
                max_value=30.0,
                category='Boost Control'
            )
        }
    
    def _get_vvt_maps(self) -> Dict[str, MapDefinition]:
        """Variable Valve Timing map definitions"""
        rpm_axis_16 = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000]
        load_axis_16 = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        
        return {
            'vvt_intake_advance': MapDefinition(
                name='Intake VVT Advance',
                address=0x015000,
                size=0x0400,
                type='2D_16x16',
                description='Intake camshaft advance angle',
                units='degrees',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=25.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='VVT Control'
            ),
            'vvt_exhaust_retard': MapDefinition(
                name='Exhaust VVT Retard',
                address=0x015400,
                size=0x0400,
                type='2D_16x16',
                description='Exhaust camshaft retard angle',
                units='degrees',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=25.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='VVT Control'
            ),
            'vvt_transition_speed': MapDefinition(
                name='VVT Transition Speed',
                address=0x015800,
                size=0x0010,
                type='Single',
                description='RPM threshold for VVT activation',
                units='RPM',
                conversion_factor=1.0,
                min_value=1000,
                max_value=3000,
                category='VVT Control'
            )
        }
    
    def _get_torque_maps(self) -> Dict[str, MapDefinition]:
        """Torque management map definitions"""
        return {
            'torque_engine_max': MapDefinition(
                name='Engine Torque Limit',
                address=0x016000,
                size=0x0200,
                type='2D_8x8',
                description='Maximum allowed engine torque',
                units='Nm',
                conversion_factor=1.0,
                min_value=200.0,
                max_value=500.0,
                x_axis=[1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000],
                y_axis=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4],
                category='Torque Management'
            ),
            'torque_transmission_max': MapDefinition(
                name='Transmission Torque Limit',
                address=0x016200,
                size=0x0200,
                type='2D_8x8',
                description='Maximum torque allowed for transmission protection',
                units='Nm',
                conversion_factor=1.0,
                min_value=200.0,
                max_value=400.0,
                x_axis=[1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000],
                y_axis=[1, 2, 3, 4, 5, 6],  # Gears
                category='Torque Management'
            )
        }
    
    def _get_limiter_maps(self) -> Dict[str, MapDefinition]:
        """Engine and vehicle limiters"""
        return {
            'rev_limit_soft': MapDefinition(
                name='Soft Rev Limit',
                address=0x017000,
                size=0x0010,
                type='Single',
                description='Soft fuel cut rev limit',
                units='RPM',
                conversion_factor=1.0,
                min_value=5000,
                max_value=8000,
                category='Limiters'
            ),
            'rev_limit_hard': MapDefinition(
                name='Hard Rev Limit',
                address=0x017010,
                size=0x0010,
                type='Single',
                description='Hard ignition cut rev limit',
                units='RPM',
                conversion_factor=1.0,
                min_value=5500,
                max_value=8500,
                category='Limiters'
            ),
            'speed_limit': MapDefinition(
                name='Speed Limiter',
                address=0x017100,
                size=0x0010,
                type='Single',
                description='Vehicle speed limit',
                units='km/h',
                conversion_factor=1.0,
                min_value=180,
                max_value=300,
                category='Limiters'
            )
        }
    
    def _get_correction_maps(self) -> Dict[str, MapDefinition]:
        """Correction and adaptation maps"""
        return {
            'knock_correction_advance': MapDefinition(
                name='Knock Correction Advance',
                address=0x018000,
                size=0x0100,
                type='1D',
                description='Maximum knock correction advance',
                units='degrees',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=5.0,
                x_axis=[1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000],
                category='Corrections'
            ),
            'knock_correction_retard': MapDefinition(
                name='Knock Correction Retard',
                address=0x018100,
                size=0x0100,
                type='1D',
                description='Maximum knock correction retard',
                units='degrees',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=10.0,
                x_axis=[1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000],
                category='Corrections'
            )
        }
    
    def _organize_categories(self) -> Dict[str, List[str]]:
        """Organize maps by category for easy access"""
        categories = {}
        for map_name, map_def in self.map_definitions.items():
            if map_def.category not in categories:
                categories[map_def.category] = []
            categories[map_def.category].append(map_name)
        return categories
    
    def get_map(self, map_name: str) -> Optional[MapDefinition]:
        """Get map definition by name"""
        return self.map_definitions.get(map_name)
    
    def get_maps_by_category(self, category: str) -> List[MapDefinition]:
        """Get all maps in a specific category"""
        map_names = self.categories.get(category, [])
        return [self.map_definitions[name] for name in map_names]
    
    def get_all_categories(self) -> List[str]:
        """Get list of all map categories"""
        return list(self.categories.keys())
    
    def validate_map_value(self, map_name: str, value: float) -> bool:
        """Validate if a value is within map's allowed range"""
        map_def = self.get_map(map_name)
        if not map_def:
            return False
        return map_def.min_value <= value <= map_def.max_value
    
    def export_definitions(self, file_path: str):
        """Export map definitions to JSON file"""
        export_data = {}
        for name, definition in self.map_definitions.items():
            export_data[name] = {
                'address': definition.address,
                'size': definition.size,
                'type': definition.type,
                'description': definition.description,
                'units': definition.units,
                'conversion_factor': definition.conversion_factor,
                'min_value': definition.min_value,
                'max_value': definition.max_value,
                'category': definition.category
            }
            if definition.x_axis:
                export_data[name]['x_axis'] = definition.x_axis
            if definition.y_axis:
                export_data[name]['y_axis'] = definition.y_axis
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Map definitions exported to {file_path}")