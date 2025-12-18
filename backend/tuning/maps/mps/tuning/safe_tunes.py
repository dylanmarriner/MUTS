#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAFE_PREMIUM_FUEL_TUNES.py
CONSERVATIVE, SAFE TUNES FOR 95, 98, 100+ OCTANE FUELS
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import json

@dataclass
class SafeFuelLimits:
    """CONSERVATIVE SAFETY LIMITS FOR DAILY DRIVER TUNES"""
    octane_95: Dict[str, float]
    octane_98: Dict[str, float] 
    octane_100_plus: Dict[str, float]

class SafePremiumFuelTuner:
    """
    SAFE, CONSERVATIVE TUNES FOR HIGH-OCTANE FUELS
    Priority on reliability and longevity over maximum power
    """
    
    def __init__(self):
        self.safe_limits = self._define_safe_limits()
        self.base_tunes = self._generate_safe_tunes()
        self.safety_monitoring = self._safety_monitoring_systems()
        
    def _define_safe_limits(self) -> SafeFuelLimits:
        """DEFINE CONSERVATIVE SAFETY LIMITS FOR EACH FUEL GRADE"""
        return SafeFuelLimits(
            octane_95={
                'max_boost_psi': 19.5,  # Conservative boost
                'max_timing_advance': 21.0,  # Moderate timing
                'min_afr_wot': 11.6,  # Richer for safety
                'max_knock_retard': -2.0,  # Sensitive knock detection
                'safe_egt_c': 880,
                'octane_safety_margin': 'Very High - 20%',
                'injector_duty_safe': 75,  # Well below max
                'turbo_safety_margin': '30% below max speed'
            },
            octane_98={
                'max_boost_psi': 21.0,
                'max_timing_advance': 22.5,
                'min_afr_wot': 11.5,
                'max_knock_retard': -1.5,
                'safe_egt_c': 900,
                'octane_safety_margin': 'High - 18%',
                'injector_duty_safe': 78,
                'turbo_safety_margin': '25% below max speed'
            },
            octane_100_plus={
                'max_boost_psi': 22.5,
                'max_timing_advance': 24.0,
                'min_afr_wot': 11.4,
                'max_knock_retard': -1.0,
                'safe_egt_c': 920,
                'octane_safety_margin': 'Moderate - 15%',
                'injector_duty_safe': 80,
                'turbo_safety_margin': '20% below max speed'
            }
        )
    
    def _generate_safe_tunes(self) -> Dict[str, Any]:
        """GENERATE SAFE TUNE TEMPLATES FOR EACH FUEL GRADE"""
        return {
            'octane_95': self._create_safe_95_octane_tune(),
            'octane_98': self._create_safe_98_octane_tune(),
            'octane_100_plus': self._create_safe_100_plus_tune()
        }
    
    def _create_safe_95_octane_tune(self) -> Dict[str, Any]:
        """SAFE, CONSERVATIVE TUNE FOR 95 OCTANE FUEL"""
        limits = self.safe_limits.octane_95
        
        return {
            'metadata': {
                'tune_type': 'SAFE_CONSERVATIVE',
                'fuel_grade': '95 RON',
                'target_power': '260-270 WHP',
                'target_torque': '300-310 WTQ',
                'description': 'Safe 95 octane tune - Maximum reliability focus',
                'safety_margin': '20% factory margin maintained',
                'recommended_use': 'Daily driving, long-term reliability'
            },
            'ignition_maps': {
                'base_timing': [
                    # RPM: 2000, 3000, 4000, 5000, 6000, 6500
                    [9, 11, 13, 15, 16, 15],    # 10% Load (Conservative)
                    [11, 13, 15, 17, 18, 17],   # 20% Load
                    [13, 15, 17, 19, 20, 19],   # 30% Load
                    [15, 17, 19, 21, 22, 21],   # 40% Load
                    [17, 19, 21, 23, 24, 23],   # 50% Load
                    [19, 21, 23, 25, 26, 25],   # 60% Load
                    [21, 23, 25, 27, 28, 27],   # 70% Load
                    [23, 25, 27, 29, 30, 29]    # 80%+ Load
                ],
                'advance_strategy': {
                    'max_advance': limits['max_timing_advance'],
                    'knock_response': 'Very Sensitive - 2.0° pull initial',
                    'recovery_rate': 0.2,  # Slow recovery for safety
                    'temperature_compensation': {
                        'coolant_derate_start': 100,  # Early derate
                        'intake_derate_start': 40,
                        'derate_rate': 0.1  # Aggressive derate
                    }
                }
            },
            'fuel_maps': {
                'target_afr': [
                    # RPM: 2000, 3000, 4000, 5000, 6000, 6500
                    [14.7, 14.7, 14.7, 14.5, 14.3, 14.1],  # Light load
                    [14.5, 14.5, 14.3, 14.1, 13.9, 13.7],  # Medium load
                    [13.5, 13.3, 13.1, 12.9, 12.7, 12.5],  # Heavy load
                    [12.5, 12.3, 12.1, 11.9, 11.7, 11.6]   # WOT (Rich for safety)
                ],
                'enrichment_strategy': {
                    'wot_target': limits['min_afr_wot'],
                    'cold_start_enrichment': 'Rich - +20%',
                    'warmup_enrichment': 'Moderate - +10%',
                    'acceleration_enrichment': 'Conservative - +5%'
                }
            },
            'boost_control': {
                'target_boost': [
                    # RPM: 2000, 3000, 4000, 5000, 6000, 6500
                    [8.0, 12.0, 15.0, 17.0, 18.0, 17.0],  # Conservative ramp
                    [10.0, 14.0, 17.0, 19.0, 19.5, 19.0],  # Moderate load
                    [12.0, 16.0, 18.5, 19.5, 19.5, 19.0]   # Heavy load
                ],
                'boost_limits': {
                    'max_boost': limits['max_boost_psi'],
                    'overboost_protection': 'Active - 1.0 psi limit',
                    'wastegate_response': 'Smooth - Progressive',
                    'spool_control': 'Conservative - Reduced stress'
                }
            },
            'safety_parameters': {
                'knock_control': {
                    'sensitivity': 'Very High',
                    'max_retard': limits['max_knock_retard'],
                    'recovery_rpm': 3000,  # Only recover at low RPM
                    'learning_rate': 0.1  # Slow adaptation
                },
                'temperature_limits': {
                    'coolant_max': 105,  # Early warning
                    'intake_max': 50,
                    'oil_max': 120,
                    'egt_max': limits['safe_egt_c']
                },
                'fuel_system': {
                    'injector_duty_max': limits['injector_duty_safe'],
                    'fuel_pressure_target': 'Stock + 10%',
                    'low_fuel_pressure_protection': 'Active'
                }
            }
        }
    
    def _create_safe_98_octane_tune(self) -> Dict[str, Any]:
        """SAFE TUNE FOR 98 OCTANE FUEL"""
        limits = self.safe_limits.octane_98
        
        return {
            'metadata': {
                'tune_type': 'SAFE_PERFORMANCE',
                'fuel_grade': '98 RON',
                'target_power': '275-285 WHP',
                'target_torque': '315-325 WTQ',
                'description': 'Safe 98 octane tune - Performance with reliability',
                'safety_margin': '18% factory margin maintained',
                'recommended_use': 'Performance driving, track days'
            },
            'ignition_maps': {
                'base_timing': [
                    [10, 12, 14, 16, 18, 17],
                    [12, 14, 16, 18, 20, 19],
                    [14, 16, 18, 20, 22, 21],
                    [16, 18, 20, 22, 24, 23],
                    [18, 20, 22, 24, 26, 25],
                    [20, 22, 24, 26, 27, 26],
                    [22, 24, 26, 27, 28, 27],
                    [24, 26, 27, 28, 29, 28]
                ],
                'advance_strategy': {
                    'max_advance': limits['max_timing_advance'],
                    'knock_response': 'Sensitive - 1.5° pull initial',
                    'recovery_rate': 0.3,
                    'temperature_compensation': {
                        'coolant_derate_start': 102,
                        'intake_derate_start': 42,
                        'derate_rate': 0.09
                    }
                }
            },
            'fuel_maps': {
                'target_afr': [
                    [14.7, 14.7, 14.7, 14.5, 14.3, 14.1],
                    [14.5, 14.5, 14.3, 14.1, 13.9, 13.7],
                    [13.3, 13.1, 12.9, 12.7, 12.5, 12.3],
                    [12.3, 12.1, 11.9, 11.7, 11.5, 11.5]
                ],
                'enrichment_strategy': {
                    'wot_target': limits['min_afr_wot'],
                    'cold_start_enrichment': 'Rich - +18%',
                    'warmup_enrichment': 'Moderate - +8%',
                    'acceleration_enrichment': 'Moderate - +7%'
                }
            },
            'boost_control': {
                'target_boost': [
                    [9.0, 13.0, 16.0, 19.0, 20.0, 19.0],
                    [11.0, 15.0, 18.0, 20.0, 21.0, 20.0],
                    [13.0, 17.0, 19.5, 21.0, 21.0, 20.0]
                ],
                'boost_limits': {
                    'max_boost': limits['max_boost_psi'],
                    'overboost_protection': 'Active - 1.5 psi limit',
                    'wastegate_response': 'Responsive - Controlled',
                    'spool_control': 'Balanced - Performance + Reliability'
                }
            },
            'safety_parameters': {
                'knock_control': {
                    'sensitivity': 'High',
                    'max_retard': limits['max_knock_retard'],
                    'recovery_rpm': 2800,
                    'learning_rate': 0.15
                },
                'temperature_limits': {
                    'coolant_max': 107,
                    'intake_max': 52,
                    'oil_max': 125,
                    'egt_max': limits['safe_egt_c']
                },
                'fuel_system': {
                    'injector_duty_max': limits['injector_duty_safe'],
                    'fuel_pressure_target': 'Stock + 15%',
                    'low_fuel_pressure_protection': 'Active'
                }
            }
        }
    
    def _create_safe_100_plus_tune(self) -> Dict[str, Any]:
        """SAFE TUNE FOR 100+ OCTANE FUEL"""
        limits = self.safe_limits.octane_100_plus
        
        return {
            'metadata': {
                'tune_type': 'SAFE_MAXIMUM',
                'fuel_grade': '100+ RON',
                'target_power': '285-295 WHP',
                'target_torque': '325-335 WTQ',
                'description': 'Safe 100+ octane tune - Maximum safe performance',
                'safety_margin': '15% factory margin maintained',
                'recommended_use': 'High performance, racing with reliability'
            },
            'ignition_maps': {
                'base_timing': [
                    [11, 13, 15, 17, 19, 18],
                    [13, 15, 17, 19, 21, 20],
                    [15, 17, 19, 21, 23, 22],
                    [17, 19, 21, 23, 25, 24],
                    [19, 21, 23, 25, 27, 26],
                    [21, 23, 25, 27, 28, 27],
                    [23, 25, 27, 28, 29, 28],
                    [25, 27, 28, 29, 30, 29]
                ],
                'advance_strategy': {
                    'max_advance': limits['max_timing_advance'],
                    'knock_response': 'Moderate - 1.0° pull initial',
                    'recovery_rate': 0.4,
                    'temperature_compensation': {
                        'coolant_derate_start': 105,
                        'intake_derate_start': 45,
                        'derate_rate': 0.08
                    }
                }
            },
            'fuel_maps': {
                'target_afr': [
                    [14.7, 14.7, 14.7, 14.5, 14.3, 14.1],
                    [14.5, 14.5, 14.3, 14.1, 13.9, 13.7],
                    [13.1, 12.9, 12.7, 12.5, 12.3, 12.1],
                    [12.1, 11.9, 11.7, 11.5, 11.4, 11.4]
                ],
                'enrichment_strategy': {
                    'wot_target': limits['min_afr_wot'],
                    'cold_start_enrichment': 'Rich - +15%',
                    'warmup_enrichment': 'Moderate - +5%',
                    'acceleration_enrichment': 'Moderate - +8%'
                }
            },
            'boost_control': {
                'target_boost': [
                    [10.0, 14.0, 17.5, 20.5, 22.0, 21.0],
                    [12.0, 16.0, 19.0, 21.5, 22.5, 21.5],
                    [14.0, 18.0, 20.5, 22.5, 22.5, 21.5]
                ],
                'boost_limits': {
                    'max_boost': limits['max_boost_psi'],
                    'overboost_protection': 'Active - 2.0 psi limit',
                    'wastegate_response': 'Quick - Responsive',
                    'spool_control': 'Aggressive - Within safety limits'
                }
            },
            'safety_parameters': {
                'knock_control': {
                    'sensitivity': 'Moderate',
                    'max_retard': limits['max_knock_retard'],
                    'recovery_rpm': 2500,
                    'learning_rate': 0.2
                },
                'temperature_limits': {
                    'coolant_max': 110,
                    'intake_max': 55,
                    'oil_max': 130,
                    'egt_max': limits['safe_egt_c']
                },
                'fuel_system': {
                    'injector_duty_max': limits['injector_duty_safe'],
                    'fuel_pressure_target': 'Stock + 20%',
                    'low_fuel_pressure_protection': 'Active'
                }
            }
        }
    
    def _safety_monitoring_systems(self) -> Dict[str, Any]:
        """DEFINE SAFETY MONITORING SYSTEMS"""
        return {
            'real_time_monitoring': {
                'knock_detection': 'Active with logging',
                'egt_monitoring': 'Active with warnings',
                'fuel_pressure_monitoring': 'Active',
                'boost_pressure_monitoring': 'Active'
            },
            'protection_systems': {
                'overboost_protection': 'Active - Immediate cut',
                'overheat_protection': 'Active - Progressive reduction',
                'low_fuel_pressure_protection': 'Active - Boost reduction',
                'misfire_detection': 'Active - Cylinder cut'
            },
            'data_logging': {
                'log_all_parameters': True,
                'log_safety_events': True,
                'log_performance_metrics': True,
                'export_format': 'CSV and JSON'
            }
        }
    
    def get_safe_tune(self, fuel_grade: str) -> Dict[str, Any]:
        """GET SAFE TUNE FOR SPECIFIED FUEL GRADE"""
        fuel_key = f"octane_{fuel_grade.replace('+', '_plus')}"
        
        if fuel_key in self.base_tunes:
            return self.base_tunes[fuel_key]
        else:
            raise ValueError(f"Unsupported fuel grade: {fuel_grade}")
    
    def validate_tune_safety(self, tune: Dict[str, Any], fuel_grade: str) -> List[str]:
        """VALIDATE TUNE AGAINST SAFETY LIMITS"""
        warnings = []
        
        # Get safety limits for fuel grade
        if fuel_grade == '95':
            limits = self.safe_limits.octane_95
        elif fuel_grade == '98':
            limits = self.safe_limits.octane_98
        elif fuel_grade in ['100', '100+']:
            limits = self.safe_limits.octane_100_plus
        else:
            warnings.append(f"Unknown fuel grade: {fuel_grade}")
            return warnings
        
        # Check boost limits
        max_boost = max(max(row) for row in tune['boost_control']['target_boost'])
        if max_boost > limits['max_boost_psi']:
            warnings.append(f"Boost too high: {max_boost} psi > {limits['max_boost_psi']} psi")
        
        # Check timing limits
        max_timing = max(max(row) for row in tune['ignition_maps']['base_timing'])
        if max_timing > limits['max_timing_advance']:
            warnings.append(f"Timing too advanced: {max_timing}° > {limits['max_timing_advance']}°")
        
        # Check AFR limits
        min_afr = min(min(row) for row in tune['fuel_maps']['target_afr'])
        if min_afr < limits['min_afr_wot']:
            warnings.append(f"AFR too lean: {min_afr} < {limits['min_afr_wot']}")
        
        return warnings
    
    def generate_tune_report(self, tune: Dict[str, Any]) -> str:
        """GENERATE DETAILED TUNE REPORT"""
        report = []
        report.append("=" * 60)
        report.append("SAFE TUNE REPORT")
        report.append("=" * 60)
        report.append(f"Tune Type: {tune['metadata']['tune_type']}")
        report.append(f"Fuel Grade: {tune['metadata']['fuel_grade']}")
        report.append(f"Target Power: {tune['metadata']['target_power']}")
        report.append(f"Target Torque: {tune['metadata']['target_torque']}")
        report.append(f"Description: {tune['metadata']['description']}")
        report.append(f"Safety Margin: {tune['metadata']['safety_margin']}")
        report.append("")
        
        report.append("IGNITION TIMING:")
        report.append(f"  Max Advance: {tune['ignition_maps']['advance_strategy']['max_advance']}°")
        report.append(f"  Knock Response: {tune['ignition_maps']['advance_strategy']['knock_response']}")
        report.append("")
        
        report.append("FUEL DELIVERY:")
        report.append(f"  WOT Target AFR: {tune['fuel_maps']['enrichment_strategy']['wot_target']}")
        report.append(f"  Cold Start Enrichment: {tune['fuel_maps']['enrichment_strategy']['cold_start_enrichment']}")
        report.append("")
        
        report.append("BOOST CONTROL:")
        max_boost = max(max(row) for row in tune['boost_control']['target_boost'])
        report.append(f"  Maximum Boost: {max_boost} psi")
        report.append(f"  Overboost Protection: {tune['boost_control']['boost_limits']['overboost_protection']}")
        report.append("")
        
        report.append("SAFETY FEATURES:")
        report.append(f"  Knock Sensitivity: {tune['safety_parameters']['knock_control']['sensitivity']}")
        report.append(f"  Max Coolant Temp: {tune['safety_parameters']['temperature_limits']['coolant_max']}°C")
        report.append(f"  Max EGT: {tune['safety_parameters']['temperature_limits']['egt_max']}°C")
        report.append("")
        
        return "\n".join(report)

# Utility functions
def get_fuel_grade_recommendations(vehicle_usage: str) -> str:
    """GET RECOMMENDED FUEL GRADE BASED ON USAGE"""
    recommendations = {
        'daily_commuting': '95 RON - Best balance of cost and reliability',
        'performance_driving': '98 RON - Good for spirited driving',
        'track_days': '100+ RON - Maximum performance with safety margin',
        'mixed_use': '98 RON - Versatile for all conditions'
    }
    
    return recommendations.get(vehicle_usage, '95 RON - Safe default choice')

def calculate_power_gain(stock_power: int, fuel_grade: str) -> int:
    """CALCULATE ESTIMATED POWER GAIN FROM FUEL GRADE"""
    gains = {
        '95': 10,   # 10 whp gain over stock
        '98': 25,   # 25 whp gain over stock
        '100+': 35  # 35 whp gain over stock
    }
    
    return stock_power + gains.get(fuel_grade, 0)

# Demonstration
def demonstrate_safe_tuning():
    """DEMONSTRATE SAFE TUNING CAPABILITIES"""
    print("MAZDASPEED 3 SAFE TUNING DEMONSTRATION")
    print("=" * 50)
    
    tuner = SafePremiumFuelTuner()
    
    # Show safety limits
    print("\nSafety Limits by Fuel Grade:")
    print(f"95 Octane - Max Boost: {tuner.safe_limits.octane_95['max_boost_psi']} psi")
    print(f"98 Octane - Max Boost: {tuner.safe_limits.octane_98['max_boost_psi']} psi")
    print(f"100+ Octane - Max Boost: {tuner.safe_limits.octane_100_plus['max_boost_psi']} psi")
    
    # Get safe tune for 98 octane
    tune_98 = tuner.get_safe_tune('98')
    print(f"\n98 Octane Tune Target: {tune_98['metadata']['target_power']}")
    
    # Validate tune
    warnings = tuner.validate_tune_safety(tune_98, '98')
    if warnings:
        print("\nSafety Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("\n✓ Tune passes all safety checks")
    
    # Generate report
    report = tuner.generate_tune_report(tune_98)
    print("\n" + report)
    
    print("\nSafe tuning demonstration complete!")

if __name__ == "__main__":
    demonstrate_safe_tuning()
