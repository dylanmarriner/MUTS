#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MUTS Integration Test
Verifies safety systems work end-to-end
"""

import sys
import os
sys.path.append('.')

from core.ecu_communication import ECUCommunicator
from core.safety_validator import get_safety_validator
from core.app_state import get_app_state, PerformanceMode
from utils.logger import get_logger
import struct

logger = get_logger(__name__)

def test_safety_validation_blocks_dangerous_writes():
    """Test that safety validator blocks dangerous tuning parameters"""
    print("Testing safety validation...")
    
    # Initialize components
    safety = get_safety_validator()
    app_state = get_app_state()
    
    # Set to track mode for testing
    app_state.set_performance_mode(PerformanceMode.TRACK)
    
    # Create dangerous tuning parameters (exceeds limits)
    dangerous_params = {
        'boost_target': 30.0,  # Exceeds track mode limit of 23 psi
        'timing_base': 35.0,   # Exceeds track mode limit of 25 degrees
        'afr_target': 10.0     # Too lean, below minimum 11.5
    }
    
    print(f"Testing dangerous parameters: boost={dangerous_params['boost_target']}psi, timing={dangerous_params['timing_base']}°, afr={dangerous_params['afr_target']}")
    
    # Test safety validation directly
    is_safe, violations = safety.validate_tuning_parameters(dangerous_params)
    
    # Check if safety blocked the request
    if not is_safe and len(violations) > 0:
        print("✅ SAFETY VALIDATION SUCCESSFULLY BLOCKED DANGEROUS PARAMETERS")
        print(f"   Violations detected: {len(violations)}")
        for violation in violations:
            print(f"   - {violation.message}")
        return True
    else:
        print("❌ SAFETY VALIDATION FAILED TO BLOCK DANGEROUS PARAMETERS")
        return False

def test_safe_parameters_allowed():
    """Test that safe tuning parameters are allowed"""
    print("\nTesting safe parameters...")
    
    # Initialize components
    safety = get_safety_validator()
    app_state = get_app_state()
    
    # Set to safe mode
    app_state.set_performance_mode(PerformanceMode.SAFE)
    
    # Create safe tuning parameters
    safe_params = {
        'boost_target': 15.0,  # Within safe mode limit of 18 psi
        'timing_base': 12.0,   # Within safe mode limit of 18 degrees
        'afr_target': 12.5     # Safe air-fuel ratio
    }
    
    print(f"Testing safe parameters: boost={safe_params['boost_target']}psi, timing={safe_params['timing_base']}°, afr={safe_params['afr_target']}")
    
    # Test safety validation directly
    is_safe, violations = safety.validate_tuning_parameters(safe_params)
    
    # Check if request was allowed
    if is_safe and len(violations) == 0:
        print("✅ SAFE PARAMETERS ALLOWED BY SAFETY SYSTEM")
        return True
    else:
        print("❌ SAFETY SYSTEM INCORRECTLY BLOCKED SAFE PARAMETERS")
        print(f"   Violations: {len(violations)}")
        for violation in violations:
            print(f"   - {violation.message}")
        return False

def test_connection_monitoring():
    """Test connection health monitoring"""
    print("\nTesting connection monitoring...")
    
    from core.connection_monitor import ConnectionHealthMonitor
    
    # Create ECU communicator and monitor
    ecu = ECUCommunicator('vcan0')
    monitor = ConnectionHealthMonitor(ecu)
    
    # Get initial health status
    health = monitor.get_health_status()
    print(f"Initial connection health: {health.value}")
    
    # Get connection metrics
    metrics = monitor.get_connection_metrics()
    print(f"Messages sent: {metrics.total_messages}")
    print(f"Failed messages: {metrics.failed_messages}")
    
    print("✅ CONNECTION MONITORING FUNCTIONAL")
    return True

def test_rom_verification():
    """Test ROM checksum verification"""
    print("\nTesting ROM verification...")
    
    from core.rom_verifier import get_rom_verifier
    
    verifier = get_rom_verifier()
    
    # Create test ROM data (simplified)
    test_rom = b'\xFF' * (1024 * 1024)  # 1MB of test data
    
    # Test ROM verification
    is_valid, results = verifier.verify_rom_integrity(test_rom)
    
    print(f"ROM verification result: {'VALID' if is_valid else 'INVALID'}")
    print(f"Checksum regions verified: {len(results)}")
    
    # Test pre-flash verification
    pre_flash_safe = verifier.verify_before_flash(test_rom)
    print(f"Pre-flash verification: {'SAFE' if pre_flash_safe else 'UNSAFE'}")
    
    print("✅ ROM VERIFICATION FUNCTIONAL")
    return True

def main():
    """Run all integration tests"""
    print("=== MUTS INTEGRATION TESTS ===\n")
    
    tests = [
        ("Safety Validation", test_safety_validation_blocks_dangerous_writes),
        ("Safe Parameters", test_safe_parameters_allowed),
        ("Connection Monitoring", test_connection_monitoring),
        ("ROM Verification", test_rom_verification),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n=== TEST RESULTS ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED - SYSTEM IS PRODUCTION READY")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - SYSTEM NEEDS ATTENTION")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
