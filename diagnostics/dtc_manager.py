"""DTC manager – coordinates DTC operations across ECM/ABS/SRS/BCM."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

# For now depend only on ECM via MazdaEcu; ABS/SRS could use additional IDs
from comms.mazda_ecu import MazdaEcu

@dataclass
class DTC:
    module: str
    code: str
    description: str
    severity: str = "UNKNOWN"

class DtcManager:
    def __init__(self, ecu: MazdaEcu):
        self.ecu = ecu

    def scan_all(self) -> List[DTC]:
        # Placeholder: just ECM for now, extend with ABS/SRS
        dtcs: list[DTC] = []
        for code in self.ecu.read_dtc_ecm():
            dtcs.append(DTC(module="ECM", code=code, description="ECM DTC"))
        return dtcs

    def clear_ecm(self) -> None:
        # Stub – would call Mazda-specific clear routine
        pass

    def clear_all(self) -> None:
        self.clear_ecm()
