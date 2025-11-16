"""Manager for multiple J2534 devices based on config/j2534_devices.yml."""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import List, Optional

import yaml

from .j2534_device import J2534Device, J2534Error

log = logging.getLogger(__name__)

@dataclass
class DeviceConfig:
    name: str
    dll_windows: Optional[str]
    protocol: str
    baud: int
    quirks: dict

class J2534Manager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.devices_config: list[DeviceConfig] = []
        self.devices: list[J2534Device] = []
        self._load_config()

    def _load_config(self) -> None:
        if not os.path.isfile(self.config_path):
            log.warning("J2534 config file not found: %s", self.config_path)
            return
        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f) or {}
        for d in data.get("devices", []):
            self.devices_config.append(
                DeviceConfig(
                    name=d.get("name", "Unnamed"),
                    dll_windows=d.get("dll_windows"),
                    protocol=d.get("protocol", "ISO15765"),
                    baud=int(d.get("baud", 500000)),
                    quirks=d.get("quirks", {}) or {},
                )
            )

    def _dll_on_path(self, dll_name: str) -> bool:
        for p in os.environ.get("PATH", "").split(os.pathsep):
            full = os.path.join(p, dll_name)
            if os.path.isfile(full):
                return True
        return False

    def scan_devices(self) -> list[J2534Device]:
        devices: list[J2534Device] = []
        for cfg in self.devices_config:
            if not cfg.dll_windows:
                continue
            if not self._dll_on_path(cfg.dll_windows):
                continue
            try:
                dev = J2534Device(cfg.dll_windows, name=cfg.name)
                devices.append(dev)
            except Exception:
                log.exception("Failed to load J2534 DLL %s", cfg.dll_windows)
        self.devices = devices
        return devices

    def auto_connect_first(self) -> Optional[J2534Device]:
        if not self.devices:
            self.scan_devices()
        for dev in self.devices:
            try:
                dev.open()
                dev.connect_iso15765()
                return dev
            except J2534Error:
                log.exception("Failed to connect to J2534 device %s", dev.name)
                continue
        return None
