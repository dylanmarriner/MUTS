from __future__ import annotations

from PyQt5 import QtWidgets

from ...services.versa_stack import VersaCoordinator


class VersaTab(QtWidgets.QWidget):
    def __init__(self, coordinator: VersaCoordinator | None = None, parent=None):
        super().__init__(parent)
        self.coordinator = coordinator or VersaCoordinator()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("VersaTuner-inspired toolset"))
        summary = QtWidgets.QPlainTextEdit()
        summary.setReadOnly(True)
        summary.setPlainText("\n".join(f"{k}: {v}" for k, v in self.coordinator.summary().items()))
        layout.addWidget(summary)

        sub_tabs = QtWidgets.QTabWidget()
        sub_tabs.addTab(VersaCommWidget(self.coordinator), "Communicator")
        sub_tabs.addTab(VersaSecurityWidget(self.coordinator), "Security")
        sub_tabs.addTab(VersaROMWidget(self.coordinator), "ROM")
        sub_tabs.addTab(VersaMapWidget(self.coordinator), "Maps")
        sub_tabs.addTab(VersaDiagWidget(self.coordinator), "Diagnostics")
        layout.addWidget(sub_tabs)


class VersaCommWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: VersaCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_connect = QtWidgets.QPushButton("Connect")
        btn_disconnect = QtWidgets.QPushButton("Disconnect")
        btn_request = QtWidgets.QPushButton("Send dummy request")

        layout.addWidget(btn_connect)
        layout.addWidget(btn_disconnect)
        layout.addWidget(btn_request)
        layout.addWidget(self.output)

        btn_connect.clicked.connect(self.connect)
        btn_disconnect.clicked.connect(self.disconnect)
        btn_request.clicked.connect(self.request)

    def connect(self) -> None:
        if self.coordinator.communicator.connect():
            self.output.appendPlainText("Versa communicator connected")
        else:
            self.output.appendPlainText("Failed to connect")

    def disconnect(self) -> None:
        self.coordinator.communicator.disconnect()
        self.output.appendPlainText("Disconnected")

    def request(self) -> None:
        try:
            response = self.coordinator.communicator.send_request(0x10, 0x02)
            self.output.appendPlainText(f"Response: {response.hex().upper()}")
        except RuntimeError as exc:
            self.output.appendPlainText(str(exc))


class VersaSecurityWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: VersaCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_unlock = QtWidgets.QPushButton("Unlock ECU")
        layout.addWidget(btn_unlock)
        layout.addWidget(self.output)
        btn_unlock.clicked.connect(self.unlock)

    def unlock(self) -> None:
        if self.coordinator.security.unlock():
            self.output.appendPlainText("Versa security unlocked")
        else:
            self.output.appendPlainText("Unlock failed")


class VersaROMWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: VersaCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.map_selector = QtWidgets.QComboBox()
        self.map_selector.addItems(self.coordinator.rom.SECTORS.keys())
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_read = QtWidgets.QPushButton("Read sector")
        btn_checksum = QtWidgets.QPushButton("Checksum")

        layout.addWidget(self.map_selector)
        layout.addWidget(btn_read)
        layout.addWidget(btn_checksum)
        layout.addWidget(self.output)

        btn_read.clicked.connect(self.read_sector)
        btn_checksum.clicked.connect(self.checksum)

    def read_sector(self) -> None:
        sector = self.map_selector.currentText()
        data = self.coordinator.rom.read_sector(sector)
        self.output.appendPlainText(f"{sector} read {len(data)} bytes")

    def checksum(self) -> None:
        sector = self.map_selector.currentText()
        value = self.coordinator.rom.checksum(sector)
        self.output.appendPlainText(f"{sector} CRC32 {value}")


class VersaMapWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: VersaCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(self.coordinator.maps.list_maps())
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_adjust = QtWidgets.QPushButton("Adjust cell")
        layout.addWidget(self.list_widget)
        layout.addWidget(btn_adjust)
        layout.addWidget(self.output)
        btn_adjust.clicked.connect(self.adjust)

    def adjust(self) -> None:
        current = self.list_widget.currentItem()
        if not current:
            self.output.appendPlainText("Select a map")
            return
        name = current.text()
        if self.coordinator.maps.adjust_cell(name, 0, 0, 0.5):
            self.output.appendPlainText(f"Modified {name}[0][0]")
        else:
            self.output.appendPlainText("Adjust failed")


class VersaDiagWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: VersaCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_scan = QtWidgets.QPushButton("Scan DTCs")
        btn_clear = QtWidgets.QPushButton("Clear DTCs")
        layout.addWidget(btn_scan)
        layout.addWidget(btn_clear)
        layout.addWidget(self.output)
        btn_scan.clicked.connect(self.scan_dtcs)
        btn_clear.clicked.connect(self.clear_dtcs)

    def scan_dtcs(self) -> None:
        dtcs = self.coordinator.diag.scan_dtcs()
        if not dtcs:
            self.output.appendPlainText("No DTCs")
            return
        for dtc in dtcs:
            self.output.appendPlainText(f"{dtc['code']} - {dtc['severity']}")

    def clear_dtcs(self) -> None:
        if self.coordinator.diag.clear_dtcs():
            self.output.appendPlainText("Cleared DTCs")
        else:
            self.output.appendPlainText("Clear failed")
