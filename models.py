"""
Shared data models and types for the Mazdaspeed 3 tuning suite.
Centralized type definitions to avoid circular imports and ensure consistency.
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime
import struct


class VehicleState(Enum):
    """Vehicle operational states."""
    OFF = "off"
    IDLE = "idle"
    RUNNING = "running"
    DRIVING = "driving"
    TUNING = "tuning"


class SecurityLevel(Enum):
    """Security access levels for ECU operations."""
    NONE = 0
    READ_ONLY = 1
    DIAGNOSTIC = 2
    TUNING = 3
    FLASH = 4
    ADMIN = 5


class CANPriority(IntEnum):
    """CAN message priority levels."""
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4


class OBDProtocol(Enum):
    """Supported OBD-II protocols."""
    ISO_9141_2 = "ISO_9141_2"
    ISO_14230_4 = "ISO_14230_4"  # KWP2000
    ISO_15765_4 = "ISO_15765_4"  # CAN
    SAE_J1850_PWM = "SAE_J1850_PWM"
    SAE_J1850_VPW = "SAE_J1850_VPW"


class TuningMode(Enum):
    """Available tuning modes."""
    STOCK = "stock"
    ECONOMY = "economy"
    PERFORMANCE = "performance"
    RACE = "race"
    CUSTOM = "custom"


class FlashState(Enum):
    """ECU flashing operation states."""
    IDLE = "idle"
    PREPARING = "preparing"
    BACKING_UP = "backing_up"
    ERASING = "erasing"
    WRITING = "writing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


class ExploiterState(Enum):
    """Exploiter operational states."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    CONNECTED = "connected"
    OPERATING = "operating"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class ECUState(Enum):
    """ECU operational states."""
    OFFLINE = "offline"
    BOOTLOADER = "bootloader"
    NORMAL = "normal"
    DIAGNOSTIC = "diagnostic"
    PROGRAMMING = "programming"
    ERROR = "error"


class EEPROMOperation(Enum):
    """EEPROM operation types."""
    READ = "read"
    WRITE = "write"
    ERASE = "erase"
    VERIFY = "verify"
    BACKUP = "backup"
    RESTORE = "restore"
    CHECKSUM = "checksum"


class ECUOperation(Enum):
    """ECU operation types."""
    READ_MEMORY = "read_memory"
    WRITE_MEMORY = "write_memory"
    FLASH_CALIBRATION = "flash_calibration"
    READ_DTC = "read_dtc"
    CLEAR_DTC = "clear_dtc"
    BACKUP_ECU = "backup_ecu"
    RESTORE_ECU = "restore_ecu"
    READ_VIN = "read_vin"
    GET_INFO = "get_info"
    RESET_ECU = "reset_ecu"
    ENTER_BOOTLOADER = "enter_bootloader"


@dataclass
class CANMessage:
    """CAN bus message structure."""
    arbitration_id: int
    data: bytes
    dlc: int = field(default=8)
    extended_id: bool = field(default=False)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    priority: CANPriority = field(default=CANPriority.NORMAL)
    
    def __post_init__(self):
        if len(self.data) > 8:
            raise ValueError(f"CAN data too long: {len(self.data)} bytes (max 8)")
        self.dlc = len(self.data)


@dataclass
class OBDPacket:
    """OBD-II communication packet."""
    service_id: int
    data: bytes
    protocol: OBDProtocol
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    response_expected: bool = field(default=True)
    
    @property
    def pid(self) -> Optional[int]:
        """Extract PID from packet if applicable."""
        if len(self.data) > 0:
            return self.data[0]
        return None


@dataclass
class TelemetryData:
    """Real-time telemetry data packet."""
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # Engine parameters
    rpm: float = 0.0
    load: float = 0.0  # Engine load percentage
    map: float = 0.0   # Manifold absolute pressure (kPa)
    maf: float = 0.0   # Mass air flow (g/s)
    iat: float = 0.0   # Intake air temperature (°C)
    ect: float = 0.0   # Engine coolant temperature (°C)
    
    # Fuel system
    afr: float = 14.7  # Air-fuel ratio
    stft: float = 0.0  # Short term fuel trim (%)
    ltft: float = 0.0  # Long term fuel trim (%)
    fuel_pressure: float = 0.0  # Fuel pressure (kPa)
    
    # Ignition system
    timing_advance: float = 0.0  # Ignition timing advance (°)
    dwell_time: float = 0.0      # Coil dwell time (ms)
    
    # Boost and turbo
    boost_pressure: float = 0.0  # Boost pressure (psi)
    boost_target: float = 0.0    # Target boost (psi)
    wastegate_duty: float = 0.0  # Wastegate duty cycle (%)
    
    # Transmission
    vehicle_speed: float = 0.0   # Vehicle speed (km/h)
    gear: int = 0                # Current gear (0=neutral)
    
    # Throttle
    throttle_position: float = 0.0  # Throttle position (%)
    pedal_position: float = 0.0     # Accelerator pedal position (%)
    
    # Safety and diagnostics
    dtc_count: int = 0           # Number of active DTCs
    knock_retard: float = 0.0    # Knock retard (°)
    oil_pressure: float = 0.0    # Oil pressure (psi)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp,
            'rpm': self.rpm,
            'load': self.load,
            'map': self.map,
            'maf': self.maf,
            'iat': self.iat,
            'ect': self.ect,
            'afr': self.afr,
            'stft': self.stft,
            'ltft': self.ltft,
            'fuel_pressure': self.fuel_pressure,
            'timing_advance': self.timing_advance,
            'dwell_time': self.dwell_time,
            'boost_pressure': self.boost_pressure,
            'boost_target': self.boost_target,
            'wastegate_duty': self.wastegate_duty,
            'vehicle_speed': self.vehicle_speed,
            'gear': self.gear,
            'throttle_position': self.throttle_position,
            'pedal_position': self.pedal_position,
            'dtc_count': self.dtc_count,
            'knock_retard': self.knock_retard,
            'oil_pressure': self.oil_pressure,
        }


@dataclass
class TuningParameter:
    """Individual tuning parameter definition."""
    name: str
    value: Union[int, float, bool]
    min_value: Union[int, float]
    max_value: Union[int, float]
    default_value: Union[int, float]
    units: str
    description: str
    category: str
    security_level: SecurityLevel = field(default=SecurityLevel.TUNING)
    address: Optional[int] = None  # ECU memory address if applicable
    data_type: str = field(default="float")  # float, int, bool, enum
    
    def validate(self) -> bool:
        """Validate parameter value within bounds."""
        if isinstance(self.value, (int, float)):
            return self.min_value <= self.value <= self.max_value
        return True


@dataclass
class TuningProfile:
    """Complete tuning configuration profile."""
    name: str
    mode: TuningMode
    parameters: Dict[str, TuningParameter]
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    author: str = "MUTS System"
    description: str = ""
    
    def get_parameter(self, name: str) -> Optional[TuningParameter]:
        """Get parameter by name."""
        return self.parameters.get(name)
    
    def set_parameter(self, param: TuningParameter) -> None:
        """Set parameter value."""
        if not param.validate():
            raise ValueError(f"Invalid parameter value for {param.name}")
        self.parameters[param.name] = param
        self.modified_at = datetime.now()


@dataclass
class DiagnosticTroubleCode:
    """DTC structure."""
    code: str  # e.g., "P0301"
    description: str
    status: str  # "active", "pending", "historic"
    first_occurrence: datetime
    last_occurrence: datetime
    occurrence_count: int = 1
    freeze_frame: Optional[TelemetryData] = None
    
    @property
    def is_misfire(self) -> bool:
        """Check if this is a misfire code."""
        return self.code.startswith("P030") and self.code != "P0300"


@dataclass
class FlashOperation:
    """ECU flash operation details."""
    operation_id: str
    state: FlashState
    progress: float = 0.0  # 0.0 to 1.0
    start_time: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    backup_created: bool = False
    checksum_verified: bool = False
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


@dataclass
class SecurityCredentials:
    """Security authentication credentials."""
    username: str
    password_hash: str
    security_level: SecurityLevel
    session_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    permissions: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if credentials have expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def has_permission(self, permission: str) -> bool:
        """Check if credentials include specific permission."""
        return permission in self.permissions


@dataclass
class CANFilter:
    """CAN message filter configuration."""
    arbitration_id: int
    mask: int
    extended: bool = False
    description: str = ""
    
    def matches(self, message: CANMessage) -> bool:
        """Check if CAN message matches this filter."""
        if message.extended_id != self.extended:
            return False
        return (message.arbitration_id & self.mask) == (self.arbitration_id & self.mask)


@dataclass
class LogEntry:
    """System log entry structure."""
    timestamp: datetime = field(default_factory=datetime.now)
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    module: str = ""
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'module': self.module,
            'message': self.message,
            'data': self.data,
        }


# Type aliases for better readability
TelemetryBuffer = List[TelemetryData]
CANMessageQueue = List[CANMessage]
DTCList = List[DiagnosticTroubleCode]
ParameterMap = Dict[str, TuningParameter]
SecurityContext = Optional[SecurityCredentials]
