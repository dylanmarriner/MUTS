from __future__ import annotations

"""High-level integration stack that composes all MUTS service coordinators.

This module provides a single entry point that wires together the toy/simulated
Cobb, Versa, MDS, MUTS and MPS ROM stacks plus diagnostics, tune library,
security and dyno helpers. It is intentionally "orchestration only" – no
hardware access or real-world exploit logic is added here.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict

from .cobb_stack import CobbCoordinator
from .diagnostic_manager import DEFAULT_VIN
from .diagnostics import DiagnosticsService
from .dyno import DynoService
from .mds_stack import MazdaIDSCoordinator
from .mpsrom_stack import MPSROMCoordinator
from .muts_stack import MutsCoordinator
from .security import SecurityService
from .tune_library import TuneLibraryService
from .torque_swas import TorqueSWASService
from .versa_stack import VersaCoordinator
from .comms_service import CommunicationService


@dataclass
class StackSummary:
    """Lightweight snapshot of the integrated stack state.

    This is primarily used by the GUI integration tab to present a
    "single-pane" view of all major subsystems.
    """

    muts: Dict[str, str]
    versa: Dict[str, str]
    cobb: Dict[str, str]
    mds: Dict[str, str]
    mpsrom: Dict[str, str]
    diagnostics: Dict[str, object]
    dyno: Dict[str, object]
    tune_library_profiles: Dict[str, int]


class IntegrationCoordinator:
    """Compose all high-level services into a single coordination point.

    The goal is to make it easy for the GUI (and future automation) to see and
    drive the complete "stack" without every tab needing to recreate its own
    coordinators.
    """

    def __init__(self, vin: str = DEFAULT_VIN) -> None:
        self.vin = vin

        # Deep stacks / ecosystems
        self.muts = MutsCoordinator(vin)
        self.versa = VersaCoordinator(vin)
        self.cobb = CobbCoordinator(vin)
        self.mds = MazdaIDSCoordinator(vin)
        self.mpsrom = MPSROMCoordinator(vin)

        # Cross-cutting services
        self.diagnostics = DiagnosticsService(vin)
        self.tune_library = TuneLibraryService()
        self.dyno = DynoService()
        self.security = SecurityService()
        self.tuning = TorqueSWASService()
        self.comms = CommunicationService()

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    def stack_summaries(self) -> StackSummary:
        """Build a structured snapshot of all major subsystems.

        This intentionally calls the existing summary/health helpers on each
        stack instead of duplicating logic.
        """

        mds_summary = {
            "protocol": getattr(self.mds.protocol, "name", str(self.mds.protocol)),
            "session": getattr(self.mds.session, "name", str(self.mds.session)),
        }

        tune_profiles: Dict[str, int] = {
            category: len(self.tune_library.get_tunes(category))
            for category in self.tune_library.categories()
        }

        return StackSummary(
            muts=self.muts.summary(),
            versa=self.versa.summary(),
            cobb=self.cobb.summary(),
            mds=mds_summary,
            mpsrom=self.mpsrom.summary(),
            diagnostics=self.diagnostics.manager.health_report(),
            dyno=self.dyno.virtual_pull(),
            tune_library_profiles=tune_profiles,
        )

    def as_dict(self) -> Dict[str, Any]:
        """Return the current stack summary as a plain dictionary.

        Useful for logging, debugging and simple GUI presentation.
        """

        return asdict(self.stack_summaries())

