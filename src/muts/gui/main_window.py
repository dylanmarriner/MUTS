from PyQt5 import QtWidgets

from ..services.integration_stack import IntegrationCoordinator
from .tabs.cobb import CobbTab
from .tabs.comms import CommsTab
from .tabs.dashboard import DashboardTab
from .tabs.diagnostic_library import DiagnosticLibraryTab
from .tabs.diagnostics import DiagnosticsTab
from .tabs.dyno import DynoTab
from .tabs.integration import IntegrationTab
from .tabs.mds import MDSTab
from .tabs.mpsrom import MPSROMTab
from .tabs.muts import MUTSTab
from .tabs.repository_explorer import RepositoryExplorerTab
from .tabs.security import SecurityTab
from .tabs.tune_library import TuneLibraryTab
from .tabs.tuning import TuningTab
from .tabs.versa import VersaTab


def run_gui() -> None:
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("MUTS — Mazda Ultimate Technician Suite")

    # Single place where all the simulated stacks are wired together
    integration = IntegrationCoordinator()

    tabs = QtWidgets.QTabWidget()
    tabs.addTab(DashboardTab(), "Dashboard")
    tabs.addTab(DiagnosticsTab(), "Diagnostics")
    tabs.addTab(DiagnosticLibraryTab(), "Diagnostic Library")
    tabs.addTab(TuningTab(), "Tuning")
    tabs.addTab(SecurityTab(), "Security")
    tabs.addTab(DynoTab(), "Dyno")
    tabs.addTab(IntegrationTab(integration), "Integration")
    tabs.addTab(CobbTab(integration.cobb), "Cobb Stack")
    tabs.addTab(VersaTab(integration.versa), "Versa Stack")
    tabs.addTab(MDSTab(integration.mds), "MDS Stack")
    tabs.addTab(MPSROMTab(integration.mpsrom), "MPS ROM")
    tabs.addTab(TuneLibraryTab(), "Tune Library")
    tabs.addTab(MUTSTab(integration.muts), "MUTS Stack")
    tabs.addTab(CommsTab(integration.comms), "Comms")
    tabs.addTab(RepositoryExplorerTab(), "Repo Explorer")

    window.setCentralWidget(tabs)
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec_())
