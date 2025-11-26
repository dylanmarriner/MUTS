from PyQt5 import QtWidgets
from ...services.diagnostics import DiagnosticsService

class DiagnosticsTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = DiagnosticsService()
        layout = QtWidgets.QVBoxLayout(self)
        self.btn_read = QtWidgets.QPushButton("Read DTCs (Sim)")
        self.btn_clear = QtWidgets.QPushButton("Clear DTCs (Sim)")
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.btn_read)
        layout.addWidget(self.btn_clear)
        layout.addWidget(self.output)
        self.btn_read.clicked.connect(self.read_dtcs)
        self.btn_clear.clicked.connect(self.clear_dtcs)

    def read_dtcs(self) -> None:
        codes = self.service.read_dtcs()
        if codes:
            formatted = ", ".join(f"{c['code']} ({c.get('severity')})" for c in codes)
            msg = f"DTCs: {formatted}"
        else:
            msg = "No DTCs."
        self.output.appendPlainText(msg)

    def clear_dtcs(self) -> None:
        ok = self.service.clear_dtcs()
        self.output.appendPlainText("Cleared." if ok else "Failed to clear.")
