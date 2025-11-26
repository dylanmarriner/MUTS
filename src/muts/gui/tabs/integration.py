"""Integration tab for external tools and high-level stack overview."""

from __future__ import annotations

from PyQt5 import QtWidgets

from ...services.integration_stack import IntegrationCoordinator


class IntegrationTab(QtWidgets.QWidget):
    """Single pane of glass for the coordinated MUTS stacks.

    This tab does *not* talk directly to hardware; instead it queries the
    :class:`IntegrationCoordinator` for a snapshot of all simulated stacks and
    helper services.
    """

    def __init__(self, coordinator: IntegrationCoordinator | None = None, parent=None):
        super().__init__(parent)
        self.coordinator = coordinator or IntegrationCoordinator()
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI wiring
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        # Stack overview
        overview_group = QtWidgets.QGroupBox("Integrated Stack Overview")
        overview_layout = QtWidgets.QVBoxLayout(overview_group)
        self.stack_summary = QtWidgets.QPlainTextEdit()
        self.stack_summary.setReadOnly(True)
        self.refresh_btn = QtWidgets.QPushButton("Refresh Stack Summary")
        self.refresh_btn.clicked.connect(self.refresh_summary)
        overview_layout.addWidget(self.stack_summary)
        overview_layout.addWidget(self.refresh_btn)

        # AI Integration (placeholder  no real external calls)
        ai_group = QtWidgets.QGroupBox("AI Integration")
        ai_layout = QtWidgets.QVBoxLayout(ai_group)
        self.ai_status = QtWidgets.QLabel("AI Status: Offline (demo)")
        self.ai_connect_btn = QtWidgets.QPushButton("Simulate AI Connection")
        self.ai_connect_btn.clicked.connect(self._simulate_ai_connect)
        ai_layout.addWidget(self.ai_status)
        ai_layout.addWidget(self.ai_connect_btn)

        # External tool launchers (conceptual only)
        tools_group = QtWidgets.QGroupBox("External Tools")
        tools_layout = QtWidgets.QVBoxLayout(tools_group)
        self.cobb_btn = QtWidgets.QPushButton("Show Cobb stack status")
        self.versa_btn = QtWidgets.QPushButton("Show Versa stack status")
        self.mds_btn = QtWidgets.QPushButton("Show MDS stack status")
        self.cobb_btn.clicked.connect(lambda: self._show_stack_section("cobb"))
        self.versa_btn.clicked.connect(lambda: self._show_stack_section("versa"))
        self.mds_btn.clicked.connect(lambda: self._show_stack_section("mds"))
        tools_layout.addWidget(self.cobb_btn)
        tools_layout.addWidget(self.versa_btn)
        tools_layout.addWidget(self.mds_btn)

        layout.addWidget(overview_group)
        layout.addWidget(ai_group)
        layout.addWidget(tools_group)
        layout.addStretch()

        # Initial fill
        self.refresh_summary()

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------
    def refresh_summary(self) -> None:
        """Refresh the text view with the current coordinator snapshot."""

        data = self.coordinator.as_dict()
        lines: list[str] = []
        for section, value in data.items():
            lines.append(f"[{section}]")
            if isinstance(value, dict):
                for key, v in value.items():
                    lines.append(f"  {key}: {v}")
            else:
                lines.append(f"  {value}")
            lines.append("")
        self.stack_summary.setPlainText("\n".join(lines))

    def _simulate_ai_connect(self) -> None:
        """Toggle a simple offline status label to avoid real network calls."""

        self.ai_status.setText("AI Status: Connected (simulated)")

    def _show_stack_section(self, section: str) -> None:
        """Scroll/highlight a specific stack section in the summary view."""

        text = self.stack_summary.toPlainText().splitlines()
        for idx, line in enumerate(text):
            if line.strip() == f"[{section}]":
                cursor = self.stack_summary.textCursor()
                block = self.stack_summary.document().findBlockByLineNumber(idx)
                cursor.setPosition(block.position())
                self.stack_summary.setTextCursor(cursor)
                break
