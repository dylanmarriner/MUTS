#!/usr/bin/env python3
"""
ADVANCED TURBO SPOOL PHYSICS WITH REAL SOLVE_IVP IMPLEMENTATION
Complete turbocharger dynamics with real differential equations
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import math

class AdvancedTurboPhysics:
    """Complete turbocharger dynamics with real differential equation solving"""
    
    def __init__(self):
        # Mazdaspeed 3 K04 turbo detailed specifications
        self.turbo_specs = {
            'compressor': {
                'inducer_diameter': 44.5e-3,      # meters
                'exducer_diameter': 60.0e-3,       # meters  
                'trim': 56,                        # compressor trim
                'max_flow': 0.18,                  # kg/s
                'max_efficiency': 0.78,
                'surge_margin': 0.15,
                'map_data': self._create_compressor_map()
            },
            'turbine': {
                'wheel_diameter': 54.0e-3,         # meters
                'housing_ar': 0.64,                # A/R ratio
                'max_efficiency': 0.75,
                'moment_of_inertia': 8.7e-5,       # kg*m²
                'flow_coefficient': 0.85,
                'velocity_ratio_optimal': 0.65
            },
            'bearing_system': {
                'friction_coefficient': 0.002,
                'viscous_damping': 1.2e-6
            }
        }
        
        # Engine specifications for exhaust energy calculation
        self.engine_specs = {
            'displacement': 2.261e-3,              # m³
            'compression_ratio': 9.5,
            'bore': 87.5e-3,                       # meters
            'stroke': 94.0e-3,                     # meters
            'rod_length': 150.0e-3,                # meters
            'exhaust_port_flow': 0.85,             # Exhaust flow coefficient
            'exhaust_temperature_base': 1173.15,   # K (900°C)
            'exhaust_pressure_ratio': 1.8          # Typical exhaust manifold pressure ratio
        }
    
    def _create_compressor_map(self):
        """Create detailed compressor map for K04 turbo"""
        # Pressure ratio vs corrected flow efficiency data
        pr_range = np.linspace(1.5, 2.5, 20)
        flow_range = np.linspace(0.05, 0.18, 20)
        
        efficiency_map = np.zeros((len(pr_range), len(flow_range)))
        
        for i, pr in enumerate(pr_range):
            for j, flow in enumerate(flow_range):
                # K04 efficiency characteristics
                peak_flow = 0.12
                peak_pr = 2.0
                
                # Distance from peak efficiency point
                flow_dist = abs(flow - peak_flow) / peak_flow
                pr_dist = abs(pr - peak_pr) / peak_pr
                
                # Efficiency calculation
                base_eff = 0.78
                flow_penalty = flow_dist * 0.3
                pr_penalty = pr_dist * 0.25
                
                efficiency_map[i,j] = max(0.50, base_eff - flow_penalty - pr_penalty)
        
        return {'pressure_ratio': pr_range, 'flow': flow_range, 'efficiency': efficiency_map}
    
    def calculate_turbo_spool_time(self, engine_rpm, throttle_position, current_turbo_rpm=0, 
                                 exhaust_temp=900, exhaust_pressure=200, time_span=(0, 10)):
        """
        Calculate exact time to reach target turbo RPM using solve_ivp
        Solves the full turbocharger rotational dynamics differential equation
        """
        # Convert engine RPM to target turbo RPM (typically 35:1 ratio for K04)
        target_turbo_rpm = engine_rpm * 35
        
        # Current state: [turbo_rpm]
        initial_state = [current_turbo_rpm]
        
        # Exhaust energy calculation
        exhaust_energy = self._calculate_exhaust_energy(engine_rpm, throttle_position, 
                                                      exhaust_temp, exhaust_pressure)
        
        # Solve the differential equation
        solution = solve_ivp(
            fun=lambda t, y: self._turbo_dynamics(t, y, exhaust_energy, target_turbo_rpm),
            t_span=time_span,
            y0=initial_state,
            method='RK45',
            rtol=1e-6,
            atol=1e-8,
            dense_output=True
        )
        
        # Find time to reach target RPM
        if solution.status == 0:  # Successful integration
            # Create interpolation function
            rpm_function = solution.sol
            
            # Find when target RPM is reached
            def time_to_target(t):
                return abs(rpm_function(t)[0] - target_turbo_rpm)
            
            # Optimize to find exact time
            result = minimize(time_to_target, x0=1.0, bounds=[(0.1, time_span[1])], 
                            method='L-BFGS-B')
            
            if result.success and result.fun < 100:  # Within 100 RPM
                return result.x[0], solution
            else:
                # Use linear search as fallback
                for t in np.linspace(0, time_span[1], 1000):
                    if rpm_function(t)[0] >= target_turbo_rpm * 0.95:  # 95% of target
                        return t, solution
        
        return time_span[1], solution  # Return max time if target not reached
    
    def _turbo_dynamics(self, t, state, exhaust_energy, target_turbo_rpm):
        """
        Turbocharger rotational dynamics differential equation
        dω/dt = (P_turbine - P_compressor - P_friction) / (I * ω)
        """
        turbo_rpm = state[0]
        turbo_omega = turbo_rpm * 2 * math.pi / 60  # Convert to rad/s
        
        # Avoid division by zero
        if turbo_omega < 0.1:
            turbo_omega = 0.1
        
        # Turbine power calculation
        turbine_power = self._calculate_turbine_power(turbo_omega, exhaust_energy)
        
        # Compressor power requirement
        compressor_power = self._calculate_compressor_power(turbo_omega, target_turbo_rpm)
        
        # Friction and bearing losses
        friction_power = self._calculate_friction_losses(turbo_omega)
        
        # Net torque
        net_torque = (turbine_power - compressor_power - friction_power) / turbo_omega
        
        # Moment of inertia
        I = self.turbo_specs['turbine']['moment_of_inertia']
        
        # Angular acceleration (rad/s²)
        alpha = net_torque / I if abs(net_torque) > 1e-6 else 0
        
        # Convert back to RPM derivative
        drpm_dt = alpha * 60 / (2 * math.pi)
        
        return [drpm_dt]
    
    def _calculate_exhaust_energy(self, engine_rpm, throttle_position, exhaust_temp, exhaust_pressure):
        """
        Calculate available exhaust gas energy for turbine
        Based on mass flow, temperature, and pressure
        """
        # Air mass flow calculation
        engine_airflow = self._calculate_engine_airflow(engine_rpm, throttle_position)
        
        # Fuel mass flow (assuming stoichiometric)
        afr = 14.7
        fuel_flow = engine_airflow / afr
        
        # Exhaust mass flow (air + fuel)
        exhaust_flow = engine_airflow + fuel_flow
        
        # Exhaust gas properties (approximate as air for simplicity)
        cp_exhaust = 1100  # J/(kg·K) - specific heat at constant pressure
        gamma_exhaust = 1.33  # Specific heat ratio for exhaust gases
        
        # Available energy in exhaust gases
        T_exhaust = exhaust_temp + 273.15  # Convert to Kelvin
        T_ambient = 298.15  # K
        
        # Ideal energy available (simplified)
        available_energy = exhaust_flow * cp_exhaust * (T_exhaust - T_ambient)
        
        # Pressure energy component
        pressure_ratio = exhaust_pressure / 101.325  # kPa to atmospheric ratio
        pressure_energy = exhaust_flow * 287 * T_exhaust * math.log(pressure_ratio)
        
        total_energy = available_energy + pressure_energy
        
        return total_energy * (throttle_position / 100)  # Scale by throttle
    
    def _calculate_engine_airflow(self, rpm, throttle_position):
        """Calculate engine airflow based on RPM and throttle position"""
        # Engine displacement per revolution (4-stroke)
        displacement_per_rev = self.engine_specs['displacement'] / 2  # m³/rev
        
        # Volumetric efficiency approximation
        ve = 0.85 + 0.15 * (throttle_position / 100)  # VE increases with throttle
        
        # Theoretical airflow
        theoretical_flow = (rpm / 60) * displacement_per_rev * ve
        
        # Air density at standard conditions (kg/m³)
        air_density = 1.225
        
        mass_flow = theoretical_flow * air_density
        
        return mass_flow
    
    def _calculate_turbine_power(self, turbo_omega, exhaust_energy):
        """
        Calculate actual turbine power output
        Includes efficiency effects based on velocity ratio
        """
        # Turbine wheel tip speed
        turbine_radius = self.turbo_specs['turbine']['wheel_diameter'] / 2
        tip_speed = turbo_omega * turbine_radius
        
        # Ideal gas velocity (simplified)
        cp = 1100  # J/(kg·K)
        gamma = 1.33
        R = 287  # J/(kg·K)
        
        # Assuming typical exhaust conditions
        T_inlet = 1173.15  # K
        P_ratio = 1.8
        
        # Ideal velocity (from isentropic expansion)
        ideal_velocity = math.sqrt(2 * cp * T_inlet * (1 - P_ratio**((1-gamma)/gamma)))
        
        # Velocity ratio
        velocity_ratio = tip_speed / ideal_velocity if ideal_velocity > 0 else 0
        
        # Turbine efficiency based on velocity ratio
        optimal_ratio = self.turbo_specs['turbine']['velocity_ratio_optimal']
        ratio_deviation = abs(velocity_ratio - optimal_ratio) / optimal_ratio
        
        # Efficiency curve (peak at optimal ratio)
        max_efficiency = self.turbo_specs['turbine']['max_efficiency']
        efficiency = max_efficiency * (1 - ratio_deviation**2)
        
        # Actual turbine power
        turbine_power = exhaust_energy * efficiency
        
        return max(0, turbine_power)
    
    def _calculate_compressor_power(self, turbo_omega, target_turbo_rpm):
        """
        Calculate compressor power requirement
        Based on pressure ratio and mass flow
        """
        # Compressor parameters
        compressor_radius = self.turbo_specs['compressor']['exducer_diameter'] / 2
        
        # Typical pressure ratio for target conditions
        pressure_ratio = 2.0 + (target_turbo_rpm / 100000)  # Simplified relationship
        
        # Mass flow estimation
        corrected_speed = turbo_omega / (2 * math.pi) * compressor_radius / 340  # Mach number approx
        mass_flow = 0.1 + 0.08 * corrected_speed  # kg/s (simplified)
        
        # Isentropic compression work
        cp = 1005  # J/(kg·K)
        gamma = 1.4
        T_inlet = 298.15  # K
        
        isentropic_work = cp * T_inlet * (pressure_ratio**((gamma-1)/gamma) - 1)
        
        # Compressor efficiency
        efficiency = self._get_compressor_efficiency(pressure_ratio, mass_flow)
        
        # Actual compressor power
        compressor_power = (mass_flow * isentropic_work) / efficiency if efficiency > 0.1 else 0
        
        return compressor_power
    
    def _get_compressor_efficiency(self, pressure_ratio, mass_flow):
        """Get compressor efficiency from map data"""
        map_data = self.turbo_specs['compressor']['map_data']
        
        # Find closest points in compressor map
        pr_idx = np.argmin(np.abs(map_data['pressure_ratio'] - pressure_ratio))
        flow_idx = np.argmin(np.abs(map_data['flow'] - mass_flow))
        
        efficiency = map_data['efficiency'][pr_idx, flow_idx]
        
        return max(0.5, efficiency)  # Minimum 50% efficiency
    
    def _calculate_friction_losses(self, turbo_omega):
        """Calculate bearing friction losses"""
        # Coulomb friction
        friction_torque = self.turbo_specs['bearing_system']['friction_coefficient'] * 9.81 * 0.1  # Simplified
        
        # Viscous damping
        viscous_torque = self.turbo_specs['bearing_system']['viscous_damping'] * turbo_omega
        
        total_friction_torque = friction_torque + viscous_torque
        friction_power = total_friction_torque * turbo_omega
        
        return friction_power

class AdvancedAITuning:
    """Advanced AI tuning with sophisticated action mapping"""
    
    def __init__(self):
        self.state_size = 15
        self.action_size = 24  # Expanded action space for finer control
        self.action_mapping = self._create_advanced_action_mapping()
        
        # Neural network for continuous action space
        self.actor_network = self._create_actor_network()
        self.critic_network = self._create_critic_network()
        
        # Experience replay with prioritization
        self.prioritized_replay = PrioritizedReplayBuffer(10000)
        
    def _create_advanced_action_mapping(self):
        """Create sophisticated action mapping for precise tuning control"""
        mapping = {
            # Ignition timing adjustments (8 levels of granularity)
            0: {'ignition_timing': 0.1, 'confidence': 0.8},   # Very small advance
            1: {'ignition_timing': 0.5, 'confidence': 0.9},   # Small advance  
            2: {'ignition_timing': 1.0, 'confidence': 0.7},   # Medium advance
            3: {'ignition_timing': 2.0, 'confidence': 0.6},   # Large advance
            4: {'ignition_timing': -0.1, 'confidence': 0.8},  # Very small retard
            5: {'ignition_timing': -0.5, 'confidence': 0.9},  # Small retard
            6: {'ignition_timing': -1.0, 'confidence': 0.7},  # Medium retard
            7: {'ignition_timing': -2.0, 'confidence': 0.6},  # Large retard
            
            # Boost control adjustments (8 levels)
            8: {'wgdc_reduction': 1.0, 'boost_target': 0.2, 'confidence': 0.7},   # Faster spool
            9: {'wgdc_reduction': 2.0, 'boost_target': 0.5, 'confidence': 0.6},   # Aggressive spool
            10: {'wgdc_increase': 1.0, 'boost_target': 0.5, 'confidence': 0.8},   # Hold boost
            11: {'wgdc_increase': 3.0, 'boost_target': 1.0, 'confidence': 0.7},   # Increase boost
            12: {'wgdc_reduction': 5.0, 'boost_target': -0.5, 'confidence': 0.9}, # Reduce boost
            13: {'boost_taper_start': 500, 'confidence': 0.6},  # Earlier taper
            14: {'boost_taper_start': -500, 'confidence': 0.6}, # Later taper
            15: {'boost_hold_rpm': 200, 'confidence': 0.5},     # Extend boost
            
            # Fuel and AFR adjustments (4 levels)
            16: {'target_afr': -0.05, 'fuel_enrichment': 1.0, 'confidence': 0.8},  # Slightly richer
            17: {'target_afr': -0.15, 'fuel_enrichment': 3.0, 'confidence': 0.7},  # Moderately richer
            18: {'target_afr': 0.05, 'fuel_enrichment': -1.0, 'confidence': 0.8},  # Slightly leaner
            19: {'target_afr': 0.15, 'fuel_enrichment': -3.0, 'confidence': 0.7},  # Moderately leaner
            
            # VVT optimization (4 levels)
            20: {'vvt_intake_advance': 2.0, 'vvt_exhaust_retard': 1.0, 'confidence': 0.7},  # Low-end torque
            21: {'vvt_intake_retard': 2.0, 'vvt_exhaust_advance': 1.0, 'confidence': 0.7},  # High-end power
            22: {'vvt_intake_advance': 5.0, 'vvt_exhaust_retard': 3.0, 'confidence': 0.6},  # Aggressive low-end
            23: {'vvt_intake_retard': 5.0, 'vvt_exhaust_advance': 3.0, 'confidence': 0.6},  # Aggressive high-end
        }
        return mapping
    
    def _create_actor_network(self):
        """Actor network for continuous action space (DDPG style)"""
        import torch.nn as nn
        
        class ActorNetwork(nn.Module):
            def __init__(self, state_size, action_size, hidden_size=256):
                super(ActorNetwork, self).__init__()
                self.network = nn.Sequential(
                    nn.Linear(state_size, hidden_size),
                    nn.LayerNorm(hidden_size),
                    nn.ReLU(),
                    nn.Dropout(0.1),
                    nn.Linear(hidden_size, hidden_size),
                    nn.LayerNorm(hidden_size),
                    nn.ReLU(),
                    nn.Dropout(0.1),
                    nn.Linear(hidden_size, hidden_size // 2),
                    nn.LayerNorm(hidden_size // 2),
                    nn.ReLU(),
                    nn.Linear(hidden_size // 2, action_size),
                    nn.Tanh()  # Output between -1 and 1
                )
                
            def forward(self, state):
                return self.network(state)
        
        return ActorNetwork(self.state_size, self.action_size)
    
    def _create_critic_network(self):
        """Critic network for value estimation"""
        import torch.nn as nn
        
        class CriticNetwork(nn.Module):
            def __init__(self, state_size, action_size, hidden_size=256):
                super(CriticNetwork, self).__init__()
                self.state_stream = nn.Sequential(
                    nn.Linear(state_size, hidden_size),
                    nn.LayerNorm(hidden_size),
                    nn.ReLU()
                )
                
                self.action_stream = nn.Sequential(
                    nn.Linear(action_size, hidden_size),
                    nn.LayerNorm(hidden_size),
                    nn.ReLU()
                )
                
                self.combined_stream = nn.Sequential(
                    nn.Linear(hidden_size * 2, hidden_size),
                    nn.ReLU(),
                    nn.Linear(hidden_size, 1)
                )
                
            def forward(self, state, action):
                state_out = self.state_stream(state)
                action_out = self.action_stream(action)
                combined = torch.cat([state_out, action_out], dim=1)
                return self.combined_stream(combined)
        
        return CriticNetwork(self.state_size, self.action_size)
    
    def map_action_to_adjustments(self, action_output, current_state):
        """
        Sophisticated action mapping that considers current engine state
        and applies non-linear transformations for optimal control
        """
        # action_output is from actor network (-1 to 1)
        action_index = self._select_action_index(action_output, current_state)
        base_adjustments = self.action_mapping.get(action_index, {})
        
        # Apply state-dependent scaling
        scaled_adjustments = self._scale_adjustments_by_state(base_adjustments, current_state)
        
        # Apply non-linear corrections based on operating conditions
        corrected_adjustments = self._apply_non_linear_corrections(scaled_adjustments, current_state)
        
        return corrected_adjustments
    
    def _select_action_index(self, action_output, current_state):
        """Select action index based on continuous output and current state"""
        # Convert continuous output to discrete action with state-dependent bias
        rpm = current_state[0] * 7000  # Denormalize RPM
        load = current_state[1] * 1.6   # Denormalize load
        
        # Action selection strategy based on operating conditions
        if rpm < 3000 and load > 0.8:
            # Low RPM, high load - prioritize spool and torque
            action_bias = [1.0, 1.0, 0.5, 0.5, -0.5, -0.5, -1.0, -1.0] + [1.0] * 8 + [0.5] * 4 + [1.0] * 4
        elif rpm > 5000:
            # High RPM - prioritize power and safety
            action_bias = [0.5, 0.5, 1.0, 1.0, -1.0, -1.0, -0.5, -0.5] + [0.5] * 8 + [1.0] * 4 + [0.5] * 4
        else:
            # Mid-range - balanced approach
            action_bias = [0.8, 0.8, 0.8, 0.8, -0.8, -0.8, -0.8, -0.8] + [0.8] * 16
        
        # Apply bias and select action
        biased_output = action_output + np.array(action_bias[:len(action_output)])
        action_index = np.argmax(biased_output)
        
        return action_index % self.action_size  # Ensure valid index
    
    def _scale_adjustments_by_state(self, adjustments, current_state):
        """Scale adjustments based on current engine operating conditions"""
        scaled = adjustments.copy()
        rpm = current_state[0] * 7000  # Denormalize
        load = current_state[1] * 1.6
        knock = current_state[5] * 8.0
        intake_temp = current_state[6] * 60
        
        # RPM-based scaling
        rpm_factor = 1.0
        if rpm < 2500:
            rpm_factor = 0.7  # Conservative at low RPM
        elif rpm > 6000:
            rpm_factor = 1.2  # More aggressive at high RPM
        
        # Load-based scaling
        load_factor = 0.5 + load * 0.5  # Scale with load
        
        # Knock-based scaling
        knock_factor = max(0.5, 1.0 - knock * 0.1)  # Reduce adjustments with knock
        
        # Temperature-based scaling
        temp_factor = 1.0
        if intake_temp > 40:
            temp_factor = 0.8  # Conservative in hot conditions
        
        overall_factor = rpm_factor * load_factor * knock_factor * temp_factor
        
        # Apply scaling to continuous adjustments
        for key in ['ignition_timing', 'boost_target', 'target_afr', 'wgdc_reduction', 
                   'wgdc_increase', 'vvt_intake_advance', 'vvt_intake_retard',
                   'vvt_exhaust_advance', 'vvt_exhaust_retard', 'fuel_enrichment']:
            if key in scaled:
                scaled[key] *= overall_factor
        
        return scaled
    
    def _apply_non_linear_corrections(self, adjustments, current_state):
        """Apply non-linear corrections based on complex engine behavior"""
        corrected = adjustments.copy()
        rpm = current_state[0] * 7000
        load = current_state[1] * 1.6
        boost = current_state[2] * 22.0
        
        # Non-linear ignition timing correction
        if 'ignition_timing' in corrected:
            timing_adj = corrected['ignition_timing']
            
            # MBT timing curve approximation
            optimal_rpm = 4500
            rpm_deviation = abs(rpm - optimal_rpm) / optimal_rpm
            timing_correction = 1.0 - rpm_deviation * 0.3
            
            # Boost effect on timing
            boost_correction = 1.0 - (boost / 22.0) * 0.2
            
            corrected['ignition_timing'] = timing_adj * timing_correction * boost_correction
        
        # Non-linear boost control correction
        if any(k in corrected for k in ['wgdc_reduction', 'wgdc_increase', 'boost_target']):
            # Turbo lag compensation
            lag_compensation = 1.0 + (7000 - rpm) / 7000 * 0.5  # More aggressive at low RPM
            
            for key in ['wgdc_reduction', 'wgdc_increase', 'boost_target']:
                if key in corrected:
                    corrected[key] *= lag_compensation
        
        # VVT non-linear effects
        if any(k in corrected for k in ['vvt_intake_advance', 'vvt_intake_retard', 
                                      'vvt_exhaust_advance', 'vvt_exhaust_retard']):
            # Cam timing effectiveness varies with RPM
            vvt_effectiveness = 0.5 + (rpm / 7000) * 0.5  # More effective at high RPM
            
            for key in ['vvt_intake_advance', 'vvt_intake_retard', 
                       'vvt_exhaust_advance', 'vvt_exhaust_retard']:
                if key in corrected:
                    corrected[key] *= vvt_effectiveness
        
        return corrected

class PrioritizedReplayBuffer:
    """Prioritized experience replay for efficient learning"""
    
    def __init__(self, capacity, alpha=0.6, beta=0.4):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.buffer = []
        self.priorities = np.zeros(capacity)
        self.position = 0
        self.size = 0
        
    def add(self, state, action, reward, next_state, done, priority=None):
        """Add experience with priority"""
        if priority is None:
            priority = max(self.priorities.max(), 1.0) if self.size > 0 else 1.0
        
        if self.size < self.capacity:
            self.buffer.append((state, action, reward, next_state, done))
            self.priorities[self.position] = priority
            self.size += 1
        else:
            self.buffer[self.position] = (state, action, reward, next_state, done)
            self.priorities[self.position] = priority
        
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size):
        """Sample batch with prioritization"""
        if self.size == 0:
            return []
        
        priorities = self.priorities[:self.size]
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        indices = np.random.choice(self.size, batch_size, p=probabilities)
        samples = [self.buffer[idx] for idx in indices]
        
        # Importance sampling weights
        weights = (self.size * probabilities[indices]) ** (-self.beta)
        weights /= weights.max()
        
        return samples, indices, weights
    
    def update_priorities(self, indices, priorities):
        """Update priorities for sampled experiences"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority

# COMPREHENSIVE TESTING AND VALIDATION
def test_advanced_turbo_spool():
    """Test the advanced turbo spool physics implementation"""
    turbo_physics = AdvancedTurboPhysics()
    
    # Test spool time calculation
    print("Testing Advanced Turbo Spool Physics...")
    
    test_cases = [
        (3000, 100, 0, 900, 200),   # Full throttle from 3000 RPM
        (2000, 100, 0, 850, 180),   # Full throttle from 2000 RPM  
        (4000, 80, 50000, 950, 220), # Partial throttle with existing spool
    ]
    
    for engine_rpm, throttle, current_turbo_rpm, exh_temp, exh_pressure in test_cases:
        spool_time, solution = turbo_physics.calculate_turbo_spool_time(
            engine_rpm, throttle, current_turbo_rpm, exh_temp, exh_pressure
        )
        
        print(f"Engine RPM: {engine_rpm}, Throttle: {throttle}%")
        print(f"Current Turbo RPM: {current_turbo_rpm}")
        print(f"Spool Time: {spool_time:.2f} seconds")
        print(f"Solution Status: {solution.status}")
        print(f"Final Turbo RPM: {solution.y[0][-1]:.0f}")
        print("-" * 50)

def test_advanced_ai_mapping():
    """Test the sophisticated AI action mapping"""
    ai_tuner = AdvancedAITuning()
    
    # Test various engine states
    test_states = [
        [0.3, 0.8, 0.5, 0.6, 0.4, 0.1, 0.3, 0.7, 0.9, 0.5, 0.4, 0.2, 0.1, 0.3, 0.5],  # Low RPM, high load
        [0.8, 0.6, 0.7, 0.8, 0.5, 0.3, 0.6, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],  # High RPM, medium load
        [0.5, 0.4, 0.3, 0.5, 0.6, 0.7, 0.4, 0.5, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],  # Mid-range, low load
    ]
    
    for i, state in enumerate(test_states):
        # Simulate actor network output
        action_output = np.random.uniform(-1, 1, ai_tuner.action_size)
        
        adjustments = ai_tuner.map_action_to_adjustments(action_output, state)
        
        print(f"Test Case {i+1}:")
        print(f"State: RPM={state[0]*7000:.0f}, Load={state[1]*1.6:.2f}, Boost={state[2]*22:.1f}psi")
        print(f"Adjustments: {adjustments}")
        print("-" * 50)

if __name__ == "__main__":
    print("ADVANCED TURBO PHYSICS AND AI TUNING VALIDATION")
    print("=" * 70)
    
    test_advanced_turbo_spool()
    test_advanced_ai_mapping()