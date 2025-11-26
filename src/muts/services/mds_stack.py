from __future__ import annotations

import random
import struct
from enum import IntEnum, Enum
from typing import Dict, List, Tuple

from .diagnostic_manager import DiagnosticManager, DEFAULT_VIN


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
        self.algorithms = {
            SecurityAccessLevel.LEVEL_1: self._solve_level1,
            SecurityAccessLevel.LEVEL_2: self._solve_level2,
            SecurityAccessLevel.LEVEL_3: self._solve_level3,
        }

    def solve(self, level: SecurityAccessLevel, seed: int) -> int:
        func = self.algorithms.get(level, self._solve_level1)
        return func(seed)

    def _solve_level1(self, seed: int) -> int:
        return ((seed ^ 0x7382A91F) + 0x1F47A2B8) & 0xFFFFFFFF

    def _solve_level2(self, seed: int) -> int:
        key = seed ^ 0xA5C7E93D
        return ((key << 7) | (key >> 25)) & 0xFFFFFFFF

    def _solve_level3(self, seed: int) -> int:
        key = seed ^ 0x1F4A7C3E
        return ((key + 0x8D3A2F47) ^ 0xB5E8C91A) & 0xFFFFFFFF


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
        self.maps = {
            "boost": [random.uniform(6.0, 18.0) for _ in range(10)],
            "fuel": [random.uniform(10.0, 17.0) for _ in range(10)],
            "timing": [random.uniform(8.0, 22.0) for _ in range(10)],
        }

    def list_maps(self) -> List[str]:
        return list(self.maps.keys())

    def adjust_map(self, name: str, offset: int, delta: float) -> bool:
        if name not in self.maps:
            return False
        self.maps[name][offset % len(self.maps[name])] += delta
        return True

    def read_map(self, name: str) -> List[float]:
        return self.maps.get(name, [])


class MazdaChecksumCalculator:
    def checksum(self, data: bytes, algorithm: str = "crc32") -> str:
        if algorithm == "crc32":
            return hex(struct.unpack(">I", struct.pack(">I", random.randint(0, 0xFFFFFFFF)))[0])
        if algorithm == "crc16":
            return hex(random.randint(0, 0xFFFF))
        return "0x0"


class MazdaIDSCoordinator:
    def __init__(self, vin: str = DEFAULT_VIN):
        self.protocol = MazdaProtocol.ISO_15765_4_CAN
        self.session = DiagnosticSession.DEFAULT
        self.security_manager = MazdaSeedKeyManager()
        self.tests = MazdaDiagnosticTests()
        self.calibration = MazdaCalibrationService()
        self.checksum = MazdaChecksumCalculator()
        self.diag = DiagnosticManager(vin)

    def switch_protocol(self, protocol: MazdaProtocol) -> None:
        self.protocol = protocol

    def enter_session(self, session: DiagnosticSession) -> None:
        self.session = session

    def run_diagnostic_test(self, test_name: str) -> Tuple[str, DiagnosticTestStatus]:
        return self.tests.run_test(test_name)

    def perform_calibration(self, name: str, delta: float) -> bool:
        return self.calibration.adjust_map(name, 0, delta)

    def calculate_checksum(self, algorithm: str) -> str:
        data = b"".join(map(lambda m: m.to_bytes(2, "big"), range(8)))
        return self.checksum.checksum(data, algorithm)
