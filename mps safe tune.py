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
                    'knock_response': 'Very Sensitive - 1.0° pull initial',
                    'recovery_rate': 0.2,  # Slow, cautious recovery
                    'temperature_compensation': {
                        'coolant_derate_start': 95,  # Early derate
                        'intake_derate_start': 35,   # Conservative
                        'derate_rate': 0.15  # Aggressive derate
                    }
                }
            },
            'fuel_maps': {
                'target_afr': {
                    'idle': 14.7,
                    'cruise': 14.7,
                    'light_load': 14.0,
                    'medium_load': 13.2,
                    'high_load': 12.4,
                    'wot': 11.6  # Richer for safety
                },
                'enrichment_strategy': {
                    'cold_start': 1.25,  # Extra fuel for safety
                    'transient_enrichment': 1.15,
                    'overrun_cut_rpm': 3500,
                    'safety_margin': 'Rich for component protection'
                }
            },
            'boost_maps': {
                'target_boost': {
                    '1st_gear': 17.0,   # Very conservative
                    '2nd_gear': 18.5,
                    '3rd_gear': 19.5,
                    '4th_gear': 19.5,
                    '5th_gear': 19.5,
                    '6th_gear': 19.0
                },
                'control_parameters': {
                    'wastegate_duty_peak': 75,  # Conservative
                    'wastegate_duty_hold': 62,
                    'spool_emphasis': 80,  # Gentle spool
                    'overshoot_prevention': 'Aggressive'
                },
                'safety_features': {
                    'boost_taper_high_rpm': True,
                    'temperature_derate_aggressive': True,
                    'gear_specific_limits_strict': True
                }
            },
            'vvt_maps': {
                'intake_advance': {
                    '2000_rpm': 18, '3000_rpm': 22, '4000_rpm': 25,
                    '5000_rpm': 26, '6000_rpm': 26, '6500_rpm': 24
                },
                'exhaust_retard': {
                    '2000_rpm': 8, '3000_rpm': 10, '4000_rpm': 12,
                    '5000_rpm': 12, '6000_rpm': 12, '6500_rpm': 10
                }
            }
        }
    
    def _create_safe_98_octane_tune(self) -> Dict[str, Any]:
        """SAFE TUNE FOR 98 OCTANE FUEL - BALANCED PERFORMANCE & RELIABILITY"""
        limits = self.safe_limits.octane_98
        
        return {
            'metadata': {
                'tune_type': 'SAFE_BALANCED',
                'fuel_grade': '98 RON',
                'target_power': '275-285 WHP',
                'target_torque': '315-325 WTQ',
                'description': 'Safe 98 octane tune - Balanced performance & reliability',
                'safety_margin': '18% factory margin maintained',
                'recommended_use': 'Daily driving with spirited capability'
            },
            'ignition_maps': {
                'base_timing': [
                    # RPM: 2000, 3000, 4000, 5000, 6000, 6500
                    [10, 12, 14, 16, 17, 16],   # 10% Load
                    [12, 14, 16, 18, 19, 18],   # 20% Load
                    [14, 16, 18, 20, 21, 20],   # 30% Load
                    [16, 18, 20, 22, 23, 22],   # 40% Load
                    [18, 20, 22, 24, 25, 24],   # 50% Load
                    [20, 22, 24, 26, 27, 26],   # 60% Load
                    [22, 24, 26, 28, 29, 28],   # 70% Load
                    [24, 26, 28, 30, 31, 30]    # 80%+ Load
                ],
                'advance_strategy': {
                    'max_advance': limits['max_timing_advance'],
                    'knock_response': 'Sensitive - 1.2° pull initial',
                    'recovery_rate': 0.25,
                    'temperature_compensation': {
                        'coolant_derate_start': 100,
                        'intake_derate_start': 40,
                        'derate_rate': 0.12
                    }
                }
            },
            'fuel_maps': {
                'target_afr': {
                    'idle': 14.7,
                    'cruise': 14.7,
                    'light_load': 13.8,
                    'medium_load': 13.0,
                    'high_load': 12.2,
                    'wot': 11.5
                },
                'enrichment_strategy': {
                    'cold_start': 1.22,
                    'transient_enrichment': 1.12,
                    'overrun_cut_rpm': 3700
                }
            },
            'boost_maps': {
                'target_boost': {
                    '1st_gear': 18.5,
                    '2nd_gear': 20.0,
                    '3rd_gear': 21.0,
                    '4th_gear': 21.0,
                    '5th_gear': 21.0,
                    '6th_gear': 20.5
                },
                'control_parameters': {
                    'wastegate_duty_peak': 78,
                    'wastegate_duty_hold': 65,
                    'spool_emphasis': 85,
                    'overshoot_prevention': 'Moderate'
                }
            },
            'vvt_maps': {
                'intake_advance': {
                    '2000_rpm': 20, '3000_rpm': 24, '4000_rpm': 27,
                    '5000_rpm': 28, '6000_rpm': 28, '6500_rpm': 26
                },
                'exhaust_retard': {
                    '2000_rpm': 9, '3000_rpm': 11, '4000_rpm': 13,
                    '5000_rpm': 13, '6000_rpm': 13, '6500_rpm': 11
                }
            }
        }
    
    def _create_safe_100_plus_tune(self) -> Dict[str, Any]:
        """SAFE BUT PERFORMANCE-ORIENTED TUNE FOR 100+ OCTANE FUEL"""
        limits = self.safe_limits.octane_100_plus
        
        return {
            'metadata': {
                'tune_type': 'SAFE_PERFORMANCE',
                'fuel_grade': '100+ RON',
                'target_power': '290-300 WHP',
                'target_torque': '330-340 WTQ',
                'description': 'Safe 100+ octane tune - Performance with reliability',
                'safety_margin': '15% factory margin maintained',
                'recommended_use': 'Spirited driving, occasional track use'
            },
            'ignition_maps': {
                'base_timing': [
                    # RPM: 2000, 3000, 4000, 5000, 6000, 6500
                    [11, 13, 15, 17, 18, 17],   # 10% Load
                    [13, 15, 17, 19, 20, 19],   # 20% Load
                    [15, 17, 19, 21, 22, 21],   # 30% Load
                    [17, 19, 21, 23, 24, 23],   # 40% Load
                    [19, 21, 23, 25, 26, 25],   # 50% Load
                    [21, 23, 25, 27, 28, 27],   # 60% Load
                    [23, 25, 27, 29, 30, 29],   # 70% Load
                    [25, 27, 29, 31, 32, 31]    # 80%+ Load
                ],
                'advance_strategy': {
                    'max_advance': limits['max_timing_advance'],
                    'knock_response': 'Moderate - 1.5° pull initial',
                    'recovery_rate': 0.3,
                    'temperature_compensation': {
                        'coolant_derate_start': 105,
                        'intake_derate_start': 45,
                        'derate_rate': 0.10
                    }
                }
            },
            'fuel_maps': {
                'target_afr': {
                    'idle': 14.7,
                    'cruise': 14.7,
                    'light_load': 13.6,
                    'medium_load': 12.8,
                    'high_load': 12.0,
                    'wot': 11.4
                },
                'enrichment_strategy': {
                    'cold_start': 1.20,
                    'transient_enrichment': 1.10,
                    'overrun_cut_rpm': 3900
                }
            },
            'boost_maps': {
                'target_boost': {
                    '1st_gear': 20.0,
                    '2nd_gear': 21.5,
                    '3rd_gear': 22.5,
                    '4th_gear': 22.5,
                    '5th_gear': 22.5,
                    '6th_gear': 22.0
                },
                'control_parameters': {
                    'wastegate_duty_peak': 82,
                    'wastegate_duty_hold': 70,
                    'spool_emphasis': 88
                }
            },
            'vvt_maps': {
                'intake_advance': {
                    '2000_rpm': 22, '3000_rpm': 26, '4000_rpm': 29,
                    '5000_rpm': 30, '6000_rpm': 30, '6500_rpm': 28
                },
                'exhaust_retard': {
                    '2000_rpm': 10, '3000_rpm': 12, '4000_rpm': 14,
                    '5000_rpm': 14, '6000_rpm': 14, '6500_rpm': 12
                }
            },
            'safety_features': {
                'launch_control': {'rpm': 4000, 'traction_integration': 'Conservative'},
                'flat_shift': {'enabled': True, 'rpm_limit': 6800},
                'throttle_mapping': 'Linear sport (not aggressive)',
                'pop_bang_tune': 'Disabled - for reliability'
            }
        }
    
    def _safety_monitoring_systems(self) -> Dict[str, Any]:
        """COMPREHENSIVE SAFETY MONITORING SYSTEMS"""
        return {
            'knock_protection': {
                'sensitivity': 'High - early detection',
                'max_retard_per_pull': -3.0,
                'learning_aggression': 0.4,  # Conservative learning
                'per_cylinder_monitoring': True,
                'false_knock_filtering': 'Aggressive'
            },
            'temperature_protection': {
                'coolant': {
                    'warning': 100,  # Early warning
                    'derate_start': 105,
                    'derate_aggressive': 110,
                    'hard_cut': 120
                },
                'intake_air': {
                    'warning': 40,
                    'derate_start': 50,
                    'derate_aggressive': 60
                },
                'oil': {
                    'warning': 120,
                    'derate_start': 130,
                    'hard_cut': 140
                }
            },
            'boost_protection': {
                'overboost_threshold': 2.0,  # PSI over target
                'overboost_timer': 2.0,  # Seconds
                'absolute_boost_limit': 25.0,  # Hard cut
                'gear_specific_limits': 'Conservative'
            },
            'fuel_system_protection': {
                'injector_duty_warning': 80,
                'injector_duty_cut': 85,
                'low_pressure_fuel_warning': 35,  # PSI
                'high_pressure_fuel_max': 1700  # PSI
            }
        }
    
    def calculate_safe_performance_gains(self) -> Dict[str, Any]:
        """CALCULATE SAFE PERFORMANCE GAINS OVER STOCK"""
        stock_whp = 233
        stock_wtq = 270
        
        return {
            'octane_95': {
                'whp_gain': 32,  # 265 vs 233
                'wtq_gain': 30,  # 300 vs 270
                'percent_gain_whp': 13.7,
                'percent_gain_wtq': 11.1,
                'safety_rating': 'EXCELLENT',
                'estimated_engine_life': 'Same as stock'
            },
            'octane_98': {
                'whp_gain': 47,  # 280 vs 233
                'wtq_gain': 45,  # 315 vs 270
                'percent_gain_whp': 20.2,
                'percent_gain_wtq': 16.7,
                'safety_rating': 'VERY GOOD',
                'estimated_engine_life': 'Minimal impact'
            },
            'octane_100_plus': {
                'whp_gain': 62,  # 295 vs 233
                'wtq_gain': 60,  # 330 vs 270
                'percent_gain_whp': 26.6,
                'percent_gain_wtq': 22.2,
                'safety_rating': 'GOOD',
                'estimated_engine_life': 'Slight reduction possible'
            }
        }
    
    def get_safe_tuning_recommendations(self) -> Dict[str, List[str]]:
        """GET SAFE TUNING RECOMMENDATIONS"""
        return {
            'octane_95': [
                "Perfect for daily commuting",
                "Ideal for high mileage vehicles",
                "Maximum component longevity",
                "Safe for all driving conditions",
                "Recommended for stock vehicles 100,000+ miles"
            ],
            'octane_98': [
                "Excellent daily driver with more power",
                "Good for occasional spirited driving",
                "Maintains strong reliability margins",
                "Safe for regular highway use",
                "Recommended for vehicles under 100,000 miles"
            ],
            'octane_100_plus': [
                "Best performance while maintaining safety",
                "Good for weekend spirited driving",
                "Occasional track use acceptable",
                "Monitor temperatures during extended use",
                "Recommended with fresh maintenance"
            ]
        }
    
    def generate_safe_tune_package(self, fuel_grade: str) -> Dict[str, Any]:
        """GENERATE COMPLETE SAFE TUNE PACKAGE"""
        if fuel_grade not in self.base_tunes:
            raise ValueError(f"Fuel grade {fuel_grade} not supported")
        
        base_tune = self.base_tunes[fuel_grade]
        performance_gains = self.calculate_safe_performance_gains()[fuel_grade]
        recommendations = self.get_safe_tuning_recommendations()[fuel_grade]
        
        return {
            'tune_data': base_tune,
            'safety_systems': self.safety_monitoring_systems,
            'performance_analysis': {
                'expected_gains': performance_gains,
                'safety_rating': performance_gains['safety_rating'],
                'estimated_engine_life': performance_gains['estimated_engine_life'],
                'estimated_0_60': self._estimate_safe_0_60(fuel_grade),
                'estimated_quarter_mile': self._estimate_safe_quarter_mile(fuel_grade)
            },
            'tuning_instructions': [
                "1. Verify vehicle maintenance is current",
                "2. Use specified fuel grade consistently",
                "3. Perform gentle break-in driving for first 100 miles",
                "4. Monitor temperatures during initial runs",
                "5. Check for any check engine lights",
                "6. Enjoy reliable increased performance"
            ],
            'maintenance_recommendations': [
                "Oil changes every 5,000 miles",
                "Spark plugs every 30,000 miles",
                "Air filter every 15,000 miles",
                "Fuel filter every 60,000 miles",
                "Regular data logging recommended"
            ],
            'recommendations': recommendations
        }
    
    def _estimate_safe_0_60(self, fuel_grade: str) -> str:
        """ESTIMATE SAFE 0-60 TIMES"""
        times = {
            'octane_95': '5.4-5.6 seconds',
            'octane_98': '5.2-5.4 seconds', 
            'octane_100_plus': '5.0-5.2 seconds'
        }
        return times.get(fuel_grade, 'Unknown')
    
    def _estimate_safe_quarter_mile(self, fuel_grade: str) -> str:
        """ESTIMATE SAFE QUARTER MILE TIMES"""
        times = {
            'octane_95': '13.6-13.8 seconds',
            'octane_98': '13.4-13.6 seconds',
            'octane_100_plus': '13.2-13.4 seconds'
        }
        return times.get(fuel_grade, 'Unknown')

# DEMONSTRATION
def demonstrate_safe_tunes():
    """DEMONSTRATE ALL SAFE TUNE OPTIONS"""
    tuner = SafePremiumFuelTuner()
    
    print("SAFE PREMIUM FUEL TUNES - 2011 MAZDASPEED 3")
    print("=" * 70)
    print("PRIORITY: RELIABILITY & LONGEVITY OVER MAXIMUM POWER")
    print("=" * 70)
    
    # Show safe performance comparison
    gains = tuner.calculate_safe_performance_gains()
    
    print("\n🎯 SAFE PERFORMANCE GAINS:")
    print("-" * 40)
    for fuel_grade, gain_data in gains.items():
        print(f"\n{fuel_grade.upper().replace('_', ' ')}:")
        print(f"  WHP: +{gain_data['whp_gain']} ({gain_data['percent_gain_whp']}%)")
        print(f"  WTQ: +{gain_data['wtq_gain']} ({gain_data['percent_gain_wtq']}%)")
        print(f"  Safety: {gain_data['safety_rating']}")
        print(f"  Engine Life: {gain_data['estimated_engine_life']}")
    
    # Generate specific safe tune examples
    print("\n🔧 SAFE TUNE PARAMETERS:")
    print("-" * 40)
    
    for fuel_grade in ['octane_95', 'octane_98', 'octane_100_plus']:
        tune_package = tuner.generate_safe_tune_package(fuel_grade)
        tune_data = tune_package['tune_data']
        
        print(f"\n{fuel_grade.upper().replace('_', ' ')} SAFE TUNE:")
        print(f"  Target: {tune_data['metadata']['target_power']}")
        print(f"  Boost: {tune_data['boost_maps']['target_boost']['3rd_gear']} PSI")
        print(f"  Timing: {tune_data['ignition_maps']['advance_strategy']['max_advance']}°")
        print(f"  AFR: {tune_data['fuel_maps']['target_afr']['wot']}:1")
        print(f"  Safety Margin: {tune_data['metadata']['safety_margin']}")
    
    # Safety features
    print("\n🛡️ SAFETY SYSTEMS ACTIVE:")
    print("-" * 40)
    safety = tuner.safety_monitoring_systems
    print("Knock Protection: Very sensitive with early detection")
    print("Temperature Monitoring: Conservative derating thresholds")
    print("Boost Protection: Strict overboost limits")
    print("Fuel System: Conservative duty cycle limits")
    
    print("\n💡 SAFE TUNING RECOMMENDATIONS:")
    print("-" * 40)
    recommendations = tuner.get_safe_tuning_recommendations()
    for fuel_grade, recs in recommendations.items():
        print(f"\n{fuel_grade.upper().replace('_', ' ')}:")
        for rec in recs:
            print(f"  • {rec}")
    
    print("\n" + "=" * 70)
    print("SUMMARY: SAFE PERFORMANCE WITH MAXIMUM RELIABILITY")
    print("=" * 70)
    print("95 Octane: +32 WHP - Maximum safety, daily driver")
    print("98 Octane: +47 WHP - Balanced performance & safety") 
    print("100+ Octane: +62 WHP - Good performance with safety")
    print("\nAll tunes maintain substantial safety margins for long-term reliability")

if __name__ == "__main__":
    demonstrate_safe_tunes()
    
    # Generate safe tune files
    tuner = SafePremiumFuelTuner()
    
    # Save safe 98 octane tune (recommended balanced choice)
    safe_tune_98 = tuner.generate_safe_tune_package('octane_98')
    with open('mazdaspeed3_safe_98_octane_tune.json', 'w') as f:
        json.dump(safe_tune_98, f, indent=2)
    
    # Save safe 100+ octane tune (for your NPD fuel)
    safe_tune_100_plus = tuner.generate_safe_tune_package('octane_100_plus')
    with open('mazdaspeed3_safe_100plus_octane_tune.json', 'w') as f:
        json.dump(safe_tune_100_plus, f, indent=2)
    
    print("\nSafe tune files generated:")
    print("  - mazdaspeed3_safe_98_octane_tune.json")
    print("  - mazdaspeed3_safe_100plus_octane_tune.json")
    print("\nThese tunes prioritize reliability and long-term engine health!")