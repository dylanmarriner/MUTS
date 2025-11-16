"""Implementation helpers for performance features (LC, FFS, valet)."""
from __future__ import annotations

from .models import PerformanceFeaturesConfig

def describe_features(cfg: PerformanceFeaturesConfig) -> str:
    return (
        f"LC: {cfg.launch_control_rpm} rpm, FFS: {cfg.flat_shift_rpm} rpm, "
        f"Limiter: {cfg.rev_limit_rpm} rpm, Speed cap: {cfg.speed_limiter_kph} kph, "
        f"Valet: {cfg.valet_mode_speed_cap_kph} kph / {cfg.valet_mode_rpm_cap} rpm, "
        f"SWAS disabled: {cfg.swas_disabled}"
    )
