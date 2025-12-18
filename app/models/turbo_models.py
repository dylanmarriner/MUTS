#!/usr/bin/env python3
"""
K04 TURBOCHARGER SPECIFIC MODELS AND CALCULATIONS
Detailed compressor and turbine maps for K04 turbo
"""

import numpy as np
from scipy.interpolate import interp1d, interp2d
from typing import Dict, Tuple, List, Optional
import math

class K04CompressorMap:
    """
    K04 compressor performance map
    Provides accurate efficiency and flow predictions
    """
    
    def __init__(self):
        # K04 compressor specifications
        self.specs = {
            'wheel_diameter_inducer': 0.0445,  # m
            'wheel_diameter_exducer': 0.060,    # m
            'trim': 56.0,
            'A_R': 0.50,
            'max_efficiency': 0.78,
            'max_pressure_ratio': 2.8,
            'surge_line_margin': 0.10
        }
        
        # Compressor map data (speed lines)
        # Each speed line has: [corrected_flow, pressure_ratio, efficiency]
        self.map_data = {
            # Speed in RPM, corrected flow in kg/s, PR, efficiency
            60000: {
                'corrected_flow': np.array([0.02, 0.04, 0.06, 0.08, 0.10]),
                'pressure_ratio': np.array([1.2, 1.4, 1.6, 1.8, 2.0]),
                'efficiency': np.array([0.65, 0.72, 0.75, 0.72, 0.65])
            },
            80000: {
                'corrected_flow': np.array([0.03, 0.06, 0.09, 0.12, 0.15]),
                'pressure_ratio': np.array([1.3, 1.6, 1.9, 2.2, 2.5]),
                'efficiency': np.array([0.68, 0.75, 0.78, 0.75, 0.68])
            },
            100000: {
                'corrected_flow': np.array([0.04, 0.08, 0.12, 0.16, 0.18]),
                'pressure_ratio': np.array([1.4, 1.8, 2.2, 2.6, 2.8]),
                'efficiency': np.array([0.70, 0.77, 0.78, 0.75, 0.70])
            },
            120000: {
                'corrected_flow': np.array([0.05, 0.10, 0.15, 0.18, 0.18]),
                'pressure_ratio': np.array([1.5, 2.0, 2.5, 2.8, 2.8]),
                'efficiency': np.array([0.72, 0.78, 0.78, 0.72, 0.65])
            },
            140000: {
                'corrected_flow': np.array([0.06, 0.12, 0.18, 0.18, 0.18]),
                'pressure_ratio': np.array([1.6, 2.2, 2.8, 2.8, 2.8]),
                'efficiency': np.array([0.74, 0.78, 0.75, 0.68, 0.60])
            }
        }
        
        # Create interpolation functions
        self._create_interpolators()
        
        # Surge line (simplified)
        self.surge_line = self._create_surge_line()
    
    def _create_interpolators(self):
        """Create 2D interpolation functions for efficiency and PR"""
        # Collect all data points
        all_flows = []
        all_speeds = []
        all_pr = []
        all_eff = []
        
        for speed, data in self.map_data.items():
            for i in range(len(data['corrected_flow'])):
                all_flows.append(data['corrected_flow'][i])
                all_speeds.append(speed)
                all_pr.append(data['pressure_ratio'][i])
                all_eff.append(data['efficiency'][i])
        
        # Create interpolators
        self.efficiency_interp = interp2d(all_flows, all_speeds, all_eff, 
                                         kind='linear', bounds_error=False, 
                                         fill_value=0.5)
        self.pr_interp = interp2d(all_flows, all_speeds, all_pr, 
                                 kind='linear', bounds_error=False, 
                                 fill_value=1.0)
    
    def _create_surge_line(self) -> Dict:
        """Create surge line data"""
        # Simplified surge line
        return {
            'corrected_flow': np.array([0.02, 0.04, 0.06, 0.08, 0.10]),
            'pressure_ratio': np.array([1.8, 2.0, 2.2, 2.4, 2.6])
        }
    
    def get_operating_point(self, corrected_speed: float, 
                          corrected_flow: float) -> Dict:
        """Get operating point on compressor map"""
        
        # Check if within map bounds
        min_speed = min(self.map_data.keys())
        max_speed = max(self.map_data.keys())
        
        if corrected_speed < min_speed:
            corrected_speed = min_speed
        elif corrected_speed > max_speed:
            corrected_speed = max_speed
        
        # Get efficiency and pressure ratio
        efficiency = float(self.efficiency_interp(corrected_flow, corrected_speed))
        pressure_ratio = float(self.pr_interp(corrected_flow, corrected_speed))
        
        # Check for surge
        surge_pr = self._get_surge_pr(corrected_flow)
        is_surge = pressure_ratio < surge_pr * (1 - self.specs['surge_line_margin'])
        
        # Check for choke (simplified)
        max_flow = 0.18  # kg/s for K04
        is_choke = corrected_flow > max_flow
        
        return {
            'corrected_speed': corrected_speed,
            'corrected_flow': corrected_flow,
            'pressure_ratio': pressure_ratio,
            'efficiency': efficiency,
            'is_surge': is_surge,
            'is_choke': is_choke,
            'surge_margin': (pressure_ratio - surge_pr) / surge_pr if surge_pr > 0 else 0
        }
    
    def _get_surge_pr(self, corrected_flow: float) -> float:
        """Get surge pressure ratio for given flow"""
        # Linear interpolation on surge line
        surge_flows = self.surge_line['corrected_flow']
        surge_prs = self.surge_line['pressure_ratio']
        
        if corrected_flow <= surge_flows[0]:
            return surge_prs[0]
        elif corrected_flow >= surge_flows[-1]:
            return surge_prs[-1]
        
        # Interpolate
        for i in range(len(surge_flows) - 1):
            if surge_flows[i] <= corrected_flow <= surge_flows[i + 1]:
                t = (corrected_flow - surge_flows[i]) / (surge_flows[i + 1] - surge_flows[i])
                return surge_prs[i] + t * (surge_prs[i + 1] - surge_prs[i])
        
        return 2.0  # Default

class K04TurbineMap:
    """
    K04 turbine performance map
    Provides efficiency and flow characteristics
    """
    
    def __init__(self):
        # K04 turbine specifications
        self.specs = {
            'wheel_diameter_inducer': 0.054,  # m
            'wheel_diameter_exducer': 0.044,    # m
            'trim': 66.0,
            'A_R': 0.64,
            'max_efficiency': 0.75,
            'max_temp': 1050,      # °C
            'moment_of_inertia': 8.7e-5  # kg·m²
        }
        
        # Turine map data (velocity ratio vs efficiency)
        self.efficiency_data = {
            'velocity_ratio': np.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.8]),
            'efficiency': np.array([0.60, 0.68, 0.73, 0.75, 0.72, 0.65])
        }
        
        # Flow parameter data
        self.flow_data = {
            'pressure_ratio': np.array([1.5, 2.0, 2.5, 3.0, 3.5, 4.0]),
            'flow_parameter': np.array([40, 45, 48, 50, 51, 51])  # kg·K/s·kPa
        }
        
        # Create interpolators
        self.efficiency_interp = interp1d(self.efficiency_data['velocity_ratio'],
                                         self.efficiency_data['efficiency'],
                                         kind='cubic', bounds_error=False,
                                         fill_value=0.5)
        
        self.flow_interp = interp1d(self.flow_data['pressure_ratio'],
                                   self.flow_data['flow_parameter'],
                                   kind='cubic', bounds_error=False,
                                   fill_value=51)
    
    def get_turbine_efficiency(self, velocity_ratio: float) -> float:
        """Get turbine efficiency at given velocity ratio"""
        # Clamp to valid range
        vr = np.clip(velocity_ratio, 0.3, 0.8)
        return float(self.efficiency_interp(vr))
    
    def get_flow_parameter(self, pressure_ratio: float) -> float:
        """Get flow parameter at given pressure ratio"""
        # Clamp to valid range
        pr = np.clip(pressure_ratio, 1.5, 4.0)
        return float(self.flow_interp(pr))
    
    def calculate_velocity_ratio(self, blade_speed: float, gas_velocity: float) -> float:
        """Calculate velocity ratio U/C"""
        if gas_velocity > 0:
            return blade_speed / gas_velocity
        return 0

class K04Turbocharger:
    """
    Complete K04 turbocharger model
    Integrates compressor and turbine models
    """
    
    def __init__(self):
        self.compressor = K04CompressorMap()
        self.turbine = K04TurbineMap()
        
        # Combined specifications
        self.specs = {
            'max_speed': 220000,      # RPM
            'max_boost': 22.0,        # PSI
            'min_oil_pressure': 30,   # PSI
            'max_oil_temp': 120,      # °C
            'bearing_type': 'journal'
        }
        
        # Dynamic state
        self.state = {
            'speed_rpm': 0,
            'speed_rad_s': 0,
            'boost_psi': 0,
            'compressor_efficiency': 0,
            'turbine_efficiency': 0,
            'power_balance': 0,
            'spool_rate': 0
        }
    
    def calculate_operating_point(self, engine_rpm: float, throttle_position: float,
                                exhaust_temp: float, ambient_temp: float = 25.0) -> Dict:
        """Calculate complete turbo operating point"""
        
        # Estimate exhaust flow (simplified)
        exhaust_flow = self._estimate_exhaust_flow(engine_rpm, throttle_position)
        
        # Estimate required boost
        target_boost = self._estimate_target_boost(throttle_position, engine_rpm)
        
        # Iterative solution for operating point
        operating_point = self._solve_operating_point(
            engine_rpm, target_boost, exhaust_flow, exhaust_temp, ambient_temp
        )
        
        # Update state
        self.state.update(operating_point)
        
        return operating_point
    
    def _estimate_exhaust_flow(self, engine_rpm: float, throttle_position: float) -> float:
        """Estimate exhaust mass flow rate"""
        # Engine displacement 2.3L
        displacement = 0.0023  # m³
        
        # Volumetric efficiency estimate
        ve = 0.85 + 0.1 * math.exp(-((engine_rpm - 4000) / 2000) ** 2)
        
        # Air flow
        intake_pressure = 101.325  # kPa
        intake_temp = 298.15  # K
        air_density = intake_pressure / (287.05 * intake_temp)
        
        cycles_per_sec = engine_rpm / 120.0  # 4-stroke
        air_flow = displacement * air_density * ve * cycles_per_sec
        
        # Exhaust flow (air + fuel)
        afr = 12.5  # Power mixture
        exhaust_flow = air_flow * (1 + 1/afr)
        
        return exhaust_flow
    
    def _estimate_target_boost(self, throttle_position: float, engine_rpm: float) -> float:
        """Estimate target boost based on throttle and RPM"""
        # Base boost curve
        if throttle_position < 50:
            return 0.0
        
        # RPM-dependent boost
        if engine_rpm < 2000:
            base_boost = 0.0
        elif engine_rpm < 3000:
            base_boost = 8.0
        elif engine_rpm < 5000:
            base_boost = 15.0
        else:
            base_boost = 18.0
        
        # Throttle scaling
        throttle_factor = (throttle_position - 50) / 50.0
        
        return base_boost * throttle_factor
    
    def _solve_operating_point(self, engine_rpm: float, target_boost: float,
                             exhaust_flow: float, exhaust_temp: float,
                             ambient_temp: float) -> Dict:
        """Solve for turbo operating point using iteration"""
        
        # Initial guess
        turbo_speed = 80000  # RPM
        tolerance = 1000  # RPM
        max_iterations = 20
        
        for iteration in range(max_iterations):
            # Calculate compressor operation
            pr = 1.0 + (target_boost * 6.89476 / 101.325)  # Convert PSI to PR
            
            # Estimate compressor flow
            corrected_flow = self._estimate_compressor_flow(turbo_speed, pr)
            
            # Get compressor operating point
            comp_point = self.compressor.get_operating_point(turbo_speed, corrected_flow)
            
            # Calculate compressor power
            comp_power = self._calculate_compressor_power(
                corrected_flow, pr, comp_point['efficiency'], ambient_temp
            )
            
            # Calculate turbine operation
            turbine_pr = 1.5  # Typical turbine PR
            turbine_eff = self.turbine.get_turbine_efficiency(0.65)  # Optimal VR
            
            # Calculate turbine power
            turb_power = self._calculate_turbine_power(
                exhaust_flow, turbine_pr, exhaust_temp, turbine_eff
            )
            
            # Power balance
            power_diff = turb_power - comp_power
            
            # Update speed guess
            if abs(power_diff) < 100:  # Within tolerance
                break
            
            # Simple proportional control
            speed_adjustment = power_diff * 10  # RPM per watt
            turbo_speed += speed_adjustment
            
            # Clamp speed
            turbo_speed = np.clip(turbo_speed, 0, self.specs['max_speed'])
        
        # Final calculations
        return {
            'speed_rpm': turbo_speed,
            'speed_rad_s': turbo_speed * 2 * math.pi / 60,
            'boost_psi': target_boost,
            'pressure_ratio': pr,
            'compressor_efficiency': comp_point['efficiency'],
            'turbine_efficiency': turbine_eff,
            'compressor_power': comp_power,
            'turbine_power': turb_power,
            'power_balance': power_diff,
            'corrected_flow': corrected_flow,
            'is_surge': comp_point['is_surge'],
            'is_choke': comp_point['is_choke']
        }
    
    def _estimate_compressor_flow(self, speed: float, pr: float) -> float:
        """Estimate compressor corrected flow"""
        # Simplified model
        max_flow = 0.18  # kg/s
        
        # Speed factor
        speed_factor = min(speed / 140000, 1.0)
        
        # PR factor
        pr_factor = math.exp(-0.5 * (pr - 1.0))
        
        flow = max_flow * speed_factor * pr_factor
        
        return flow
    
    def _calculate_compressor_power(self, mass_flow: float, pr: float,
                                  efficiency: float, inlet_temp: float) -> float:
        """Calculate compressor power requirement"""
        gamma = 1.4
        cp = 1005.0  # J/(kg·K)
        
        # Isentropic work
        work_isentropic = (gamma / (gamma - 1)) * cp * inlet_temp * \
                         ((pr ** ((gamma - 1) / gamma)) - 1)
        
        # Actual work
        work_actual = work_isentropic / efficiency
        
        # Power
        power = mass_flow * work_actual
        
        return power
    
    def _calculate_turbine_power(self, mass_flow: float, pr: float,
                               inlet_temp: float, efficiency: float) -> float:
        """Calculate turbine power output"""
        gamma = 1.4
        cp = 1100.0  # J/(kg·K) for exhaust gas
        
        # Temperature ratio
        temp_ratio = (1 / pr) ** ((gamma - 1) / gamma)
        
        # Work output
        work = cp * inlet_temp * efficiency * (1 - temp_ratio)
        
        # Power
        power = mass_flow * work
        
        return power
    
    def calculate_spool_time(self, current_speed: float, target_speed: float,
                           exhaust_energy: float) -> float:
        """Calculate spool time using energy balance"""
        
        # Moment of inertia
        J = 8.7e-5  # kg·m²
        
        # Energy required
        omega_current = current_speed * 2 * math.pi / 60
        omega_target = target_speed * 2 * math.pi / 60
        
        energy_required = 0.5 * J * (omega_target ** 2 - omega_current ** 2)
        
        # Time estimate
        if exhaust_energy > 0:
            spool_time = energy_required / exhaust_energy
        else:
            spool_time = float('inf')
        
        return min(spool_time, 5.0)  # Cap at 5 seconds
    
    def get_performance_map(self) -> Dict:
        """Get complete performance map data"""
        return {
            'compressor_map': self.compressor.map_data,
            'turbine_map': {
                'efficiency': {
                    'velocity_ratio': self.turbine.efficiency_data['velocity_ratio'].tolist(),
                    'efficiency': self.turbine.efficiency_data['efficiency'].tolist()
                },
                'flow': {
                    'pressure_ratio': self.turbine.flow_data['pressure_ratio'].tolist(),
                    'flow_parameter': self.turbine.flow_data['flow_parameter'].tolist()
                }
            },
            'specs': self.specs
        }
    
    def get_state(self) -> Dict:
        """Get current turbo state"""
        return self.state.copy()

class TurboSystemManager:
    """
    Manages complete turbo system including wastegate and blow-off valve
    """
    
    def __init__(self):
        self.turbo = K04Turbocharger()
        
        # Control system parameters
        self.control = {
            'wastegate_duty_cycle': 0.0,  # %
            'boost_target': 15.0,          # PSI
            'boost_error_integral': 0.0,
            'boost_error_previous': 0.0,
            'pid_gains': {
                'kp': 5.0,
                'ki': 0.5,
                'kd': 1.0
            }
        }
        
        # Wastegate model
        self.wastegate = {
            'flow_coefficient': 0.8,
            'effective_area': 0.001,  # m²
            'max_duty': 100.0,
            'min_duty': 0.0
        }
        
        # Blow-off valve
        self.bov = {
            'crack_pressure': 1.0,  # PSI above target
            'full_open_pressure': 2.0,  # PSI above target
            'flow_capacity': 0.05  # kg/s
        }
    
    def update_control(self, current_boost: float, target_boost: float,
                      engine_rpm: float, throttle_position: float) -> Dict:
        """Update boost control system"""
        
        # PID control
        error = target_boost - current_boost
        
        # Proportional
        p_term = self.control['pid_gains']['kp'] * error
        
        # Integral
        self.control['boost_error_integral'] += error
        i_term = self.control['pid_gains']['ki'] * self.control['boost_error_integral']
        
        # Derivative
        d_term = self.control['pid_gains']['kd'] * \
                (error - self.control['boost_error_previous'])
        self.control['boost_error_previous'] = error
        
        # Control output
        control_output = p_term + i_term + d_term
        
        # Convert to wastegate duty cycle
        wg_duty = self._control_to_wastegate(control_output)
        
        # Check blow-off valve
        bov_open = self._check_bov_condition(current_boost, target_boost, throttle_position)
        
        # Update control state
        self.control['wastegate_duty_cycle'] = wg_duty
        self.control['boost_target'] = target_boost
        
        return {
            'wastegate_duty_cycle': wg_duty,
            'bov_open': bov_open,
            'control_output': control_output,
            'boost_error': error
        }
    
    def _control_to_wastegate(self, control_output: float) -> float:
        """Convert control output to wastegate duty cycle"""
        # Inverse relationship - more control = more wastegate opening
        duty = 100.0 - np.clip(control_output, 0, 100)
        return np.clip(duty, self.wastegate['min_duty'], self.wastegate['max_duty'])
    
    def _check_bov_condition(self, current_boost: float, target_boost: float,
                           throttle_position: float) -> bool:
        """Check if blow-off valve should open"""
        # BOV opens on throttle lift with high boost
        boost_above_target = current_boost - target_boost
        
        if throttle_position < 50 and boost_above_target > self.bov['crack_pressure']:
            return True
        
        return False
    
    def calculate_wastegate_flow(self, upstream_pressure: float, 
                                downstream_pressure: float) -> float:
        """Calculate flow through wastegate"""
        
        if self.control['wastegate_duty_cycle'] == 0:
            return 0.0
        
        # Effective area based on duty cycle
        effective_area = self.wastegate['effective_area'] * \
                        (self.control['wastegate_duty_cycle'] / 100.0)
        
        # Pressure ratio
        pr = upstream_pressure / downstream_pressure
        
        # Choked flow check
        critical_pr = (2.0 / (1.4 + 1)) ** (1.4 / (1.4 - 1))
        
        if pr > critical_pr:
            # Choked flow
            flow = self.wastegate['flow_coefficient'] * effective_area * \
                   upstream_pressure / math.sqrt(287.05 * 298.15) * \
                   math.sqrt(1.4 * (2 / (1.4 + 1)) ** ((1.4 + 1) / (1.4 - 1)))
        else:
            # Subsonic flow
            flow = self.wastegate['flow_coefficient'] * effective_area * \
                   upstream_pressure / math.sqrt(287.05 * 298.15) * \
                   math.sqrt((2 * 1.4 / (1.4 - 1)) * 
                            (pr ** (2 / 1.4) - pr ** ((1.4 + 1) / 1.4)))
        
        return flow
    
    def get_system_state(self) -> Dict:
        """Get complete turbo system state"""
        return {
            'turbo': self.turbo.get_state(),
            'control': self.control.copy(),
            'wastegate': self.wastegate.copy(),
            'bov': self.bov.copy()
        }
