from PyQt5 import QtWidgets
from ...services.dyno import DynoService

class DynoTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = DynoService()
        layout = QtWidgets.QVBoxLayout(self)
        self.btn = QtWidgets.QPushButton("Run Virtual Pull")
        self.out = QtWidgets.QPlainTextEdit()
        self.out.setReadOnly(True)
        layout.addWidget(self.btn)
        layout.addWidget(self.out)
        self.btn.clicked.connect(self.pull)

    def pull(self) -> None:
        res = self.service.virtual_pull()
        self.out.appendPlainText(f"Peak: {res['peak_hp']} hp / {res['peak_tq']} Nm")
