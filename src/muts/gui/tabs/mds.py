from __future__ import annotations

import random

from PyQt5 import QtWidgets

from ...services.mds_stack import (
    MazdaIDSCoordinator,
    MazdaProtocol,
    SecurityAccessLevel,
)

# Import additional classes from app/mds for enhanced GUI functionality
from app.mds.diagnostics.diagnostic_database import MazdaDTCDatabase
from app.mds.calibration.calibration_files import MazdaCalibrationDatabase
from app.mds.core.ids_software import MazdaIDS


class MDSTab(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator | None = None, parent=None):
        super().__init__(parent)
        self.coordinator = coordinator or MazdaIDSCoordinator()
        
        # Initialize databases for enhanced functionality
        self.dtc_database = MazdaDTCDatabase()
        self.calibration_database = MazdaCalibrationDatabase()
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Mazda IDS/M-MDS inspired suite"))
        summary = QtWidgets.QPlainTextEdit()
        summary.setReadOnly(True)
        summary.setPlainText(self._build_summary())
        layout.addWidget(summary)
        sub_tabs = QtWidgets.QTabWidget()
        sub_tabs.addTab(MDSProtocolWidget(self.coordinator), "Protocol")
        sub_tabs.addTab(MDSSecurityWidget(self.coordinator), "Security")
        sub_tabs.addTab(MDSDiagnosticsWidget(self.coordinator, self.dtc_database), "Diagnostics")
        sub_tabs.addTab(MDSCalibrationWidget(self.coordinator, self.calibration_database), "Calibration")
        sub_tabs.addTab(MDSChecksumWidget(self.coordinator), "Checksum")
        sub_tabs.addTab(MDSVehicleWidget(self.coordinator), "Vehicle")
        layout.addWidget(sub_tabs)

    def _build_summary(self) -> str:
        vehicle_info = self.coordinator.get_vehicle_info()
        summary = (
            f"Active protocol: {self.coordinator.protocol.name}\n"
            f"Session: {self.coordinator.session.name}\n"
        )
        if vehicle_info:
            summary += f"\nVehicle Info:\n"
            for key, value in vehicle_info.items():
                summary += f"  {key}: {value}\n"
        return summary


class MDSProtocolWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.combo = QtWidgets.QComboBox()
        for protocol in MazdaProtocol:
            self.combo.addItem(protocol.name, protocol)
        btn = QtWidgets.QPushButton("Switch protocol")
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        btn.clicked.connect(self.switch)
        layout.addWidget(self.combo)
        layout.addWidget(btn)
        layout.addWidget(self.output)

    def switch(self) -> None:
        protocol = self.combo.currentData()
        if protocol:
            self.coordinator.switch_protocol(protocol)
            self.output.appendPlainText(f"Switched to {protocol.name}")


class MDSSecurityWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        self.status = QtWidgets.QLabel("Security idle")
        btn = QtWidgets.QPushButton("Calculate level 3 key")
        btn.clicked.connect(self.calculate)
        layout.addWidget(self.status)
        layout.addWidget(btn)

    def calculate(self) -> None:
        seed = 0x1A2B3C4D
        key = self.coordinator.security_manager.solve(SecurityAccessLevel.LEVEL_3, seed)
        self.status.setText(f"Derived key: {hex(key)}")


class MDSDiagnosticsWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator, dtc_database: MazdaDTCDatabase):
        super().__init__()
        self.coordinator = coordinator
        self.dtc_database = dtc_database
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(list(self.coordinator.tests.TESTS.keys()))
        btn = QtWidgets.QPushButton("Run test")
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        
        # Add DTC lookup functionality
        dtc_lookup_layout = QtWidgets.QHBoxLayout()
        self.dtc_input = QtWidgets.QLineEdit()
        self.dtc_input.setPlaceholderText("Enter DTC (e.g., P0300)")
        btn_lookup = QtWidgets.QPushButton("Lookup DTC")
        btn_lookup.clicked.connect(self.lookup_dtc)
        dtc_lookup_layout.addWidget(QtWidgets.QLabel("DTC Lookup:"))
        dtc_lookup_layout.addWidget(self.dtc_input)
        dtc_lookup_layout.addWidget(btn_lookup)
        
        layout.addWidget(self.list_widget)
        layout.addWidget(btn)
        layout.addLayout(dtc_lookup_layout)
        layout.addWidget(self.output)
        btn.clicked.connect(self.run_test)

    def run_test(self) -> None:
        current = self.list_widget.currentItem()
        if not current:
            self.output.appendPlainText("Choose a test")
            return
        name = current.text()
        desc, status = self.coordinator.run_diagnostic_test(name)
        self.output.appendPlainText(f"{desc}: {status.name}")
    
    def lookup_dtc(self) -> None:
        dtc_code = self.dtc_input.text().strip()
        if not dtc_code:
            return
        
        dtc_info = self.dtc_database.get_dtc_definition(dtc_code)
        if dtc_info:
            self.output.appendPlainText(f"DTC {dtc_code}:")
            self.output.appendPlainText(f"  Description: {dtc_info.description}")
            self.output.appendPlainText(f"  Severity: {dtc_info.severity.name}")
            self.output.appendPlainText(f"  Symptoms: {', '.join(dtc_info.symptoms)}")
            self.output.appendPlainText(f"  Causes: {', '.join(dtc_info.causes)}")
        else:
            self.output.appendPlainText(f"DTC {dtc_code} not found in database")


class MDSCalibrationWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator, calibration_database: MazdaCalibrationDatabase):
        super().__init__()
        self.coordinator = coordinator
        self.calibration_database = calibration_database
        layout = QtWidgets.QVBoxLayout(self)
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        
        # Add map selection
        map_layout = QtWidgets.QHBoxLayout()
        self.map_combo = QtWidgets.QComboBox()
        self.refresh_maps()
        btn_refresh = QtWidgets.QPushButton("Refresh Maps")
        btn_refresh.clicked.connect(self.refresh_maps)
        map_layout.addWidget(QtWidgets.QLabel("Select Map:"))
        map_layout.addWidget(self.map_combo)
        map_layout.addWidget(btn_refresh)
        
        # Add adjustment controls
        adjust_layout = QtWidgets.QHBoxLayout()
        self.adjustment_spin = QtWidgets.QDoubleSpinBox()
        self.adjustment_spin.setRange(-10.0, 10.0)
        self.adjustment_spin.setSingleStep(0.1)
        self.adjustment_spin.setValue(0.5)
        btn_adjust = QtWidgets.QPushButton("Adjust Map")
        btn_adjust.clicked.connect(self.adjust_selected_map)
        adjust_layout.addWidget(QtWidgets.QLabel("Adjustment:"))
        adjust_layout.addWidget(self.adjustment_spin)
        adjust_layout.addWidget(btn_adjust)
        
        btn = QtWidgets.QPushButton("Adjust boost map")
        btn.clicked.connect(self.adjust)
        layout.addLayout(map_layout)
        layout.addLayout(adjust_layout)
        layout.addWidget(btn)
        layout.addWidget(self.output)

    def refresh_maps(self) -> None:
        self.map_combo.clear()
        maps = self.coordinator.calibration.list_maps()
        self.map_combo.addItems(maps)
    
    def adjust_selected_map(self) -> None:
        map_name = self.map_combo.currentText()
        if not map_name:
            self.output.appendPlainText("No map selected")
            return
        
        delta = self.adjustment_spin.value()
        if self.coordinator.perform_calibration(map_name, delta):
            self.output.appendPlainText(f"{map_name} map adjusted by {delta}")
        else:
            self.output.appendPlainText(f"Failed to adjust {map_name} map")

    def adjust(self) -> None:
        if self.coordinator.perform_calibration("boost", 0.5):
            self.output.appendPlainText("Boost map adjusted")
        else:
            self.output.appendPlainText("Adjustment failed")


class MDSChecksumWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        btn_crc = QtWidgets.QPushButton("CRC32")
        btn_crc.clicked.connect(lambda: self.compute("crc32"))
        btn_crc16 = QtWidgets.QPushButton("CRC16")
        btn_crc16.clicked.connect(lambda: self.compute("crc16"))
        btn_mazda = QtWidgets.QPushButton("Mazda Proprietary")
        btn_mazda.clicked.connect(lambda: self.compute("mazda"))
        self.output = QtWidgets.QPlainTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(btn_crc)
        layout.addWidget(btn_crc16)
        layout.addWidget(btn_mazda)
        layout.addWidget(self.output)

    def compute(self, algo: str) -> None:
        value = self.coordinator.calculate_checksum(algo)
        self.output.appendPlainText(f"{algo.upper()} value: {value}")


class MDSVehicleWidget(QtWidgets.QWidget):
    def __init__(self, coordinator: MazdaIDSCoordinator):
        super().__init__()
        self.coordinator = coordinator
        layout = QtWidgets.QVBoxLayout(self)
        
        # Connection controls
        conn_layout = QtWidgets.QHBoxLayout()
        btn_connect = QtWidgets.QPushButton("Connect to Vehicle")
        btn_disconnect = QtWidgets.QPushButton("Disconnect")
        btn_connect.clicked.connect(self.connect_vehicle)
        btn_disconnect.clicked.connect(self.disconnect_vehicle)
        conn_layout.addWidget(btn_connect)
        conn_layout.addWidget(btn_disconnect)
        
        # Vehicle info display
        self.info_display = QtWidgets.QPlainTextEdit()
        self.info_display.setReadOnly(True)
        
        # Status label
        self.status_label = QtWidgets.QLabel("Not connected")
        
        layout.addLayout(conn_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(QtWidgets.QLabel("Vehicle Information:"))
        layout.addWidget(self.info_display)
        
        # Update initial status
        self.update_status()

    def connect_vehicle(self) -> None:
        self.status_label.setText("Connecting...")
        success = self.coordinator.connect_to_vehicle()
        if success:
            self.status_label.setText("Connected")
            self.update_vehicle_info()
        else:
            self.status_label.setText("Connection failed")

    def disconnect_vehicle(self) -> None:
        self.coordinator.disconnect_from_vehicle()
        self.status_label.setText("Disconnected")
        self.info_display.clear()

    def update_status(self) -> None:
        if hasattr(self.coordinator, 'ids') and self.coordinator.ids.vehicle_connected:
            self.status_label.setText("Connected")
            self.update_vehicle_info()
        else:
            self.status_label.setText("Not connected")

    def update_vehicle_info(self) -> None:
        vehicle_info = self.coordinator.get_vehicle_info()
        if vehicle_info:
            info_text = "Vehicle Information:\n"
            for key, value in vehicle_info.items():
                info_text += f"  {key}: {value}\n"
            
            # Add system status
            system_status = self.coordinator.ids.get_system_status()
            info_text += "\nSystem Status:\n"
            for key, value in system_status.items():
                info_text += f"  {key}: {value}\n"
            
            self.info_display.setPlainText(info_text)
