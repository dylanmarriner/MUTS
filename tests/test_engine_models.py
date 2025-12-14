"""Tests for models engine_models module."""
import unittest

# Import directly to avoid muts package import issues
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'muts' / 'models'))
from engine_models import IdealGasPhysics, TurbochargerDynamics, EngineCycleAnalysis


class TestIdealGasPhysics(unittest.TestCase):
    """Test IdealGasPhysics class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.physics = IdealGasPhysics()
    
    def test_initialization(self):
        """Test IdealGasPhysics initialization."""
        self.assertEqual(self.physics.R_specific, 287.05)
        self.assertEqual(self.physics.gamma_air, 1.4)
        self.assertEqual(self.physics.gamma_exhaust, 1.33)
    
    def test_calculate_ideal_gas_velocity_air(self):
        """Test calculate_ideal_gas_velocity for air."""
        velocity = self.physics.calculate_ideal_gas_velocity(
            temperature=300.0,  # 27°C
            pressure_ratio=2.0,
            gas_type='air'
        )
        
        self.assertGreater(velocity, 0)
        self.assertIsInstance(velocity, float)
    
    def test_calculate_ideal_gas_velocity_exhaust(self):
        """Test calculate_ideal_gas_velocity for exhaust."""
        velocity = self.physics.calculate_ideal_gas_velocity(
            temperature=800.0,  # Hot exhaust
            pressure_ratio=1.5,
            gas_type='exhaust'
        )
        
        self.assertGreater(velocity, 0)
        self.assertIsInstance(velocity, float)
    
    def test_calculate_ideal_gas_velocity_choked(self):
        """Test calculate_ideal_gas_velocity with choked flow."""
        # Use very high pressure ratio to ensure choked flow
        velocity = self.physics.calculate_ideal_gas_velocity(
            temperature=300.0,
            pressure_ratio=0.5,  # Low downstream/upstream ratio = choked
            gas_type='air'
        )
        
        self.assertGreater(velocity, 0)
    
    def test_calculate_mass_flow_rate(self):
        """Test calculate_mass_flow_rate method."""
        mass_flow = self.physics.calculate_mass_flow_rate(
            area=0.001,  # 1 cm²
            upstream_pressure=200.0,  # kPa
            upstream_temp=300.0,  # K (27°C)
            downstream_pressure=100.0,  # kPa
            gas_type='air',
            efficiency=0.95
        )
        
        self.assertGreater(mass_flow, 0)
        self.assertIsInstance(mass_flow, float)
    
    def test_calculate_mass_flow_rate_exhaust(self):
        """Test calculate_mass_flow_rate for exhaust gas."""
        mass_flow = self.physics.calculate_mass_flow_rate(
            area=0.001,
            upstream_pressure=250.0,
            upstream_temp=800.0,  # Hot exhaust
            downstream_pressure=101.325,
            gas_type='exhaust',
            efficiency=0.90
        )
        
        self.assertGreater(mass_flow, 0)


class TestTurbochargerDynamics(unittest.TestCase):
    """Test TurbochargerDynamics class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.turbo = TurbochargerDynamics()
    
    def test_initialization(self):
        """Test TurbochargerDynamics initialization."""
        self.assertIsNotNone(self.turbo.gas_physics)
        self.assertIsInstance(self.turbo.gas_physics, IdealGasPhysics)
        self.assertIsNotNone(self.turbo.turbo_specs)
    
    def test_initialize_turbo_specs(self):
        """Test _initialize_turbo_specs method."""
        specs = self.turbo._initialize_turbo_specs()
        
        self.assertIn('compressor', specs)
        self.assertIn('turbine', specs)
        self.assertIn('inducer_diameter', specs['compressor'])
    
    def test_calculate_turbine_power(self):
        """Test calculate_turbine_power method."""
        power, rpm, efficiency = self.turbo.calculate_turbine_power(
            turbo_rpm=150000.0,
            exhaust_mass_flow=0.2,
            exhaust_temp=800.0,
            turbine_inlet_pressure=250.0,
            turbine_outlet_pressure=101.325
        )
        
        self.assertIsInstance(power, float)
        self.assertIsInstance(rpm, float)
        self.assertIsInstance(efficiency, float)
        self.assertGreaterEqual(efficiency, 0)
        self.assertLessEqual(efficiency, 1.0)
    
    def test_get_compressor_efficiency(self):
        """Test _get_compressor_efficiency method."""
        efficiency = self.turbo._get_compressor_efficiency(
            pressure_ratio=2.0,
            corrected_speed=150000.0,
            mass_flow=0.15
        )
        
        self.assertGreaterEqual(efficiency, 0.5)  # Minimum 50%
        self.assertLessEqual(efficiency, 1.0)
        self.assertIsInstance(efficiency, float)


class TestEngineCycleAnalysis(unittest.TestCase):
    """Test EngineCycleAnalysis class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cycle = EngineCycleAnalysis()
    
    def test_initialization(self):
        """Test EngineCycleAnalysis initialization."""
        self.assertIsNotNone(self.cycle.gas_physics)
        self.assertIsNotNone(self.cycle.engine_specs)
        self.assertIn('displacement', self.cycle.engine_specs)
    
    def test_initialize_engine_specs(self):
        """Test _initialize_engine_specs method."""
        specs = self.cycle._initialize_engine_specs()
        
        self.assertIn('displacement', specs)
        self.assertIn('compression_ratio', specs)
        self.assertIn('ve_table', specs)
    
    def test_create_detailed_ve_table(self):
        """Test _create_detailed_ve_table method."""
        ve_table = self.cycle._create_detailed_ve_table()
        
        self.assertIn('rpm', ve_table)
        self.assertIn('load', ve_table)
        self.assertIn('efficiency', ve_table)
        self.assertGreater(ve_table['efficiency'].size, 0)
    
    def test_calculate_indicated_mean_effective_pressure(self):
        """Test calculate_indicated_mean_effective_pressure method."""
        imep = self.cycle.calculate_indicated_mean_effective_pressure(
            rpm=5000.0,
            load=1.0,
            afr=12.5,
            ignition_timing=20.0,
            boost_pressure=20.0,
            intake_temp=25.0
        )
        
        self.assertGreater(imep, 0)
        self.assertIsInstance(imep, float)


if __name__ == '__main__':
    unittest.main()

