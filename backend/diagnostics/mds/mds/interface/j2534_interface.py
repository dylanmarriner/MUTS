#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J2534 INTERFACE - Complete J2534 Pass-Thru Implementation
Reverse engineered from Mazda IDS/M-MDS J2534 interface
"""

import ctypes
import logging
import platform
from typing import Dict, List, Any, Optional, Tuple
from enum import IntEnum
from ctypes import wintypes, windll, WinDLL

logger = logging.getLogger(__name__)

class J2534Error(IntEnum):
    """J2534 Error Codes"""
    STATUS_NOERROR = 0x00
    ERR_NOT_SUPPORTED = 0x01
    ERR_INVALID_CHANNEL_ID = 0x02
    ERR_INVALID_PROTOCOL_ID = 0x03
    ERR_NULL_PARAMETER = 0x04
    ERR_INVALID_IOCTL_VALUE = 0x05
    ERR_INVALID_FLAGS = 0x06
    ERR_FAILED = 0x07
    ERR_DEVICE_NOT_CONNECTED = 0x08
    ERR_TIMEOUT = 0x09
    ERR_INVALID_MSG = 0x0A
    ERR_INVALID_TIME_INTERVAL = 0x0B
    ERR_EXCEEDED_LIMIT = 0x0C
    ERR_INVALID_MSG_ID = 0x0D
    ERR_DEVICE_IN_USE = 0x0E
    ERR_INVALID_IOCTL_ID = 0x0F
    ERR_BUFFER_EMPTY = 0x10
    ERR_BUFFER_FULL = 0x11
    ERR_BUFFER_OVERFLOW = 0x12
    ERR_PIN_INVALID = 0x13
    ERR_CHANNEL_IN_USE = 0x14
    ERR_MSG_PROTOCOL_ID = 0x15
    ERR_INVALID_FILTER_ID = 0x16
    ERR_NO_FLOW_CONTROL = 0x17
    ERR_NOT_UNIQUE = 0x18
    ERR_INVALID_BAUDRATE = 0x19
    ERR_INVALID_DEVICE_ID = 0x1A

class J2534Protocol(IntEnum):
    """J2534 Protocol IDs"""
    J1850VPW = 0x01
    J1850PWM = 0x02
    ISO9141 = 0x03
    ISO14230 = 0x04
    ISO15765 = 0x05
    SCI_A_ENGINE = 0x06
    SCI_A_TRANS = 0x07
    SCI_B_ENGINE = 0x08
    SCI_B_TRANS = 0x09
    CAN = 0x0A
    CAN_PS = 0x0B

class J2534Ioctl(IntEnum):
    """J2534 IOCTL IDs"""
    GET_CONFIG = 0x01
    SET_CONFIG = 0x02
    READ_VBATT = 0x03
    READ_PROG_VOLTAGE = 0x04
    FIVE_BAUD_INIT = 0x05
    FAST_INIT = 0x06
    CLEAR_TX_BUFFER = 0x07
    CLEAR_RX_BUFFER = 0x08
    CLEAR_PERIODIC_MSGS = 0x09
    CLEAR_MSG_FILTERS = 0x0A
    CLEAR_FUNCT_MSG_LOOKUP_TABLE = 0x0B
    ADD_TO_FUNCT_MSG_LOOKUP_TABLE = 0x0C
    DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE = 0x0D
    READ_PROG_VOLTAGE_2 = 0x0E

class J2534MessageFlag(IntEnum):
    """J2534 Message Flags"""
    TX_FLAG_NONE = 0x00
    TX_FLAG_SCI_TX_VOLTAGE = 0x0080
    TX_FLAG_SCI_MODE = 0x0100
    TX_FLAG_CAN_29BIT_ID = 0x0100

class J2534Interface:
    """
    Complete J2534 Pass-Thru Interface Implementation
    Provides low-level vehicle communication for Mazda diagnostics
    """
    
    def __init__(self, dll_path: Optional[str] = None):
        self.library = None
        self.device_id = None
        self.channel_id = None
        self.is_connected = False
        
        # Load J2534 library
        if not self._load_j2534_library(dll_path):
            logger.error("Failed to load J2534 library")
            return
        
        logger.info("J2534 interface initialized")
    
    def _load_j2534_library(self, dll_path: Optional[str]) -> bool:
        """Load J2534 DLL library"""
        try:
            if platform.system() == "Windows":
                if dll_path:
                    self.library = windll.LoadLibrary(dll_path)
                else:
                    # Try common J2534 DLL locations
                    common_paths = [
                        "C:\\Windows\\System32\\j2534.dll",
                        "C:\\Program Files\\J2534\\j2534.dll",
                        "C:\\Program Files (x86)\\J2534\\j2534.dll"
                    ]
                    
                    for path in common_paths:
                        try:
                            self.library = windll.LoadLibrary(path)
                            logger.info(f"Loaded J2534 library from: {path}")
                            break
                        except:
                            continue
                    
                    if not self.library:
                        logger.error("J2534 DLL not found")
                        return False
            else:
                logger.warning("J2534 interface only supported on Windows")
                return False
            
            # Set up function prototypes
            self._setup_function_prototypes()
            return True
            
        except Exception as e:
            logger.error(f"Error loading J2534 library: {e}")
            return False
    
    def _setup_function_prototypes(self):
        """Set up J2534 function prototypes"""
        # PassThruOpen
        self.library.PassThruOpen.argtypes = [wintypes.LPVOID, wintypes.LPDWORD]
        self.library.PassThruOpen.restype = wintypes.LONG
        
        # PassThruClose
        self.library.PassThruClose.argtypes = [wintypes.DWORD]
        self.library.PassThruClose.restype = wintypes.LONG
        
        # PassThruConnect
        self.library.PassThruConnect.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.LPDWORD]
        self.library.PassThruConnect.restype = wintypes.LONG
        
        # PassThruDisconnect
        self.library.PassThruDisconnect.argtypes = [wintypes.DWORD]
        self.library.PassThruDisconnect.restype = wintypes.LONG
        
        # PassThruReadMsg
        self.library.PassThruReadMsg.argtypes = [wintypes.DWORD, wintypes.LPVOID, wintypes.LPDWORD, wintypes.DWORD]
        self.library.PassThruReadMsg.restype = wintypes.LONG
        
        # PassThruWriteMsg
        self.library.PassThruWriteMsg.argtypes = [wintypes.DWORD, wintypes.LPVOID, wintypes.LPDWORD]
        self.library.PassThruWriteMsg.restype = wintypes.LONG
        
        # PassThruStartPeriodicMsg
        self.library.PassThruStartPeriodicMsg.argtypes = [wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD]
        self.library.PassThruStartPeriodicMsg.restype = wintypes.LONG
        
        # PassThruStopPeriodicMsg
        self.library.PassThruStopPeriodicMsg.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.library.PassThruStopPeriodicMsg.restype = wintypes.LONG
        
        # PassThruStartMsgFilter
        self.library.PassThruStartMsgFilter.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID, wintypes.LPVOID, wintypes.LPDWORD]
        self.library.PassThruStartMsgFilter.restype = wintypes.LONG
        
        # PassThruStopMsgFilter
        self.library.PassThruStopMsgFilter.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.library.PassThruStopMsgFilter.restype = wintypes.LONG
        
        # PassThruSetProgrammingVoltage
        self.library.PassThruSetProgrammingVoltage.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD]
        self.library.PassThruSetProgrammingVoltage.restype = wintypes.LONG
        
        # PassThruReadVersion
        self.library.PassThruReadVersion.argtypes = [wintypes.DWORD, wintypes.LPSTR, wintypes.LPSTR, wintypes.LPSTR]
        self.library.PassThruReadVersion.restype = wintypes.LONG
        
        # PassThruGetLastError
        self.library.PassThruGetLastError.argtypes = [wintypes.LPSTR]
        self.library.PassThruGetLastError.restype = wintypes.LONG
        
        # PassThruIoctl
        self.library.PassThruIoctl.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID]
        self.library.PassThruIoctl.restype = wintypes.LONG
    
    def pass_thru_open(self, device_id: Optional[int] = None) -> bool:
        """Open J2534 device"""
        try:
            if not self.library:
                logger.error("J2534 library not loaded")
                return False
            
            device_ptr = ctypes.c_void_p(device_id) if device_id else None
            device_id_out = wintypes.DWORD()
            
            result = self.library.PassThruOpen(device_ptr, ctypes.byref(device_id_out))
            
            if result == J2534Error.STATUS_NOERROR:
                self.device_id = device_id_out.value
                self.is_connected = True
                logger.info(f"J2534 device opened, ID: {self.device_id}")
                return True
            else:
                logger.error(f"Failed to open J2534 device: {self._get_error_string(result)}")
                return False
                
        except Exception as e:
            logger.error(f"Error opening J2534 device: {e}")
            return False
    
    def pass_thru_close(self) -> bool:
        """Close J2534 device"""
        try:
            if not self.library or not self.is_connected:
                return False
            
            result = self.library.PassThruClose(self.device_id)
            
            if result == J2534Error.STATUS_NOERROR:
                self.is_connected = False
                self.device_id = None
                logger.info("J2534 device closed")
                return True
            else:
                logger.error(f"Failed to close J2534 device: {self._get_error_string(result)}")
                return False
                
        except Exception as e:
            logger.error(f"Error closing J2534 device: {e}")
            return False
    
    def pass_thru_connect(self, protocol: J2534Protocol, flags: int = 0, baud_rate: int = 500000) -> bool:
        """Connect to vehicle protocol"""
        try:
            if not self.is_connected:
                logger.error("Device not connected")
                return False
            
            channel_id_out = wintypes.DWORD()
            
            result = self.library.PassThruConnect(
                self.device_id,
                protocol,
                flags,
                baud_rate,
                ctypes.byref(channel_id_out)
            )
            
            if result == J2534Error.STATUS_NOERROR:
                self.channel_id = channel_id_out.value
                logger.info(f"Connected to protocol {protocol.name}, channel ID: {self.channel_id}")
                return True
            else:
                logger.error(f"Failed to connect to protocol: {self._get_error_string(result)}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to protocol: {e}")
            return False
    
    def pass_thru_disconnect(self) -> bool:
        """Disconnect from protocol"""
        try:
            if not self.channel_id:
                return False
            
            result = self.library.PassThruDisconnect(self.channel_id)
            
            if result == J2534Error.STATUS_NOERROR:
                self.channel_id = None
                logger.info("Disconnected from protocol")
                return True
            else:
                logger.error(f"Failed to disconnect: {self._get_error_string(result)}")
                return False
                
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False
    
    def pass_thru_write_msg(self, messages: List[Dict[str, Any]]) -> bool:
        """Write messages to vehicle"""
        try:
            if not self.channel_id:
                logger.error("No channel connected")
                return False
            
            # Prepare message structures
            msg_array = (J2534_MESSAGE * len(messages))()
            num_msgs = wintypes.DWORD(len(messages))
            
            for i, msg in enumerate(messages):
                msg_array[i].ProtocolID = msg.get('protocol_id', J2534Protocol.ISO15765)
                msg_array[i].DataSize = len(msg.get('data', b''))
                msg_array[i].Data = (ctypes.c_ubyte * len(msg.get('data', b'')))(*msg.get('data', b''))
                msg_array[i].TxFlags = msg.get('flags', 0)
            
            result = self.library.PassThruWriteMsg(
                self.channel_id,
                ctypes.byref(msg_array),
                ctypes.byref(num_msgs)
            )
            
            if result == J2534Error.STATUS_NOERROR:
                return True
            else:
                logger.error(f"Failed to write messages: {self._get_error_string(result)}")
                return False
                
        except Exception as e:
            logger.error(f"Error writing messages: {e}")
            return False
    
    def pass_thru_read_msg(self, timeout_ms: int = 100, max_msgs: int = 1) -> Optional[List[Dict[str, Any]]]:
        """Read messages from vehicle"""
        try:
            if not self.channel_id:
                logger.error("No channel connected")
                return None
            
            # Prepare message structures
            msg_array = (J2534_MESSAGE * max_msgs)()
            num_msgs = wintypes.DWORD(max_msgs)
            
            result = self.library.PassThruReadMsg(
                self.channel_id,
                ctypes.byref(msg_array),
                ctypes.byref(num_msgs),
                timeout_ms
            )
            
            if result == J2534Error.STATUS_NOERROR:
                messages = []
                for i in range(num_msgs.value):
                    msg = {
                        'protocol_id': msg_array[i].ProtocolID,
                        'data': bytes(msg_array[i].Data[:msg_array[i].DataSize]),
                        'timestamp': msg_array[i].Timestamp,
                        'rx_status': msg_array[i].RxStatus
                    }
                    messages.append(msg)
                return messages
            elif result == J2534Error.ERR_BUFFER_EMPTY:
                return []
            else:
                logger.error(f"Failed to read messages: {self._get_error_string(result)}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading messages: {e}")
            return None
    
    def _get_error_string(self, error_code: int) -> str:
        """Get error description from error code"""
        error_strings = {
            J2534Error.ERR_NOT_SUPPORTED: "Function not supported",
            J2534Error.ERR_INVALID_CHANNEL_ID: "Invalid channel ID",
            J2534Error.ERR_INVALID_PROTOCOL_ID: "Invalid protocol ID",
            J2534Error.ERR_NULL_PARAMETER: "Null parameter",
            J2534Error.ERR_INVALID_IOCTL_VALUE: "Invalid IOCTL value",
            J2534Error.ERR_INVALID_FLAGS: "Invalid flags",
            J2534Error.ERR_FAILED: "Operation failed",
            J2534Error.ERR_DEVICE_NOT_CONNECTED: "Device not connected",
            J2534Error.ERR_TIMEOUT: "Operation timeout",
            J2534Error.ERR_INVALID_MSG: "Invalid message",
            J2534Error.ERR_INVALID_TIME_INTERVAL: "Invalid time interval",
            J2534Error.ERR_EXCEEDED_LIMIT: "Exceeded limit",
            J2534Error.ERR_INVALID_MSG_ID: "Invalid message ID",
            J2534Error.ERR_DEVICE_IN_USE: "Device in use",
            J2534Error.ERR_INVALID_IOCTL_ID: "Invalid IOCTL ID",
            J2534Error.ERR_BUFFER_EMPTY: "Buffer empty",
            J2534Error.ERR_BUFFER_FULL: "Buffer full",
            J2534Error.ERR_BUFFER_OVERFLOW: "Buffer overflow",
            J2534Error.ERR_PIN_INVALID: "Invalid pin",
            J2534Error.ERR_CHANNEL_IN_USE: "Channel in use",
            J2534Error.ERR_MSG_PROTOCOL_ID: "Message protocol ID error",
            J2534Error.ERR_INVALID_FILTER_ID: "Invalid filter ID",
            J2534Error.ERR_NO_FLOW_CONTROL: "No flow control",
            J2534Error.ERR_NOT_UNIQUE: "Not unique",
            J2534Error.ERR_INVALID_BAUDRATE: "Invalid baud rate",
            J2534Error.ERR_INVALID_DEVICE_ID: "Invalid device ID"
        }
        return error_strings.get(error_code, f"Unknown error: 0x{error_code:04X}")

# J2534 Message structure
class J2534_MESSAGE(ctypes.Structure):
    _fields_ = [
        ("ProtocolID", wintypes.DWORD),
        ("DataSize", wintypes.DWORD),
        ("Data", wintypes.POINTER(wintypes.BYTE)),
        ("TxFlags", wintypes.DWORD),
        ("Timestamp", wintypes.DWORD),
        ("RxStatus", wintypes.DWORD)
    ]
