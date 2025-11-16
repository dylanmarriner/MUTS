"""SWAS management helpers."""
from __future__ import annotations

from diagnostics.bcm_module import BcmModule

class SwasManager:
    def __init__(self, bcm: BcmModule):
        self.bcm = bcm

    def is_enabled(self) -> bool:
        return self.bcm.read_swas_state().enabled

    def set_enabled(self, enabled: bool) -> None:
        self.bcm.set_swas_state(enabled)
