#!/usr/bin/env python3
"""
COMPLETE ENGINE PHYSICAL MODELS FOR MAZDASPEED 3
Ideal gas physics, turbocharger dynamics, and engine cycle analysis
"""

import numpy as np
from scipy.interpolate import interp1d
from typing import Dict, Tuple, Optional
import math

class IdealGasPhysics:
    """
    Ideal gas law calculations for engine modeling
    Provides accurate thermodynamic properties
    """
    
    def __init__(self):
        # Universal gas constant
        self.R_universal = 8.314462618  # J/(mol·K)
        
        # Air properties
        self.air_molar_mass = 0.0289647  # kg/mol
        self.R_air = self.R_universal / self.air_molar_mass  # 287.058 J/(kg·K)
        
        # Specific heat ratios
        self.gamma_air = 1.4  # Diatomic gas
        self.cp_air = 1005.0   # J/(kg·K)
        self.cv_air = 717.18   # J/(kg·K)
        
        # Standard conditions
        self.P_standard = 101325  # Pa
        self.T_standard = 298.15  # K (25°C)
    
    def calculate_gas_velocity(self, pressure_ratio: float, 
                             inlet_temp: float, outlet_temp: float) -> float:
        """
        Calculate gas velocity through restriction using isentropic flow
        Returns velocity in m/s
        """
        gamma = self.gamma_air
        
        # Isentropic flow equation
        # v = sqrt(2 * gamma / (gamma - 1) * R * T * (1 - (P2/P1)^((gamma-1)/gamma)))
        
        term1 = (2 * gamma / (gamma - 1)) * self.R_air * inlet_temp
        term2 = 1 - pressure_ratio ** ((gamma - 1) / gamma)
        
        velocity = math.sqrt(term1 * term2)
        
        return velocity
    
    def calculate_mass_flow_rate(self, pressure: float, temperature: float,
                               area: float, mach_number: float = 0.5) -> float:
        """
        Calculate mass flow rate through an orifice
        Returns mass flow in kg/s
        """
        # Density from ideal gas law
        density = pressure / (self.R_air * temperature)
        
        # Velocity from Mach number
        sound_speed = math.sqrt(self.gamma_air * self.R_air * temperature)
        velocity = mach_number * sound_speed
        
        # Mass flow rate
        mass_flow = density * velocity * area
        
        return mass_flow
    
    def calculate_pressure_ratio(self, inlet_pressure: float, 
                               outlet_pressure: float) -> float:
        """Calculate pressure ratio"""
        return outlet_pressure / inlet_pressure
    
    def calculate_temperature_ratio(self, inlet_temp: float, 
                                  outlet_temp: float) -> float:
        """Calculate temperature ratio"""
        return outlet_temp / inlet_temp
    
    def calculate_isentropic_work(self, pressure_ratio: float, 
                                inlet_temp: float, mass_flow: float) -> float:
        """
        Calculate isentropic work of compression/expansion
        Returns work in Watts
        """
        gamma = self.gamma_air
        
        # Isentropic work per unit mass
        work_per_kg = (gamma / (gamma - 1)) * self.R_air * inlet_temp * \
                     ((pressure_ratio ** ((gamma - 1) / gamma)) - 1)
        
        # Total work
        total_work = mass_flow * work_per_kg
        
        return total_work
    
    def calculate_density(self, pressure: float, temperature: float) -> float:
        """Calculate gas density from ideal gas law"""
        return pressure / (self.R_air * temperature)
    
    def calculate_dynamic_pressure(self, velocity: float, density: float) -> float:
        """Calculate dynamic pressure"""
        return 0.5 * density * velocity ** 2
    
    def calculate_reynolds_number(self, velocity: float, 
                                characteristic_length: float,
                                density: float, viscosity: float) -> float:
        """Calculate Reynolds number for flow analysis"""
        return (density * velocity * characteristic_length) / viscosity

class TurbochargerDynamics:
    """
    Complete turbocharger dynamics model
    Includes compressor and turbine physics
    """
    
    def __init__(self):
        # K04 turbocharger specifications
        self.specs = {
            'compressor': {
                'inducer_diameter': 0.0445,  # m
                'exducer_diameter': 0.060,    # m
                'trim': 56.0,
                'max_efficiency': 0.78,
                'max_pressure_ratio': 2.8,
                'max_flow': 0.18,             # kg/s
                'surge_margin': 0.15
            },
            'turbine': {
                'inducer_diameter': 0.054,    # m
                'exducer_diameter': 0.044,    # m
                'trim': 66.0,
                'max_efficiency': 0.75,
                'A_R': 0.64,                  # Area/Radius ratio
                'max_temp': 1050,              # °C
                'moment_of_inertia': 8.7e-5    # kg·m²
            },
            'mechanical': {
                'max_speed': 220000,           # RPM
                'bearing_type': 'journal',
                'oil_pressure_min': 30,        # PSI
                'oil_temp_max': 120            # °C
            }
        }
        
        # Performance maps (simplified)
        self.compressor_map = self._create_compressor_map()
        self.turbine_map = self._create_turbine_map()
        
        # Dynamic state
        self.state = {
            'speed_rpm': 0,
            'speed_rad_s': 0,
            'acceleration': 0,
            'power_compressor': 0,
            'power_turbine': 0,
            'efficiency_compressor': 0,
            'efficiency_turbine': 0
        }
    
    def _create_compressor_map(self) -> Dict:
        """Create simplified compressor performance map"""
        # Pressure ratio vs corrected flow at various speeds
        return {
            'speed_lines': {
                60000: {'pr': [1.2, 1.4, 1.6, 1.8, 2.0], 'flow': [0.02, 0.04, 0.06, 0.08, 0.10], 'eff': [0.65, 0.72, 0.75, 0.72, 0.65]},
                80000: {'pr': [1.3, 1.6, 1.9, 2.2, 2.5], 'flow': [0.03, 0.06, 0.09, 0.12, 0.15], 'eff': [0.68, 0.75, 0.78, 0.75, 0.68]},
                100000: {'pr': [1.4, 1.8, 2.2, 2.6, 2.8], 'flow': [0.04, 0.08, 0.12, 0.16, 0.18], 'eff': [0.70, 0.77, 0.78, 0.75, 0.70]},
                120000: {'pr': [1.5, 2.0, 2.5, 2.8, 2.8], 'flow': [0.05, 0.10, 0.15, 0.18, 0.18], 'eff': [0.72, 0.78, 0.78, 0.72, 0.65]},
                140000: {'pr': [1.6, 2.2, 2.8, 2.8, 2.8], 'flow': [0.06, 0.12, 0.18, 0.18, 0.18], 'eff': [0.74, 0.78, 0.75, 0.68, 0.60]}
            }
        }
    
    def _create_turbine_map(self) -> Dict:
        """Create simplified turbine performance map"""
        return {
            'efficiency_map': {
                'velocity_ratios': [0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
                'pressure_ratios': [1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
                'efficiencies': [0.60, 0.68, 0.73, 0.75, 0.72, 0.65]
            }
        }
    
    def calculate_compressor_operation(self, speed_rpm: float, 
                                    pressure_ratio: float) -> Dict:
        """Calculate compressor operating point"""
        
        # Corrected speed
        corrected_speed = speed_rpm * math.sqrt(298.15 / 288.15) / math.sqrt(101.325 / 100.0)
        
        # Find efficiency at operating point
        efficiency = self._interpolate_compressor_efficiency(
            corrected_speed, pressure_ratio
        )
        
        # Calculate power requirement
        # P = (m_dot * cp * T1 / ηc) * ((PR^((γ-1)/γ)) - 1)
        gamma = 1.4
        cp = 1005.0
        T1 = 298.15  # Inlet temperature
        
        # Estimate mass flow from speed and pressure ratio
        mass_flow = self._estimate_compressor_flow(corrected_speed, pressure_ratio)
        
        # Power calculation
        temp_ratio = pressure_ratio ** ((gamma - 1) / gamma)
        power = (mass_flow * cp * T1 / efficiency) * (temp_ratio - 1)
        
        return {
            'speed_rpm': speed_rpm,
            'pressure_ratio': pressure_ratio,
            'mass_flow': mass_flow,
            'efficiency': efficiency,
            'power_required': power,
            'outlet_temp': T1 * (1 + (temp_ratio - 1) / efficiency)
        }
    
    def calculate_turbine_operation(self, speed_rpm: float,
                                  pressure_ratio: float, inlet_temp: float) -> Dict:
        """Calculate turbine operating point"""
        
        # Velocity ratio
        # VR = U / C where U is blade speed and C is gas velocity
        blade_speed = speed_rpm * 2 * math.pi / 60 * self.specs['turbine']['inducer_diameter'] / 2
        
        # Estimate gas velocity from pressure ratio and temperature
        gamma = 1.4
        R = 287.05
        gas_velocity = math.sqrt(2 * gamma / (gamma - 1) * R * inlet_temp * 
                               (1 - (1 / pressure_ratio) ** ((gamma - 1) / gamma)))
        
        velocity_ratio = blade_speed / gas_velocity if gas_velocity > 0 else 0
        
        # Find efficiency
        efficiency = self._interpolate_turbine_efficiency(velocity_ratio, pressure_ratio)
        
        # Calculate power output
        # P = m_dot * cp * T1 * ηt * (1 - (1/PR)^((γ-1)/γ))
        mass_flow = self._estimate_turbine_flow(speed_rpm, pressure_ratio)
        
        temp_ratio = (1 / pressure_ratio) ** ((gamma - 1) / gamma)
        power = mass_flow * 1005.0 * inlet_temp * efficiency * (1 - temp_ratio)
        
        return {
            'speed_rpm': speed_rpm,
            'pressure_ratio': pressure_ratio,
            'velocity_ratio': velocity_ratio,
            'mass_flow': mass_flow,
            'efficiency': efficiency,
            'power_output': power,
            'outlet_temp': inlet_temp * (1 - efficiency * (1 - temp_ratio))
        }
    
    def calculate_spool_time(self, current_speed: float, target_speed: float,
                           exhaust_energy: float) -> float:
        """Calculate turbo spool time using energy balance"""
        
        # Moment of inertia
        J = self.specs['turbine']['moment_of_inertia']
        
        # Convert speeds to rad/s
        omega_current = current_speed * 2 * math.pi / 60
        omega_target = target_speed * 2 * math.pi / 60
        
        # Energy required
        kinetic_energy_required = 0.5 * J * (omega_target ** 2 - omega_current ** 2)
        
        # Estimate time (simplified - assumes constant power)
        if exhaust_energy > 0:
            spool_time = kinetic_energy_required / exhaust_energy
        else:
            spool_time = float('inf')
        
        return min(spool_time, 5.0)  # Cap at 5 seconds
    
    def _interpolate_compressor_efficiency(self, speed: float, 
                                         pressure_ratio: float) -> float:
        """Interpolate compressor efficiency from map"""
        # Simplified interpolation
        max_eff = self.specs['compressor']['max_efficiency']
        
        # Efficiency drops off from optimal point
        optimal_pr = 2.0
        pr_factor = math.exp(-((pressure_ratio - optimal_pr) / 1.0) ** 2)
        
        # Speed factor
        optimal_speed = 100000
        speed_factor = math.exp(-((speed - optimal_speed) / 50000) ** 2)
        
        efficiency = max_eff * pr_factor * speed_factor
        
        return max(efficiency, 0.5)  # Minimum 50% efficiency
    
    def _interpolate_turbine_efficiency(self, velocity_ratio: float,
                                       pressure_ratio: float) -> float:
        """Interpolate turbine efficiency from map"""
        max_eff = self.specs['turbine']['max_efficiency']
        
        # Optimal velocity ratio
        optimal_vr = 0.65
        
        # Efficiency curve
        efficiency = max_eff * (1 - 2 * (velocity_ratio - optimal_vr) ** 2)
        
        # Pressure ratio effect
        pr_factor = min(pressure_ratio / 2.5, 1.0)
        efficiency *= pr_factor
        
        return max(efficiency, 0.4)  # Minimum 40% efficiency
    
    def _estimate_compressor_flow(self, speed: float, pressure_ratio: float) -> float:
        """Estimate compressor mass flow"""
        # Simplified model
        max_flow = self.specs['compressor']['max_flow']
        
        # Flow increases with speed
        speed_factor = min(speed / 140000, 1.0)
        
        # Flow decreases with pressure ratio
        pr_factor = math.exp(-0.5 * (pressure_ratio - 1.0))
        
        flow = max_flow * speed_factor * pr_factor
        
        return flow
    
    def _estimate_turbine_flow(self, speed: float, pressure_ratio: float) -> float:
        """Estimate turbine mass flow"""
        # Turbine flow typically higher than compressor
        # due to temperature increase
        compressor_flow = self._estimate_compressor_flow(speed, pressure_ratio)
        
        # Temperature correction
        temp_ratio = 1.5  # Typical exhaust to inlet temp ratio
        turbine_flow = compressor_flow * math.sqrt(temp_ratio)
        
        return turbine_flow
    
    def get_turbo_state(self) -> Dict:
        """Get current turbocharger state"""
        return self.state.copy()

class EngineCycleAnalysis:
    """
    Complete engine cycle analysis for performance prediction
    Implements ideal Otto and Diesel cycles with real gas corrections
    """
    
    def __init__(self):
        # Engine specifications
        self.engine = {
            'displacement': 0.0023,    # m³ (2.3L)
            'bore': 0.0875,           # m
            'stroke': 0.094,          # m
            'compression_ratio': 9.5,
            'connecting_rod': 0.150,  # m
            'num_cylinders': 4
        }
        
        # Calculate geometric parameters
        self.engine['cylinder_volume'] = self.engine['displacement'] / self.engine['num_cylinders']
        self.engine['clearance_volume'] = self.engine['cylinder_volume'] / (self.engine['compression_ratio'] - 1)
        self.engine['total_volume'] = self.engine['cylinder_volume'] + self.engine['clearance_volume']
        
        # Gas properties
        self.gamma = 1.4
        self.R = 287.05  # J/(kg·K)
        
    def calculate_imep(self, peak_pressure: float, rpm: float) -> float:
        """
        Calculate Indicated Mean Effective Pressure (IMEP)
        Returns IMEP in bar
        """
        # Simplified IMEP calculation from peak pressure
        # IMEP ≈ (Peak Pressure - Intake Pressure) / 2
        
        intake_pressure = 101.325  # kPa (atmospheric)
        
        # Dynamic correction for RPM
        rpm_factor = 1.0 - (rpm - 3000) / 10000.0  # Efficiency drops at high RPM
        rpm_factor = max(rpm_factor, 0.7)
        
        imep = ((peak_pressure - intake_pressure) / 2.0) * rpm_factor
        
        return imep / 100  # Convert to bar
    
    def calculate_bmep(self, imep: float, rpm: float) -> float:
        """
        Calculate Brake Mean Effective Pressure (BMEP)
        Accounts for mechanical losses
        """
        # Mechanical efficiency model
        # ηm = 1 - (FMEP / IMEP)
        
        # Friction mean effective pressure (FMEP)
        fmep = 50 + (rpm / 1000.0) * 20  # kPa, increases with RPM
        
        # Mechanical efficiency
        if imep > 0:
            mechanical_efficiency = 1.0 - (fmep / (imep * 100))
            mechanical_efficiency = max(mechanical_efficiency, 0.7)
        else:
            mechanical_efficiency = 0.7
        
        # BMEP = IMEP * ηm
        bmep = imep * mechanical_efficiency
        
        return bmep
    
    def calculate_volumetric_efficiency(self, rpm: float, boost_pressure: float,
                                      intake_temp: float) -> float:
        """
        Calculate volumetric efficiency
        Accounts for valve timing, intake tuning, and boost
        """
        # Base VE curve
        base_ve = 0.85 + 0.1 * math.exp(-((rpm - 4000) / 2000) ** 2)
        
        # Boost correction
        boost_ratio = boost_pressure / 14.7
        boost_correction = 1.0 + (boost_ratio - 1.0) * 0.05
        
        # Temperature correction
        temp_correction = math.sqrt(intake_temp / 298.15)
        
        # Valve overlap effect (simplified)
        if 2000 <= rpm <= 4000:
            ve_bonus = 0.05
        else:
            ve_bonus = 0.0
        
        ve = base_ve * boost_correction / temp_correction + ve_bonus
        
        return min(max(ve, 0.5), 1.15)  # Clamp between 50% and 115%
    
    def calculate_air_charge(self, rpm: float, boost_pressure: float,
                           intake_temp: float, ve: float) -> float:
        """
        Calculate air charge per cylinder
        Returns mass in kg
        """
        # Intake manifold conditions
        manifold_pressure = 101.325 + (boost_pressure * 6.89476)  # kPa to Pa
        manifold_temp = intake_temp + 273.15  # °C to K
        
        # Air density
        air_density = manifold_pressure / (self.R * manifold_temp)
        
        # Air charge
        cylinder_volume = self.engine['cylinder_volume']
        air_charge = cylinder_volume * air_density * ve
        
        return air_charge
    
    def calculate_fuel_requirement(self, air_charge: float, target_afr: float,
                                fuel_density: float = 750.0) -> float:
        """
        Calculate fuel requirement based on air charge and target AFR
        Returns fuel mass in kg
        """
        # Air-fuel ratio
        afr = target_afr
        
        # Fuel mass
        fuel_mass = air_charge / afr
        
        # Convert to volume (cc)
        fuel_volume = (fuel_mass / fuel_density) * 1e6
        
        return fuel_mass, fuel_volume
    
    def calculate_exhaust_energy(self, exhaust_temp: float, exhaust_flow: float) -> float:
        """
        Calculate exhaust energy available for turbocharger
        Returns power in Watts
        """
        # Exhaust gas properties (approximation)
        cp_exhaust = 1100.0  # J/(kg·K)
        ambient_temp = 298.15  # K
        
        # Energy available
        delta_t = exhaust_temp - ambient_temp
        energy_rate = exhaust_flow * cp_exhaust * delta_t
        
        # Only a portion can be extracted
        extractable_energy = energy_rate * 0.7  # 70% extraction efficiency
        
        return extractable_energy
    
    def calculate_power_output(self, bmep: float, rpm: float) -> Tuple[float, float]:
        """
        Calculate power and torque from BMEP
        Returns (torque_Nm, power_kW, power_hp)
        """
        # Power = BMEP * Displacement * RPM / (120 * 1000) for kW
        power_kw = (bmep * 100 * self.engine['displacement'] * rpm) / (120 * 1000)
        
        # Torque = Power * 9549 / RPM
        torque_nm = power_kw * 9549 / rpm if rpm > 0 else 0
        
        # Convert to HP
        power_hp = power_kw * 1.34102
        
        return torque_nm, power_kw, power_hp
    
    def analyze_complete_cycle(self, rpm: float, boost_pressure: float,
                            intake_temp: float, target_afr: float,
                            ignition_timing: float) -> Dict:
        """
        Complete engine cycle analysis
        Returns comprehensive performance data
        """
        
        # Volumetric efficiency
        ve = self.calculate_volumetric_efficiency(rpm, boost_pressure, intake_temp)
        
        # Air charge
        air_charge = self.calculate_air_charge(rpm, boost_pressure, intake_temp, ve)
        
        # Fuel requirement
        fuel_mass, fuel_volume = self.calculate_fuel_requirement(air_charge, target_afr)
        
        # Peak pressure estimation
        peak_pressure = self._estimate_peak_pressure(
            boost_pressure, ve, ignition_timing, target_afr
        )
        
        # IMEP and BMEP
        imep = self.calculate_imep(peak_pressure, rpm)
        bmep = self.calculate_bmep(imep, rpm)
        
        # Power output
        torque, power_kw, power_hp = self.calculate_power_output(bmep, rpm)
        
        # Exhaust conditions
        exhaust_temp = self._estimate_exhaust_temp(
            peak_pressure, ignition_timing, target_afr, rpm
        )
        exhaust_flow = air_charge + fuel_mass
        
        # Exhaust energy
        exhaust_energy = self.calculate_exhaust_energy(exhaust_temp, exhaust_flow)
        
        return {
            'rpm': rpm,
            'boost_pressure': boost_pressure,
            'intake_temp': intake_temp,
            'volumetric_efficiency': ve,
            'air_charge': air_charge,
            'fuel_mass': fuel_mass,
            'fuel_volume': fuel_volume,
            'peak_pressure': peak_pressure,
            'imep': imep,
            'bmep': bmep,
            'torque_nm': torque,
            'power_kw': power_kw,
            'power_hp': power_hp,
            'exhaust_temp': exhaust_temp,
            'exhaust_flow': exhaust_flow,
            'exhaust_energy': exhaust_energy,
            'thermal_efficiency': self._calculate_thermal_efficiency(power_kw, fuel_mass)
        }
    
    def _estimate_peak_pressure(self, boost_pressure: float, ve: float,
                              ignition_timing: float, afr: float) -> float:
        """Estimate peak cylinder pressure"""
        # Base pressure from boost
        base_pressure = 101.325 + (boost_pressure * 6.89476)  # kPa
        
        # Compression effect
        compression_factor = self.engine['compression_ratio'] ** self.gamma
        
        # Combustion pressure addition
        # Optimal timing gives maximum pressure
        optimal_timing = 15.0 + (boost_pressure * 0.5)
        timing_error = abs(ignition_timing - optimal_timing)
        timing_factor = math.exp(-timing_error / 10.0)
        
        # AFR effect
        afr_factor = 1.0
        if 12.5 <= afr <= 13.5:
            afr_factor = 1.1  # Peak power mixture
        elif afr < 12.0:
            afr_factor = 0.9  # Rich mixture
        elif afr > 14.0:
            afr_factor = 0.85  # Lean mixture
        
        # Calculate peak pressure
        peak_pressure = base_pressure * compression_factor * timing_factor * afr_factor * ve
        
        return peak_pressure
    
    def _estimate_exhaust_temp(self, peak_pressure: float, ignition_timing: float,
                             afr: float, rpm: float) -> float:
        """Estimate exhaust gas temperature in Kelvin"""
        # Base exhaust temperature
        base_temp = 773.15  # 500°C
        
        # Pressure effect
        pressure_factor = (peak_pressure / 5000.0) ** 0.5
        
        # Timing effect
        timing_factor = 1.0 + (20.0 - ignition_timing) * 0.02
        
        # AFR effect
        afr_factor = 1.0 + (14.7 - afr) * 20.0
        
        # RPM effect
        rpm_factor = 1.0 + (rpm - 3000) / 1000.0 * 0.1
        
        exhaust_temp = base_temp * pressure_factor * timing_factor * afr_factor * rpm_factor
        
        return exhaust_temp
    
    def _calculate_thermal_efficiency(self, power_kw: float, fuel_mass: float) -> float:
        """Calculate brake thermal efficiency"""
        # Fuel energy (gasoline LHV)
        fuel_energy = fuel_mass * 44.4e6  # J
        
        # Efficiency
        if fuel_energy > 0:
            efficiency = (power_kw * 1000) / fuel_energy
        else:
            efficiency = 0
        
        return efficiency
