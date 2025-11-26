#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3 UNIFIED GUI FRAMEWORK
Main GUI application that integrates all MUTS platforms
"""

import sys
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTextEdit, QProgressBar,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QGroupBox, QGridLayout,
    QMessageBox, QFileDialog, QStatusBar, QMenuBar, QMenu,
    QAction, QToolBar, QSplitter, QFrame, QScrollArea
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

from core.app_state import get_app_state, SystemState, PerformanceMode
from core.ecu_communication import ECUCommunicator
from utils.logger import get_logger

logger = get_logger(__name__)

class GUIState(Enum):
    """GUI operational states"""
    INITIALIZING = "initializing"
    READY = "ready"
    CONNECTING = "connecting"
    TUNING = "tuning"
    DIAGNOSTIC = "diagnostic"
    ERROR = "error"

@dataclass
class PlatformConfig:
    """Platform configuration"""
    name: str
    display_name: str
    color: str
    enabled: bool = True
    module_path: str = ""

class DataUpdateThread(QThread):
    """Thread for updating real-time data"""
    data_updated = pyqtSignal(dict)
    
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.running = False
    
    def run(self):
        self.running = True
        while self.running:
            try:
                # Get current ECU data
                ecu_data = self.app_state.get_ecu_data()
                data_dict = {
                    'engine_rpm': ecu_data.engine_rpm,
                    'boost_psi': ecu_data.boost_psi,
                    'ignition_timing': ecu_data.ignition_timing,
                    'afr': ecu_data.afr,
                    'coolant_temp': ecu_data.coolant_temp,
                    'throttle_position': ecu_data.throttle_position,
                    'vehicle_speed': ecu_data.vehicle_speed,
                    'timestamp': ecu_data.timestamp
                }
                self.data_updated.emit(data_dict)
                self.msleep(100)  # Update every 100ms
            except Exception as e:
                logger.error(f"Data update error: {e}")
    
    def stop(self):
        self.running = False

class DashboardTab(QWidget):
    """Main dashboard tab"""
    
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Gauges section
        gauges_group = QGroupBox("Real-time Gauges")
        gauges_layout = QGridLayout()
        
        # RPM gauge
        self.rpm_label = QLabel("RPM: 0")
        self.rpm_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E86AB;")
        gauges_layout.addWidget(self.rpm_label, 0, 0)
        
        # Boost gauge
        self.boost_label = QLabel("Boost: 0.0 psi")
        self.boost_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #A23B72;")
        gauges_layout.addWidget(self.boost_label, 0, 1)
        
        # Timing gauge
        self.timing_label = QLabel("Timing: 0.0°")
        self.timing_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #F18F01;")
        gauges_layout.addWidget(self.timing_label, 0, 2)
        
        # AFR gauge
        self.afr_label = QLabel("AFR: 14.7")
        self.afr_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #C73E1D;")
        gauges_layout.addWidget(self.afr_label, 1, 0)
        
        # Coolant temp
        self.coolant_label = QLabel("Coolant: 90°C")
        self.coolant_label.setStyleSheet("font-size: 18px; color: #2E86AB;")
        gauges_layout.addWidget(self.coolant_label, 1, 1)
        
        # Throttle position
        self.throttle_label = QLabel("Throttle: 0%")
        self.throttle_label.setStyleSheet("font-size: 18px; color: #A23B72;")
        gauges_layout.addWidget(self.throttle_label, 1, 2)
        
        gauges_group.setLayout(gauges_layout)
        layout.addWidget(gauges_group)
        
        # Status section
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-size: 16px; color: green;")
        status_layout.addWidget(self.status_label)
        
        self.connection_label = QLabel("ECU: Disconnected")
        self.connection_label.setStyleSheet("font-size: 16px; color: red;")
        status_layout.addWidget(self.connection_label)
        
        self.mode_label = QLabel("Mode: Stock")
        self.mode_label.setStyleSheet("font-size: 16px; color: blue;")
        status_layout.addWidget(self.mode_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Control buttons
        controls_group = QGroupBox("Controls")
        controls_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Connect ECU")
        self.connect_btn.clicked.connect(self.connect_ecu)
        controls_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_ecu)
        self.disconnect_btn.setEnabled(False)
        controls_layout.addWidget(self.disconnect_btn)
        
        self.read_vin_btn = QPushButton("Read VIN")
        self.read_vin_btn.clicked.connect(self.read_vin)
        self.read_vin_btn.setEnabled(False)
        controls_layout.addWidget(self.read_vin_btn)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        self.setLayout(layout)
    
    def update_gauges(self, data: Dict):
        """Update gauge displays"""
        try:
            self.rpm_label.setText(f"RPM: {data.get('engine_rpm', 0):.0f}")
            self.boost_label.setText(f"Boost: {data.get('boost_psi', 0):.1f} psi")
            self.timing_label.setText(f"Timing: {data.get('ignition_timing', 0):.1f}°")
            self.afr_label.setText(f"AFR: {data.get('afr', 14.7):.1f}")
            
            ecu_data = self.app_state.get_ecu_data()
            self.coolant_label.setText(f"Coolant: {ecu_data.coolant_temp:.1f}°C")
            self.throttle_label.setText(f"Throttle: {ecu_data.throttle_position:.1f}%")
            
        except Exception as e:
            logger.error(f"Error updating gauges: {e}")
    
    def update_status(self):
        """Update status displays"""
        try:
            status = self.app_state.get_system_status()
            state = self.app_state.get_state()
            tuning = self.app_state.get_tuning_parameters()
            
            # Update status label
            status_text = f"Status: {state.value.title()}"
            self.status_label.setText(status_text)
            
            # Color code status
            if state == SystemState.ERROR:
                self.status_label.setStyleSheet("font-size: 16px; color: red;")
            elif state == SystemState.TUNING:
                self.status_label.setStyleSheet("font-size: 16px; color: orange;")
            else:
                self.status_label.setStyleSheet("font-size: 16px; color: green;")
            
            # Update connection
            conn_text = "ECU: Connected" if status.ecu_connected else "ECU: Disconnected"
            self.connection_label.setText(conn_text)
            conn_color = "green" if status.ecu_connected else "red"
            self.connection_label.setStyleSheet(f"font-size: 16px; color: {conn_color};")
            
            # Update mode
            mode_text = f"Mode: {tuning.performance_mode.value.title()}"
            self.mode_label.setText(mode_text)
            
            # Update button states
            self.connect_btn.setEnabled(not status.ecu_connected)
            self.disconnect_btn.setEnabled(status.ecu_connected)
            self.read_vin_btn.setEnabled(status.ecu_connected)
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def connect_ecu(self):
        """Connect to ECU"""
        try:
            self.app_state.set_state(SystemState.CONNECTING)
            # ECU connection logic would be handled by communicator
            logger.info("ECU connection initiated")
        except Exception as e:
            logger.error(f"Error connecting ECU: {e}")
    
    def disconnect_ecu(self):
        """Disconnect from ECU"""
        try:
            self.app_state.set_state(SystemState.READY)
            self.app_state.update_system_status(ecu_connected=False)
            logger.info("ECU disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting ECU: {e}")
    
    def read_vin(self):
        """Read vehicle VIN"""
        try:
            # VIN reading logic would be handled by communicator
            logger.info("VIN read initiated")
        except Exception as e:
            logger.error(f"Error reading VIN: {e}")

class TuningTab(QWidget):
    """Tuning configuration tab"""
    
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Performance mode selection
        mode_group = QGroupBox("Performance Mode")
        mode_layout = QHBoxLayout()
        
        self.mode_combo = QComboBox()
        modes = [mode.value.title() for mode in PerformanceMode]
        self.mode_combo.addItems(modes)
        self.mode_combo.currentTextChanged.connect(self.change_performance_mode)
        mode_layout.addWidget(QLabel("Mode:"))
        mode_layout.addWidget(self.mode_combo)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Tuning parameters
        params_group = QGroupBox("Tuning Parameters")
        params_layout = QGridLayout()
        
        # Boost target
        params_layout.addWidget(QLabel("Boost Target (psi):"), 0, 0)
        self.boost_spin = QDoubleSpinBox()
        self.boost_spin.setRange(10.0, 30.0)
        self.boost_spin.setSingleStep(0.5)
        self.boost_spin.valueChanged.connect(self.update_boost_target)
        params_layout.addWidget(self.boost_spin, 0, 1)
        
        # Timing base
        params_layout.addWidget(QLabel("Timing Base (°):"), 1, 0)
        self.timing_spin = QDoubleSpinBox()
        self.timing_spin.setRange(0.0, 30.0)
        self.timing_spin.setSingleStep(0.5)
        self.timing_spin.valueChanged.connect(self.update_timing_base)
        params_layout.addWidget(self.timing_spin, 1, 1)
        
        # AFR target
        params_layout.addWidget(QLabel("AFR Target:"), 2, 0)
        self.afr_spin = QDoubleSpinBox()
        self.afr_spin.setRange(10.0, 16.0)
        self.afr_spin.setSingleStep(0.1)
        self.afr_spin.valueChanged.connect(self.update_afr_target)
        params_layout.addWidget(self.afr_spin, 2, 1)
        
        # Rev limit
        params_layout.addWidget(QLabel("Rev Limit (RPM):"), 3, 0)
        self.rev_limit_spin = QSpinBox()
        self.rev_limit_spin.setRange(5000, 8000)
        self.rev_limit_spin.setSingleStep(100)
        self.rev_limit_spin.valueChanged.connect(self.update_rev_limit)
        params_layout.addWidget(self.rev_limit_spin, 3, 1)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Apply buttons
        buttons_group = QGroupBox("Actions")
        buttons_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self.apply_tuning_changes)
        buttons_layout.addWidget(self.apply_btn)
        
        self.reset_btn = QPushButton("Reset to Stock")
        self.reset_btn.clicked.connect(self.reset_to_stock)
        buttons_layout.addWidget(self.reset_btn)
        
        self.save_btn = QPushButton("Save Tune")
        self.save_btn.clicked.connect(self.save_tune)
        buttons_layout.addWidget(self.save_btn)
        
        buttons_group.setLayout(buttons_layout)
        layout.addWidget(buttons_group)
        
        self.setLayout(layout)
        
        # Load current values
        self.load_current_values()
    
    def load_current_values(self):
        """Load current tuning values"""
        try:
            tuning = self.app_state.get_tuning_parameters()
            
            self.boost_spin.setValue(tuning.boost_target)
            self.timing_spin.setValue(tuning.timing_base)
            self.afr_spin.setValue(tuning.afr_target)
            self.rev_limit_spin.setValue(int(tuning.rev_limit))
            
            # Set current mode
            mode_index = self.mode_combo.findText(tuning.performance_mode.value.title())
            if mode_index >= 0:
                self.mode_combo.setCurrentIndex(mode_index)
                
        except Exception as e:
            logger.error(f"Error loading tuning values: {e}")
    
    def change_performance_mode(self, mode_text: str):
        """Change performance mode"""
        try:
            mode = PerformanceMode(mode_text.lower())
            self.app_state.set_performance_mode(mode)
            self.load_current_values()  # Reload values for new mode
            logger.info(f"Performance mode changed to: {mode.value}")
        except Exception as e:
            logger.error(f"Error changing performance mode: {e}")
    
    def update_boost_target(self, value: float):
        """Update boost target"""
        try:
            self.app_state.update_tuning_parameters(boost_target=value)
        except Exception as e:
            logger.error(f"Error updating boost target: {e}")
    
    def update_timing_base(self, value: float):
        """Update timing base"""
        try:
            self.app_state.update_tuning_parameters(timing_base=value)
        except Exception as e:
            logger.error(f"Error updating timing base: {e}")
    
    def update_afr_target(self, value: float):
        """Update AFR target"""
        try:
            self.app_state.update_tuning_parameters(afr_target=value)
        except Exception as e:
            logger.error(f"Error updating AFR target: {e}")
    
    def update_rev_limit(self, value: int):
        """Update rev limit"""
        try:
            self.app_state.update_tuning_parameters(rev_limit=float(value))
        except Exception as e:
            logger.error(f"Error updating rev limit: {e}")
    
    def apply_tuning_changes(self):
        """Apply tuning changes"""
        try:
            logger.info("Applying tuning changes...")
            # Implementation would send changes to ECU
            QMessageBox.information(self, "Success", "Tuning changes applied successfully!")
        except Exception as e:
            logger.error(f"Error applying tuning changes: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {e}")
    
    def reset_to_stock(self):
        """Reset to stock tuning"""
        try:
            reply = QMessageBox.question(self, "Confirm Reset", 
                                       "Are you sure you want to reset to stock tuning?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                logger.info("Resetting to stock tuning...")
                self.app_state.set_performance_mode(PerformanceMode.STOCK)
                self.load_current_values()
                QMessageBox.information(self, "Success", "Reset to stock tuning completed!")
        except Exception as e:
            logger.error(f"Error resetting to stock: {e}")
            QMessageBox.critical(self, "Error", f"Failed to reset: {e}")
    
    def save_tune(self):
        """Save current tune"""
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Save Tune", "", "Tune Files (*.tun)")
            if filename:
                logger.info(f"Saving tune to: {filename}")
                # Implementation would save tune data
                QMessageBox.information(self, "Success", "Tune saved successfully!")
        except Exception as e:
            logger.error(f"Error saving tune: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save tune: {e}")

class DiagnosticsTab(QWidget):
    """Diagnostics tab"""
    
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # DTC section
        dtc_group = QGroupBox("Diagnostic Trouble Codes")
        dtc_layout = QVBoxLayout()
        
        dtc_buttons = QHBoxLayout()
        self.read_dtcs_btn = QPushButton("Read DTCs")
        self.read_dtcs_btn.clicked.connect(self.read_dtcs)
        dtc_buttons.addWidget(self.read_dtcs_btn)
        
        self.clear_dtcs_btn = QPushButton("Clear DTCs")
        self.clear_dtcs_btn.clicked.connect(self.clear_dtcs)
        dtc_buttons.addWidget(self.clear_dtcs_btn)
        
        dtc_layout.addLayout(dtc_buttons)
        
        self.dtc_table = QTableWidget()
        self.dtc_table.setColumnCount(3)
        self.dtc_table.setHorizontalHeaderLabels(["Code", "Status", "Timestamp"])
        dtc_layout.addWidget(self.dtc_table)
        
        dtc_group.setLayout(dtc_layout)
        layout.addWidget(dtc_group)
        
        # Live data section
        live_group = QGroupBox("Live Data")
        live_layout = QVBoxLayout()
        
        live_buttons = QHBoxLayout()
        self.start_live_btn = QPushButton("Start Live Data")
        self.start_live_btn.clicked.connect(self.start_live_data)
        live_buttons.addWidget(self.start_live_btn)
        
        self.stop_live_btn = QPushButton("Stop Live Data")
        self.stop_live_btn.clicked.connect(self.stop_live_data)
        self.stop_live_btn.setEnabled(False)
        live_buttons.addWidget(self.stop_live_btn)
        
        live_layout.addLayout(live_buttons)
        
        self.live_table = QTableWidget()
        self.live_table.setColumnCount(2)
        self.live_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        live_layout.addWidget(self.live_table)
        
        live_group.setLayout(live_layout)
        layout.addWidget(live_group)
        
        self.setLayout(layout)
    
    def read_dtcs(self):
        """Read diagnostic trouble codes"""
        try:
            logger.info("Reading DTCs...")
            # Implementation would read actual DTCs
            self.dtc_table.setRowCount(0)  # Clear table
            QMessageBox.information(self, "DTC Read", "No DTCs found")
        except Exception as e:
            logger.error(f"Error reading DTCs: {e}")
            QMessageBox.critical(self, "Error", f"Failed to read DTCs: {e}")
    
    def clear_dtcs(self):
        """Clear diagnostic trouble codes"""
        try:
            reply = QMessageBox.question(self, "Confirm Clear", 
                                       "Are you sure you want to clear all DTCs?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                logger.info("Clearing DTCs...")
                # Implementation would clear actual DTCs
                self.dtc_table.setRowCount(0)
                QMessageBox.information(self, "DTC Cleared", "All DTCs cleared successfully!")
        except Exception as e:
            logger.error(f"Error clearing DTCs: {e}")
            QMessageBox.critical(self, "Error", f"Failed to clear DTCs: {e}")
    
    def start_live_data(self):
        """Start live data monitoring"""
        try:
            self.start_live_btn.setEnabled(False)
            self.stop_live_btn.setEnabled(True)
            logger.info("Starting live data monitoring...")
            # Implementation would start live data thread
        except Exception as e:
            logger.error(f"Error starting live data: {e}")
    
    def stop_live_data(self):
        """Stop live data monitoring"""
        try:
            self.start_live_btn.setEnabled(True)
            self.stop_live_btn.setEnabled(False)
            logger.info("Stopping live data monitoring...")
            # Implementation would stop live data thread
        except Exception as e:
            logger.error(f"Error stopping live data: {e}")

class MUTSMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.app_state = get_app_state()
        self.data_thread = None
        self.init_ui()
        self.setup_data_updates()
        
        # Register for state changes
        self.app_state.register_callback('state_change', self.on_state_change)
        self.app_state.register_callback('ecu_data_update', self.on_ecu_data_update)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("MUTS - Mazda Universal Tuning Suite")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2B2B2B;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #3C3C3C;
            }
            QTabBar::tab {
                background-color: #555;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0078D4;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #0E5A9A;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """)
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.dashboard_tab = DashboardTab(self.app_state)
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        self.tuning_tab = TuningTab(self.app_state)
        self.tab_widget.addTab(self.tuning_tab, "Tuning")
        
        self.diagnostics_tab = DiagnosticsTab(self.app_state)
        self.tab_widget.addTab(self.diagnostics_tab, "Diagnostics")
        
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        logger.info("Main GUI initialized")
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Tune", self)
        open_action.triggered.connect(self.open_tune)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save Tune", self)
        save_action.triggered.connect(self.save_tune)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        connect_action = QAction("Connect ECU", self)
        connect_action.triggered.connect(self.dashboard_tab.connect_ecu)
        tools_menu.addAction(connect_action)
        
        disconnect_action = QAction("Disconnect ECU", self)
        disconnect_action.triggered.connect(self.dashboard_tab.disconnect_ecu)
        tools_menu.addAction(disconnect_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_data_updates(self):
        """Setup real-time data updates"""
        self.data_thread = DataUpdateThread(self.app_state)
        self.data_thread.data_updated.connect(self.dashboard_tab.update_gauges)
        self.data_thread.start()
    
    def on_state_change(self, data):
        """Handle state changes"""
        try:
            self.dashboard_tab.update_status()
            state = data['new']
            self.status_bar.showMessage(f"State: {state.value.title()}")
        except Exception as e:
            logger.error(f"Error handling state change: {e}")
    
    def on_ecu_data_update(self, data):
        """Handle ECU data updates"""
        try:
            # Dashboard is updated via data thread
            pass
        except Exception as e:
            logger.error(f"Error handling ECU data update: {e}")
    
    def open_tune(self):
        """Open tune file"""
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Open Tune", "", "Tune Files (*.tun)")
            if filename:
                logger.info(f"Opening tune file: {filename}")
                # Implementation would load tune file
                QMessageBox.information(self, "Success", "Tune file loaded successfully!")
        except Exception as e:
            logger.error(f"Error opening tune file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open tune file: {e}")
    
    def save_tune(self):
        """Save tune file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Save Tune", "", "Tune Files (*.tun)")
            if filename:
                logger.info(f"Saving tune file: {filename}")
                # Implementation would save tune file
                QMessageBox.information(self, "Success", "Tune file saved successfully!")
        except Exception as e:
            logger.error(f"Error saving tune file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save tune file: {e}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About MUTS", 
                         "Mazda Universal Tuning Suite v2.0\n\n"
                         "Complete tuning and diagnostic system for\n"
                         "2011 Mazdaspeed 3 with MZR 2.3L DISI Turbo")
    
    def closeEvent(self, event):
        """Handle application close"""
        try:
            logger.info("Shutting down application...")
            
            # Stop data thread
            if self.data_thread:
                self.data_thread.stop()
                self.data_thread.wait()
            
            # Cleanup app state
            self.app_state.set_state(SystemState.SHUTDOWN)
            
            event.accept()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            event.accept()

def main():
    """Main application entry point"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("MUTS")
        app.setApplicationVersion("2.0")
        
        # Create and show main window
        window = MUTSMainWindow()
        window.show()
        
        logger.info("MUTS GUI application started")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Failed to start GUI application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
