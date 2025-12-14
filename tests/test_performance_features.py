"""Tests for services performance_features module."""
import unittest
from unittest.mock import Mock

# Import directly to avoid muts package import issues
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'muts' / 'services'))
from performance_features import (
    AntiLagSystem, TwoStepRevLimiter, LaunchControlSystem, AdvancedPerformanceManager
)


class TestAntiLagSystem(unittest.TestCase):
    """Test AntiLagSystem class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.als = AntiLagSystem()
    
    def test_initialization(self):
        """Test AntiLagSystem initialization."""
        self.assertFalse(self.als.als_enabled)
        self.assertFalse(self.als.als_active)
        self.assertEqual(self.als.als_mode, 'soft')
        self.assertIn('soft', self.als.als_modes)
        self.assertIn('aggressive', self.als.als_modes)
        self.assertIn('rally', self.als.als_modes)
    
    def test_calculate_als_parameters(self):
        """Test calculate_als_parameters method."""
        params = self.als.calculate_als_parameters(
            vehicle_speed=50.0,
            throttle_position=0.0,  # Off throttle
            current_turbo_rpm=40000.0,
            exhaust_temp=800.0
        )
        
        self.assertIsInstance(params, dict)
        self.assertIn('als_active', params)
    
    def test_safety_monitor(self):
        """Test safety_monitor method."""
        safety = self.als.safety_monitor(
            exhaust_temp=850.0,
            coolant_temp=90.0,
            engine_rpm=5000.0,
            vehicle_speed=60.0
        )
        
        self.assertIsInstance(safety, dict)
        self.assertIn('als_safe', safety)
    
    def test_calculate_als_parameters_enabled(self):
        """Test calculate_als_parameters with ALS enabled."""
        import time
        self.als.als_enabled = True
        self.als.last_activation_time = time.time() - 15.0  # Past cooldown
        
        params = self.als.calculate_als_parameters(
            vehicle_speed=50.0,
            throttle_position=0.0,
            current_turbo_rpm=40000.0,
            exhaust_temp=800.0
        )
        
        self.assertIsInstance(params, dict)
        self.assertIn('als_active', params)
    
    def test_calculate_exhaust_energy_boost(self):
        """Test calculate_exhaust_energy_boost method."""
        als_params = {'als_active': True}
        
        boosted = self.als.calculate_exhaust_energy_boost(1000.0, als_params)
        
        self.assertGreater(boosted, 1000.0)  # Should be boosted
        self.assertIsInstance(boosted, float)
    
    def test_calculate_exhaust_energy_boost_inactive(self):
        """Test calculate_exhaust_energy_boost with ALS inactive."""
        als_params = {'als_active': False}
        
        boosted = self.als.calculate_exhaust_energy_boost(1000.0, als_params)
        
        self.assertEqual(boosted, 1000.0)  # Should be unchanged
    
    def test_update_turbo_spool_als(self):
        """Test update_turbo_spool_als method."""
        self.als.als_active = True
        
        new_rpm = self.als.update_turbo_spool_als(
            current_turbo_rpm=50000.0,
            exhaust_energy=5000.0,
            time_step=0.1
        )
        
        self.assertIsInstance(new_rpm, (float, type(50000.0)))
        self.assertGreaterEqual(new_rpm, 0)
    
    def test_update_turbo_spool_als_inactive(self):
        """Test update_turbo_spool_als with ALS inactive."""
        self.als.als_active = False
        
        new_rpm = self.als.update_turbo_spool_als(
            current_turbo_rpm=50000.0,
            exhaust_energy=5000.0,
            time_step=0.1
        )
        
        self.assertEqual(new_rpm, 50000.0)  # Should be unchanged
    
    def test_safety_monitor_high_temp(self):
        """Test safety_monitor with high exhaust temperature."""
        safety = self.als.safety_monitor(
            exhaust_temp=960.0,  # Above max
            coolant_temp=90.0,
            engine_rpm=5000.0,
            vehicle_speed=60.0
        )
        
        self.assertFalse(safety['als_safe'])
        self.assertIsNotNone(safety['override_reason'])


class TestTwoStepRevLimiter(unittest.TestCase):
    """Test TwoStepRevLimiter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.two_step = TwoStepRevLimiter()
    
    def test_initialization(self):
        """Test TwoStepRevLimiter initialization."""
        self.assertFalse(self.two_step.two_step_enabled)
        self.assertEqual(self.two_step.launch_rpm, 4500)
        self.assertEqual(self.two_step.normal_redline, 6700)
        self.assertIn('ignition_cut', self.two_step.cut_strategies)
    
    def test_calculate_rev_limit_parameters(self):
        """Test calculate_rev_limit_parameters method."""
        params = self.two_step.calculate_rev_limit_parameters(
            engine_rpm=5000.0,
            vehicle_speed=0.0,
            clutch_position=0.0,  # Clutch depressed
            throttle_position=100.0
        )
        
        self.assertIsInstance(params, dict)
        self.assertIn('rev_limit_active', params)
    
    def test_calculate_exhaust_pop_effect(self):
        """Test calculate_exhaust_pop_effect method."""
        cut_params = {'ignition_retard': -15.0, 'fuel_cut_percent': 25.0}
        
        temp_increase = self.two_step.calculate_exhaust_pop_effect(
            cut_params, exhaust_temp=800.0
        )
        
        self.assertGreaterEqual(temp_increase, 0)
        self.assertLessEqual(temp_increase, 150.0)  # Capped at 150°C
        self.assertIsInstance(temp_increase, float)
    
    def test_calculate_rev_limit_parameters_launch(self):
        """Test calculate_rev_limit_parameters in launch mode."""
        self.two_step.two_step_enabled = True
        
        params = self.two_step.calculate_rev_limit_parameters(
            engine_rpm=4600.0,  # Above launch RPM
            vehicle_speed=0.0,
            clutch_position=0.0,  # Clutch depressed
            throttle_position=100.0
        )
        
        self.assertIsInstance(params, dict)
        self.assertIn('rev_limit_active', params)
    
    def test_calculate_rev_limit_parameters_normal(self):
        """Test calculate_rev_limit_parameters in normal mode."""
        self.two_step.two_step_enabled = True
        
        params = self.two_step.calculate_rev_limit_parameters(
            engine_rpm=6800.0,  # Above normal redline
            vehicle_speed=60.0,
            clutch_position=100.0,  # Clutch engaged
            throttle_position=100.0
        )
        
        self.assertIsInstance(params, dict)


class TestLaunchControlSystem(unittest.TestCase):
    """Test LaunchControlSystem class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.launch = LaunchControlSystem()
    
    def test_initialization(self):
        """Test LaunchControlSystem initialization."""
        self.assertFalse(self.launch.launch_control_enabled)
        self.assertFalse(self.launch.launch_active)
        self.assertEqual(self.launch.launch_rpm, 4500)
        self.assertIn('drag', self.launch.launch_strategies)
        self.assertIn('street', self.launch.launch_strategies)
        self.assertIn('track', self.launch.launch_strategies)
    
    def test_calculate_launch_parameters(self):
        """Test calculate_launch_parameters method."""
        params = self.launch.calculate_launch_parameters(
            vehicle_speed=0.0,
            engine_rpm=4500.0,
            throttle_position=100.0,
            clutch_position=0.0,
            wheel_speeds=[0.0, 0.0, 0.0, 0.0],
            current_boost=15.0
        )
        
        self.assertIsInstance(params, dict)
        self.assertIn('launch_active', params)
    
    def test_calculate_launch_timing_advance(self):
        """Test calculate_launch_timing_advance method."""
        timing = self.launch.calculate_launch_timing_advance(
            current_rpm=4500.0,
            current_boost=18.0,
            intake_temp=25.0
        )
        
        self.assertGreaterEqual(timing, 0)
        self.assertLessEqual(timing, 8.0)  # Maximum 8° advance
        self.assertIsInstance(timing, float)
    
    def test_calculate_launch_parameters_active(self):
        """Test calculate_launch_parameters with launch active."""
        self.launch.launch_control_enabled = True
        
        params = self.launch.calculate_launch_parameters(
            vehicle_speed=0.0,
            engine_rpm=4500.0,
            throttle_position=100.0,
            clutch_position=0.0,
            wheel_speeds=[0.0, 0.0, 0.0, 0.0],
            current_boost=15.0
        )
        
        self.assertIsInstance(params, dict)
        self.assertIn('launch_active', params)
    
    def test_calculate_launch_parameters_different_strategies(self):
        """Test calculate_launch_parameters with different strategies."""
        self.launch.launch_control_enabled = True
        
        # Test drag strategy
        self.launch.current_strategy = 'drag'
        params_drag = self.launch.calculate_launch_parameters(
            vehicle_speed=0.0,
            engine_rpm=4500.0,
            throttle_position=100.0,
            clutch_position=0.0,
            wheel_speeds=[0.0, 0.0, 0.0, 0.0],
            current_boost=15.0
        )
        self.assertIsInstance(params_drag, dict)
        
        # Test street strategy
        self.launch.current_strategy = 'street'
        params_street = self.launch.calculate_launch_parameters(
            vehicle_speed=0.0,
            engine_rpm=4500.0,
            throttle_position=100.0,
            clutch_position=0.0,
            wheel_speeds=[0.0, 0.0, 0.0, 0.0],
            current_boost=15.0
        )
        self.assertIsInstance(params_street, dict)


class TestAdvancedPerformanceManager(unittest.TestCase):
    """Test AdvancedPerformanceManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = AdvancedPerformanceManager()
    
    def test_initialization(self):
        """Test AdvancedPerformanceManager initialization."""
        self.assertIsNotNone(self.manager.anti_lag_system)
        self.assertIsNotNone(self.manager.two_step_limiter)
        self.assertIsNotNone(self.manager.launch_control_system)
        self.assertIn('street', self.manager.performance_modes)
        self.assertIn('track', self.manager.performance_modes)
        self.assertIn('drag', self.manager.performance_modes)
    
    def test_set_performance_mode_street(self):
        """Test set_performance_mode with street mode."""
        self.manager.set_performance_mode('street')
        
        self.assertEqual(self.manager.current_mode, 'street')
        self.assertFalse(self.manager.anti_lag_system.als_enabled)
        self.assertTrue(self.manager.two_step_limiter.two_step_enabled)
    
    def test_set_performance_mode_track(self):
        """Test set_performance_mode with track mode."""
        self.manager.set_performance_mode('track')
        
        self.assertEqual(self.manager.current_mode, 'track')
        self.assertTrue(self.manager.anti_lag_system.als_enabled)
        self.assertEqual(self.manager.anti_lag_system.als_mode, 'aggressive')
    
    def test_set_performance_mode_drag(self):
        """Test set_performance_mode with drag mode."""
        self.manager.set_performance_mode('drag')
        
        self.assertEqual(self.manager.current_mode, 'drag')
        self.assertTrue(self.manager.anti_lag_system.als_enabled)
        self.assertEqual(self.manager.anti_lag_system.als_mode, 'rally')
    
    def test_set_performance_mode_invalid(self):
        """Test set_performance_mode with invalid mode."""
        with self.assertRaises(ValueError):
            self.manager.set_performance_mode('invalid_mode')
    
    def test_calculate_integrated_performance_parameters(self):
        """Test calculate_integrated_performance_parameters method."""
        sensor_data = {
            'vehicle_speed': 0.0,
            'engine_rpm': 4500.0,
            'throttle_position': 100.0,
            'clutch_position': 0.0,
            'boost_psi': 18.0,
            'turbo_rpm': 50000.0,
            'exhaust_temp': 800.0,
            'wheel_speeds': [0.0, 0.0, 0.0, 0.0],
            'current_gear': 1,
            'intake_temp': 25.0,
            'coolant_temp': 90.0
        }
        
        params = self.manager.calculate_integrated_performance_parameters(sensor_data)
        
        self.assertIsInstance(params, dict)


if __name__ == '__main__':
    unittest.main()

