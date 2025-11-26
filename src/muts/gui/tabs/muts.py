from __future__ import annotations

import random

from PyQt5 import QtWidgets

from ...services.muts_stack import MutsCoordinator


class MUTSTab(QtWidgets.QWidget):
    def __init__(self, coordinator: MutsCoordinator | None = None, parent=None):
        super().__init__(parent)
        self.coordinator = coordinator or MutsCoordinator()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("MUTS deep stack (security, SRS, EEPROM, knowledge)"))
        summary = QtWidgets.QPlainTextEdit()
        summary.setReadOnly(True)
        summary.setPlainText("\n".join(f"{k}: {v}" for k, v in self.coordinator.summary().items()))
        layout.addWidget(summary)
        sub_tabs = QtWidgets.QTabWidget()
        sub_tabs.addTab(MUTSSecurityWidget(self.coordinator), "Security")
        sub_tabs.addTab(MUTSSRSWidget(self.coordinator), "SRS")
        sub_tabs.addTab(MUTSEEPROMWidget(self.coordinator), "EEPROM")
        sub_tabs.addTab(MUTSBackdoorWidget(self.coordinator), "Backdoors")
        sub_tabs.addTab(MUTSExploitWidget(self.coordinator), "Exploits")
        sub_tabs.addTab(MUTSKnowledgeWidget(self.coordinator), "Knowledge")
        layout.addWidget(sub_tabs)


class MUTSSecurityWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MutsCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn = QtWidgets.QPushButton("Unlock to level 5")
        btn.clicked.connect(self.unlock)
        layout.addWidget(btn)
        layout.addWidget(self.output)

    def unlock(self) -> None:
        success = self.coordinator.security.unlock(5)
        key = self.coordinator.security.calculate_key(5)
        seed = self.coordinator.security.last_seed
        self.output.appendPlainText(f"Seed: 0x{seed:04X} Key: 0x{key:04X} Unlock: {'ok' if success else 'failed'}")


class MUTSSRSWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MutsCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_manufacturer = QtWidgets.QPushButton("Manufacturer method")
        btn_timing = QtWidgets.QPushButton("Timing attack")
        btn_manufacturer.clicked.connect(lambda: self.attempt("manufacturer"))
        btn_timing.clicked.connect(lambda: self.attempt("timing"))
        layout.addWidget(btn_manufacturer)
        layout.addWidget(btn_timing)
        layout.addWidget(self.output)

    def attempt(self, method: str) -> None:
        granted = self.coordinator.srs.attempt_unlock(method)
        self.output.appendPlainText(f"{method}: {'granted' if granted else 'denied'} ({self.coordinator.srs.current_status()})")


class MUTSEEPROMWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MutsCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_patch = QtWidgets.QPushButton("Apply EEPROM patch")
        btn_patch.clicked.connect(self.apply_patch)
        layout.addWidget(btn_patch)
        layout.addWidget(self.output)

    def apply_patch(self) -> None:
        token = self.coordinator.eeprom.apply_patch("crash_history")
        self.output.appendPlainText(f"Patch applied token {token}")
        for entry in self.coordinator.eeprom.patch_history():
            self.output.appendPlainText(entry)


class MUTSBackdoorWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MutsCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        for mode in ["FACTORY", "DEALER", "SERVICE"]:
            btn = QtWidgets.QPushButton(f"Engage {mode}")
            btn.clicked.connect(lambda _checked, m=mode: self.engage(m))
            layout.addWidget(btn)
        layout.addWidget(self.output)

    def engage(self, mode: str) -> None:
        self.output.appendPlainText(self.coordinator.backdoor.engage(mode))
        for log in self.coordinator.backdoor.history():
            self.output.appendPlainText(log)


class MUTSExploitWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MutsCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn = QtWidgets.QPushButton("Apply racing exploit")
        btn.clicked.connect(self.exploit)
        layout.addWidget(btn)
        layout.addWidget(self.output)
        for feature in self.coordinator.exploit.list_features():
            self.output.appendPlainText(f"feature: {feature}")

    def exploit(self) -> None:
        feature = random.choice(self.coordinator.exploit.list_features())
        self.output.appendPlainText(self.coordinator.exploit.simulate_racing_feature(feature))


class MUTSKnowledgeWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MutsCoordinator):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(QtWidgets.QLabel("Factory knowledge references"))
        layout.addWidget(self.output)
        for entry in coordinator.knowledge.entries():
            self.output.appendPlainText(entry)
