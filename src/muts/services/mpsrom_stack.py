from __future__ import annotations

import binascii
import random
import struct
import zlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .diagnostic_manager import DiagnosticManager, DEFAULT_VIN


@dataclass
class ROMDefinition:
    base_address: int
    size: int
    description: str
    checksum_offset: Optional[int] = None
    checksum_algorithm: Optional[str] = None


class ROMAnalyzer:
    def __init__(self) -> None:
        self.definitions: Dict[str, ROMDefinition] = self._load_definitions()
        max_address = max(
            defn.base_address + defn.size for defn in self.definitions.values()
        )
        checksum_max = max(
            (defn.checksum_offset or 0) + 4 for defn in self.definitions.values()
        )
        total_size = max(max_address, checksum_max) + 0x100
        self.memory = bytearray(random.getrandbits(8) for _ in range(total_size))

    def _load_definitions(self) -> Dict[str, ROMDefinition]:
        return {
            "boot_sector": ROMDefinition(
                0x000000, 0x010000, "Bootloader & security", checksum_offset=0x00FFFC, checksum_algorithm="SUM16"
            ),
            "calibration": ROMDefinition(
                0x010000, 0x080000, "Calibration tables", checksum_offset=0x1FFFF0, checksum_algorithm="CRC32"
            ),
            "operating_system": ROMDefinition(
                0x110000, 0x040000, "ECU operating system", checksum_offset=0x14FFFC, checksum_algorithm="CRC16"
            ),
            "fault_storage": ROMDefinition(
                0x150000, 0x020000, "Fault & DTC storage"
            ),
            "adaptation": ROMDefinition(
                0x170000, 0x020000, "Adaptive learning data"
            ),
            "vehicle_data": ROMDefinition(
                0x190000, 0x001000, "VIN & vehicle info"
            ),
        }

    def list_sectors(self) -> List[str]:
        return sorted(self.definitions.keys())

    def read_sector(self, name: str) -> bytes:
        defn = self.definitions[name]
        start = defn.base_address
        end = start + defn.size
        return bytes(self.memory[start:end])

    def dump_all(self) -> Dict[str, bytes]:
        return {name: self.read_sector(name) for name in self.definitions}

    def write_at(self, offset: int, data: bytes) -> None:
        self.memory[offset : offset + len(data)] = data

    def read_bytes(self, offset: int, length: int) -> bytes:
        return bytes(self.memory[offset : offset + length])


class ChecksumAnalyzer:
    ALGORITHMS = {"CRC32", "CRC16", "SUM16"}

    def __init__(self, rom: ROMAnalyzer) -> None:
        self.rom = rom
        self.initialize_checksums()

    def initialize_checksums(self) -> None:
        for name in self.rom.list_sectors():
            defn = self.rom.definitions[name]
            if defn.checksum_offset and defn.checksum_algorithm:
                calc = self.calculate(name, defn.checksum_algorithm)
                self._store(defn, calc)

    def calculate(self, sector_name: str, algorithm: str) -> int:
        data = self.rom.read_sector(sector_name)
        match algorithm.upper():
            case "CRC32":
                return zlib.crc32(data) & 0xFFFFFFFF
            case "CRC16":
                return binascii.crc_hqx(data, 0xFFFF)
            case "SUM16":
                return self._sum16(data)
            case _:
                raise ValueError(f"Unsupported algorithm {algorithm}")

    def verify(self, sector_name: str) -> Tuple[int, int, bool]:
        defn = self.rom.definitions[sector_name]
        if not defn.checksum_offset or not defn.checksum_algorithm:
            return (0, 0, False)

        calculated = self.calculate(sector_name, defn.checksum_algorithm)
        stored = self._read(defn)
        return (calculated, stored, calculated == stored)

    def patch(self, sector_name: str) -> None:
        defn = self.rom.definitions[sector_name]
        if not defn.checksum_offset or not defn.checksum_algorithm:
            return
        value = self.calculate(sector_name, defn.checksum_algorithm)
        self._store(defn, value)

    def _sum16(self, data: bytes) -> int:
        total = 0
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                total = (total + (data[i] << 8) + data[i + 1]) & 0xFFFF
        return total

    def _store(self, defn: ROMDefinition, value: int) -> None:
        size = 4 if defn.checksum_algorithm != "CRC16" else 2
        self.rom.write_at(defn.checksum_offset, value.to_bytes(size, "big"))

    def _read(self, defn: ROMDefinition) -> int:
        size = 4 if defn.checksum_algorithm != "CRC16" else 2
        return int.from_bytes(self.rom.read_bytes(defn.checksum_offset, size), "big")


class SecurityAccessService:
    LEVELS = [1, 2, 3]

    def __init__(self) -> None:
        self.seed = None
        self.unlocked_level = 0

    def request_seed(self) -> int:
        self.seed = random.getrandbits(32)
        return self.seed

    def calculate_key(self, level: int) -> int:
        if self.seed is None:
            self.request_seed()
        mask = 0xA5C7E93D ^ (level << 8)
        key = ((self.seed ^ mask) + (level * 0x1001)) & 0xFFFFFFFF
        return key

    def verify_key(self, level: int, key: int) -> bool:
        expected = self.calculate_key(level)
        return key == expected

    def unlock_to(self, level: int) -> bool:
        if level not in self.LEVELS:
            return False
        seed = self.request_seed()
        key = self.calculate_key(level)
        if self.verify_key(level, key):
            self.unlocked_level = level
            return True
        return False


class MapLibrary:
    def __init__(self) -> None:
        self.entries = self._load_maps()

    def _load_maps(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        return {
            "ignition": {
                "primary_timing": {"address": "0x012000", "type": "16x16", "description": "Basic ignition advance"},
                "cold_temp": {"address": "0x012C00", "type": "8x8", "description": "Cold temp correction"},
            },
            "fuel": {
                "primary_fuel": {"address": "0x013000", "type": "16x16", "description": "Main fuel table"},
                "wot_enrich": {"address": "0x013400", "type": "8x8", "description": "Wide open throttle enrichment"},
            },
            "boost": {
                "boost_target": {"address": "0x014000", "type": "16x16", "description": "Target boost by load"},
                "wastegate": {"address": "0x014400", "type": "16x16", "description": "Wastegate duty cycle"},
            },
        }

    def groups(self) -> List[str]:
        return list(self.entries.keys())

    def entries_in_group(self, group: str) -> List[str]:
        return list(self.entries.get(group, {}).keys())

    def describe(self, group: str, entry: str) -> Dict[str, str]:
        return self.entries.get(group, {}).get(entry, {})


class MPSROMCoordinator:
    def __init__(self, vin: str = DEFAULT_VIN) -> None:
        self.rom = ROMAnalyzer()
        self.checksum = ChecksumAnalyzer(self.rom)
        self.security = SecurityAccessService()
        self.maps = MapLibrary()
        self.diag = DiagnosticManager(vin)

    def summary(self) -> Dict[str, str]:
        return {
            "sectors": str(len(self.rom.definitions)),
            "security_level": f"{self.security.unlocked_level}",
            "map_groups": ", ".join(self.maps.groups()),
        }
