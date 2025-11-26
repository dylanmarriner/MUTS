from __future__ import annotations

import random
import time
from typing import Dict, List


class MazdaOBDService:
    """Simple simulator for Mazda OBD-II interactions."""

    def __init__(self, simulate_delay: float = 0.05) -> None:
        self._connected = False
        self._simulate_delay = simulate_delay

    def connect(self) -> bool:
        time.sleep(self._simulate_delay)
        self._connected = True
        return True

    def disconnect(self) -> None:
        if self._connected:
            time.sleep(self._simulate_delay)
        self._connected = False

    def read_ecu_data(self) -> Dict[str, float]:
        maf_flow = random.uniform(2.5, 14.0)
        base_rpm = random.randint(800, 3200)
        boost = random.uniform(8.0, 20.0)

        return {
            "rpm": base_rpm,
            "boost_psi": boost,
            "throttle_position": random.uniform(10.0, 80.0),
            "ignition_timing": random.uniform(10.0, 23.0),
            "fuel_trim_long": random.uniform(-5.0, 5.0),
            "fuel_trim_short": random.uniform(-2.0, 2.0),
            "maf_voltage": maf_flow,
            "afr": min(max(10.5, 14.7 - (maf_flow / 50)), 16.0),
            "coolant_temp": random.uniform(68.0, 102.0),
            "intake_temp": random.uniform(38.0, 68.0),
            "knock_count": random.randint(0, 3),
            "vvt_advance": random.uniform(-5.0, 10.0),
            "calculated_load": random.uniform(40.0, 85.0),
        }

    def read_dtcs(self) -> List[Dict[str, str]]:
        if not self._connected:
            return []
        samples = [
            {"code": "P0101", "description": "MAF sensor performance", "severity": "LOW"},
            {"code": "C0035", "description": "Left front wheel speed sensor", "severity": "MEDIUM"},
        ]
        return random.sample(samples, random.randint(0, len(samples)))

    def clear_dtcs(self) -> bool:
        return self._connected
