from __future__ import annotations

import binascii
import random
import struct
import time
from typing import Dict, Iterable, List, Optional

try:
    from cobb2 import J2534Protocol  # Real J2534 J2534Protocol wrapper
except Exception:  # pragma: no cover - optional hardware dependency
    J2534Protocol = None  # type: ignore[assignment]

try:
    from cobb3 import MZRECU  # Reverse-engineered ECU model
except Exception:  # pragma: no cover
    MZRECU = None  # type: ignore[assignment]

try:
    from cobb5 import CobbAccessPortEmulator
except Exception:  # pragma: no cover
    CobbAccessPortEmulator = None  # type: ignore[assignment]

try:
    from cobb6 import HardwareInterface as AdvancedHardwareInterface
except Exception:  # pragma: no cover
    AdvancedHardwareInterface = None  # type: ignore[assignment]


from .queue import queue
from .diagnostic_manager import DiagnosticManager, DEFAULT_VIN


class CobbSecurityService:
    ECU_TX_ID = 0x7E0
    ECU_RX_ID = 0x7E8
    TUNING_LEVEL = 0x07

    def __init__(self) -> None:
        self.security_level = 0
        self.session_active = False
        self._memory: Dict[int, bytes] = {}
        self._seed_value = 0

    def _seed_key_algorithm(self, seed: int) -> int:
        temp = ((seed >> 8) & 0xFF) ^ (seed & 0xFF)
        temp = (temp * 0x201) & 0xFFFF
        temp ^= 0x8147
        temp = (temp + 0x1A2B) & 0xFFFF
        key = ((temp << 8) | (temp >> 8)) & 0xFFFF
        return key ^ 0x55AA

    def request_seed(self, level: int) -> int:
        self._seed_value = random.randint(0, 0xFFFF)
        self.security_level = min(self.security_level, level - 1)
        return self._seed_value

    def send_key(self, level: int, key: int) -> bool:
        expected = self._seed_key_algorithm(self._seed_value)
        if key == expected:
            self.security_level = level
            return True
        return False

    def unlock_ecu(self, target_level: int) -> bool:
        if self.session_active and self.security_level >= target_level:
            return True

        for level in range(self.security_level + 1, target_level + 1):
            seed = self.request_seed(level)
            key = self._seed_key_algorithm(seed)
            if not self.send_key(level, key):
                self.session_active = False
                return False
            time.sleep(0.01)

        self.session_active = True
        return True

    def read_memory(self, address: int, length: int) -> Optional[bytes]:
        if not self.session_active:
            return None
        return self._memory.get(address, b"\x00" * length)

    def write_memory(self, address: int, data: bytes) -> bool:
        if not self.session_active:
            return False
        self._memory[address] = data
        return True

    def read_identification(self) -> Dict[str, str]:
        return {
            "VIN": "7AT0C13JX20200064",
            "ECU_PN": "LFRE461BCD",
            "CAL_ID": "8C02F1",
        }


class CobbJ2534Service:
    def __init__(self) -> None:
        self.device_id: Optional[int] = None
        self.connected = False
        # Optional real J2534 implementation from cobb2.py
        self.real: Optional[J2534Protocol] = (
            J2534Protocol() if "J2534Protocol" in globals() and J2534Protocol is not None else None
        )

    def connect(self) -> bool:
        """Connect using the built-in simulated J2534 interface."""
        self.device_id = random.randint(1, 0xFFFF)
        self.connected = True
        return True

    def disconnect(self) -> None:
        self.connected = False
        self.device_id = None

    def read_messages(self) -> list[dict[str, str]]:
        if not self.connected:
            return []
        return [
            {"id": hex(random.randint(0x700, 0x7FF)), "payload": binascii.hexlify(random.randbytes(8)).decode()}
            for _ in range(3)
        ]

    def write_messages(self, payload: bytes) -> bool:
        if not self.connected:
            return False
        queue.push_many([{"type": "j2534_write", "payload": payload.hex()}])
        queue.drain_sim()
        return True

    # --- Optional real-driver hooks -------------------------------------

    def load_real_driver(self, dll_path: str) -> bool:
        """Attempt to load a real J2534 driver DLL via cobb2.J2534Protocol.

        Returns False if the cobb2 module or driver is not available.
        """
        if self.real is None:
            return False
        return self.real.load_driver(dll_path)


class ECUMapService:
    def __init__(self) -> None:
        self.maps: Dict[str, Dict[str, Iterable[int]]] = {
            "boost_map": {"address": 0x2000, "size": 128},
            "fuel_map": {"address": 0x2100, "size": 128},
            "timing_map": {"address": 0x2200, "size": 64},
        }

    def list_tables(self) -> List[str]:
        return list(self.maps.keys())

    def describe_table(self, name: str) -> Dict[str, int]:
        return self.maps.get(name, {})


class HardwareEmulationService:
    def __init__(self) -> None:
        self.leds = {"power": False, "status": False}
        self.version = "AccessPort v2.3"

    def press_button(self, button: str) -> str:
        self.leds["status"] = not self.leds["status"]
        return f"Button {button} pressed, status LED toggled"

    def toggle_power(self) -> str:
        self.leds["power"] = not self.leds["power"]
        return f"Power {'on' if self.leds['power'] else 'off'}"


class HardwareInterfaceService:
    def __init__(self) -> None:
        self.connected = False
        self.port_name = "/dev/ttyAP"

    def open_port(self) -> bool:
        self.connected = True
        return True

    def close_port(self) -> None:
        self.connected = False

    def status(self) -> str:
        return "connected" if self.connected else "disconnected"


class CobbOBDService:
    def __init__(self, diag_manager: DiagnosticManager) -> None:
        self.manager = diag_manager

    def read_dtcs(self) -> List[Dict[str, str]]:
        return self.manager.scan_dtcs()

    def clear_dtcs(self) -> bool:
        return self.manager.clear_dtcs()


class CobbFlashManager:
    def __init__(self, security: CobbSecurityService) -> None:
        self.security = security

    def flash_calibration(self, target_table: str, payload: bytes) -> Dict[str, str]:
        if not self.security.session_active:
            return {"status": "locked", "message": "Unlock ECU first"}

        chunk_size = 32
        for i in range(0, len(payload), chunk_size):
            chunk = payload[i : i + chunk_size]
            queue.push_many(
                [
                    {
                        "type": "flash_chunk",
                        "table": target_table,
                        "offset": i,
                        "crc": binascii.crc32(chunk),
                    }
                ]
            )
        queue.drain_sim()
        checksum = binascii.crc32(payload)
        return {
            "status": "success",
            "table": target_table,
            "bytes": str(len(payload)),
            "crc": hex(checksum),
        }


class RealTimeMonitorService:
    def __init__(self) -> None:
        self.history: List[Dict[str, float]] = []

    def sample(self) -> Dict[str, float]:
        snapshot = {
            "rpm": random.randint(900, 4200),
            "boost": random.uniform(8.0, 22.0),
            "afr": random.uniform(11.0, 15.5),
            "timing": random.uniform(10.0, 22.0),
        }
        self.history.append(snapshot)
        queue.push_many([{"type": "realtime_snapshot", "data": snapshot}])
        queue.drain_sim()
        return snapshot


class CobbCoordinator:
    def __init__(self, vin: str = DEFAULT_VIN) -> None:
        self.security = CobbSecurityService()
        self.j2534 = CobbJ2534Service()
        self.mapping = ECUMapService()
        self.hardware = HardwareEmulationService()
        self.interface = HardwareInterfaceService()
        self.obd = CobbOBDService(DiagnosticManager(vin))
        self.flash = CobbFlashManager(self.security)
        self.monitor = RealTimeMonitorService()

        # Optional reverse-engineered ECU model & advanced hardware hooks
        self.ecu_model = MZRECU(self.security) if "MZRECU" in globals() and MZRECU is not None else None
        self.ap_emulator = None
        self.advanced_hw = (
            AdvancedHardwareInterface()
            if "AdvancedHardwareInterface" in globals() and AdvancedHardwareInterface is not None
            else None
        )

    def summary(self) -> Dict[str, str]:
        return {
            "security_level": str(self.security.security_level),
            "session_active": str(self.security.session_active),
            "port": self.interface.port_name,
            "hardware_version": self.hardware.version,
            "mzrecu_model": "yes" if self.ecu_model is not None else "no",
            "advanced_hw": "yes" if self.advanced_hw is not None else "no",
        }

    # --- Advanced helpers -------------------------------------------------

    def start_virtual_ap(self) -> bool:
        """Start the CobbAccessPortEmulator from cobb5.py, if available.

        Returns False if the emulator or underlying USB stack is not available.
        """
        if "CobbAccessPortEmulator" not in globals() or CobbAccessPortEmulator is None:
            return False
        if self.ap_emulator is None:
            self.ap_emulator = CobbAccessPortEmulator()
        return self.ap_emulator.create_virtual_device()
