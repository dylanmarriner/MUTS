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

class VehicleSpecific:
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
                self._send_command(f"ATSP {self.protocol.value}")
            
            # Get supported PIDs
            self._get_supported_pids()
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing OBD: {e}")
            return False
    
    def _auto_detect_protocol(self) -> Optional[OBDProtocol]:
        """Auto-detect OBD protocol"""
        try:
            # Send protocol detection command
            response = self._send_command("ATDP")
            if response:
                protocol_num = int(response.strip())
                return OBDProtocol(protocol_num)
            
            return None
            
        except Exception as e:
            logger.error(f"Error auto-detecting protocol: {e}")
            return None
    
    def _get_supported_pids(self):
        """Get supported PIDs from vehicle"""
        try:
            # Query PID 1-20 support
            response = self._send_command("0100")
            if response and len(response) > 4:
                # Parse PID support bitmap
                pid_bytes = bytes.fromhex(response[4:])
                if len(pid_bytes) >= 4:
                    # PID 1-8 support
                    self.vehicle_supported_pids[1] = pid_bytes[2]
                    # PID 9-20 support
                    self.vehicle_supported_pids[9] = pid_bytes[3]
            
            # Query PID 21-40 support
            response = self._send_command("0120")
            if response and len(response) > 4:
                pid_bytes = bytes.fromhex(response[4:])
                if len(pid_bytes) >= 4:
                    self.vehicle_supported_pids[21] = pid_bytes[2]
                    self.vehicle_supported_pids[29] = pid_bytes[3]
                    
        except Exception as e:
            logger.error(f"Error getting supported PIDs: {e}")
    
    def disconnect(self):
        """Disconnect from OBD interface"""
        try:
            if self.serial_conn:
                self.serial_conn.close()
                self.serial_conn = None
            
            self.is_connected = False
            logger.info("Disconnected from OBD-II interface")
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
    
    def _send_command(self, command: str) -> Optional[str]:
        """Send command to OBD interface"""
        try:
            if not self.serial_conn:
                return None
            
            # Clear buffer
            self.serial_conn.reset_input_buffer()
            
            # Send command
            self.serial_conn.write((command + "\r").encode())
            
            # Read response
            response = b""
            start_time = time.time()
            
            while time.time() - start_time < 2.0:
                if self.serial_conn.in_waiting > 0:
                    byte = self.serial_conn.read(1)
                    response += byte
                    
                    # Check for end of response
                    if byte == b'>':
                        break
                else:
                    time.sleep(0.01)
            
            # Convert to string and clean up
            response_str = response.decode('ascii', errors='ignore')
            response_str = response_str.replace('\r', '').replace('>', '')
            
            # Filter out echo and empty lines
            lines = [line for line in response_str.split('\n') 
                    if line and not line.startswith(command)]
            
            return lines[-1] if lines else None
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
    
    def read_pid(self, pid: int) -> Optional[float]:
        """
        Read PID value
        
        Args:
            pid: PID to read
            
        Returns:
            PID value or None
        """
        try:
            # Check if PID is supported
            if not self._is_pid_supported(pid):
                logger.warning(f"PID {pid:02X} not supported by vehicle")
                return None
            
            # Send PID request
            command = f"01{pid:02X}"
            response = self._send_command(command)
            
            if not response:
                return None
            
            # Parse response
            return self._parse_pid_response(pid, response)
            
        except Exception as e:
            logger.error(f"Error reading PID {pid:02X}: {e}")
            return None
    
    def _is_pid_supported(self, pid: int) -> bool:
        """Check if PID is supported"""
        # Find the PID range
        for start_pid, support_byte in self.vehicle_supported_pids.items():
            if start_pid <= pid < start_pid + 8:
                bit_position = pid - start_pid
                return (support_byte >> (7 - bit_position)) & 1
        
        # Default to supported if we don't have info
        return True
    
    def _parse_pid_response(self, pid: int, response: str) -> Optional[float]:
        """Parse PID response"""
        try:
            # Remove response header
            if len(response) >= 4 and response[:2] == "41":
                data_bytes = bytes.fromhex(response[4:])
                
                # Convert based on PID
                if pid == 0x0C:  # Engine RPM
                    if len(data_bytes) >= 2:
                        value = (data_bytes[0] << 8) | data_bytes[1]
                        return value / 4.0
                        
                elif pid == 0x0D:  # Vehicle Speed
                    if len(data_bytes) >= 1:
                        return data_bytes[0]
                        
                elif pid == 0x11:  # Throttle Position
                    if len(data_bytes) >= 1:
                        return data_bytes[0] * 100 / 255
                        
                elif pid == 0x04:  # Engine Load
                    if len(data_bytes) >= 1:
                        return data_bytes[0] * 100 / 255
                        
                elif pid == 0x05:  # Coolant Temperature
                    if len(data_bytes) >= 1:
                        return data_bytes[0] - 40
                        
                elif pid == 0x0F:  # Intake Air Temperature
                    if len(data_bytes) >= 1:
                        return data_bytes[0] - 40
                        
                elif pid == 0x10:  # MAF Flow
                    if len(data_bytes) >= 2:
                        value = (data_bytes[0] << 8) | data_bytes[1]
                        return value / 100
                        
                elif pid == 0x0B:  # MAP Pressure
                    if len(data_bytes) >= 1:
                        return data_bytes[0]
                        
                elif pid == 0x0A:  # Fuel Pressure
                    if len(data_bytes) >= 1:
                        return data_bytes[0] * 3
                        
                elif pid == 0x0E:  # Timing Advance
                    if len(data_bytes) >= 1:
                        return data_bytes[0] / 2 - 64
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing PID response: {e}")
            return None
    
    def read_mazda_specific_pid(self, pid: int) -> Optional[float]:
        """
        Read Mazda-specific PID
        
        Args:
            pid: Mazda-specific PID
            
        Returns:
            PID value or None
        """
        try:
            # Mazda-specific PIDs use mode 22
            command = f"22{pid:04X}"
            response = self._send_command(command)
            
            if not response:
                return None
            
            # Parse response
            if len(response) >= 6 and response[:2] == "62":
                data_bytes = bytes.fromhex(response[6:])
                
                # Mazda-specific conversions
                if pid == 0xF190:  # VIN
                    return data_bytes.decode('ascii', errors='ignore')
                    
                elif pid == 0xF18C:  # ECU Part Number
                    return data_bytes.decode('ascii', errors='ignore')
                    
                elif pid == 0xF195:  # Software Version
                    return data_bytes.decode('ascii', errors='ignore')
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading Mazda PID {pid:04X}: {e}")
            return None
    
    def read_dtc(self) -> List[str]:
        """Read diagnostic trouble codes"""
        try:
            dtcs = []
            
            # Read stored DTCs
            response = self._send_command("03")
            if response:
                # Parse DTC response
                dtc_bytes = bytes.fromhex(response[2:])
                
                for i in range(0, len(dtc_bytes), 2):
                    if i + 1 < len(dtc_bytes):
                        dtc_code = self._parse_dtc(dtc_bytes[i:i+2])
                        if dtc_code:
                            dtcs.append(dtc_code)
            
            return dtcs
            
        except Exception as e:
            logger.error(f"Error reading DTCs: {e}")
            return []
    
    def _parse_dtc(self, dtc_bytes: bytes) -> str:
        """Parse DTC bytes"""
        if len(dtc_bytes) != 2:
            return ""
        
        first_byte = dtc_bytes[0]
        second_byte = dtc_bytes[1]
        
        # Extract DTC type
        dtc_type = (first_byte >> 6) & 0x03
        type_chars = ['P', 'C', 'B', 'U']
        dtc_char = type_chars[dtc_type]
        
        # Extract digits
        digit1 = (first_byte >> 4) & 0x03
        digit2 = first_byte & 0x0F
        digit3 = (second_byte >> 4) & 0x0F
        digit4 = second_byte & 0x0F
        
        return f"{dtc_char}{digit1}{digit2}{digit3}{digit4}"
    
    def clear_dtc(self) -> bool:
        """Clear diagnostic trouble codes"""
        try:
            response = self._send_command("04")
            return response is not None
            
        except Exception as e:
            logger.error(f"Error clearing DTCs: {e}")
            return False
    
    def get_vehicle_info(self) -> Dict[str, Any]:
        """Get vehicle information"""
        info = {}
        
        try:
            # Read VIN
            vin = self.read_mazda_specific_pid(0xF190)
            if vin:
                info['vin'] = vin
            
            # Read ECU part number
            part_num = self.read_mazda_specific_pid(0xF18C)
            if part_num:
                info['ecu_part_number'] = part_num
            
            # Read software version
            sw_version = self.read_mazda_specific_pid(0xF195)
            if sw_version:
                info['software_version'] = sw_version
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting vehicle info: {e}")
            return info
