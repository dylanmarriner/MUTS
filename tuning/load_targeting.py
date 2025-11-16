"""Helpers for computing and validating load target tables."""
from __future__ import annotations

import numpy as np

def smooth_table(table: "np.ndarray", passes: int = 1) -> "np.ndarray":
    t = table.astype(float).copy()
    for _ in range(passes):
        t[1:-1, 1:-1] = (
            t[1:-1, 1:-1]
            + t[:-2, 1:-1]
            + t[2:, 1:-1]
            + t[1:-1, :-2]
            + t[1:-1, 2:]
        ) / 5.0
    return t
