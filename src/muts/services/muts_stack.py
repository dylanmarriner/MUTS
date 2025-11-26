from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .diagnostic_manager import DiagnosticManager, DEFAULT_VIN


class MutsSecurityService:
    LEVELS = [1, 2, 3, 4, 5, 6]

    def __init__(self) -> None:
        self.last_seed = 0
        self.unlocked_level = 0

    def request_seed(self, level: int) -> int:
        self.last_seed = random.getrandbits(16)
        return self.last_seed

    def calculate_key(self, level: int) -> int:
        seed = self.last_seed or self.request_seed(level)
        key = (
            ((seed ^ 0x73A1) + (level << 4))
            ^ ((seed << (level % 8)) | (seed >> (16 - (level % 8))))
        ) & 0xFFFF
        key ^= 0x55AA
        return key

    def unlock(self, target_level: int) -> bool:
        for lvl in self.LEVELS:
            if lvl > target_level:
                break
            seed = self.request_seed(lvl)
            key = self.calculate_key(lvl)
            if (key ^ seed) & 0xFF != 0xAA:  # silly check
                return False
        self.unlocked_level = target_level
        return True


class MutsSRSService:
    BACKDOOR_CODES = [
        "SRS-TECH-ACCESS-2024",
        "AIRBAG-SERVICE-MODE",
        "CRASH-DATA-RESET",
        "MAZDA-SRS-ADMIN-2287",
    ]

    def __init__(self) -> None:
        self.granted = False
        self.last_method = ""

    def attempt_unlock(self, method: str) -> bool:
        self.last_method = method
        if method == "manufacturer":
            self.granted = True
        else:
            self.granted = random.choice([True, False])
        return self.granted

    def current_status(self) -> str:
        return f"Last method: {self.last_method or 'none'} ({'granted' if self.granted else 'denied'})"


class MutsEEPROMService:
    def __init__(self) -> None:
        self.patches: List[Tuple[str, str]] = []

    def apply_patch(self, name: str) -> str:
        token = f"{name}-{random.randint(0,9999):04}"
        self.patches.append((name, token))
        return token

    def patch_history(self) -> List[str]:
        return [f"{name} => {token}" for name, token in self.patches]


class MutsBackdoorService:
    def __init__(self) -> None:
        self.codes = {
            "FACTORY": "MZDA_FACT_2287",
            "DEALER": "MZDA_DEAL_2024",
            "SERVICE": "MZDA_SERV_1234",
        }
        self.active = []

    def engage(self, mode: str) -> str:
        code = self.codes.get(mode.upper(), "UNKNOWN")
        status = f"{mode} engaged with {code}"
        self.active.append(status)
        return status

    def history(self) -> List[str]:
        return self.active[-5:]


class MutsExploitService:
    def simulate_racing_feature(self, feature: str) -> str:
        return f"{feature} boost tweak applied (+{random.uniform(3.0,5.5):.1f} psi)"

    def list_features(self) -> List[str]:
        return [
            "Launch control limiter adjustment",
            "Knock controller bias reset",
            "Aggressive torque bias in 1st/2nd",
        ]


class MutsKnowledgeService:
    def entries(self) -> List[str]:
        return [
            "MUTS Factory Platform: full dealer-grade diagnostics + tuning blueprint",
            "Production-ready GUI: low-noise components, focus on reliability",
            "Race engineering reference: training on safe limits, data retention, and security bypass",
        ]


class MutsCoordinator:
    def __init__(self, vin: str = DEFAULT_VIN) -> None:
        self.security = MutsSecurityService()
        self.srs = MutsSRSService()
        self.eeprom = MutsEEPROMService()
        self.backdoor = MutsBackdoorService()
        self.exploit = MutsExploitService()
        self.knowledge = MutsKnowledgeService()
        self.diag = DiagnosticManager(vin)

    def summary(self) -> Dict[str, str]:
        return {
            "security_level": str(self.security.unlocked_level),
            "srs_status": "unlocked" if self.srs.granted else "locked",
            "patches_applied": str(len(self.eeprom.patches)),
            "backdoor_engaged": str(len(self.backdoor.active)),
        }
