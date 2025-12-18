from __future__ import annotations

import random
import struct
from enum import IntEnum, Enum
from typing import Dict, List, Tuple

from .diagnostic_manager import DiagnosticManager, DEFAULT_VIN

# Import from new app/mds modules
from app.mds.protocols.diagnostic_protocols import MazdaDiagnosticProtocol, DiagnosticSession, SecurityAccessLevel
from app.mds.security.security_algorithms import MazdaSecurityAccess, MazdaSecurityAlgorithm
from app.mds.diagnostics.diagnostic_database import MazdaDTCDatabase
from app.mds.calibration.calibration_files import MazdaCalibrationDatabase
from app.mds.programming.programming_routines import MazdaProgrammingService
from app.mds.interface.j2534_interface import J2534Interface
from app.mds.core.ids_software import MazdaIDS
from app.mds.calibration.calibration_tools import MazdaCalibrationService
from app.mds.utils.checksum_routines import ChecksumCalculator, ChecksumType


class MazdaProtocol(IntEnum):
    ISO_9141_2 = 1
    ISO_14230_4_KWP = 2
    ISO_15765_4_CAN = 3
    ISO_15765_4_CAN_29 = 4
    MAZDA_CAN_HS = 5
    MAZDA_CAN_MS = 6
    MAZDA_SUB_CAN = 7


class DiagnosticSession(IntEnum):
    DEFAULT = 0x01
    PROGRAMMING = 0x02
    EXTENDED = 0x03
    SAFETY = 0x04
    MANUFACTURER = 0x40


class SecurityAccessLevel(IntEnum):
    LEVEL_1 = 0x01
    LEVEL_2 = 0x02
    LEVEL_3 = 0x03


class MazdaSeedKeyManager:
    def __init__(self):
        # Use the new MazdaSecurityAccess from app/mds
        self.security_access = MazdaSecurityAccess()

    def solve(self, level: SecurityAccessLevel, seed: int) -> int:
        # Convert seed to bytes for the new security access module
        seed_bytes = seed.to_bytes(4, 'big')
        
        # Map old levels to new algorithms
        algorithm_map = {
            SecurityAccessLevel.LEVEL_1: MazdaSecurityAlgorithm.ALGORITHM_27_STANDARD,
            SecurityAccessLevel.LEVEL_2: MazdaSecurityAlgorithm.ALGORITHM_27_ENHANCED,
            SecurityAccessLevel.LEVEL_3: MazdaSecurityAlgorithm.ALGORITHM_27_RACE,
        }
        
        algorithm = algorithm_map.get(level, MazdaSecurityAlgorithm.ALGORITHM_27_STANDARD)
        key_bytes = self.security_access.calculate_seed_key(seed_bytes, algorithm)
        
        # Convert back to int
        return int.from_bytes(key_bytes, 'big')


class DiagnosticTestStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MazdaDiagnosticTests:
    TESTS = {
        "A/C_SYSTEM": "Air conditioning system activation",
        "FUEL_PUMP": "Fuel pump circuit verification",
        "KNOCK_SENSOR": "Knock sensor functional test",
    }

    def run_test(self, test_name: str) -> Tuple[str, DiagnosticTestStatus]:
        status = random.choice(list(DiagnosticTestStatus))
        return (self.TESTS.get(test_name, "Unknown test"), status)


class CalibrationOperationLevel(IntEnum):
    READ = 1
    WRITE = 2
    VERIFY = 3
    ADJUST = 4
    CHECKSUM = 5


class MazdaCalibrationService:
    def __init__(self):
        # Use the new calibration database from app/mds
        self.calibration_database = MazdaCalibrationDatabase()
        self.maps = {
            "boost": [random.uniform(6.0, 18.0) for _ in range(10)],
            "fuel": [random.uniform(10.0, 17.0) for _ in range(10)],
            "timing": [random.uniform(8.0, 22.0) for _ in range(10)],
        }

    def list_maps(self) -> List[str]:
        # Return maps from the new calibration database
        calibration = self.calibration_database.get_calibration("L3K9-18-881A")
        if calibration:
            return list(calibration.maps.keys())
        return list(self.maps.keys())

    def adjust_map(self, name: str, offset: int, delta: float) -> bool:
        if name not in self.maps:
            return False
        self.maps[name][offset % len(self.maps[name])] += delta
        return True

    def read_map(self, name: str) -> List[float]:
        # Try to read from calibration database first
        calibration = self.calibration_database.get_calibration("L3K9-18-881A")
        if calibration and name in calibration.maps:
            map_def = calibration.maps[name]
            return map_def.values[0] if map_def.values else []
        return self.maps.get(name, [])


class MazdaChecksumCalculator:
    def __init__(self):
        # Use the new checksum calculator from app/mds
        self.checksum_calc = ChecksumCalculator()
    
    def checksum(self, data: bytes, algorithm: str = "crc32") -> str:
        # Map algorithm names to ChecksumType
        algorithm_map = {
            "crc32": ChecksumType.CRC32,
            "crc16": ChecksumType.CRC16,
            "simple": ChecksumType.SIMPLE_SUM,
            "mazda": ChecksumType.MAZDA_PROPRIETARY,
        }
        
        checksum_type = algorithm_map.get(algorithm, ChecksumType.CRC32)
        checksum_value = self.checksum_calc.calculate_checksum(data, checksum_type)
        
        return hex(checksum_value)


class MazdaIDSCoordinator:
    def __init__(self, vin: str = DEFAULT_VIN):
        # Initialize with the new IDS software from app/mds
        self.ids = MazdaIDS()
        self.protocol = MazdaProtocol.ISO_15765_4_CAN
        self.session = DiagnosticSession.DEFAULT
        self.security_manager = MazdaSeedKeyManager()
        self.tests = MazdaDiagnosticTests()
        self.calibration = MazdaCalibrationService()
        self.checksum = MazdaChecksumCalculator()
        self.diag = DiagnosticManager(vin)
        
        # Connect the IDS components
        self._connect_ids_components()

    def _connect_ids_components(self):
        """Connect IDS components together"""
        # Set up relationships between components
        self.ids.programming_service.diagnostic_protocol = self.ids.diagnostic_protocol
        if hasattr(self.ids, 'calibration_service'):
            self.ids.calibration_service.diagnostic_protocol = self.ids.diagnostic_protocol
            self.ids.calibration_service.programming_service = self.ids.programming_service

    def switch_protocol(self, protocol: MazdaProtocol) -> None:
        self.protocol = protocol
        # Update IDS protocol if needed
        if hasattr(self.ids, 'diagnostic_protocol'):
            self.ids.diagnostic_protocol.protocol = protocol

    def enter_session(self, session: DiagnosticSession) -> None:
        self.session = session
        # Use IDS to enter session
        if hasattr(self.ids, 'diagnostic_protocol'):
            self.ids.diagnostic_protocol.start_diagnostic_session(session)

    def run_diagnostic_test(self, test_name: str) -> Tuple[str, DiagnosticTestStatus]:
        # Use IDS diagnostic modules if available
        if hasattr(self.ids, 'diagnostic_service'):
            results = self.ids.diagnostic_service.perform_system_scan()
            return (f"System scan completed with {len(results.get('dtcs_found', []))} DTCs found", 
                   DiagnosticTestStatus.COMPLETED)
        return self.tests.run_test(test_name)

    def perform_calibration(self, name: str, delta: float) -> bool:
        return self.calibration.adjust_map(name, 0, delta)

    def calculate_checksum(self, algorithm: str) -> str:
        data = b"".join(map(lambda m: m.to_bytes(2, "big"), range(8)))
        return self.checksum.checksum(data, algorithm)
    
    def connect_to_vehicle(self) -> bool:
        """Connect to vehicle using IDS"""
        return self.ids.connect_to_vehicle()
    
    def disconnect_from_vehicle(self):
        """Disconnect from vehicle"""
        self.ids.disconnect_from_vehicle()
    
    def get_vehicle_info(self) -> Dict[str, any]:
        """Get vehicle information"""
        return self.ids.current_vehicle_info
