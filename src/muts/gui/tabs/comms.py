"""Communications tab for protocol and interface management"""

from PyQt5 import QtWidgets, QtCore

class CommsTab(QtWidgets.QWidget):
    """Communications tab for protocol management"""

    def __init__(self, coordinator=None, parent=None):
        super().__init__(parent)
        self.coordinator = coordinator
        self.setup_ui()

    def setup_ui(self):
        """Setup communications UI"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Interface selection
        interface_group = QtWidgets.QGroupBox("Interface Selection")
        interface_layout = QtWidgets.QFormLayout(interface_group)
        
        self.interface_combo = QtWidgets.QComboBox()
        self.interface_combo.addItems(["Simulation", "J2534", "CAN Bus", "OBD-II"])
        
        self.port_combo = QtWidgets.QComboBox()
        self.port_combo.addItems(["COM1", "COM2", "COM3", "can0", "can1"])
        
        interface_layout.addRow("Interface:", self.interface_combo)
        interface_layout.addRow("Port:", self.port_combo)
        
        # Protocol settings
        protocol_group = QtWidgets.QGroupBox("Protocol Settings")
        protocol_layout = QtWidgets.QFormLayout(protocol_group)
        
        self.protocol_combo = QtWidgets.QComboBox()
        self.protocol_combo.addItems(["ISO-TP", "UDS", "KWP2000", "OBD-II"])
        
        self.baud_combo = QtWidgets.QComboBox()
        self.baud_combo.addItems(["500000", "250000", "125000", "38400", "9600"])
        
        protocol_layout.addRow("Protocol:", self.protocol_combo)
        protocol_layout.addRow("Baud Rate:", self.baud_combo)
        
        # Message log
        self.message_log = QtWidgets.QPlainTextEdit()
        self.message_log.setReadOnly(True)
        layout.addWidget(self.message_log)
