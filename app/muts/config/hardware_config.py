#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3_HARDWARE_CONFIG.py
HARDWARE CONFIGURATION AND DEVICE MANAGEMENT
"""

import serial
import can
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class DeviceType(Enum):
    """Device types for VersaTuner"""
    J2534 = "j2534"
    OBD2_USB = "obd2_usb"
    CAN_INTERFACE = "can_interface"
    SERIAL_ADAPTER = "serial_adapter"
    BLUETOOTH = "bluetooth"
    WIFI = "wifi"

@dataclass
class DeviceConfig:
    """Device configuration structure"""
    name: str
    device_type: DeviceType
    port: str
    baudrate: int
    protocol: str
    parameters: Dict[str, Any]
    connected: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['device_type'] = self.device_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DeviceConfig':
        """Create from dictionary"""
        data = data.copy()
        data['device_type'] = DeviceType(data['device_type'])
        return cls(**data)

class HardwareConfig:
    """
    HARDWARE CONFIGURATION MANAGER
    Manages all hardware devices and interfaces
    """
    
    def __init__(self):
        self.devices = {}
        self.active_device = None
        self.logger = logging.getLogger('HardwareConfig')
        
        # Default device configurations
        self.default_configs = {
            'j2534_drew_tech': DeviceConfig(
                name='Drew Technologies J2534',
                device_type=DeviceType.J2534,
                port='COM1',
                baudrate=115200,
                protocol='ISO15765-4 (CAN 11/500)',
                parameters={
                    'protocol_id': 6,
                    'baud_rate': 500000,
                    'connector': 'OBDII'
                }
            ),
            'obd2_usb_cable': DeviceConfig(
                name='OBD2 USB Cable',
                device_type=DeviceType.OBD2_USB,
                port='/dev/ttyUSB0',
                baudrate=38400,
                protocol='ISO9141-2',
                parameters={
                    'init_string': 'ATZ',
                    'echo_off': 'ATE0',
                    'headers_on': 'ATH1'
                }
            ),
            'can_usb': DeviceConfig(
                name='CAN USB Interface',
                device_type=DeviceType.CAN_INTERFACE,
                port='can0',
                baudrate=500000,
                protocol='CAN',
                parameters={
                    'bustype': 'socketcan',
                    'bitrate': 500000,
                    'receive_own_messages': False
                }
            )
        }
        
        # Load saved configurations
        self.load_configurations()
    
    def add_device(self, device: DeviceConfig) -> bool:
        """Add a new device configuration"""
        try:
            if device.name in self.devices:
                self.logger.warning(f"Device {device.name} already exists")
                return False
            
            self.devices[device.name] = device
            self.save_configurations()
            self.logger.info(f"Added device: {device.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add device: {e}")
            return False
    
    def remove_device(self, name: str) -> bool:
        """Remove a device configuration"""
        try:
            if name not in self.devices:
                self.logger.error(f"Device {name} not found")
                return False
            
            # Disconnect if active
            if self.active_device and self.active_device.name == name:
                self.disconnect_device()
            
            del self.devices[name]
            self.save_configurations()
            self.logger.info(f"Removed device: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove device: {e}")
            return False
    
    def update_device(self, name: str, updates: Dict) -> bool:
        """Update device configuration"""
        try:
            if name not in self.devices:
                self.logger.error(f"Device {name} not found")
                return False
            
            device = self.devices[name]
            
            # Update allowed fields
            allowed_fields = ['port', 'baudrate', 'protocol', 'parameters']
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(device, field, value)
            
            self.save_configurations()
            self.logger.info(f"Updated device: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update device: {e}")
            return False
    
    def connect_device(self, name: str) -> bool:
        """Connect to a device"""
        try:
            if name not in self.devices:
                self.logger.error(f"Device {name} not found")
                return False
            
            device = self.devices[name]
            
            if device.device_type == DeviceType.J2534:
                success = self._connect_j2534(device)
            elif device.device_type == DeviceType.OBD2_USB:
                success = self._connect_obd2_usb(device)
            elif device.device_type == DeviceType.CAN_INTERFACE:
                success = self._connect_can_interface(device)
            else:
                self.logger.error(f"Unsupported device type: {device.device_type}")
                return False
            
            if success:
                device.connected = True
                self.active_device = device
                self.logger.info(f"Connected to device: {name}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect device: {e}")
        
        return False
    
    def disconnect_device(self) -> bool:
        """Disconnect active device"""
        try:
            if not self.active_device:
                return True
            
            device = self.active_device
            
            if device.device_type == DeviceType.J2534:
                self._disconnect_j2534(device)
            elif device.device_type == DeviceType.OBD2_USB:
                self._disconnect_obd2_usb(device)
            elif device.device_type == DeviceType.CAN_INTERFACE:
                self._disconnect_can_interface(device)
            
            device.connected = False
            self.active_device = None
            self.logger.info("Device disconnected")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disconnect device: {e}")
            return False
    
    def _connect_j2534(self, device: DeviceConfig) -> bool:
        """Connect to J2534 device"""
        try:
            # This would use the actual J2534 API
            # For now, simulate connection
            self.logger.info(f"Connecting to J2534 device on {device.port}")
            return True
        except Exception as e:
            self.logger.error(f"J2534 connection failed: {e}")
            return False
    
    def _disconnect_j2534(self, device: DeviceConfig):
        """Disconnect from J2534 device"""
        try:
            # This would use the actual J2534 API
            self.logger.info("Disconnecting from J2534 device")
        except Exception as e:
            self.logger.error(f"J2534 disconnection failed: {e}")
    
    def _connect_obd2_usb(self, device: DeviceConfig) -> bool:
        """Connect to OBD2 USB device"""
        try:
            self.serial_conn = serial.Serial(
                port=device.port,
                baudrate=device.baudrate,
                timeout=5
            )
            
            # Send initialization commands
            if 'init_string' in device.parameters:
                self.serial_conn.write(f"{device.parameters['init_string']}\r".encode())
            
            if 'echo_off' in device.parameters:
                self.serial_conn.write(f"{device.parameters['echo_off']}\r".encode())
            
            if 'headers_on' in device.parameters:
                self.serial_conn.write(f"{device.parameters['headers_on']}\r".encode())
            
            return True
            
        except Exception as e:
            self.logger.error(f"OBD2 USB connection failed: {e}")
            return False
    
    def _disconnect_obd2_usb(self, device: DeviceConfig):
        """Disconnect from OBD2 USB device"""
        try:
            if hasattr(self, 'serial_conn') and self.serial_conn:
                self.serial_conn.close()
        except Exception as e:
            self.logger.error(f"OBD2 USB disconnection failed: {e}")
    
    def _connect_can_interface(self, device: DeviceConfig) -> bool:
        """Connect to CAN interface"""
        try:
            self.can_bus = can.interface.Bus(
                channel=device.port,
                bustype=device.parameters.get('bustype', 'socketcan'),
                bitrate=device.parameters.get('bitrate', 500000),
                receive_own_messages=device.parameters.get('receive_own_messages', False)
            )
            return True
            
        except Exception as e:
            self.logger.error(f"CAN interface connection failed: {e}")
            return False
    
    def _disconnect_can_interface(self, device: DeviceConfig):
        """Disconnect from CAN interface"""
        try:
            if hasattr(self, 'can_bus') and self.can_bus:
                self.can_bus.shutdown()
        except Exception as e:
            self.logger.error(f"CAN interface disconnection failed: {e}")
    
    def scan_for_devices(self) -> List[Dict]:
        """Scan for available devices"""
        found_devices = []
        
        # Scan serial ports
        import serial.tools.list_ports
        
        ports = serial.tools.list_ports.comports()
        for port in ports:
            device_info = {
                'port': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'type': 'serial'
            }
            found_devices.append(device_info)
        
        # Scan CAN interfaces
        try:
            can_interfaces = can.detect_available_configs()
            for interface in can_interfaces:
                if 'interface' in interface:
                    device_info = {
                        'port': interface.get('channel', 'unknown'),
                        'description': interface.get('interface', 'unknown'),
                        'hwid': str(interface),
                        'type': 'can'
                    }
                    found_devices.append(device_info)
        except:
            pass
        
        return found_devices
    
    def get_device_list(self) -> List[Dict]:
        """Get list of all configured devices"""
        return [device.to_dict() for device in self.devices.values()]
    
    def get_active_device(self) -> Optional[Dict]:
        """Get active device information"""
        if self.active_device:
            return self.active_device.to_dict()
        return None
    
    def test_device(self, name: str) -> Dict:
        """Test device connection"""
        result = {
            'success': False,
            'message': '',
            'response_time': 0
        }
        
        try:
            import time
            start_time = time.time()
            
            if self.connect_device(name):
                # Send test command
                if self.active_device.device_type == DeviceType.OBD2_USB:
                    if hasattr(self, 'serial_conn'):
                        self.serial_conn.write('ATI\r'.encode())
                        response = self.serial_conn.read_all().decode()
                        if 'ELM' in response:
                            result['success'] = True
                            result['message'] = 'Device responded to test command'
                
                elif self.active_device.device_type == DeviceType.CAN_INTERFACE:
                    if hasattr(self, 'can_bus'):
                        # Try to send a test message
                        test_msg = can.Message(
                            arbitration_id=0x7DF,
                            data=[0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
                        )
                        self.can_bus.send(test_msg)
                        result['success'] = True
                        result['message'] = 'CAN test message sent successfully'
                
                result['response_time'] = (time.time() - start_time) * 1000
                self.disconnect_device()
            
        except Exception as e:
            result['message'] = str(e)
        
        return result
    
    def save_configurations(self):
        """Save device configurations to file"""
        try:
            config_data = {
                'devices': [device.to_dict() for device in self.devices.values()]
            }
            
            with open('hardware_config.json', 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save configurations: {e}")
    
    def load_configurations(self):
        """Load device configurations from file"""
        try:
            with open('hardware_config.json', 'r') as f:
                config_data = json.load(f)
            
            for device_data in config_data.get('devices', []):
                device = DeviceConfig.from_dict(device_data)
                self.devices[device.name] = device
                
        except FileNotFoundError:
            # Use default configurations
            self.devices = {name: device for name, device in self.default_configs.items()}
        except Exception as e:
            self.logger.error(f"Failed to load configurations: {e}")
            self.devices = {name: device for name, device in self.default_configs.items()}

# Device manager instance
hardware_manager = HardwareConfig()

# Utility functions
def get_supported_protocols() -> Dict[str, str]:
    """Get list of supported protocols"""
    return {
        'ISO9141-2': 'ISO 9141-2 (K-Line)',
        'ISO14230-4': 'ISO 14230-4 (KWP2000)',
        'ISO15765-4': 'ISO 15765-4 (CAN)',
        'SAE J1850 PWM': 'SAE J1850 PWM',
        'SAE J1850 VPW': 'SAE J1850 VPW',
        'ISO8711-3': 'ISO 8711-3 (J1708)',
    }

def get_baud_rates() -> List[int]:
    """Get list of supported baud rates"""
    return [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

def validate_device_config(config: Dict) -> List[str]:
    """Validate device configuration"""
    errors = []
    
    required_fields = ['name', 'device_type', 'port', 'baudrate', 'protocol']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    if 'device_type' in config:
        try:
            DeviceType(config['device_type'])
        except ValueError:
            errors.append(f"Invalid device type: {config['device_type']}")
    
    if 'baudrate' in config:
        if config['baudrate'] not in get_baud_rates():
            errors.append(f"Invalid baud rate: {config['baudrate']}")
    
    return errors

# Demonstration
def demonstrate_hardware_config():
    """DEMONSTRATE HARDWARE CONFIGURATION"""
    print("MAZDASPEED 3 HARDWARE CONFIGURATION DEMONSTRATION")
    print("=" * 50)
    
    # Create hardware manager
    manager = HardwareConfig()
    
    # Show available devices
    print("\nConfigured devices:")
    for device in manager.get_device_list():
        status = "Connected" if device['connected'] else "Disconnected"
        print(f"  - {device['name']} ({device['device_type']}) - {status}")
    
    # Scan for devices
    print("\nScanning for devices...")
    found = manager.scan_for_devices()
    for device in found:
        print(f"  Found: {device['description']} at {device['port']}")
    
    # Test device
    if manager.devices:
        device_name = list(manager.devices.keys())[0]
        print(f"\nTesting device: {device_name}")
        result = manager.test_device(device_name)
        print(f"  Result: {'Success' if result['success'] else 'Failed'}")
        print(f"  Message: {result['message']}")
        print(f"  Response time: {result['response_time']:.1f}ms")
    
    print("\nHardware configuration demonstration complete!")

if __name__ == "__main__":
    demonstrate_hardware_config()
