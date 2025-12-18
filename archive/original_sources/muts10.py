import serial
import time
import logging
from threading import Lock
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class MazdaOBDService:
    """
    OBD-II service specifically tailored for Mazdaspeed 3 2011
    Implements Mazda-specific protocols and commands
    """
    
    # Mazda-specific PIDs
    MAZDA_SPECIFIC_PIDS = {
        'BOOST_PRESSURE': '223365',
        'VVT_ANGLE': '22345C',
        'KNOCK_CORRECTION': '223456',
        'INJECTOR_PULSE': '223467',
        'TURBO_WASTEGATE': '223478'
    }
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 38400):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.lock = Lock()
        self.is_connected = False
        
    def connect(self) -> bool:
        """Establish connection to vehicle ECU"""
        try:
            with self.lock:
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=5,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS
                )
                
                # Initialize OBD connection
                self._send_command('ATZ')  # Reset
                time.sleep(2)
                self._send_command('ATE0')  # Echo off
                self._send_command('ATH1')  # Headers on
                
                # Mazda specific initialization
                self._send_command('ATSP6')  # Protocol for Mazda
                
                self.is_connected = True
                logger.info(f"Connected to Mazda ECU on {self.port}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect to ECU: {e}")
            self.is_connected = False
            return False
    
    def _send_command(self, command: str) -> str:
        """Send command to ECU and return response"""
        if not self.serial_conn or not self.serial_conn.is_open:
            raise ConnectionError("Not connected to ECU")
        
        self.serial_conn.write(f"{command}\r".encode())
        time.sleep(0.1)
        response = self.serial_conn.read_all().decode().strip()
        return response
    
    def read_ecu_data(self) -> Dict:
        """
        Read comprehensive ECU data from Mazdaspeed 3
        Returns real-time engine parameters
        """
        data = {}
        
        try:
            # Standard OBD-II PIDs
            data['rpm'] = self._parse_response(self._send_command('010C'))
            data['speed'] = self._parse_response(self._send_command('010D'))
            data['throttle_position'] = self._parse_response(self._send_command('0111'))
            data['maf_flow'] = self._parse_response(self._send_command('0110'))
            data['coolant_temp'] = self._parse_response(self._send_command('0105'))
            data['intake_temp'] = self._parse_response(self._send_command('010F'))
            
            # Mazda-specific parameters
            data['boost_psi'] = self._read_boost_pressure()
            data['vvt_angle'] = self._read_vvt_angle()
            data['knock_correction'] = self._read_knock_correction()
            data['injector_pulse'] = self._read_injector_pulse()
            data['afr'] = self._calculate_afr(data['maf_flow'])
            
        except Exception as e:
            logger.error(f"Error reading ECU data: {e}")
            
        return data
    
    def _read_boost_pressure(self) -> float:
        """Read turbo boost pressure in PSI"""
        response = self._send_command(self.MAZDA_SPECIFIC_PIDS['BOOST_PRESSURE'])
        # Convert hex response to PSI value
        raw_value = self._parse_hex_response(response)
        return (raw_value - 100) / 10.0  # Convert to PSI
    
    def _read_vvt_angle(self) -> float:
        """Read Variable Valve Timing angle"""
        response = self._send_command(self.MAZDA_SPECIFIC_PIDS['VVT_ANGLE'])
        raw_value = self._parse_hex_response(response)
        return (raw_value - 128) / 2.0  # Convert to degrees
    
    def _read_knock_correction(self) -> float:
        """Read knock correction values"""
        response = self._send_command(self.MAZDA_SPECIFIC_PIDS['KNOCK_CORRECTION'])
        raw_value = self._parse_hex_response(response)
        return (raw_value - 128) / 2.0  # Convert to degrees
    
    def _read_injector_pulse(self) -> float:
        """Read fuel injector pulse width in ms"""
        response = self._send_command(self.MAZDA_SPECIFIC_PIDS['INJECTOR_PULSE'])
        raw_value = self._parse_hex_response(response)
        return raw_value / 1000.0  # Convert to milliseconds
    
    def _parse_response(self, response: str) -> float:
        """Parse standard OBD-II response"""
        try:
            lines = response.split('\r')
            for line in lines:
                if line.startswith('41'):
                    data = line[4:].replace(' ', '')
                    if len(data) >= 2:
                        return int(data[:2], 16)
        except:
            pass
        return 0.0
    
    def _parse_hex_response(self, response: str) -> int:
        """Parse hex response from Mazda-specific commands"""
        try:
            lines = response.split('\r')
            for line in lines:
                if line.startswith('62'):
                    data = line[2:].replace(' ', '')
                    return int(data, 16)
        except:
            pass
        return 0
    
    def _calculate_afr(self, maf_flow: float) -> float:
        """Calculate Air-Fuel Ratio from MAF flow"""
        if maf_flow <= 0:
            return 14.7
        # Simplified AFR calculation
        return min(max(10.5, 14.7 - (maf_flow / 50)), 16.0)
    
    def read_dtcs(self) -> List[Dict]:
        """Read Diagnostic Trouble Codes"""
        dtcs = []
        try:
            response = self._send_command('03')
            # Parse DTC response
            # Implementation for parsing multiple DTCs
            pass
        except Exception as e:
            logger.error(f"Error reading DTCs: {e}")
        return dtcs
    
    def clear_dtcs(self) -> bool:
        """Clear all Diagnostic Trouble Codes"""
        try:
            response = self._send_command('04')
            return 'OK' in response
        except Exception as e:
            logger.error(f"Error clearing DTCs: {e}")
            return False
    
    def disconnect(self):
        """Close connection to ECU"""
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            self.is_connected = False