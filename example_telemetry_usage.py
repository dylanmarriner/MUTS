#!/usr/bin/env python3
"""
Example usage of the RealTimeTelemetry module.

This script demonstrates how to use the RealTimeTelemetry class to collect
and display vehicle telemetry data in real-time.
"""
import time
import can
import signal
import sys
from RealTimeTelemetry import RealTimeTelemetry, CAN_ID

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\nShutting down gracefully...")
    if 'telemetry' in globals():
        telemetry.stop()
    if 'bus' in globals():
        bus.shutdown()
    sys.exit(0)

def setup_can_bus():
    """Set up and return a CAN bus interface."""
    try:
        # Try to use a real CAN interface
        print("Attempting to connect to CAN bus...")
        bus = can.interface.Bus(channel='can0', bustype='socketcan')
        print("Connected to CAN bus")
        return bus
    except Exception as e:
        print(f"Could not connect to CAN bus: {e}")
        print("Using a mock CAN bus for demonstration...")
        
        # Fall back to a mock CAN bus for demonstration
        class MockCANBus:
            def __init__(self):
                self.count = 0
                self.is_running = True
                
            def recv(self, timeout=None):
                import random
                import can
                
                if not self.is_running:
                    return None
                    
                self.count += 1
                if self.count > 10000:  # Safety limit
                    return None
                    
                # Simulate different message types
                msg_type = self.count % 5
                
                if msg_type == 0:  # RPM (1000-7000)
                    rpm = 1000 + (time.time() * 500 % 6000)
                    data = int(rpm / 0.25).to_bytes(2, 'little')
                    return can.Message(arbitration_id=CAN_ID.ENGINE_RPM.value, data=data)
                    
                elif msg_type == 1:  # Boost (-10 to +20 PSI)
                    boost = 5 + 15 * (time.time() % 2)  # Oscillate between -10 and +20
                    data = int((boost + 14.7) / 0.1).to_bytes(2, 'little')
                    return can.Message(arbitration_id=CAN_ID.BOOST_PRESSURE.value, data=data)
                    
                elif msg_type == 2:  # AFR (12-18)
                    afr = 12 + (time.time() % 6)
                    data = int(afr / 0.01).to_bytes(2, 'little')
                    return can.Message(arbitration_id=CAN_ID.AIR_FUEL_RATIO.value, data=data)
                    
                elif msg_type == 3:  # Ignition timing (-20 to +40 deg)
                    timing = 10 + 30 * (time.time() % 2)  # Oscillate between -20 and +40
                    data = int((timing + 64) / 0.5).to_bytes(1, 'little')
                    return can.Message(arbitration_id=CAN_ID.IGNITION_TIMING.value, data=data)
                    
                else:  # Coolant temp (70-110°C)
                    temp = 70 + (time.time() * 10 % 40)
                    data = int(temp + 40).to_bytes(1, 'little')
                    return can.Message(arbitration_id=CAN_ID.COOLANT_TEMP.value, data=data)
            
            def shutdown(self):
                self.is_running = False
        
        return MockCANBus()

def display_metrics(telemetry):
    """Display the current telemetry metrics in a formatted way."""
    status = telemetry.get_status()
    metrics = status['metrics']
    perf = status['performance']
    
    # Clear screen and move cursor to top-left
    print("\033[H\033[J", end="")
    
    # Display header
    print("=== Real-Time Vehicle Telemetry ===")
    print("Press Ctrl+C to exit\n")
    
    # Display engine metrics
    print("=== Engine Metrics ===")
    print(f"RPM:           {metrics['rpm']['value']:7.1f} {metrics['rpm']['unit']}")
    print(f"Boost:         {metrics['boost']['value']:7.1f} {metrics['boost']['unit']}")
    print(f"AFR:           {metrics['afr']['value']:7.2f} {metrics['afr']['unit']}")
    print(f"Ignition:      {metrics['ignition']['value']:7.1f} {metrics['ignition']['unit']}")
    print(f"Coolant Temp:  {metrics['coolant_temp']['value']:7.1f} {metrics['coolant_temp']['unit']}")
    
    # Display performance metrics
    print("\n=== Performance ===")
    print(f"Sample Rate:   {perf['sample_rate_hz']:7.0f} Hz")
    print(f"Samples:       {perf['samples_collected']:7.0f}")
    print(f"Avg Loop Time: {perf['avg_loop_time_ms']:7.2f} ms")
    print(f"CPU Usage:     {perf['cpu_usage_percent']:6.1f}%")
    print(f"Missed:        {perf['missed_deadlines']:7.0f}")
    
    # Display warning if CPU usage is high
    if perf['cpu_usage_percent'] > 80:
        print("\n\033[91mWARNING: High CPU usage! Consider reducing sample rate.\033[0m")


def main():
    """Main function to run the telemetry example."""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Set up CAN bus
    global bus
    bus = setup_can_bus()
    
    try:
        # Create and start telemetry
        global telemetry
        telemetry = RealTimeTelemetry(bus, sample_rate_hz=100)
        
        print("Starting telemetry system...")
        telemetry.start()
        
        # Main loop
        print("Collecting telemetry data...")
        while True:
            display_metrics(telemetry)
            time.sleep(0.1)  # Update display at 10Hz
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        if 'telemetry' in globals():
            telemetry.stop()
        if 'bus' in globals() and hasattr(bus, 'shutdown'):
            bus.shutdown()

if __name__ == "__main__":
    main()
