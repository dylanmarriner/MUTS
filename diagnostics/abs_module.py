"""ABS diagnostics – placeholder module.

Real implementation will use different CAN IDs / services; for now this
module defines the interface and returns dummy data, so the UI and higher
layers can be built and tested without hardware.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

@dataclass
class AbsWheelSpeed:
    fl: float
    fr: float
    rl: float
    rr: float

class AbsModule:
    def read_wheel_speeds(self) -> AbsWheelSpeed:
        # Dummy values – rolling at 50kph
        return AbsWheelSpeed(50.0, 50.0, 50.0, 50.0)

    def read_dtcs(self) -> List[str]:
        return []

    def clear_dtcs(self) -> None:
        pass
