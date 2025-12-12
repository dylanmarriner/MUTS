"""
J2534CANEngine - Concrete implementation of MazdaCANEngine using J2534 Pass-Thru interface.
Provides support for commercial tuning tools and professional ECU communication.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import ctypes

try:
    import j2534
    from j2534 import J2534, J2534Error
    J2534_AVAILABLE = True
except ImportError:
    J2534_AVAILABLE = False

from mazda_can_engine import MazdaCANEngine, CANMessage, CANInterfaceType, CANState


class J2534Config:
    """Configuration for J2534 Pass-Thru backend."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize J2534 configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Device configuration
        self.library_path = config.get('library_path', None)  # Auto-detect if None
        self.device_id = config.get('device_id', 0)  # First device
        
        # Protocol configuration
        self.protocol = config.get('protocol', 'CAN')  # CAN protocol
        self.baudrate = config.get('baudrate', 500000)  # 500Kbps
        self.flags = config.get('flags', 0)  # Protocol flags
        
        # Channel configuration
        self.channel_id = config.get('channel_id', 0)  # First CAN channel
        
        # Performance settings
        self.buffer_size = config.get('buffer_size', 1024)
        self.timeout_ms = config.get('timeout_ms', 1000)
        self.block_size = config.get('block_size', 32)
        
        # J2534 specific
        self.filter_type = config.get('filter_type', 'PASS_FILTER')
        self.flow_control = config.get('flow_control', 'NONE')


class J2534CANEngine(MazdaCANEngine):
    """
    J2534 Pass-Thru based implementation of MazdaCANEngine.
    Provides professional-grade CAN interface support.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize J2534 CAN engine.
        
        Args:
            config: Backend-specific configuration
        """
        if not J2534_AVAILABLE:
            raise ImportError("j2534 library is required. Install with: pip install j2534")
        
        # Initialize base class
        super().__init__(interface_type=CANInterfaceType.VECTOR)
        
        # Store J2534 specific config
        self.j2534_config = J2534Config(config)
        self.logger = logging.getLogger(__name__)
        
        # J2534 specific attributes
        self.j2534: Optional[J2534] = None
        self.device_id: Optional[int] = None
        self.channel_id: Optional[int] = None
        
        self.logger.info("J2534CANEngine initialized")
    
    async def connect(self, interface_type: Optional[CANInterfaceType] = None) -> bool:
        """
        Connect to J2534 device.
        
        Args:
            interface_type: Override interface type (ignored, uses J2534)
            
        Returns:
            True if connection successful
        """
        if self.state != CANState.DISCONNECTED:
            self.logger.warning(f"Cannot connect, current state: {self.state.value}")
            return False
        
        try:
            self.state = CANState.CONNECTING
            
            # Load J2534 library
            if self.j2534_config.library_path:
                self.j2534 = J2534(self.j2534_config.library_path)
            else:
                self.j2534 = J2534()  # Auto-detect
            
            # Open device
            self.device_id = self.j2534.passThruOpen()
            if self.device_id is None:
                raise RuntimeError("Failed to open J2534 device")
            
            # Connect to CAN channel
            self.channel_id = self.j2534.passThruConnect(
                self.device_id,
                self.j2534_config.protocol,
                self.j2534_config.flags,
                self.j2534_config.baudrate
            )
            
            if self.channel_id is None:
                raise RuntimeError("Failed to connect to CAN channel")
            
            # Set filters for Mazda CAN IDs
            await self._setup_j2534_filters()
            
            # Set up periodic message reception
            self.j2534.passThruStartPeriodicMsg(
                self.channel_id,
                self.j2534_config.block_size,
                self.j2534_config.timeout_ms
            )
            
            self.state = CANState.CONNECTED
            self._running = True
            
            # Store event loop reference for thread-safe operations
            self.event_loop = asyncio.get_running_loop()
            
            # Start background tasks
            self.reader_task = asyncio.create_task(self._message_reader())
            
            self.logger.info(f"Connected to J2534 device: {self.device_id}, channel: {self.channel_id}")
            return True
            
        except Exception as e:
            self.state = CANState.ERROR
            self.logger.error(f"Failed to connect to J2534 device: {e}")
            await self._cleanup_connection()
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from J2534 device."""
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
            
            # Cleanup J2534 connection
            await self._cleanup_connection()
            
            self.state = CANState.DISCONNECTED
            self.logger.info("Disconnected from J2534 device")
            return True
            
        except Exception as e:
            self.state = CANState.ERROR
            self.logger.error(f"Error disconnecting from J2534 device: {e}")
            return False
    
    async def _cleanup_connection(self) -> None:
        """Clean up J2534 connection resources."""
        try:
            if self.channel_id is not None and self.j2534:
                self.j2534.passThruDisconnect(self.channel_id)
                self.channel_id = None
            
            if self.device_id is not None and self.j2534:
                self.j2534.passThruClose(self.device_id)
                self.device_id = None
            
            if self.j2534:
                self.j2534 = None
                
        except Exception as e:
            self.logger.error(f"Error during J2534 cleanup: {e}")
    
    async def send_message(self, message: CANMessage) -> bool:
        """
        Send CAN message using J2534.
        
        Args:
            message: CAN message to send
            
        Returns:
            True if message sent successfully
        """
        if self.state != CANState.CONNECTED or not self.j2534 or not self.channel_id:
            self.logger.warning("Cannot send message, not connected")
            return False
        
        try:
            # Prepare J2534 message structure
            msg_data = bytearray(message.data)
            msg_size = len(msg_data)
            
            # Send message
            result = self.j2534.passThruWriteMsg(
                self.channel_id,
                msg_data,
                msg_size,
                message.arbitration_id,
                message.extended_id
            )
            
            if result:
                # Update statistics
                self.stats['messages_sent'] += 1
                return True
            else:
                self.logger.error("J2534 passThruWriteMsg failed")
                self.stats['send_errors'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send CAN message via J2534: {e}")
            self.stats['send_errors'] += 1
            return False
    
    async def _message_reader(self) -> None:
        """Background task to read CAN messages from J2534."""
        while self._running and self.j2534 and self.channel_id:
            try:
                # Read messages from J2534
                messages = self.j2534.passThruReadMsg(
                    self.channel_id,
                    self.j2534_config.block_size,
                    self.j2534_config.timeout_ms
                )
                
                if not messages:
                    await asyncio.sleep(0.01)
                    continue
                
                # Process each message
                for msg_data in messages:
                    try:
                        # Parse J2534 message
                        can_msg = self._parse_j2534_message(msg_data)
                        
                        if can_msg:
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
                        self.logger.error(f"Error parsing J2534 message: {e}")
                        self.stats['receive_errors'] += 1
                
            except Exception as e:
                if self._running:
                    self.logger.error(f"Error reading J2534 messages: {e}")
                    self.stats['receive_errors'] += 1
                await asyncio.sleep(0.1)
    
    def _parse_j2534_message(self, msg_data: bytes) -> Optional[CANMessage]:
        """Parse J2534 message data into CANMessage."""
        try:
            # J2534 message format varies by implementation
            # This is a simplified parser for common formats
            
            if len(msg_data) < 4:
                return None
            
            # Extract arbitration ID (first 4 bytes, little-endian)
            arbitration_id = int.from_bytes(msg_data[0:4], 'little')
            
            # Check if extended ID
            extended_id = bool(arbitration_id & 0x80000000)
            if extended_id:
                arbitration_id &= 0x1FFFFFFF  # Clear extended flag
            
            # Extract data (remaining bytes)
            data = msg_data[4:]
            dlc = len(data)
            
            return CANMessage(
                arbitration_id=arbitration_id,
                data=data,
                dlc=dlc,
                extended_id=extended_id,
                timestamp=time.time(),
                priority=self._get_priority_from_id(arbitration_id)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse J2534 message: {e}")
            return None
    
    async def _setup_j2534_filters(self) -> None:
        """Set up J2534 message filters for Mazda CAN IDs."""
        if not self.j2534 or not self.channel_id:
            return
        
        try:
            # Set up filters for Mazda-specific CAN IDs
            mazda_can_ids = [
                0x280,  # Engine RPM
                0x281,  # Vehicle Speed
                0x250,  # Throttle Position
                0x311,  # Boost Pressure
                0x310,  # MAP Sensor
                0x290,  # MAF Flow
            ]
            
            for can_id in mazda_can_ids:
                # Create pass filter for each ID
                mask = 0x7FF if not (can_id & 0x80000000) else 0x1FFFFFFF
                pattern = can_id
                
                result = self.j2534.passThruStartMsgFilter(
                    self.channel_id,
                    self.j2534_config.filter_type,
                    mask,
                    pattern,
                    None,  # No flow control
                    None   # No flow control
                )
                
                if not result:
                    self.logger.warning(f"Failed to set J2534 filter for CAN ID 0x{can_id:03X}")
            
            self.logger.info("J2534 message filters configured")
            
        except Exception as e:
            self.logger.error(f"Failed to set up J2534 filters: {e}")
    
    def _get_priority_from_id(self, arbitration_id: int) -> int:
        """Get priority from CAN arbitration ID."""
        # Standard CAN priority based on ID (lower = higher priority)
        if arbitration_id < 0x800:
            return 7 - (arbitration_id >> 7)
        else:
            return 0  # Extended ID, lowest priority
    
    def get_interface_info(self) -> Dict[str, Any]:
        """Get J2534 interface information."""
        info = super().get_interface_info()
        
        if self.j2534:
            info.update({
                'backend': 'j2534-passthru',
                'device_id': self.device_id,
                'channel_id': self.channel_id,
                'protocol': self.j2534_config.protocol,
                'baudrate': self.j2534_config.baudrate,
                'library_path': self.j2534_config.library_path or 'auto-detected',
                'bus_state': 'connected' if self.state == CANState.CONNECTED else 'disconnected',
                'protocol': 'J2534 Pass-Thru',
            })
        else:
            info.update({
                'backend': 'j2534-passthru',
                'device_id': None,
                'channel_id': None,
                'protocol': self.j2534_config.protocol,
                'baudrate': self.j2534_config.baudrate,
                'library_path': self.j2534_config.library_path or 'auto-detected',
                'bus_state': 'disconnected',
                'protocol': 'J2534 Pass-Thru',
            })
        
        return info
    
    @staticmethod
    def get_available_devices() -> List[Dict[str, Any]]:
        """Get list of available J2534 devices."""
        if not J2534_AVAILABLE:
            return []
        
        try:
            devices = []
            j2534 = J2534()
            
            # Try to open devices to find available ones
            for device_id in range(0, 16):  # Check first 16 devices
                try:
                    dev_id = j2534.passThruOpen(device_id)
                    if dev_id is not None:
                        # Get device info if available
                        devices.append({
                            'device_id': dev_id,
                            'index': device_id,
                            'status': 'available'
                        })
                        j2534.passThruClose(dev_id)
                except Exception:
                    continue
            
            return devices
            
        except Exception:
            return []
    
    def test_connection(self) -> bool:
        """Test if J2534 connection is working."""
        if not self.j2534 or not self.channel_id or self.state != CANState.CONNECTED:
            return False
        
        try:
            # Try to send a test message
            test_msg = bytearray([0x01, 0x00])  # Simple test data
            
            result = self.j2534.passThruWriteMsg(
                self.channel_id,
                test_msg,
                len(test_msg),
                0x7DF,  # OBD diagnostic request
                False   # Standard ID
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"J2534 connection test failed: {e}")
            return False
