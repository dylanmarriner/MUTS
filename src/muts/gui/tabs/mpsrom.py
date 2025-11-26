from __future__ import annotations

from PyQt5 import QtWidgets

from ...services.mpsrom_stack import MPSROMCoordinator


class MPSROMTab(QtWidgets.QWidget):
    def __init__(self, coordinator: MPSROMCoordinator | None = None, parent=None):
        super().__init__(parent)
        self.coordinator = coordinator or MPSROMCoordinator()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("MPS ROM analysis and checksum suite"))
        summary = QtWidgets.QPlainTextEdit()
        summary.setReadOnly(True)
        summary.setPlainText("\n".join(f"{k}: {v}" for k, v in self.coordinator.summary().items()))
        layout.addWidget(summary)

        sub_tabs = QtWidgets.QTabWidget()
        sub_tabs.addTab(MPSROMStructureWidget(self.coordinator), "ROM Structure")
        sub_tabs.addTab(MPSChecksumWidget(self.coordinator), "Checksums")
        sub_tabs.addTab(MPSecurityWidget(self.coordinator), "Security")
        sub_tabs.addTab(MPSMapWidget(self.coordinator), "Maps")
        layout.addWidget(sub_tabs)


class MPSROMStructureWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MPSROMCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget()
        self.detail = QtWidgets.QPlainTextEdit()
        self.detail.setReadOnly(True)
        btn_refresh = QtWidgets.QPushButton("Refresh sectors")
        layout.addWidget(btn_refresh)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.detail)
        btn_refresh.clicked.connect(self.reload)
        self.list_widget.currentTextChanged.connect(self.show_details)
        self.reload()

    def reload(self) -> None:
        self.list_widget.clear()
        for name in self.coordinator.rom.list_sectors():
            defn = self.coordinator.rom.definitions[name]
            self.list_widget.addItem(f"{name} ({defn.size} bytes)")

    def show_details(self, text: str) -> None:
        name = text.split(" ")[0]
        defn = self.coordinator.rom.definitions.get(name)
        if not defn:
            return
        lines = [
            f"Name: {name}",
            f"Address: 0x{defn.base_address:06X}",
            f"Size: {defn.size}",
            f"Checksum algorithm: {defn.checksum_algorithm or 'n/a'}",
            f"Checksum offset: {defn.checksum_offset or 'n/a'}",
            f"Description: {defn.description}",
        ]
        self.detail.setPlainText("\n".join(lines))


class MPSChecksumWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MPSROMCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.sector_combo = QtWidgets.QComboBox()
        self.sector_combo.addItems(self.coordinator.rom.list_sectors())
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_calc = QtWidgets.QPushButton("Calculate & verify")
        btn_patch = QtWidgets.QPushButton("Patch checksum")
        layout.addWidget(self.sector_combo)
        layout.addWidget(btn_calc)
        layout.addWidget(btn_patch)
        layout.addWidget(self.output)
        btn_calc.clicked.connect(self.calculate)
        btn_patch.clicked.connect(self.patch)

    def calculate(self) -> None:
        sector = self.sector_combo.currentText()
        calc, stored, matches = self.coordinator.checksum.verify(sector)
        self.output.appendPlainText(
            f"{sector}: calc=0x{calc:08X} stored=0x{stored:08X} match={matches}"
        )

    def patch(self) -> None:
        sector = self.sector_combo.currentText()
        self.coordinator.checksum.patch(sector)
        self.output.appendPlainText(f"{sector}: patched checksum data")


class MPSecurityWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MPSROMCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_seed = QtWidgets.QPushButton("Request seed")
        btn_unlock = QtWidgets.QPushButton("Unlock level 3")
        layout.addWidget(btn_seed)
        layout.addWidget(btn_unlock)
        layout.addWidget(self.output)
        btn_seed.clicked.connect(self.request_seed)
        btn_unlock.clicked.connect(self.unlock)

    def request_seed(self) -> None:
        seed = self.coordinator.security.request_seed()
        self.output.appendPlainText(f"Seed: 0x{seed:08X}")

    def unlock(self) -> None:
        success = self.coordinator.security.unlock_to(3)
        text = "unlocked level 3" if success else "unlock failed"
        self.output.appendPlainText(text)


class MPSMapWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MPSROMCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.addItems(self.coordinator.maps.groups())
        self.entry_combo = QtWidgets.QComboBox()
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn_refresh = QtWidgets.QPushButton("Describe map")
        layout.addWidget(self.group_combo)
        layout.addWidget(self.entry_combo)
        layout.addWidget(btn_refresh)
        layout.addWidget(self.output)
        self.group_combo.currentTextChanged.connect(self.refresh_entries)
        btn_refresh.clicked.connect(self.describe)
        self.refresh_entries()

    def refresh_entries(self) -> None:
        group = self.group_combo.currentText()
        self.entry_combo.clear()
        self.entry_combo.addItems(self.coordinator.maps.entries_in_group(group))

    def describe(self) -> None:
        group = self.group_combo.currentText()
        entry = self.entry_combo.currentText()
        desc = self.coordinator.maps.describe(group, entry)
        lines = [f"{key}: {value}" for key, value in desc.items()]
        if not lines:
            lines = ["No description available"]
        self.output.setPlainText("\n".join(lines))
