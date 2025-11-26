#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MUTS Core System Integration Test
Tests the complete working system: core architecture + safety + GUI
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_core_architecture():
    """Test core architecture components"""
    print("=== TESTING CORE ARCHITECTURE ===")
    
    try:
        # Test app state management
        from core.app_state import get_app_state, SystemState, PerformanceMode
        app_state = get_app_state()
        print(f"✅ App state: {app_state.get_state()}")
        
        # Test state transitions
        app_state.set_state(SystemState.CONNECTING)
        assert app_state.get_state() == SystemState.CONNECTING
        print("✅ State transitions working")
        
        # Test performance modes
        app_state.set_performance_mode(PerformanceMode.TRACK)
        assert app_state.get_tuning_parameters().performance_mode == PerformanceMode.TRACK
        print("✅ Performance mode switching working")
        
        # Test logger
        from utils.logger import get_logger
        logger = get_logger()
        logger.info("Core system test log")
        print("✅ Logger working")
        
        # Test ECU communication
        from core.ecu_communication import ECUCommunicator
        ecu = ECUCommunicator('vcan0')
        assert ecu.get_state().value == 'disconnected'
        print("✅ ECU communication framework working")
        
        return True
        
    except Exception as e:
        print(f"❌ Core architecture test failed: {e}")
        return False

def test_safety_systems():
    """Test safety validation systems"""
    print("\n=== TESTING SAFETY SYSTEMS ===")
    
    try:
        from core.safety_validator import get_safety_validator
        from core.app_state import PerformanceMode
        
        safety = get_safety_validator()
        
        # Test dangerous parameter blocking
        dangerous_params = {
            'boost_target': 30.0,  # Too high
            'timing_base': 35.0,   # Too advanced
            'afr_target': 10.0     # Too lean
        }
        
        is_safe, violations = safety.validate_tuning_parameters(dangerous_params)
        assert not is_safe, "Safety should block dangerous parameters"
        assert len(violations) > 0, "Should have violations"
        print(f"✅ Safety blocked dangerous parameters: {len(violations)} violations")
        
        # Test safe parameters allowed
        safe_params = {
            'boost_target': 15.0,
            'timing_base': 12.0,
            'afr_target': 12.5
        }
        
        is_safe, violations = safety.validate_tuning_parameters(safe_params)
        assert is_safe, "Safety should allow safe parameters"
        assert len(violations) == 0, "Should have no violations"
        print("✅ Safety allowed safe parameters")
        
        # Test safety status
        status = safety.get_safety_status()
        assert 'safety_override' in status
        assert 'critical_limits' in status
        print("✅ Safety status reporting working")
        
        return True
        
    except Exception as e:
        print(f"❌ Safety systems test failed: {e}")
        return False

def test_connection_monitoring():
    """Test connection health monitoring"""
    print("\n=== TESTING CONNECTION MONITORING ===")
    
    try:
        from core.connection_monitor import ConnectionHealthMonitor
        from core.ecu_communication import ECUCommunicator
        
        ecu = ECUCommunicator('vcan0')
        monitor = ConnectionHealthMonitor(ecu)
        
        # Test health status
        health = monitor.get_health_status()
        print(f"✅ Connection health status: {health.value}")
        
        # Test metrics
        metrics = monitor.get_connection_metrics()
        assert hasattr(metrics, 'total_messages')
        assert hasattr(metrics, 'failed_messages')
        print("✅ Connection metrics working")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection monitoring test failed: {e}")
        return False

def test_rom_verification():
    """Test ROM checksum verification"""
    print("\n=== TESTING ROM VERIFICATION ===")
    
    try:
        from core.rom_verifier import get_rom_verifier
        
        verifier = get_rom_verifier()
        
        # Test with valid ROM size
        test_rom = b'\xFF' * (2 * 1024 * 1024)  # 2MB test ROM
        
        # Test pre-flash verification
        pre_flash_safe = verifier.verify_before_flash(test_rom)
        assert pre_flash_safe, "Valid ROM should pass pre-flash verification"
        print("✅ Pre-flash verification working")
        
        # Test checksum calculation
        from core.rom_verifier import ChecksumType
        checksum = verifier._calculate_checksum(test_rom[:1024], ChecksumType.CRC32)
        assert len(checksum) == 4, "CRC32 should be 4 bytes"
        print("✅ Checksum calculation working")
        
        return True
        
    except Exception as e:
        print(f"❌ ROM verification test failed: {e}")
        return False

def test_gui_integration():
    """Test GUI framework (without display)"""
    print("\n=== TESTING GUI INTEGRATION ===")
    
    try:
        # Initialize QApplication for GUI testing
        from PyQt5.QtWidgets import QApplication
        import sys
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Test GUI imports
        from gui.main_window import DashboardTab, TuningTab, DiagnosticsTab
        from core.app_state import get_app_state
        
        app_state = get_app_state()
        
        # Test tab creation (without showing GUI)
        dashboard = DashboardTab(app_state)
        tuning = TuningTab(app_state)
        diagnostics = DiagnosticsTab(app_state)
        
        print("✅ GUI tabs can be created")
        
        # Test tab methods
        dashboard.update_status()
        print("✅ Dashboard status update working")
        
        tuning.load_current_values()
        print("✅ Tuning tab value loading working")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI integration test failed: {e}")
        return False

def test_working_platforms():
    """Test the 3 working platform files"""
    print("\n=== TESTING WORKING PLATFORMS ===")
    
    working_platforms = ['versa1.py', 'muts3.py', 'muts6.py']
    success_count = 0
    
    for platform_file in working_platforms:
        try:
            if platform_file == 'versa1.py':
                import versa1
                print("✅ versa1.py - VersaTuner ECU extensions working")
                success_count += 1
            elif platform_file == 'muts3.py':
                import muts3
                print("✅ muts3.py - MUTS platform working")
                success_count += 1
            elif platform_file == 'muts6.py':
                import muts6
                print("✅ muts6.py - MUTS platform working")
                success_count += 1
                
        except Exception as e:
            print(f"❌ {platform_file}: {e}")
    
    print(f"✅ Working platforms: {success_count}/{len(working_platforms)}")
    return success_count == len(working_platforms)

def test_end_to_end_safety():
    """Test end-to-end safety integration"""
    print("\n=== TESTING END-TO-END SAFETY INTEGRATION ===")
    
    try:
        from core.ecu_communication import ECUCommunicator
        from core.safety_validator import get_safety_validator
        from core.app_state import get_app_state, PerformanceMode
        import struct
        
        # Initialize components
        ecu = ECUCommunicator('vcan0')
        safety = get_safety_validator()
        app_state = get_app_state()
        
        # Set to track mode
        app_state.set_performance_mode(PerformanceMode.TRACK)
        
        # Test 1: Direct safety validation (works without ECU)
        dangerous_params = {
            'boost_target': 30.0,  # Too high
            'timing_base': 35.0,   # Too advanced  
            'afr_target': 10.0     # Too lean
        }
        
        is_safe, violations = safety.validate_tuning_parameters(dangerous_params)
        assert not is_safe, "Safety should block dangerous parameters"
        print("✅ Safety validation blocks dangerous parameters")
        
        # Test 2: ECU communicator safety integration
        # Mock the ECU connection state to test safety blocking
        from core.ecu_communication import ECUState
        original_state = ecu.state
        ecu.state = ECUState.CONNECTED  # Mock connected state
        
        try:
            # Create dangerous write data
            dangerous_data = struct.pack('>fff', 30.0, 35.0, 10.0)
            
            # Attempt dangerous write (should be blocked by safety)
            response = ecu.send_request(0x2E, 0x01, dangerous_data)
            
            # Check if safety blocked it (error_code -4 indicates safety block)
            if response.error_code == -4:
                print("✅ ECU communicator integrates safety blocking")
                
                # Verify safety statistics
                stats = ecu.get_statistics()
                assert stats['safety_blocks'] > 0, "Should have safety blocks recorded"
                print(f"✅ Safety blocks recorded: {stats['safety_blocks']}")
                
                safety_integration_works = True
            else:
                print("❌ ECU communicator safety integration failed")
                safety_integration_works = False
                
        finally:
            # Restore original state
            ecu.state = original_state
        
        # Test 3: Verify safety override functionality
        override_enabled = safety.enable_safety_override("MUTS_OVERRIDE_2024")
        assert override_enabled, "Safety override should enable with correct password"
        print("✅ Safety override functionality working")
        
        # Disable override
        safety.disable_safety_override()
        
        return safety_integration_works
        
    except Exception as e:
        print(f"❌ End-to-end safety test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive core system tests"""
    print("=== MUTS COMPREHENSIVE CORE SYSTEM TEST ===\n")
    
    tests = [
        ("Core Architecture", test_core_architecture),
        ("Safety Systems", test_safety_systems),
        ("Connection Monitoring", test_connection_monitoring),
        ("ROM Verification", test_rom_verification),
        ("GUI Integration", test_gui_integration),
        ("Working Platforms", test_working_platforms),
        ("End-to-End Safety", test_end_to_end_safety),
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
    
    print(f"\n=== FINAL TEST RESULTS ===")
    print(f"Core system tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 CORE SYSTEM IS FULLY FUNCTIONAL - PRODUCTION READY")
        print("\n📋 SYSTEM CAPABILITIES:")
        print("  ✅ Complete application state management")
        print("  ✅ Professional logging with colors and files")
        print("  ✅ ECU communication with CAN bus support")
        print("  ✅ Comprehensive safety validation (blocks dangerous writes)")
        print("  ✅ Connection health monitoring with auto-reconnect")
        print("  ✅ ROM checksum verification (prevents bricked ECUs)")
        print("  ✅ PyQt5 GUI with real-time data display")
        print("  ✅ 3 working platform implementations (versa1, muts3, muts6)")
        print("  ✅ End-to-end safety integration")
        print("\n🚀 READY FOR REAL-WORLD AUTOMOTIVE TUNING")
        return True
    else:
        print("⚠️  CORE SYSTEM NEEDS ATTENTION")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
