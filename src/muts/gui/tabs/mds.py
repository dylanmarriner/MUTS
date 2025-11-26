from __future__ import annotations

import random

from PyQt5 import QtWidgets

from ...services.mds_stack import (
    MazdaIDSCoordinator,
    MazdaProtocol,
    SecurityAccessLevel,
)


class MDSTab(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator | None = None, parent=None):
        super().__init__(parent)
        self.coordinator = coordinator or MazdaIDSCoordinator()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Mazda IDS/M-MDS inspired suite"))
        summary = QtWidgets.QPlainTextEdit()
        summary.setReadOnly(True)
        summary.setPlainText(self._build_summary())
        layout.addWidget(summary)
        sub_tabs = QtWidgets.QTabWidget()
        sub_tabs.addTab(MDSProtocolWidget(self.coordinator), "Protocol")
        sub_tabs.addTab(MDSSecurityWidget(self.coordinator), "Security")
        sub_tabs.addTab(MDSDiagnosticsWidget(self.coordinator), "Diagnostics")
        sub_tabs.addTab(MDSCalibrationWidget(self.coordinator), "Calibration")
        sub_tabs.addTab(MDSChecksumWidget(self.coordinator), "Checksum")
        layout.addWidget(sub_tabs)

    def _build_summary(self) -> str:
        return (
            f"Active protocol: {self.coordinator.protocol.name}\n"
            f"Session: {self.coordinator.session.name}"
        )


class MDSProtocolWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.combo = QtWidgets.QComboBox()
        for protocol in MazdaProtocol:
            self.combo.addItem(protocol.name, protocol)
        btn = QtWidgets.QPushButton("Switch protocol")
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn.clicked.connect(self.switch)
        layout.addWidget(self.combo)
        layout.addWidget(btn)
        layout.addWidget(self.output)

    def switch(self) -> None:
        protocol = self.combo.currentData()
        if protocol:
            self.coordinator.switch_protocol(protocol)
            self.output.appendPlainText(f"Switched to {protocol.name}")


class MDSSecurityWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.status = QtWidgets.QLabel("Security idle")
        btn = QtWidgets.QPushButton("Calculate level 3 key")
        btn.clicked.connect(self.calculate)
        layout.addWidget(self.status)
        layout.addWidget(btn)

    def calculate(self) -> None:
        seed = 0x1A2B3C4D
        key = self.coordinator.security_manager.solve(SecurityAccessLevel.LEVEL_3, seed)
        self.status.setText(f"Derived key: {hex(key)}")


class MDSDiagnosticsWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(list(self.coordinator.tests.TESTS.keys()))
        btn = QtWidgets.QPushButton("Run test")
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.list_widget)
        layout.addWidget(btn)
        layout.addWidget(self.output)
        btn.clicked.connect(self.run_test)

    def run_test(self) -> None:
        current = self.list_widget.currentItem()
        if not current:
            self.output.appendPlainText("Choose a test")
            return
        name = current.text()
        desc, status = self.coordinator.run_diagnostic_test(name)
        self.output.appendPlainText(f"{desc}: {status.name}")


class MDSCalibrationWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn = QtWidgets.QPushButton("Adjust boost map")
        btn.clicked.connect(self.adjust)
        layout.addWidget(btn)
        layout.addWidget(self.output)

    def adjust(self) -> None:
        if self.coordinator.perform_calibration("boost", 0.5):
            self.output.appendPlainText("Boost map adjusted")
        else:
            self.output.appendPlainText("Adjustment failed")


class MDSChecksumWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        btn_crc = QtWidgets.QPushButton("CRC32")
        btn_crc.clicked.connect(lambda: self.compute("crc32"))
        btn_crc16 = QtWidgets.QPushButton("CRC16")
        btn_crc16.clicked.connect(lambda: self.compute("crc16"))
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(btn_crc)
        layout.addWidget(btn_crc16)
        layout.addWidget(self.output)

    def compute(self, algo: str) -> None:
        value = self.coordinator.calculate_checksum(algo)
        self.output.appendPlainText(f"{algo.upper()} value: {value}")
