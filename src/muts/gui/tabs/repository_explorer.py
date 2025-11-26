from __future__ import annotations

from pathlib import Path

from PyQt5 import QtWidgets

from ...services.repository_catalog import DirectoryCatalog, RepositoryCatalogService


class RepositoryExplorerTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.catalog = RepositoryCatalogService().catalog()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Repository Explorer"))
        self.sub_tabs = QtWidgets.QTabWidget()
        if not self.catalog:
            layout.addWidget(QtWidgets.QLabel("No catalogued directories found"))
        for entry in self.catalog:
            self.sub_tabs.addTab(DirectoryWidget(entry), entry.name.capitalize())
        layout.addWidget(self.sub_tabs)


class DirectoryWidget(QtWidgets.QWidget):
    def __init__(self, catalog: DirectoryCatalog):
        super().__init__()
        self.catalog = catalog
        layout = QtWidgets.QVBoxLayout(self)
        self.list = QtWidgets.QListWidget()
        for file_summary in self.catalog.files:
            self.list.addItem(file_summary.display)
        button_bar = QtWidgets.QHBoxLayout()
        self.btn_preview = QtWidgets.QPushButton("Preview file")
        self.btn_readme = QtWidgets.QPushButton("Show README")
        self.btn_diagram = QtWidgets.QPushButton("Show diagram")
        button_bar.addWidget(self.btn_preview)
        button_bar.addWidget(self.btn_readme)
        button_bar.addWidget(self.btn_diagram)
        self.detail = QtWidgets.QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.btn_preview.clicked.connect(self.preview_current)
        self.btn_readme.clicked.connect(self.show_readme)
        self.btn_diagram.clicked.connect(self.show_diagram)
        self.btn_readme.setEnabled(bool(self.catalog.readme))
        self.btn_diagram.setEnabled(bool(self.catalog.diagram))
        layout.addLayout(button_bar)
        layout.addWidget(self.list)
        layout.addWidget(self.detail)
        self.list.currentRowChanged.connect(self.preview_current)
        if self.catalog.files:
            self.list.setCurrentRow(0)

    def preview_current(self, row: int | None = None) -> None:
        if row is None:
            row = self.list.currentRow()
        if row < 0 or row >= len(self.catalog.files):
            self.detail.setPlainText("No file selected")
            return
        file_summary = self.catalog.files[row]
        content = self._preview_file(file_summary.path)
        if content:
            self.detail.setPlainText(content)
        else:
            self.detail.setPlainText(file_summary.summary or "(no content available)")

    def show_readme(self) -> None:
        if not self.catalog.readme:
            return
        self.detail.setPlainText(self.catalog.readme)

    def show_diagram(self) -> None:
        if not self.catalog.diagram:
            return
        self.detail.setPlainText(self.catalog.diagram)

    def _preview_file(self, path: Path, max_lines: int = 40) -> str | None:
        try:
            with path.open(encoding="utf-8", errors="ignore") as fh:
                lines = []
                for _ in range(max_lines):
                    line = fh.readline()
                    if not line:
                        break
                    lines.append(line.rstrip("\n"))
                return "\n".join(lines)
        except Exception:
            return None
