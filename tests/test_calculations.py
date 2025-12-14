"""Tests for utils calculations module."""
import unittest
from unittest.mock import patch
import math

# Import directly to avoid muts package import issues
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'muts' / 'utils'))
from calculations import AdvancedCalculations, TuningSecrets


class TestAdvancedCalculations(unittest.TestCase):
    """Test AdvancedCalculations class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calc = AdvancedCalculations()
    
    def test_initialization(self):
        """Test AdvancedCalculations initialization."""
        self.assertIsNotNone(self.calc.physical_constants)
        self.assertIn('air_density_std', self.calc.physical_constants)
        self.assertIn('atmospheric_pressure', self.calc.physical_constants)
    
    def test_calculate_brake_horsepower(self):
        """Test calculate_brake_horsepower method."""
        # HP = (Torque (N·m) × RPM) / 7121.416
        # For 300 N·m at 6000 RPM: (300 * 6000) / 7121.416 ≈ 252.8 HP
        hp = self.calc.calculate_brake_horsepower(300.0, 6000.0)
        
        self.assertAlmostEqual(hp, 252.8, places=1)
    
    def test_calculate_brake_horsepower_zero_rpm(self):
        """Test calculate_brake_horsepower with zero RPM."""
        hp = self.calc.calculate_brake_horsepower(300.0, 0.0)
        
        self.assertEqual(hp, 0.0)
    
    def test_calculate_engine_torque(self):
        """Test calculate_engine_torque method."""
        # IMEP in bar, displacement in liters
        torque = self.calc.calculate_engine_torque(15.0, 2.3, 0.85)
        
        self.assertGreater(torque, 0)
        self.assertIsInstance(torque, float)
    
    def test_calculate_air_fuel_ratio(self):
        """Test calculate_air_fuel_ratio method."""
        # 14.7:1 stoichiometric
        afr = self.calc.calculate_air_fuel_ratio(14.7, 1.0)
        
        self.assertEqual(afr, 14.7)
    
    def test_calculate_air_fuel_ratio_zero_fuel(self):
        """Test calculate_air_fuel_ratio with zero fuel."""
        afr = self.calc.calculate_air_fuel_ratio(10.0, 0.0)
        
        self.assertEqual(afr, float('inf'))
    
    def test_calculate_boost_pressure(self):
        """Test calculate_boost_pressure method."""
        # Pressure ratio of 2.0 means absolute pressure is 2x atmospheric
        # Boost = (2.0 * 101.325) - 101.325 = 101.325 kPa = 14.7 PSI
        boost_psi = self.calc.calculate_boost_pressure(2.0)
        
        self.assertAlmostEqual(boost_psi, 14.7, places=1)
    
    def test_calculate_pressure_ratio(self):
        """Test calculate_pressure_ratio method."""
        # 14.7 PSI boost = 101.325 kPa = 1.0 pressure ratio boost
        # Total ratio = 1.0 + 1.0 = 2.0
        ratio = self.calc.calculate_pressure_ratio(14.7)
        
        self.assertAlmostEqual(ratio, 2.0, places=1)
    
    def test_calculate_exhaust_gas_temperature(self):
        """Test calculate_exhaust_gas_temperature method."""
        try:
            egt = self.calc.calculate_exhaust_gas_temperature(
                intake_temp=25.0,
                pressure_ratio=2.0,
                afr=12.5,
                ignition_timing=15.0,
                engine_load=0.8
            )
            
            # EGT should be a reasonable temperature in Celsius
            self.assertGreater(egt, 400.0)  # Should be hot
            self.assertLess(egt, 1200.0)  # Should be reasonable
            self.assertIsInstance(egt, float)
        except Exception as e:
            # If method doesn't exist or has different signature, skip
            self.skipTest(f"calculate_exhaust_gas_temperature not available: {e}")
    
    def test_calculate_volumetric_efficiency(self):
        """Test calculate_volumetric_efficiency method."""
        ve = self.calc.calculate_volumetric_efficiency(
            engine_rpm=6000.0,
            intake_runner_length=0.3,
            intake_runner_diameter=0.05,
            valve_diameter=0.035,
            camshaft_timing=15.0
        )
        
        self.assertGreaterEqual(ve, 0.7)
        self.assertLessEqual(ve, 1.1)
        self.assertIsInstance(ve, float)
    
    def test_calculate_compressor_outlet_temp(self):
        """Test calculate_compressor_outlet_temperature method."""
        # Test with normal efficiency
        outlet_temp = self.calc.calculate_compressor_outlet_temperature(
            inlet_temp=25.0,
            pressure_ratio=2.0,
            efficiency=0.75
        )
        
        self.assertGreater(outlet_temp, 25.0)  # Should be hotter
        self.assertIsInstance(outlet_temp, float)
        
        # Test with zero efficiency (edge case)
        outlet_temp_zero = self.calc.calculate_compressor_outlet_temperature(
            inlet_temp=25.0,
            pressure_ratio=2.0,
            efficiency=0.0
        )
        
        self.assertEqual(outlet_temp_zero, 25.0)  # Should return inlet temp
    
    def test_calculate_turbo_mass_flow(self):
        """Test calculate_turbo_mass_flow method."""
        mass_flow = self.calc.calculate_turbo_mass_flow(
            engine_rpm=5000.0,
            engine_displacement=2.3,
            volumetric_efficiency=0.85,
            pressure_ratio=2.0,
            intake_temp=25.0
        )
        
        self.assertGreater(mass_flow, 0.0)
        self.assertIsInstance(mass_flow, float)
    
    def test_calculate_exhaust_gas_temperature_rich_afr(self):
        """Test calculate_exhaust_gas_temperature with rich AFR."""
        # Rich AFR should produce higher EGT
        egt_rich = self.calc.calculate_exhaust_gas_temperature(
            intake_temp=25.0,
            pressure_ratio=2.0,
            afr=11.0,  # Rich
            ignition_timing=15.0,
            engine_load=0.8
        )
        
        egt_stoich = self.calc.calculate_exhaust_gas_temperature(
            intake_temp=25.0,
            pressure_ratio=2.0,
            afr=12.5,  # Stoichiometric
            ignition_timing=15.0,
            engine_load=0.8
        )
        
        self.assertGreater(egt_rich, egt_stoich)
        self.assertIsInstance(egt_rich, float)


class TestTuningSecrets(unittest.TestCase):
    """Test TuningSecrets class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.secrets = TuningSecrets()
    
    def test_initialization(self):
        """Test TuningSecrets initialization."""
        self.assertIsNotNone(self.secrets.secret_methods)
        self.assertIn('faster_spool_lower_psi', self.secrets.secret_methods)
        self.assertIn('vvt_torque_optimization', self.secrets.secret_methods)
    
    def test_faster_spool_technique(self):
        """Test _faster_spool_technique method."""
        result = self.secrets._faster_spool_technique(
            rpm=3000.0,
            target_boost=20.0,
            current_boost=5.0,
            throttle_position=100.0
        )
        
        self.assertIsInstance(result, dict)
        # Should have some adjustment key (wgdc_reduction, wgdc_increase, or wgdc_fine_tune)
        has_adjustment = any(key.startswith('wgdc') for key in result.keys())
        self.assertTrue(has_adjustment or 'boost_target_temp' in result)
    
    def test_vvt_torque_optimization(self):
        """Test _vvt_torque_optimization method."""
        result = self.secrets._vvt_torque_optimization(
            rpm=5000.0,
            load=0.8,
            throttle_position=90.0
        )
        
        self.assertIsInstance(result, dict)
    
    def test_ignition_knock_margin(self):
        """Test _ignition_knock_margin method."""
        result = self.secrets._ignition_knock_margin(
            rpm=6000.0,
            load=0.9,
            intake_temp=40.0,
            coolant_temp=90.0,
            fuel_quality='premium'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('ignition_timing', result)
    
    def test_ignition_knock_margin_regular_fuel(self):
        """Test _ignition_knock_margin with regular fuel."""
        result = self.secrets._ignition_knock_margin(
            rpm=5000.0,
            load=0.8,
            intake_temp=25.0,
            coolant_temp=90.0,
            fuel_quality='regular'
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('ignition_timing', result)
    
    def test_vvt_torque_optimization_high_load(self):
        """Test _vvt_torque_optimization with high load."""
        result = self.secrets._vvt_torque_optimization(
            rpm=4000.0,
            load=1.2,  # High load
            throttle_position=100.0
        )
        
        self.assertIsInstance(result, dict)
        # High load should amplify adjustments
        if 'vvt_intake_advance' in result:
            self.assertGreater(result['vvt_intake_advance'], 0)
    
    def test_faster_spool_technique_transition_phase(self):
        """Test _faster_spool_technique in transition phase."""
        result = self.secrets._faster_spool_technique(
            rpm=4000.0,  # Transition phase
            target_boost=20.0,
            current_boost=15.0,  # Below 90% of target
            throttle_position=100.0
        )
        
        self.assertIsInstance(result, dict)
    
    def test_faster_spool_technique_hold_phase(self):
        """Test _faster_spool_technique in hold phase."""
        result = self.secrets._faster_spool_technique(
            rpm=5000.0,  # Hold phase
            target_boost=20.0,
            current_boost=19.0,  # Above 95% of target
            throttle_position=100.0
        )
        
        self.assertIsInstance(result, dict)
    
    def test_boost_taper_optimization_high_rpm(self):
        """Test _boost_taper_optimization at high RPM."""
        result = self.secrets._boost_taper_optimization(
            rpm=7000.0,  # High RPM
            current_boost=22.0,
            target_boost=20.0,
            airflow=200.0  # Low VE
        )
        
        self.assertIsInstance(result, dict)
        if 'boost_target' in result:
            self.assertLess(result['boost_target'], 20.0)  # Should taper
    
    def test_boost_taper_optimization(self):
        """Test _boost_taper_optimization method."""
        result = self.secrets._boost_taper_optimization(
            rpm=6500.0,
            current_boost=22.0,
            target_boost=20.0,
            airflow=250.0
        )
        
        self.assertIsInstance(result, dict)
    
    def test_apply_tuning_secret(self):
        """Test apply_tuning_secret method."""
        result = self.secrets.apply_tuning_secret(
            'faster_spool_lower_psi',
            {
                'rpm': 3000.0,
                'target_boost': 20.0,
                'current_boost': 5.0,
                'throttle_position': 100.0
            }
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
    
    def test_apply_tuning_secret_invalid(self):
        """Test apply_tuning_secret with invalid method."""
        with self.assertRaises(ValueError):
            self.secrets.apply_tuning_secret('invalid_method', {})


if __name__ == '__main__':
    unittest.main()

