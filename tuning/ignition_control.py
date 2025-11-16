"""Ignition control helpers."""
from __future__ import annotations

import numpy as np

def apply_knock_margin(ign_table: "np.ndarray", margin_deg: float = 2.0) -> "np.ndarray":
    """Reduce ignition advance everywhere by a fixed margin."""
    return ign_table - margin_deg
