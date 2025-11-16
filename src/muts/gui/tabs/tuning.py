from PyQt5 import QtWidgets
from ...services.torque_swas import TorqueSWASService

class TuningTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = TorqueSWASService()
        layout = QtWidgets.QFormLayout(self)
        self.chk_swas = QtWidgets.QCheckBox("Disable SWAS")
        self.chk_boost = QtWidgets.QCheckBox("Remove 1st/2nd Boost Cut (safe)")
        self.btn_apply = QtWidgets.QPushButton("Queue ECU Actions")
        layout.addRow(self.chk_swas)
        layout.addRow(self.chk_boost)
        layout.addRow(self.btn_apply)
        self.btn_apply.clicked.connect(self.apply)

    def apply(self) -> None:
        actions = []
        if self.chk_swas.isChecked():
            actions.append({"type": "swas_override", "value": True})
        if self.chk_boost.isChecked():
            actions.append({"type": "gear_torque_limit", "gears": [1, 2], "delta_nm": 50})
        self.service.queue_actions(actions)
