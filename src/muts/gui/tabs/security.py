from PyQt5 import QtWidgets
from ...services.security import SecurityService

class SecurityTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = SecurityService()
        layout = QtWidgets.QFormLayout(self)
        self.chk_valet = QtWidgets.QCheckBox("Enable Valet Mode")
        self.pin = QtWidgets.QLineEdit()
        self.pin.setEchoMode(QtWidgets.QLineEdit.Password)
        self.btn_apply = QtWidgets.QPushButton("Apply")
        layout.addRow(self.chk_valet)
        layout.addRow("PIN", self.pin)
        layout.addRow(self.btn_apply)
        self.btn_apply.clicked.connect(self.apply)

    def apply(self) -> None:
        pin = self.pin.text() or "0000"
        if self.chk_valet.isChecked():
            self.service.enable_valet(pin)
        else:
            self.service.disable_valet(pin)
