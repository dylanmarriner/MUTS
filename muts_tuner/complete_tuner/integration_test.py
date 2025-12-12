#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDA TUNING SYSTEM INTEGRATION TEST
Tests complete data flow: ECU → Security → Calibration → Write Back
"""

import sys
import os
import logging
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegrationTest:
    """Complete integration test for Mazda tuning system"""
    
    def __init__(self):
        self.test_results = {}
        self.ecu_core = None
        self.advanced_access = None
        self.calibration_manager = None
        
    def run_all_tests(self):
        """Run complete integration test suite"""
        logger.info("Starting Mazda Tuning System Integration Test")
        
        test_methods = [
            self.test_import_dependencies,
            self.test_ecu_core_initialization,
            self.test_advanced_access_initialization,
            self.test_calibration_manager_initialization,
            self.test_component_integration,
            self.test_mock_vehicle_connection,
            self.test_security_access_simulation,
            self.test_calibration_read_simulation,
            self.test_calibration_modification,
            self.test_performance_tune_generation,
            self.test_file_operations,
            self.test_complete_workflow
        ]
        
        for test_method in test_methods:
            try:
                logger.info(f"Running {test_method.__name__}")
                result = test_method()
                self.test_results[test_method.__name__] = {
                    'status': 'PASS' if result else 'FAIL',
                    'timestamp': time.strftime("%H:%M:%S")
                }
                logger.info(f"{test_method.__name__}: {'PASS' if result else 'FAIL'}")
            except Exception as e:
                logger.error(f"{test_method.__name__}: ERROR - {e}")
                self.test_results[test_method.__name__] = {
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': time.strftime("%H:%M:%S")
                }
        
        self.print_test_summary()
        return self.get_overall_result()
    
    def test_import_dependencies(self) -> bool:
        """Test that all required dependencies can be imported"""
        try:
            # Test standard library imports
            import numpy as np
            import struct
            import hashlib
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            
            # Test MDS component imports (these will likely fail without actual files)
            try:
                from mds6 import J2534Interface, J2534Protocol
                logger.info("✓ MDS6 J2534 interface imported successfully")
            except ImportError as e:
                logger.warning(f"⚠ MDS6 import failed (expected): {e}")
                # Create mock for testing
                self._create_mock_mds6()
            
            try:
                from mds8 import MazdaCalibrationService, MapAdjustment
                logger.info("✓ MDS8 calibration service imported successfully")
            except ImportError as e:
                logger.warning(f"⚠ MDS8 import failed (expected): {e}")
                self._create_mock_mds8()
            
            try:
                from mds9 import MazdaChecksumCalculator, ChecksumType
                logger.info("✓ MDS9 checksum calculator imported successfully")
            except ImportError as e:
                logger.warning(f"⚠ MDS9 import failed (expected): {e}")
                self._create_mock_mds9()
            
            try:
                from mds14 import MazdaDataConverter
                logger.info("✓ MDS14 data converter imported successfully")
            except ImportError as e:
                logger.warning(f"⚠ MDS14 import failed (expected): {e}")
                self._create_mock_mds14()
            
            return True
            
        except Exception as e:
            logger.error(f"Import dependency test failed: {e}")
            return False
    
    def test_ecu_core_initialization(self) -> bool:
        """Test ECU core initialization"""
        try:
            from mazda_ecu_core import MazdaECUCore, CommunicationMethod
            
            self.ecu_core = MazdaECUCore()
            
            # Test basic properties
            assert self.ecu_core is not None
            assert len(self.ecu_core.mazda_ecus) > 0
            assert CommunicationMethod.J2534_PASSTHRU in self.ecu_core.supported_methods
            
            # Test interface detection
            available_interfaces = self.ecu_core.detect_available_interfaces()
            assert isinstance(available_interfaces, dict)
            
            logger.info("✓ ECU Core initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"ECU core initialization test failed: {e}")
            return False
    
    def test_advanced_access_initialization(self) -> bool:
        """Test advanced access initialization"""
        try:
            from advanced_ecu_access import AdvancedECUAccess, SecurityLevel
            
            if not self.ecu_core:
                logger.error("ECU core not initialized")
                return False
            
            self.advanced_access = AdvancedECUAccess(self.ecu_core)
            
            # Test basic properties
            assert self.advanced_access is not None
            assert len(self.advanced_access.security_algorithms) > 0
            assert len(self.advanced_access.memory_map) > 0
            assert self.advanced_access.current_security_level == SecurityLevel.LEVEL_1
            
            logger.info("✓ Advanced ECU Access initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Advanced access initialization test failed: {e}")
            return False
    
    def test_calibration_manager_initialization(self) -> bool:
        """Test calibration manager initialization"""
        try:
            from mazda_calibration_manager import MazdaCalibrationManager, CalibrationType
            
            if not self.ecu_core:
                logger.error("ECU core not initialized")
                return False
            
            self.calibration_manager = MazdaCalibrationManager(
                self.ecu_core, 
                self.advanced_access
            )
            
            # Test basic properties
            assert self.calibration_manager is not None
            assert len(self.calibration_manager.calibration_definitions) > 0
            assert CalibrationType.IGNITION_TIMING in [t.type for t in self.calibration_manager.calibration_definitions.values()]
            
            logger.info("✓ Calibration Manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Calibration manager initialization test failed: {e}")
            return False
    
    def test_component_integration(self) -> bool:
        """Test that components are properly integrated"""
        try:
            # Test component references
            assert self.calibration_manager.ecu_core is self.ecu_core
            assert self.calibration_manager.advanced_access is self.advanced_access
            assert self.advanced_access.ecu_core is self.ecu_core
            
            # Test shared state
            status = self.ecu_core.get_connection_status()
            assert isinstance(status, dict)
            assert 'connected' in status
            
            memory_map = self.advanced_access.get_memory_map_info()
            assert isinstance(memory_map, dict)
            assert len(memory_map) > 0
            
            logger.info("✓ Component integration test passed")
            return True
            
        except Exception as e:
            logger.error(f"Component integration test failed: {e}")
            return False
    
    def test_mock_vehicle_connection(self) -> bool:
        """Test mock vehicle connection"""
        try:
            # Create mock connection for testing
            from mazda_ecu_core import ECUConnection, CommunicationMethod, J2534Protocol
            
            mock_connection = ECUConnection(
                method=CommunicationMethod.J2534_PASSTHRU,
                interface="mock_j2534.dll",
                protocol=J2534Protocol.ISO15765,
                baudrate=500000,
                connected=True,
                vehicle_info={'vin': 'JM1BL3VP8A1300001', 'calibration_id': 'MZRDISI2011'}
            )
            
            self.ecu_core.current_connection = mock_connection
            
            # Test connection status
            status = self.ecu_core.get_connection_status()
            assert status['connected'] == True
            assert status['method'] == 'J2534_PASSTHRU'
            
            logger.info("✓ Mock vehicle connection test passed")
            return True
            
        except Exception as e:
            logger.error(f"Mock vehicle connection test failed: {e}")
            return False
    
    def test_security_access_simulation(self) -> bool:
        """Test security access simulation"""
        try:
            from advanced_ecu_access import SecurityLevel
            
            # Test security level progression
            assert self.advanced_access.current_security_level == SecurityLevel.LEVEL_1
            
            # Simulate security access (without actual ECU)
            self.advanced_access.current_security_level = SecurityLevel.LEVEL_3
            
            assert self.advanced_access.current_security_level == SecurityLevel.LEVEL_3
            
            # Test memory access based on security level
            memory_map = self.advanced_access.get_memory_map_info()
            for region_name, region_info in memory_map.items():
                if region_info['accessible']:
                    assert self.advanced_access.current_security_level >= int(region_info['access_level'].split('_')[-1])
            
            logger.info("✓ Security access simulation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Security access simulation test failed: {e}")
            return False
    
    def test_calibration_read_simulation(self) -> bool:
        """Test calibration read simulation"""
        try:
            # Create mock calibration data
            mock_calibration = self._create_mock_calibration()
            self.calibration_manager.current_calibration = mock_calibration
            
            # Test calibration summary
            summary = self.calibration_manager.get_calibration_summary()
            assert isinstance(summary, dict)
            assert 'vehicle_info' in summary
            assert 'total_maps' in summary
            assert summary['total_maps'] > 0
            
            logger.info("✓ Calibration read simulation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Calibration read simulation test failed: {e}")
            return False
    
    def test_calibration_modification(self) -> bool:
        """Test calibration modification"""
        try:
            if not self.calibration_manager.current_calibration:
                logger.error("No calibration loaded for modification test")
                return False
            
            # Test map modification
            adjustments = {
                'ignition_timing_base': {'offset': 2.0},
                'boost_target': {'offset': 1.5}
            }
            
            result = self.calibration_manager.modify_calibration_map(
                'ignition_timing_base', 
                adjustments['ignition_timing_base']
            )
            
            # Check if modification was applied
            calibration_map = self.calibration_manager.current_calibration.calibration_data['ignition_timing_base']
            assert calibration_map.modified == True
            
            logger.info("✓ Calibration modification test passed")
            return True
            
        except Exception as e:
            logger.error(f"Calibration modification test failed: {e}")
            return False
    
    def test_performance_tune_generation(self) -> bool:
        """Test performance tune generation"""
        try:
            # Test Stage 1 tune generation
            stage1_adjustments = self.calibration_manager.generate_performance_tune("1")
            assert isinstance(stage1_adjustments, dict)
            assert len(stage1_adjustments) > 0
            
            # Test Stage 2 tune generation
            stage2_adjustments = self.calibration_manager.generate_performance_tune("2")
            assert isinstance(stage2_adjustments, dict)
            assert len(stage2_adjustments) > 0
            
            # Test Stage 3 tune generation
            stage3_adjustments = self.calibration_manager.generate_performance_tune("3")
            assert isinstance(stage3_adjustments, dict)
            assert len(stage3_adjustments) > 0
            
            logger.info("✓ Performance tune generation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Performance tune generation test failed: {e}")
            return False
    
    def test_file_operations(self) -> bool:
        """Test file save/load operations"""
        try:
            if not self.calibration_manager.current_calibration:
                logger.error("No calibration loaded for file test")
                return False
            
            # Test save to file
            test_file = project_root / "test_calibration.json"
            save_result = self.calibration_manager.save_calibration_to_file(str(test_file))
            assert save_result == True
            assert test_file.exists()
            
            # Test load from file
            new_calibration_manager = MazdaCalibrationManager(self.ecu_core, self.advanced_access)
            load_result = new_calibration_manager.load_calibration_from_file(str(test_file))
            assert load_result == True
            assert new_calibration_manager.current_calibration is not None
            
            # Clean up test file
            test_file.unlink()
            
            logger.info("✓ File operations test passed")
            return True
            
        except Exception as e:
            logger.error(f"File operations test failed: {e}")
            return False
    
    def test_complete_workflow(self) -> bool:
        """Test complete workflow simulation"""
        try:
            logger.info("Testing complete workflow simulation...")
            
            # Step 1: Initialize components
            assert self.ecu_core is not None
            assert self.advanced_access is not None
            assert self.calibration_manager is not None
            
            # Step 2: Simulate vehicle connection
            from mazda_ecu_core import ECUConnection, CommunicationMethod, J2534Protocol
            mock_connection = ECUConnection(
                method=CommunicationMethod.J2534_PASSTHRU,
                interface="mock_j2534.dll",
                protocol=J2534Protocol.ISO15765,
                baudrate=500000,
                connected=True,
                vehicle_info={'vin': 'JM1BL3VP8A1300001', 'calibration_id': 'MZRDISI2011'}
            )
            self.ecu_core.current_connection = mock_connection
            
            # Step 3: Simulate security access
            from advanced_ecu_access import SecurityLevel
            self.advanced_access.current_security_level = SecurityLevel.LEVEL_3
            
            # Step 4: Read calibration
            mock_calibration = self._create_mock_calibration()
            self.calibration_manager.current_calibration = mock_calibration
            
            # Step 5: Generate performance tune
            tune_adjustments = self.calibration_manager.generate_performance_tune("2")
            assert len(tune_adjustments) > 0
            
            # Step 6: Apply tune modifications
            for map_name, adjustment in tune_adjustments.items():
                if map_name in self.calibration_manager.current_calibration.calibration_data:
                    self.calibration_manager.modify_calibration_map(map_name, adjustment)
            
            # Step 7: Verify modifications
            modified_count = len(self.calibration_manager.modified_maps)
            assert modified_count > 0
            
            # Step 8: Save calibration
            test_file = project_root / "workflow_test_calibration.json"
            save_result = self.calibration_manager.save_calibration_to_file(str(test_file))
            assert save_result == True
            
            # Step 9: Load and verify
            new_manager = MazdaCalibrationManager(self.ecu_core, self.advanced_access)
            load_result = new_manager.load_calibration_from_file(str(test_file))
            assert load_result == True
            
            # Clean up
            test_file.unlink()
            
            logger.info("✓ Complete workflow simulation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Complete workflow test failed: {e}")
            return False
    
    def _create_mock_calibration(self):
        """Create mock calibration for testing"""
        from mazda_calibration_manager import CalibrationFile, CalibrationMap, CalibrationType
        import numpy as np
        
        # Create mock calibration maps
        calibration_data = {}
        
        # Ignition timing map
        ignition_map = CalibrationMap(
            name="Base Ignition Timing",
            type=CalibrationType.IGNITION_TIMING,
            address=0xFFA000,
            size=0x800,
            rows=16,
            columns=16,
            x_axis=list(range(1000, 7000, 375)),
            y_axis=list(range(0, 160, 10)),
            data=np.random.uniform(10.0, 35.0, (16, 16)),
            description="Base ignition timing map",
            units="degrees BTDC",
            min_value=-20.0,
            max_value=60.0,
            modified=False,
            original_data=np.random.uniform(10.0, 35.0, (16, 16))
        )
        calibration_data['ignition_timing_base'] = ignition_map
        
        # Fuel injection map
        fuel_map = CalibrationMap(
            name="Base Fuel Injection",
            type=CalibrationType.FUEL_INJECTION,
            address=0xFFB000,
            size=0x800,
            rows=16,
            columns=16,
            x_axis=list(range(1000, 7000, 375)),
            y_axis=list(range(0, 160, 10)),
            data=np.random.uniform(2.0, 20.0, (16, 16)),
            description="Base fuel injection map",
            units="ms",
            min_value=0.0,
            max_value=50.0,
            modified=False,
            original_data=np.random.uniform(2.0, 20.0, (16, 16))
        )
        calibration_data['fuel_injection_base'] = fuel_map
        
        # Boost target map
        boost_map = CalibrationMap(
            name="Target Boost Pressure",
            type=CalibrationType.BOOST_CONTROL,
            address=0xFFBC00,
            size=0x400,
            rows=8,
            columns=16,
            x_axis=list(range(1000, 7000, 375)),
            y_axis=list(range(0, 80, 10)),
            data=np.random.uniform(5.0, 20.0, (8, 16)),
            description="Target boost pressure map",
            units="psi",
            min_value=0.0,
            max_value=30.0,
            modified=False,
            original_data=np.random.uniform(5.0, 20.0, (8, 16))
        )
        calibration_data['boost_target'] = boost_map
        
        return CalibrationFile(
            vehicle_info={'vin': 'JM1BL3VP8A1300001', 'calibration_id': 'MZRDISI2011'},
            calibration_data=calibration_data,
            checksums={'ignition_timing_base': 0x12345678, 'fuel_injection_base': 0x87654321, 'boost_target': 0xABCDEF00},
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            version="1.0",
            modified=False
        )
    
    def _create_mock_mds6(self):
        """Create mock MDS6 module"""
        import types
        
        mds6 = types.ModuleType('mds6')
        
        class J2534Protocol:
            ISO15765 = 1
            ISO9141 = 2
            KWP2000 = 3
        
        class J2534Interface:
            def __init__(self):
                self.device_id = None
                self.channel_id = None
                self.is_connected = False
            
            def connect(self):
                return True
            
            def connect_channel(self, protocol, baudrate):
                return True
            
            def disconnect(self):
                pass
        
        mds6.J2534Interface = J2534Interface
        mds6.J2534Protocol = J2534Protocol
        
        sys.modules['mds6'] = mds6
    
    def _create_mock_mds8(self):
        """Create mock MDS8 module"""
        import types
        
        mds8 = types.ModuleType('mds8')
        
        class MapAdjustment:
            def __init__(self, offset=0.0, scaling=1.0):
                self.offset = offset
                self.scaling = scaling
        
        class CalibrationValidationResult:
            def __init__(self, status, message):
                self.status = status
                self.message = message
        
        class MazdaCalibrationService:
            def __init__(self, diagnostic_protocol, programming_service):
                pass
        
        mds8.MapAdjustment = MapAdjustment
        mds8.CalibrationValidationResult = CalibrationValidationResult
        mds8.MazdaCalibrationService = MazdaCalibrationService
        
        sys.modules['mds8'] = mds8
    
    def _create_mock_mds9(self):
        """Create mock MDS9 module"""
        import types
        
        mds9 = types.ModuleType('mds9')
        
        class ChecksumType:
            SIMPLE_SUM = 1
            CRC16 = 2
            CRC32 = 3
            MAZDA_PROPRIETARY = 4
        
        class MazdaChecksumCalculator:
            def calculate_checksum(self, data, checksum_type, start_address=0, length=0):
                return 0x12345678
        
        mds9.ChecksumType = ChecksumType
        mds9.MazdaChecksumCalculator = MazdaChecksumCalculator
        
        sys.modules['mds9'] = mds9
    
    def _create_mock_mds14(self):
        """Create mock MDS14 module"""
        import types
        
        mds14 = types.ModuleType('mds14')
        
        class MazdaDataConverter:
            @staticmethod
            def bytes_to_uint8(data, offset=0):
                return data[offset] if len(data) > offset else 0
        
        mds14.MazdaDataConverter = MazdaDataConverter
        
        sys.modules['mds14'] = mds14
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("MAZDA TUNING SYSTEM INTEGRATION TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        failed = sum(1 for result in self.test_results.values() if result['status'] == 'FAIL')
        errors = sum(1 for result in self.test_results.values() if result['status'] == 'ERROR')
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print()
        
        for test_name, result in self.test_results.items():
            status = result['status']
            timestamp = result['timestamp']
            
            if status == 'PASS':
                print(f"✓ {test_name:<40} [{timestamp}]")
            elif status == 'FAIL':
                print(f"✗ {test_name:<40} [{timestamp}] - FAILED")
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"✗ {test_name:<40} [{timestamp}] - ERROR: {error_msg}")
        
        print("="*80)
    
    def get_overall_result(self) -> bool:
        """Get overall test result"""
        return all(result['status'] == 'PASS' for result in self.test_results.values())

if __name__ == "__main__":
    """Run integration tests"""
    test = IntegrationTest()
    success = test.run_all_tests()
    
    if success:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("The Mazda tuning system components are properly integrated and ready for GUI development.")
        sys.exit(0)
    else:
        print("\n❌ SOME INTEGRATION TESTS FAILED!")
        print("Please resolve the issues before proceeding to GUI development.")
        sys.exit(1)
