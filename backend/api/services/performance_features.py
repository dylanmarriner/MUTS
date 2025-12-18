#!/usr/bin/env python3
"""
ADVANCED PERFORMANCE FEATURES FOR MAZDASPEED 3
Complete anti-lag system, two-step rev limiter, and launch control
"""

import numpy as np
from typing import Dict, Tuple, Optional
import time

class AntiLagSystem:
    """
    Complete Anti-Lag System (ALS) for Mazdaspeed 3
    Reduces turbo lag by maintaining exhaust energy during throttle lift
    """
    
    def __init__(self):
        # ALS configuration
        self.config = {
            'activation_speed': 50.0,      # km/h
            'min_rpm': 2500,               # Minimum RPM for activation
            'max_rpm': 6000,               # Maximum RPM for activation
            'min_throttle': 0.0,           # Throttle position for activation
            'min_boost': 5.0,              # Minimum boost to maintain
            'target_boost': 12.0,          # Target boost during ALS
            'max_retard': -15.0,           # Maximum timing retard
            'fuel_enrichment': 2.0,        # Additional fuel (%)
            'als_active': False,
            'als_mode': 'off'              # off, soft, aggressive, rally
        }
        
        # Safety parameters
        self.safety = {
            'max_exhaust_temp': 950.0,     # °C
            'max_egt_duration': 10.0,       # seconds
            'min_coolant_temp': 70.0,       # °C
            'max_intake_temp': 60.0,        # °C
            'oil_pressure_min': 20.0        # PSI
        }
        
        # State tracking
        self.state = {
            'start_time': 0,
            'egt_timer': 0,
            'activation_count': 0,
            'total_als_time': 0
        }
    
    def calculate_als_parameters(self, vehicle_speed: float, throttle_position: float,
                                current_turbo_rpm: float, exhaust_temp: float,
                                coolant_temp: float, intake_temp: float,
                                oil_pressure: float, engine_rpm: float) -> Dict:
        """Calculate ALS parameters based on current conditions"""
        
        params = {
            'als_active': False,
            'timing_adjustment': 0,
            'fuel_adjustment': 0,
            'boost_target': 0,
            'warnings': []
        }
        
        # Check activation conditions
        should_activate = self._check_activation_conditions(
            vehicle_speed, throttle_position, current_turbo_rpm,
            exhaust_temp, coolant_temp, intake_temp, oil_pressure, engine_rpm
        )
        
        if should_activate:
            params['als_active'] = True
            self.config['als_active'] = True
            
            # Calculate adjustments based on mode
            if self.config['als_mode'] == 'soft':
                params['timing_adjustment'] = -8.0
                params['fuel_adjustment'] = 1.5
                params['boost_target'] = 8.0
            elif self.config['als_mode'] == 'aggressive':
                params['timing_adjustment'] = -12.0
                params['fuel_adjustment'] = 2.5
                params['boost_target'] = 12.0
            elif self.config['als_mode'] == 'rally':
                params['timing_adjustment'] = -15.0
                params['fuel_adjustment'] = 3.0
                params['boost_target'] = 15.0
            else:
                params['als_active'] = False
                self.config['als_active'] = False
                return params
            
            # Update state
            if not self.state['start_time']:
                self.state['start_time'] = time.time()
            
            # Check safety limits
            if exhaust_temp > self.safety['max_exhaust_temp']:
                params['warnings'].append('Exhaust temperature too high')
                params['als_active'] = False
                self.config['als_active'] = False
            
            if coolant_temp < self.safety['min_coolant_temp']:
                params['warnings'].append('Coolant temperature too low')
                params['als_active'] = False
                self.config['als_active'] = False
            
            if intake_temp > self.safety['max_intake_temp']:
                params['warnings'].append('Intake temperature too high')
                params['timing_adjustment'] += 2.0  # Reduce retard
            
        else:
            # Deactivate ALS
            if self.config['als_active']:
                self.config['als_active'] = False
                if self.state['start_time']:
                    self.state['total_als_time'] += time.time() - self.state['start_time']
                    self.state['start_time'] = 0
        
        return params
    
    def _check_activation_conditions(self, vehicle_speed: float, throttle_position: float,
                                   current_turbo_rpm: float, exhaust_temp: float,
                                   coolant_temp: float, intake_temp: float,
                                   oil_pressure: float, engine_rpm: float) -> bool:
        """Check if ALS should be activated"""
        
        # Basic conditions
        if vehicle_speed > self.config['activation_speed']:
            return False
        
        if throttle_position > self.config['min_throttle'] + 5.0:
            return False
        
        if not (self.config['min_rpm'] <= engine_rpm <= self.config['max_rpm']):
            return False
        
        # Safety conditions
        if coolant_temp < self.safety['min_coolant_temp']:
            return False
        
        if intake_temp > self.safety['max_intake_temp']:
            return False
        
        if oil_pressure < self.safety['oil_pressure_min']:
            return False
        
        # Turbo condition
        if current_turbo_rpm < 30000:  # Turbo not spinning fast enough
            return False
        
        return True
    
    def set_als_mode(self, mode: str):
        """Set ALS mode"""
        valid_modes = ['off', 'soft', 'aggressive', 'rally']
        if mode in valid_modes:
            self.config['als_mode'] = mode
    
    def get_als_status(self) -> Dict:
        """Get current ALS status"""
        return {
            'active': self.config['als_active'],
            'mode': self.config['als_mode'],
            'total_usage_time': self.state['total_als_time'],
            'activation_count': self.state['activation_count']
        }

class TwoStepRevLimiter:
    """
    Two-Step Rev Limiter for consistent launches
    Maintains target RPM for optimal launch
    """
    
    def __init__(self):
        # Configuration
        self.config = {
            'launch_rpm': 4500,            # Target launch RPM
            'launch_rpm_tolerance': 100,    # RPM tolerance
            'fuel_cut_rpm': 4800,          # Hard fuel cut limit
            'spark_cut_rpm': 4700,         # Spark cut limit
            'min_vehicle_speed': 5.0,      # km/h
            'max_vehicle_speed': 10.0,     # km/h
            'clutch_disengaged': True,     # Clutch must be disengaged
            'full_throttle_required': True  # Full throttle for activation
        }
        
        # State
        self.state = {
            'rev_limit_active': False,
            'fuel_cut_active': False,
            'spark_cut_active': False,
            'launch_count': 0
        }
    
    def calculate_rev_limit_parameters(self, engine_rpm: float, vehicle_speed: float,
                                     clutch_position: float, throttle_position: float) -> Dict:
        """Calculate rev limiter parameters"""
        
        params = {
            'rev_limit_active': False,
            'fuel_cut_active': False,
            'spark_cut_active': False,
            'target_rpm': self.config['launch_rpm'],
            'timing_retard': 0,
            'fuel_enrichment': 0
        }
        
        # Check activation conditions
        should_activate = self._check_activation_conditions(
            engine_rpm, vehicle_speed, clutch_position, throttle_position
        )
        
        if should_activate:
            params['rev_limit_active'] = True
            self.state['rev_limit_active'] = True
            
            # Calculate limiting strategy
            rpm_error = engine_rpm - self.config['launch_rpm']
            
            if rpm_error > self.config['launch_rpm_tolerance']:
                # Above target - apply limiting
                if engine_rpm >= self.config['fuel_cut_rpm']:
                    params['fuel_cut_active'] = True
                    self.state['fuel_cut_active'] = True
                elif engine_rpm >= self.config['spark_cut_rpm']:
                    params['spark_cut_active'] = True
                    self.state['spark_cut_active'] = True
                    params['timing_retard'] = -10.0
                else:
                    # Soft limiting with timing
                    params['timing_retard'] = min(-5.0, -rpm_error / 10)
                    params['fuel_enrichment'] = 1.0
            else:
                # Below target - build boost
                params['timing_retard'] = -8.0
                params['fuel_enrichment'] = 2.0
        
        else:
            # Deactivate
            self.state['rev_limit_active'] = False
            self.state['fuel_cut_active'] = False
            self.state['spark_cut_active'] = False
        
        return params
    
    def _check_activation_conditions(self, engine_rpm: float, vehicle_speed: float,
                                   clutch_position: float, throttle_position: float) -> bool:
        """Check if two-step should activate"""
        
        # Vehicle speed condition
        if not (self.config['min_vehicle_speed'] <= vehicle_speed <= self.config['max_vehicle_speed']):
            return False
        
        # Clutch condition
        if self.config['clutch_disengaged'] and clutch_position > 50.0:
            return False
        
        # Throttle condition
        if self.config['full_throttle_required'] and throttle_position < 95.0:
            return False
        
        # RPM condition
        if engine_rpm < 3000:  # Too low for launch
            return False
        
        return True
    
    def set_launch_rpm(self, rpm: int):
        """Set target launch RPM"""
        if 3000 <= rpm <= 5500:
            self.config['launch_rpm'] = rpm

class LaunchControlSystem:
    """
    Complete Launch Control System
    Integrates two-step, boost control, and traction management
    """
    
    def __init__(self):
        self.two_step = TwoStepRevLimiter()
        self.als = AntiLagSystem()
        
        # Launch control configuration
        self.config = {
            'launch_boost_target': 15.0,    # PSI
            'boost_tolerance': 2.0,          # PSI tolerance
            'max_launch_duration': 5.0,      # seconds
            'traction_control_active': True,
            'wheel_slip_threshold': 10.0,    # % slip
            'min_gear': 1,
            'max_gear': 1
        }
        
        # State
        self.state = {
            'launch_active': False,
            'launch_start_time': 0,
            'launch_count': 0,
            'best_launch': None
        }
        
        # Performance tracking
        self.performance = {
            'launch_times': [],
            'sixty_foot_times': [],
            'boost_build_times': []
        }
    
    def calculate_launch_parameters(self, vehicle_speed: float, engine_rpm: float,
                                  throttle_position: float, clutch_position: float,
                                  wheel_speeds: list, current_boost: float,
                                  gear: int) -> Dict:
        """Calculate complete launch control parameters"""
        
        params = {
            'launch_active': False,
            'target_boost': 0,
            'timing_adjustment': 0,
            'fuel_adjustment': 0,
            'rev_limit_params': {},
            'als_params': {},
            'traction_adjust': 0,
            'warnings': []
        }
        
        # Check activation conditions
        should_activate = self._check_launch_conditions(
            vehicle_speed, engine_rpm, throttle_position, clutch_position, gear
        )
        
        if should_activate:
            params['launch_active'] = True
            self.state['launch_active'] = True
            
            # Start launch timer
            if not self.state['launch_start_time']:
                self.state['launch_start_time'] = time.time()
            
            # Get two-step parameters
            params['rev_limit_params'] = self.two_step.calculate_rev_limit_parameters(
                engine_rpm, vehicle_speed, clutch_position, throttle_position
            )
            
            # Get ALS parameters for boost building
            params['als_params'] = self.als.calculate_als_parameters(
                vehicle_speed, throttle_position, 50000, 800, 90, 30, 40, engine_rpm
            )
            
            # Calculate boost target
            params['target_boost'] = self.config['launch_boost_target']
            
            # Check boost build
            boost_error = self.config['launch_boost_target'] - current_boost
            if boost_error > self.config['boost_tolerance']:
                # Need more boost
                params['timing_adjustment'] = -10.0
                params['fuel_adjustment'] = 2.5
                self.als.set_als_mode('aggressive')
            else:
                # Boost on target
                params['timing_adjustment'] = params['rev_limit_params'].get('timing_retard', 0)
                params['fuel_adjustment'] = params['rev_limit_params'].get('fuel_enrichment', 0)
                self.als.set_als_mode('soft')
            
            # Traction control
            if self.config['traction_control_active'] and wheel_speeds:
                slip = self._calculate_wheel_slip(wheel_speeds, vehicle_speed)
                if slip > self.config['wheel_slip_threshold']:
                    params['traction_adjust'] = -5.0  # Reduce power
                    params['warnings'].append(f'Wheel slip: {slip:.1f}%')
            
            # Check launch duration
            if self.state['launch_start_time']:
                duration = time.time() - self.state['launch_start_time']
                if duration > self.config['max_launch_duration']:
                    params['warnings'].append('Launch duration exceeded')
                    params['launch_active'] = False
                    self.state['launch_active'] = False
        
        else:
            # Deactivate launch
            if self.state['launch_active']:
                self._complete_launch()
        
        return params
    
    def _check_launch_conditions(self, vehicle_speed: float, engine_rpm: float,
                               throttle_position: float, clutch_position: float,
                               gear: int) -> bool:
        """Check if launch control should activate"""
        
        # Speed condition
        if vehicle_speed > 10.0:
            return False
        
        # Gear condition
        if not (self.config['min_gear'] <= gear <= self.config['max_gear']):
            return False
        
        # Throttle condition
        if throttle_position < 95.0:
            return False
        
        # Clutch condition
        if clutch_position > 50.0:  # Clutch engaged
            return False
        
        # RPM condition
        if engine_rpm < 3000:
            return False
        
        return True
    
    def _calculate_wheel_slip(self, wheel_speeds: list, vehicle_speed: float) -> float:
        """Calculate wheel slip percentage"""
        if not wheel_speeds:
            return 0.0
        
        # Average driven wheel speed
        driven_speeds = wheel_speeds[0:2]  # Front wheels
        avg_wheel_speed = np.mean(driven_speeds)
        
        # Calculate slip
        if vehicle_speed > 0:
            slip = ((avg_wheel_speed - vehicle_speed) / vehicle_speed) * 100
        else:
            slip = 0.0
        
        return abs(slip)
    
    def _complete_launch(self):
        """Complete launch and record performance"""
        self.state['launch_active'] = False
        self.state['launch_count'] += 1
        
        # Reset systems
        self.als.set_als_mode('off')
        
        # Record launch time
        if self.state['launch_start_time']:
            launch_time = time.time() - self.state['launch_start_time']
            self.performance['launch_times'].append(launch_time)
            self.state['launch_start_time'] = 0
            
            # Update best launch
            if not self.state['best_launch'] or launch_time < self.state['best_launch']:
                self.state['best_launch'] = launch_time
    
    def get_launch_status(self) -> Dict:
        """Get launch control status"""
        return {
            'active': self.state['launch_active'],
            'launch_count': self.state['launch_count'],
            'best_launch': self.state['best_launch'],
            'average_launch_time': np.mean(self.performance['launch_times']) if self.performance['launch_times'] else None
        }

class PerformanceFeatureManager:
    """
    Master controller for all performance features
    Coordinates ALS, two-step, and launch control
    """
    
    def __init__(self):
        self.als = AntiLagSystem()
        self.two_step = TwoStepRevLimiter()
        self.launch_control = LaunchControlSystem()
        
        # Global configuration
        self.config = {
            'features_enabled': {
                'als': True,
                'two_step': True,
                'launch_control': True,
                'traction_control': True
            },
            'safety_mode': 'medium',  # off, low, medium, high
            'driver_mode': 'street'    # street, track, drag, rally
        }
        
        # Integrated parameters
        self.integrated_params = {
            'global_timing_offset': 0,
            'global_fuel_offset': 0,
            'boost_limit': 22.0,
            'rpm_limit': 7000
        }
    
    def calculate_integrated_parameters(self, sensor_data: Dict) -> Dict:
        """Calculate integrated parameters for all systems"""
        
        params = {
            'final_timing': sensor_data.get('base_timing', 10.0),
            'final_fuel': sensor_data.get('base_fuel', 0.0),
            'final_boost_target': sensor_data.get('base_boost', 15.0),
            'fuel_cut': False,
            'spark_cut': False,
            'active_features': [],
            'warnings': []
        }
        
        # Get individual system parameters
        als_params = {}
        two_step_params = {}
        launch_params = {}
        
        if self.config['features_enabled']['als']:
            als_params = self.als.calculate_als_parameters(
                sensor_data.get('vehicle_speed', 0),
                sensor_data.get('throttle_position', 0),
                sensor_data.get('turbo_rpm', 0),
                sensor_data.get('exhaust_temp', 800),
                sensor_data.get('coolant_temp', 90),
                sensor_data.get('intake_temp', 30),
                sensor_data.get('oil_pressure', 40),
                sensor_data.get('engine_rpm', 0)
            )
        
        if self.config['features_enabled']['two_step']:
            two_step_params = self.two_step.calculate_rev_limit_parameters(
                sensor_data.get('engine_rpm', 0),
                sensor_data.get('vehicle_speed', 0),
                sensor_data.get('clutch_position', 100),
                sensor_data.get('throttle_position', 0)
            )
        
        if self.config['features_enabled']['launch_control']:
            launch_params = self.launch_control.calculate_launch_parameters(
                sensor_data.get('vehicle_speed', 0),
                sensor_data.get('engine_rpm', 0),
                sensor_data.get('throttle_position', 0),
                sensor_data.get('clutch_position', 100),
                sensor_data.get('wheel_speeds', []),
                sensor_data.get('boost_psi', 0),
                sensor_data.get('gear', 1)
            )
        
        # Priority system: Launch > Two-step > ALS
        if launch_params.get('launch_active', False):
            params['active_features'].append('launch_control')
            params['final_timing'] += launch_params.get('timing_adjustment', 0)
            params['final_fuel'] += launch_params.get('fuel_adjustment', 0)
            params['final_boost_target'] = launch_params.get('target_boost', 15.0)
            params['fuel_cut'] = launch_params.get('rev_limit_params', {}).get('fuel_cut_active', False)
            params['spark_cut'] = launch_params.get('rev_limit_params', {}).get('spark_cut_active', False)
            params['warnings'].extend(launch_params.get('warnings', []))
        
        elif two_step_params.get('rev_limit_active', False):
            params['active_features'].append('two_step')
            params['final_timing'] += two_step_params.get('timing_retard', 0)
            params['final_fuel'] += two_step_params.get('fuel_enrichment', 0)
            params['fuel_cut'] = two_step_params.get('fuel_cut_active', False)
            params['spark_cut'] = two_step_params.get('spark_cut_active', False)
        
        elif als_params.get('als_active', False):
            params['active_features'].append('als')
            params['final_timing'] += als_params.get('timing_adjustment', 0)
            params['final_fuel'] += als_params.get('fuel_adjustment', 0)
            params['final_boost_target'] = als_params.get('boost_target', 15.0)
            params['warnings'].extend(als_params.get('warnings', []))
        
        # Apply safety limits based on mode
        params = self._apply_safety_limits(params, sensor_data)
        
        return params
    
    def _apply_safety_limits(self, params: Dict, sensor_data: Dict) -> Dict:
        """Apply safety limits based on safety mode"""
        
        if self.config['safety_mode'] == 'off':
            return params
        
        # RPM limit
        if sensor_data.get('engine_rpm', 0) > self.integrated_params['rpm_limit']:
            params['fuel_cut'] = True
            params['warnings'].append('RPM limit exceeded')
        
        # Boost limit
        if params['final_boost_target'] > self.integrated_params['boost_limit']:
            params['final_boost_target'] = self.integrated_params['boost_limit']
            params['warnings'].append('Boost limited')
        
        # Timing limits
        if params['final_timing'] < -20:
            params['final_timing'] = -20
            params['warnings'].append('Timing retard limited')
        
        # Safety mode adjustments
        if self.config['safety_mode'] == 'high':
            # More conservative limits
            self.integrated_params['boost_limit'] = 18.0
            self.integrated_params['rpm_limit'] = 6500
        elif self.config['safety_mode'] == 'low':
            # More aggressive limits
            self.integrated_params['boost_limit'] = 25.0
            self.integrated_params['rpm_limit'] = 7200
        
        return params
    
    def set_driver_mode(self, mode: str):
        """Set driver mode"""
        valid_modes = ['street', 'track', 'drag', 'rally']
        if mode in valid_modes:
            self.config['driver_mode'] = mode
            
            # Adjust settings based on mode
            if mode == 'street':
                self.als.set_als_mode('off')
                self.two_step.set_launch_rpm(4000)
                self.config['safety_mode'] = 'medium'
            elif mode == 'track':
                self.als.set_als_mode('soft')
                self.two_step.set_launch_rpm(4500)
                self.config['safety_mode'] = 'low'
            elif mode == 'drag':
                self.als.set_als_mode('aggressive')
                self.two_step.set_launch_rpm(5000)
                self.config['safety_mode'] = 'low'
            elif mode == 'rally':
                self.als.set_als_mode('rally')
                self.two_step.set_launch_rpm(4500)
                self.config['safety_mode'] = 'medium'
    
    def get_system_status(self) -> Dict:
        """Get status of all performance features"""
        return {
            'als': self.als.get_als_status(),
            'two_step': {
                'active': self.two_step.state['rev_limit_active'],
                'launch_rpm': self.two_step.config['launch_rpm']
            },
            'launch_control': self.launch_control.get_launch_status(),
            'driver_mode': self.config['driver_mode'],
            'safety_mode': self.config['safety_mode'],
            'enabled_features': [k for k, v in self.config['features_enabled'].items() if v]
        }
