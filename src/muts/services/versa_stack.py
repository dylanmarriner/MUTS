from __future__ import annotations

import binascii
import random
import struct
import time
from typing import Dict, Iterable, List

from .queue import queue
from .diagnostic_manager import DiagnosticManager, DEFAULT_VIN


class VersaCommunicator:
    RESPONSES = {
        (0x27, 0x01): b"\x67\x01" + b"\x0A\x0B\x0C\x0D",
        (0x22, 0xF1): b"\x62\xF1\x90" + b"7AT0C13JX20200064",
        (0x10, 0x02): b"\x50\x02",
    }

    def __init__(self) -> None:
        self.connected = False
        self.history: List[str] = []

    def connect(self) -> bool:
        time.sleep(0.01)
        self.connected = True
        return True

    def disconnect(self) -> None:
        self.connected = False

    def send_request(self, service: int, subfunction: int, payload: bytes = b"") -> bytes:
        if not self.connected:
            raise RuntimeError("Not connected")
        key = (service, subfunction)
        self.history.append(f"{service:02X}.{subfunction:02X}")
        return self.RESPONSES.get(key, b"\x7F\x00")


class VersaSecurityManager:
    LEVELS = [0x01, 0x03, 0x05, 0x07]

    def __init__(self, communicator: VersaCommunicator):
        self.communicator = communicator
        self.unlocked_level = 0

    def _derive_key(self, seed: int, level: int) -> int:
        key = seed ^ (0xA5C7 << (level % 4))
        key = ((key << 3) | (key >> 29)) & 0xFFFFFFFF
        key = (key + (level * 0x1001)) & 0xFFFFFFFF
        return key

    def unlock(self, target: int = 0x05) -> bool:
        if not self.communicator.connected:
            self.communicator.connect()

        for level in self.LEVELS:
            if level > target:
                break
            seed_data = self.communicator.send_request(0x27, level)
            if len(seed_data) < 6:
                return False
            seed = int.from_bytes(seed_data[2:6], "big")
            key = self._derive_key(seed, level)
            response = self.communicator.send_request(0x27, level + 1, key.to_bytes(4, "big"))
            if not response or response[0] != 0x67:
                return False
            self.unlocked_level = level
        return True


class VersaROMOperations:
    SECTORS = {
        "boot_sector": (0x000000, 0x010000),
        "calibration": (0x010000, 0x080000),
        "fault_memory": (0x150000, 0x020000),
    }

    def __init__(self) -> None:
        self.blob: Dict[str, bytes] = {name: bytes(size) for name, (_, size) in self.SECTORS.items()}

    def read_sector(self, sector: str) -> bytes:
        return self.blob.get(sector, b"")

    def write_sector(self, sector: str, data: bytes) -> bool:
        if sector not in self.blob:
            return False
        self.blob[sector] = data[: len(self.blob[sector])]
        return True

    def checksum(self, sector: str) -> str:
        data = self.read_sector(sector)
        return hex(binascii.crc32(data) & 0xFFFFFFFF)


class VersaMapManager:
    def __init__(self) -> None:
        self.maps: Dict[str, List[List[float]]] = {
            "boost_map": [[random.uniform(5.0, 18.0) for _ in range(8)] for _ in range(8)],
            "fuel_map": [[random.uniform(10.0, 18.0) for _ in range(6)] for _ in range(6)],
            "timing_map": [[random.uniform(10.0, 22.0) for _ in range(4)] for _ in range(4)],
        }

    def list_maps(self) -> List[str]:
        return list(self.maps.keys())

    def read_map(self, name: str) -> List[List[float]]:
        return self.maps.get(name, [])

    def adjust_cell(self, name: str, row: int, col: int, delta: float) -> bool:
        table = self.maps.get(name)
        if not table or row >= len(table) or col >= len(table[0]):
            return False
        table[row][col] += delta
        return True


class VersaCoordinator:
    def __init__(self, vin: str = DEFAULT_VIN) -> None:
        self.communicator = VersaCommunicator()
        self.security = VersaSecurityManager(self.communicator)
        self.rom = VersaROMOperations()
        self.maps = VersaMapManager()
        self.diag = DiagnosticManager(vin)

    def summary(self) -> Dict[str, str]:
        return {
            "communicator": "connected" if self.communicator.connected else "disconnected",
            "security_level": f"{self.security.unlocked_level:02X}",
            "loaded_maps": ", ".join(self.maps.list_maps()),
        }
