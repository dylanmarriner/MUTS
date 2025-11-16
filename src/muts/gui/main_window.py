from PyQt5 import QtWidgets
from .tabs.dashboard import DashboardTab
from .tabs.diagnostics import DiagnosticsTab
from .tabs.tuning import TuningTab
from .tabs.security import SecurityTab
from .tabs.dyno import DynoTab

def run_gui() -> None:
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QMainWindow()
    window.setWindowTitle("MUTS — Mazda Ultimate Technician Suite")
    tabs = QtWidgets.QTabWidget()
    tabs.addTab(DashboardTab(), "Dashboard")
    tabs.addTab(DiagnosticsTab(), "Diagnostics")
    tabs.addTab(TuningTab(), "Tuning")
    tabs.addTab(SecurityTab(), "Security")
    tabs.addTab(DynoTab(), "Dyno")
    window.setCentralWidget(tabs)
    window.resize(1100, 700)
    window.show()
    sys.exit(app.exec_())
