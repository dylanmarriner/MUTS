from PyQt5 import QtWidgets

class DashboardTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Vehicle: 2011 Mazdaspeed 3 — VIN 7AT0C13JX20200064"))
        layout.addWidget(QtWidgets.QLabel("ABS/SRS modules ready (no interface connected)"))
