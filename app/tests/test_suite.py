#!/usr/bin/env python3
"""
COMPREHENSIVE TEST SUITE FOR MAZDASPEED 3 TUNING SYSTEM
Unit tests and integration tests for all components
"""

import unittest
import numpy as np
import tempfile
import os
from ..database.ecu_database import Mazdaspeed3Database, ECUCalibration
from ..services.ai_tuner import AITuningSystem
from ..services.physics_engine import TurbochargerPhysics, EngineThermodynamics
from ..services.dealer_service import MazdaDealerSecurity
from ..services.performance_features import AntiLagSystem, TwoStepRevLimiter, LaunchControlSystem
from ..models.engine_models import IdealGasPhysics, TurbochargerDynamics
from ..models.turbo_models import K04Turbocharger
from ..utils.calculations import AdvancedCalculations, TuningSecrets
from ..utils.security import SecurityManager

class TestECUDatabase(unittest.TestCase):
    """Test ECU database functionality"""
    
    def setUp(self):
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.db = Mazdaspeed3Database(self.db_path)
    
    def tearDown(self):
        # Clean up temporary database
        self.db.session.close()
        os.unlink(self.db_path)
    
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
        # Test pressure ratio calculation
        manifold_pressure_kpa = 101.325 + (18.0 * 6.89476)  # Atmospheric + boost
        pressure_ratio = manifold_pressure_kpa / 101.325
        self.assertAlmostEqual(pressure_ratio, 2.23, delta=0.1)  # ~2.23:1 for 18 PSI
    
    def test_compressor_efficiency(self):
        """Test compressor efficiency calculation"""
        efficiency = self.turbo_physics._calculate_compressor_efficiency(2.0, 0.1)
        self.assertGreater(efficiency, 0.5)
        self.assertLessEqual(efficiency, 0.78)  # Max efficiency for K04

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
    
    def test_safety_limits(self):
        """Test safety limit enforcement"""
        # Test with extreme values
        extreme_data = {
            'rpm': 8000,  # Over limit
            'boost_psi': 30.0,  # Over limit
            'knock_retard': -10.0,  # Severe knock
            'load': 1.5,
            'ignition_timing': 20.0,
            'afr': 10.0,
            'intake_temp': 80.0,
            'coolant_temp': 120.0,
            'throttle_position': 100.0
        }
        
        adjustments = self.ai_tuner.real_time_optimization(extreme_data)
        
        # Should have conservative adjustments due to safety
        if 'boost_target' in adjustments:
            self.assertLessEqual(adjustments['boost_target'], 22.0)

class TestPerformanceFeatures(unittest.TestCase):
    """Test performance features"""
    
    def setUp(self):
        self.als = AntiLagSystem()
        self.two_step = TwoStepRevLimiter()
        self.launch_control = LaunchControlSystem()
    
    def test_als_activation(self):
        """Test anti-lag system activation"""
        params = self.als.calculate_als_parameters(
            vehicle_speed=30,  # Low speed
            throttle_position=0,  # Throttle lift
            current_turbo_rpm=40000,
            exhaust_temp=800,
            coolant_temp=90,
            intake_temp=30,
            oil_pressure=40,
            engine_rpm=4000
        )
        
        # ALS should activate under these conditions
        self.assertTrue(params.get('als_active', False))
    
    def test_two_step_activation(self):
        """Test two-step rev limiter"""
        params = self.two_step.calculate_rev_limit_parameters(
            engine_rpm=4500,
            vehicle_speed=8,
            clutch_position=0,  # Clutch disengaged
            throttle_position=100  # Full throttle
        )
        
        self.assertTrue(params.get('rev_limit_active', False))
    
    def test_launch_control(self):
        """Test launch control system"""
        params = self.launch_control.calculate_launch_parameters(
            vehicle_speed=5,
            engine_rpm=4500,
            throttle_position=100,
            clutch_position=0,
            wheel_speeds=[5, 5, 5, 5],
            current_boost=5.0,
            gear=1
        )
        
        self.assertTrue(params.get('launch_active', False))

class TestTurboModels(unittest.TestCase):
    """Test turbocharger models"""
    
    def setUp(self):
        self.k04 = K04Turbocharger()
    
    def test_compressor_map(self):
        """Test compressor map lookup"""
        operating_point = self.k04.compressor.get_operating_point(
            corrected_speed=100000,
            corrected_flow=0.1
        )
        
        self.assertGreater(operating_point['pressure_ratio'], 1.0)
        self.assertLess(operating_point['pressure_ratio'], 3.0)
        self.assertGreater(operating_point['efficiency'], 0.5)
    
    def test_turbo_spool_time(self):
        """Test turbo spool time calculation"""
        spool_time = self.k04.calculate_spool_time(
            current_speed=30000,
            target_speed=100000,
            exhaust_energy=5000  # Watts
        )
        
        self.assertGreater(spool_time, 0)
        self.assertLess(spool_time, 5.0)  # Should spool within 5 seconds

class TestSecurity(unittest.TestCase):
    """Test security features"""
    
    def setUp(self):
        self.security = SecurityManager('test_password')
    
    def test_data_encryption(self):
        """Test data encryption/decryption"""
        test_data = {'calibration': 'secret_data', 'maps': [1, 2, 3]}
        
        # Encrypt
        encrypted = self.security.encrypt_calibration_data(test_data)
        self.assertIsInstance(encrypted, bytes)
        
        # Decrypt
        decrypted = self.security.decrypt_calibration_data(encrypted)
        self.assertEqual(decrypted, test_data)
    
    def test_vehicle_signature(self):
        """Test vehicle signature generation"""
        vin = "JM1BL1V44A1234567"
        ecu_id = "L3K9-188K1"
        calibration_id = "STAGE1_TUNE"
        
        signature = self.security.generate_vehicle_signature(vin, ecu_id, calibration_id)
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)  # SHA256 hex length
        
        # Verify signature
        is_valid = self.security.verify_vehicle_signature(vin, ecu_id, calibration_id, signature)
        self.assertTrue(is_valid)

class TestTuningSecrets(unittest.TestCase):
    """Test tuning secrets and techniques"""
    
    def setUp(self):
        self.secrets = TuningSecrets()
    
    def test_faster_spool_technique(self):
        """Test faster spool technique"""
        adjustments = self.secrets.apply_faster_spool_technique(
            current_rpm=2500,
            target_boost=18.0,
            current_boost=5.0
        )
        
        self.assertIn('ignition_timing', adjustments)
        self.assertIn('fuel_enrichment', adjustments)
        self.assertLess(adjustments['ignition_timing'], 0)  # Should retard timing
    
    def test_vvt_optimization(self):
        """Test VVT optimization"""
        adjustments = self.secrets.apply_vvt_optimization(rpm=3000, load=0.8)
        
        self.assertIn('intake_cam', adjustments)
        self.assertIn('exhaust_cam', adjustments)
        self.assertGreater(adjustments['intake_cam'], 0)  # Should advance intake
    
    def test_knock_management(self):
        """Test knock management"""
        adjustments = self.secrets.apply_knock_management(
            knock_retard=-3.0,
            cylinder_temps=[900, 950, 920, 910]
        )
        
        self.assertIn('timing_retard', adjustments)
        self.assertIn('fuel_enrichment', adjustments)
        self.assertLess(adjustments['timing_retard'], 0)

class TestIntegration(unittest.TestCase):
    """Integration tests for complete system"""
    
    def setUp(self):
        # Initialize all components
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        self.db = Mazdaspeed3Database(self.db_path)
        self.ai_tuner = AITuningSystem()
        self.physics = TurbochargerPhysics()
        self.calculations = AdvancedCalculations()
    
    def tearDown(self):
        self.db.session.close()
        os.unlink(self.db_path)
    
    def test_complete_tuning_loop(self):
        """Test complete tuning optimization loop"""
        # Get factory calibration
        calibration = self.db.get_factory_calibration()
        self.assertIsNotNone(calibration)
        
        # Simulate sensor data
        sensor_data = {
            'rpm': 4000,
            'load': 1.0,
            'boost_psi': 15.0,
            'ignition_timing': 12.0,
            'afr': 12.0,
            'knock_retard': 0,
            'intake_temp': 30,
            'coolant_temp': 90,
            'throttle_position': 75
        }
        
        # Get AI adjustments
        ai_adjustments = self.ai_tuner.real_time_optimization(sensor_data)
        
        # Calculate physics
        airflow = self.physics.calculate_airflow(
            sensor_data['rpm'],
            sensor_data['boost_psi'],
            sensor_data['intake_temp']
        )
        
        # Calculate power
        torque = self.calculations.calculate_engine_torque(280, sensor_data['rpm'])
        
        # Verify results
        self.assertGreater(airflow, 0)
        self.assertGreater(torque, 0)
        self.assertIsInstance(ai_adjustments, dict)
    
    def test_performance_calculation_chain(self):
        """Test performance calculation chain"""
        # Test data
        rpm = 5000
        boost = 18.0
        afr = 12.0
        
        # Calculate airflow
        airflow = self.physics.calculate_airflow(rpm, boost, 25)
        
        # Calculate fuel requirement
        fuel_mass, fuel_volume = self.calculations.calculate_fuel_flow_rate(
            265,  # cc/min
            50,   # % duty
            3.0   # bar
        )
        
        # Calculate power
        torque = self.calculations.calculate_engine_torque(330, rpm)
        horsepower = self.calculations.calculate_brake_horsepower(torque, rpm)
        
        # Verify calculations
        self.assertGreater(airflow, 0)
        self.assertGreater(fuel_mass, 0)
        self.assertGreater(horsepower, 300)
        self.assertAlmostEqual(horsepower, 330, delta=10)

# Test runner
if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestECUDatabase,
        TestPhysicsEngine,
        TestAITuning,
        TestPerformanceFeatures,
        TestTurboModels,
        TestSecurity,
        TestTuningSecrets,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
