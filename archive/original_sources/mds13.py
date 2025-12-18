#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OBD INTERFACE - Complete OBD-II Implementation
Standard OBD-II interface for Mazda vehicles
"""

import serial
import time
import logging
from typing import Dict, List, Any, Optional
from enum import IntEnum

logger = logging.getLogger(__name__)

class OBDProtocol(IntEnum):
    """OBD-II Protocols"""
    AUTO = 0
    ISO_9141_2 = 1
    ISO_14230_4_KWP = 2
    ISO_14230_4_KWP_FAST = 3
    ISO_15765_4_CAN_11B_500K = 4
    ISO_15765_4_CAN_29B_500K = 5
    ISO_15765_4_CAN_11B_250K = 6
    ISO_15765_4_CAN_29B_250K = 7
    SAE_J1850_PWM = 8
    SAE_J1850_VPW = 9

class MazdaOBDInterface:
    """
    Complete OBD-II Interface for Mazda Vehicles
    Provides standard OBD-II communication with Mazda-specific extensions
    """
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 38400, 
                 protocol: OBDProtocol = OBDProtocol.AUTO):
        self.port = port
        self.baudrate = baudrate
        self.protocol = protocol
        self.serial_conn = None
        self.is_connected = False
        self.vehicle_supported_pids = {}
        
    def connect(self) -> bool:
        """
        Connect to OBD-II interface
        
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Connecting to OBD-II interface: {self.port}")
            
            # Initialize serial connection
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            # Initialize OBD connection
            if not self._initialize_obd():
                logger.error("Failed to initialize OBD connection")
                self.serial_conn.close()
                self.serial_conn = None
                return False
            
            self.is_connected = True
            logger.info("Successfully connected to OBD-II interface")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OBD-II interface: {e}")
            self.is_connected = False
            return False
    
    def _initialize_obd(self) -> bool:
        """Initialize OBD connection"""
        try:
            # Reset the interface
            self._send_command("ATZ")
            time.sleep(2)
            
            # Echo off
            self._send_command("ATE0")
            
            # Headers on (for Mazda)
            self._send_command("ATH1")
            
            # Try to auto-detect protocol
            if self.protocol == OBDProtocol.AUTO:
                detected_protocol = self._auto_detect_protocol()
                if detected_protocol:
                    logger.info(f"Auto-detected protocol: {detected_protocol.name}")
                else:
                    logger.warning("Could not auto-detect protocol, using default")
                    self.protocol = OBDProtocol.ISO_15765_4_CAN_11B_500K
            else:
                # Set specific protocol
                protocol_cmd = f"ATSP{self.protocol}"
                response = self._send_command(protocol_cmd)
                if "OK" not in response:
                    logger.warning(f"Could not set protocol {self.protocol}, trying auto")
                    self.protocol = OBDProtocol.AUTO
                    return self._initialize_obd()
            
            # Test communication
            response = self._send_command("0100")
            if response and "NO DATA" not in response:
                # Parse supported PIDs
                self._update_supported_pids(response)
                return True
            else:
                logger.error("No response from vehicle")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing OBD: {e}")
            return False
    
    def _auto_detect_protocol(self) -> Optional[OBDProtocol]:
        """Auto-detect OBD protocol"""
        protocols_to_try = [
            OBDProtocol.ISO_15765_4_CAN_11B_500K,  # Most common for modern Mazdas
            OBDProtocol.ISO_14230_4_KWP,           # KWP2000 for older Mazdas
            OBDProtocol.ISO_9141_2,                # K-line for older vehicles
        ]
        
        for protocol in protocols_to_try:
            try:
                protocol_cmd = f"ATSP{protocol}"
                response = self._send_command(protocol_cmd)
                if "OK" in response:
                    # Test communication
                    test_response = self._send_command("0100")
                    if test_response and "NO DATA" not in test_response:
                        self.protocol = protocol
                        return protocol
            except:
                continue
        
        return None
    
    def disconnect(self):
        """Disconnect from OBD-II interface"""
        try:
            if self.serial_conn:
                self.serial_conn.close()
                self.serial_conn = None
            
            self.is_connected = False
            logger.info("Disconnected from OBD-II interface")
            
        except Exception as e:
            logger.error(f"Error disconnecting from OBD-II interface: {e}")
    
    def _send_command(self, command: str) -> str:
        """
        Send command to OBD interface and read response
        
        Args:
            command: OBD command to send
            
        Returns:
            Response string
        """
        try:
            if not self.serial_conn:
                logger.error("OBD interface not connected")
                return ""
            
            # Clear buffer
            self.serial_conn.reset_input_buffer()
            
            # Send command
            full_command = command + "\r"
            self.serial_conn.write(full_command.encode())
            
            # Read response
            response = ""
            start_time = time.time()
            
            while time.time() - start_time < 5:  # 5 second timeout
                if self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        response += line + " "
                    if ">" in line:  # Prompt indicates end of response
                        break
            
            logger.debug(f"OBD Command: {command} -> Response: {response}")
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error sending OBD command: {e}")
            return ""
    
    def read_pid(self, pid: str) -> Optional[Dict[str, Any]]:
        """
        Read OBD PID value
        
        Args:
            pid: PID to read (e.g., "010C" for RPM)
            
        Returns:
            PID data or None if failed
        """
        try:
            response = self._send_command(pid)
            if not response or "NO DATA" in response or "?" in response:
                return None
            
            # Parse response
            parsed_data = self._parse_pid_response(pid, response)
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error reading PID {pid}: {e}")
            return None
    
    def _parse_pid_response(self, pid: str, response: str) -> Dict[str, Any]:
        """Parse PID response"""
        result = {
            'pid': pid,
            'raw_response': response,
            'value': None,
            'units': 'Unknown'
        }
        
        try:
            # Extract hex data from response
            lines = response.split()
            for line in lines:
                if len(line) >= 4 and line[:2] in ['41', '7F']:  # Response identifier
                    data = line[2:]
                    
                    if pid == "010C":  # Engine RPM
                        if len(data) >= 4:
                            a = int(data[0:2], 16)
                            b = int(data[2:4], 16)
                            rpm = (a * 256 + b) / 4.0
                            result['value'] = rpm
                            result['units'] = 'RPM'
                    
                    elif pid == "010D":  # Vehicle Speed
                        if len(data) >= 2:
                            speed = int(data[0:2], 16)
                            result['value'] = speed
                            result['units'] = 'km/h'
                    
                    elif pid == "0105":  # Engine Coolant Temperature
                        if len(data) >= 2:
                            temp = int(data[0:2], 16) - 40
                            result['value'] = temp
                            result['units'] = '°C'
                    
                    elif pid == "010B":  # Intake Manifold Pressure
                        if len(data) >= 2:
                            pressure = int(data[0:2], 16)
                            result['value'] = pressure
                            result['units'] = 'kPa'
                    
                    elif pid == "0111":  # Throttle Position
                        if len(data) >= 2:
                            position = (int(data[0:2], 16) * 100) / 255.0
                            result['value'] = position
                            result['units'] = '%'
                    
                    elif pid == "0104":  # Calculated Engine Load
                        if len(data) >= 2:
                            load = (int(data[0:2], 16) * 100) / 255.0
                            result['value'] = load
                            result['units'] = '%'
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing PID response: {e}")
            result['error'] = str(e)
            return result
    
    def read_multiple_pids(self, pids: List[str]) -> Dict[str, Any]:
        """
        Read multiple PIDs
        
        Args:
            pids: List of PIDs to read
            
        Returns:
            Dictionary of PID values
        """
        results = {}
        
        for pid in pids:
            pid_data = self.read_pid(pid)
            if pid_data:
                results[pid] = pid_data
        
        return results
    
    def read_live_data(self, pids: List[str], duration: int = 30) -> Dict[str, Any]:
        """
        Read live data from multiple PIDs over time
        
        Args:
            pids: PIDs to monitor
            duration: Monitoring duration in seconds
            
        Returns:
            Live data results
        """
        logger.info(f"Reading live data for {duration} seconds")
        
        live_data = {
            'start_time': time.time(),
            'end_time': 0,
            'samples': [],
            'pid_config': pids,
            'statistics': {}
        }
        
        try:
            start_time = time.time()
            sample_count = 0
            
            while time.time() - start_time < duration:
                sample = {
                    'timestamp': time.time(),
                    'values': {}
                }
                
                # Read all PIDs
                for pid in pids:
                    pid_data = self.read_pid(pid)
                    if pid_data and pid_data.get('value') is not None:
                        sample['values'][pid] = pid_data['value']
                
                live_data['samples'].append(sample)
                sample_count += 1
                
                # Wait before next sample
                time.sleep(0.5)  # 2 samples per second
            
            live_data['end_time'] = time.time()
            live_data['sample_count'] = sample_count
            
            # Calculate statistics
            live_data['statistics'] = self._calculate_live_data_statistics(live_data['samples'])
            
            logger.info(f"Live data collection completed: {sample_count} samples")
            return live_data
            
        except Exception as e:
            logger.error(f"Error reading live data: {e}")
            live_data['error'] = str(e)
            return live_data
    
    def _calculate_live_data_statistics(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics from live data samples"""
        statistics = {}
        
        if not samples:
            return statistics
        
        # Get all PIDs from first sample
        first_sample = samples[0]
        pids = list(first_sample['values'].keys())
        
        for pid in pids:
            values = [sample['values'].get(pid) for sample in samples]
            valid_values = [v for v in values if v is not None]
            
            if valid_values:
                statistics[pid] = {
                    'min': min(valid_values),
                    'max': max(valid_values),
                    'avg': sum(valid_values) / len(valid_values),
                    'samples': len(valid_values)
                }
        
        return statistics
    
    def read_diagnostic_trouble_codes(self) -> Optional[Dict[str, Any]]:
        """
        Read diagnostic trouble codes
        
        Returns:
            DTC information or None if failed
        """
        try:
            # Read stored DTCs
            response = self._send_command("03")
            if not response or "NO DATA" in response:
                return None
            
            dtc_info = {
                'dtc_count': 0,
                'dtc_list': [],
                'raw_response': response
            }
            
            # Parse DTC response
            lines = response.split()
            for line in lines:
                if len(line) >= 6 and line[:2] in ['43', '7F']:  # Response identifier
                    data = line[2:]
                    
                    # Parse DTCs (each DTC is 2 bytes)
                    for i in range(0, len(data), 4):
                        if i + 4 <= len(data):
                            dtc_bytes = data[i:i+4]
                            dtc_code = self._parse_dtc_code(dtc_bytes)
                            if dtc_code:
                                dtc_info['dtc_list'].append(dtc_code)
            
            dtc_info['dtc_count'] = len(dtc_info['dtc_list'])
            return dtc_info
            
        except Exception as e:
            logger.error(f"Error reading DTCs: {e}")
            return None
    
    def _parse_dtc_code(self, dtc_bytes: str) -> Optional[str]:
        """Parse DTC code from hex bytes"""
        try:
            if len(dtc_bytes) != 4:
                return None
            
            first_byte = int(dtc_bytes[0:2], 16)
            
            # Determine DTC type
            dtc_type = (first_byte >> 6) & 0x03
            type_chars = ['P', 'C', 'B', 'U']
            dtc_char = type_chars[dtc_type]
            
            # Extract digits
            digit1 = (first_byte >> 4) & 0x03
            digit2 = first_byte & 0x0F
            digit3 = int(dtc_bytes[2:3], 16)
            digit4 = int(dtc_bytes[3:4], 16)
            digit5 = int(dtc_bytes[4:5], 16) if len(dtc_bytes) > 4 else 0
            
            return f"{dtc_char}{digit1}{digit2}{digit3}{digit4}"
            
        except:
            return None
    
    def clear_diagnostic_trouble_codes(self) -> bool:
        """
        Clear diagnostic trouble codes
        
        Returns:
            True if codes cleared successfully
        """
        try:
            response = self._send_command("04")
            if "OK" in response or "NO DATA" in response:
                logger.info("Diagnostic trouble codes cleared")
                return True
            else:
                logger.error("Failed to clear DTCs")
                return False
                
        except Exception as e:
            logger.error(f"Error clearing DTCs: {e}")
            return False
    
    def read_vehicle_information(self) -> Dict[str, Any]:
        """
        Read vehicle information
        
        Returns:
            Vehicle information
        """
        vehicle_info = {}
        
        try:
            # Read VIN
            vin_response = self._send_command("0902")
            if vin_response and "NO DATA" not in vin_response:
                # Parse VIN from response
                lines = vin_response.split()
                for line in lines:
                    if len(line) >= 18 and line[:2] in ['49', '7F']:
                        data = line[2:]
                        # VIN is typically in the first 17 bytes of data
                        if len(data) >= 34:  # 17 bytes * 2 hex chars per byte
                            vin_hex = data[2:36]  # Skip first byte (usually 01)
                            try:
                                vin = bytes.fromhex(vin_hex).decode('ascii', errors='ignore')
                                vehicle_info['vin'] = vin.strip()
                            except:
                                pass
            
            # Read calibration ID
            cal_response = self._send_command("0904")
            if cal_response and "NO DATA" not in cal_response:
                # Parse calibration ID
                lines = cal_response.split()
                for line in lines:
                    if len(line) >= 6 and line[:2] in ['49', '7F']:
                        data = line[6:]  # Skip first 2 bytes
                        try:
                            cal_id = bytes.fromhex(data).decode('ascii', errors='ignore')
                            vehicle_info['calibration_id'] = cal_id.strip()
                        except:
                            pass
            
            return vehicle_info
            
        except Exception as e:
            logger.error(f"Error reading vehicle information: {e}")
            vehicle_info['error'] = str(e)
            return vehicle_info
    
    def _update_supported_pids(self, response: str):
        """Update list of supported PIDs"""
        try:
            lines = response.split()
            for line in lines:
                if len(line) >= 10 and line[:2] in ['41', '7F']:
                    data = line[2:]
                    
                    # Parse supported PIDs from bitmask
                    if len(data) >= 8:
                        # First 4 bytes indicate supported PIDs 01-20, 21-40, etc.
                        for i in range(0, min(8, len(data)), 2):
                            byte_val = int(data[i:i+2], 16)
                            for bit in range(8):
                                if byte_val & (1 << (7 - bit)):
                                    pid_num = (i//2) * 0x20 + bit + 1
                                    pid_hex = f"01{pid_num:02X}"
                                    self.vehicle_supported_pids[pid_hex] = True
            
            logger.debug(f"Supported PIDs: {list(self.vehicle_supported_pids.keys())}")
            
        except Exception as e:
            logger.error(f"Error updating supported PIDs: {e}")
    
    def get_supported_pids(self) -> List[str]:
        """
        Get list of supported PIDs
        
        Returns:
            List of supported PID codes
        """
        return list(self.vehicle_supported_pids.keys())
    
    def perform_obd_health_check(self) -> Dict[str, Any]:
        """
        Perform OBD system health check
        
        Returns:
            Health check results
        """
        health_status = {
            'connection_ok': self.is_connected,
            'protocol': self.protocol.name if self.protocol else 'Unknown',
            'supported_pids': len(self.vehicle_supported_pids),
            'communication_test': 'Unknown',
            'monitor_status': 'Unknown',
            'recommendations': []
        }
        
        try:
            # Test basic communication
            test_response = self._send_command("0100")
            if test_response and "NO DATA" not in test_response:
                health_status['communication_test'] = 'PASS'
            else:
                health_status['communication_test'] = 'FAIL'
                health_status['recommendations'].append("Check OBD connection and protocol")
            
            # Read monitor status
            monitor_response = self._send_command("0101")
            if monitor_response and "NO DATA" not in monitor_response:
                health_status['monitor_status'] = 'AVAILABLE'
                
                # Parse monitor status
                lines = monitor_response.split()
                for line in lines:
                    if len(line) >= 10 and line[:2] in ['41', '7F']:
                        data = line[2:]
                        if len(data) >= 4:
                            # Check if monitors are complete
                            status_byte = int(data[0:2], 16)
                            if status_byte & 0x80:  # MIL status
                                health_status['mil_status'] = 'ON'
                                health_status['recommendations'].append("Check engine light is on")
                            else:
                                health_status['mil_status'] = 'OFF'
            else:
                health_status['monitor_status'] = 'UNAVAILABLE'
            
            # Check for supported PIDs
            if health_status['supported_pids'] == 0:
                health_status['recommendations'].append("No supported PIDs detected - check protocol")
            elif health_status['supported_pids'] < 10:
                health_status['recommendations'].append("Limited PID support - vehicle may have restrictions")
            else:
                health_status['recommendations'].append("Good PID support detected")
            
            logger.info("OBD health check completed")
            return health_status
            
        except Exception as e:
            logger.error(f"Error performing OBD health check: {e}")
            health_status['error'] = str(e)
            return health_status