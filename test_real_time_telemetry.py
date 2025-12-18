import pytest
import time
import can
from unittest.mock import MagicMock, patch
from RealTimeTelemetry import RealTimeTelemetry, CANMessageDecoder, TelemetryMetric, CAN_ID
import numpy as np

@pytest.fixture
def mock_can_bus():
    """Create a mock CAN bus interface."""
    bus = MagicMock()
    bus.recv.side_effect = []
    return bus

@pytest.fixture
def telemetry(mock_can_bus):
    """Create a telemetry instance with a mock CAN bus."""
    return RealTimeTelemetry(mock_can_bus, sample_rate_hz=100)

def test_telemetry_initialization(telemetry, mock_can_bus):
    """Test that telemetry initializes correctly."""
    assert telemetry.sample_rate_hz == 100
    assert telemetry.sample_interval == 0.01
    assert not telemetry._running
    assert telemetry._thread is None

def test_start_stop_telemetry(telemetry, mock_can_bus):
    """Test starting and stopping the telemetry system."""
    telemetry.start()
    assert telemetry._running
    assert telemetry._thread is not None
    assert telemetry._thread.is_alive()
    
    telemetry.stop()
    assert not telemetry._running
    # Thread should be stopped or about to stop
    telemetry._thread.join(timeout=1.0)
    assert not telemetry._thread.is_alive()

def test_can_message_processing(telemetry, mock_can_bus):
    """Test processing of CAN messages."""
    # Create test CAN messages
    rpm_msg = can.Message(
        arbitration_id=CAN_ID.ENGINE_RPM.value,
        data=int(3000 / 0.25).to_bytes(2, 'little')
    )
    
    boost_msg = can.Message(
        arbitration_id=CAN_ID.BOOST_PRESSURE.value,
        data=int((10 + 14.7) / 0.1).to_bytes(2, 'little')
    )
    
    # Set up mock to return these messages
    mock_can_bus.recv.side_effect = [rpm_msg, boost_msg, None]
    
    # Process messages
    telemetry._process_can_message(rpm_msg)
    telemetry._process_can_message(boost_msg)
    
    # Check that metrics were updated
    assert abs(telemetry.get_metric_value('rpm') - 3000) < 0.1
    assert abs(telemetry.get_metric_value('boost') - 10.0) < 0.1

def test_performance_metrics(telemetry):
    """Test performance metrics collection."""
    # Simulate some processing
    telemetry._sample_count = 100
    telemetry._total_loop_time = 1.0  # 1 second total for 100 samples
    telemetry._min_loop_time = 0.008
    telemetry._max_loop_time = 0.012
    telemetry._missed_deadlines = 2
    
    metrics = telemetry.get_performance_metrics()
    
    assert metrics['sample_rate_hz'] == 100
    assert metrics['samples_collected'] == 100
    assert metrics['missed_deadlines'] == 2
    assert abs(metrics['avg_loop_time_ms'] - 10.0) < 0.1  # 10ms average
    assert abs(metrics['min_loop_time_ms'] - 8.0) < 0.1
    assert abs(metrics['max_loop_time_ms'] - 12.0) < 0.1
    assert abs(metrics['cpu_usage_percent'] - 100.0) < 1.0  # ~100% CPU usage

def test_telemetry_metric_updates():
    """Test the TelemetryMetric class functionality."""
    metric = TelemetryMetric('test', 'units', max_history=5)
    
    # Initial state
    assert metric.value is None
    assert metric.stats['min'] is None
    assert metric.stats['max'] is None
    
    # Update with values
    timestamps = [time.time() + i for i in range(5)]
    for i, ts in enumerate(timestamps, 1):
        metric.update(float(i), timestamp=ts)
    
    # Check current value and stats
    assert metric.value == 5.0
    assert metric.stats['min'] == 1.0
    assert metric.stats['max'] == 5.0
    assert abs(metric.stats['avg'] - 3.0) < 0.001
    
    # Check history
    history = metric.get_history()
    assert len(history) == 5
    assert [h['value'] for h in history] == [1.0, 2.0, 3.0, 4.0, 5.0]
    
    # Test history limiting
    metric.update(6.0)
    history = metric.get_history(3)
    assert len(history) == 3
    assert [h['value'] for h in history] == [4.0, 5.0, 6.0]

def test_can_decoder():
    """Test CAN message decoding functions."""
    decoder = CANMessageDecoder()
    
    # Test RPM decoding
    rpm_data = int(3000 / 0.25).to_bytes(2, 'little')
    assert abs(decoder.decode_rpm(rpm_data) - 3000) < 0.1
    
    # Test boost decoding
    boost_data = int((15.0 + 14.7) / 0.1).to_bytes(2, 'little')
    assert abs(decoder.decode_boost(boost_data) - 15.0) < 0.1
    
    # Test AFR decoding
    afr_data = int(14.7 / 0.01).to_bytes(2, 'little')
    assert abs(decoder.decode_afr(afr_data) - 14.7) < 0.01
    
    # Test ignition timing decoding
    timing_data = int((10.0 + 64) / 0.5).to_bytes(1, 'little')
    assert abs(decoder.decode_ignition(timing_data) - 10.0) < 0.1
    
    # Test coolant temp decoding
    temp_data = int(90 + 40).to_bytes(1, 'little')
    assert abs(decoder.decode_coolant_temp(temp_data) - 90.0) < 0.1

@pytest.mark.asyncio
async def test_real_time_telemetry_integration():
    """Integration test with a simulated CAN bus."""
    from unittest.mock import MagicMock
    
    # Create a mock CAN bus that generates test messages
    class MockCANBus:
        def __init__(self):
            self.count = 0
            
        def recv(self, timeout=None):
            import random
            import can
            
            self.count += 1
            if self.count > 100:  # Limit number of test messages
                return None
                
            # Alternate between different message types
            msg_type = self.count % 5
            
            if msg_type == 0:  # RPM
                rpm = 1000 + (random.random() * 6000)
                data = int(rpm / 0.25).to_bytes(2, 'little')
                return can.Message(arbitration_id=CAN_ID.ENGINE_RPM.value, data=data)
                
            elif msg_type == 1:  # Boost
                boost = (random.random() * 30) - 10
                data = int((boost + 14.7) / 0.1).to_bytes(2, 'little')
                return can.Message(arbitration_id=CAN_ID.BOOST_PRESSURE.value, data=data)
                
            # Add other message types...
    
    # Create and start telemetry
    can_bus = MockCANBus()
    telemetry = RealTimeTelemetry(can_bus, sample_rate_hz=100)
    
    try:
        telemetry.start()
        
        # Let it run for a short time
        import asyncio
        await asyncio.sleep(0.1)
        
        # Check that we got some data
        status = telemetry.get_status()
        assert status['running'] is True
        assert status['thread_alive'] is True
        
        # Should have received some messages
        assert telemetry._sample_count > 0
        
        # Check that metrics were updated
        rpm = telemetry.get_metric_value('rpm')
        assert rpm is not None and rpm > 0
        
    finally:
        telemetry.stop()
