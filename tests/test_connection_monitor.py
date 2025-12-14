"""Tests for core connection_monitor module."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from core.connection_monitor import (
    ConnectionHealthMonitor, ConnectionHealth, ConnectionMetrics
)
from core.ecu_communication import ECUCommunicator, ECUResponse


class TestConnectionHealth(unittest.TestCase):
    """Test ConnectionHealth enum."""
    
    def test_connection_health_values(self):
        """Test ConnectionHealth enum values."""
        self.assertEqual(ConnectionHealth.EXCELLENT.value, "excellent")
        self.assertEqual(ConnectionHealth.GOOD.value, "good")
        self.assertEqual(ConnectionHealth.POOR.value, "poor")
        self.assertEqual(ConnectionHealth.DISCONNECTED.value, "disconnected")
        self.assertEqual(ConnectionHealth.ERROR.value, "error")


class TestConnectionMetrics(unittest.TestCase):
    """Test ConnectionMetrics dataclass."""
    
    def test_connection_metrics_defaults(self):
        """Test ConnectionMetrics default values."""
        metrics = ConnectionMetrics()
        
        self.assertEqual(metrics.total_messages, 0)
        self.assertEqual(metrics.failed_messages, 0)
        self.assertEqual(metrics.consecutive_failures, 0)
        self.assertEqual(metrics.response_time_ms, 0.0)
        self.assertEqual(metrics.messages_per_second, 0.0)
        self.assertEqual(metrics.error_rate, 0.0)


class TestConnectionHealthMonitor(unittest.TestCase):
    """Test ConnectionHealthMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_ecu = Mock(spec=ECUCommunicator)
        self.monitor = ConnectionHealthMonitor(self.mock_ecu)
    
    def test_initialization(self):
        """Test ConnectionHealthMonitor initialization."""
        self.assertIsNotNone(self.monitor.ecu_comm)
        self.assertIsNotNone(self.monitor.metrics)
        self.assertEqual(self.monitor.health_status, ConnectionHealth.DISCONNECTED)
        self.assertIsNotNone(self.monitor._lock)
    
    def test_get_health_status(self):
        """Test get_health_status method."""
        status = self.monitor.get_health_status()
        
        self.assertIsInstance(status, ConnectionHealth)
    
    def test_get_connection_metrics(self):
        """Test get_connection_metrics method."""
        metrics = self.monitor.get_connection_metrics()
        
        self.assertIsInstance(metrics, ConnectionMetrics)
        self.assertEqual(metrics.total_messages, 0)
        self.assertEqual(metrics.failed_messages, 0)
    
    def test_start_monitoring(self):
        """Test start_monitoring method."""
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.monitoring)
    
    def test_stop_monitoring(self):
        """Test stop_monitoring method."""
        self.monitor.monitoring = True
        self.monitor._shutdown_flag = Mock()
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.monitoring)
    
    def test_check_connection_health_success(self):
        """Test _check_connection_health with successful response."""
        mock_response = ECUResponse(True, b'\x50\x01', time.time())
        self.mock_ecu.send_request.return_value = mock_response
        
        self.monitor._check_connection_health()
        
        self.assertGreater(self.monitor.metrics.total_messages, 0)
        self.assertEqual(self.monitor.metrics.consecutive_failures, 0)
    
    def test_check_connection_health_failure(self):
        """Test _check_connection_health with failed response."""
        mock_response = ECUResponse(False, b'', time.time())
        self.mock_ecu.send_request.return_value = mock_response
        
        initial_failed = self.monitor.metrics.failed_messages
        
        self.monitor._check_connection_health()
        
        self.assertGreater(self.monitor.metrics.failed_messages, initial_failed)
        self.assertGreater(self.monitor.metrics.consecutive_failures, 0)
    
    def test_check_connection_health_exception(self):
        """Test _check_connection_health with exception."""
        self.mock_ecu.send_request.side_effect = Exception("Connection error")
        
        initial_failed = self.monitor.metrics.failed_messages
        
        self.monitor._check_connection_health()
        
        self.assertGreater(self.monitor.metrics.failed_messages, initial_failed)
        self.assertGreater(self.monitor.metrics.consecutive_failures, 0)
    
    def test_update_health_status_excellent(self):
        """Test _update_health_status sets EXCELLENT."""
        self.monitor.metrics.consecutive_failures = 0
        self.monitor.metrics.error_rate = 0.005  # Less than 0.01
        self.monitor.metrics.response_time_ms = 50.0  # Less than 100
        
        self.monitor._update_health_status()
        
        self.assertEqual(self.monitor.health_status, ConnectionHealth.EXCELLENT)
    
    def test_update_health_status_good(self):
        """Test _update_health_status sets GOOD."""
        self.monitor.metrics.consecutive_failures = 0
        self.monitor.metrics.error_rate = 0.02  # Less than 0.05
        self.monitor.metrics.response_time_ms = 200.0  # Less than 500
        
        self.monitor._update_health_status()
        
        self.assertEqual(self.monitor.health_status, ConnectionHealth.GOOD)
    
    def test_update_health_status_poor(self):
        """Test _update_health_status sets POOR."""
        self.monitor.metrics.consecutive_failures = 0
        self.monitor.metrics.error_rate = 0.06  # Greater than 0.05
        self.monitor.metrics.response_time_ms = 600.0  # Greater than 500
        
        self.monitor._update_health_status()
        
        self.assertEqual(self.monitor.health_status, ConnectionHealth.POOR)
    
    def test_update_health_status_disconnected(self):
        """Test _update_health_status sets DISCONNECTED."""
        self.monitor.metrics.consecutive_failures = 10
        self.monitor.metrics.error_rate = 1.0
        
        self.monitor._update_health_status()
        
        self.assertEqual(self.monitor.health_status, ConnectionHealth.DISCONNECTED)


if __name__ == '__main__':
    unittest.main()

