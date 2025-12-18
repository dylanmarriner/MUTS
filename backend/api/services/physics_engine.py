#!/usr/bin/env python3
"""
ADVANCED PHYSICS ENGINE FOR MAZDASPEED 3 TUNING
Implements accurate performance prediction and thermodynamic calculations
"""

import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, Tuple, Optional
import math

class TurbochargerPhysics:
    """Advanced turbocharger thermodynamics model"""
    
    def __init__(self):
        # K04 turbocharger specifications
        self.turbo_specs = {
            'compressor_wheel_diameter': 0.0445,  # m
            'turbine_wheel_diameter': 0.054,    # m
            'compressor_efficiency_max': 0.78,
            'turbine_efficiency_max': 0.75,
            'moment_of_inertia': 8.7e-5,         # kg·m²
            'max_speed': 220000,                 # RPM
            'pressure_ratio_max': 2.8
        }
        
        # Air properties
        self.air_properties = {
            'gamma': 1.4,           # Specific heat ratio
            'R': 287.05,            # Gas constant J/(kg·K)
            'cp': 1005.0,           # Specific heat J/(kg·K)
            'cv': 718.0             # Specific heat at constant volume
        }
    
    def calculate_airflow(self, rpm: float, boost_psi: float, temp_c: float) -> float:
        """Calculate mass airflow through engine"""
        # Convert units
        boost_pa = boost_psi * 6894.76  # PSI to Pa
        temp_k = temp_c + 273.15        # Celsius to Kelvin
        
        # Engine parameters (2.3L DISI)
        displacement = 0.0023  # m³
        volumetric_efficiency = self._calculate_volumetric_efficiency(rpm, boost_psi)
        
        # Calculate airflow
        cycles_per_rev = rpm / 120.0  # 4-stroke engine
        cylinder_fill = displacement * volumetric_efficiency
        
        # Air density at manifold conditions
        manifold_pressure = 101325 + boost_pa  # Pa
        air_density = manifold_pressure / (self.air_properties['R'] * temp_k)
        
        # Mass flow rate (kg/s)
        mass_flow = cylinder_fill * air_density * cycles_per_rev
        
        return mass_flow
    
    def _calculate_volumetric_efficiency(self, rpm: float, boost_psi: float) -> float:
        """Calculate volumetric efficiency based on RPM and boost"""
        # Base VE curve for DISI engine
        base_ve = 0.85 + 0.1 * np.exp(-((rpm - 4000) / 2000) ** 2)
        
        # Boost correction
        boost_correction = 1.0 + (boost_psi / 14.7) * 0.05
        
        return min(base_ve * boost_correction, 1.0)
    
    def calculate_compressor_power(self, mass_flow: float, pressure_ratio: float, 
                                 efficiency: float = None) -> float:
        """Calculate compressor power requirement"""
        if efficiency is None:
            efficiency = self._calculate_compressor_efficiency(pressure_ratio, mass_flow)
        
        # Isentropic compression
        gamma = self.air_properties['gamma']
        T1 = 298.15  # Inlet temperature (K)
        
        # Ideal work
        work_ideal = (gamma / (gamma - 1)) * self.air_properties['R'] * T1 * \
                    ((pressure_ratio ** ((gamma - 1) / gamma)) - 1)
        
        # Actual work accounting for efficiency
        work_actual = work_ideal / efficiency
        
        # Power (W)
        power = mass_flow * work_actual
        
        return power
    
    def _calculate_compressor_efficiency(self, pressure_ratio: float, mass_flow: float) -> float:
        """Calculate compressor efficiency at operating point"""
        # Simplified efficiency map
        optimal_pr = 2.0
        optimal_flow = 0.1
        
        # Efficiency drops off from optimal point
        pr_factor = np.exp(-((pressure_ratio - optimal_pr) / 1.0) ** 2)
        flow_factor = np.exp(-((mass_flow - optimal_flow) / 0.05) ** 2)
        
        efficiency = self.turbo_specs['compressor_efficiency_max'] * pr_factor * flow_factor
        
        return max(efficiency, 0.5)  # Minimum 50% efficiency
    
    def calculate_turbine_power(self, exhaust_flow: float, exhaust_temp: float,
                              pressure_ratio: float) -> float:
        """Calculate turbine power output"""
        gamma = self.air_properties['gamma']
        
        # Turbine efficiency (simplified model)
        efficiency = self._calculate_turbine_efficiency(pressure_ratio, exhaust_flow)
        
        # Isentropic expansion work
        work_ideal = (gamma / (gamma - 1)) * self.air_properties['R'] * exhaust_temp * \
                    (1 - (1 / pressure_ratio) ** ((gamma - 1) / gamma))
        
        # Actual work
        work_actual = work_ideal * efficiency
        
        # Power (W)
        power = exhaust_flow * work_actual
        
        return power
    
    def _calculate_turbine_efficiency(self, pressure_ratio: float, exhaust_flow: float) -> float:
        """Calculate turbine efficiency at operating point"""
        # Velocity ratio optimization
        optimal_velocity_ratio = 0.65
        
        # Simplified model
        efficiency = self.turbo_specs['turbine_efficiency_max'] * \
                    (1 - 2 * (pressure_ratio - optimal_velocity_ratio) ** 2)
        
        return max(efficiency, 0.4)  # Minimum 40% efficiency
    
    def calculate_spool_time(self, current_rpm: float, target_rpm: float,
                           exhaust_energy: float) -> float:
        """Calculate turbo spool time using differential equations"""
        
        def spool_dynamics(t, y):
            """Differential equation for turbo spool"""
            omega = y[0]  # Angular velocity (rad/s)
            
            # Torque from turbine
            turbine_torque = exhaust_energy / (omega + 1)  # Avoid division by zero
            
            # Friction losses
            friction_torque = 0.001 * omega ** 2
            
            # Net torque
            net_torque = turbine_torque - friction_torque
            
            # Angular acceleration
            alpha = net_torque / self.turbo_specs['moment_of_inertia']
            
            return [alpha]
        
        # Initial conditions
        omega_0 = current_rpm * 2 * np.pi / 60
        omega_target = target_rpm * 2 * np.pi / 60
        
        # Solve ODE
        sol = solve_ivp(spool_dynamics, [0, 5], [omega_0], 
                       dense_output=True, max_step=0.01)
        
        # Find time to reach target
        for i, t in enumerate(sol.t):
            if sol.y[0][i] >= omega_target:
                return t
        
        return 5.0  # Max 5 seconds if not reached

class EngineThermodynamics:
    """Engine thermodynamic calculations for performance prediction"""
    
    def __init__(self):
        # Engine specifications
        self.engine_specs = {
            'displacement': 0.0023,    # m³ (2.3L)
            'bore': 0.0875,           # m
            'stroke': 0.094,          # m
            'compression_ratio': 9.5,
            'connecting_rod_length': 0.150,  # m
            'num_cylinders': 4
        }
        
        # Fuel properties (gasoline)
        self.fuel_properties = {
            'lower_heating_value': 44.4e6,  # J/kg
            'stoichiometric_afr': 14.7,
            'density': 750.0,               # kg/m³
            'specific_heat': 2000.0         # J/(kg·K)
        }
    
    def calculate_brake_torque(self, rpm: float, bmep: float) -> float:
        """Calculate brake torque from BMEP"""
        # BMEP to torque conversion
        displacement = self.engine_specs['displacement']
        torque = (bmep * displacement) / (4 * np.pi)  # N·m
        
        return torque
    
    def calculate_indicated_power(self, rpm: float, imep: float) -> float:
        """Calculate indicated power from IMEP"""
        displacement = self.engine_specs['displacement']
        power = (imep * displacement * rpm) / (120 * 1000)  # kW
        
        return power
    
    def calculate_exhaust_temperature(self, rpm: float, load: float, 
                                    afr: float, ignition_timing: float) -> float:
        """Calculate exhaust gas temperature"""
        # Base exhaust temperature
        base_temp = 450.0  # °C
        
        # Load factor
        load_factor = min(load / 1.0, 1.0)
        
        # AFR correction (leaner = hotter)
        afr_correction = (14.7 - afr) * 50.0
        
        # Timing correction (retarded = hotter)
        timing_correction = (20.0 - ignition_timing) * 10.0
        
        # RPM correction
        rpm_correction = (rpm - 2000) / 1000.0 * 20.0
        
        # Calculate final temperature
        exhaust_temp = base_temp + (load_factor * 300.0) + \
                      afr_correction + timing_correction + rpm_correction
        
        return max(exhaust_temp, 200.0)  # Minimum 200°C
    
    def calculate_pumping_losses(self, rpm: float, boost_psi: float) -> float:
        """Calculate pumping losses (kW)"""
        # Simplified pumping loss model
        base_loss = 0.5 + (rpm / 1000.0) * 0.5  # kW
        
        # Boost penalty
        boost_penalty = boost_psi * 0.1  # kW per PSI
        
        total_loss = base_loss + boost_penalty
        
        return total_loss
    
    def calculate_friction_losses(self, rpm: float) -> float:
        """Calculate friction losses (kW)"""
        # Friction increases with RPM squared
        friction_coefficient = 0.00001
        
        friction_loss = friction_coefficient * (rpm ** 2) / 1000.0  # kW
        
        return friction_loss
    
    def calculate_thermal_efficiency(self, rpm: float, load: float, 
                                   afr: float, ignition_timing: float) -> float:
        """Calculate brake thermal efficiency"""
        # Base efficiency
        base_efficiency = 0.35
        
        # Load factor
        load_factor = min(load / 1.0, 1.0)
        load_bonus = load_factor * 0.1
        
        # AFR optimization
        if 12.5 <= afr <= 13.5:
            afr_bonus = 0.02
        elif 12.0 <= afr <= 14.0:
            afr_bonus = 0.01
        else:
            afr_bonus = -0.02
        
        # Timing optimization
        optimal_timing = 15.0 + (rpm - 3000) / 1000.0 * 2.0
        timing_error = abs(ignition_timing - optimal_timing)
        timing_penalty = timing_error * 0.001
        
        # Calculate efficiency
        efficiency = base_efficiency + load_bonus + afr_bonus - timing_penalty
        
        return max(min(efficiency, 0.45), 0.20)  # Clamp between 20% and 45%

class PerformanceCalculator:
    """High-level performance calculations"""
    
    def __init__(self):
        self.turbo = TurbochargerPhysics()
        self.engine = EngineThermodynamics()
    
    def calculate_power_curve(self, rpm_range: Tuple[int, int], 
                           boost_map: Dict, afr_map: Dict, 
                           timing_map: Dict) -> Dict:
        """Calculate complete power curve"""
        results = {
            'rpm': [],
            'torque': [],
            'power': [],
            'boost': [],
            'exhaust_temp': [],
            'efficiency': []
        }
        
        for rpm in range(rpm_range[0], rpm_range[1], 100):
            # Get operating point values
            boost = self._interpolate_map(boost_map, rpm, 1.0)
            afr = self._interpolate_map(afr_map, rpm, 1.0)
            timing = self._interpolate_map(timing_map, rpm, 1.0)
            
            # Calculate performance
            airflow = self.turbo.calculate_airflow(rpm, boost, 25.0)
            
            # Estimate BMEP from airflow and AFR
            bmep = self._calculate_bmep_from_airflow(airflow, afr)
            
            torque = self.engine.calculate_brake_torque(rpm, bmep)
            power = torque * rpm / 9549.296  # Convert to HP
            
            exhaust_temp = self.engine.calculate_exhaust_temperature(rpm, 1.0, afr, timing)
            efficiency = self.engine.calculate_thermal_efficiency(rpm, 1.0, afr, timing)
            
            # Store results
            results['rpm'].append(rpm)
            results['torque'].append(torque)
            results['power'].append(power)
            results['boost'].append(boost)
            results['exhaust_temp'].append(exhaust_temp)
            results['efficiency'].append(efficiency)
        
        return results
    
    def _interpolate_map(self, map_data: Dict, rpm: float, load: float) -> float:
        """Interpolate value from 2D map"""
        # Simplified interpolation - would use proper 2D interpolation in reality
        rpm_points = sorted(map_data.keys())
        
        # Find surrounding RPM points
        for i in range(len(rpm_points) - 1):
            if rpm_points[i] <= rpm <= rpm_points[i + 1]:
                # Linear interpolation
                t = (rpm - rpm_points[i]) / (rpm_points[i + 1] - rpm_points[i])
                value1 = map_data[rpm_points[i]]
                value2 = map_data[rpm_points[i + 1]]
                return value1 + t * (value2 - value1)
        
        # Return nearest value if outside range
        if rpm < rpm_points[0]:
            return map_data[rpm_points[0]]
        else:
            return map_data[rpm_points[-1]]
    
    def _calculate_bmep_from_airflow(self, airflow: float, afr: float) -> float:
        """Estimate BMEP from airflow and AFR"""
        # Simplified model
        # More air = more potential power
        # AFR affects combustion efficiency
        
        # Normalize airflow
        max_airflow = 0.2  # kg/s at peak
        airflow_factor = min(airflow / max_airflow, 1.0)
        
        # AFR factor
        if afr >= 14.7:
            afr_factor = 14.7 / afr  # Lean penalty
        else:
            afr_factor = 1.0 - (14.7 - afr) * 0.05  # Rich penalty
        
        # Calculate BMEP (bar)
        bmep = 20.0 * airflow_factor * afr_factor
        
        return bmep
