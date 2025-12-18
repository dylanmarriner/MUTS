#!/usr/bin/env python3
"""
Main GUI Interface - VersaTuner-like user interface
Provides professional tuning interface with real-time data display
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from typing import Dict, List, Optional, Any
from ..core.ecu_communication import ECUCommunicator
from ..core.security_access import SecurityManager
from ..core.rom_operations import ROMOperations
from ..tuning.map_editor import MapEditor
from ..tuning.realtime_tuning import RealTimeTuner
from ..vehicle.mazdaspeed3_2011 import Mazdaspeed32011
from ..utils.logger import VersaLogger

class VersaTunerGUI:
    """
    Main GUI class providing VersaTuner-like interface
    with professional layout and real-time data display
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VersaTuner - Mazdaspeed 3 2011")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Initialize core components
        self.logger = VersaLogger(__name__)
        self.ecu_comm = ECUCommunicator()
        self.security_mgr = SecurityManager(self.ecu_comm)
        self.rom_ops = ROMOperations(self.ecu_comm)
        self.map_editor = MapEditor(self.rom_ops)
        self.realtime_tuner = RealTimeTuner(self.ecu_comm)
        self.vehicle = Mazdaspeed32011()
        
        # Application state
        self.is_connected = False
        self.rom_data = None
        self.current_tab = None
        
        # Create GUI
        self._setup_gui()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _setup_gui(self):
        """Setup main GUI layout and components"""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self._create_connection_tab()
        self._create_dashboard_tab()
        self._create_tuning_tab()
        self._create_diagnostic_tab()
        self._create_flashing_tab()
        self._create_settings_tab()
        
        # Status bar
        self._create_status_bar(main_frame)
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
    
    def _create_connection_tab(self):
        """Create connection and vehicle info tab"""
        connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(connection_frame, text="Connection")
        
        # Connection controls
        conn_control_frame = ttk.LabelFrame(connection_frame, text="ECU Connection", padding=10)
        conn_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(conn_control_frame, text="CAN Interface:").grid(row=0, column=0, sticky=tk.W)
        self.interface_var = tk.StringVar(value="can0")
        ttk.Entry(conn_control_frame, textvariable=self.interface_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Button(conn_control_frame, text="Connect", 
                  command=self._connect_ecu).grid(row=0, column=2, padx=5)
        ttk.Button(conn_control_frame, text="Disconnect", 
                  command=self._disconnect_ecu).grid(row=0, column=3, padx=5)
        
        # Vehicle information
        vehicle_frame = ttk.LabelFrame(connection_frame, text="Vehicle Information", padding=10)
        vehicle_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.vehicle_info_text = tk.Text(vehicle_frame, height=8, width=80)
        self.vehicle_info_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Security access
        security_frame = ttk.LabelFrame(connection_frame, text="Security Access", padding=10)
        security_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(security_frame, text="Unlock ECU (Level 1)", 
                  command=lambda: self._unlock_ecu(1)).grid(row=0, column=0, padx=5)
        ttk.Button(security_frame, text="Unlock ECU (Level 3)", 
                  command=lambda: self._unlock_ecu(3)).grid(row=0, column=1, padx=5)
        ttk.Button(security_frame, text="Enter Programming Mode", 
                  command=self._enter_programming_mode).grid(row=0, column=2, padx=5)
        
        self.security_status_var = tk.StringVar(value="Security: Not Unlocked")
        ttk.Label(security_frame, textvariable=self.security_status_var).grid(row=1, column=0, columnspan=3, pady=5)
    
    def _create_dashboard_tab(self):
        """Create real-time dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Create gauge frames
        gauge_frame = ttk.Frame(dashboard_frame)
        gauge_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # RPM Gauge
        rpm_frame = ttk.LabelFrame(gauge_frame, text="RPM")
        rpm_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.rpm_var = tk.StringVar(value="0")
        ttk.Label(rpm_frame, textvariable=self.rpm_var, font=("Arial", 24)).pack(padx=20, pady=20)
        
        # Boost Gauge
        boost_frame = ttk.LabelFrame(gauge_frame, text="Boost (PSI)")
        boost_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.boost_var = tk.StringVar(value="0.0")
        ttk.Label(boost_frame, textvariable=self.boost_var, font=("Arial", 24)).pack(padx=20, pady=20)
        
        # Throttle Gauge
        throttle_frame = ttk.LabelFrame(gauge_frame, text="Throttle (%)")
        throttle_frame.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
        self.throttle_var = tk.StringVar(value="0.0")
        ttk.Label(throttle_frame, textvariable=self.throttle_var, font=("Arial", 24)).pack(padx=20, pady=20)
        
        # Speed Gauge
        speed_frame = ttk.LabelFrame(gauge_frame, text="Speed (km/h)")
        speed_frame.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.speed_var = tk.StringVar(value="0")
        ttk.Label(speed_frame, textvariable=self.speed_var, font=("Arial", 24)).pack(padx=20, pady=20)
        
        # Coolant Temp Gauge
        coolant_frame = ttk.LabelFrame(gauge_frame, text="Coolant (°C)")
        coolant_frame.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.coolant_var = tk.StringVar(value="0")
        ttk.Label(coolant_frame, textvariable=self.coolant_var, font=("Arial", 24)).pack(padx=20, pady=20)
        
        # Intake Temp Gauge
        intake_frame = ttk.LabelFrame(gauge_frame, text="Intake (°C)")
        intake_frame.grid(row=1, column=2, padx=5, pady=5, sticky=tk.NSEW)
        self.intake_var = tk.StringVar(value="0")
        ttk.Label(intake_frame, textvariable=self.intake_var, font=("Arial", 24)).pack(padx=20, pady=20)
        
        # Configure grid weights
        gauge_frame.columnconfigure(0, weight=1)
        gauge_frame.columnconfigure(1, weight=1)
        gauge_frame.columnconfigure(2, weight=1)
        gauge_frame.rowconfigure(0, weight=1)
        gauge_frame.rowconfigure(1, weight=1)
        
        # Data logging controls
        log_frame = ttk.LabelFrame(dashboard_frame, text="Data Logging")
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(log_frame, text="Start Logging", 
                  command=self._start_logging).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(log_frame, text="Stop Logging", 
                  command=self._stop_logging).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.logging_status_var = tk.StringVar(value="Logging: Stopped")
        ttk.Label(log_frame, textvariable=self.logging_status_var).pack(side=tk.LEFT, padx=20)
    
    def _create_tuning_tab(self):
        """Create tuning map editing tab"""
        tuning_frame = ttk.Frame(self.notebook)
        self.notebook.add(tuning_frame, text="Tuning")
        
        # Map selection
        selection_frame = ttk.LabelFrame(tuning_frame, text="Map Selection")
        selection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Category:").grid(row=0, column=0, sticky=tk.W)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(selection_frame, textvariable=self.category_var)
        self.category_combo.grid(row=0, column=1, padx=5, pady=5)
        self.category_combo.bind('<<ComboboxSelected>>', self._on_category_selected)
        
        ttk.Label(selection_frame, text="Map:").grid(row=0, column=2, sticky=tk.W)
        self.map_var = tk.StringVar()
        self.map_combo = ttk.Combobox(selection_frame, textvariable=self.map_var)
        self.map_combo.grid(row=0, column=3, padx=5, pady=5)
        self.map_combo.bind('<<ComboboxSelected>>', self._on_map_selected)
        
        ttk.Button(selection_frame, text="Load Map", 
                  command=self._load_selected_map).grid(row=0, column=4, padx=5)
        
        # Map display frame
        self.map_display_frame = ttk.LabelFrame(tuning_frame, text="Map Editor")
        self.map_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create table for map display
        self.map_table = ttk.Treeview(self.map_display_frame)
        self.map_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Map controls
        control_frame = ttk.Frame(tuning_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Apply Changes", 
                  command=self._apply_map_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Reset to Original", 
                  command=self._reset_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Map As...", 
                  command=self._save_map).pack(side=tk.LEFT, padx=5)
        
        # Tune presets
        preset_frame = ttk.LabelFrame(tuning_frame, text="Quick Tune Presets")
        preset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(preset_frame, text="Stage 1 (+30HP)", 
                  command=lambda: self._apply_preset_tune(30)).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="Stage 2 (+60HP)", 
                  command=lambda: self._apply_preset_tune(60)).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_frame, text="Stage 3 (+90HP)", 
                  command=lambda: self._apply_preset_tune(90)).pack(side=tk.LEFT, padx=5)
    
    def _create_diagnostic_tab(self):
        """Create diagnostic and DTC tab"""
        diagnostic_frame = ttk.Frame(self.notebook)
        self.notebook.add(diagnostic_frame, text="Diagnostics")
        
        # DTC controls
        dtc_frame = ttk.LabelFrame(diagnostic_frame, text="Diagnostic Trouble Codes")
        dtc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(dtc_frame, text="Read DTCs", 
                  command=self._read_dtcs).pack(anchor=tk.W, padx=5, pady=5)
        ttk.Button(dtc_frame, text="Clear DTCs", 
                  command=self._clear_dtcs).pack(anchor=tk.W, padx=5, pady=5)
        
        # DTC list
        self.dtc_tree = ttk.Treeview(dtc_frame, columns=("Code", "Description", "Status"), show="headings")
        self.dtc_tree.heading("Code", text="Code")
        self.dtc_tree.heading("Description", text="Description")
        self.dtc_tree.heading("Status", text="Status")
        self.dtc_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Live data monitoring
        live_data_frame = ttk.LabelFrame(diagnostic_frame, text="Live Data")
        live_data_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.live_data_text = tk.Text(live_data_frame, height=10)
        self.live_data_text.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(live_data_frame, text="Start Monitoring", 
                  command=self._start_live_monitoring).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(live_data_frame, text="Stop Monitoring", 
                  command=self._stop_live_monitoring).pack(side=tk.LEFT, padx=5, pady=5)
    
    def _create_flashing_tab(self):
        """Create ECU flashing tab"""
        flash_frame = ttk.Frame(self.notebook)
        self.notebook.add(flash_frame, text="Flashing")
        
        # ROM operations
        rom_frame = ttk.LabelFrame(flash_frame, text="ROM Operations")
        rom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(rom_frame, text="Read ROM", 
                  command=self._read_rom).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(rom_frame, text="Save ROM As...", 
                  command=self._save_rom).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(rom_frame, text="Load ROM File...", 
                  command=self._load_rom_file).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(rom_frame, text="Verify ROM", 
                  command=self._verify_rom).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Flashing controls
        flash_control_frame = ttk.LabelFrame(flash_frame, text="ECU Flashing")
        flash_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(flash_control_frame, text="Write ROM to ECU", 
                  command=self._write_rom).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(flash_control_frame, text="Backup Original ROM", 
                  command=self._backup_rom).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(flash_control_frame, text="Restore Backup", 
                  command=self._restore_backup).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Progress bar
        self.flash_progress = ttk.Progressbar(flash_frame, mode='determinate')
        self.flash_progress.pack(fill=tk.X, padx=5, pady=5)
        
        self.flash_status_var = tk.StringVar(value="Ready")
        ttk.Label(flash_frame, textvariable=self.flash_status_var).pack(padx=5, pady=5)
    
    def _create_settings_tab(self):
        """Create settings and configuration tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Application settings
        app_frame = ttk.LabelFrame(settings_frame, text="Application Settings")
        app_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(app_frame, text="Update Interval (ms):").grid(row=0, column=0, sticky=tk.W)
        self.update_interval_var = tk.StringVar(value="100")
        ttk.Entry(app_frame, textvariable=self.update_interval_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(app_frame, text="Log Level:").grid(row=1, column=0, sticky=tk.W)
        self.log_level_var = tk.StringVar(value="INFO")
        log_combo = ttk.Combobox(app_frame, textvariable=self.log_level_var, 
                                values=["DEBUG", "INFO", "WARNING", "ERROR"])
        log_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Vehicle-specific settings
        vehicle_frame = ttk.LabelFrame(settings_frame, text="Vehicle Settings")
        vehicle_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(vehicle_frame, text="Vehicle Model:").grid(row=0, column=0, sticky=tk.W)
        self.vehicle_model_var = tk.StringVar(value="Mazdaspeed 3 2011")
        ttk.Label(vehicle_frame, textvariable=self.vehicle_model_var).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(vehicle_frame, text="ECU Type:").grid(row=1, column=0, sticky=tk.W)
        self.ecu_type_var = tk.StringVar(value="MZR 2.3L DISI TURBO")
        ttk.Label(vehicle_frame, textvariable=self.ecu_type_var).grid(row=1, column=1, sticky=tk.W)
        
        # Save settings
        ttk.Button(settings_frame, text="Save Settings", 
                  command=self._save_settings).pack(anchor=tk.E, padx=5, pady=10)
    
    def _create_status_bar(self, parent):
        """Create status bar at bottom of window"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)
    
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        # Populate categories and maps
        categories = self.map_editor.map_manager.get_all_categories()
        self.category_combo['values'] = categories
        if categories:
            self.category_combo.set(categories[0])
            self._on_category_selected()
    
    def _on_tab_changed(self, event):
        """Handle tab change events"""
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        self.current_tab = selected_tab
        self.logger.debug(f"Switched to tab: {selected_tab}")
    
    def _connect_ecu(self):
        """Connect to ECU"""
        def connect_thread():
            interface = self.interface_var.get()
            self.ecu_comm.interface = interface
            
            if self.ecu_comm.connect():
                self.is_connected = True
                self.root.after(0, self._on_connect_success)
            else:
                self.root.after(0, self._on_connect_failure)
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def _on_connect_success(self):
        """Handle successful ECU connection"""
        self.status_var.set("Connected to ECU")
        messagebox.showinfo("Success", "Successfully connected to ECU")
        
        # Update vehicle information
        self._update_vehicle_info()
    
    def _on_connect_failure(self):
        """Handle failed ECU connection"""
        messagebox.showerror("Error", "Failed to connect to ECU. Check interface and connection.")
    
    def _disconnect_ecu(self):
        """Disconnect from ECU"""
        self.ecu_comm.disconnect()
        self.is_connected = False
        self.status_var.set("Disconnected")
        messagebox.showinfo("Disconnected", "Disconnected from ECU")
    
    def _update_vehicle_info(self):
        """Update vehicle information display"""
        if not self.is_connected:
            return
        
        info = self.rom_ops.read_ecu_info()
        info_text = f"VIN: {info.get('vin', 'Unknown')}\n"
        info_text += f"ECU Part Number: {info.get('ecu_part_number', 'Unknown')}\n"
        info_text += f"Calibration ID: {info.get('calibration_id', 'Unknown')}\n"
        info_text += f"Software Version: {info.get('software_version', 'Unknown')}\n"
        
        self.vehicle_info_text.delete(1.0, tk.END)
        self.vehicle_info_text.insert(1.0, info_text)
    
    def _unlock_ecu(self, level):
        """Unlock ECU security access"""
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to ECU")
            return
        
        success = self.security_mgr.unlock_ecu(level)
        if success:
            status = self.security_mgr.check_security_status()
            self.security_status_var.set(f"Security: Level {status['current_level']} - {status['level_description']}")
            messagebox.showinfo("Success", f"Security level {level} unlocked")
        else:
            messagebox.showerror("Error", "Failed to unlock ECU security")
    
    def _enter_programming_mode(self):
        """Enter ECU programming mode"""
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to ECU")
            return
        
        success = self.security_mgr.enter_programming_mode()
        if success:
            messagebox.showinfo("Success", "Programming mode entered")
        else:
            messagebox.showerror("Error", "Failed to enter programming mode")
    
    def _on_category_selected(self, event=None):
        """Handle category selection"""
        category = self.category_var.get()
        if not category:
            return
        
        maps = self.map_editor.map_manager.get_maps_by_category(category)
        map_names = [map_def.name for map_def in maps]
        self.map_combo['values'] = map_names
        if map_names:
            self.map_combo.set(map_names[0])
    
    def _on_map_selected(self, event=None):
        """Handle map selection"""
        # This would load and display the selected map
        pass
    
    def _load_selected_map(self):
        """Load the selected map from ROM"""
        if not self.rom_data:
            messagebox.showerror("Error", "No ROM data loaded")
            return
        
        map_name = self.map_var.get()
        if not map_name:
            messagebox.showerror("Error", "No map selected")
            return
        
        map_data = self.map_editor.load_map_from_rom(map_name, self.rom_data)
        if map_data:
            self._display_map_data(map_data)
            messagebox.showinfo("Success", f"Loaded map: {map_name}")
        else:
            messagebox.showerror("Error", f"Failed to load map: {map_name}")
    
    def _display_map_data(self, map_data):
        """Display map data in table"""
        # Clear existing table
        for item in self.map_table.get_children():
            self.map_table.delete(item)
        
        # Configure columns based on map type
        if len(map_data.data.shape) == 2:
            # 2D map - create columns for each X value
            columns = ["Y/X"] + [str(i) for i in range(map_data.data.shape[1])]
            self.map_table.configure(columns=columns)
            
            for i, col in enumerate(columns):
                self.map_table.heading(col, text=col)
            
            # Add data rows
            for y in range(map_data.data.shape[0]):
                row_data = [f"Row {y}"] + [f"{map_data.data[y, x]:.2f}" for x in range(map_data.data.shape[1])]
                self.map_table.insert("", tk.END, values=row_data)
        
        elif len(map_data.data.shape) == 1:
            # 1D map
            self.map_table.configure(columns=("Index", "Value"))
            self.map_table.heading("Index", text="Index")
            self.map_table.heading("Value", text="Value")
            
            for i, value in enumerate(map_data.data):
                self.map_table.insert("", tk.END, values=(i, f"{value:.2f}"))
    
    def _apply_map_changes(self):
        """Apply changes to current map"""
        # Implementation for applying map edits
        messagebox.showinfo("Info", "Map changes applied (simulated)")
    
    def _reset_map(self):
        """Reset map to original values"""
        messagebox.showinfo("Info", "Map reset to original values (simulated)")
    
    def _save_map(self):
        """Save current map to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Map As",
            filetypes=[("Map files", "*.map"), ("All files", "*.*")]
        )
        if filename:
            messagebox.showinfo("Info", f"Map saved to {filename} (simulated)")
    
    def _apply_preset_tune(self, hp_gain):
        """Apply preset tune based on horsepower target"""
        if not self.rom_data:
            messagebox.showerror("Error", "No ROM data loaded")
            return
        
        try:
            tuned_rom = self.map_editor.create_performance_tune(self.rom_data, hp_gain)
            self.rom_data = tuned_rom
            messagebox.showinfo("Success", f"Stage {hp_gain//30} tune applied successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply tune: {e}")
    
    def _read_dtcs(self):
        """Read diagnostic trouble codes"""
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to ECU")
            return
        
        dtcs = self.ecu_comm.read_dtcs()
        
        # Clear existing DTCs
        for item in self.dtc_tree.get_children():
            self.dtc_tree.delete(item)
        
        # Add new DTCs
        for dtc in dtcs:
            self.dtc_tree.insert("", tk.END, values=(
                dtc['code'], dtc['description'], dtc['status']
            ))
    
    def _clear_dtcs(self):
        """Clear diagnostic trouble codes"""
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to ECU")
            return
        
        success = self.ecu_comm.clear_dtcs()
        if success:
            messagebox.showinfo("Success", "DTCs cleared successfully")
            self._read_dtcs()  # Refresh DTC list
        else:
            messagebox.showerror("Error", "Failed to clear DTCs")
    
    def _start_live_monitoring(self):
        """Start live data monitoring"""
        self.realtime_tuner.start_monitoring()
        messagebox.showinfo("Info", "Live monitoring started")
    
    def _stop_live_monitoring(self):
        """Stop live data monitoring"""
        self.realtime_tuner.stop_monitoring()
        messagebox.showinfo("Info", "Live monitoring stopped")
    
    def _read_rom(self):
        """Read ROM from ECU"""
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to ECU")
            return
        
        def read_thread():
            self.flash_status_var.set("Reading ROM from ECU...")
            
            def progress_callback(current, total):
                progress = (current / total) * 100
                self.root.after(0, lambda: self.flash_progress.configure(value=progress))
            
            rom_data = self.rom_ops.read_complete_rom(progress_callback)
            
            self.root.after(0, lambda: self._on_rom_read_complete(rom_data))
        
        threading.Thread(target=read_thread, daemon=True).start()
    
    def _on_rom_read_complete(self, rom_data):
        """Handle ROM read completion"""
        if rom_data:
            self.rom_data = rom_data
            self.flash_status_var.set(f"ROM read complete: {len(rom_data)} bytes")
            messagebox.showinfo("Success", "ROM read successfully")
        else:
            self.flash_status_var.set("ROM read failed")
            messagebox.showerror("Error", "Failed to read ROM")
        
        self.flash_progress.configure(value=0)
    
    def _save_rom(self):
        """Save ROM to file"""
        if not self.rom_data:
            messagebox.showerror("Error", "No ROM data to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save ROM As",
            defaultextension=".bin",
            filetypes=[("ROM files", "*.bin"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'wb') as f:
                    f.write(self.rom_data)
                messagebox.showinfo("Success", f"ROM saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save ROM: {e}")
    
    def _load_rom_file(self):
        """Load ROM from file"""
        filename = filedialog.askopenfilename(
            title="Load ROM File",
            filetypes=[("ROM files", "*.bin"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'rb') as f:
                    self.rom_data = f.read()
                messagebox.showinfo("Success", f"ROM loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load ROM: {e}")
    
    def _verify_rom(self):
        """Verify ROM integrity"""
        if not self.rom_data:
            messagebox.showerror("Error", "No ROM data to verify")
            return
        
        results = self.rom_ops.verify_rom_integrity(self.rom_data)
        
        if results['overall_valid']:
            messagebox.showinfo("Success", "ROM verification passed")
        else:
            error_msg = "ROM verification failed:\n" + "\n".join(results['errors'])
            messagebox.showerror("Error", error_msg)
    
    def _write_rom(self):
        """Write ROM to ECU"""
        if not self.rom_data:
            messagebox.showerror("Error", "No ROM data to write")
            return
        
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to ECU")
            return
        
        # Confirm flash operation
        if not messagebox.askyesno("Confirm", "This will overwrite the ECU ROM. Continue?"):
            return
        
        def write_thread():
            self.flash_status_var.set("Writing ROM to ECU...")
            
            def progress_callback(current, total):
                progress = (current / total) * 100
                self.root.after(0, lambda: self.flash_progress.configure(value=progress))
            
            success = self.rom_ops.write_complete_rom(self.rom_data, progress_callback)
            
            self.root.after(0, lambda: self._on_rom_write_complete(success))
        
        threading.Thread(target=write_thread, daemon=True).start()
    
    def _on_rom_write_complete(self, success):
        """Handle ROM write completion"""
        if success:
            self.flash_status_var.set("ROM write complete")
            messagebox.showinfo("Success", "ROM written to ECU successfully")
        else:
            self.flash_status_var.set("ROM write failed")
            messagebox.showerror("Error", "Failed to write ROM to ECU")
        
        self.flash_progress.configure(value=0)
    
    def _backup_rom(self):
        """Backup original ROM"""
        messagebox.showinfo("Info", "Backup feature would be implemented here")
    
    def _restore_backup(self):
        """Restore ROM from backup"""
        messagebox.showinfo("Info", "Restore feature would be implemented here")
    
    def _start_logging(self):
        """Start data logging"""
        messagebox.showinfo("Info", "Data logging started (simulated)")
        self.logging_status_var.set("Logging: Active")
    
    def _stop_logging(self):
        """Stop data logging"""
        messagebox.showinfo("Info", "Data logging stopped (simulated)")
        self.logging_status_var.set("Logging: Stopped")
    
    def _save_settings(self):
        """Save application settings"""
        messagebox.showinfo("Info", "Settings saved (simulated)")
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point for VersaTuner GUI"""
    app = VersaTunerGUI()
    app.run()

if __name__ == "__main__":
    main()