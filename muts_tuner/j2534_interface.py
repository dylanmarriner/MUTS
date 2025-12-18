#!/usr/bin/env python3
"""
J2534 Interface Integration Layer
Provides Windows DLL access for J2534 vehicle communication interfaces
"""

import ctypes
import platform
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import IntEnum
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class J2534Protocol(IntEnum):
    """J2534 Protocol IDs"""
    J1850VPW = 0x01
    J1850PWM = 0x02
    ISO9141 = 0x03
    ISO14230 = 0x04
    CAN = 0x05
    ISO15765 = 0x06
    SCI_A_ENGINE = 0x07
    SCI_A_TRANS = 0x08
    SCI_B_ENGINE = 0x09
    SCI_B_TRANS = 0x0A

class J2534FilterType(IntEnum):
    """J2534 Filter Types"""
    PASS_FILTER = 0x01
    BLOCK_FILTER = 0x02
    FLOW_CONTROL_FILTER = 0x03

class J2534ErrorCode(IntEnum):
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
    ERR_PIN_NOT_FOUND = 0x13
    ERR_PIN_IN_USE = 0x14
    ERR_INVALID_DEVICE_ID = 0x15
    ERR_INVALID_FILTER_ID = 0x16
    ERR_CHANNEL_IN_USE = 0x17
    ERR_MSG_PROTOCOL_ID = 0x18
    ERR_INVALID_LABEL = 0x19
    ERR_INVALID_BAUDRATE = 0x1A
    ERR_INVALID_DEVICE_ID = 0x1B

class J2534Message(ctypes.Structure):
    """J2534 Message structure"""
    _fields_ = [
        ("ProtocolID", ctypes.c_ulong),
        ("RxStatus", ctypes.c_ulong),
        ("TxFlags", ctypes.c_ulong),
        ("Timestamp", ctypes.c_ulong),
        ("DataSize", ctypes.c_ulong),
        ("ExtraDataIndex", ctypes.c_ulong),
        ("Data", ctypes.c_ubyte * 4128)  # Maximum message size
    ]

class J2534Interface:
    """
    J2534 Pass-thru Interface for vehicle communication
    Provides access to J2534 DLL for ECU communication
    """
    
    def __init__(self, dll_path: Optional[str] = None):
        """
        Initialize J2534 Interface
        
        Args:
            dll_path: Path to J2534 DLL file. If None, will try common locations
        """
        self.dll = None
        self.device_id = 0
        self.channel_id = 0
        self.filter_id = 0
        self.is_connected = False
        self.is_channel_open = False
        self._message_callbacks: List[Callable] = []
        self._receive_thread = None
        self._stop_receiving = False
        
        # Load J2534 DLL
        self._load_dll(dll_path)
        
        # Setup function signatures
        self._setup_functions()
    
    def _load_dll(self, dll_path: Optional[str] = None):
        """Load J2534 DLL from system"""
        if platform.system() != 'Windows':
            raise RuntimeError("J2534 interface requires Windows")
        
        # Try common DLL paths if not specified
        if not dll_path:
            common_paths = [
                "C:\\Windows\\System32\\j2534.dll",
                "C:\\Program Files\\Drew Technologies\\MongoosePro J2534\\DLL\\MongoosePro.dll",
                "C:\\Program Files (x86)\\Drew Technologies\\MongoosePro J2534\\DLL\\MongoosePro.dll",
                "C:\\Program Files\\Cardaq Technologies\\Cardaq-Plus\\j2534.dll",
                "C:\\Program Files (x86)\\Cardaq Technologies\\Cardaq-Plus\\j2534.dll"
            ]
            
            for path in common_paths:
                try:
                    self.dll = ctypes.windll.LoadLibrary(path)
                    logger.info(f"Loaded J2534 DLL from: {path}")
                    break
                except:
                    continue
            else:
                raise RuntimeError("J2534 DLL not found. Please install J2534 interface software.")
        else:
            try:
                self.dll = ctypes.windll.LoadLibrary(dll_path)
                logger.info(f"Loaded J2534 DLL from: {dll_path}")
            except Exception as e:
                raise RuntimeError(f"Failed to load J2534 DLL from {dll_path}: {e}")
    
    def _setup_functions(self):
        """Setup J2534 function signatures"""
        # PassThruOpen
        self.dll.PassThruOpen.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_ulong)]
        self.dll.PassThruOpen.restype = ctypes.c_ulong
        
        # PassThruClose
        self.dll.PassThruClose.argtypes = [ctypes.c_ulong]
        self.dll.PassThruClose.restype = ctypes.c_ulong
        
        # PassThruConnect
        self.dll.PassThruConnect.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
        self.dll.PassThruConnect.restype = ctypes.c_ulong
        
        # PassThruDisconnect
        self.dll.PassThruDisconnect.argtypes = [ctypes.c_ulong]
        self.dll.PassThruDisconnect.restype = ctypes.c_ulong
        
        # PassThruReadMsgs
        self.dll.PassThruReadMsgs.argtypes = [ctypes.c_ulong, ctypes.POINTER(J2534Message), ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong]
        self.dll.PassThruReadMsgs.restype = ctypes.c_ulong
        
        # PassThruWriteMsgs
        self.dll.PassThruWriteMsgs.argtypes = [ctypes.c_ulong, ctypes.POINTER(J2534Message), ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong]
        self.dll.PassThruWriteMsgs.restype = ctypes.c_ulong
        
        # PassThruStartPeriodicMsg
        self.dll.PassThruStartPeriodicMsg.argtypes = [ctypes.c_ulong, ctypes.POINTER(J2534Message), ctypes.POINTER(ctypes.c_ulong), ctypes.c_ulong]
        self.dll.PassThruStartPeriodicMsg.restype = ctypes.c_ulong
        
        # PassThruStopPeriodicMsg
        self.dll.PassThruStopPeriodicMsg.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
        self.dll.PassThruStopPeriodicMsg.restype = ctypes.c_ulong
        
        # PassThruStartMsgFilter
        self.dll.PassThruStartMsgFilter.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(J2534Message), ctypes.POINTER(J2534Message), ctypes.POINTER(J2534Message), ctypes.POINTER(ctypes.c_ulong)]
        self.dll.PassThruStartMsgFilter.restype = ctypes.c_ulong
        
        # PassThruStopMsgFilter
        self.dll.PassThruStopMsgFilter.argtypes = [ctypes.c_ulong, ctypes.c_ulong]
        self.dll.PassThruStopMsgFilter.restype = ctypes.c_ulong
        
        # PassThruSetProgrammingVoltage
        self.dll.PassThruSetProgrammingVoltage.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
        self.dll.PassThruSetProgrammingVoltage.restype = ctypes.c_ulong
        
        # PassThruReadVersion
        self.dll.PassThruReadVersion.argtypes = [ctypes.c_ulong, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        self.dll.PassThruReadVersion.restype = ctypes.c_ulong
        
        # PassThruGetLastError
        self.dll.PassThruGetLastError.argtypes = [ctypes.c_char_p]
        self.dll.PassThruGetLastError.restype = ctypes.c_ulong
        
        # PassThruIoctl
        self.dll.PassThruIoctl.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
        self.dll.PassThruIoctl.restype = ctypes.c_ulong
    
    def connect(self, device_id: Optional[str] = None) -> bool:
        """
        Connect to J2534 device
        
        Args:
            device_id: Device identifier (optional)
            
        Returns:
            bool: True if successful
        """
        try:
            # Convert device_id to bytes if provided
            device_ptr = None
            if device_id:
                device_bytes = device_id.encode('ascii')
                device_ptr = ctypes.create_string_buffer(device_bytes)
            
            # Open device
            result = self.dll.PassThruOpen(device_ptr, ctypes.byref(ctypes.c_ulong(self.device_id)))
            
            if result != J2534ErrorCode.STATUS_NOERROR:
                error_msg = self._get_error_string(result)
                logger.error(f"Failed to open J2534 device: {error_msg}")
                return False
            
            self.is_connected = True
            logger.info("J2534 device connected successfully")
            
            # Read device version info
            self._read_version_info()
            
            return True
            
        except Exception as e:
            logger.error(f"Exception connecting to J2534 device: {e}")
            return False
    
    def open_channel(self, protocol: J2534Protocol = J2534Protocol.ISO15765, 
                    baudrate: int = 500000, flags: int = 0) -> bool:
        """
        Open communication channel
        
        Args:
            protocol: Communication protocol
            baudrate: Communication speed
            flags: Channel flags
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected:
            logger.error("Device not connected")
            return False
        
        try:
            result = self.dll.PassThruConnect(
                self.device_id,
                protocol,
                flags,
                baudrate,
                ctypes.byref(ctypes.c_ulong(self.channel_id))
            )
            
            if result != J2534ErrorCode.STATUS_NOERROR:
                error_msg = self._get_error_string(result)
                logger.error(f"Failed to open channel: {error_msg}")
                return False
            
            self.is_channel_open = True
            logger.info(f"Channel opened with protocol {protocol}")
            
            # Start message receiving thread
            self._start_message_receiver()
            
            return True
            
        except Exception as e:
            logger.error(f"Exception opening channel: {e}")
            return False
    
    def send_message(self, data: bytes, protocol_id: int = 0, tx_flags: int = 0) -> bool:
        """
        Send message to ECU
        
        Args:
            data: Message data
            protocol_id: Protocol ID
            tx_flags: Transmit flags
            
        Returns:
            bool: True if successful
        """
        if not self.is_channel_open:
            logger.error("Channel not open")
            return False
        
        try:
            # Create message structure
            msg = J2534Message()
            msg.ProtocolID = protocol_id
            msg.RxStatus = 0
            msg.TxFlags = tx_flags
            msg.Timestamp = 0
            msg.DataSize = len(data)
            msg.ExtraDataIndex = 0
            
            # Copy data to message buffer
            for i, byte in enumerate(data):
                if i < len(msg.Data):
                    msg.Data[i] = byte
            
            # Send message
            num_msgs = ctypes.c_ulong(1)
            result = self.dll.PassThruWriteMsgs(
                self.channel_id,
                ctypes.byref(msg),
                ctypes.byref(num_msgs),
                ctypes.c_ulong(50)  # Timeout
            )
            
            if result != J2534ErrorCode.STATUS_NOERROR:
                error_msg = self._get_error_string(result)
                logger.error(f"Failed to send message: {error_msg}")
                return False
            
            logger.debug(f"Sent message: {data.hex()}")
            return True
            
        except Exception as e:
            logger.error(f"Exception sending message: {e}")
            return False
    
    def read_messages(self, timeout_ms: int = 50, max_msgs: int = 1) -> List[bytes]:
        """
        Read messages from ECU
        
        Args:
            timeout_ms: Read timeout in milliseconds
            max_msgs: Maximum number of messages to read
            
        Returns:
            List of received messages (as bytes)
        """
        if not self.is_channel_open:
            return []
        
        try:
            # Create message buffer
            msg_buffer = (J2534Message * max_msgs)()
            num_msgs = ctypes.c_ulong(max_msgs)
            
            result = self.dll.PassThruReadMsgs(
                self.channel_id,
                ctypes.byref(msg_buffer),
                ctypes.byref(num_msgs),
                ctypes.c_ulong(timeout_ms)
            )
            
            messages = []
            if result == J2534ErrorCode.STATUS_NOERROR:
                for i in range(num_msgs.value):
                    msg = msg_buffer[i]
                    # Extract data bytes from the ctypes structure
                    data = bytes(msg.Data[:msg.DataSize])
                    messages.append(data)
                    logger.debug(f"Received message: {data.hex()}")
            elif result != J2534ErrorCode.ERR_BUFFER_EMPTY:
                error_msg = self._get_error_string(result)
                logger.warning(f"Read messages error: {error_msg}")
            
            return messages
            
        except Exception as e:
            logger.error(f"Exception reading messages: {e}")
            return []
    
    def _start_message_receiver(self):
        """Start background message receiving thread"""
        self._stop_receiving = False
        self._receive_thread = threading.Thread(target=self._message_receiver_loop, daemon=True)
        self._receive_thread.start()
    
    def _message_receiver_loop(self):
        """Background message receiving loop"""
        while not self._stop_receiving and self.is_channel_open:
            messages = self.read_messages(timeout_ms=10)
            for message in messages:
                for callback in self._message_callbacks:
                    try:
                        callback(message)
                    except:
                        pass
            time.sleep(0.001)  # Small delay to prevent CPU spinning
    
    def add_message_callback(self, callback: Callable[[bytes], None]):
        """Add callback for received messages"""
        self._message_callbacks.append(callback)
    
    def remove_message_callback(self, callback: Callable[[bytes], None]):
        """Remove message callback"""
        if callback in self._message_callbacks:
            self._message_callbacks.remove(callback)
    
    def _read_version_info(self):
        """Read device version information"""
        try:
            firmware = ctypes.create_string_buffer(80)
            dll = ctypes.create_string_buffer(80)
            api = ctypes.create_string_buffer(80)
            
            result = self.dll.PassThruReadVersion(
                self.device_id,
                firmware,
                dll,
                api
            )
            
            if result == J2534ErrorCode.STATUS_NOERROR:
                logger.info(f"Firmware: {firmware.value.decode()}")
                logger.info(f"DLL: {dll.value.decode()}")
                logger.info(f"API: {api.value.decode()}")
            
        except Exception as e:
            logger.warning(f"Failed to read version info: {e}")
    
    def _get_error_string(self, error_code: int) -> str:
        """Get error description from error code"""
        error_strings = {
            J2534ErrorCode.ERR_NOT_SUPPORTED: "Not supported",
            J2534ErrorCode.ERR_INVALID_CHANNEL_ID: "Invalid channel ID",
            J2534ErrorCode.ERR_INVALID_PROTOCOL_ID: "Invalid protocol ID",
            J2534ErrorCode.ERR_NULL_PARAMETER: "Null parameter",
            J2534ErrorCode.ERR_INVALID_IOCTL_VALUE: "Invalid IOCTL value",
            J2534ErrorCode.ERR_INVALID_FLAGS: "Invalid flags",
            J2534ErrorCode.ERR_FAILED: "Failed",
            J2534ErrorCode.ERR_DEVICE_NOT_CONNECTED: "Device not connected",
            J2534ErrorCode.ERR_TIMEOUT: "Timeout",
            J2534ErrorCode.ERR_INVALID_MSG: "Invalid message",
            J2534ErrorCode.ERR_INVALID_TIME_INTERVAL: "Invalid time interval",
            J2534ErrorCode.ERR_EXCEEDED_LIMIT: "Exceeded limit",
            J2534ErrorCode.ERR_INVALID_MSG_ID: "Invalid message ID",
            J2534ErrorCode.ERR_DEVICE_IN_USE: "Device in use",
            J2534ErrorCode.ERR_INVALID_IOCTL_ID: "Invalid IOCTL ID",
            J2534ErrorCode.ERR_BUFFER_EMPTY: "Buffer empty",
            J2534ErrorCode.ERR_BUFFER_FULL: "Buffer full",
            J2534ErrorCode.ERR_BUFFER_OVERFLOW: "Buffer overflow",
            J2534ErrorCode.ERR_PIN_NOT_FOUND: "Pin not found",
            J2534ErrorCode.ERR_PIN_IN_USE: "Pin in use",
            J2534ErrorCode.ERR_INVALID_DEVICE_ID: "Invalid device ID",
            J2534ErrorCode.ERR_INVALID_FILTER_ID: "Invalid filter ID",
            J2534ErrorCode.ERR_CHANNEL_IN_USE: "Channel in use",
            J2534ErrorCode.ERR_MSG_PROTOCOL_ID: "Message protocol ID",
            J2534ErrorCode.ERR_INVALID_LABEL: "Invalid label",
            J2534ErrorCode.ERR_INVALID_BAUDRATE: "Invalid baudrate"
        }
        return error_strings.get(error_code, f"Unknown error (0x{error_code:02X})")
    
    def disconnect(self):
        """Disconnect from J2534 device"""
        try:
            # Stop message receiver
            self._stop_receiving = True
            if self._receive_thread and self._receive_thread.is_alive():
                self._receive_thread.join(timeout=2.0)
            
            # Close channel
            if self.is_channel_open:
                self.dll.PassThruDisconnect(self.channel_id)
                self.is_channel_open = False
            
            # Close device
            if self.is_connected:
                self.dll.PassThruClose(self.device_id)
                self.is_connected = False
            
            logger.info("J2534 device disconnected")
            
        except Exception as e:
            logger.error(f"Exception during disconnect: {e}")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()

# Test function for J2534 interface
def test_j2534_interface():
    """Test J2534 interface functionality"""
    logger.info("Testing J2534 Interface...")
    
    try:
        # Create interface
        interface = J2534Interface()
        
        # Connect to device
        if not interface.connect():
            logger.error("Failed to connect to J2534 device")
            return False
        
        # Open CAN channel
        if not interface.open_channel(J2534Protocol.ISO15765, 500000):
            logger.error("Failed to open CAN channel")
            interface.disconnect()
            return False
        
        # Add message callback
        def message_callback(data):
            logger.info(f"Received: {data.hex()}")
        
        interface.add_message_callback(message_callback)
        
        # Send test message (ISO-TP request for VIN)
        test_msg = bytes([0x22, 0xF1, 0x89])  # Read VIN request
        if interface.send_message(test_msg):
            logger.info("Test message sent successfully")
            
            # Wait for response
            time.sleep(1)
        
        # Cleanup
        interface.disconnect()
        logger.info("J2534 interface test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"J2534 interface test failed: {e}")
        return False

if __name__ == "__main__":
    test_j2534_interface()
