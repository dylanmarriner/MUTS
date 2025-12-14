"""Tests for core app_state module."""
import unittest
from unittest.mock import Mock, patch
import time

from core.app_state import (
    AppStateManager, SystemState, PerformanceMode, 
    ECUData, TuningParameters, SystemStatus, get_app_state
)


class TestSystemState(unittest.TestCase):
    """Test SystemState enum."""
    
    def test_system_state_values(self):
        """Test SystemState enum values."""
        self.assertEqual(SystemState.INITIALIZING.value, "initializing")
        self.assertEqual(SystemState.READY.value, "ready")
        self.assertEqual(SystemState.CONNECTING.value, "connecting")
        self.assertEqual(SystemState.TUNING.value, "tuning")
        self.assertEqual(SystemState.DIAGNOSTIC.value, "diagnostic")
        self.assertEqual(SystemState.ERROR.value, "error")
        self.assertEqual(SystemState.SHUTDOWN.value, "shutdown")


class TestPerformanceMode(unittest.TestCase):
    """Test PerformanceMode enum."""
    
    def test_performance_mode_values(self):
        """Test PerformanceMode enum values."""
        self.assertEqual(PerformanceMode.STOCK.value, "stock")
        self.assertEqual(PerformanceMode.STREET.value, "street")
        self.assertEqual(PerformanceMode.TRACK.value, "track")
        self.assertEqual(PerformanceMode.DRAG.value, "drag")
        self.assertEqual(PerformanceMode.ECO.value, "eco")
        self.assertEqual(PerformanceMode.SAFE.value, "safe")


class TestECUData(unittest.TestCase):
    """Test ECUData dataclass."""
    
    def test_ecu_data_defaults(self):
        """Test ECUData default values."""
        data = ECUData()
        self.assertEqual(data.engine_rpm, 0.0)
        self.assertEqual(data.boost_psi, 0.0)
        self.assertEqual(data.manifold_pressure, 101.3)
        self.assertEqual(data.ignition_timing, 0.0)
        self.assertEqual(data.afr, 14.7)
        self.assertEqual(data.coolant_temp, 90.0)
        self.assertIsNotNone(data.timestamp)


class TestTuningParameters(unittest.TestCase):
    """Test TuningParameters dataclass."""
    
    def test_tuning_parameters_defaults(self):
        """Test TuningParameters default values."""
        params = TuningParameters()
        self.assertEqual(params.boost_target, 15.0)
        self.assertEqual(params.timing_base, 10.0)
        self.assertEqual(params.performance_mode, PerformanceMode.STOCK)


class TestSystemStatus(unittest.TestCase):
    """Test SystemStatus dataclass."""
    
    def test_system_status_defaults(self):
        """Test SystemStatus default values."""
        status = SystemStatus()
        self.assertFalse(status.can_connected)
        self.assertFalse(status.ecu_connected)
        self.assertFalse(status.security_unlocked)
        self.assertFalse(status.tuning_active)
        self.assertTrue(status.data_logging)
        self.assertFalse(status.safety_override)
        self.assertEqual(status.error_count, 0)
        self.assertIsNone(status.last_error)


class TestAppStateManager(unittest.TestCase):
    """Test AppStateManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app_state = AppStateManager()
    
    def test_initialization(self):
        """Test AppStateManager initialization."""
        self.assertIsNotNone(self.app_state._lock)
        self.assertEqual(self.app_state.get_state(), SystemState.READY)
        self.assertIsNotNone(self.app_state._ecu_data)
        self.assertIsNotNone(self.app_state._tuning_params)
        self.assertIsNotNone(self.app_state._system_status)
    
    def test_set_state(self):
        """Test set_state method."""
        self.app_state.set_state(SystemState.CONNECTING)
        self.assertEqual(self.app_state.get_state(), SystemState.CONNECTING)
        
        self.app_state.set_state(SystemState.TUNING)
        self.assertEqual(self.app_state.get_state(), SystemState.TUNING)
    
    def test_get_state(self):
        """Test get_state method."""
        state = self.app_state.get_state()
        self.assertIsInstance(state, SystemState)
    
    def test_update_ecu_data(self):
        """Test update_ecu_data method."""
        self.app_state.update_ecu_data(
            engine_rpm=3000.0,
            boost_psi=15.5,
            throttle_position=50.0
        )
        
        ecu_data = self.app_state.get_ecu_data()
        self.assertEqual(ecu_data.engine_rpm, 3000.0)
        self.assertEqual(ecu_data.boost_psi, 15.5)
        self.assertEqual(ecu_data.throttle_position, 50.0)
        self.assertIsNotNone(ecu_data.timestamp)
    
    def test_get_ecu_data(self):
        """Test get_ecu_data method."""
        ecu_data = self.app_state.get_ecu_data()
        self.assertIsInstance(ecu_data, ECUData)
    
    def test_update_tuning_parameters(self):
        """Test update_tuning_parameters method."""
        self.app_state.update_tuning_parameters(
            boost_target=20.0,
            timing_base=15.0,
            afr_target=12.0
        )
        
        params = self.app_state.get_tuning_parameters()
        self.assertEqual(params.boost_target, 20.0)
        self.assertEqual(params.timing_base, 15.0)
        self.assertEqual(params.afr_target, 12.0)
    
    def test_get_tuning_parameters(self):
        """Test get_tuning_parameters method."""
        params = self.app_state.get_tuning_parameters()
        self.assertIsInstance(params, TuningParameters)
    
    def test_update_system_status(self):
        """Test update_system_status method."""
        self.app_state.update_system_status(
            can_connected=True,
            ecu_connected=True,
            error_count=5
        )
        
        status = self.app_state.get_system_status()
        self.assertTrue(status.can_connected)
        self.assertTrue(status.ecu_connected)
        self.assertEqual(status.error_count, 5)
    
    def test_get_system_status(self):
        """Test get_system_status method."""
        status = self.app_state.get_system_status()
        self.assertIsInstance(status, SystemStatus)
    
    def test_set_performance_mode_stock(self):
        """Test set_performance_mode with STOCK mode."""
        self.app_state.set_performance_mode(PerformanceMode.STOCK)
        params = self.app_state.get_tuning_parameters()
        self.assertEqual(params.performance_mode, PerformanceMode.STOCK)
        self.assertEqual(params.boost_target, 15.0)
        self.assertEqual(params.timing_base, 10.0)
    
    def test_set_performance_mode_street(self):
        """Test set_performance_mode with STREET mode."""
        self.app_state.set_performance_mode(PerformanceMode.STREET)
        params = self.app_state.get_tuning_parameters()
        self.assertEqual(params.performance_mode, PerformanceMode.STREET)
        self.assertEqual(params.boost_target, 18.0)
        self.assertEqual(params.timing_base, 15.0)
    
    def test_set_performance_mode_track(self):
        """Test set_performance_mode with TRACK mode."""
        self.app_state.set_performance_mode(PerformanceMode.TRACK)
        params = self.app_state.get_tuning_parameters()
        self.assertEqual(params.performance_mode, PerformanceMode.TRACK)
        self.assertEqual(params.boost_target, 22.0)
        self.assertEqual(params.timing_base, 20.0)
    
    def test_set_performance_mode_drag(self):
        """Test set_performance_mode with DRAG mode."""
        self.app_state.set_performance_mode(PerformanceMode.DRAG)
        params = self.app_state.get_tuning_parameters()
        self.assertEqual(params.performance_mode, PerformanceMode.DRAG)
        self.assertEqual(params.boost_target, 24.0)
        self.assertEqual(params.timing_base, 25.0)
    
    def test_set_performance_mode_eco(self):
        """Test set_performance_mode with ECO mode."""
        self.app_state.set_performance_mode(PerformanceMode.ECO)
        params = self.app_state.get_tuning_parameters()
        self.assertEqual(params.performance_mode, PerformanceMode.ECO)
        self.assertEqual(params.boost_target, 14.0)
        self.assertEqual(params.timing_base, 8.0)
    
    def test_set_performance_mode_safe(self):
        """Test set_performance_mode with SAFE mode."""
        self.app_state.set_performance_mode(PerformanceMode.SAFE)
        params = self.app_state.get_tuning_parameters()
        self.assertEqual(params.performance_mode, PerformanceMode.SAFE)
        self.assertEqual(params.boost_target, 16.0)
        self.assertEqual(params.timing_base, 12.0)
    
    def test_set_error(self):
        """Test set_error method."""
        error_msg = "Test error message"
        self.app_state.set_error(error_msg)
        
        status = self.app_state.get_system_status()
        self.assertEqual(status.last_error, error_msg)
        self.assertEqual(status.error_count, 1)
    
    def test_clear_error(self):
        """Test clear_error method."""
        self.app_state.set_error("Test error")
        self.app_state.clear_error()
        
        status = self.app_state.get_system_status()
        self.assertIsNone(status.last_error)
    
    def test_register_callback(self):
        """Test register_callback method."""
        callback = Mock()
        self.app_state.register_callback('test_event', callback)
        
        # Trigger the callback
        self.app_state._notify_callbacks('test_event', 'test_data')
        callback.assert_called_once_with('test_data')
    
    def test_unregister_callback(self):
        """Test unregister_callback method."""
        callback = Mock()
        self.app_state.register_callback('test_event', callback)
        self.app_state.unregister_callback('test_event', callback)
        
        # Trigger the callback - should not be called
        self.app_state._notify_callbacks('test_event', 'test_data')
        callback.assert_not_called()
    
    def test_get_history(self):
        """Test get_history method."""
        # Update some data to create history
        self.app_state.update_ecu_data(engine_rpm=3000.0)
        self.app_state.update_ecu_data(engine_rpm=3500.0)
        
        history = self.app_state.get_history()
        self.assertGreater(len(history), 0)
        
        # Get specific type history
        ecu_history = self.app_state.get_history('ecu_data')
        self.assertGreater(len(ecu_history), 0)
        
        # Get limited history
        limited = self.app_state.get_history(limit=1)
        self.assertLessEqual(len(limited), 1)
    
    def test_get_config(self):
        """Test get_config method."""
        config = self.app_state.get_config()
        self.assertIsInstance(config, dict)
        self.assertIn('can_interface', config)
        self.assertIn('performance_modes', config)
        
        # Get specific config key
        interface = self.app_state.get_config('can_interface')
        self.assertEqual(interface, 'can0')
    
    def test_set_config(self):
        """Test set_config method."""
        self.app_state.set_config('test_key', 'test_value')
        value = self.app_state.get_config('test_key')
        self.assertEqual(value, 'test_value')
    
    def test_export_state(self):
        """Test export_state method."""
        state_dict = self.app_state.export_state()
        
        self.assertIn('state', state_dict)
        self.assertIn('ecu_data', state_dict)
        self.assertIn('tuning_params', state_dict)
        self.assertIn('system_status', state_dict)
        self.assertIn('config', state_dict)
        self.assertIn('timestamp', state_dict)
    
    def test_import_state(self):
        """Test import_state method."""
        # Export current state
        exported = self.app_state.export_state()
        
        # Modify state
        self.app_state.set_state(SystemState.TUNING)
        self.app_state.update_ecu_data(engine_rpm=5000.0)
        
        # Import back
        self.app_state.import_state(exported)
        
        # Verify state was restored
        self.assertEqual(self.app_state.get_state().value, exported['state'])


class TestGetAppState(unittest.TestCase):
    """Test get_app_state function."""
    
    def test_get_app_state(self):
        """Test get_app_state returns AppStateManager instance."""
        app_state = get_app_state()
        self.assertIsInstance(app_state, AppStateManager)


if __name__ == '__main__':
    unittest.main()

