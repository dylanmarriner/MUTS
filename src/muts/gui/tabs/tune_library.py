from __future__ import annotations

from PyQt5 import QtWidgets

from ...services.tune_library import TuneLibraryService


class TuneLibraryTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = TuneLibraryService()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Tune templates derived from mps safe/premium files"))
        tab = QtWidgets.QTabWidget()
        for category in self.service.categories():
            tab.addTab(TuneCategoryWidget(self.service, category), category)
        layout.addWidget(tab)


class TuneCategoryWidget(QtWidgets.QWidget):
    def __init__(self, service: TuneLibraryService, category: str):
        super().__init__()
        self.service = service
        self.category = category
        tunes = self.service.get_tunes(category)
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Grade", "Power", "Torque", "Max boost", "AFR @ WOT"])
        self.detail = QtWidgets.QPlainTextEdit()
        self.detail.setReadOnly(True)
        btn_detail = QtWidgets.QPushButton("Show details")
        layout.addWidget(self.table)
        layout.addWidget(btn_detail)
        layout.addWidget(self.detail)
        self._populate_table(tunes)
        btn_detail.clicked.connect(self.show_details)

    def _populate_table(self, tunes):
        self.table.setRowCount(len(tunes))
        for row, (key, tune) in enumerate(tunes.items()):
            values = [
                key,
                tune.target_power,
                tune.target_torque,
                f"{tune.max_boost:.1f} psi",
                f"{tune.target_afr:.2f}",
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(value))

    def show_details(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        grade_item = self.table.item(row, 0)
        if not grade_item:
            return
        key = grade_item.text()
        tune = self.service.get_metadata(self.category, key)
        lines = [
            f"Grade: {tune.fuel_grade}",
            f"Description: {tune.description}",
            f"Safety: {tune.safety_margin}",
            f"Knock response: {tune.knock_response}",
            f"Max timing: {tune.max_timing}°",
            f"Target AFR (WOT): {tune.target_afr}",
        ]
        self.detail.setPlainText("\n".join(lines))
