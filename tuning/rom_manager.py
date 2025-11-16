"""ROM manager – handles reading/writing binary images and maps."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml
import numpy as np

from core.checksum import calculate as calc_checksum, patch_checksum

log = logging.getLogger(__name__)

class RomManager:
    def __init__(self, maps_config_path: str = "config/maps_mps3_gen2.yml"):
        with open(maps_config_path, "r") as f:
            self.maps_cfg = yaml.safe_load(f) or {}

    def load_rom(self, path: str | Path) -> bytes:
        return Path(path).read_bytes()

    def save_rom(self, path: str | Path, data: bytes) -> None:
        Path(path).write_bytes(data)

    def read_map(self, rom: bytes, map_id: str) -> np.ndarray:
        m = self.maps_cfg["maps"][map_id]
        addr = int(m["address"], 0) if isinstance(m["address"], str) else int(m["address"])
        rows = int(m["rows"])
        cols = int(m["cols"])
        dt = m.get("data_type", "uint8")
        size = rows * cols
        raw = rom[addr : addr + size]
        arr = np.frombuffer(raw, dtype=np.uint8).astype(float)
        # For a real implementation we would apply scaling/offsets
        return arr.reshape((rows, cols))

    def write_map(self, rom: bytearray, map_id: str, table: "np.ndarray") -> None:
        m = self.maps_cfg["maps"][map_id]
        addr = int(m["address"], 0) if isinstance(m["address"], str) else int(m["address"])
        flat = table.astype(np.uint8).tobytes()
        rom[addr : addr + len(flat)] = flat

    def update_checksum(self, rom: bytes) -> bytes:
        return patch_checksum(rom)
