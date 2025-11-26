from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping


@dataclass
class TuneMetadata:
    target_power: str
    target_torque: str
    description: str
    safety_margin: str
    fuel_grade: str
    max_boost: float
    max_timing: float
    target_afr: float
    knock_response: str


SAFE_TUNES: Mapping[str, TuneMetadata] = {
    "octane_95": TuneMetadata(
        target_power="260-270 WHP",
        target_torque="300-310 WTQ",
        description="Conservative safe tune that prioritizes longevity on 95 RON fuel.",
        safety_margin="20% factory margin maintained",
        fuel_grade="95 RON",
        max_boost=19.5,
        max_timing=21.0,
        target_afr=11.6,
        knock_response="Very sensitive – 1° pull with knock",
    ),
    "octane_98": TuneMetadata(
        target_power="275-285 WHP",
        target_torque="315-325 WTQ",
        description="Balanced safe tune for 98 fuel with moderate performance lift.",
        safety_margin="18% factory margin",
        fuel_grade="98 RON",
        max_boost=21.0,
        max_timing=22.5,
        target_afr=11.5,
        knock_response="Sensitive – 1.2° pull",
    ),
    "octane_100_plus": TuneMetadata(
        target_power="285-300 WHP",
        target_torque="330-340 WTQ",
        description="Safe high octane tune that gives extra headroom but stays under stress limits.",
        safety_margin="15% factory margin",
        fuel_grade="100+ RON",
        max_boost=22.5,
        max_timing=24.0,
        target_afr=11.4,
        knock_response="Moderate – 1.4° pull",
    ),
}

PREMIUM_TUNES: Mapping[str, TuneMetadata] = {
    "octane_95": TuneMetadata(
        target_power="275-290 WHP",
        target_torque="310-325 WTQ",
        description="Optimized 95 RON tune with aggressive timing and boost.",
        safety_margin="12% factory margin",
        fuel_grade="95 RON",
        max_boost=21.5,
        max_timing=23.0,
        target_afr=11.4,
        knock_response="Moderate – 1.5° pull",
    ),
    "octane_98": TuneMetadata(
        target_power="290-305 WHP",
        target_torque="325-340 WTQ",
        description="High-performing 98 RON tune with aggressive spool and timing.",
        safety_margin="10% factory margin",
        fuel_grade="98 RON",
        max_boost=23.0,
        max_timing=25.0,
        target_afr=11.3,
        knock_response="Aggressive – 1.0° pull",
    ),
    "octane_100_plus": TuneMetadata(
        target_power="310-325 WHP",
        target_torque="345-360 WTQ",
        description="Race-ready 100+ RON tune that pushes boost/timing to the limit.",
        safety_margin="8% factory margin",
        fuel_grade="100+ RON",
        max_boost=24.5,
        max_timing=27.0,
        target_afr=11.2,
        knock_response="Aggressive – 0.8° pull",
    ),
}


class TuneLibraryService:
    def __init__(self) -> None:
        self._categories = {
            "Safe": SAFE_TUNES,
            "Premium": PREMIUM_TUNES,
        }

    def categories(self) -> List[str]:
        return list(self._categories.keys())

    def get_tunes(self, category: str) -> Mapping[str, TuneMetadata]:
        return self._categories.get(category, {})

    def get_metadata(self, category: str, tune_key: str) -> TuneMetadata:
        return self._categories[category][tune_key]
