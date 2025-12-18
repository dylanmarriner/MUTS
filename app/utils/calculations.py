#!/usr/bin/env python3
"""
ADVANCED CALCULATION UTILITIES FOR MAZDASPEED 3 TUNING
Exact mathematical implementations for performance calculations
"""

import numpy as np
import math
from typing import Dict, Tuple, Optional

class AdvancedCalculations:
    """
    Advanced calculation utilities for Mazdaspeed 3 tuning
    Provides precise mathematical formulas for performance metrics
    """
    
    def __init__(self):
        # Engine constants
        self.engine_constants = {
            'displacement': 2.3,          # Liters
            'displacement_cc': 2300,       # cc
            'bore': 87.5,                 # mm
            'stroke': 94.0,               # mm
            'compression_ratio': 9.5,
            'rod_length': 150.0,          # mm
            'num_cylinders': 4
        }
        
        # Conversion factors
        self.conversions = {
            'psi_to_kpa': 6.89476,
            'kpa_to_psi': 0.145038,
            'nm_to_lbft': 0.737562,
            'lbft_to_nm': 1.35582,
            'kw_to_hp': 1.34102,
            'hp_to_kw': 0.7457
        }
    
    def calculate_brake_horsepower(self, torque_nm: float, rpm: float) -> float:
        """
        Calculate brake horsepower from torque and RPM
        Formula: HP = (Torque × RPM) / 5252
        """
        if rpm <= 0:
            return 0.0
        
        hp = (torque_nm * self.conversions['nm_to_lbft'] * rpm) / 5252
        return hp
    
    def calculate_engine_torque(self, horsepower: float, rpm: float) -> float:
        """
        Calculate engine torque from horsepower and RPM
        Formula: Torque = (HP × 5252) / RPM
        """
        if rpm <= 0:
            return 0.0
        
        torque_lbft = (horsepower * 5252) / rpm
        torque_nm = torque_lbft * self.conversions['lbft_to_nm']
        return torque_nm
    
    def calculate_air_fuel_ratio(self, fuel_mass: float, air_mass: float) -> float:
        """
        Calculate air-fuel ratio
        Formula: AFR = Air Mass / Fuel Mass
        """
        if fuel_mass <= 0:
            return float('inf')
        
        return air_mass / fuel_mass
    
    def calculate_boost_pressure(self, manifold_pressure_kpa: float) -> float:
        """
        Calculate boost pressure from manifold absolute pressure
        Formula: Boost = MAP - Atmospheric Pressure
        """
        atmospheric_pressure = 101.325  # kPa
        boost_kpa = manifold_pressure_kpa - atmospheric_pressure
        return boost_kpa * self.conversions['kpa_to_psi']
    
    def calculate_compressor_outlet_temp(self, inlet_temp_c: float, 
                                       pressure_ratio: float, 
                                       efficiency: float) -> float:
        """
        Calculate compressor outlet temperature
        Formula: T2 = T1 + T1 × ((PR^(γ-1)/γ - 1) / ηc)
        """
        gamma = 1.4  # Specific heat ratio for air
        inlet_temp_k = inlet_temp_c + 273.15
        
        # Temperature rise
        temp_rise = inlet_temp_k * ((pressure_ratio ** ((gamma - 1) / gamma)) - 1) / efficiency
        
        outlet_temp_k = inlet_temp_k + temp_rise
        outlet_temp_c = outlet_temp_k - 273.15
        
        return outlet_temp_c
    
    def calculate_turbo_mass_flow(self, pressure_ratio: float, 
                                inlet_temp_c: float, 
                                turbo_rpm: float) -> float:
        """
        Calculate turbo mass flow rate
        Simplified model based on turbo speed and pressure ratio
        """
        # Base flow at standard conditions
        base_flow = 0.05  # kg/s at 100,000 RPM and PR=2.0
        
        # Speed correction
        speed_factor = (turbo_rpm / 100000) ** 0.5
        
        # Pressure ratio correction
        pr_factor = math.sqrt(pressure_ratio - 1.0)
        
        # Temperature correction
        temp_factor = math.sqrt(298.15 / (inlet_temp_c + 273.15))
        
        mass_flow = base_flow * speed_factor * pr_factor * temp_factor
        
        return mass_flow
    
    def calculate_exhaust_gas_temperature(self, engine_load: float, 
                                       afr: float, 
                                       ignition_timing: float,
                                       rpm: float) -> float:
        """
        Calculate exhaust gas temperature
        Empirical formula based on load, AFR, timing, and RPM
        """
        # Base EGT at moderate conditions
        base_egt = 800.0  # °C
        
        # Load factor (0-1)
        load_factor = min(engine_load, 1.0)
        
        # AFR correction
        afr_deviation = 14.7 - afr
        afr_correction = afr_deviation * 50.0  # °C per AFR unit
        
        # Timing correction (retarded timing increases EGT)
        timing_correction = (20.0 - ignition_timing) * 15.0  # °C per degree
        
        # RPM correction
        rpm_correction = (rpm - 3000) / 1000.0 * 20.0  # °C per 1000 RPM
        
        # Calculate final EGT
        egt = base_egt + (load_factor * 400.0) + afr_correction + \
              timing_correction + rpm_correction
        
        return max(egt, 200.0)  # Minimum 200°C
    
    def calculate_volumetric_efficiency(self, rpm: float, 
                                      boost_psi: float, 
                                      intake_temp_c: float) -> float:
        """
        Calculate volumetric efficiency
        Accounts for valve timing, intake tuning, and boost
        """
        # Base VE curve for DISI engine
        base_ve = 0.85 + 0.1 * math.exp(-((rpm - 4000) / 2000) ** 2)
        
        # Boost correction
        boost_ratio = boost_psi / 14.7
        boost_correction = 1.0 + (boost_ratio - 1.0) * 0.05
        
        # Temperature correction
        temp_correction = math.sqrt((intake_temp_c + 273.15) / 298.15)
        
        # Calculate VE
        ve = base_ve * boost_correction / temp_correction
        
        return min(max(ve, 0.5), 1.15)  # Clamp between 50% and 115%
    
    def calculate_indicated_mean_effective_pressure(self, 
                                                  peak_pressure_bar: float, 
                                                  compression_ratio: float) -> float:
        """
        Calculate indicated mean effective pressure (IMEP)
        Formula: IMEP = (Peak Pressure × (2π/Stroke)) × Efficiency Factor
        """
        # Simplified model based on peak pressure
        imep = peak_pressure_bar * 0.8  # Empirical factor
        
        return imep
    
    def calculate_brake_mean_effective_pressure(self, 
                                              imep: float, 
                                              rpm: float) -> float:
        """
        Calculate brake mean effective pressure (BMEP)
        Accounts for mechanical losses
        """
        # Friction mean effective pressure (FMEP)
        fmep = 0.5 + (rpm / 1000.0) * 0.2  # bar, increases with RPM
        
        # Mechanical efficiency
        mechanical_efficiency = 1.0 - (fmep / imep) if imep > 0 else 0.7
        mechanical_efficiency = max(mechanical_efficiency, 0.7)
        
        # BMEP = IMEP × ηm
        bmep = imep * mechanical_efficiency
        
        return bmep
    
    def calculate_fuel_flow_rate(self, injector_flow_cc_min: float, 
                               duty_cycle: float, 
                               fuel_pressure_psi: float) -> float:
        """
        Calculate fuel flow rate from injector parameters
        """
        # Correct for fuel pressure
        pressure_correction = math.sqrt(fuel_pressure_psi / 43.5)  # 43.5 psi base
        
        # Actual flow
        actual_flow = injector_flow_cc_min * duty_cycle / 100.0 * pressure_correction
        
        # Convert to kg/s (gasoline density ~0.75 g/cc)
        flow_rate_kg_s = (actual_flow * 0.75) / 60000.0
        
        return flow_rate_kg_s
    
    def calculate_dynamic_compression_ratio(self, 
                                          static_cr: float, 
                                          intake_valve_close_angle: float) -> float:
        """
        Calculate dynamic compression ratio
        Accounts for intake valve closing timing
        """
        # Effective stroke reduction factor
        # Based on intake valve closing angle
        if intake_valve_close_angle < 30:
            ivc_factor = 1.0
        elif intake_valve_close_angle < 60:
            ivc_factor = 0.95
        elif intake_valve_close_angle < 90:
            ivc_factor = 0.85
        else:
            ivc_factor = 0.75
        
        # Dynamic CR
        dynamic_cr = static_cr * ivc_factor
        
        return dynamic_cr

class TuningSecrets:
    """
    Proprietary tuning secrets and techniques
    Contains advanced methods for performance optimization
    """
    
    def __init__(self):
        self.secrets = {
            'faster_spool': {
                'description': 'Techniques to reduce turbo lag',
                'methods': [
                    'Optimized exhaust manifold design',
                    'Reduced exhaust backpressure',
                    'Advanced ignition timing during spool',
                    'Precise wastegate control',
                    'Cold air intake optimization'
                ]
            },
            'vvt_optimization': {
                'description': 'Variable Valve Timing tuning strategies',
                'methods': [
                    'Intake cam advance for low-end torque',
                    'Exhaust cam retard for scavenging',
                    'Split-overlap tuning for mid-range',
                    'High-RPM retard for peak power',
                    'Transient response optimization'
                ]
            },
            'knock_management': {
                'description': 'Advanced knock detection and control',
                'methods': [
                    'Real-time knock intensity analysis',
                    'Adaptive timing retard strategies',
                    'Cylinder-specific knock control',
                    'Fuel quality compensation',
                    'Temperature-based knock prediction'
                ]
            },
            'boost_taper': {
                'description': 'Optimal boost taper curves',
                'methods': [
                    'Progressive boost reduction at high RPM',
                'Torque-based boost limiting',
                'Gear-dependent boost curves',
                'Temperature-compensated boost',
                'Altitude-based boost adjustment'
            ]
            },
            'direct_injection_fueling': {
                'description': 'DI-specific fueling strategies',
                'methods': [
                    'Multiple injection events',
                    'Pilot injection for stability',
                    'Post-injection for emissions',
                    'Fuel spray targeting optimization',
                    'Wall wetting compensation'
                ]
            }
        }
    
    def apply_faster_spool_technique(self, current_rpm: float, 
                                    target_boost: float, 
                                    current_boost: float) -> Dict:
        """
        Apply faster spool techniques
        Returns recommended adjustments
        """
        adjustments = {}
        
        # Spool phase detection
        if current_rpm < 3000 and current_boost < target_boost * 0.5:
            # Early spool phase
            adjustments['ignition_timing'] = -5.0  # Retard for exhaust energy
            adjustments['fuel_enrichment'] = 1.5    # Enrich for cooling
            adjustments['wastegate'] = 0           # Keep wastegate closed
            adjustments['vvt_intake'] = 8.0        # Advance intake cam
            adjustments['vvt_exhaust'] = 5.0       # Retard exhaust cam
            
        elif current_rpm < 4000 and current_boost < target_boost * 0.8:
            # Mid spool phase
            adjustments['ignition_timing'] = -3.0
            adjustments['fuel_enrichment'] = 1.0
            adjustments['wastegate'] = 10          # Slight opening for control
            adjustments['vvt_intake'] = 5.0
            adjustments['vvt_exhaust'] = 3.0
        
        return adjustments
    
    def apply_vvt_optimization(self, rpm: float, load: float) -> Dict:
        """
        Apply VVT optimization based on RPM and load
        """
        if rpm < 2500:
            # Low RPM torque optimization
            return {
                'intake_cam': 12.0,  # degrees advance
                'exhaust_cam': 8.0,   # degrees retard
                'overlap': 15.0       # degrees overlap
            }
        elif 2500 <= rpm < 4500:
            # Mid-range power
            return {
                'intake_cam': 8.0,
                'exhaust_cam': 4.0,
                'overlap': 10.0
            }
        else:
            # High RPM peak power
            return {
                'intake_cam': -2.0,  # Slight retard
                'exhaust_cam': 0.0,
                'overlap': 5.0
            }
    
    def apply_knock_management(self, knock_retard: float, 
                             cylinder_temps: list) -> Dict:
        """
        Apply knock management strategies
        """
        if knock_retard < -0.5:
            # Knock detected
            severity = abs(knock_retard)
            
            if severity < 2.0:
                # Mild knock
                return {
                    'timing_retard': -1.0,
                    'fuel_enrichment': 0.5,
                    'boost_reduction': -1.0
                }
            elif severity < 4.0:
                # Moderate knock
                return {
                    'timing_retard': -2.5,
                    'fuel_enrichment': 1.0,
                    'boost_reduction': -2.0
                }
            else:
                # Severe knock
                return {
                    'timing_retard': -5.0,
                    'fuel_enrichment': 2.0,
                    'boost_reduction': -4.0,
                    'boost_limit': 10.0
                }
        
        return {}  # No adjustment needed
    
    def calculate_boost_taper(self, rpm: float, base_boost: float) -> float:
        """
        Calculate optimal boost taper for given RPM
        """
        # Start tapering at 5500 RPM
        if rpm < 5500:
            return base_boost
        
        # Progressive taper
        taper_rate = (rpm - 5500) / 1000.0  # RPM in thousands above 5500
        boost_reduction = taper_rate * 2.0  # 2 PSI per 1000 RPM
        
        tapered_boost = base_boost - boost_reduction
        
        # Minimum boost
        return max(tapered_boost, 10.0)
    
    def optimize_direct_injection(self, rpm: float, load: float, 
                                afr_target: float) -> Dict:
        """
        Optimize direct injection strategy
        """
        injection_strategy = {}
        
        if rpm < 3000:
            # Low RPM - single injection
            injection_strategy['injection_events'] = 1
            injection_strategy['pilot_injection'] = 0
            injection_strategy['post_injection'] = 0
            injection_strategy['timing'] = 300  # BTDC
            
        elif 3000 <= rpm < 5000:
            # Mid RPM - pilot + main
            injection_strategy['injection_events'] = 2
            injection_strategy['pilot_injection'] = 5  # % of total
            injection_strategy['post_injection'] = 0
            injection_strategy['timing'] = 280
            
        else:
            # High RPM - triple injection
            injection_strategy['injection_events'] = 3
            injection_strategy['pilot_injection'] = 5
            injection_strategy['post_injection'] = 10  # % of total
            injection_strategy['timing'] = 260
        
        # Adjust for load
        if load > 0.8:
            injection_strategy['fuel_pressure'] = 2000  # bar
        else:
            injection_strategy['fuel_pressure'] = 1500  # bar
        
        return injection_strategy
    
    def get_secret_technique(self, technique_name: str) -> Optional[Dict]:
        """
        Get details of a specific secret technique
        """
        return self.secrets.get(technique_name)
    
    def list_all_secrets(self) -> Dict:
        """
        List all available secret techniques
        """
        return self.secrets
