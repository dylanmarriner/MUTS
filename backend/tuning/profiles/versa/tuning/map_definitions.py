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
                max_value=25.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='Ignition'
            ),
            'ignition_cranking': MapDefinition(
                name='Cranking Ignition',
                address=0x012C00,
                size=0x0010,
                type='1D',
                description='Ignition timing during engine cranking',
                units='degrees',
                conversion_factor=0.1,
                min_value=-5.0,
                max_value=15.0,
                x_axis=[-20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130],
                category='Ignition'
            )
        }
    
    def _get_fuel_maps(self) -> Dict[str, MapDefinition]:
        """Fuel map definitions"""
        rpm_axis_16 = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000]
        load_axis_16 = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        
        return {
            'fuel_primary': MapDefinition(
                name='Primary Fuel',
                address=0x014000,
                size=0x0400,
                type='2D_16x16',
                description='Primary fuel injection map',
                units='ms',
                conversion_factor=0.001,
                min_value=0.0,
                max_value=30.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='Fuel'
            ),
            'fuel_high_load': MapDefinition(
                name='High Load Fuel',
                address=0x014400,
                size=0x0400,
                type='2D_16x16',
                description='High load fuel enrichment map',
                units='ms',
                conversion_factor=0.001,
                min_value=0.0,
                max_value=30.0,
                x_axis=rpm_axis_16,
                y_axis=load_axis_16,
                category='Fuel'
            ),
            'fuel_cranking': MapDefinition(
                name='Cranking Fuel',
                address=0x014800,
                size=0x0010,
                type='1D',
                description='Fuel injection during engine cranking',
                units='ms',
                conversion_factor=0.001,
                min_value=0.0,
                max_value=50.0,
                x_axis=[-20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130],
                category='Fuel'
            )
        }
    
    def _get_boost_maps(self) -> Dict[str, MapDefinition]:
        """Boost control map definitions"""
        rpm_axis_8 = [2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500]
        load_axis_8 = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]
        
        return {
            'boost_target': MapDefinition(
                name='Target Boost',
                address=0x016000,
                size=0x0100,
                type='2D_8x8',
                description='Target boost pressure map',
                units='psi',
                conversion_factor=0.01,
                min_value=0.0,
                max_value=25.0,
                x_axis=rpm_axis_8,
                y_axis=load_axis_8,
                category='Boost'
            ),
            'boost_wg_duty': MapDefinition(
                name='Wastegate Duty',
                address=0x016100,
                size=0x0100,
                type='2D_8x8',
                description='Wastegate duty cycle map',
                units='%',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=100.0,
                x_axis=rpm_axis_8,
                y_axis=load_axis_8,
                category='Boost'
            )
        }
    
    def _get_vvt_maps(self) -> Dict[str, MapDefinition]:
        """Variable Valve Timing map definitions"""
        rpm_axis_8 = [1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500]
        load_axis_8 = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]
        
        return {
            'vvt_intake_advance': MapDefinition(
                name='Intake VVT Advance',
                address=0x018000,
                size=0x0100,
                type='2D_8x8',
                description='Intake camshaft advance angle',
                units='degrees',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=50.0,
                x_axis=rpm_axis_8,
                y_axis=load_axis_8,
                category='VVT'
            ),
            'vvt_exhaust_advance': MapDefinition(
                name='Exhaust VVT Advance',
                address=0x018100,
                size=0x0100,
                type='2D_8x8',
                description='Exhaust camshaft advance angle',
                units='degrees',
                conversion_factor=0.1,
                min_value=0.0,
                max_value=50.0,
                x_axis=rpm_axis_8,
                y_axis=load_axis_8,
                category='VVT'
            )
        }
    
    def _get_torque_maps(self) -> Dict[str, MapDefinition]:
        """Torque management map definitions"""
        rpm_axis_8 = [1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500]
        gear_axis_8 = [1, 2, 3, 4, 5, 6, 'N', 'R']
        
        return {
            'torque_limit': MapDefinition(
                name='Torque Limit',
                address=0x01A000,
                size=0x0100,
                type='2D_8x8',
                description='Maximum torque output limit',
                units='Nm',
                conversion_factor=1.0,
                min_value=0.0,
                max_value=400.0,
                x_axis=rpm_axis_8,
                y_axis=gear_axis_8,
                category='Torque'
            )
        }
    
    def _get_limiter_maps(self) -> Dict[str, MapDefinition]:
        """Limiter and protection map definitions"""
        return {
            'rev_limiter': MapDefinition(
                name='Rev Limiter',
                address=0x01C000,
                size=0x0004,
                type='Single',
                description='Engine RPM limiter',
                units='RPM',
                conversion_factor=1.0,
                min_value=5000.0,
                max_value=8000.0,
                category='Limiters'
            ),
            'speed_limiter': MapDefinition(
                name='Speed Limiter',
                address=0x01C004,
                size=0x0004,
                type='Single',
                description='Vehicle speed limiter',
                units='km/h',
                conversion_factor=1.0,
                min_value=200.0,
                max_value=300.0,
                category='Limiters'
            )
        }
    
    def _get_correction_maps(self) -> Dict[str, MapDefinition]:
        """Correction and adaptation map definitions"""
        return {
            'iat_correction': MapDefinition(
                name='Intake Air Temp Correction',
                address=0x01E000,
                size=0x0020,
                type='1D',
                description='Fuel correction based on intake air temperature',
                units='%',
                conversion_factor=0.1,
                min_value=-20.0,
                max_value=20.0,
                x_axis=[-40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110],
                category='Corrections'
            ),
            'ect_correction': MapDefinition(
                name='Engine Coolant Temp Correction',
                address=0x01E020,
                size=0x0020,
                type='1D',
                description='Fuel correction based on engine coolant temperature',
                units='%',
                conversion_factor=0.1,
                min_value=-20.0,
                max_value=20.0,
                x_axis=[-40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110],
                category='Corrections'
            )
        }
    
    def _organize_categories(self) -> Dict[str, List[str]]:
        """Organize maps by category"""
        categories = {}
        for map_name, map_def in self.map_definitions.items():
            category = map_def.category
            if category not in categories:
                categories[category] = []
            categories[category].append(map_name)
        return categories
    
    def get_map(self, name: str) -> Optional[MapDefinition]:
        """Get map definition by name"""
        return self.map_definitions.get(name)
    
    def get_maps_by_category(self, category: str) -> List[MapDefinition]:
        """Get all maps in a category"""
        return [self.map_definitions[name] for name in self.categories.get(category, [])]
    
    def get_all_maps(self) -> Dict[str, MapDefinition]:
        """Get all map definitions"""
        return self.map_definitions.copy()
    
    def export_definitions(self, filename: str) -> bool:
        """Export map definitions to JSON file"""
        try:
            export_data = {}
            for name, map_def in self.map_definitions.items():
                export_data[name] = {
                    'name': map_def.name,
                    'address': hex(map_def.address),
                    'size': hex(map_def.size),
                    'type': map_def.type,
                    'description': map_def.description,
                    'units': map_def.units,
                    'conversion_factor': map_def.conversion_factor,
                    'min_value': map_def.min_value,
                    'max_value': map_def.max_value,
                    'x_axis': map_def.x_axis,
                    'y_axis': map_def.y_axis,
                    'category': map_def.category
                }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Map definitions exported to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export definitions: {e}")
            return False
