#!/usr/bin/env python3
"""
COMPREHENSIVE TEST SUITE FOR MAZDASPEED 3 TUNING SYSTEM
Unit tests and integration tests for all components
"""

import unittest
import numpy as np
from app.database.ecu_database import Mazdaspeed3Database, ECUCalibration
from app.services.ai_tuner import AITuningSystem
from app.services.physics_engine import TurbochargerPhysics, EngineThermodynamics
from app.services.dealer_service import MazdaDealerSecurity
from app.services.performance_features import AntiLagSystem, TwoStepRevLimiter, LaunchControlSystem
from app.models.engine_models import IdealGasPhysics, TurbochargerDynamics
from app.models.turbo_models import K04Turbocharger
from app.utils.calculations import AdvancedCalculations, TuningSecrets
from app.utils.security import SecurityManager

class TestECUDatabase(unittest.TestCase):
    """Test ECU database functionality"""
    
    def setUp(self):
        self.db = Mazdaspeed3Database(':memory:')  # Use in-memory database for testing
    
    def test_factory_calibration_loading(self):
        """Test loading factory calibration data"""
        calibration = self.db.get_factory_calibration()
        self.assertIsNotNone(calibration)
        self.assertEqual(calibration.vehicle_model, "MAZDASPEED3_2011")
    
    def test_ignition_map_retrieval(self):
        """Test ignition map retrieval and structure"""
        calibration = self.db.get_factory_calibration()
        ignition_map = calibration.get_ignition_map('high')
        self.assertEqual(ignition_map.shape, (16, 16))  # 16x16 map

class TestPhysicsEngine(unittest.TestCase):
    """Test physics engine calculations"""
    
    def setUp(self):
        self.turbo_physics = TurbochargerPhysics()
        self.engine_thermo = EngineThermodynamics()
        self.calculations = AdvancedCalculations()
    
    def test_airflow_calculation(self):
        """Test airflow calculation accuracy"""
        mass_flow = self.turbo_physics.calculate_airflow(5000, 18.0, 25.0)
        self.assertGreater(mass_flow, 0.05)
        self.assertLess(mass_flow, 0.2)  # Within K04 limits
    
    def test_horsepower_calculation(self):
        """Test exact horsepower calculation"""
        # Test known values: 300 lb-ft at 5000 RPM = 285 HP
        torque_nm = 300 * 1.35582  # Convert lb-ft to N·m
        horsepower = self.calculations.calculate_brake_horsepower(torque_nm, 5000)
        self.assertAlmostEqual(horsepower, 285, delta=5)  # Within 5 HP
    
    def test_boost_pressure_conversion(self):
        """Test boost pressure to pressure ratio conversion"""
        pressure_ratio = self.calculations.calculate_pressure_ratio(18.0)
        self.assertAlmostEqual(pressure_ratio, 2.23, delta=0.1)  # ~2.23:1 for 18 PSI
        
        boost_psi = self.calculations.calculate_boost_pressure(2.23)
        self.assertAlmostEqual(boost_psi, 18.0, delta=0.5)  # Round-trip accuracy

class TestAITuning(unittest.TestCase):
    """Test AI tuning system"""
    
    def setUp(self):
        self.ai_tuner = AITuningSystem()
    
    def test_real_time_optimization(self):
        """Test real-time optimization with sample data"""
        sample_data = {
            'rpm': 4500,
            'load': 1.2,
            'boost_psi': 16.5,
            'ignition_timing': 14.0,
            'afr': 11.5,
            'knock_retard': -1.0,
            'intake_temp': 28.0,
            'coolant_temp': 92.0,
            'throttle_position': 85.0,
            'manifold_pressure': 220.0,
            'vvt_intake_angle': 20.0,
            'fuel_trim_long': 1.5
        }
        
        adjustments = self.ai_tuner.real_time_optimization(sample_data)
        self.assertIsInstance(adjustments, dict)
        
        # Verify adjustments are within reasonable bounds
        if 'ignition_timing' in adjustments:
            self.assertGreaterEqual(adjustments['ignition_timing'], -5.0)
            self.assertLessEqual(adjustments['ignition_timing'], 5.0)
        
        if 'boost_target' in adjustments:
            self.assertGreaterEqual(adjustments['boost_target'], 12.0)
            self.assertLessEqual(adjustments['boost_target'], 22.0)

class TestPerformanceFeatures(unittest.TestCase):
    """Test anti-lag, 2-step, and launch control"""
    
    def setUp(self):
        self.anti_lag = AntiLagSystem()
        self.two_step = TwoStepRevLimiter()
        self.launch_control = LaunchControlSystem()
    
    def test_anti_lag_activation(self):
        """Test anti-lag system activation conditions"""
        # Conditions that should activate ALS
        als_params = self.anti_lag.calculate_als_parameters(
            vehicle_speed=50.0,
            throttle_position=0.0,  # Off-throttle
            current_turbo_rpm=60000,
            exhaust_temp=800.0
        )
        
        # ALS should not activate immediately (needs more conditions)
        self.assertFalse(als_params.get('als_active', False))
    
    def test_two_step_rev_limiting(self):
        """Test 2-step rev limiter operation"""
        # Stationary, clutch in, full throttle - should activate launch control
        params = self.two_step.calculate_rev_limit_parameters(
            engine_rpm=5000,
            vehicle_speed=0.0,
            clutch_position=0.0,  # Clutch depressed
            throttle_position=100.0  # Full throttle
        )
        
        self.assertTrue(params['rev_limit_active'])
        self.assertEqual(params['target_rpm'], self.two_step.launch_rpm)
    
    def test_launch_control_parameters(self):
        """Test launch control parameter calculation"""
        params = self.launch_control.calculate_launch_parameters(
            vehicle_speed=0.0,
            engine_rpm=4500,
            throttle_position=100.0,
            clutch_position=0.0,
            wheel_speeds=[0.0, 0.0, 0.0, 0.0],
            current_boost=0.0
        )
        
        self.assertTrue(params['launch_active'])
        self.assertGreater(params['target_boost'], 0.0)

class TestTurboModels(unittest.TestCase):
    """Test K04 turbocharger specific models"""
    
    def setUp(self):
        self.k04_turbo = K04Turbocharger()
    
    def test_compressor_operation(self):
        """Test compressor operation point calculation"""
        # Typical operating point: 120k corrected speed, 2.0 pressure ratio
        op_point = self.k04_turbo.calculate_compressor_operation(120000, 2.0)
        
        self.assertGreater(op_point['mass_flow'], 0.05)
        self.assertLess(op_point['mass_flow'], 0.2)
        self.assertGreater(op_point['efficiency'], 0.6)
        self.assertLess(op_point['efficiency'], 0.8)
    
    def test_turbine_efficiency(self):
        """Test turbine efficiency calculation"""
        # Optimal velocity ratio ~0.65
        efficiency = self.k04_turbo.calculate_turbine_efficiency(0.65, 2.0)
        self.assertGreater(efficiency, 0.7)  # Should be near peak efficiency
        
        # Poor velocity ratio
        poor_efficiency = self.k04_turbo.calculate_turbine_efficiency(0.3, 2.0)
        self.assertLess(poor_efficiency, efficiency)  # Should be lower

class TestSecurity(unittest.TestCase):
    """Test security and encryption functionality"""
    
    def setUp(self):
        self.security = SecurityManager("test_master_key")
    
    def test_calibration_encryption(self):
        """Test calibration data encryption and decryption"""
        test_calibration = {
            'ignition_map': [[10.0, 12.0], [11.0, 13.0]],
            'fuel_map': [[2.5, 2.6], [2.4, 2.5]],
            'boost_target': 18.0
        }
        
        # Encrypt calibration
        encrypted = self.security.encrypt_calibration_data(test_calibration)
        self.assertIsInstance(encrypted, str)
        self.assertGreater(len(encrypted), 0)
        
        # Decrypt calibration
        decrypted = self.security.decrypt_calibration_data(encrypted)
        self.assertEqual(decrypted, test_calibration)
    
    def test_vehicle_signature(self):
        """Test vehicle signature generation and verification"""
        vin = "JM1BL143141123456"
        calibration_id = "L3K9-188K1-11A"
        
        # Generate signature
        signature = self.security.generate_vehicle_signature(vin, calibration_id)
        self.assertIsInstance(signature, str)
        
        # Verify signature
        is_valid = self.security.verify_vehicle_signature(signature, vin, calibration_id)
        self.assertTrue(is_valid)
        
        # Test with wrong VIN
        is_invalid = self.security.verify_vehicle_signature(signature, "WRONGVIN", calibration_id)
        self.assertFalse(is_invalid)

class TestTuningSecrets(unittest.TestCase):
    """Test proprietary tuning secrets"""
    
    def setUp(self):
        self.secrets = TuningSecrets()
    
    def test_faster_spool_technique(self):
        """Test faster spool tuning secret"""
        adjustments = self.secrets.apply_tuning_secret('faster_spool_lower_psi', {
            'rpm': 2500,
            'target_boost': 18.0,
            'current_boost': 8.0,
            'throttle_position': 100.0
        })
        
        # Should suggest WGDC reduction for faster spool
        self.assertIn('wgdc_reduction', adjustments)
        self.assertGreater(adjustments['wgdc_reduction'], 0.0)
    
    def test_vvt_optimization(self):
        """Test VVT optimization secret"""
        adjustments = self.secrets.apply_tuning_secret('vvt_torque_optimization', {
            'rpm': 4000,
            'load': 1.2,
            'throttle_position': 80.0
        })
        
        # Should suggest VVT adjustments
        self.assertTrue(
            any(key.startswith('vvt_') for key in adjustments.keys())
        )

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)