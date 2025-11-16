"""Shared tuning configuration models for MUTS."""
from __future__ import annotations

from pydantic import BaseModel
from typing import Dict, List

class TorqueConfig(BaseModel):
    per_gear_limits_nm: Dict[int, float]  # gear -> torque limit

class PerformanceFeaturesConfig(BaseModel):
    launch_control_rpm: int = 3500
    flat_shift_rpm: int = 4500
    rev_limit_rpm: int = 7000
    speed_limiter_kph: int = 250
    swas_disabled: bool = False
    valet_mode_speed_cap_kph: int = 60
    valet_mode_rpm_cap: int = 3000

class TuneConfiguration(BaseModel):
    name: str
    description: str = ""
    load_targets: List[List[float]] = []
    boost_targets: List[List[float]] = []
    ignition_timing: List[List[float]] = []
    afr_targets: List[List[float]] = []
    fuel_pressure_base_psi: float = 400.0
    fuel_pressure_max_psi: float = 1800.0
    torque: TorqueConfig = TorqueConfig(per_gear_limits_nm={})
    features: PerformanceFeaturesConfig = PerformanceFeaturesConfig()
