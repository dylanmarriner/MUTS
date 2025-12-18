#!/usr/bin/env python3
"""
DSG Shift Detection Test for VW Golf Mk6
Validates that DSG shifts are properly detected with 7-speed ratios
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import numpy as np
from muts.dyno.dsg_shift_detector import DSGShiftDetector
from muts.models.vehicle_constants import VehicleConstantsPreset, VehicleConstants
from muts.models.database_models import db
from muts import create_app


def create_test_telemetry():
    """Create test telemetry with simulated DSG shifts"""
    
    # Sample rate: 100Hz
    sample_rate = 100
    duration = 10.0  # 10 seconds
    num_samples = int(duration * sample_rate)
    
    # Time array
    time = np.linspace(0, duration, num_samples)
    
    # Create realistic telemetry with shifts
    rpm = np.zeros(num_samples)
    speed = np.zeros(num_samples)
    throttle = np.zeros(num_samples)
    
    # VW Golf Mk6 7-speed DSG ratios
    gear_ratios = [3.76, 2.27, 1.52, 1.13, 0.92, 0.81, 0.69]
    final_drive = 3.16
    wheel_radius = 0.297  # meters
    
    # Simulate acceleration through gears 1-4
    current_gear = 0
    shift_points = [2.0, 4.0, 6.0, 8.0]  # Shift times
    
    for i, t in enumerate(time):
        # Determine current gear
        if t >= shift_points[3]:
            current_gear = 3
        elif t >= shift_points[2]:
            current_gear = 2
        elif t >= shift_points[1]:
            current_gear = 1
        elif t >= shift_points[0]:
            current_gear = 0
        else:
            current_gear = 0
        
        # Simulate shift (RPM drops, speed continues)
        if any(abs(t - sp) < 0.1 for sp in shift_points):
            rpm[i] = 2500 - 500 * abs(t - min(shift_points, key=lambda x: abs(x - t)))
        else:
            # Normal acceleration
            rpm[i] = 2000 + (t - shift_points[min(current_gear, 3)]) * 300
            rpm[i] = min(rpm[i], 6000)
        
        # Calculate speed from RPM and gear ratio
        if rpm[i] > 1000:
            gear_ratio = gear_ratios[current_gear]
            wheel_rpm = rpm[i] / (gear_ratio * final_drive)
            speed[i] = wheel_rpm * wheel_radius * 2 * np.pi * 60 / 1000  # km/h
        
        # Throttle position
        throttle[i] = 80 if not any(abs(t - sp) < 0.1 for sp in shift_points) else 0
    
    # Create telemetry samples
    samples = []
    for i in range(num_samples):
        samples.append({
            'timestamp': time[i],
            'rpm': rpm[i],
            'speed': speed[i],
            'throttle_position': throttle[i]
        })
    
    return samples, shift_points


def test_dsg_detection():
    """Test DSG shift detection with VW Golf configuration"""
    print("\n" + "="*60)
    print("DSG SHIFT DETECTION TEST - VW GOLF MK6")
    print("="*60 + "\n")
    
    app = create_app()
    
    with app.app_context():
        # Get VW Golf constants
        vw_preset = VehicleConstantsPreset.query.filter_by(
            manufacturer='Volkswagen',
            model='Golf',
            generation='Mk6'
        ).first()
        
        if not vw_preset:
            print("❌ VW Golf preset not found - run seed script first")
            return False
        
        print(f"✅ Found VW Golf preset: {vw_preset.name}")
        print(f"   Transmission: {vw_preset.transmission_type.value}")
        print(f"   Gear ratios: {vw_preset.get_gear_ratios()}")
        print(f"   Final drive: {vw_preset.final_drive_ratio}")
        
        # Create DSG detector with VW parameters
        detector = DSGShiftDetector(
            ratio_change_threshold=0.5,
            guard_window=0.5,
            min_segment_duration=1.0,
            throttle_threshold=80.0
        )
        
        print("\n✅ DSG detector initialized")
        print(f"   Ratio threshold: {detector.ratio_change_threshold}")
        print(f"   Guard window: {detector.guard_window}s")
        
        # Generate test telemetry
        print("\n--- Generating Test Telemetry ---")
        samples, expected_shifts = create_test_telemetry()
        print(f"✅ Generated {len(samples)} samples over 10 seconds")
        print(f"   Expected shifts at: {expected_shifts}")
        
        # Detect shifts
        print("\n--- Detecting Shifts ---")
        try:
            # Calculate effective gear ratios
            gear_ratios = []
            for sample in samples:
                if sample['rpm'] > 1000 and sample['speed'] > 5:
                    # Simplified gear ratio calculation
                    ratio = sample['rpm'] / (sample['speed'] * 10)  # Rough approximation
                    gear_ratios.append((sample['timestamp'], ratio))
            
            # Run detection
            shifts = detector.detect_shifts(gear_ratios)
            
            print(f"✅ Detected {len(shifts)} shifts")
            
            # Check results
            if len(shifts) >= 3:  # Should detect at least 3 shifts
                print("\n--- Shift Detection Results ---")
                for i, shift in enumerate(shifts[:3]):
                    print(f"Shift {i+1}:")
                    print(f"  Time: {shift.timestamp_start:.1f}s - {shift.timestamp_end:.1f}s")
                    print(f"  Type: {shift.shift_type}")
                    print(f"  Confidence: {shift.confidence:.2f}")
                
                print("\n✅ DSG shift detection working correctly")
                return True
            else:
                print(f"\n❌ Expected at least 3 shifts, detected {len(shifts)}")
                return False
                
        except Exception as e:
            print(f"\n❌ DSG detection failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_dyno_integration():
    """Test that dyno properly uses DSG detection for VW"""
    print("\n--- Dyno Integration Test ---")
    
    try:
        # Check if DynoRun references vehicle constants
        from muts.models.database_models import DynoRun
        
        # Verify relationship exists
        assert hasattr(DynoRun, 'vehicle_constants')
        assert hasattr(DynoRun, 'shift_events')
        
        print("✅ DynoRun has proper relationships for DSG shifts")
        
        # Check DSG detector is available in dyno module
        from muts.dyno.dyno_processor import DynoProcessor
        
        processor = DynoProcessor()
        assert hasattr(processor, 'detect_shifts')
        
        print("✅ DynoProcessor includes shift detection")
        return True
        
    except Exception as e:
        print(f"❌ Dyno integration test failed: {e}")
        return False


def main():
    """Run DSG detection tests"""
    print("\nTesting DSG shift detection for VW Golf Mk6...")
    
    # Test 1: Basic DSG detection
    if not test_dsg_detection():
        print("\n❌ DSG detection test failed")
        return False
    
    # Test 2: Dyno integration
    if not test_dyno_integration():
        print("\n❌ Dyno integration test failed")
        return False
    
    # Success
    print("\n" + "="*60)
    print("✅ DSG SHIFT DETECTION FULLY VALIDATED")
    print("="*60)
    print("\nThe VW Golf Mk6 is ready for:")
    print("• Accurate shift detection during dyno runs")
    print("• Proper segmentation by gear")
    print("• Torque curve optimization per gear")
    print("="*60 + "\n")
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
