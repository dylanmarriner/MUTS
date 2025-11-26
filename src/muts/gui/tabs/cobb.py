from __future__ import annotations

from PyQt5 import QtWidgets

from ...services.cobb_stack import CobbCoordinator, CobbSecurityService


class CobbTab(QtWidgets.QWidget):
    def __init__(self, coordinator: CobbCoordinator | None = None, parent=None):
        super().__init__(parent)
        self.coordinator = coordinator or CobbCoordinator()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Cobb integration overview"))
        summary = QtWidgets.QPlainTextEdit()
        summary.setReadOnly(True)
        summary.setPlainText(
            "\n".join(f"{key}: {value}" for key, value in self.coordinator.summary().items())
        )
        layout.addWidget(summary)

        sub_tabs = QtWidgets.QTabWidget()
        sub_tabs.addTab(CobbSecurityWidget(self.coordinator), "Security")
        sub_tabs.addTab(CobbJ2534Widget(self.coordinator), "J2534")
        sub_tabs.addTab(CobbMapWidget(self.coordinator), "ECU Map")
        sub_tabs.addTab(CobbHardwareWidget(self.coordinator), "Hardware")
        sub_tabs.addTab(CobbOBDWidget(self.coordinator), "OBD")
        sub_tabs.addTab(CobbFlashWidget(self.coordinator), "Flash")
        sub_tabs.addTab(CobbRealtimeWidget(self.coordinator), "Realtime")
        layout.addWidget(sub_tabs)


class CobbSecurityWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: CobbCoordinator):
        super().__init__()
        self.coordinator = coordinator
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_seed = QtWidgets.QPushButton("Request seed")
        btn_unlock = QtWidgets.QPushButton("Unlock ECU")
        btn_ident = QtWidgets.QPushButton("Read identification")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(btn_seed)
        layout.addWidget(btn_unlock)
        layout.addWidget(btn_ident)
        layout.addWidget(self.output)

        btn_seed.clicked.connect(self.request_seed)
        btn_unlock.clicked.connect(self.unlock_ecu)
        btn_ident.clicked.connect(self.read_identification)

    def request_seed(self) -> None:
        seed = self.coordinator.security.request_seed(CobbSecurityService.TUNING_LEVEL)
        self.output.appendPlainText(f"Seed: {seed:04X}")

    def unlock_ecu(self) -> None:
        level = CobbSecurityService.TUNING_LEVEL
        success = self.coordinator.security.unlock_ecu(level)
        self.output.appendPlainText("ECU unlocked" if success else "Unlock failed")

    def read_identification(self) -> None:
        ident = self.coordinator.security.read_identification()
        for key, value in ident.items():
            self.output.appendPlainText(f"{key}: {value}")


class CobbJ2534Widget(QtWidgets.QWidget):
    def __init__(self, coordinator: CobbCoordinator):
        super().__init__()
        self.coordinator = coordinator
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_connect = QtWidgets.QPushButton("Connect (simulated)")
        btn_disconnect = QtWidgets.QPushButton("Disconnect")
        btn_read = QtWidgets.QPushButton("Read messages")
        btn_write = QtWidgets.QPushButton("Write test payload")
        btn_load_driver = QtWidgets.QPushButton("Load real J2534 driver (cobb2)")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(btn_connect)
        layout.addWidget(btn_disconnect)
        layout.addWidget(btn_read)
        layout.addWidget(btn_write)
        layout.addWidget(btn_load_driver)
        layout.addWidget(self.output)

        btn_connect.clicked.connect(self.connect)
        btn_disconnect.clicked.connect(self.disconnect)
        btn_read.clicked.connect(self.read)
        btn_write.clicked.connect(self.write)
        btn_load_driver.clicked.connect(self.load_real_driver)

    def connect(self) -> None:
        if self.coordinator.j2534.connect():
            self.output.appendPlainText("PassThru connected (simulated)")
        else:
            self.output.appendPlainText("Connection failed")

    def disconnect(self) -> None:
        self.coordinator.j2534.disconnect()
        self.output.appendPlainText("Disconnected")

    def read(self) -> None:
        messages = self.coordinator.j2534.read_messages()
        if not messages:
            self.output.appendPlainText("No messages")
            return
        for msg in messages:
            self.output.appendPlainText(f"{msg['id']} => {msg['payload']}")

    def write(self) -> None:
        payload = b"\x10\x02\x3E\x00"
        success = self.coordinator.j2534.write_messages(payload)
        self.output.appendPlainText("Write queued" if success else "Write failed")

    def load_real_driver(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select J2534 DLL",
            "",
            "DLL files (*.dll);;All files (*)",
        )
        if not path:
            return
        if self.coordinator.j2534.load_real_driver(path):
            self.output.appendPlainText(f"Loaded real J2534 driver from: {path}")
        else:
            self.output.appendPlainText("Failed to load real J2534 driver (cobb2/J2534Protocol not available)")


class CobbMapWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: CobbCoordinator):
        super().__init__()
        self.coordinator = coordinator
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_list = QtWidgets.QPushButton("List calibration tables (simulated)")
        btn_describe = QtWidgets.QPushButton("Describe selected table")
        btn_list_mzrecu = QtWidgets.QPushButton("List MZRECU tables (cobb3)")
        self.table_input = QtWidgets.QLineEdit()
        self.table_input.setPlaceholderText("Enter table name")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(btn_list)
        layout.addWidget(btn_list_mzrecu)
        layout.addWidget(self.table_input)
        layout.addWidget(btn_describe)
        layout.addWidget(self.output)

        btn_list.clicked.connect(self.list_tables)
        btn_describe.clicked.connect(self.describe)
        btn_list_mzrecu.clicked.connect(self.list_mzrecu_tables)

    def list_tables(self) -> None:
        tables = self.coordinator.mapping.list_tables()
        self.output.appendPlainText("Tables: " + ", ".join(tables))

    def list_mzrecu_tables(self) -> None:
        ecu_model = getattr(self.coordinator, "ecu_model", None)
        if ecu_model is None:
            self.output.appendPlainText("MZRECU model not available (cobb3 import failed)")
            return
        tables = sorted(ecu_model.CALIBRATION_TABLES.keys())
        self.output.appendPlainText("MZRECU tables: " + ", ".join(tables))

    def describe(self) -> None:
        name = self.table_input.text().strip()
        desc = self.coordinator.mapping.describe_table(name)
        self.output.appendPlainText(f"{name}: {desc}")


class CobbHardwareWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: CobbCoordinator):
        super().__init__()
        self.coordinator = coordinator
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_power = QtWidgets.QPushButton("Toggle power (simulated)")
        btn_button = QtWidgets.QPushButton("Press action button")
        btn_virtual_ap = QtWidgets.QPushButton("Start virtual AP emulator (cobb5)")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(btn_power)
        layout.addWidget(btn_button)
        layout.addWidget(btn_virtual_ap)
        layout.addWidget(self.output)

        btn_power.clicked.connect(self.toggle_power)
        btn_button.clicked.connect(self.press_button)
        btn_virtual_ap.clicked.connect(self.start_virtual_ap)

    def toggle_power(self) -> None:
        status = self.coordinator.hardware.toggle_power()
        self.output.appendPlainText(status)

    def press_button(self) -> None:
        result = self.coordinator.hardware.press_button("ACTION")
        self.output.appendPlainText(result)

    def start_virtual_ap(self) -> None:
        if self.coordinator.start_virtual_ap():
            self.output.appendPlainText("Virtual Cobb AP emulator started")
        else:
            self.output.appendPlainText(
                "Failed to start virtual AP emulator (cobb5 or USB stack not available)"
            )


class CobbOBDWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: CobbCoordinator):
        super().__init__()
        self.coordinator = coordinator
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_scan = QtWidgets.QPushButton("Scan DTCs")
        btn_clear = QtWidgets.QPushButton("Clear DTCs")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(btn_scan)
        layout.addWidget(btn_clear)
        layout.addWidget(self.output)

        btn_scan.clicked.connect(self.scan)
        btn_clear.clicked.connect(self.clear)

    def scan(self) -> None:
        dtcs = self.coordinator.obd.read_dtcs()
        if not dtcs:
            self.output.appendPlainText("No DTCs found")
            return
        for dtc in dtcs:
            self.output.appendPlainText(f"{dtc['code']} - {dtc['description']}")

    def clear(self) -> None:
        if self.coordinator.obd.clear_dtcs():
            self.output.appendPlainText("DTCs cleared")
        else:
            self.output.appendPlainText("Failed to clear DTCs")


class CobbFlashWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: CobbCoordinator):
        super().__init__()
        self.coordinator = coordinator
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_flash = QtWidgets.QPushButton("Flash sample calibration")
        self.table_input = QtWidgets.QLineEdit()
        self.table_input.setPlaceholderText("Table name (e.g., boost_map)")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.table_input)
        layout.addWidget(btn_flash)
        layout.addWidget(self.output)

        btn_flash.clicked.connect(self.flash)

    def flash(self) -> None:
        table = self.table_input.text().strip() or "boost_map"
        payload = (table * 64).encode("ascii", errors="ignore")[:256]
        result = self.coordinator.flash.flash_calibration(table, payload)
        self.output.appendPlainText(f"Flash result: {result}")


class CobbRealtimeWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: CobbCoordinator):
        super().__init__()
        self.coordinator = coordinator
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        self.btn_sample = QtWidgets.QPushButton("Capture realtime snapshot")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.btn_sample)
        layout.addWidget(self.output)

        self.btn_sample.clicked.connect(self.capture)

    def capture(self) -> None:
        sample = self.coordinator.monitor.sample()
        self.output.appendPlainText(f"Snapshot: {sample}")
