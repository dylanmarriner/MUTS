from core.ecu_communication import ECUCommunicator, ECUResponse, ECUState
from core.safety_validator import get_safety_validator
from utils.logger import get_logger
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
                result['status'] = 'COMPLETED'
                result['timestamp'] = time.time()
                
                # Store results
                self.test_results[routine_name] = result
                return result
            else:
                return {
                    'status': 'FAILED',
                    'error': f"Service execution failed: {response.error_code:02X}",
                    'timestamp': time.time()
                }
                
        except Exception as e:
            self.logger.error(f"Diagnostic routine failed: {e}")
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def _parse_readiness_codes(self, data: bytes) -> Dict[str, Any]:
        """Parse system readiness codes"""
        if len(data) < 4:
            return {'error': 'Invalid response length'}
        
        readiness_byte = data[3]  # Typically byte 3 contains readiness status
        
        monitors = {
            'catalyst': (readiness_byte >> 0) & 0x01,
            'heated_catalyst': (readiness_byte >> 1) & 0x01,
            'evap_system': (readiness_byte >> 2) & 0x01,
            'secondary_air': (readiness_byte >> 3) & 0x01,
            'ac_system': (readiness_byte >> 4) & 0x01,
            'oxygen_sensor': (readiness_byte >> 5) & 0x01,
            'oxygen_sensor_heater': (readiness_byte >> 6) & 0x01,
            'egr_system': (readiness_byte >> 7) & 0x01
        }
        
        # Convert to status strings
        status = {}
        for monitor, value in monitors.items():
            status[monitor] = 'READY' if value else 'NOT_READY'
        
        return {'monitors': status}
    
    def _parse_freeze_frame(self, data: bytes) -> Dict[str, Any]:
        """Parse freeze frame data"""
        if len(data) < 10:
            return {'error': 'Invalid freeze frame data'}
        
        frame = {
            'dtc': f"{data[3]:02X}{data[4]:02X}",  # DTC code
            'priority': data[5],  # DTC priority
            'occurrence_count': data[6],  # How many times DTC occurred
        }
        
        # Parse parameter values (structure varies by DTC)
        if len(data) >= 14:
            frame.update({
                'engine_rpm': ((data[7] << 8) | data[8]) / 4,  # RPM
                'vehicle_speed': data[9],  # km/h
                'coolant_temp': data[10] - 40,  # °C
                'load_value': (data[11] * 100) / 255,  # %
            })
        
        return {'freeze_frame': frame}
    
    def _parse_component_test(self, data: bytes) -> Dict[str, Any]:
        """Parse component test results"""
        if len(data) < 4:
            return {'error': 'Invalid component test response'}
        
        test_result = data[3]  # Test result byte
        
        return {
            'test_status': 'PASS' if test_result == 0x00 else 'FAIL',
            'result_code': test_result,
            'components_tested': [
                'Fuel Pump',
                'Injectors', 
                'Ignition Coils',
                'Sensors'
            ]
        }
    
    def _parse_clear_adaptations(self, data: bytes) -> Dict[str, Any]:
        """Parse clear adaptations response"""
        return {
            'adaptations_cleared': True,
            'cleared_items': [
                'Fuel Trims',
                'Throttle Adaptation',
                'Knock Learning',
                'Transmission Adaptation'
            ]
        }
    
    def _parse_turbo_test(self, data: bytes) -> Dict[str, Any]:
        """Parse turbocharger system test results"""
        if len(data) < 8:
            return {'error': 'Invalid turbo test response'}
        
        # Parse turbo-specific parameters
        boost_pressure = struct.unpack('>H', data[3:5])[0] / 10.0  # PSI
        wastegate_position = data[5]  # %
        turbo_speed = struct.unpack('>H', data[6:8])[0]  # RPM
        
        return {
            'boost_pressure': boost_pressure,
            'wastegate_position': wastegate_position,
            'turbo_speed': turbo_speed,
            'test_status': 'PASS' if boost_pressure > 5.0 else 'FAIL'
        }
    
    def _parse_fuel_system_test(self, data: bytes) -> Dict[str, Any]:
        """Parse fuel system test results"""
        if len(data) < 10:
            return {'error': 'Invalid fuel system test response'}
        
        fuel_pressure = struct.unpack('>H', data[3:5])[0] / 10.0  # PSI
        injector_pulse = struct.unpack('>H', data[5:7])[0] / 1000.0  # ms
        fuel_flow = data[7]  # L/h
        system_status = data[8]  # Status byte
        
        return {
            'fuel_pressure': fuel_pressure,
            'injector_pulse': injector_pulse,
            'fuel_flow': fuel_flow,
            'system_status': 'NORMAL' if system_status == 0x00 else 'ABNORMAL',
            'test_status': 'PASS' if fuel_pressure > 40.0 else 'FAIL'
        }
    
    def _parse_ignition_test(self, data: bytes) -> Dict[str, Any]:
        """Parse ignition system test results"""
        if len(data) < 8:
            return {'error': 'Invalid ignition test response'}
        
        spark_voltage = struct.unpack('>H', data[3:5])[0] / 1000.0  # kV
        burn_time = data[5]  # ms
        misfire_count = data[6]  # Count
        system_status = data[7]  # Status byte
        
        return {
            'spark_voltage': spark_voltage,
            'burn_time': burn_time,
            'misfire_count': misfire_count,
            'system_status': 'NORMAL' if system_status == 0x00 else 'ABNORMAL',
            'test_status': 'PASS' if misfire_count == 0 else 'FAIL'
        }
    
    def perform_comprehensive_diagnostic(self) -> Dict[str, Any]:
        """
        Perform comprehensive vehicle diagnostic
        
        Returns:
            Dict containing all diagnostic results
        """
        self.logger.info("Starting comprehensive diagnostic")
        
        results = {
            'timestamp': time.time(),
            'tests': {},
            'overall_status': 'PASS'
        }
        
        # Execute all diagnostic routines
        for routine_name in self.services.keys():
            self.logger.info(f"Running diagnostic: {routine_name}")
            
            test_result = self.execute_diagnostic_routine(routine_name)
            results['tests'][routine_name] = test_result
            
            # Update overall status if any test fails
            if test_result.get('status') in ['FAILED', 'ERROR']:
                results['overall_status'] = 'FAIL'
            
            # Brief delay between tests
            time.sleep(0.5)
        
        self.logger.info(f"Comprehensive diagnostic completed: {results['overall_status']}")
        return results
    
    def read_adaptive_values(self) -> Dict[str, Any]:
        """
        Read current adaptive learning values
        
        Returns:
            Dict containing adaptive values
        """
        adaptive_data = {}
        
        try:
            # Read fuel trim adaptations
            response = self.ecu.send_request(0x22, 0x2100)  # Fuel trim learn values
            if response.success and len(response.data) >= 67:
                # Parse fuel trim data (simplified)
                adaptive_data['fuel_trim_learn'] = {
                    'status': 'AVAILABLE',
                    'data_size': len(response.data) - 3
                }
            
            # Read knock learning
            response = self.ecu.send_request(0x22, 0x2101)  # Knock learn values
            if response.success:
                adaptive_data['knock_learning'] = {
                    'status': 'AVAILABLE', 
                    'data_size': len(response.data) - 3
                }
            
            # Read throttle adaptation
            response = self.ecu.send_request(0x22, 0x2102)  # Throttle adaptation
            if response.success:
                adaptive_data['throttle_adaptation'] = {
                    'status': 'AVAILABLE',
                    'data_size': len(response.data) - 3
                }
            
        except Exception as e:
            self.logger.error(f"Failed to read adaptive values: {e}")
            adaptive_data['error'] = str(e)
        
        return adaptive_data
    
    def reset_adaptive_memory(self) -> bool:
        """
        Reset all adaptive learning memory
        
        Returns:
            bool: True if reset successful
        """
        try:
            # Clear fuel trims
            response = self.ecu.send_request(0x31, 0x04, b'\xFF')  # Clear fuel adaptations
            if not response.success:
                return False
            
            # Clear knock learning
            response = self.ecu.send_request(0x31, 0x05, b'\xFF')  # Clear knock learning
            if not response.success:
                return False
            
            # Clear throttle adaptation
            response = self.ecu.send_request(0x31, 0x06, b'\xFF')  # Clear throttle adaptation
            if not response.success:
                return False
            
            self.logger.info("All adaptive memory reset successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset adaptive memory: {e}")
            return False
    
    def monitor_live_parameters(self, duration: int = 30) -> List[Dict[str, Any]]:
        """
        Monitor live parameters for specified duration
        
        Args:
            duration: Monitoring duration in seconds
            
        Returns:
            List of parameter snapshots
        """
        self.logger.info(f"Starting live parameter monitoring for {duration} seconds")
        
        parameters = []
        start_time = time.time()
        
        # Parameters to monitor
        monitor_pids = [
            (0x0C, 'rpm'),
            (0x0D, 'speed'), 
            (0x11, 'throttle'),
            (0x05, 'coolant_temp'),
            (0x0F, 'intake_temp'),
            (0x223365, 'boost'),
            (0x223456, 'knock_correction')
        ]
        
        try:
            while time.time() - start_time < duration:
                snapshot = {
                    'timestamp': time.time(),
                    'parameters': {}
                }
                
                # Read all parameters
                for pid, name in monitor_pids:
                    value = self.ecu.read_live_data(pid)
                    if value is not None:
                        snapshot['parameters'][name] = value
                
                parameters.append(snapshot)
                
                # Wait before next reading
                time.sleep(0.1)  # 10 Hz sampling
                
        except Exception as e:
            self.logger.error(f"Live monitoring interrupted: {e}")
        
        self.logger.info(f"Live monitoring completed: {len(parameters)} samples collected")
        return parameters
    
    def get_diagnostic_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive diagnostic report
        
        Returns:
            Dict containing diagnostic report
        """
        report = {
            'generated_at': time.time(),
            'vehicle_info': self._get_vehicle_info(),
            'test_results': self.test_results,
            'adaptive_data': self.read_adaptive_values(),
            'recommendations': []
        }
        
        # Generate recommendations based on test results
        for test_name, result in self.test_results.items():
            if result.get('status') == 'FAILED':
                recommendation = self._generate_recommendation(test_name, result)
                if recommendation:
                    report['recommendations'].append(recommendation)
        
        return report
    
    def _get_vehicle_info(self) -> Dict[str, Any]:
        """Get basic vehicle information"""
        try:
            vin = self.ecu.read_vin()
            return {
                'vin': vin,
                'connected': True,
                'timestamp': time.time()
            }
        except:
            return {
                'vin': 'Unknown',
                'connected': False,
                'timestamp': time.time()
            }
    
    def _generate_recommendation(self, test_name: str, result: Dict[str, Any]) -> str:
        """Generate recommendation based on failed test"""
        recommendations = {
            'turbo_test': "Inspect turbocharger system for leaks or damage",
            'fuel_system_test': "Check fuel pressure and injector operation", 
            'ignition_system_test': "Inspect spark plugs and ignition coils",
            'system_readiness': "Complete drive cycle to set readiness monitors"
        }
        
        return recommendations.get(test_name, f"Investigate {test_name} failure")