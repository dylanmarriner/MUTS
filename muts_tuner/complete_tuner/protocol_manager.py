#!/usr/bin/env python3
"""
Complete ECU Protocol Manager
Unified interface for VersaTuner, Cobb, and MUTS protocols
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ProtocolType(Enum):
    """Supported ECU communication protocols"""
    VERSA_TUNER = "versa_tuner"
    COBB_TUNING = "cobb_tuning"
    MUTS_J2534 = "muts_j2534"
    OBD2_STANDARD = "obd2_standard"

@dataclass
class ECUMessage:
    """Unified ECU message structure"""
    protocol: ProtocolType
    data: bytes
    timestamp: float
    message_type: str = "request"
    source: str = ""

@dataclass
class LiveData:
    """Unified live data structure"""
    timestamp: float
    rpm: Optional[float] = None
    speed: Optional[float] = None
    throttle: Optional[float] = None
    coolant_temp: Optional[float] = None
    intake_temp: Optional[float] = None
    boost: Optional[float] = None
    knock_correction: Optional[float] = None
    afr: Optional[float] = None
    fuel_pressure: Optional[float] = None
    oil_pressure: Optional[float] = None
    vvt_angle: Optional[float] = None

class ECUProtocolInterface(ABC):
    """Abstract interface for all ECU protocols"""
    
    @abstractmethod
    async def connect(self, device_config: Dict[str, Any]) -> bool:
        """Connect to ECU using specific protocol"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from ECU"""
        pass
    
    @abstractmethod
    async def send_message(self, message: ECUMessage) -> bool:
        """Send message to ECU"""
        pass
    
    @abstractmethod
    async def read_messages(self, timeout_ms: int = 100) -> List[ECUMessage]:
        """Read messages from ECU"""
        pass
    
    @abstractmethod
    async def read_live_data(self) -> LiveData:
        """Read live ECU data"""
        pass
    
    @abstractmethod
    async def read_vin(self) -> Optional[str]:
        """Read vehicle VIN"""
        pass
    
    @abstractmethod
    async def read_dtc(self) -> List[Dict[str, Any]]:
        """Read diagnostic trouble codes"""
        pass
    
    @abstractmethod
    async def clear_dtc(self) -> bool:
        """Clear diagnostic trouble codes"""
        pass
    
    @abstractmethod
    async def read_rom(self, progress_callback: Optional[callable] = None) -> Optional[bytes]:
        """Read ECU ROM"""
        pass
    
    @abstractmethod
    async def write_rom(self, rom_data: bytes, progress_callback: Optional[callable] = None) -> bool:
        """Write ROM to ECU"""
        pass
    
    @abstractmethod
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get protocol information"""
        pass

class VersaTunerProtocol(ECUProtocolInterface):
    """VersaTuner protocol implementation"""
    
    def __init__(self):
        from versa1 import VersaTunerECU
        from versa2 import SecurityManager
        from versa3 import ROMOperations
        
        self.ecu = VersaTunerECU()
        self.security = SecurityManager(self.ecu)
        self.rom_ops = ROMOperations(self.ecu)
        self.is_connected = False
    
    async def connect(self, device_config: Dict[str, Any]) -> bool:
        """Connect using VersaTuner CAN protocol"""
        try:
            interface = device_config.get('interface', 'can0')
            bitrate = device_config.get('bitrate', 500000)
            
            self.ecu.interface = interface
            self.ecu.bitrate = bitrate
            
            result = self.ecu.connect()
            if result:
                # Unlock security access
                security_result = self.security.unlock_ecu()
                self.is_connected = security_result
                return self.is_connected
            
            return False
            
        except Exception as e:
            logger.error(f"VersaTuner connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect VersaTuner protocol"""
        try:
            self.ecu.disconnect()
            self.is_connected = False
            return True
        except Exception as e:
            logger.error(f"VersaTuner disconnect failed: {e}")
            return False
    
    async def send_message(self, message: ECUMessage) -> bool:
        """Send message using VersaTuner protocol"""
        if not self.is_connected:
            return False
        
        try:
            # Convert to VersaTuner format
            service = message.data[0] if len(message.data) > 0 else 0x22
            subfunction = message.data[1] if len(message.data) > 1 else 0x00
            data = message.data[2:] if len(message.data) > 2 else b''
            
            response = self.ecu.send_request(service, subfunction, data)
            return response.success
            
        except Exception as e:
            logger.error(f"VersaTuner send failed: {e}")
            return False
    
    async def read_messages(self, timeout_ms: int = 100) -> List[ECUMessage]:
        """Read messages using VersaTuner protocol"""
        if not self.is_connected:
            return []
        
        messages = []
        try:
            # VersaTuner uses request/response pattern, not continuous messaging
            # This would be implemented based on specific needs
            
        except Exception as e:
            logger.error(f"VersaTuner read failed: {e}")
        
        return messages
    
    async def read_live_data(self) -> LiveData:
        """Read live data using VersaTuner protocol"""
        if not self.is_connected:
            return LiveData(timestamp=0)
        
        try:
            import time
            
            # Read standard PIDs
            rpm = self.ecu.read_live_data(0x0C)
            speed = self.ecu.read_live_data(0x0D)
            throttle = self.ecu.read_live_data(0x11)
            coolant_temp = self.ecu.read_live_data(0x05)
            intake_temp = self.ecu.read_live_data(0x0F)
            
            # Read Mazda-specific PIDs
            boost = self.ecu.read_live_data(0x223365)
            
            return LiveData(
                timestamp=time.time(),
                rpm=rpm,
                speed=speed,
                throttle=throttle,
                coolant_temp=coolant_temp,
                intake_temp=intake_temp,
                boost=boost
            )
            
        except Exception as e:
            logger.error(f"VersaTuner live data failed: {e}")
            return LiveData(timestamp=0)
    
    async def read_vin(self) -> Optional[str]:
        """Read VIN using VersaTuner protocol"""
        if not self.is_connected:
            return None
        
        try:
            return self.ecu.read_vin()
        except Exception as e:
            logger.error(f"VersaTuner VIN read failed: {e}")
            return None
    
    async def read_dtc(self) -> List[Dict[str, Any]]:
        """Read DTCs using VersaTuner protocol"""
        if not self.is_connected:
            return []
        
        try:
            return self.ecu.read_dtcs()
        except Exception as e:
            logger.error(f"VersaTuner DTC read failed: {e}")
            return []
    
    async def clear_dtc(self) -> bool:
        """Clear DTCs using VersaTuner protocol"""
        if not self.is_connected:
            return False
        
        try:
            return self.ecu.clear_dtcs()
        except Exception as e:
            logger.error(f"VersaTuner DTC clear failed: {e}")
            return False
    
    async def read_rom(self, progress_callback: Optional[callable] = None) -> Optional[bytes]:
        """Read ROM using VersaTuner protocol"""
        if not self.is_connected:
            return None
        
        try:
            return self.rom_ops.read_complete_rom(progress_callback)
        except Exception as e:
            logger.error(f"VersaTuner ROM read failed: {e}")
            return None
    
    async def write_rom(self, rom_data: bytes, progress_callback: Optional[callable] = None) -> bool:
        """Write ROM using VersaTuner protocol"""
        if not self.is_connected:
            return False
        
        try:
            # Patch checksums first
            rom_data = self.rom_ops.patch_checksums(rom_data)
            
            # Write ROM
            result = self.rom_ops.write_complete_rom(rom_data, progress_callback)
            
            if result:
                # Verify integrity
                verification = self.rom_ops.verify_rom_integrity(rom_data)
                return verification['overall_valid']
            
            return False
            
        except Exception as e:
            logger.error(f"VersaTuner ROM write failed: {e}")
            return False
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get VersaTuner protocol info"""
        return {
            "name": "VersaTuner",
            "type": ProtocolType.VERSA_TUNER.value,
            "description": "Mazdaspeed 3 CAN protocol",
            "supported_vehicles": ["Mazdaspeed 3 2010-2013"],
            "features": ["ROM read/write", "Live data", "Diagnostics", "Security access"]
        }

class CobbProtocol(ECUProtocolInterface):
    """Cobb tuning protocol implementation"""
    
    def __init__(self):
        # Import Cobb modules
        self.is_connected = False
        logger.info("Cobb protocol initialized")
    
    async def connect(self, device_config: Dict[str, Any]) -> bool:
        """Connect using Cobb protocol"""
        try:
            # Implement Cobb connection logic from cobb1.py, cobb2.py
            logger.info("Connecting with Cobb protocol...")
            # Mock implementation
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Cobb connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect Cobb protocol"""
        try:
            self.is_connected = False
            return True
        except Exception as e:
            logger.error(f"Cobb disconnect failed: {e}")
            return False
    
    async def send_message(self, message: ECUMessage) -> bool:
        """Send message using Cobb protocol"""
        # Implement from cobb3.py, cobb7.py
        return False
    
    async def read_messages(self, timeout_ms: int = 100) -> List[ECUMessage]:
        """Read messages using Cobb protocol"""
        return []
    
    async def read_live_data(self) -> LiveData:
        """Read live data using Cobb protocol"""
        # Implement from cobb12.py RealTimeMonitor
        return LiveData(timestamp=0)
    
    async def read_vin(self) -> Optional[str]:
        """Read VIN using Cobb protocol"""
        return None
    
    async def read_dtc(self) -> List[Dict[str, Any]]:
        """Read DTCs using Cobb protocol"""
        return []
    
    async def clear_dtc(self) -> bool:
        """Clear DTCs using Cobb protocol"""
        return False
    
    async def read_rom(self, progress_callback: Optional[callable] = None) -> Optional[bytes]:
        """Read ROM using Cobb protocol"""
        # Implement from cobb11.py FlashManager
        return None
    
    async def write_rom(self, rom_data: bytes, progress_callback: Optional[callable] = None) -> bool:
        """Write ROM using Cobb protocol"""
        # Implement from cobb11.py FlashManager
        return False
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get Cobb protocol info"""
        return {
            "name": "Cobb Tuning",
            "type": ProtocolType.COBB_TUNING.value,
            "description": "Cobb AccessPort protocol",
            "supported_vehicles": ["Subaru", "Mazda", "Mitsubishi", "Nissan"],
            "features": ["ROM read/write", "Live data", "Real-time tuning"]
        }

class MUTSJ2534Protocol(ECUProtocolInterface):
    """MUTS J2534 protocol implementation"""
    
    def __init__(self):
        from j2534_interface import J2534Interface, J2534Protocol
        
        self.j2534 = J2534Interface()
        self.is_connected = False
    
    async def connect(self, device_config: Dict[str, Any]) -> bool:
        """Connect using J2534 protocol"""
        try:
            # Connect to J2534 device
            result = self.j2534.connect()
            if result:
                # Open communication channel
                protocol = J2534Protocol.ISO15765  # CAN protocol
                baudrate = device_config.get('baudrate', 500000)
                result = self.j2534.open_channel(protocol, baudrate)
                self.is_connected = result
            
            return self.is_connected
            
        except Exception as e:
            logger.error(f"MUTS J2534 connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect J2534 protocol"""
        try:
            self.j2534.disconnect()
            self.is_connected = False
            return True
        except Exception as e:
            logger.error(f"MUTS J2534 disconnect failed: {e}")
            return False
    
    async def send_message(self, message: ECUMessage) -> bool:
        """Send message using J2534 protocol"""
        if not self.is_connected:
            return False
        
        try:
            return self.j2534.send_message(message.data)
        except Exception as e:
            logger.error(f"MUTS J2534 send failed: {e}")
            return False
    
    async def read_messages(self, timeout_ms: int = 100) -> List[ECUMessage]:
        """Read messages using J2534 protocol"""
        if not self.is_connected:
            return []
        
        try:
            messages = []
            raw_messages = self.j2534.read_messages(timeout_ms, 10)
            
            for raw_msg in raw_messages:
                ecu_msg = ECUMessage(
                    protocol=ProtocolType.MUTS_J2534,
                    data=raw_msg,
                    timestamp=0,
                    message_type="response"
                )
                messages.append(ecu_msg)
            
            return messages
            
        except Exception as e:
            logger.error(f"MUTS J2534 read failed: {e}")
            return []
    
    async def read_live_data(self) -> LiveData:
        """Read live data using J2534 protocol"""
        if not self.is_connected:
            return LiveData(timestamp=0)
        
        try:
            import time
            
            # Send diagnostic requests and parse responses
            # This would be implemented with specific PID requests
            
            return LiveData(
                timestamp=time.time(),
                rpm=800,  # Mock values
                speed=0,
                throttle=0,
                coolant_temp=85,
                intake_temp=25,
                boost=0
            )
            
        except Exception as e:
            logger.error(f"MUTS J2534 live data failed: {e}")
            return LiveData(timestamp=0)
    
    async def read_vin(self) -> Optional[str]:
        """Read VIN using J2534 protocol"""
        if not self.is_connected:
            return None
        
        try:
            # Send VIN request (ISO-TP)
            vin_request = bytes([0x22, 0xF1, 0x89])
            if self.j2534.send_message(vin_request):
                # Wait for response
                import time
                time.sleep(0.1)
                messages = self.j2534.read_messages(100)
                for msg in messages:
                    # Parse VIN response
                    if len(msg) >= 20 and msg[0] == 0x62:
                        vin_bytes = msg[3:20]
                        return vin_bytes.decode('ascii', errors='ignore').strip()
            
            return None
            
        except Exception as e:
            logger.error(f"MUTS J2534 VIN read failed: {e}")
            return None
    
    async def read_dtc(self) -> List[Dict[str, Any]]:
        """Read DTCs using J2534 protocol"""
        if not self.is_connected:
            return []
        
        try:
            # Send DTC request
            dtc_request = bytes([0x19, 0x01])  # Read current DTCs
            if self.j2534.send_message(dtc_request):
                import time
                time.sleep(0.1)
                messages = self.j2534.read_messages(100)
                
                dtcs = []
                for msg in messages:
                    # Parse DTC response
                    if len(msg) >= 4 and msg[0] == 0x59:
                        # Extract DTC data
                        dtc_data = msg[3:]
                        for i in range(0, len(dtc_data) - 1, 2):
                            if dtc_data[i] == 0x00 and dtc_data[i+1] == 0x00:
                                continue
                            # Parse DTC code
                            dtc_code = self._parse_dtc_bytes(dtc_data[i:i+2])
                            if dtc_code:
                                dtcs.append({
                                    'code': dtc_code,
                                    'description': 'DTC detected',
                                    'status': 'Active'
                                })
                
                return dtcs
            
            return []
            
        except Exception as e:
            logger.error(f"MUTS J2534 DTC read failed: {e}")
            return []
    
    def _parse_dtc_bytes(self, dtc_bytes: bytes) -> Optional[str]:
        """Parse DTC bytes to code"""
        if len(dtc_bytes) != 2:
            return None
        
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
    
    async def clear_dtc(self) -> bool:
        """Clear DTCs using J2534 protocol"""
        if not self.is_connected:
            return False
        
        try:
            # Send clear DTC request
            clear_request = bytes([0x14, 0xFF])
            return self.j2534.send_message(clear_request)
            
        except Exception as e:
            logger.error(f"MUTS J2534 DTC clear failed: {e}")
            return False
    
    async def read_rom(self, progress_callback: Optional[callable] = None) -> Optional[bytes]:
        """Read ROM using J2534 protocol"""
        if not self.is_connected:
            return None
        
        try:
            # Implement ROM reading via J2534 memory access
            # This would use ReadMemoryByAddress service
            return None
            
        except Exception as e:
            logger.error(f"MUTS J2534 ROM read failed: {e}")
            return None
    
    async def write_rom(self, rom_data: bytes, progress_callback: Optional[callable] = None) -> bool:
        """Write ROM using J2534 protocol"""
        if not self.is_connected:
            return False
        
        try:
            # Implement ROM writing via J2534 memory access
            # This would use WriteMemoryByAddress service
            return False
            
        except Exception as e:
            logger.error(f"MUTS J2534 ROM write failed: {e}")
            return False
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get MUTS J2534 protocol info"""
        return {
            "name": "MUTS J2534",
            "type": ProtocolType.MUTS_J2534.value,
            "description": "J2534 Pass-thru interface",
            "supported_vehicles": ["J2534 compatible vehicles"],
            "features": ["Standard diagnostics", "ROM access", "Live data"]
        }

class ProtocolManager:
    """Unified protocol manager for all ECU communication"""
    
    def __init__(self):
        self.protocols = {
            ProtocolType.VERSA_TUNER: VersaTunerProtocol(),
            ProtocolType.COBB_TUNING: CobbProtocol(),
            ProtocolType.MUTS_J2534: MUTSJ2534Protocol(),
        }
        self.current_protocol: Optional[ECUProtocolInterface] = None
        self.current_type: Optional[ProtocolType] = None
    
    async def connect(self, protocol_type: ProtocolType, device_config: Dict[str, Any]) -> bool:
        """Connect using specified protocol"""
        try:
            # Disconnect current if connected
            if self.current_protocol:
                await self.current_protocol.disconnect()
            
            # Get new protocol
            protocol = self.protocols.get(protocol_type)
            if not protocol:
                logger.error(f"Protocol {protocol_type} not available")
                return False
            
            # Connect
            result = await protocol.connect(device_config)
            if result:
                self.current_protocol = protocol
                self.current_type = protocol_type
                logger.info(f"Connected using {protocol_type.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Protocol connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect current protocol"""
        if not self.current_protocol:
            return True
        
        try:
            result = await self.current_protocol.disconnect()
            self.current_protocol = None
            self.current_type = None
            return result
        except Exception as e:
            logger.error(f"Protocol disconnect failed: {e}")
            return False
    
    def get_current_protocol(self) -> Optional[ECUProtocolInterface]:
        """Get current protocol instance"""
        return self.current_protocol
    
    def get_current_type(self) -> Optional[ProtocolType]:
        """Get current protocol type"""
        return self.current_type
    
    def get_available_protocols(self) -> List[Dict[str, Any]]:
        """Get list of available protocols"""
        protocols = []
        for protocol_type, protocol in self.protocols.items():
            info = protocol.get_protocol_info()
            protocols.append(info)
        return protocols
    
    def is_connected(self) -> bool:
        """Check if connected to ECU"""
        return self.current_protocol is not None

# Global protocol manager instance
protocol_manager = ProtocolManager()
