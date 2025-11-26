from __future__ import annotations

from PyQt5 import QtCore, QtWidgets

from ...services.diagnostic_database import DiagnosticDatabaseService


class DiagnosticLibraryTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = DiagnosticDatabaseService()
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("Mazdaspeed 3 diagnostic PID/DTC reference")
        layout.addWidget(label)
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(PIDLibraryWidget(self.service), "PIDs")
        tabs.addTab(DTCLibraryWidget(self.service), "DTCs")
        layout.addWidget(tabs)


class PIDLibraryWidget(QtWidgets.QWidget):
    def __init__(self, service: DiagnosticDatabaseService):
        super().__init__()
        self.service = service
        layout = QtWidgets.QVBoxLayout(self)
        controls = QtWidgets.QHBoxLayout()
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search PID or description")
        self.chk_mazda = QtWidgets.QCheckBox("Mazda-specific only")
        self.chk_proprietary = QtWidgets.QCheckBox("Proprietary (22xx)")
        btn_refresh = QtWidgets.QPushButton("Refresh")
        controls.addWidget(self.search)
        controls.addWidget(self.chk_mazda)
        controls.addWidget(self.chk_proprietary)
        controls.addWidget(btn_refresh)
        layout.addLayout(controls)
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["PID", "Description", "Formula", "Units", "Bytes", "Mazda-specific"]
        )
        layout.addWidget(self.table)
        btn_refresh.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        rows = self.service.list_pids(
            query=self.search.text(),
            mazda_only=self.chk_mazda.isChecked() or None,
            proprietary_only=self.chk_proprietary.isChecked(),
        )
        self.table.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            for col, key in enumerate(
                ["pid", "description", "formula", "units", "byte_length", "mazda_specific"]
            ):
                item = QtWidgets.QTableWidgetItem(row[key])
                if col == 0:
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsSelectable)
                self.table.setItem(idx, col, item)


class DTCLibraryWidget(QtWidgets.QWidget):
    def __init__(self, service: DiagnosticDatabaseService):
        super().__init__()
        self.service = service
        layout = QtWidgets.QVBoxLayout(self)
        controls = QtWidgets.QHBoxLayout()
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Search DTC code or description")
        self.severity = QtWidgets.QComboBox()
        self.severity.addItem("All", "")
        self.severity.addItem("LOW")
        self.severity.addItem("MEDIUM")
        self.severity.addItem("HIGH")
        self.chk_mazda = QtWidgets.QCheckBox("Mazda-specific only")
        btn_refresh = QtWidgets.QPushButton("Refresh")
        controls.addWidget(self.search)
        controls.addWidget(self.severity)
        controls.addWidget(self.chk_mazda)
        controls.addWidget(btn_refresh)
        layout.addLayout(controls)
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Code", "Description", "Severity", "Common causes"])
        layout.addWidget(self.table)
        btn_refresh.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        severity = self.severity.currentData()
        rows = self.service.list_dtcs(
            severity=severity,
            mazda_specific=self.chk_mazda.isChecked() or None,
            query=self.search.text(),
        )
        self.table.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            self.table.setItem(idx, 0, QtWidgets.QTableWidgetItem(row["code"]))
            self.table.setItem(idx, 1, QtWidgets.QTableWidgetItem(row["description"]))
            self.table.setItem(idx, 2, QtWidgets.QTableWidgetItem(row["severity"]))
            self.table.setItem(idx, 3, QtWidgets.QTableWidgetItem(row["causes"]))
