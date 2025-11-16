"""Torque management helpers."""
from __future__ import annotations

from typing import Dict

def clamp_torque_per_gear(requested: Dict[int, float], max_safe_nm: float) -> Dict[int, float]:
    """Clamp requested torque per gear to a global maximum."""
    return {g: min(t, max_safe_nm) for g, t in requested.items()}
