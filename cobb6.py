from core.ecu_communication import ECUCommunicator, ECUResponse, ECUState
from core.safety_validator import get_safety_validator
from utils.logger import get_logger
"""
Hardware Interface Layer
Abstracts communication with physical/virtual Cobb AP hardware
"""

import serial
import socket
import select
import struct
from typing import Optional, Union

class HardwareInterface:
    """
    Unified hardware interface for Cobb AP communication
    Supports USB, Serial, and Ethernet connections
    """
    
    def __init__(self):
        self.connection = None
        self.interface_type = None
        self.timeout = 5.0
        
    def connect_usb(self, vendor_id: int = 0x16C0, product_id: int = 0x05DC) -> bool:
        """Connect to USB Cobb Access Port"""
        try:
            import usb.core
            import usb.backend.libusb1
            
            # Find Cobb AP device
            self.connection = usb.core.find(
                idVendor=vendor_id, 
                idProduct=product_id
            )
            
            if self.connection is None:
                # Try virtual device
                from .cobb_emulator import CobbAccessPortEmulator
                virtual_ap = CobbAccessPortEmulator()
                if virtual_ap.create_virtual_device():
                    self.connection = virtual_ap
                    self.interface_type = 'virtual'
                    return True
                return False
            
            # Configure real USB device
            self.connection.set_configuration()
            usb.util.claim_interface(self.connection, 0)
            self.interface_type = 'usb'
            return True
            
        except Exception as e:
            print(f"USB connection failed: {e}")
            return False
    
    def connect_serial(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200) -> bool:
        """Connect to serial interface (for bench flashing)"""
        try:
            self.connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            self.interface_type = 'serial'
            return self.connection.is_open
            
        except Exception as e:
            print(f"Serial connection failed: {e}")
            return False
    
    def connect_ethernet(self, host: str, port: int = 23) -> bool:
        """Connect to Ethernet interface (for network-enabled AP)"""
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.settimeout(self.timeout)
            self.connection.connect((host, port))
            self.interface_type = 'ethernet'
            return True
            
        except Exception as e:
            print(f"Ethernet connection failed: {e}")
            return False
    
    def send_command(self, command: bytes, expect_response: bool = True) -> Optional[bytes]:
        """Send command to connected hardware"""
        if not self.connection:
            return None
            
        try:
            if self.interface_type == 'usb':
                # USB bulk transfer
                written = self.connection.write(0x01, command, timeout=1000)
                if expect_response:
                    response = self.connection.read(0x81, 64, timeout=1000)
                    return bytes(response)
                    
            elif self.interface_type == 'virtual':
                # Virtual device message
                message_type = command[0] if command else 0
                return self.connection.send_usb_message(message_type, command[1:])
                
            elif self.interface_type == 'serial':
                # Serial write/read
                self.connection.write(command)
                if expect_response:
                    return self.connection.read(64)
                    
            elif self.interface_type == 'ethernet':
                # TCP send/receive
                self.connection.send(command)
                if expect_response:
                    return self.connection.recv(64)
                    
        except Exception as e:
            print(f"Send command failed: {e}")
            
        return None
    
    def identify_device(self) -> Optional[dict]:
        """Identify connected Cobb AP device"""
        identify_cmd = b'\x10'  # Identify command
        response = self.send_command(identify_cmd)
        
        if response and len(response) >= 34:
            # Parse identify response
            firmware = response[1:17].decode('ascii').strip('\x00')
            serial = response[17:33].decode('ascii').strip('\x00')
            state = response[33]
            
            return {
                'firmware': firmware,
                'serial': serial,
                'state': state,
                'interface': self.interface_type
            }
        
        return None
    
    def ecu_connect(self, protocol: int = 6, baudrate: int = 500000) -> bool:
        """Connect to ECU through hardware interface"""
        connect_cmd = struct.pack('<BBI', 0x11, protocol, baudrate)
        response = self.send_command(connect_cmd)
        
        return response and response[1] == 0x01
    
    def read_ecu_memory(self, address: int, length: int) -> Optional[bytes]:
        """Read ECU memory through hardware interface"""
        read_cmd = struct.pack('<BIB', 0x12, address, length)
        response = self.send_command(read_cmd)
        
        if response and response[0] == 0x92:
            return response[1:1+length]
            
        return None
    
    def write_ecu_memory(self, address: int, data: bytes) -> bool:
        """Write ECU memory through hardware interface"""
        write_cmd = struct.pack('<BI', 0x13, address) + data
        response = self.send_command(write_cmd)
        
        return response and response[1] == 0x01
    
    def disconnect(self):
        """Disconnect from hardware"""
        if self.connection:
            if self.interface_type == 'usb':
                usb.util.release_interface(self.connection, 0)
            elif self.interface_type == 'serial':
                self.connection.close()
            elif self.interface_type == 'ethernet':
                self.connection.close()
            elif self.interface_type == 'virtual':
                self.connection.disconnect()
                
        self.connection = None
        self.interface_type = None