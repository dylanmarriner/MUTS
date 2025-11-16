"""Freeze frame storage & representation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FreezeFrame:
    dtc: str
    data: Dict[str, Any]
