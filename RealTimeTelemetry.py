"""
RealTimeTelemetry - High-performance telemetry collection and processing module.
Handles 100Hz sampling, CAN message decoding, and thread-safe data access.
"""
import asyncio
import time
import threading
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Deque, Tuple, Any
import numpy as np
from threading import Lock
from datetime import datetime
import statistics

# CAN Message IDs (example values - adjust based on your vehicle's CAN bus)
class CAN_ID(Enum):
    ENGINE_RPM = 0x201
    BOOST_PRESSURE = 0x202
    AIR_FUEL_RATIO = 0x203
    IGNITION_TIMING = 0x204
    COOLANT_TEMP = 0x205
    THROTTLE_POSITION = 0x206
    VEHICLE_SPEED = 0x207

@dataclass
class TelemetryDataPoint:
    """Single timestamped telemetry data point."""
    timestamp: float
    value: float
    unit: str
    raw_data: bytes = field(default_factory=bytes)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'value': self.value,
            'unit': self.unit,
            'raw_data': self.raw_data.hex() if self.raw_data else None
        }

class TelemetryMetric:
    """Thread-safe telemetry metric with history and statistics."""
    def __init__(self, name: str, unit: str, max_history: int = 1000):
        self.name = name
        self.unit = unit
        self._lock = Lock()
        self._current_value: Optional[float] = None
        self._history: Deque[TelemetryDataPoint] = deque(maxlen=max_history)
        self._stats = {
            'min': None,
            'max': None,
            'avg': None,
            'last_updated': None
        }
    
    def update(self, value: float, timestamp: Optional[float] = None, raw_data: bytes = None):
        """Update the metric with a new value."""
        if timestamp is None:
            timestamp = time.time()
            
        point = TelemetryDataPoint(
            timestamp=timestamp,
            value=value,
            unit=self.unit,
            raw_data=raw_data if raw_data else bytes()
        )
        
        with self._lock:
            self._current_value = value
            self._history.append(point)
            
            # Update statistics
            values = [p.value for p in self._history]
            self._stats = {
                'min': min(values) if values else None,
                'max': max(values) if values else None,
                'avg': statistics.mean(values) if values else None,
                'last_updated': timestamp
            }
    
    @property
    def value(self) -> Optional[float]:
        """Get the current value."""
        with self._lock:
            return self._current_value
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get statistics about this metric."""
        with self._lock:
            return self._stats.copy()
    
    def get_history(self, max_points: int = 100) -> List[Dict[str, Any]]:
        """Get historical data points."""
        with self._lock:
            # Return most recent points
            points = list(self._history)[-max_points:]
            return [p.to_dict() for p in points]

class CANMessageDecoder:
    """Decodes raw CAN messages into telemetry data."""
    
    @staticmethod
    def decode_rpm(data: bytes) -> float:
        """Decode RPM from CAN data (example implementation)."""
        # Example: RPM is stored in bytes 0-1, little-endian, 0.25 RPM/bit
        if len(data) >= 2:
            return int.from_bytes(data[0:2], 'little') * 0.25
        return 0.0
    
    @staticmethod
    def decode_boost(data: bytes) -> float:
        """Decode boost pressure in PSI (example implementation)."""
        # Example: Boost is in bytes 0-1, little-endian, 0.1 PSI/bit, offset -14.7
        if len(data) >= 2:
            return (int.from_bytes(data[0:2], 'little') * 0.1) - 14.7
        return 0.0
    
    @staticmethod
    def decode_afr(data: bytes) -> float:
        """Decode air/fuel ratio (example implementation)."""
        # Example: AFR is in bytes 0-1, little-endian, 0.01 AFR/bit
        if len(data) >= 2:
            return int.from_bytes(data[0:2], 'little') * 0.01
        return 14.7  # Stoichiometric AFR for gasoline
    
    @staticmethod
    def decode_ignition(data: bytes) -> float:
        """Decode ignition timing in degrees (example implementation)."""
        # Example: Timing is in byte 0, 0.5 deg/bit, offset -64
        if data:
            return (data[0] * 0.5) - 64.0
        return 0.0
    
    @staticmethod
    def decode_coolant_temp(data: bytes) -> float:
        """Decode coolant temperature in °C (example implementation)."""
        # Example: Temp is in byte 0, 1.0 °C/bit, offset -40
        if data:
            return float(data[0]) - 40.0
        return 0.0

class RealTimeTelemetry:
    """High-performance telemetry collection and processing system."""
    
    def __init__(self, can_bus, sample_rate_hz: int = 100):
        """
        Initialize the telemetry system.
        
        Args:
            can_bus: CAN bus interface (must implement recv() method)
            sample_rate_hz: Desired sampling rate in Hz (default: 100Hz)
        """
        self.can_bus = can_bus
        self.sample_rate_hz = sample_rate_hz
        self.sample_interval = 1.0 / sample_rate_hz
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self._decoder = CANMessageDecoder()
        
        # Initialize metrics
        self.metrics = {
            'rpm': TelemetryMetric('rpm', 'RPM'),
            'boost': TelemetryMetric('boost', 'PSI'),
            'afr': TelemetryMetric('afr', 'AFR'),
            'ignition': TelemetryMetric('ignition', 'deg'),
            'coolant_temp': TelemetryMetric('coolant_temp', '°C'),
            'throttle': TelemetryMetric('throttle', '%'),
            'speed': TelemetryMetric('speed', 'km/h')
        }
        
        # Performance metrics
        self._sample_count = 0
        self._missed_deadlines = 0
        self._last_sample_time = 0
        self._min_loop_time = float('inf')
        self._max_loop_time = 0
        self._total_loop_time = 0
    
    def start(self) -> None:
        """Start the telemetry collection thread."""
        if self._running:
            return
            
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_telemetry_loop,
            name="TelemetryThread",
            daemon=True
        )
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the telemetry collection thread."""
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
    
    def _run_telemetry_loop(self) -> None:
        """Main telemetry collection loop running in a separate thread."""
        next_sample_time = time.perf_counter()
        
        while self._running and not self._stop_event.is_set():
            loop_start = time.perf_counter()
            
            try:
                # Process all available CAN messages
                while True:
                    # Non-blocking receive
                    msg = self.can_bus.recv(timeout=0)
                    if msg is None:
                        break
                    self._process_can_message(msg)
                
                # Update performance metrics
                self._sample_count += 1
                now = time.perf_counter()
                loop_time = now - loop_start
                self._total_loop_time += loop_time
                self._min_loop_time = min(self._min_loop_time, loop_time)
                self._max_loop_time = max(self._max_loop_time, loop_time)
                
                # Calculate sleep time to maintain desired sample rate
                next_sample_time += self.sample_interval
                sleep_time = next_sample_time - time.perf_counter()
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self._missed_deadlines += 1
                    # If we're falling behind, skip the next deadline
                    next_sample_time = time.perf_counter() + self.sample_interval
                
            except Exception as e:
                print(f"Error in telemetry loop: {e}")
                # Prevent tight error loop
                time.sleep(0.1)
    
    def _process_can_message(self, msg) -> None:
        """Process a single CAN message and update metrics."""
        try:
            can_id = msg.arbitration_id
            data = msg.data
            
            # Route to appropriate decoder based on CAN ID
            if can_id == CAN_ID.ENGINE_RPM.value:
                rpm = self._decoder.decode_rpm(data)
                self.metrics['rpm'].update(rpm, raw_data=data)
                
            elif can_id == CAN_ID.BOOST_PRESSURE.value:
                boost = self._decoder.decode_boost(data)
                self.metrics['boost'].update(boost, raw_data=data)
                
            elif can_id == CAN_ID.AIR_FUEL_RATIO.value:
                afr = self._decoder.decode_afr(data)
                self.metrics['afr'].update(afr, raw_data=data)
                
            elif can_id == CAN_ID.IGNITION_TIMING.value:
                timing = self._decoder.decode_ignition(data)
                self.metrics['ignition'].update(timing, raw_data=data)
                
            elif can_id == CAN_ID.COOLANT_TEMP.value:
                temp = self._decoder.decode_coolant_temp(data)
                self.metrics['coolant_temp'].update(temp, raw_data=data)
                
            # Add more CAN ID handlers as needed
                
        except Exception as e:
            print(f"Error processing CAN message: {e}")
    
    def get_metric(self, name: str) -> Optional[TelemetryMetric]:
        """Get a telemetry metric by name."""
        return self.metrics.get(name)
    
    def get_metric_value(self, name: str) -> Optional[float]:
        """Get the current value of a telemetry metric."""
        metric = self.metrics.get(name)
        return metric.value if metric else None
    
    def get_metric_history(self, name: str, max_points: int = 100) -> List[Dict[str, Any]]:
        """Get historical data for a metric."""
        metric = self.metrics.get(name)
        return metric.get_history(max_points) if metric else []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance statistics for the telemetry system."""
        avg_loop_time = (self._total_loop_time / self._sample_count) if self._sample_count > 0 else 0
        
        return {
            'sample_rate_hz': self.sample_rate_hz,
            'samples_collected': self._sample_count,
            'missed_deadlines': self._missed_deadlines,
            'min_loop_time_ms': self._min_loop_time * 1000,
            'max_loop_time_ms': self._max_loop_time * 1000,
            'avg_loop_time_ms': avg_loop_time * 1000,
            'cpu_usage_percent': (avg_loop_time / self.sample_interval) * 100 if self.sample_interval > 0 else 0
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the telemetry system."""
        return {
            'running': self._running,
            'thread_alive': self._thread.is_alive() if self._thread else False,
            'metrics': {name: {
                'value': metric.value,
                'unit': metric.unit,
                'stats': metric.stats
            } for name, metric in self.metrics.items()},
            'performance': self.get_performance_metrics()
        }

# Example usage
if __name__ == "__main__":
    # This would be replaced with your actual CAN bus interface
    class MockCANBus:
        def __init__(self):
            self.count = 0
            
        def recv(self, timeout=None):
            import random
            import can
            
            self.count += 1
            if self.count > 1000:  # Simulate some messages
                return None
                
            # Simulate different CAN messages
            msg_type = self.count % 5
            
            if msg_type == 0:  # RPM
                rpm = 800 + (random.random() * 5000)
                data = int(rpm / 0.25).to_bytes(2, 'little')
                return can.Message(arbitration_id=CAN_ID.ENGINE_RPM.value, data=data)
                
            elif msg_type == 1:  # Boost
                boost = (random.random() * 30) - 10  # -10 to +20 PSI
                data = int((boost + 14.7) / 0.1).to_bytes(2, 'little')
                return can.Message(arbitration_id=CAN_ID.BOOST_PRESSURE.value, data=data)
                
            elif msg_type == 2:  # AFR
                afr = 10 + (random.random() * 5)  # 10-15 AFR
                data = int(afr / 0.01).to_bytes(2, 'little')
                return can.Message(arbitration_id=CAN_ID.AIR_FUEL_RATIO.value, data=data)
                
            elif msg_type == 3:  # Ignition timing
                timing = (random.random() * 40) - 20  # -20 to +20 deg
                data = int((timing + 64) / 0.5).to_bytes(1, 'little')
                return can.Message(arbitration_id=CAN_ID.IGNITION_TIMING.value, data=data)
                
            else:  # Coolant temp
                temp = 70 + (random.random() * 50)  # 70-120°C
                data = int(temp + 40).to_bytes(1, 'little')
                return can.Message(arbitration_id=CAN_ID.COOLANT_TEMP.value, data=data)
    
    # Create and start the telemetry system
    can_bus = MockCANBus()
    telemetry = RealTimeTelemetry(can_bus, sample_rate_hz=100)
    
    try:
        print("Starting telemetry system...")
        telemetry.start()
        
        # Run for a while to collect data
        import time
        for i in range(5):
            time.sleep(1)
            status = telemetry.get_status()
            print(f"\n--- Status Update ({i+1}/5) ---")
            print(f"RPM: {status['metrics']['rpm']['value']:.1f} {status['metrics']['rpm']['unit']}")
            print(f"Boost: {status['metrics']['boost']['value']:.1f} {status['metrics']['boost']['unit']}")
            print(f"AFR: {status['metrics']['afr']['value']:.2f} {status['metrics']['afr']['unit']}")
            
        # Get performance metrics
        perf = telemetry.get_performance_metrics()
        print("\n--- Performance Metrics ---")
        for k, v in perf.items():
            if isinstance(v, float):
                print(f"{k}: {v:.2f}")
            else:
                print(f"{k}: {v}")
        
    except KeyboardInterrupt:
        print("\nStopping telemetry system...")
    finally:
        telemetry.stop()
