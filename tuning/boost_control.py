"""Boost control helpers."""
from __future__ import annotations

import numpy as np

def derive_boost_from_load(load_table: "np.ndarray", base_psi: float = 14.7) -> "np.ndarray":
    """Very rough mapping from load to boost target.

    In reality this depends on engine VE, displacement, temperature, etc.
    Here we provide a simple proportional mapping so the UI can function.
    """
    return (load_table - 1.0) * base_psi
