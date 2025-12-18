"""
OBD-II Protocol Implementation for Mazdaspeed 3
Provides standard OBD-II functionality alongside Cobb-specific features
"""

import struct
import time
from typing import Dict, List, Optional

class OBD2Protocol:
    """
    OBD-II protocol implementation with Mazdaspeed 3 extensions
    Supports standard PIDs and Mazda-specific proprietary PIDs
    """
    
    # Standard OBD-II PIDs
    STANDARD_PIDS = {
        0x00: "PIDs supported [01-20]",
        0x04: "Calculated engine load",
        0x05: "Engine coolant temperature",
        0x0C: "Engine RPM",
        0x0D: "Vehicle speed",
        0x0F: "Intake air temperature",
        0x11: "Throttle position",
        0x1C: "OBD standards this vehicle conforms to",
        0x21: "Distance traveled with MIL on"
    }
    
    # Mazda proprietary PIDs
    MAZDA_PIDS = {
        0x01: "Boost pressure (actual)",
        0x02: "Boost pressure (target)",
        0x03: "Wastegate duty cycle",
        0x04: "VVT intake actual",
        0x05: "VVT intake target",
        0x06: "VVT exhaust actual",
        0x07: "VVT exhaust target",
        0x08: "Knock retard cylinder 1",
        0x09: "Knock retard cylinder 2",
        0x0A: "Knock retard cylinder 3",
        0x0B: "Knock retard cylinder 4",
        0x0C: "Fuel final base",
        0x0D: "Fuel final correction",
        0x0E: "Ignition base timing",
        0x0F: "Ignition correction",
        0x10: "MAF voltage",
        0x11: "MAF g/s",
        0x12: "Injector pulse width",
        0x13: "Fuel pump duty cycle",
        0x14: "EGT bank 1",
        0x15: "EGT bank 2"
    }
    
    def __init__(self, can_protocol):
        self.can = can_protocol
        self.connected = False
        
    def connect_obd(self) -> bool:
        """Initialize OBD-II connection"""
        # Send OBD initialization sequence
        init_sequence = [
            bytes([0x81, 0x13, 0xF1, 0x81]),  # Start communication
            bytes([0x10, 0x03]),  # Set protocol
        ]
        
        for cmd in init_sequence:
            self.can.send_can_message(0x7E0, cmd)
            time.sleep(0.1)
            
        response = self.can.receive_can_message(1.0)
        self.connected = response is not None
        return self.connected
    
    def read_pid(self, pid: int, mode: int = 0x01) -> Optional[float]:
        """
        Read OBD-II PID value
        mode 0x01 = Show current data
        mode 0x22 = Read data by identifier (proprietary)
        """
        if mode == 0x01 and pid not in self.STANDARD_PIDS:
            return None
        if mode == 0x22 and pid not in self.MAZDA_PIDS:
            return None
            
        # Build OBD request
        if mode == 0x01:
            request = bytes([mode, pid])
        else:
            request = bytes([mode, pid >> 8, pid & 0xFF])
            
        self.can.send_can_message(0x7E0, request)
        response = self.can.receive_can_message(1.0)
        
        if response and len(response.data) >= 4:
            return self._parse_pid_response(pid, mode, response.data)
            
        return None
    
    def _parse_pid_response(self, pid: int, mode: int, data: bytes) -> float:
        """Parse OBD response data into engineering units"""
        if mode == 0x01:
            # Standard PID parsing
            if pid == 0x04:  # Engine load
                return data[3] * 100 / 255
            elif pid == 0x05:  # Coolant temp
                return data[3] - 40
            elif pid == 0x0C:  # Engine RPM
                return ((data[3] * 256) + data[4]) / 4
            elif pid == 0x0D:  # Vehicle speed
                return data[3]
            elif pid == 0x0F:  # Intake air temp
                return data[3] - 40
            elif pid == 0x11:  # Throttle position
                return data[3] * 100 / 255
                
        elif mode == 0x22:
            # Mazda proprietary PID parsing
            if pid in [0x01, 0x02]:  # Boost pressure
                return (struct.unpack('>H', data[3:5])[0] * 0.01) - 1
            elif pid == 0x03:  # Wastegate duty
                return data[3] * 0.5
            elif pid in [0x04, 0x05, 0x06, 0x07]:  # VVT
                return data[3] * 0.5
            elif pid in range(0x08, 0x0C):  # Knock retard
                return data[3] * 0.1
            elif pid in [0x0C, 0x0D]:  # Fuel
                return struct.unpack('>H', data[3:5])[0] * 0.001
            elif pid in [0x0E, 0x0F]:  # Ignition
                return (data[3] * 0.1) - 64
            elif pid == 0x10:  # MAF voltage
                return data[3] * 0.01
            elif pid == 0x11:  # MAF g/s
                return struct.unpack('>H', data[3:5])[0] * 0.01
            elif pid == 0x12:  # Injector pulse
                return struct.unpack('>H', data[3:5])[0] * 0.001
            elif pid == 0x13:  # Fuel pump duty
                return data[3] * 0.5
            elif pid in [0x14, 0x15]:  # EGT
                return struct.unpack('>H', data[3:5])[0] * 0.1
                
        return 0.0
    
    def read_dtc(self) -> List[str]:
        """Read Diagnostic Trouble Codes"""
        dtc_cmd = bytes([0x03])  # Read DTCs
        self.can.send_can_message(0x7E0, dtc_cmd)
        response = self.can.receive_can_message(2.0)
        
        dtcs = []
        if response and len(response.data) >= 4:
            # Parse DTC response (simplified)
            num_dtcs = response.data[1]
            for i in range(num_dtcs):
                if i * 2 + 2 < len(response.data):
                    dtc_byte1 = response.data[i * 2 + 2]
                    dtc_byte2 = response.data[i * 2 + 3]
                    dtc = self._parse_dtc_bytes(dtc_byte1, dtc_byte2)
                    if dtc:
                        dtcs.append(dtc)
                        
        return dtcs
    
    def _parse_dtc_bytes(self, byte1: int, byte2: int) -> str:
        """Parse DTC from two-byte format to string format"""
        # Extract DTC components
        first_char = (byte1 >> 6) & 0x03
        second_char = (byte1 >> 4) & 0x03
        code1 = byte1 & 0x0F
        code2 = (byte2 >> 4) & 0x0F
        code3 = byte2 & 0x0F
        
        # Convert to DTC string
        chars = ['P', 'C', 'B', 'U']
        dtc_str = f"{chars[first_char]}{second_char:01X}{code1:01X}{code2:01X}{code3:01X}"
        return dtc_str
    
    def clear_dtc(self) -> bool:
        """Clear Diagnostic Trouble Codes"""
        clear_cmd = bytes([0x04])  # Clear DTCs
        self.can.send_can_message(0x7E0, clear_cmd)
        response = self.can.receive_can_message(2.0)
        
        return response is not None and response.data[0] == 0x44
    
    def read_all_realtime_data(self) -> Dict[str, float]:
        """Read all available real-time data"""
        data = {}
        
        # Read standard PIDs
        for pid in [0x04, 0x05, 0x0C, 0x0D, 0x0F, 0x11]:
            value = self.read_pid(pid, 0x01)
            if value is not None:
                data[self.STANDARD_PIDS[pid]] = value
                
        # Read Mazda proprietary PIDs
        for pid in range(0x01, 0x16):
            value = self.read_pid(pid, 0x22)
            if value is not None:
                data[self.MAZDA_PIDS[pid]] = value
                
        return data
