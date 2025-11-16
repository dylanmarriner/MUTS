"""Manage creation, storage and retrieval of tune profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import TuneConfiguration

class TuneProfileManager:
    def __init__(self, root: str = "tunes"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def list_profiles(self) -> List[Path]:
        return sorted(self.root.glob("*.muts_tune.json"))

    def save_profile(self, cfg: TuneConfiguration) -> Path:
        path = self.root / f"{cfg.name}.muts_tune.json"
        with path.open("w") as f:
            json.dump(cfg.model_dump(), f, indent=2)
        return path

    def load_profile(self, path: Path) -> TuneConfiguration:
        with path.open("r") as f:
            data = json.load(f)
        return TuneConfiguration(**data)
