"""
MazdaCANEngine - CAN bus communication and message handling for Mazda vehicles.
Provides low-level CAN interface, message filtering, and protocol handling.
Supports both standard and extended CAN IDs with real-time message processing.
"""

import time
import asyncio
import struct
import logging
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum, IntEnum, IntFlag
from collections import deque, defaultdict
import threading
import queue

from models import (
    CANMessage, CANFilter, CANPriority, TelemetryData,
    SecurityLevel, SecurityCredentials, LogEntry, UDSRequest, UDSResponse, UDSService, UDSNegativeResponseCode
)


class CANState(Enum):
    """CAN interface states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    BUS_OFF = "bus_off"


class CANError(Enum):
    """CAN error types."""
    NONE = "none"
    STUFF = "stuff_error"
    FORM = "form_error"
    ACK = "ack_error"
    BIT_RECESSIVE = "bit_recessive_error"
    BIT_DOMINANT = "bit_dominant_error"
    CRC = "crc_error"
    SOFTWARE = "software_error"


class CANFrameType(Enum):
    """CAN frame types."""
    DATA = "data"
    REMOTE = "remote"
    ERROR = "error"
    OVERLOAD = "overload"


@dataclass
class CANInterfaceConfig:
    """CAN interface configuration."""
    interface_type: str = "socketcan"  # socketcan, pcan, vector, slcan
    channel: str = "can0"
    bitrate: int = 500000  # 500kbps standard for automotive
    fd_mode: bool = False  # CAN FD support
    termination: bool = True  # 120 ohm termination
    filters: List[CANFilter] = field(default_factory=list)
    
    # Timing parameters for 500kbps
    sjw: int = 1  # Synchronization jump width
    tseg1: int = 16  # Time segment 1
    tseg2: int = 7  # Time segment 2
    brp: int = 1  # Bit rate prescaler


@dataclass
class CANStatistics:
    """CAN communication statistics."""
    total_messages_sent: int = 0
    total_messages_received: int = 0
    error_frames: int = 0
    bus_off_count: int = 0
    last_message_time: float = 0.0
    peak_load: float = 0.0  # Peak bus load percentage
    current_load: float = 0.0  # Current bus load percentage
    
    # Error counters
    tx_error_count: int = 0
    rx_error_count: int = 0
    
    # Timing statistics
    avg_tx_time: float = 0.0
    avg_rx_time: float = 0.0
    max_tx_time: float = 0.0
    max_rx_time: float = 0.0


class CANError(Exception):
    """CAN communication errors."""
    pass


class CANInterfaceError(CANError):
    """CAN interface hardware errors."""
    pass


class CANProtocolError(CANError):
    """CAN protocol errors."""
    pass


class MazdaCANEngine:
    """
    CAN bus communication engine for Mazda vehicles.
    Handles low-level CAN communication, filtering, and message processing.
    Includes UDS (Unified Diagnostic Services) support for diagnostic operations.
    """
    
    # Mazda-specific CAN IDs (2011 Mazdaspeed 3)
    MAZDA_CAN_IDS = {
        # Engine control module
        "ECM_REQUEST": 0x7E0,      # ECM request ID
        "ECM_RESPONSE": 0x7E8,     # ECM response ID
        "ECM_BROADCAST": 0x7DF,    # Broadcast to all ECUs
        
        # Transmission control module
        "TCM_REQUEST": 0x7E1,
        "TCM_RESPONSE": 0x7E9,
        
        # ABS/ESC module
        "ABS_REQUEST": 0x7E2,
        "ABS_RESPONSE": 0x7EA,
        
        # Instrument cluster
        "CLUSTER_STATUS": 0x430,
        "CLUSTER_REQUEST": 0x7E3,
        "CLUSTER_RESPONSE": 0x7EB,
        
        # Body control module
        "BCM_REQUEST": 0x7E4,
        "BCM_RESPONSE": 0x7EC,
        
        # Steering angle sensor
        "SAS_DATA": 0x0F0,
        
        # Wheel speed sensors
        "WHEEL_SPEED_FL": 0x1A0,
        "WHEEL_SPEED_FR": 0x1A1,
        "WHEEL_SPEED_RL": 0x1A2,
        "WHEEL_SPEED_RR": 0x1A3,
        
        # Throttle position
        "TPS_DATA": 0x250,
        
        # Pedal position
        "PEDAL_DATA": 0x251,
        
        # Brake pressure
        "BRAKE_PRESSURE": 0x1A4,
        
        # Fuel system
        "FUEL_PRESSURE": 0x350,
        "FUEL_LEVEL": 0x351,
        
        # Temperature sensors
        "COOLANT_TEMP": 0x300,
        "OIL_TEMP": 0x301,
        "IAT_TEMP": 0x302,
        
        # Pressure sensors
        "MAP_SENSOR": 0x310,
        "BOOST_PRESSURE": 0x311,
        "OIL_PRESSURE": 0x312,
        
        # Ignition system
        "IGNITION_TIMING": 0x320,
        "COIL_DWELL": 0x321,
        
        # Engine parameters
        "ENGINE_RPM": 0x280,
        "VEHICLE_SPEED": 0x281,
        "MAF_FLOW": 0x290,
        
        # Emissions
        "O2_SENSOR_1": 0x360,
        "O2_SENSOR_2": 0x361,
        "EVAP_STATUS": 0x370,
        
        # Safety systems
        "AIRBAG_STATUS": 0x400,
        "SRS_MODULE": 0x401,
        
        # Climate control
        "HVAC_STATUS": 0x420,
        "AC_PRESSURE": 0x421,
        
        # Lighting
        "LIGHTING_STATUS": 0x440,
        "HEADLIGHT_STATUS": 0x441,
        
        # Power accessories
        "POWER_WINDOWS": 0x460,
        "POWER_DOORS": 0x461,
        "POWER_MIRRORS": 0x462,
    }
    
    # UDS Configuration
    UDS_DEFAULT_TIMEOUT = 2.0  # seconds
    UDS_MAX_RETRIES = 3
    
    def __init__(self, config: Optional[CANInterfaceConfig] = None):
        """
        Initialize CAN engine.
        
        Args:
            config: CAN interface configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or CANInterfaceConfig()
        
        # Interface state
        self.state = CANState.DISCONNECTED
        self.interface = None
        self.reader_task = None
        self.writer_task = None
        
        # Message handling
        self.message_queue = asyncio.Queue(maxsize=1000)
        self.message_handlers: Dict[int, List[Callable]] = defaultdict(list)
        self.filters: List[CANFilter] = self.config.filters.copy()
        
        # Statistics and monitoring
        self.stats = CANStatistics()
        self.message_buffer = deque(maxlen=10000)  # Circular buffer
        self.load_samples = deque(maxlen=100)
        
        # Threading for real-time processing
        self._running = False
        self._receive_thread = None
        self._process_thread = None
        self._thread_queue = queue.Queue(maxsize=1000)
        self.event_loop = None  # Main event loop reference
        
        # UDS state
        self._uds_sequence_number = 0
        self._uds_pending_requests: Dict[int, asyncio.Future] = {}
        self._uds_response_queues: Dict[int, asyncio.Queue] = {}
        
        # Error handling
        self.error_callbacks: List[Callable[[CANError], None]] = []
        self.last_error = None
        
        self.logger.info(f"MazdaCANEngine initialized with {self.config.interface_type}")
    
    async def connect(self) -> bool:
        """
        Connect to CAN interface.
        
        Returns:
            True if connection successful
        """
        if self.state != CANState.DISCONNECTED:
            raise CANError(f"Cannot connect, current state: {self.state.value}")
        
        try:
            self.state = CANState.CONNECTING
            
            # Initialize interface based on type
            if self.config.interface_type == "socketcan":
                success = await self._connect_socketcan()
            elif self.config.interface_type == "pcan":
                success = await self._connect_pcan()
            elif self.config.interface_type == "vector":
                success = await self._connect_vector()
            elif self.config.interface_type == "slcan":
                success = await self._connect_slcan()
            else:
                raise CANInterfaceError(f"Unsupported interface type: {self.config.interface_type}")
            
            if success:
                self.state = CANState.CONNECTED
                self._running = True
                
                # Store event loop reference for thread-safe operations
                self.event_loop = asyncio.get_running_loop()
                
                # Start background tasks
                self.reader_task = asyncio.create_task(self._message_reader())
                self.writer_task = asyncio.create_task(self._message_writer())
                
                # Start real-time processing threads
                self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
                self._process_thread = threading.Thread(target=self._process_loop, daemon=True)
                self._receive_thread.start()
                self._process_thread.start()
                
                self.logger.info(f"CAN interface connected: {self.config.channel}")
                return True
            else:
                self.state = CANState.ERROR
                return False
                
        except Exception as e:
            self.state = CANState.ERROR
            self.logger.error(f"CAN connection failed: {e}")
            raise CANInterfaceError(f"Connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from CAN interface."""
        if self.state == CANState.DISCONNECTED:
            return
        
        self._running = False
        
        # Stop background tasks
        if self.reader_task:
            self.reader_task.cancel()
            try:
                await self.reader_task
            except asyncio.CancelledError:
                pass
        
        if self.writer_task:
            self.writer_task.cancel()
            try:
                await self.writer_task
            except asyncio.CancelledError:
                pass
        
        # Close interface
        if self.interface:
            try:
                if hasattr(self.interface, 'close'):
                    await self.interface.close()
            except Exception as e:
                self.logger.warning(f"Error closing interface: {e}")
        
        self.state = CANState.DISCONNECTED
        self.logger.info("CAN interface disconnected")
    
    async def _connect_socketcan(self) -> bool:
        """Connect to SocketCAN interface."""
        try:
            # Try to import python-can
            import can
            
            # Create bus configuration
            bus_config = {
                'interface': 'socketcan',
                'channel': self.config.channel,
                'bitrate': self.config.bitrate,
                'receive_own_messages': False,
            }
            
            # Add timing parameters if supported
            if hasattr(can, 'BitTiming'):
                bus_config.update({
                    'sjw': self.config.sjw,
                    'tseg1': self.config.tseg1,
                    'tseg2': self.config.tseg2,
                    'brp': self.config.brp,
                })
            
            self.interface = can.Bus(**bus_config)
            
            # Set up filters
            if self.filters:
                can_filters = []
                for filt in self.filters:
                    can_filters.append({
                        'can_id': filt.arbitration_id,
                        'can_mask': filt.mask,
                        'extended': filt.extended
                    })
                self.interface.set_filters(can_filters)
            
            return True
            
        except ImportError:
            self.logger.error("python-can library not found")
            return False
        except Exception as e:
            self.logger.error(f"SocketCAN connection failed: {e}")
            return False
    
    async def _connect_pcan(self) -> bool:
        """Connect to PCAN interface."""
        try:
            import can
            
            bus_config = {
                'interface': 'pcan',
                'channel': self.config.channel,
                'bitrate': self.config.bitrate,
            }
            
            self.interface = can.Bus(**bus_config)
            return True
            
        except Exception as e:
            self.logger.error(f"PCAN connection failed: {e}")
            return False
    
    async def _connect_vector(self) -> bool:
        """Connect to Vector interface."""
        try:
            import can
            
            bus_config = {
                'interface': 'vector',
                'channel': self.config.channel,
                'bitrate': self.config.bitrate,
            }
            
            self.interface = can.Bus(**bus_config)
            return True
            
        except Exception as e:
            self.logger.error(f"Vector connection failed: {e}")
            return False
    
    async def _connect_slcan(self) -> bool:
        """Connect to SLCAN interface."""
        try:
            import can
            
            bus_config = {
                'interface': 'slcan',
                'channel': self.config.channel,
                'bitrate': self.config.bitrate,
            }
            
            self.interface = can.Bus(**bus_config)
            return True
            
        except Exception as e:
            self.logger.error(f"SLCAN connection failed: {e}")
            return False
    
    def _receive_loop(self) -> None:
        """Real-time message receiving loop (threaded)."""
        while self._running:
            try:
                if self.interface and hasattr(self.interface, 'recv'):
                    message = self.interface.recv(timeout=0.1)
                    if message:
                        # Convert to our CANMessage format
                        can_msg = CANMessage(
                            arbitration_id=message.arbitration_id,
                            data=message.data,
                            dlc=message.dlc,
                            extended_id=message.is_extended_id,
                            timestamp=message.timestamp,
                            priority=self._get_priority_from_id(message.arbitration_id)
                        )
                        
                        # Add to thread queue for processing
                        try:
                            self._thread_queue.put_nowait(can_msg)
                        except queue.Full:
                            self.logger.warning("Thread queue full, dropping message")
                            
            except Exception as e:
                if self._running:  # Only log if not shutting down
                    self.logger.warning(f"Receive loop error: {e}")
    
    def _process_loop(self) -> None:
        """Real-time message processing loop (threaded)."""
        while self._running:
            try:
                # Get message from thread queue
                can_msg = self._thread_queue.get(timeout=0.1)
                
                # Update statistics
                self.stats.total_messages_received += 1
                self.stats.last_message_time = time.time()
                
                # Add to buffer
                self.message_buffer.append(can_msg)
                
                # Check filters
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
                
                self._thread_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                if self._running:
                    self.logger.warning(f"Process loop error: {e}")
    
    async def _message_reader(self) -> None:
        """Async message reader for handlers."""
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(), timeout=1.0
                )
                
                # Call registered handlers
                handlers = self.message_handlers.get(message.arbitration_id, [])
                for handler in handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(message)
                        else:
                            handler(message)
                    except Exception as e:
                        self.logger.error(f"Handler error: {e}")
                
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if self._running:
                    self.logger.error(f"Message reader error: {e}")
    
    async def _message_writer(self) -> None:
        """Async message writer (for future use)."""
        while self._running:
            await asyncio.sleep(0.1)
    
    def _get_priority_from_id(self, arbitration_id: int) -> CANPriority:
        """Determine message priority from CAN ID."""
        # Lower arbitration ID = higher priority
        if arbitration_id < 0x100:
            return CANPriority.HIGHEST
        elif arbitration_id < 0x200:
            return CANPriority.HIGH
        elif arbitration_id < 0x700:
            return CANPriority.NORMAL
        else:
            return CANPriority.LOW
    
    def _should_accept_message(self, message: CANMessage) -> bool:
        """Check if message passes all filters."""
        if not self.filters:
            return True
        
        for filt in self.filters:
            if filt.matches(message):
                return True
        
        return False
    
    async def send_message(self, message: CANMessage, 
                          credentials: Optional[SecurityCredentials] = None) -> bool:
        """
        Send CAN message.
        
        Args:
            message: CAN message to send
            credentials: Security credentials
            
        Returns:
            True if message sent successfully
        """
        if self.state != CANState.CONNECTED:
            raise CANError("Not connected to CAN interface")
        
        # Check security for restricted IDs
        if credentials and not self._check_send_security(credentials, message):
            raise CANError(f"Insufficient permissions for CAN ID {message.arbitration_id:03X}")
        
        try:
            start_time = time.time()
            
            # Convert to python-can format if needed
            if hasattr(self.interface, 'send'):
                import can
                can_msg = can.Message(
                    arbitration_id=message.arbitration_id,
                    data=message.data,
                    is_extended_id=message.extended_id,
                    is_remote_frame=False,
                    is_error_frame=False,
                )
                self.interface.send(can_msg)
            else:
                raise CANInterfaceError("Interface does not support sending")
            
            # Update statistics
            tx_time = time.time() - start_time
            self.stats.total_messages_sent += 1
            self.stats.avg_tx_time = (
                (self.stats.avg_tx_time * (self.stats.total_messages_sent - 1) + tx_time) /
                self.stats.total_messages_sent
            )
            self.stats.max_tx_time = max(self.stats.max_tx_time, tx_time)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send CAN message: {e}")
            self.stats.tx_error_count += 1
            return False
    
    def _check_send_security(self, credentials: SecurityCredentials, 
                           message: CANMessage) -> bool:
        """Check if user has permission to send to this CAN ID."""
        # Define restricted CAN IDs that require higher security
        restricted_ids = {
            0x7E0: SecurityLevel.DIAGNOSTIC,  # ECM requests
            0x7E1: SecurityLevel.DIAGNOSTIC,  # TCM requests
            0x7E2: SecurityLevel.DIAGNOSTIC,  # ABS requests
            0x7DF: SecurityLevel.DIAGNOSTIC,  # Broadcast requests
        }
        
        required_level = restricted_ids.get(message.arbitration_id, SecurityLevel.NONE)
        
        if not credentials:
            return required_level == SecurityLevel.NONE
        
        return credentials.security_level.value >= required_level.value
    
    def add_filter(self, filt: CANFilter) -> None:
        """Add message filter."""
        self.filters.append(filt)
        
        # Update interface filters if connected
        if self.interface and hasattr(self.interface, 'set_filters'):
            self._update_interface_filters()
    
    def remove_filter(self, arbitration_id: int) -> None:
        """Remove filter by arbitration ID."""
        self.filters = [f for f in self.filters if f.arbitration_id != arbitration_id]
        
        # Update interface filters if connected
        if self.interface and hasattr(self.interface, 'set_filters'):
            self._update_interface_filters()
    
    def _update_interface_filters(self) -> None:
        """Update interface hardware filters."""
        if not self.interface or not hasattr(self.interface, 'set_filters'):
            return
        
        can_filters = []
        for filt in self.filters:
            can_filters.append({
                'can_id': filt.arbitration_id,
                'can_mask': filt.mask,
                'extended': filt.extended
            })
        
        self.interface.set_filters(can_filters)
    
    def add_handler(self, arbitration_id: int, handler: Callable[[CANMessage], None]) -> None:
        """Add message handler for specific CAN ID."""
        self.message_handlers[arbitration_id].append(handler)
    
    def remove_handler(self, arbitration_id: int, handler: Callable[[CANMessage], None]) -> None:
        """Remove message handler."""
        if arbitration_id in self.message_handlers:
            try:
                self.message_handlers[arbitration_id].remove(handler)
                if not self.message_handlers[arbitration_id]:
                    del self.message_handlers[arbitration_id]
            except ValueError:
                pass
    
    def add_error_callback(self, callback: Callable[[CANError], None]) -> None:
        """Add error callback."""
        self.error_callbacks.append(callback)
    
    def _notify_error(self, error: CANError) -> None:
        """Notify all error callbacks."""
        self.last_error = error
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                self.logger.error(f"Error callback failed: {e}")
    
    async def request_message(self, arbitration_id: int, timeout: float = 2.0) -> Optional[CANMessage]:
        """
        Request specific message and wait for response.
        
        Args:
            arbitration_id: CAN ID to request
            timeout: Maximum wait time
            
        Returns:
            Response message or None if timeout
        """
        if self.state != CANState.CONNECTED:
            raise CANError("Not connected to CAN interface")
        
        # Create a simple request message
        request = CANMessage(
            arbitration_id=arbitration_id,
            data=bytes([0x00]),  # Simple request
            priority=CANPriority.NORMAL
        )
        
        # Send request
        await self.send_message(request)
        
        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check recent messages
            for msg in reversed(list(self.message_buffer)):
                if (msg.arbitration_id == arbitration_id + 8 and  # Response ID pattern
                    msg.timestamp > start_time):
                    return msg
            
            await asyncio.sleep(0.01)
        
        return None
    
    def get_recent_messages(self, count: int = 100, 
                           arbitration_id: Optional[int] = None) -> List[CANMessage]:
        """
        Get recent messages from buffer.
        
        Args:
            count: Maximum number of messages
            arbitration_id: Filter by specific CAN ID
            
        Returns:
            List of recent messages
        """
        messages = list(self.message_buffer)
        
        if arbitration_id is not None:
            messages = [msg for msg in messages if msg.arbitration_id == arbitration_id]
        
        return messages[-count:] if len(messages) > count else messages
    
    def get_statistics(self) -> CANStatistics:
        """Get current CAN statistics."""
        # Calculate current bus load
        if len(self.load_samples) > 0:
            self.stats.current_load = sum(self.load_samples) / len(self.load_samples)
        
        return self.stats
    
    def reset_statistics(self) -> None:
        """Reset all statistics."""
        self.stats = CANStatistics()
        self.message_buffer.clear()
        self.load_samples.clear()
    
    def get_mazda_id_name(self, arbitration_id: int) -> Optional[str]:
        """Get Mazda-specific name for CAN ID."""
        for name, can_id in self.MAZDA_CAN_IDS.items():
            if can_id == arbitration_id:
                return name
        return None
    
    def is_mazda_id(self, arbitration_id: int) -> bool:
        """Check if CAN ID is Mazda-specific."""
        return arbitration_id in self.MAZDA_CAN_IDS.values()
    
    async def send_mazda_request(self, module: str, service_id: int, 
                                data: Optional[bytes] = None,
                                credentials: Optional[SecurityCredentials] = None) -> bool:
        """
        Send request to specific Mazda module.
        
        Args:
            module: Module name (e.g., "ECM", "TCM", "ABS")
            service_id: Service ID for request
            data: Optional data bytes
            credentials: Security credentials
            
        Returns:
            True if request sent successfully
        """
        request_id_key = f"{module.upper()}_REQUEST"
        response_id_key = f"{module.upper()}_RESPONSE"
        
        if request_id_key not in self.MAZDA_CAN_IDS:
            raise ValueError(f"Unknown module: {module}")
        
        request_id = self.MAZDA_CAN_IDS[request_id_key]
        
        # Build request data
        request_data = bytes([service_id])
        if data:
            request_data += data
        
        message = CANMessage(
            arbitration_id=request_id,
            data=request_data,
            priority=CANPriority.HIGH
        )
        
        return await self.send_message(message, credentials)
    
    async def wait_for_mazda_response(self, module: str, timeout: float = 2.0):
        """
        Wait for response from specific Mazda module.
        
        Args:
            module: Module name (e.g., "ECM", "TCM", "ABS")
            timeout: Maximum wait time
            
        Returns:
            Response message or None if timeout
        """
        response_id = self.MAZDA_CAN_IDS.get(f"{module}_RESPONSE")
        if not response_id:
            self.logger.error(f"Unsupported module: {module}")
            return None
            
        try:
            return await asyncio.wait_for(
                self.request_message(response_id, timeout=timeout),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for response from {module}")
            return None
            
    # ===== UDS (Unified Diagnostic Services) Methods =====
    
    async def send_diagnostic_request(
        self,
        request: UDSRequest,
        response_id: Optional[int] = None,
        timeout: Optional[float] = None,
        retries: int = 3,
        credentials: Optional[SecurityCredentials] = None
    ) -> Tuple[Optional[UDSResponse], Optional[CANMessage]]:
        """
        Send a UDS diagnostic request and wait for the response.
        
        Args:
            request: UDS request to send
            response_id: Expected response CAN ID (None for default)
            timeout: Maximum time to wait for response (seconds)
            retries: Number of retry attempts
            credentials: Security credentials if required
            
        Returns:
            Tuple of (UDSResponse, raw CANMessage) or (None, None) on failure
        """
        if self.state != CANState.CONNECTED:
            raise CANError("Not connected to CAN interface")
        
        timeout = timeout or self.UDS_DEFAULT_TIMEOUT
        
        # Determine response ID if not provided
        if response_id is None and request.response_id is not None:
            response_id = request.response_id
        
        # Build the request data with padding
        request_data = self._pad_to_length(request.build(), 8)
        
        # Create CAN message
        message = CANMessage(
            arbitration_id=request.service_id,  # Use service ID as arbitration ID for simplicity
            data=request_data,
            priority=CANPriority.HIGH
        )
        
        # Try sending the request with retries
        last_error = None
        for attempt in range(max(1, retries)):
            try:
                # Send the request
                if not await self.send_message(message, credentials):
                    continue
                
                # If no response expected, return success
                if response_id is None or request.suppress_positive_response:
                    return UDSResponse(
                        service_id=request.service_id,
                        negative_response_code=UDSNegativeResponseCode.POSITIVE_RESPONSE
                    ), None
                
                # Wait for response
                response = await self.wait_for_response(
                    response_id=response_id,
                    timeout=timeout,
                    filter_func=lambda msg: self._is_matching_response(msg, request)
                )
                
                if response:
                    try:
                        uds_response = UDSResponse.from_bytes(response.data)
                        return uds_response, response
                    except ValueError as e:
                        self.logger.error(f"Failed to parse UDS response: {e}")
                        last_error = e
                        continue
                
                # If we get here, either no response or invalid response
                self.logger.warning(f"No valid response received (attempt {attempt + 1}/{retries})")
                
            except Exception as e:
                last_error = e
                self.logger.error(f"Diagnostic request failed (attempt {attempt + 1}/{retries}): {e}")
                await asyncio.sleep(0.1)  # Small delay between retries
        
        self.logger.error(f"All retries exhausted for UDS service 0x{request.service_id:02X}")
        if last_error:
            self._notify_error(CANError(f"UDS request failed: {last_error}"))
        return None, None

    async def receive(
        self,
        response_id: int,
        timeout: float = 2.0,
        filter_func: Optional[Callable[[CANMessage], bool]] = None
    ) -> Optional[CANMessage]:
        """
        Wait for a specific CAN message with optional filtering.
        
        Args:
            response_id: Expected CAN ID of the response
            timeout: Maximum time to wait (seconds)
            filter_func: Optional function to filter messages (returns True to accept)
                
        Returns:
            CANMessage if received, None on timeout
        """
        return await self.wait_for_response(response_id, timeout, filter_func)

    async def wait_for_response(
        self,
        response_id: int,
        timeout: float = 2.0,
        filter_func: Optional[Callable[[CANMessage], bool]] = None
    ) -> Optional[CANMessage]:
        """
        Wait for a specific CAN message with optional filtering.
        
        Args:
            response_id: Expected CAN ID of the response
            timeout: Maximum time to wait (seconds)
            filter_func: Optional function to filter messages (returns True to accept)
                
        Returns:
            CANMessage if received, None on timeout
        """
        if self.state != CANState.CONNECTED:
            raise CANError("Not connected to CAN interface")
        
        start_time = time.time()
        remaining = timeout
        
        while remaining > 0:
            # Check for matching messages in buffer
            for msg in reversed(list(self.message_buffer)):
                if (msg.arbitration_id == response_id and 
                    (filter_func is None or filter_func(msg))):
                    return msg
            
            # Wait for new messages
            try:
                await asyncio.wait_for(
                    asyncio.shield(self.message_queue.get()),
                    timeout=min(0.1, remaining)
                )
            except asyncio.TimeoutError:
                pass
            
            remaining = timeout - (time.time() - start_time)
        
        return None

    def _is_matching_response(self, msg: CANMessage, request: UDSRequest) -> bool:
        """Check if a CAN message is a valid response to a UDS request."""
        try:
            if not msg.data:
                return False
                
            # Check for negative response
            if msg.data[0] == 0x7F and len(msg.data) >= 3:
                return msg.data[1] == request.service_id
                
            # Check for positive response
            if msg.data[0] == (request.service_id | 0x40):
                return True
                
            # Check for subfunction response
            if (request.subfunction is not None and 
                len(msg.data) > 1 and 
                msg.data[0] == (request.service_id | 0x40) and 
                msg.data[1] == request.subfunction):
                return True
                
            return False
        except Exception:
            return False

    def _pad_to_length(self, data: bytes, length: int, pad_byte: int = 0x55) -> bytes:
        """Pad data to specified length with given padding byte."""
        if len(data) >= length:
            return data[:length]
        return data + bytes([pad_byte] * (length - len(data)))

    # ===== UDS Service Wrappers =====
    
    async def read_data_by_identifier(
        self,
        data_identifier: int,
        response_id: Optional[int] = None,
        timeout: Optional[float] = None,
        credentials: Optional[SecurityCredentials] = None
    ) -> Tuple[Optional[UDSResponse], Optional[CANMessage]]:
        """
        UDS Read Data By Identifier (0x22) service.
        
        Args:
            data_identifier: 16-bit data identifier
            response_id: Expected response CAN ID (None for default)
            timeout: Response timeout in seconds
            credentials: Security credentials if required
            
        Returns:
            Tuple of (UDSResponse, raw CANMessage) or (None, None) on failure
        """
        request = UDSRequest(
            service_id=UDSService.READ_DATA_BY_IDENTIFIER,
            data=struct.pack('>H', data_identifier),  # Big-endian 16-bit
            response_id=response_id
        )
        return await self.send_diagnostic_request(
            request=request,
            response_id=response_id,
            timeout=timeout,
            credentials=credentials
        )

    async def write_data_by_identifier(
        self,
        data_identifier: int,
        data: bytes,
        response_id: Optional[int] = None,
        timeout: Optional[float] = None,
        credentials: Optional[SecurityCredentials] = None
    ) -> Tuple[Optional[UDSResponse], Optional[CANMessage]]:
        """
        UDS Write Data By Identifier (0x2E) service.
        
        Args:
            data_identifier: 16-bit data identifier
            data: Data to write
            response_id: Expected response CAN ID (None for default)
            timeout: Response timeout in seconds
            credentials: Security credentials if required
            
        Returns:
            Tuple of (UDSResponse, raw CANMessage) or (None, None) on failure
        """
        request = UDSRequest(
            service_id=UDSService.WRITE_DATA_BY_IDENTIFIER,
            data=struct.pack('>H', data_identifier) + data,
            response_id=response_id
        )
        return await self.send_diagnostic_request(
            request=request,
            response_id=response_id,
            timeout=timeout,
            credentials=credentials
        )

    async def diagnostic_session_control(
        self,
        session_type: int,
        response_id: Optional[int] = None,
        timeout: Optional[float] = None,
        credentials: Optional[SecurityCredentials] = None
    ) -> Tuple[Optional[UDSResponse], Optional[CANMessage]]:
        """
        UDS Diagnostic Session Control (0x10) service.
        
        Args:
            session_type: Session type (1=default, 2=programming, 3=extended)
            response_id: Expected response CAN ID (None for default)
            timeout: Response timeout in seconds
            credentials: Security credentials if required
            
        Returns:
            Tuple of (UDSResponse, raw CANMessage) or (None, None) on failure
        """
        request = UDSRequest(
            service_id=UDSService.DIAGNOSTIC_SESSION_CONTROL,
            subfunction=session_type,
            response_id=response_id
        )
        return await self.send_diagnostic_request(
            request=request,
            response_id=response_id,
            timeout=timeout,
            credentials=credentials
        )

    async def security_access(
        self,
        security_level: int,
        key: Optional[bytes] = None,
        response_id: Optional[int] = None,
        timeout: Optional[float] = None,
        credentials: Optional[SecurityCredentials] = None
    ) -> Tuple[Optional[UDSResponse], Optional[CANMessage]]:
        """
        UDS Security Access (0x27) service.
        
        Args:
            security_level: Security level (0x01-0x7F for request seed, 0x41-0x7F for send key)
            key: Security key (for send key subfunction)
            response_id: Expected response CAN ID (None for default)
            timeout: Response timeout in seconds
            credentials: Security credentials if required
            
        Returns:
            Tuple of (UDSResponse, raw CANMessage) or (None, None) on failure
        """
        if key is None:
            # Request seed
            request = UDSRequest(
                service_id=UDSService.SECURITY_ACCESS,
                subfunction=security_level,
                response_id=response_id
            )
        else:
            # Send key
            request = UDSRequest(
                service_id=UDSService.SECURITY_ACCESS,
                subfunction=security_level + 0x40,  # Add 0x40 for key subfunction
                data=key,
                response_id=response_id
            )
        
        return await self.send_diagnostic_request(
            request=request,
            response_id=response_id,
            timeout=timeout,
            credentials=credentials
        )

    async def tester_present(
        self,
        suppress_response: bool = True,
        response_id: Optional[int] = None,
        timeout: Optional[float] = None,
        credentials: Optional[SecurityCredentials] = None
    ) -> Tuple[Optional[UDSResponse], Optional[CANMessage]]:
        """
        UDS Tester Present (0x3E) service.
        
        Args:
            suppress_response: If True, suppress positive response
            response_id: Expected response CAN ID (None for default)
            timeout: Response timeout in seconds
            credentials: Security credentials if required
            
        Returns:
            Tuple of (UDSResponse, raw CANMessage) or (None, None) on failure
        """
        request = UDSRequest(
            service_id=UDSService.TESTER_PRESENT,
            subfunction=0x00,
            suppress_positive_response=suppress_response,
            response_id=response_id
        )
        return await self.send_diagnostic_request(
            request=request,
            response_id=response_id,
            timeout=timeout,
            credentials=credentials
        )

    async def clear_diagnostic_information(
        self,
        group_of_dtc: int = 0xFFFFFF,  # Default: all DTCs
        response_id: Optional[int] = None,
        timeout: Optional[float] = None,
        credentials: Optional[SecurityCredentials] = None
    ) -> Tuple[Optional[UDSResponse], Optional[CANMessage]]:
        """
        UDS Clear Diagnostic Information (0x14) service.
        
        Args:
            group_of_dtc: Group of DTCs to clear (0xFFFFFF = all DTCs)
            response_id: Expected response CAN ID (None for default)
            timeout: Response timeout in seconds
            credentials: Security credentials if required
            
        Returns:
            Tuple of (UDSResponse, raw CANMessage) or (None, None) on failure
        """
        request = UDSRequest(
            service_id=UDSService.CLEAR_DIAGNOSTIC_INFORMATION,
            data=struct.pack('>I', group_of_dtc)[1:],  # 3-byte DTC group
            response_id=response_id
        )
        return await self.send_diagnostic_request(
            request=request,
            response_id=response_id,
            timeout=timeout,
            credentials=credentials
        )

    async def read_dtc_information(
        self,
        report_type: int,
        dtc_status_mask: Optional[int] = None,
        response_id: Optional[int] = None,
        timeout: Optional[float] = None,
        credentials: Optional[SecurityCredentials] = None
    ) -> Tuple[Optional[UDSResponse], Optional[CANMessage]]:
        """
        UDS Read DTC Information (0x19) service.
        
        Args:
            report_type: Type of DTC report (0x01-0x0A, 0x42, 0x55, 0x56, 0x61, 0x71, 0x86, 0x87, 0x92)
            dtc_status_mask: DTC status mask (only for certain report types)
            response_id: Expected response CAN ID (None for default)
            timeout: Response timeout in seconds
            credentials: Security credentials if required
            
        Returns:
            Tuple of (UDSResponse, raw CANMessage) or (None, None) on failure
        """
        if dtc_status_mask is not None:
            request_data = bytes([report_type, dtc_status_mask])
        else:
            request_data = bytes([report_type])
            
        request = UDSRequest(
            service_id=UDSService.READ_DTC_INFORMATION,
            data=request_data,
            response_id=response_id
        )
        return await self.send_diagnostic_request(
            request=request,
            response_id=response_id,
            timeout=timeout,
            credentials=credentials
        )

    def get_supported_modules(self) -> List[str]:
        """Get list of supported Mazda modules."""
        modules = set()
        for name in self.MAZDA_CAN_IDS.keys():
            if name.endswith("_REQUEST"):
                module_name = name.replace("_REQUEST", "")
                modules.add(module_name)
        return sorted(list(modules))
    
    async def monitor_bus_load(self, duration: float = 1.0) -> float:
        """
        Monitor CAN bus load for specified duration.
        
        Args:
            duration: Monitoring duration in seconds
            
        Returns:
            Average bus load percentage
        """
        if self.state != CANState.CONNECTED:
            return 0.0
        
        start_time = time.time()
        message_count = 0
        
        while time.time() - start_time < duration:
            # Count messages in last 100ms window
            current_time = time.time()
            recent_messages = [
                msg for msg in self.message_buffer
                if current_time - msg.timestamp < 0.1
            ]
            message_count += len(recent_messages)
            await asyncio.sleep(0.1)
        
        # Calculate load (simplified estimation)
        # Assumes 500kbps, 8 bytes data + header bits per message
        bits_per_message = 8 * 8 + 64  # 64 bits for overhead
        total_bits = message_count * bits_per_message
        capacity_bits = self.config.bitrate * duration
        load_percentage = (total_bits / capacity_bits) * 100
        
        # Update statistics
        self.load_samples.append(min(load_percentage, 100.0))
        self.stats.current_load = load_percentage
        self.stats.peak_load = max(self.stats.peak_load, load_percentage)
        
        return load_percentage
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.state != CANState.DISCONNECTED:
            self.logger.warning("CANEngine deleted while still connected")
