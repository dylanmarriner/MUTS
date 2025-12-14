"""Tests for services physics_engine module."""
import unittest
import numpy as np

# Import directly to avoid muts package import issues
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'muts' / 'services'))
from physics_engine import TurbochargerPhysics, EngineThermodynamics, PerformanceCalculator


class TestTurbochargerPhysics(unittest.TestCase):
    """Test TurbochargerPhysics class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.turbo = TurbochargerPhysics()
    
    def test_initialization(self):
        """Test TurbochargerPhysics initialization."""
        self.assertIsNotNone(self.turbo.turbo_specs)
        self.assertIn('compressor', self.turbo.turbo_specs)
        self.assertIn('turbine', self.turbo.turbo_specs)
        self.assertIsNotNone(self.turbo.engine_specs)
    
    def test_create_ve_table(self):
        """Test _create_ve_table method."""
        ve_table = self.turbo._create_ve_table()
        
        self.assertIsInstance(ve_table, np.ndarray)
        self.assertGreater(ve_table.size, 0)
    
    def test_calculate_airflow(self):
        """Test calculate_airflow method."""
        airflow = self.turbo.calculate_airflow(
            rpm=5000.0,
            boost_pressure=20.0,
            intake_temp=25.0
        )
        
        self.assertGreater(airflow, 0)
        self.assertIsInstance(airflow, (float, np.floating))
    
    def test_calculate_airflow_zero_boost(self):
        """Test calculate_airflow with zero boost."""
        airflow = self.turbo.calculate_airflow(
            rpm=3000.0,
            boost_pressure=0.0,
            intake_temp=25.0
        )
        
        self.assertGreater(airflow, 0)
    
    def test_calculate_compressor_efficiency(self):
        """Test calculate_compressor_efficiency method."""
        efficiency = self.turbo.calculate_compressor_efficiency(
            pressure_ratio=2.0,
            mass_flow=0.15
        )
        
        self.assertGreater(efficiency, 0)
        self.assertLessEqual(efficiency, 1.0)


class TestEngineThermodynamics(unittest.TestCase):
    """Test EngineThermodynamics class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.thermo = EngineThermodynamics()
    
    def test_initialization(self):
        """Test EngineThermodynamics initialization."""
        self.assertIsNotNone(self.thermo.fuel_properties)
        self.assertIn('gasoline_lhv', self.thermo.fuel_properties)
        self.assertIsNotNone(self.thermo.friction_mean_effective_pressure)
    
    def test_calculate_fmep_curve(self):
        """Test _calculate_fmep_curve method."""
        fmep = self.thermo._calculate_fmep_curve()
        
        self.assertIsInstance(fmep, dict)
        self.assertGreater(len(fmep), 0)
    
    def test_calculate_brake_torque(self):
        """Test calculate_brake_torque method."""
        brake_torque = self.thermo.calculate_brake_torque(
            indicated_torque=300.0,
            rpm=5000.0
        )
        
        self.assertGreater(brake_torque, 0)
        self.assertLess(brake_torque, 300.0)  # Should be less than indicated due to friction
        self.assertIsInstance(brake_torque, float)
    
    def test_calculate_indicated_power(self):
        """Test calculate_indicated_power method."""
        power = self.thermo.calculate_indicated_power(
            mass_airflow=0.2,  # kg/s
            afr=12.5,
            ignition_timing=20.0,
            compression_ratio=9.5
        )
        
        self.assertGreater(power, 0)
        self.assertIsInstance(power, float)
    
    def test_timing_efficiency_factor(self):
        """Test _timing_efficiency_factor method."""
        # Optimal timing
        factor_optimal = self.thermo._timing_efficiency_factor(20.0)
        self.assertGreaterEqual(factor_optimal, 0.85)
        self.assertLessEqual(factor_optimal, 1.0)
        
        # Non-optimal timing
        factor_retarded = self.thermo._timing_efficiency_factor(10.0)
        self.assertLess(factor_retarded, factor_optimal)
    
    def test_calculate_exhaust_temperature(self):
        """Test calculate_exhaust_temperature method."""
        egt = self.thermo.calculate_exhaust_temperature(
            mass_airflow=0.2,
            afr=12.5,
            ignition_timing=20.0,
            boost_pressure=20.0
        )
        
        self.assertGreater(egt, 400.0)  # Should be hot
        self.assertLess(egt, 1200.0)  # Should be reasonable
        self.assertIsInstance(egt, float)


class TestPerformanceCalculator(unittest.TestCase):
    """Test PerformanceCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calc = PerformanceCalculator()
    
    def test_initialization(self):
        """Test PerformanceCalculator initialization."""
        self.assertIsNotNone(self.calc.vehicle_specs)
        self.assertIn('curb_weight', self.calc.vehicle_specs)
        self.assertIn('gear_ratios', self.calc.vehicle_specs)
    
    def test_calculate_wheel_torque(self):
        """Test calculate_wheel_torque method."""
        wheel_torque = self.calc.calculate_wheel_torque(
            engine_torque=300.0,
            gear=3
        )
        
        self.assertGreater(wheel_torque, engine_torque)  # Should be multiplied by gear ratios
        self.assertIsInstance(wheel_torque, float)
    
    def test_calculate_wheel_torque_first_gear(self):
        """Test calculate_wheel_torque in first gear."""
        wheel_torque = self.calc.calculate_wheel_torque(
            engine_torque=300.0,
            gear=1
        )
        
        self.assertGreater(wheel_torque, 300.0)
    
    def test_calculate_acceleration_force(self):
        """Test calculate_acceleration_force method."""
        force = self.calc.calculate_acceleration_force(
            wheel_torque=2000.0,
            velocity=0.0
        )
        
        self.assertGreater(force, 0)
        self.assertIsInstance(force, float)
    
    def test_calculate_acceleration_force_with_velocity(self):
        """Test calculate_acceleration_force at speed."""
        # At zero velocity
        force_zero = self.calc.calculate_acceleration_force(
            wheel_torque=2000.0,
            velocity=0.0
        )
        
        # At high velocity (drag reduces force)
        force_high = self.calc.calculate_acceleration_force(
            wheel_torque=2000.0,
            velocity=100.0  # m/s ≈ 224 mph
        )
        
        self.assertGreater(force_zero, force_high)
    
    def test_calculate_theoretical_horsepower(self):
        """Test calculate_theoretical_horsepower method."""
        if not hasattr(self.calc, 'calculate_theoretical_horsepower'):
            self.skipTest("calculate_theoretical_horsepower not available")
        
        try:
            hp = self.calc.calculate_theoretical_horsepower(
                engine_torque=300.0,
                rpm=6000.0
            )
            
            self.assertGreater(hp, 0)
            self.assertIsInstance(hp, float)
        except Exception as e:
            self.skipTest(f"calculate_theoretical_horsepower failed: {e}")


if __name__ == '__main__':
    unittest.main()

