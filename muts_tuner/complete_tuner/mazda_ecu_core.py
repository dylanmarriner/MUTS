#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDA ECU COMMUNICATION CORE
Local ECU communication using safe MDS components
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from enum import IntEnum
from dataclasses import dataclass

# Import safe MDS components with compatibility layer
import mds_compatibility
from mds6 import J2534Interface
from mds12 import MazdaCANInterface, CANFrame, CANFrameType
from mds13 import MazdaOBDInterface, OBDProtocol

# Use compatibility layer classes
J2534Error = mds_compatibility.J2534Error
J2534Protocol = mds_compatibility.J2534Protocol

logger = logging.getLogger(__name__)

class CommunicationMethod(IntEnum):
    """Communication Methods"""
    J2534_PASSTHRU = 1
    CAN_DIRECT = 2
    OBD_SERIAL = 3

@dataclass
class ECUConnection:
    """ECU Connection Configuration"""
    method: CommunicationMethod
    interface: str
    protocol: Union[J2534Protocol, OBDProtocol]
    baudrate: int
    connected: bool = False
    vehicle_info: Dict[str, Any] = None

class MazdaECUCore:
    """
    Core ECU Communication System
    Combines safe MDS communication methods
    """
    
    def __init__(self):
        self.j2534_interface = J2534Interface()
        self.can_interface = MazdaCANInterface()
        self.obd_interface = MazdaOBDInterface()
        
        self.current_connection = None
        self.supported_methods = [
            CommunicationMethod.J2534_PASSTHRU,
            CommunicationMethod.CAN_DIRECT,
            CommunicationMethod.OBD_SERIAL
        ]
        
        # Mazda-specific ECU addresses
        self.mazda_ecus = {
            'engine': {'tx': 0x7E0, 'rx': 0x7E8, 'name': 'Engine ECU'},
            'transmission': {'tx': 0x7E1, 'rx': 0x7E9, 'name': 'TCM'},
            'abs': {'tx': 0x7E2, 'rx': 0x7EA, 'name': 'ABS Module'},
            'bcm': {'tx': 0x7E6, 'rx': 0x7EE, 'name': 'Body Control'},
            'immobilizer': {'tx': 0x7E5, 'rx': 0x7ED, 'name': 'Immobilizer'}
        }
        
        logger.info("Mazda ECU Core initialized")
    
    def detect_available_interfaces(self) -> Dict[str, List[str]]:
        """
        Detect available communication interfaces
        
        Returns:
            Dictionary of available interfaces by method
        """
        available = {
            'j2534': [],
            'can': [],
            'obd': []
        }
        
        # Check J2534 devices
        try:
            # Try common J2534 DLL paths
            common_paths = [
                "C:\\Program Files\\Mazda\\IDS\\J2534PassThru.dll",
                "C:\\Program Files (x86)\\Mazda\\IDS\\J2534PassThru.dll",
                "C:\\Windows\\System32\\J2534PassThru.dll"
            ]
            
            for path in common_paths:
                try:
                    # Test if DLL can be loaded
                    import ctypes
                    ctypes.WinDLL(path)
                    available['j2534'].append(path)
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"J2534 detection error: {e}")
        
        # Check CAN interfaces
        try:
            import socket
            # Test if CAN socket is available
            test_socket = socket.socket(socket.AF_CAN, socket.SOCK_RAW)
            test_socket.close()
            available['can'].append('can0')
        except:
            pass
        
        # Check OBD interfaces
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if any(keyword in port.description.lower() for keyword in ['obd', 'elm', 'scan']):
                    available['obd'].append(port.device)
        except:
            pass
        
        logger.info(f"Available interfaces: {available}")
        return available
    
    def connect_to_vehicle(self, method: CommunicationMethod, 
                          interface: str, **kwargs) -> bool:
        """
        Connect to vehicle using specified method
        
        Args:
            method: Communication method to use
            interface: Interface identifier
            **kwargs: Additional connection parameters
            
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Connecting to vehicle using {method.name} on {interface}")
            
            if method == CommunicationMethod.J2534_PASSTHRU:
                return self._connect_j2534(interface, **kwargs)
            elif method == CommunicationMethod.CAN_DIRECT:
                return self._connect_can(interface, **kwargs)
            elif method == CommunicationMethod.OBD_SERIAL:
                return self._connect_obd(interface, **kwargs)
            else:
                logger.error(f"Unsupported communication method: {method}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to vehicle: {e}")
            return False
    
    def _connect_j2534(self, interface: str, protocol: J2534Protocol = J2534Protocol.ISO15765,
                      baudrate: int = 500000) -> bool:
        """Connect via J2534 Pass-Thru"""
        try:
            # Load J2534 library
            if not self.j2534_interface._load_j2534_library(interface):
                logger.error("Failed to load J2534 library")
                return False
            
            # Connect to device
            if not self.j2534_interface.connect():
                logger.error("Failed to connect J2534 device")
                return False
            
            # Connect to vehicle channel
            if not self.j2534_interface.connect_channel(protocol, baudrate):
                logger.error("Failed to connect vehicle channel")
                return False
            
            # Create connection object
            self.current_connection = ECUConnection(
                method=CommunicationMethod.J2534_PASSTHRU,
                interface=interface,
                protocol=protocol,
                baudrate=baudrate,
                connected=True
            )
            
            logger.info("J2534 connection established")
            return True
            
        except Exception as e:
            logger.error(f"J2534 connection error: {e}")
            return False
    
    def _connect_can(self, interface: str, bitrate: int = 500000) -> bool:
        """Connect via direct CAN interface"""
        try:
            self.can_interface.bitrate = bitrate
            
            if not self.can_interface.connect():
                logger.error("Failed to connect CAN interface")
                return False
            
            # Create connection object
            self.current_connection = ECUConnection(
                method=CommunicationMethod.CAN_DIRECT,
                interface=interface,
                protocol=OBDProtocol.ISO_15765_4_CAN_11B_500K,
                baudrate=bitrate,
                connected=True
            )
            
            logger.info("CAN connection established")
            return True
            
        except Exception as e:
            logger.error(f"CAN connection error: {e}")
            return False
    
    def _connect_obd(self, interface: str, baudrate: int = 38400,
                    protocol: OBDProtocol = OBDProtocol.AUTO) -> bool:
        """Connect via OBD-II serial interface"""
        try:
            self.obd_interface.port = interface
            self.obd_interface.baudrate = baudrate
            self.obd_interface.protocol = protocol
            
            if not self.obd_interface.connect():
                logger.error("Failed to connect OBD interface")
                return False
            
            # Create connection object
            self.current_connection = ECUConnection(
                method=CommunicationMethod.OBD_SERIAL,
                interface=interface,
                protocol=protocol,
                baudrate=baudrate,
                connected=True
            )
            
            logger.info("OBD connection established")
            return True
            
        except Exception as e:
            logger.error(f"OBD connection error: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from vehicle"""
        try:
            if not self.current_connection:
                logger.warning("No active connection to disconnect")
                return True
            
            method = self.current_connection.method
            
            if method == CommunicationMethod.J2534_PASSTHRU:
                self.j2534_interface.disconnect()
            elif method == CommunicationMethod.CAN_DIRECT:
                self.can_interface.disconnect()
            elif method == CommunicationMethod.OBD_SERIAL:
                self.obd_interface.disconnect()
            
            self.current_connection.connected = False
            self.current_connection = None
            
            logger.info("Disconnected from vehicle")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False
    
    def send_diagnostic_message(self, ecu_target: str, service_id: int, 
                              data: bytes = b'') -> Optional[bytes]:
        """
        Send diagnostic message to specific ECU
        
        Args:
            ecu_target: Target ECU ('engine', 'transmission', etc.)
            service_id: Diagnostic service ID
            data: Service data
            
        Returns:
            Response data or None if failed
        """
        try:
            if not self.current_connection or not self.current_connection.connected:
                logger.error("No active connection")
                return None
            
            if ecu_target not in self.mazda_ecus:
                logger.error(f"Unknown ECU target: {ecu_target}")
                return None
            
            ecu_info = self.mazda_ecus[ecu_target]
            target_address = ecu_info['tx']
            
            # Build diagnostic message
            message = bytearray()
            message.append(service_id)
            message.extend(data)
            
            # Send based on connection method
            if self.current_connection.method == CommunicationMethod.J2534_PASSTHRU:
                return self._send_j2534_diagnostic(target_address, bytes(message))
            elif self.current_connection.method == CommunicationMethod.CAN_DIRECT:
                return self._send_can_diagnostic(target_address, bytes(message))
            elif self.current_connection.method == CommunicationMethod.OBD_SERIAL:
                return self._send_obd_diagnostic(bytes(message))
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending diagnostic message: {e}")
            return None
    
    def _send_j2534_diagnostic(self, target_address: int, message: bytes) -> Optional[bytes]:
        """Send diagnostic via J2534"""
        try:
            # This would use the J2534 diagnostic protocol
            # For now, simulate the send/receive
            logger.debug(f"J2534 TX: 0x{target_address:03X} {message.hex().upper()}")
            
            # Simulate response
            time.sleep(0.05)
            response = bytearray([0x7F, message[0], 0x31])  # Service not supported
            
            return bytes(response)
            
        except Exception as e:
            logger.error(f"J2534 diagnostic error: {e}")
            return None
    
    def _send_can_diagnostic(self, target_address: int, message: bytes) -> Optional[bytes]:
        """Send diagnostic via CAN"""
        try:
            if not self.can_interface.send_diagnostic_message(target_address, message):
                logger.error("Failed to send CAN diagnostic message")
                return None
            
            # Wait for response
            response = self.can_interface.receive_diagnostic_message(target_address + 8, timeout=1.0)
            
            if response:
                logger.debug(f"CAN RX: 0x{target_address + 8:03X} {response.hex().upper()}")
            
            return response
            
        except Exception as e:
            logger.error(f"CAN diagnostic error: {e}")
            return None
    
    def _send_obd_diagnostic(self, message: bytes) -> Optional[bytes]:
        """Send diagnostic via OBD"""
        try:
            # Convert to OBD command format
            command = message.hex().upper()
            response = self.obd_interface._send_command(command)
            
            if response and "NO DATA" not in response:
                # Parse response
                lines = response.split()
                for line in lines:
                    if len(line) >= 4 and line[:2] in ['7F', str(hex(message[0])[2:].upper())]:
                        return bytes.fromhex(line[2:])
            
            return None
            
        except Exception as e:
            logger.error(f"OBD diagnostic error: {e}")
            return None
    
    def read_vehicle_identification(self) -> Optional[Dict[str, str]]:
        """Read vehicle identification information"""
        try:
            vehicle_info = {}
            
            # Read VIN (service 0x09, PID 0x02)
            vin_response = self.send_diagnostic_message('engine', 0x09, bytes([0x02]))
            if vin_response and len(vin_response) > 2:
                # Parse VIN from response
                vin_data = vin_response[2:]  # Skip service and PID
                if len(vin_data) >= 17:
                    vehicle_info['vin'] = vin_data[:17].decode('ascii', errors='ignore').strip()
            
            # Read calibration ID (service 0x09, PID 0x04)
            cal_response = self.send_diagnostic_message('engine', 0x09, bytes([0x04]))
            if cal_response and len(cal_response) > 2:
                cal_data = cal_response[2:]
                vehicle_info['calibration_id'] = cal_data.decode('ascii', errors='ignore').strip()
            
            return vehicle_info if vehicle_info else None
            
        except Exception as e:
            logger.error(f"Error reading vehicle identification: {e}")
            return None
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        status = {
            'connected': False,
            'method': None,
            'interface': None,
            'vehicle_detected': False,
            'vehicle_info': {}
        }
        
        if self.current_connection and self.current_connection.connected:
            status.update({
                'connected': True,
                'method': self.current_connection.method.name,
                'interface': self.current_connection.interface,
                'protocol': self.current_connection.protocol.name,
                'baudrate': self.current_connection.baudrate
            })
            
            # Try to read vehicle info
            if not self.current_connection.vehicle_info:
                self.current_connection.vehicle_info = self.read_vehicle_identification()
            
            if self.current_connection.vehicle_info:
                status['vehicle_detected'] = True
                status['vehicle_info'] = self.current_connection.vehicle_info
        
        return status
    
    def test_communication(self) -> Dict[str, bool]:
        """Test communication with all ECUs"""
        results = {}
        
        if not self.current_connection or not self.current_connection.connected:
            logger.error("No active connection for testing")
            return results
        
        for ecu_name, ecu_info in self.mazda_ecus.items():
            try:
                # Send simple test message (service 0x01 - current data)
                response = self.send_diagnostic_message(ecu_name, 0x01, bytes([0x00]))
                results[ecu_name] = response is not None
                
                if response:
                    logger.debug(f"{ecu_name} communication: OK")
                else:
                    logger.debug(f"{ecu_name} communication: No response")
                    
            except Exception as e:
                logger.error(f"Error testing {ecu_name} communication: {e}")
                results[ecu_name] = False
        
        return results
