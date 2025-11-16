"""Fueling helpers (AFR target shaping, etc.)."""
from __future__ import annotations

import numpy as np

def enrich_wot(afr_table: "np.ndarray", wot_rows: int = 2, target_afr: float = 11.5) -> "np.ndarray":
    """Force the last N rows (highest load) richer for WOT protection."""
    out = afr_table.copy()
    if wot_rows <= 0:
        return out
    out[-wot_rows:, :] = target_afr
    return out
