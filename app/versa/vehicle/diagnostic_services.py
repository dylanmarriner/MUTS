#!/usr/bin/env python3
"""
Diagnostic Services Module - Complete diagnostic functionality for Mazdaspeed 3
Implements all Mazda-specific diagnostic services and routines
"""

import time
import struct
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from ..core.ecu_communication import ECUCommunicator, ECUResponse
from ..utils.logger import VersaLogger

@dataclass
class DiagnosticService:
    """Definition of a diagnostic service"""
    service_id: int
    subfunction: int
    description: str
    request_data: bytes
    response_parser: Callable

class DiagnosticManager:
    """
    Comprehensive diagnostic service manager for Mazdaspeed 3
    Implements all factory diagnostic routines and tests
    """
    
    def __init__(self, ecu_communicator: ECUCommunicator):
        """
        Initialize Diagnostic Manager
        
        Args:
            ecu_communicator: ECUCommunicator instance
        """
        self.ecu = ecu_communicator
        self.logger = VersaLogger(__name__)
        
        # Diagnostic service definitions
        self.services = self._initialize_services()
        
        # Test results storage
        self.test_results = {}
    
    def _initialize_services(self) -> Dict[str, DiagnosticService]:
        """Initialize all diagnostic services"""
        return {
            'system_readiness': DiagnosticService(
                0x01, 0x01, "Read System Readiness",
                b'', self._parse_readiness_codes
            ),
            'freeze_frame_data': DiagnosticService(
                0x12, 0x00, "Read Freeze Frame Data", 
                b'', self._parse_freeze_frame
            ),
            'component_test': DiagnosticService(
                0x31, 0x01, "Component Active Test",
                b'', self._parse_component_test
            ),
            'clear_adaptations': DiagnosticService(
                0x31, 0xFF, "Clear All Adaptations",
                b'', self._parse_clear_adaptations
            ),
            'turbo_test': DiagnosticService(
                0x31, 0x11, "Turbocharger System Test",
                b'', self._parse_turbo_test
            ),
            'fuel_system_test': DiagnosticService(
                0x31, 0x12, "Fuel System Test",
                b'', self._parse_fuel_system_test
            ),
            'ignition_system_test': DiagnosticService(
                0x31, 0x13, "Ignition System Test", 
                b'', self._parse_ignition_test
            )
        }
    
    def execute_diagnostic_routine(self, routine_name: str, 
                                 parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute diagnostic routine
        
        Args:
            routine_name: Name of diagnostic routine
            parameters: Optional parameters for the routine
            
        Returns:
            Dict containing test results
        """
        if routine_name not in self.services:
            raise ValueError(f"Unknown diagnostic routine: {routine_name}")
        
        service = self.services[routine_name]
        self.logger.info(f"Executing diagnostic routine: {service.description}")
        
        try:
            # Execute service
            response = self.ecu.send_request(service.service_id, service.subfunction, service.request_data)
            
            if response.success:
                # Parse response
                result = service.response_parser(response.data)
                self.test_results[routine_name] = result
                
                self.logger.info(f"Diagnostic routine completed: {routine_name}")
                return result
            else:
                error = {
                    'success': False,
                    'error_code': response.error_code,
                    'message': 'Diagnostic routine failed'
                }
                self.test_results[routine_name] = error
                return error
                
        except Exception as e:
            error = {
                'success': False,
                'error': str(e),
                'message': 'Diagnostic routine error'
            }
            self.test_results[routine_name] = error
            self.logger.error(f"Diagnostic routine error: {e}")
            return error
    
    def _parse_readiness_codes(self, data: bytes) -> Dict[str, Any]:
        """Parse system readiness response"""
        if len(data) < 4:
            return {'success': False, 'message': 'Invalid response length'}
        
        # Extract readiness bits
        readiness_byte = data[3]
        
        readiness_flags = {
            'misfire': bool(readiness_byte & 0x01),
            'fuel_system': bool(readiness_byte & 0x02),
            'components': bool(readiness_byte & 0x04),
            'catalyst': bool(readiness_byte & 0x08),
            'heated_catalyst': bool(readiness_byte & 0x10),
            'evap_system': bool(readiness_byte & 0x20),
            'secondary_air': bool(readiness_byte & 0x40),
            'ac_system': bool(readiness_byte & 0x80),
        }
        
        return {
            'success': True,
            'readiness_flags': readiness_flags,
            'ready_count': sum(readiness_flags.values()),
            'total_count': len(readiness_flags)
        }
    
    def _parse_freeze_frame(self, data: bytes) -> Dict[str, Any]:
        """Parse freeze frame data response"""
        if len(data) < 20:
            return {'success': False, 'message': 'Invalid freeze frame data'}
        
        # Parse freeze frame snapshot
        dtc_code = self._parse_dtc_code(data[3:5])
        freeze_frame = {
            'success': True,
            'dtc_code': dtc_code,
            'timestamp': time.time(),
            'data': {}
        }
        
        # Extract sensor values (simplified)
        if len(data) >= 12:
            freeze_frame['data']['rpm'] = struct.unpack('>H', data[6:8])[0]
            freeze_frame['data']['load'] = struct.unpack('>H', data[8:10])[0] / 100
            freeze_frame['data']['speed'] = struct.unpack('>H', data[10:12])[0]
        
        return freeze_frame
    
    def _parse_component_test(self, data: bytes) -> Dict[str, Any]:
        """Parse component test response"""
        if len(data) < 4:
            return {'success': False, 'message': 'Invalid test response'}
        
        test_status = data[3]
        
        return {
            'success': True,
            'test_status': test_status,
            'completed': bool(test_status & 0x01),
            'passed': bool(test_status & 0x02),
            'failed': bool(test_status & 0x04),
            'running': bool(test_status & 0x08)
        }
    
    def _parse_clear_adaptations(self, data: bytes) -> Dict[str, Any]:
        """Parse clear adaptations response"""
        return {
            'success': True,
            'message': 'Adaptations cleared successfully'
        }
    
    def _parse_turbo_test(self, data: bytes) -> Dict[str, Any]:
        """Parse turbocharger test response"""
        if len(data) < 10:
            return {'success': False, 'message': 'Invalid turbo test response'}
        
        # Extract turbo test results
        boost_actual = struct.unpack('>H', data[4:6])[0] / 100
        boost_target = struct.unpack('>H', data[6:8])[0] / 100
        wastegate_duty = struct.unpack('>H', data[8:10])[0] / 10
        
        return {
            'success': True,
            'boost_actual': boost_actual,
            'boost_target': boost_target,
            'boost_error': boost_actual - boost_target,
            'wastegate_duty': wastegate_duty,
            'test_passed': abs(boost_actual - boost_target) < 1.0
        }
    
    def _parse_fuel_system_test(self, data: bytes) -> Dict[str, Any]:
        """Parse fuel system test response"""
        if len(data) < 12:
            return {'success': False, 'message': 'Invalid fuel test response'}
        
        # Extract fuel test results
        fuel_pressure = struct.unpack('>H', data[4:6])[0] / 10
        injector_duty = struct.unpack('>H', data[6:8])[0] / 10
        afr_measured = struct.unpack('>H', data[8:10])[0] / 10
        afr_target = struct.unpack('>H', data[10:12])[0] / 10
        
        return {
            'success': True,
            'fuel_pressure': fuel_pressure,
            'injector_duty': injector_duty,
            'afr_measured': afr_measured,
            'afr_target': afr_target,
            'afr_error': afr_measured - afr_target,
            'test_passed': abs(afr_measured - afr_target) < 0.5
        }
    
    def _parse_ignition_test(self, data: bytes) -> Dict[str, Any]:
        """Parse ignition system test response"""
        if len(data) < 10:
            return {'success': False, 'message': 'Invalid ignition test response'}
        
        # Extract ignition test results
        timing_advance = struct.unpack('>H', data[4:6])[0] / 10
        knock_count = struct.unpack('>H', data[6:8])[0]
        dwell_time = struct.unpack('>H', data[8:10])[0] / 10
        
        return {
            'success': True,
            'timing_advance': timing_advance,
            'knock_count': knock_count,
            'dwell_time': dwell_time,
            'test_passed': knock_count < 5
        }
    
    def _parse_dtc_code(self, dtc_bytes: bytes) -> str:
        """Parse 2-byte DTC to standard format"""
        if len(dtc_bytes) != 2:
            return ""
        
        first_byte = dtc_bytes[0]
        second_byte = dtc_bytes[1]
        
        dtc_type = (first_byte >> 6) & 0x03
        digit1 = (first_byte >> 4) & 0x03
        digit2 = first_byte & 0x0F
        digit3 = (second_byte >> 4) & 0x0F
        digit4 = second_byte & 0x0F
        
        type_map = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
        type_char = type_map.get(dtc_type, 'P')
        
        return f"{type_char}{digit1}{digit2}{digit3}{digit4}"
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """
        Run complete diagnostic suite
        
        Returns:
            Dict containing all test results
        """
        self.logger.info("Starting full diagnostic suite")
        
        results = {
            'timestamp': time.time(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0
            }
        }
        
        # Run all diagnostic routines
        for routine_name in self.services.keys():
            test_result = self.execute_diagnostic_routine(routine_name)
            results['tests'][routine_name] = test_result
            
            # Update summary
            results['summary']['total_tests'] += 1
            if test_result.get('success', False):
                if test_result.get('test_passed', True):
                    results['summary']['passed_tests'] += 1
                else:
                    results['summary']['failed_tests'] += 1
            else:
                results['summary']['failed_tests'] += 1
        
        self.logger.info(f"Diagnostic suite completed: {results['summary']['passed_tests']}/{results['summary']['total_tests']} passed")
        return results
    
    def get_test_results(self, test_name: str = None) -> Dict[str, Any]:
        """
        Get test results
        
        Args:
            test_name: Specific test name, or None for all results
            
        Returns:
            Dict containing test results
        """
        if test_name:
            return self.test_results.get(test_name, {})
        return self.test_results.copy()
    
    def clear_test_results(self):
        """Clear all stored test results"""
        self.test_results.clear()
        self.logger.info("Test results cleared")
