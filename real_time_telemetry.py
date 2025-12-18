"""
RealTimeTelemetry - Hybrid CAN/OBD telemetry collection system.
Collects high-frequency data via CAN events and lower-frequency data via OBD polling.
Uses circular buffering and batch database writes to prevent I/O blocking.
"""

import asyncio
import time
import threading
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import logging
import json
from concurrent.futures import ThreadPoolExecutor

from models import (
    TelemetryData, CANMessage, OBDPacket, VehicleState,
    SecurityLevel, SecurityCredentials, LogEntry
)
from mazda_obd_service import MazdaOBDService, OBDCommandMode
from mazda_can_engine import MazdaCANEngine, CANFilter
from secure_database import SecureDatabase
from mazda_security_core import MazdaSecurityCore


class TelemetryState(Enum):
    """Telemetry system states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class TelemetryConfig:
    """Telemetry collection configuration."""
    # CAN-based high-frequency data
    can_enabled: bool = True
    can_buffer_size: int = 1000
    can_batch_size: int = 100
    
    # OBD-based lower-frequency data
    obd_enabled: bool = True
    obd_poll_interval: float = 1.0  # seconds
    
    # Sampling rates (Hz)
    rpm_sample_rate: float = 50.0
    boost_sample_rate: float = 25.0
    throttle_sample_rate: float = 20.0
    temp_sample_rate: float = 1.0
    pressure_sample_rate: float = 2.0
    
    # Database settings
    db_enabled: bool = True
    db_batch_interval: float = 0.5  # seconds
    db_batch_size: int = 50
    
    # Performance settings
    max_cpu_usage: float = 80.0  # percentage
    memory_limit_mb: int = 100
    
    # Data filtering
    enable_filtering: bool = True
    outlier_threshold: float = 3.0  # standard deviations


@dataclass
class TelemetryStats:
    """Telemetry collection statistics."""
    start_time: float = field(default_factory=time.time)
    total_samples: int = 0
    can_samples: int = 0
    obd_samples: int = 0
    database_writes: int = 0
    errors: int = 0
    avg_sample_rate: float = 0.0
    buffer_overruns: int = 0
    last_sample_time: float = 0.0
    
    @property
    def uptime_seconds(self) -> float:
        """Get system uptime in seconds."""
        return time.time() - self.start_time
    
    @property
    def can_sample_rate(self) -> float:
        """Get CAN sample rate."""
        if self.uptime_seconds > 0:
            return self.can_samples / self.uptime_seconds
        return 0.0
    
    @property
    def obd_sample_rate(self) -> float:
        """Get OBD sample rate."""
        if self.uptime_seconds > 0:
            return self.obd_samples / self.uptime_seconds
        return 0.0


class TelemetryError(Exception):
    """Telemetry system errors."""
    pass


class TelemetryConfigError(TelemetryError):
    """Configuration errors."""
    pass


class RealTimeTelemetry:
    """
    Real-time telemetry collection system with hybrid CAN/OBD approach.
    Uses circular buffering and async database operations for optimal performance.
    """
    
    # High-frequency CAN IDs to monitor
    CAN_TELEMETRY_IDS = {
        "ENGINE_RPM": 0x280,
        "VEHICLE_SPEED": 0x281,
        "THROTTLE_POSITION": 0x250,
        "PEDAL_POSITION": 0x251,
        "BOOST_PRESSURE": 0x311,
        "MAP_SENSOR": 0x310,
        "MAF_FLOW": 0x290,
        "WHEEL_SPEED_FL": 0x1A0,
        "WHEEL_SPEED_FR": 0x1A1,
        "WHEEL_SPEED_RL": 0x1A2,
        "WHEEL_SPEED_RR": 0x1A3,
    }
    
    # OBD PIDs for lower-frequency data
    OBD_TELEMETRY_PIDS = {
        "COOLANT_TEMP": "05",
        "OIL_TEMP": "5C",  # Mazda-specific
        "IAT_TEMP": "0F",
        "FUEL_PRESSURE": "0A",
        "OIL_PRESSURE": "A6",  # Mazda-specific
        "FUEL_TRIM_BANK1": "06",
        "FUEL_TRIM_BANK2": "08",
        "AFR": "44",  # Air-fuel ratio
        "IGNITION_TIMING": "0E",
        "KNOCK_RETARD": "A5",  # Mazda-specific
        "LOAD": "04",
        "GEAR": "A7",  # Mazda-specific
    }
    
    def __init__(self, config: Optional[TelemetryConfig] = None):
        """
        Initialize telemetry system.
        
        Args:
            config: Telemetry configuration
        """
        self.config = config or TelemetryConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.state = TelemetryState.STOPPED
        self.session_id: Optional[str] = None
        self.current_credentials: Optional[SecurityCredentials] = None
        
        # Communication interfaces (to be injected)
        self.obd_service: Optional[MazdaOBDService] = None
        self.can_engine: Optional[MazdaCANEngine] = None
        self.database: Optional[SecureDatabase] = None
        
        # Data collection
        self.telemetry_buffer: deque = deque(maxlen=self.config.can_buffer_size)
        self.latest_telemetry = TelemetryData()
        
        # CAN message processing
        self.can_handlers: Dict[int, Callable] = {}
        self.can_filters: List[CANFilter] = []
        
        # OBD polling
        self.obd_task: Optional[asyncio.Task] = None
        self.obd_last_poll = 0.0
        
        # Database batch processing
        self.db_batch_buffer: List[TelemetryData] = []
        self.db_task: Optional[asyncio.Task] = None
        self.db_last_write = 0.0
        
        # Event loop reference for thread-safe operations
        self._main_event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._db_queue: Optional[asyncio.Queue] = None
        self._db_processor_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = TelemetryStats()
        
        # Thread pool for database operations
        self.db_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="telemetry_db")
        
        # Data validation and filtering
        self.data_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        self.logger.info("RealTimeTelemetry initialized")
    
    def set_obd_service(self, obd_service: MazdaOBDService) -> None:
        """Set OBD service interface."""
        self.obd_service = obd_service
        self.logger.info("OBD service interface set")
    
    def set_can_engine(self, can_engine: MazdaCANEngine) -> None:
        """Set CAN engine interface."""
        self.can_engine = can_engine
        self._setup_can_handlers()
        self.logger.info("CAN engine interface set")
    
    def set_database(self, database: SecureDatabase) -> None:
        """Set database interface."""
        self.database = database
        self.logger.info("Database interface set")
    
    def set_credentials(self, credentials: SecurityCredentials) -> None:
        """Set security credentials."""
        self.current_credentials = credentials
        self.logger.info(f"Credentials set for user: {credentials.username}")
    
    def _setup_can_handlers(self) -> None:
        """Set up CAN message handlers for telemetry."""
        if not self.can_engine:
            return
        
        # Register handlers for high-frequency data
        can_handlers = {
            0x280: self._handle_engine_rpm,
            0x281: self._handle_vehicle_speed,
            0x250: self._handle_throttle_position,
            0x251: self._handle_pedal_position,
            0x311: self._handle_boost_pressure,
            0x310: self._handle_map_sensor,
            0x290: self._handle_maf_flow,
        }
        
        for can_id, handler in can_handlers.items():
            self.can_engine.add_handler(can_id, handler)
            self.can_handlers[can_id] = handler
        
        # Add CAN filters for telemetry IDs
        for can_id in self.CAN_TELEMETRY_IDS.values():
            filt = CANFilter(
                arbitration_id=can_id,
                mask=0x7FF,  # Standard 11-bit mask
                description=f"Telemetry CAN ID 0x{can_id:03X}"
            )
            self.can_filters.append(filt)
            self.can_engine.add_filter(filt)
    
    # CAN message handlers
    def _handle_engine_rpm(self, message: CANMessage) -> None:
        """Handle engine RPM CAN message."""
        try:
            if len(message.data) >= 2:
                # Parse RPM (typical format: 2 bytes, big-endian)
                rpm_raw = (message.data[0] << 8) | message.data[1]
                rpm = rpm_raw * 0.25  # Scaling factor
                
                self._update_telemetry_field("rpm", rpm)
                self.stats.can_samples += 1
                
        except Exception as e:
            self.logger.error(f"Failed to parse RPM CAN message: {e}")
            self.stats.errors += 1
    
    def _handle_vehicle_speed(self, message: CANMessage) -> None:
        """Handle vehicle speed CAN message."""
        try:
            if len(message.data) >= 1:
                speed = message.data[0] * 0.5  # km/h scaling
                self._update_telemetry_field("vehicle_speed", speed)
                self.stats.can_samples += 1
                
        except Exception as e:
            self.logger.error(f"Failed to parse vehicle speed CAN message: {e}")
            self.stats.errors += 1
    
    def _handle_throttle_position(self, message: CANMessage) -> None:
        """Handle throttle position CAN message."""
        try:
            if len(message.data) >= 1:
                throttle = message.data[0] * 100.0 / 255.0  # Percentage
                self._update_telemetry_field("throttle_position", throttle)
                self.stats.can_samples += 1
                
        except Exception as e:
            self.logger.error(f"Failed to parse throttle position CAN message: {e}")
            self.stats.errors += 1
    
    def _handle_pedal_position(self, message: CANMessage) -> None:
        """Handle accelerator pedal position CAN message."""
        try:
            if len(message.data) >= 1:
                pedal = message.data[0] * 100.0 / 255.0  # Percentage
                self._update_telemetry_field("pedal_position", pedal)
                self.stats.can_samples += 1
                
        except Exception as e:
            self.logger.error(f"Failed to parse pedal position CAN message: {e}")
            self.stats.errors += 1
    
    def _handle_boost_pressure(self, message: CANMessage) -> None:
        """Handle boost pressure CAN message."""
        try:
            if len(message.data) >= 2:
                # Parse boost pressure (typical Mazda format)
                boost_raw = (message.data[0] << 8) | message.data[1]
                boost = boost_raw * 0.001 - 14.7  # Convert to psi gauge pressure
                self._update_telemetry_field("boost_pressure", boost)
                self.stats.can_samples += 1
                
        except Exception as e:
            self.logger.error(f"Failed to parse boost pressure CAN message: {e}")
            self.stats.errors += 1
    
    def _handle_map_sensor(self, message: CANMessage) -> None:
        """Handle MAP sensor CAN message."""
        try:
            if len(message.data) >= 2:
                map_raw = (message.data[0] << 8) | message.data[1]
                map_pressure = map_raw * 0.01  # kPa
                self._update_telemetry_field("map", map_pressure)
                self.stats.can_samples += 1
                
        except Exception as e:
            self.logger.error(f"Failed to parse MAP sensor CAN message: {e}")
            self.stats.errors += 1
    
    def _handle_maf_flow(self, message: CANMessage) -> None:
        """Handle MAF flow CAN message."""
        try:
            if len(message.data) >= 2:
                maf_raw = (message.data[0] << 8) | message.data[1]
                maf = maf_raw * 0.01  # g/s
                self._update_telemetry_field("maf", maf)
                self.stats.can_samples += 1
                
        except Exception as e:
            self.logger.error(f"Failed to parse MAF flow CAN message: {e}")
            self.stats.errors += 1
    
    def _update_telemetry_field(self, field_name: str, value: float) -> None:
        """Update telemetry field with validation and filtering."""
        try:
            # Apply filtering if enabled
            if self.config.enable_filtering:
                if not self._validate_data_point(field_name, value):
                    return  # Filter out outliers
            
            # Update latest telemetry
            setattr(self.latest_telemetry, field_name, value)
            self.latest_telemetry.timestamp = time.time()
            
            # Add to circular buffer
            telemetry_copy = TelemetryData()
            telemetry_copy.__dict__.update(self.latest_telemetry.__dict__)
            self.telemetry_buffer.append(telemetry_copy)
            
            # Update statistics
            self.stats.total_samples += 1
            self.stats.last_sample_time = time.time()
            
            # Calculate average sample rate
            if self.stats.uptime_seconds > 0:
                self.stats.avg_sample_rate = self.stats.total_samples / self.stats.uptime_seconds
            
        except Exception as e:
            self.logger.error(f"Failed to update telemetry field {field_name}: {e}")
            self.stats.errors += 1
    
    def _validate_data_point(self, field_name: str, value: float) -> bool:
        """Validate data point using statistical filtering."""
        try:
            history = self.data_history[field_name]
            
            # Add current value to history
            history.append(value)
            
            # Need enough samples for statistics
            if len(history) < 10:
                return True
            
            # Calculate mean and standard deviation
            values = list(history)
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            
            # Check if value is within threshold
            if std_dev > 0:
                z_score = abs(value - mean) / std_dev
                return z_score <= self.config.outlier_threshold
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation failed for {field_name}: {e}")
            return True  # Allow data on validation error
    
    async def start_collection(self, session_id: Optional[str] = None) -> bool:
        """
        Start telemetry data collection.
        
        Args:
            session_id: Optional session identifier
            
        Returns:
            True if collection started successfully
        """
        if self.state != TelemetryState.STOPPED:
            self.logger.warning(f"Cannot start telemetry, current state: {self.state.value}")
            return False
        
        try:
            self.state = TelemetryState.STARTING
            
            # Validate interfaces
            if not self.obd_service or not self.can_engine:
                raise TelemetryError("OBD service and CAN engine must be set")
            
            # Generate session ID if not provided
            if not session_id:
                session_id = f"telemetry_{int(time.time())}"
            self.session_id = session_id
            
            # Store event loop reference for thread-safe operations
            self._main_event_loop = asyncio.get_running_loop()
            
            # Initialize database queue and processor
            if self.config.db_enabled and self.database:
                self._db_queue = asyncio.Queue()
                self._db_processor_task = asyncio.create_task(self._process_db_queue())
            
            # Start OBD polling task
            if self.config.obd_enabled:
                self.obd_task = asyncio.create_task(self._obd_polling_loop())
            
            # Start database batch writing task
            if self.config.db_enabled and self.database:
                self.db_task = asyncio.create_task(self._db_batch_loop())
            
            self.state = TelemetryState.RUNNING
            self.stats.start_time = time.time()
            
            self.logger.info(f"Telemetry collection started: {session_id}")
            return True
            
        except Exception as e:
            self.state = TelemetryState.ERROR
            self.logger.error(f"Failed to start telemetry collection: {e}")
            return False
    
    async def stop_collection(self) -> bool:
        """Stop telemetry data collection."""
        if self.state == TelemetryState.STOPPED:
            return True
        
        try:
            self.state = TelemetryState.STOPPED
            
            # Cancel background tasks
            if self.obd_task:
                self.obd_task.cancel()
                try:
                    await self.obd_task
                except asyncio.CancelledError:
                    pass
            
            if self.db_task:
                self.db_task.cancel()
                try:
                    await self.db_task
                except asyncio.CancelledError:
                    pass
            
            if self._db_processor_task:
                self._db_processor_task.cancel()
                try:
                    await self._db_processor_task
                except asyncio.CancelledError:
                    pass
            
            # Flush remaining data to database
            if self.config.db_enabled and self.database and self.db_batch_buffer:
                await self._flush_to_database()
            
            # Flush database queue
            if self._db_queue:
                await self._flush_db_queue()
            
            # Clear event loop reference
            self._main_event_loop = None
            
            self.logger.info("Telemetry collection stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping telemetry collection: {e}")
            return False
    
    async def _obd_polling_loop(self) -> None:
        """OBD data polling loop."""
        while self.state == TelemetryState.RUNNING:
            try:
                # Check if it's time to poll
                current_time = time.time()
                if current_time - self.obd_last_poll >= self.config.obd_poll_interval:
                    await self._poll_obd_data()
                    self.obd_last_poll = current_time
                
                await asyncio.sleep(0.1)  # Small sleep to prevent busy loop
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"OBD polling loop error: {e}")
                self.stats.errors += 1
                await asyncio.sleep(1.0)  # Wait before retry
    
    async def _poll_obd_data(self) -> None:
        """Poll OBD data for lower-frequency parameters."""
        try:
            # Poll each OBD PID
            for param_name, pid in self.OBD_TELEMETRY_PIDS.items():
                try:
                    # Read PID value
                    value = await self.obd_service.read_pid(
                        pid, 
                        mazda_specific=pid.startswith("A"),
                        credentials=self.current_credentials
                    )
                    
                    # Update telemetry
                    field_name = self._map_obd_pid_to_field(param_name)
                    if field_name:
                        self._update_telemetry_field(field_name, value)
                    
                    self.stats.obd_samples += 1
                    
                except Exception as e:
                    self.logger.warning(f"Failed to read OBD PID {pid}: {e}")
                    self.stats.errors += 1
                
                # Small delay between PIDs
                await asyncio.sleep(0.01)
                
        except Exception as e:
            self.logger.error(f"OBD polling error: {e}")
            self.stats.errors += 1
    
    def _map_obd_pid_to_field(self, pid_name: str) -> Optional[str]:
        """Map OBD PID name to telemetry field."""
        mapping = {
            "COOLANT_TEMP": "ect",
            "OIL_TEMP": "oil_pressure",  # Will be updated later
            "IAT_TEMP": "iat",
            "FUEL_PRESSURE": "fuel_pressure",
            "OIL_PRESSURE": "oil_pressure",
            "FUEL_TRIM_BANK1": "stft",
            "FUEL_TRIM_BANK2": "ltft",
            "AFR": "afr",
            "IGNITION_TIMING": "timing_advance",
            "KNOCK_RETARD": "knock_retard",
            "LOAD": "load",
            "GEAR": "gear",
        }
        return mapping.get(pid_name)
    
    async def _db_batch_loop(self) -> None:
        """Database batch writing loop."""
        while self.state == TelemetryState.RUNNING:
            try:
                current_time = time.time()
                
                # Check if it's time to write batch
                if (current_time - self.db_last_write >= self.config.db_batch_interval or
                    len(self.db_batch_buffer) >= self.config.db_batch_size):
                    
                    await self._flush_to_database()
                    self.db_last_write = current_time
                
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Database batch loop error: {e}")
                self.stats.errors += 1
                await asyncio.sleep(1.0)
    
    async def _flush_to_database(self) -> None:
        """Flush telemetry buffer to database."""
        if not self.database or not self.db_batch_buffer:
            return
        
        try:
            # Copy buffer and clear
            telemetry_batch = self.db_batch_buffer.copy()
            self.db_batch_buffer.clear()
            
            # Write to database in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                self.db_executor,
                self._write_batch_to_database_sync,
                telemetry_batch
            )
            
            self.stats.database_writes += len(telemetry_batch)
            
        except Exception as e:
            self.logger.error(f"Failed to flush to database: {e}")
            self.stats.errors += 1
    
    def _write_batch_to_database_sync(self, telemetry_batch: List[TelemetryData]) -> None:
        """Synchronous database write for thread pool."""
        try:
            # Use synchronous database calls directly in thread pool
            for telemetry in telemetry_batch:
                # Create a new synchronous database method call
                self._save_telemetry_sync(telemetry)
        except Exception as e:
            self.logger.error(f"Synchronous database write failed: {e}")
    
    def _save_telemetry_sync(self, telemetry: TelemetryData) -> None:
        """Synchronous telemetry save method."""
        if not self.database or not self.session_id:
            return
        
        try:
            # Use the stored event loop reference from start_collection
            if hasattr(self, '_main_event_loop') and self._main_event_loop and not self._main_event_loop.is_closed():
                # Add telemetry to queue for async processing
                asyncio.run_coroutine_threadsafe(
                    self._db_queue.put(telemetry),
                    self._main_event_loop
                )
            else:
                # Fallback: queue is not available, skip this write
                self.logger.warning("Event loop not available, skipping telemetry write")
                
        except Exception as e:
            self.logger.error(f"Failed to queue telemetry for saving: {e}")
    
    async def _process_db_queue(self) -> None:
        """Background task to process database queue."""
        while self.state == TelemetryState.RUNNING:
            try:
                # Get telemetry from queue with timeout
                try:
                    telemetry = await asyncio.wait_for(self._db_queue.get(), timeout=1.0)
                    
                    # Save to database
                    await self.database.save_telemetry_data(self.session_id, telemetry)
                    
                    # Mark task as done
                    self._db_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # No items in queue, continue loop
                    continue
                
            except Exception as e:
                self.logger.error(f"Failed to process database queue item: {e}")
    
    async def _flush_db_queue(self) -> None:
        """Flush all items in database queue."""
        if not self._db_queue:
            return
        
        # Drain the queue without waiting
        while not self._db_queue.empty():
            try:
                telemetry = self._db_queue.get_nowait()
                await self.database.save_telemetry_data(self.session_id, telemetry)
                self._db_queue.task_done()
            except asyncio.QueueEmpty:
                break
            except Exception as e:
                self.logger.error(f"Failed to flush queue item: {e}")
    
    def get_latest_telemetry(self) -> TelemetryData:
        """Get latest telemetry data."""
        return self.latest_telemetry
    
    def get_telemetry_history(self, count: int = 100) -> List[TelemetryData]:
        """Get recent telemetry history."""
        return list(self.telemetry_buffer)[-count:]
    
    def get_statistics(self) -> TelemetryStats:
        """Get telemetry collection statistics."""
        return self.stats
    
    def get_current_state(self) -> TelemetryState:
        """Get current telemetry state."""
        return self.state
    
    def is_collecting(self) -> bool:
        """Check if telemetry is actively collecting."""
        return self.state == TelemetryState.RUNNING
    
    async def get_session_data(self, session_id: Optional[str] = None,
                              limit: int = 1000) -> List[TelemetryData]:
        """
        Get stored telemetry data for session.
        
        Args:
            session_id: Session ID (uses current session if None)
            limit: Maximum number of records
            
        Returns:
            List of telemetry data
        """
        if not self.database:
            return []
        
        target_session_id = session_id or self.session_id
        if not target_session_id:
            return []
        
        try:
            return await self.database.get_telemetry_data(target_session_id, limit)
        except Exception as e:
            self.logger.error(f"Failed to get session data: {e}")
            return []
    
    def configure_sampling_rates(self, rates: Dict[str, float]) -> None:
        """
        Configure sampling rates for different data types.
        
        Args:
            rates: Dictionary of field names to sampling rates (Hz)
        """
        for field_name, rate in rates.items():
            if hasattr(self.config, f"{field_name}_sample_rate"):
                setattr(self.config, f"{field_name}_sample_rate", rate)
                self.logger.info(f"Updated {field_name} sample rate to {rate} Hz")
    
    def reset_statistics(self) -> None:
        """Reset telemetry statistics."""
        self.stats = TelemetryStats()
        self.logger.info("Telemetry statistics reset")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            # Shutdown thread pool
            if hasattr(self, 'db_executor'):
                self.db_executor.shutdown(wait=False)
        except Exception:
            pass
