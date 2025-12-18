#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PREMIUM_FUEL_OPTIMAL_TUNE.py
MAXIMUM PERFORMANCE TUNE FOR 95, 98, 100+ OCTANE FUELS
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import json

@dataclass
class PremiumFuelLimits:
    """SAFETY LIMITS FOR PREMIUM FUEL TUNES"""
    octane_95: Dict[str, float]
    octane_98: Dict[str, float] 
    octane_100_plus: Dict[str, float]

class PremiumFuelTuner:
    """
    OPTIMAL TUNES FOR HIGH-OCTANE FUELS (95, 98, 100+)
    Leverages higher knock resistance for maximum performance
    """
    
    def __init__(self):
        self.fuel_limits = self._define_fuel_limits()
        self.base_tunes = self._generate_base_tunes()
        
    def _define_fuel_limits(self) -> PremiumFuelLimits:
        """DEFINE SAFETY LIMITS FOR EACH FUEL GRADE"""
        return PremiumFuelLimits(
            octane_95={
                'max_boost_psi': 21.5,
                'max_timing_advance': 23.0,
                'min_afr_wot': 11.4,
                'max_knock_retard': -3.0,
                'safe_egt_c': 920,
                'octane_safety_margin': 'Moderate'
            },
            octane_98={
                'max_boost_psi': 23.0,
                'max_timing_advance': 25.0,
                'min_afr_wot': 11.3,
                'max_knock_retard': -2.0,
                'safe_egt_c': 940,
                'octane_safety_margin': 'High'
            },
            octane_100_plus={
                'max_boost_psi': 24.5,
                'max_timing_advance': 27.0,
                'min_afr_wot': 11.2,
                'max_knock_retard': -1.0,
                'safe_egt_c': 950,
                'octane_safety_margin': 'Very High'
            }
        )
    
    def _generate_base_tunes(self) -> Dict[str, Any]:
        """GENERATE BASE TUNE TEMPLATES FOR EACH FUEL GRADE"""
        return {
            'octane_95': self._create_95_octane_tune(),
            'octane_98': self._create_98_octane_tune(),
            'octane_100_plus': self._create_100_plus_tune()
        }
    
    def _create_95_octane_tune(self) -> Dict[str, Any]:
        """OPTIMAL TUNE FOR 95 OCTANE FUEL"""
        limits = self.fuel_limits.octane_95
        
        return {
            'metadata': {
                'fuel_grade': '95 RON',
                'target_power': '275-290 WHP',
                'target_torque': '310-325 WTQ',
                'description': 'Aggressive 95 octane tune - good knock resistance',
                'safety_margin': '12% factory margin'
            },
            'ignition_maps': {
                'base_timing': [
                    # RPM: 2000, 3000, 4000, 5000, 6000, 6500, 7000
                    [11, 13, 15, 17, 18, 17, 16],    # 10% Load
                    [13, 15, 17, 19, 20, 19, 18],    # 20% Load
                    [15, 17, 19, 21, 22, 21, 20],    # 30% Load
                    [17, 19, 21, 23, 24, 23, 22],    # 40% Load
                    [19, 21, 23, 25, 26, 25, 24],    # 50% Load
                    [21, 23, 25, 27, 28, 27, 26],    # 60% Load
                    [23, 25, 27, 29, 30, 29, 28],    # 70% Load
                    [25, 27, 29, 31, 32, 31, 30]     # 80%+ Load
                ],
                'advance_strategy': {
                    'max_advance': limits['max_timing_advance'],
                    'knock_response': 'Moderate - 1.5° pull initial',
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
                    # RPM: 2000, 3000, 4000, 5000, 6000, 6500, 7000
                    [14.7, 14.7, 14.7, 14.5, 14.3, 14.1, 13.9],  # Light load
                    [14.5, 14.5, 14.3, 14.1, 13.9, 13.7, 13.5],  # Medium load
                    [13.3, 13.1, 12.9, 12.7, 12.5, 12.3, 12.1],  # Heavy load
                    [12.3, 12.1, 11.9, 11.7, 11.5, 11.4, 11.4]   # WOT
                ],
                'enrichment_strategy': {
                    'wot_target': limits['min_afr_wot'],
                    'cold_start_enrichment': '+15%',
                    'warmup_enrichment': '+5%',
                    'acceleration_enrichment': '+8%'
                }
            },
            'boost_control': {
                'target_boost': [
                    # RPM: 2000, 3000, 4000, 5000, 6000, 6500, 7000
                    [10.0, 14.0, 17.5, 20.0, 21.0, 20.5, 19.0],  # Light load
                    [12.0, 16.0, 19.0, 21.0, 21.5, 21.0, 20.0],  # Medium load
                    [14.0, 18.0, 20.5, 21.5, 21.5, 21.0, 20.0]   # Heavy load
                ],
                'boost_limits': {
                    'max_boost': limits['max_boost_psi'],
                    'overboost_protection': 'Active - 2.0 psi limit',
                    'wastegate_response': 'Quick',
                    'spool_control': 'Aggressive'
                }
            }
        }
    
    def _create_98_octane_tune(self) -> Dict[str, Any]:
        """OPTIMAL TUNE FOR 98 OCTANE FUEL"""
        limits = self.fuel_limits.octane_98
        
        return {
            'metadata': {
                'fuel_grade': '98 RON',
                'target_power': '290-310 WHP',
                'target_torque': '325-345 WTQ',
                'description': 'High performance 98 octane tune - excellent knock resistance',
                'safety_margin': '10% factory margin'
            },
            'ignition_maps': {
                'base_timing': [
                    [12, 14, 16, 18, 20, 19, 18],
                    [14, 16, 18, 20, 22, 21, 20],
                    [16, 18, 20, 22, 24, 23, 22],
                    [18, 20, 22, 24, 26, 25, 24],
                    [20, 22, 24, 26, 28, 27, 26],
                    [22, 24, 26, 27, 29, 28, 27],
                    [24, 26, 27, 28, 30, 29, 28],
                    [26, 27, 28, 29, 31, 30, 29]
                ],
                'advance_strategy': {
                    'max_advance': limits['max_timing_advance'],
                    'knock_response': 'Moderate - 1.0° pull initial',
                    'recovery_rate': 0.5,
                    'temperature_compensation': {
                        'coolant_derate_start': 108,
                        'intake_derate_start': 48,
                        'derate_rate': 0.06
                    }
                }
            },
            'fuel_maps': {
                'target_afr': [
                    [14.7, 14.7, 14.7, 14.5, 14.3, 14.1, 13.9],
                    [14.5, 14.5, 14.3, 14.1, 13.9, 13.7, 13.5],
                    [13.1, 12.9, 12.7, 12.5, 12.3, 12.1, 11.9],
                    [12.1, 11.9, 11.7, 11.5, 11.3, 11.3, 11.3]
                ],
                'enrichment_strategy': {
                    'wot_target': limits['min_afr_wot'],
                    'cold_start_enrichment': '+12%',
                    'warmup_enrichment': '+3%',
                    'acceleration_enrichment': '+10%'
                }
            },
            'boost_control': {
                'target_boost': [
                    [11.0, 15.0, 18.5, 21.5, 22.5, 22.0, 20.5],
                    [13.0, 17.0, 20.0, 22.5, 23.0, 22.5, 21.5],
                    [15.0, 19.0, 21.5, 23.0, 23.0, 22.5, 21.5]
                ],
                'boost_limits': {
                    'max_boost': limits['max_boost_psi'],
                    'overboost_protection': 'Active - 2.5 psi limit',
                    'wastegate_response': 'Very Quick',
                    'spool_control': 'Very Aggressive'
                }
            }
        }
    
    def _create_100_plus_tune(self) -> Dict[str, Any]:
        """OPTIMAL TUNE FOR 100+ OCTANE FUEL"""
        limits = self.fuel_limits.octane_100_plus
        
        return {
            'metadata': {
                'fuel_grade': '100+ RON',
                'target_power': '310-330 WHP',
                'target_torque': '345-365 WTQ',
                'description': 'Maximum performance 100+ octane tune - race fuel',
                'safety_margin': '8% factory margin'
            },
            'ignition_maps': {
                'base_timing': [
                    [13, 15, 17, 19, 21, 20, 19],
                    [15, 17, 19, 21, 23, 22, 21],
                    [17, 19, 21, 23, 25, 24, 23],
                    [19, 21, 23, 25, 27, 26, 25],
                    [21, 23, 25, 27, 29, 28, 27],
                    [23, 25, 27, 28, 30, 29, 28],
                    [25, 27, 28, 29, 31, 30, 29],
                    [27, 28, 29, 30, 32, 31, 30]
                ],
                'advance_strategy': {
                    'max_advance': limits['max_timing_advance'],
                    'knock_response': 'Aggressive - 0.5° pull initial',
                    'recovery_rate': 0.6,
                    'temperature_compensation': {
                        'coolant_derate_start': 110,
                        'intake_derate_start': 50,
                        'derate_rate': 0.05
                    }
                }
            },
            'fuel_maps': {
                'target_afr': [
                    [14.7, 14.7, 14.7, 14.5, 14.3, 14.1, 13.9],
                    [14.5, 14.5, 14.3, 14.1, 13.9, 13.7, 13.5],
                    [12.9, 12.7, 12.5, 12.3, 12.1, 11.9, 11.7],
                    [11.9, 11.7, 11.5, 11.3, 11.2, 11.2, 11.2]
                ],
                'enrichment_strategy': {
                    'wot_target': limits['min_afr_wot'],
                    'cold_start_enrichment': '+10%',
                    'warmup_enrichment': '+2%',
                    'acceleration_enrichment': '+12%'
                }
            },
            'boost_control': {
                'target_boost': [
                    [12.0, 16.0, 19.5, 22.5, 24.0, 23.5, 22.0],
                    [14.0, 18.0, 21.0, 23.5, 24.5, 24.0, 23.0],
                    [16.0, 20.0, 22.5, 24.5, 24.5, 24.0, 23.0]
                ],
                'boost_limits': {
                    'max_boost': limits['max_boost_psi'],
                    'overboost_protection': 'Active - 3.0 psi limit',
                    'wastegate_response': 'Maximum',
                    'spool_control': 'Race'
                }
            }
        }
    
    def get_performance_tune(self, fuel_grade: str) -> Dict[str, Any]:
        """GET PERFORMANCE TUNE FOR SPECIFIED FUEL GRADE"""
        fuel_key = f"octane_{fuel_grade.replace('+', '_plus')}"
        
        if fuel_key in self.base_tunes:
            return self.base_tunes[fuel_key]
        else:
            raise ValueError(f"Unsupported fuel grade: {fuel_grade}")
    
    def optimize_for_conditions(self, base_tune: Dict[str, Any], 
                               ambient_temp: float, humidity: float,
                               altitude: float) -> Dict[str, Any]:
        """OPTIMIZE TUNE FOR ENVIRONMENTAL CONDITIONS"""
        optimized_tune = base_tune.copy()
        
        # Temperature compensation
        if ambient_temp > 30:  # Hot weather
            # Reduce timing and enrich mixture
            for i in range(len(optimized_tune['ignition_maps']['base_timing'])):
                for j in range(len(optimized_tune['ignition_maps']['base_timing'][i])):
                    optimized_tune['ignition_maps']['base_timing'][i][j] -= 1
            
            # Enrich fuel
            for i in range(len(optimized_tune['fuel_maps']['target_afr'])):
                for j in range(len(optimized_tune['fuel_maps']['target_afr'][i])):
                    optimized_tune['fuel_maps']['target_afr'][i][j] -= 0.1
        
        elif ambient_temp < 10:  # Cold weather
            # Can advance timing more
            for i in range(len(optimized_tune['ignition_maps']['base_timing'])):
                for j in range(len(optimized_tune['ignition_maps']['base_timing'][i])):
                    optimized_tune['ignition_maps']['base_timing'][i][j] += 1
        
        # Altitude compensation
        if altitude > 1000:  # High altitude
            # Reduce boost target
            for i in range(len(optimized_tune['boost_control']['target_boost'])):
                for j in range(len(optimized_tune['boost_control']['target_boost'][i])):
                    optimized_tune['boost_control']['target_boost'][i][j] -= (altitude / 1000) * 0.5
        
        # Humidity compensation
        if humidity > 70:  # High humidity
            # Slightly enrich mixture
            for i in range(len(optimized_tune['fuel_maps']['target_afr'])):
                for j in range(len(optimized_tune['fuel_maps']['target_afr'][i])):
                    optimized_tune['fuel_maps']['target_afr'][i][j] -= 0.05
        
        return optimized_tune
    
    def calculate_performance_metrics(self, tune: Dict[str, Any]) -> Dict[str, float]:
        """CALCULATE EXPECTED PERFORMANCE METRICS"""
        metrics = {}
        
        # Extract key parameters
        max_boost = max(max(row) for row in tune['boost_control']['target_boost'])
        max_timing = max(max(row) for row in tune['ignition_maps']['base_timing'])
        min_afr = min(min(row) for row in tune['fuel_maps']['target_afr'])
        
        # Estimate power gain based on parameters
        base_power = 263  # Stock WHP
        boost_gain = (max_boost - 15.5) * 8  # ~8 WHP per psi over stock
        timing_gain = (max_timing - 15) * 3   # ~3 WHP per degree over stock
        afr_gain = (11.5 - min_afr) * 10     # ~10 WHP per 0.1 AFR leaner
        
        estimated_power = base_power + boost_gain + timing_gain + afr_gain
        metrics['estimated_wheel_power'] = estimated_power
        
        # Estimate torque (typically 1.2x power)
        metrics['estimated_wheel_torque'] = estimated_power * 1.2
        
        # Calculate efficiency metrics
        metrics['boost_efficiency'] = max_boost / 24.5  # Percentage of max safe boost
        metrics['timing_efficiency'] = max_timing / 27.0  # Percentage of max safe timing
        
        return metrics
    
    def generate_comparison_report(self, tune1: Dict[str, Any], tune2: Dict[str, Any],
                                 tune1_name: str, tune2_name: str) -> str:
        """GENERATE COMPARISON REPORT BETWEEN TWO TUNES"""
        report = []
        report.append("=" * 60)
        report.append(f"TUNE COMPARISON: {tune1_name} vs {tune2_name}")
        report.append("=" * 60)
        
        # Calculate metrics for both tunes
        metrics1 = self.calculate_performance_metrics(tune1)
        metrics2 = self.calculate_performance_metrics(tune2)
        
        # Power comparison
        power_diff = metrics2['estimated_wheel_power'] - metrics1['estimated_wheel_power']
        report.append(f"\nPOWER COMPARISON:")
        report.append(f"  {tune1_name}: {metrics1['estimated_wheel_power']:.0f} WHP")
        report.append(f"  {tune2_name}: {metrics2['estimated_wheel_power']:.0f} WHP")
        report.append(f"  Difference: {power_diff:+.0f} WHP")
        
        # Torque comparison
        torque_diff = metrics2['estimated_wheel_torque'] - metrics1['estimated_wheel_torque']
        report.append(f"\nTORQUE COMPARISON:")
        report.append(f"  {tune1_name}: {metrics1['estimated_wheel_torque']:.0f} WTQ")
        report.append(f"  {tune2_name}: {metrics2['estimated_wheel_torque']:.0f} WTQ")
        report.append(f"  Difference: {torque_diff:+.0f} WTQ")
        
        # Boost comparison
        boost1 = max(max(row) for row in tune1['boost_control']['target_boost'])
        boost2 = max(max(row) for row in tune2['boost_control']['target_boost'])
        boost_diff = boost2 - boost1
        report.append(f"\nBOOST COMPARISON:")
        report.append(f"  {tune1_name}: {boost1:.1f} psi")
        report.append(f"  {tune2_name}: {boost2:.1f} psi")
        report.append(f"  Difference: {boost_diff:+.1f} psi")
        
        # Timing comparison
        timing1 = max(max(row) for row in tune1['ignition_maps']['base_timing'])
        timing2 = max(max(row) for row in tune2['ignition_maps']['base_timing'])
        timing_diff = timing2 - timing1
        report.append(f"\nTIMING COMPARISON:")
        report.append(f"  {tune1_name}: {timing1:.1f}°")
        report.append(f"  {tune2_name}: {timing2:.1f}°")
        report.append(f"  Difference: {timing_diff:+.1f}°")
        
        return "\n".join(report)

# Utility functions
def get_fuel_requirements(power_target: int) -> str:
    """GET REQUIRED FUEL GRADE FOR POWER TARGET"""
    if power_target <= 270:
        return "95 RON - Sufficient for moderate power goals"
    elif power_target <= 300:
        return "98 RON - Recommended for high power goals"
    else:
        return "100+ RON - Required for maximum power"

def estimate_fuel_economy_impact(tune: Dict[str, Any]) -> float:
    """ESTIMATE FUEL ECONOMY IMPACT OF TUNE"""
    # Base on boost and timing
    max_boost = max(max(row) for row in tune['boost_control']['target_boost'])
    max_timing = max(max(row) for row in tune['ignition_maps']['base_timing'])
    
    # Calculate impact percentage
    boost_impact = (max_boost - 15.5) * 2  # 2% per psi over stock
    timing_impact = (max_timing - 15) * 1   # 1% per degree over stock
    
    total_impact = boost_impact + timing_impact
    return -total_impact  # Negative because it reduces economy

# Demonstration
def demonstrate_performance_tuning():
    """DEMONSTRATE PERFORMANCE TUNING CAPABILITIES"""
    print("MAZDASPEED 3 PERFORMANCE TUNING DEMONSTRATION")
    print("=" * 50)
    
    tuner = PremiumFuelTuner()
    
    # Get 98 octane tune
    tune_98 = tuner.get_performance_tune('98')
    print(f"\n98 Octane Performance Tune:")
    print(f"Target Power: {tune_98['metadata']['target_power']}")
    print(f"Target Torque: {tune_98['metadata']['target_torque']}")
    
    # Calculate performance metrics
    metrics = tuner.calculate_performance_metrics(tune_98)
    print(f"\nEstimated Performance:")
    print(f"Wheel Power: {metrics['estimated_wheel_power']:.0f} WHP")
    print(f"Wheel Torque: {metrics['estimated_wheel_torque']:.0f} WTQ")
    
    # Optimize for conditions
    optimized = tuner.optimize_for_conditions(tune_98, 25, 60, 500)
    print(f"\nOptimized for 25°C, 60% humidity, 500m altitude")
    
    # Compare with safe tune
    from .safe_tunes import SafePremiumFuelTuner
    safe_tuner = SafePremiumFuelTuner()
    safe_tune = safe_tuner.get_safe_tune('98')
    
    comparison = tuner.generate_comparison_report(
        safe_tune, tune_98, 
        "Safe 98 Octane", "Performance 98 Octane"
    )
    print("\n" + comparison)
    
    print("\nPerformance tuning demonstration complete!")

if __name__ == "__main__":
    demonstrate_performance_tuning()
