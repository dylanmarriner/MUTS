"""
PythonCANEngine - Concrete implementation of MazdaCANEngine using python-can library.
Provides SocketCAN, PCAN, Vector, and other interface support through python-can.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

try:
    import can
    from can import Bus, Message
    PYTHON_CAN_AVAILABLE = True
except ImportError:
    PYTHON_CAN_AVAILABLE = False

from mazda_can_engine import MazdaCANEngine, CANMessage, CANInterfaceType, CANState


class PythonCANConfig:
    """Configuration for python-can backend."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize python-can configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Interface configuration
        self.interface = config.get('interface', 'socketcan')  # socketcan, pcan, vector, etc.
        self.channel = config.get('channel', 'can0')  # can0, PCAN_USBBUS1, etc.
        self.bitrate = config.get('bitrate', 500000)  # 500Kbps typical
        
        # Bus configuration
        self.receive_own_messages = config.get('receive_own_messages', False)
        self.fd = config.get('fd', False)  # CAN FD support
        
        # Performance settings
        self.buffer_size = config.get('buffer_size', 1024)
        self.timeout = config.get('timeout', 1.0)
        
        # Logging
        self.log_level = config.get('log_level', 'WARNING')


class PythonCANEngine(MazdaCANEngine):
    """
    Python-can based implementation of MazdaCANEngine.
    Supports various CAN interfaces through the python-can library.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize python-can engine.
        
        Args:
            config: Backend-specific configuration
        """
        if not PYTHON_CAN_AVAILABLE:
            raise ImportError("python-can library is required. Install with: pip install python-can")
        
        # Initialize base class with generic config
        super().__init__(interface_type=CANInterfaceType.SOCKETCAN)
        
        # Store python-can specific config
        self.pycan_config = PythonCANConfig(config)
        self.logger = logging.getLogger(__name__)
        
        # Python-can specific attributes
        self.bus: Optional[Bus] = None
        self._reader_task: Optional[asyncio.Task] = None
        
        # Configure python-can logging
        can_logger = logging.getLogger('can')
        can_logger.setLevel(self.pycan_config.log_level)
        
        self.logger.info(f"PythonCANEngine initialized with {self.pycan_config.interface} interface")
    
    async def connect(self, interface_type: Optional[CANInterfaceType] = None) -> bool:
        """
        Connect to CAN interface using python-can.
        
        Args:
            interface_type: Override interface type (ignored, uses config)
            
        Returns:
            True if connection successful
        """
        if self.state != CANState.DISCONNECTED:
            self.logger.warning(f"Cannot connect, current state: {self.state.value}")
            return False
        
        try:
            self.state = CANState.CONNECTING
            
            # Create bus configuration
            bus_config = {
                'interface': self.pycan_config.interface,
                'channel': self.pycan_config.channel,
                'bitrate': self.pycan_config.bitrate,
                'receive_own_messages': self.pycan_config.receive_own_messages,
                'fd': self.pycan_config.fd,
            }
            
            # Connect to CAN bus
            self.bus = Bus(**bus_config)
            
            if not self.bus:
                raise RuntimeError("Failed to create python-can bus")
            
            self.state = CANState.CONNECTED
            self._running = True
            
            # Store event loop reference for thread-safe operations
            self.event_loop = asyncio.get_running_loop()
            
            # Start background tasks
            self.reader_task = asyncio.create_task(self._message_reader())
            
            self.logger.info(f"Connected to CAN bus: {self.pycan_config.interface}:{self.pycan_config.channel}")
            return True
            
        except Exception as e:
            self.state = CANState.ERROR
            self.logger.error(f"Failed to connect to CAN bus: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from CAN interface."""
        if self.state == CANState.DISCONNECTED:
            return True
        
        try:
            self._running = False
            self.state = CANState.DISCONNECTING
            
            # Stop background tasks
            if self.reader_task:
                self.reader_task.cancel()
                try:
                    await self.reader_task
                except asyncio.CancelledError:
                    pass
            
            # Close python-can bus
            if self.bus:
                self.bus.shutdown()
                self.bus = None
            
            self.state = CANState.DISCONNECTED
            self.logger.info("Disconnected from CAN bus")
            return True
            
        except Exception as e:
            self.state = CANState.ERROR
            self.logger.error(f"Error disconnecting from CAN bus: {e}")
            return False
    
    async def send_message(self, message: CANMessage) -> bool:
        """
        Send CAN message using python-can.
        
        Args:
            message: CAN message to send
            
        Returns:
            True if message sent successfully
        """
        if self.state != CANState.CONNECTED or not self.bus:
            self.logger.warning("Cannot send message, not connected")
            return False
        
        try:
            # Convert to python-can message
            can_msg = Message(
                arbitration_id=message.arbitration_id,
                data=message.data,
                is_extended_id=message.extended_id,
                is_remote_frame=False,
                is_error_frame=False,
                timestamp=time.time()
            )
            
            # Send message
            self.bus.send(can_msg, timeout=self.pycan_config.timeout)
            
            # Update statistics
            self.stats['messages_sent'] += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send CAN message: {e}")
            self.stats['send_errors'] += 1
            return False
    
    async def _message_reader(self) -> None:
        """Background task to read CAN messages from python-can."""
        while self._running and self.bus:
            try:
                # Read message with timeout
                msg = self.bus.recv(timeout=self.pycan_config.timeout)
                
                if msg is None:
                    continue
                
                # Convert to internal CAN message format
                can_msg = CANMessage(
                    arbitration_id=msg.arbitration_id,
                    data=msg.data,
                    dlc=msg.dlc,
                    extended_id=msg.is_extended_id,
                    timestamp=msg.timestamp,
                    priority=self._get_priority_from_id(msg.arbitration_id)
                )
                
                # Apply filters
                if self._should_accept_message(can_msg):
                    # Add to async queue for handlers
                    try:
                        if self.event_loop and not self.event_loop.is_closed():
                            asyncio.run_coroutine_threadsafe(
                                self.message_queue.put(can_msg),
                                self.event_loop
                            ).result(timeout=0.01)
                    except Exception:
                        pass  # Drop if async queue is full or loop is busy
                
                # Update statistics
                self.stats['messages_received'] += 1
                
            except Exception as e:
                if self._running:
                    self.logger.error(f"Error reading CAN message: {e}")
                    self.stats['receive_errors'] += 1
                await asyncio.sleep(0.1)
    
    def _get_priority_from_id(self, arbitration_id: int) -> int:
        """Get priority from CAN arbitration ID."""
        # Standard CAN priority based on ID (lower = higher priority)
        if arbitration_id < 0x800:
            return 7 - (arbitration_id >> 7)
        else:
            return 0  # Extended ID, lowest priority
    
    def get_interface_info(self) -> Dict[str, Any]:
        """Get python-can interface information."""
        info = super().get_interface_info()
        
        if self.bus:
            info.update({
                'backend': 'python-can',
                'interface': self.pycan_config.interface,
                'channel': self.pycan_config.channel,
                'bitrate': self.pycan_config.bitrate,
                'fd_enabled': self.pycan_config.fd,
                'bus_state': self.bus.state.__class__.__name__,
                'protocol': 'CAN 2.0A/B' + (' FD' if self.pycan_config.fd else ''),
            })
        else:
            info.update({
                'backend': 'python-can',
                'interface': self.pycan_config.interface,
                'channel': self.pycan_config.channel,
                'bitrate': self.pycan_config.bitrate,
                'fd_enabled': self.pycan_config.fd,
                'bus_state': 'disconnected',
                'protocol': 'CAN 2.0A/B' + (' FD' if self.pycan_config.fd else ''),
            })
        
        return info
    
    @staticmethod
    def get_available_interfaces() -> List[str]:
        """Get list of available python-can interfaces."""
        if not PYTHON_CAN_AVAILABLE:
            return []
        
        try:
            # Get available interfaces from python-can
            interfaces = []
            
            # Check for common interfaces
            common_interfaces = ['socketcan', 'pcan', 'vector', 'slcan', 'iscan', 'neovi', 'ics_neovi']
            
            for interface in common_interfaces:
                try:
                    # Try to create a test bus (without actually connecting)
                    test_config = {'interface': interface}
                    Bus(**test_config)
                    interfaces.append(interface)
                except Exception:
                    pass
            
            return interfaces
            
        except Exception:
            return []
    
    @staticmethod
    def get_available_channels(interface: str) -> List[str]:
        """Get list of available channels for an interface."""
        if not PYTHON_CAN_AVAILABLE:
            return []
        
        try:
            channels = []
            
            if interface == 'socketcan':
                # Check for available CAN interfaces
                import os
                if os.path.exists('/sys/class/net/'):
                    for item in os.listdir('/sys/class/net/'):
                        if item.startswith('can'):
                            channels.append(item)
            
            elif interface == 'pcan':
                # PCAN USB devices
                for i in range(1, 17):
                    channels.append(f'PCAN_USBBUS{i}')
            
            elif interface == 'vector':
                # Vector interfaces
                for i in range(1, 9):
                    channels.append(f'VN{i}')
            
            return channels
            
        except Exception:
            return []
    
    def test_connection(self) -> bool:
        """Test if CAN connection is working."""
        if not self.bus or self.state != CANState.CONNECTED:
            return False
        
        try:
            # Try to send a test message
            test_msg = Message(
                arbitration_id=0x7DF,  # OBD diagnostic request
                data=[0x01, 0x00],     # Test request
                is_extended_id=False
            )
            
            self.bus.send(test_msg, timeout=1.0)
            return True
            
        except Exception as e:
            self.logger.error(f"CAN connection test failed: {e}")
            return False
