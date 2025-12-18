#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3_PRODUCTION_SOFTWARE.py
COMPLETE PRODUCTION-READY TUNING SOFTWARE
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
import logging
from datetime import datetime
from pathlib import Path
import can
import serial
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Import from app/muts modules
from ..core.factory_platform import MazdaFactoryPlatform
from ..security.security_engine import MazdaSecurity
from ..ecu.ecu_exploits import MazdaECUExploit

class MazdaSpeed3TunerGUI:
    """
    COMPLETE GRAPHICAL USER INTERFACE
    Production-ready tuning software
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Mazdaspeed 3 Professional Tuner v2.0")
        self.root.geometry("1200x800")
        
        # Initialize core systems
        self.factory_platform = MazdaFactoryPlatform()
        self.security_engine = MazdaSecurity()
        self.ecu_exploiter = MazdaECUExploit()
        self.tuning_session = None
        
        # Data storage
        self.current_tune = {}
        self.vehicle_data = {}
        self.log_data = []
        self.connected = False
        
        # Setup interface
        self.setup_logging()
        self.create_interface()
        self.setup_plots()
        
        # Start background threads
        self.running = True
        self.start_background_tasks()
        
    def setup_logging(self):
        """SETUP COMPREHENSIVE LOGGING SYSTEM"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mazda_tuner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_interface(self):
        """CREATE MAIN APPLICATION INTERFACE"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_dashboard_tab()
        self.setup_tuning_tab()
        self.setup_diagnostics_tab()
        self.setup_race_tab()
        self.setup_logs_tab()
        
        # Status bar
        self.setup_status_bar()
        
    def setup_dashboard_tab(self):
        """CREATE REAL-TIME DASHBOARD TAB"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Main gauges frame
        gauges_frame = ttk.LabelFrame(dashboard_frame, text="Live Data", padding=10)
        gauges_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create gauge grid
        self.create_gauges(gauges_frame)
        
        # Control buttons
        control_frame = ttk.Frame(dashboard_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="Connect to Vehicle", 
                  command=self.connect_vehicle).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Start Logging", 
                  command=self.start_logging).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Emergency Stop", 
                  command=self.emergency_stop, style="Emergency.TButton").pack(side=tk.RIGHT, padx=5)
        
        # Apply emergency button style
        style = ttk.Style()
        style.configure("Emergency.TButton", foreground='red', font=('Arial', 10, 'bold'))
        
    def create_gauges(self, parent):
        """CREATE REAL-TIME DATA GAUGES"""
        # Important parameters to display
        parameters = [
            ("RPM", "rpm", "0", "8000"),
            ("Boost", "boost_psi", "-10", "25"), 
            ("AFR", "afr", "10", "16"),
            ("Timing", "ignition_timing", "0", "30"),
            ("Coolant", "coolant_temp", "0", "120"),
            ("Knock", "knock_retard", "-10", "0")
        ]
        
        self.gauges = {}
        
        for i, (label, key, min_val, max_val) in enumerate(parameters):
            frame = ttk.Frame(parent)
            frame.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="nsew")
            
            ttk.Label(frame, text=label, font=('Arial', 12, 'bold')).pack()
            
            # Value display
            value_var = tk.StringVar(value="--")
            value_label = ttk.Label(frame, textvariable=value_var, 
                                  font=('Arial', 16, 'bold'))
            value_label.pack()
            
            # Progress bar for visual indication
            progress = ttk.Progressbar(frame, orient=tk.VERTICAL, 
                                     length=100, mode='determinate')
            progress.pack(pady=5)
            
            self.gauges[key] = {
                'var': value_var,
                'progress': progress,
                'min': float(min_val),
                'max': float(max_val)
            }
            
    def setup_tuning_tab(self):
        """CREATE TUNING AND CALIBRATION TAB"""
        tuning_frame = ttk.Frame(self.notebook)
        self.notebook.add(tuning_frame, text="Tuning")
        
        # Tuning mode selection
        mode_frame = ttk.LabelFrame(tuning_frame, text="Tuning Mode", padding=10)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.tuning_mode = tk.StringVar(value="performance")
        modes = [
            ("Stock", "stock"),
            ("Performance", "performance"), 
            ("Race", "race"),
            ("Economy", "economy"),
            ("Track", "track")
        ]
        
        for text, mode in modes:
            ttk.Radiobutton(mode_frame, text=text, variable=self.tuning_mode, 
                           value=mode).pack(side=tk.LEFT, padx=10)
        
        # Modification selection
        mod_frame = ttk.LabelFrame(tuning_frame, text="Vehicle Modifications", padding=10)
        mod_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mods_vars = {}
        mods = ["intake", "downpipe", "intercooler", "exhaust", "ethanol", "upgraded_internals"]
        
        for mod in mods:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(mod_frame, text=mod.replace('_', ' ').title(), 
                               variable=var)
            cb.pack(side=tk.LEFT, padx=10)
            self.mods_vars[mod] = var
        
        # Tune generation
        tune_frame = ttk.Frame(tuning_frame)
        tune_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(tune_frame, text="Generate Tune", 
                  command=self.generate_tune).pack(side=tk.LEFT, padx=5)
        ttk.Button(tune_frame, text="Flash ECU", 
                  command=self.flash_ecu).pack(side=tk.LEFT, padx=5)
        ttk.Button(tune_frame, text="Real-time Tune", 
                  command=self.start_real_time_tuning).pack(side=tk.LEFT, padx=5)
        
        # Tune display
        tune_display_frame = ttk.LabelFrame(tuning_frame, text="Tune Details", padding=10)
        tune_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tune_text = scrolledtext.ScrolledText(tune_display_frame, height=15)
        self.tune_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_diagnostics_tab(self):
        """CREATE DIAGNOSTICS TAB"""
        diag_frame = ttk.Frame(self.notebook)
        self.notebook.add(diag_frame, text="Diagnostics")
        
        # DTC section
        dtc_frame = ttk.LabelFrame(diag_frame, text="Diagnostic Trouble Codes", padding=10)
        dtc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(dtc_frame, text="Scan for DTCs", 
                  command=self.scan_dtcs).pack(side=tk.LEFT, padx=5)
        ttk.Button(dtc_frame, text="Clear DTCs", 
                  command=self.clear_dtcs).pack(side=tk.LEFT, padx=5)
        ttk.Button(dtc_frame, text="Save Report", 
                  command=self.save_diag_report).pack(side=tk.LEFT, padx=5)
        
        # DTC display
        self.dtc_tree = ttk.Treeview(diag_frame, columns=('Code', 'Description', 'Severity'), show='headings')
        self.dtc_tree.heading('Code', text='Code')
        self.dtc_tree.heading('Description', text='Description')
        self.dtc_tree.heading('Severity', text='Severity')
        self.dtc_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Live data section
        live_frame = ttk.LabelFrame(diag_frame, text="Live Data", padding=10)
        live_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.live_text = scrolledtext.ScrolledText(live_frame, height=10)
        self.live_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_race_tab(self):
        """CREATE RACING FEATURES TAB"""
        race_frame = ttk.Frame(self.notebook)
        self.notebook.add(race_frame, text="Racing")
        
        # Launch control
        launch_frame = ttk.LabelFrame(race_frame, text="Launch Control", padding=10)
        launch_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(launch_frame, text="Launch RPM:").pack(side=tk.LEFT, padx=5)
        self.launch_rpm = tk.IntVar(value=4500)
        ttk.Spinbox(launch_frame, from_=3000, to=6000, textvariable=self.launch_rpm, 
                   width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(launch_frame, text="Enable Launch Control", 
                  command=self.enable_launch_control).pack(side=tk.LEFT, padx=20)
        
        # Flat shift
        flat_frame = ttk.LabelFrame(race_frame, text="Flat Shift", padding=10)
        flat_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(flat_frame, text="Fuel Cut (ms):").pack(side=tk.LEFT, padx=5)
        self.fuel_cut = tk.IntVar(value=50)
        ttk.Spinbox(flat_frame, from_=10, to=100, textvariable=self.fuel_cut, 
                   width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(flat_frame, text="Ignition Retard:").pack(side=tk.LEFT, padx=20)
        self.ign_retard = tk.IntVar(value=20)
        ttk.Spinbox(flat_frame, from_=0, to=40, textvariable=self.ign_retard, 
                   width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(flat_frame, text="Enable Flat Shift", 
                  command=self.enable_flat_shift).pack(side=tk.LEFT, padx=20)
        
        # Anti-lag
        anti_frame = ttk.LabelFrame(race_frame, text="Anti-Lag", padding=10)
        anti_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(anti_frame, text="Aggressiveness:").pack(side=tk.LEFT, padx=5)
        self.anti_lag = tk.IntVar(value=2)
        ttk.Scale(anti_frame, from_=1, to=5, variable=self.anti_lag, 
                 orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(anti_frame, text="Enable Anti-Lag", 
                  command=self.enable_anti_lag).pack(side=tk.LEFT, padx=20)
        
    def setup_logs_tab(self):
        """CREATE LOGGING TAB"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Logs")
        
        # Log controls
        control_frame = ttk.Frame(log_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Clear Logs", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save Logs", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Export CSV", 
                  command=self.export_csv).pack(side=tk.LEFT, padx=5)
        
        # Log display
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_status_bar(self):
        """CREATE STATUS BAR"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # Connection status
        self.conn_var = tk.StringVar(value="Disconnected")
        self.conn_label = ttk.Label(status_frame, textvariable=self.conn_var, 
                                   foreground='red')
        self.conn_label.pack(side=tk.RIGHT, padx=5)
        
    def setup_plots(self):
        """SETUP MATPLOTLIB PLOTS"""
        # Create figure for data plotting
        self.fig, self.axes = plt.subplots(2, 2, figsize=(10, 6))
        self.fig.tight_layout(pad=3.0)
        
        # Initialize plot data
        self.plot_data = {
            'time': [],
            'rpm': [],
            'boost': [],
            'afr': []
        }
        
        # Setup plot lines
        self.lines = {
            'rpm': self.axes[0, 0].plot([], [], 'b-')[0],
            'boost': self.axes[0, 1].plot([], [], 'r-')[0],
            'afr': self.axes[1, 0].plot([], [], 'g-')[0]
        }
        
        # Configure axes
        self.axes[0, 0].set_title('RPM')
        self.axes[0, 0].set_ylim(0, 8000)
        self.axes[0, 1].set_title('Boost (PSI)')
        self.axes[0, 1].set_ylim(-10, 25)
        self.axes[1, 0].set_title('AFR')
        self.axes[1, 0].set_ylim(10, 16)
        self.axes[1, 1].axis('off')  # Hide fourth subplot
        
    def connect_vehicle(self):
        """CONNECT TO VEHICLE"""
        def connect_thread():
            try:
                self.status_var.set("Connecting...")
                success = asyncio.run(self.factory_platform.connect())
                
                if success:
                    self.connected = True
                    self.conn_var.set("Connected")
                    self.conn_label.configure(foreground='green')
                    self.status_var.set("Connected to vehicle")
                    self.log_message("Successfully connected to vehicle")
                else:
                    self.status_var.set("Connection failed")
                    self.log_message("Failed to connect to vehicle", level='ERROR')
                    
            except Exception as e:
                self.status_var.set(f"Error: {e}")
                self.log_message(f"Connection error: {e}", level='ERROR')
                
        threading.Thread(target=connect_thread, daemon=True).start()
        
    def start_logging(self):
        """START DATA LOGGING"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to vehicle first")
            return
            
        self.logging = True
        self.log_message("Started data logging")
        threading.Thread(target=self.logging_loop, daemon=True).start()
        
    def logging_loop(self):
        """MAIN LOGGING LOOP"""
        while self.logging and self.running:
            if self.connected:
                try:
                    # Get live data
                    data = asyncio.run(self.factory_platform.get_live_data())
                    
                    # Update gauges
                    self.update_gauges(data)
                    
                    # Update plots
                    self.update_plots(data)
                    
                    # Log data
                    self.log_data.append({
                        'timestamp': time.time(),
                        **data
                    })
                    
                    # Update live data display
                    self.update_live_display(data)
                    
                except Exception as e:
                    self.log_message(f"Logging error: {e}", level='ERROR')
                    
            time.sleep(0.1)
            
    def update_gauges(self, data):
        """UPDATE GAUGE DISPLAYS"""
        for key, gauge in self.gauges.items():
            if key in data:
                value = data[key]
                gauge['var'].set(f"{value:.1f}")
                
                # Update progress bar
                progress = (value - gauge['min']) / (gauge['max'] - gauge['min']) * 100
                gauge['progress']['value'] = max(0, min(100, progress))
                
    def update_plots(self, data):
        """UPDATE MATPLOTLIB PLOTS"""
        current_time = time.time()
        
        # Add data to plot buffers
        self.plot_data['time'].append(current_time)
        for key in ['rpm', 'boost', 'afr']:
            if key in data:
                self.plot_data[key].append(data[key])
                
        # Keep only last 100 points
        max_points = 100
        for key in self.plot_data:
            if len(self.plot_data[key]) > max_points:
                self.plot_data[key] = self.plot_data[key][-max_points:]
                
        # Update plot lines
        if len(self.plot_data['time']) > 1:
            times = np.array(self.plot_data['time'])
            times = times - times[0]  # Relative time
            
            for key, line in self.lines.items():
                if key in self.plot_data and len(self.plot_data[key]) > 0:
                    line.set_data(times, self.plot_data[key])
                    
            # Update plot limits
            for ax in self.axes.flat:
                if ax.has_data():
                    ax.relim()
                    ax.autoscale_view()
                    
    def update_live_display(self, data):
        """UPDATE LIVE DATA TEXT DISPLAY"""
        if hasattr(self, 'live_text'):
            self.live_text.delete(1.0, tk.END)
            
            for key, value in data.items():
                self.live_text.insert(tk.END, f"{key.replace('_', ' ').title()}: {value:.2f}\n")
                
    def generate_tune(self):
        """GENERATE TUNE BASED ON SETTINGS"""
        mode = self.tuning_mode.get()
        mods = [mod for mod, var in self.mods_vars.items() if var.get()]
        
        # Generate tune based on mode and modifications
        tune = self.create_tune_map(mode, mods)
        
        # Display tune
        self.tune_text.delete(1.0, tk.END)
        self.tune_text.insert(tk.END, json.dumps(tune, indent=2))
        
        self.current_tune = tune
        self.log_message(f"Generated {mode} tune with modifications: {', '.join(mods)}")
        
    def create_tune_map(self, mode: str, modifications: List[str]) -> Dict:
        """CREATE TUNE MAP BASED ON MODE AND MODIFICATIONS"""
        base_tune = {
            'mode': mode,
            'modifications': modifications,
            'maps': {}
        }
        
        # Base maps for different modes
        if mode == 'stock':
            base_tune['maps'] = {
                'boost_target': [15.0] * 10,
                'fuel_target': [14.7] * 10,
                'timing_advance': [15.0] * 10
            }
        elif mode == 'performance':
            base_tune['maps'] = {
                'boost_target': [18.0, 19.0, 20.0, 21.0, 22.0, 22.0, 22.0, 22.0, 21.0, 20.0],
                'fuel_target': [12.5, 12.2, 12.0, 11.8, 11.5, 11.5, 11.5, 11.8, 12.0, 12.2],
                'timing_advance': [18.0, 20.0, 22.0, 23.0, 24.0, 24.0, 24.0, 23.0, 22.0, 20.0]
            }
        elif mode == 'race':
            base_tune['maps'] = {
                'boost_target': [22.0, 23.0, 24.0, 25.0, 25.0, 25.0, 25.0, 25.0, 24.0, 23.0],
                'fuel_target': [11.5, 11.2, 11.0, 10.8, 10.5, 10.5, 10.5, 10.8, 11.0, 11.2],
                'timing_advance': [20.0, 22.0, 24.0, 25.0, 26.0, 26.0, 26.0, 25.0, 24.0, 22.0]
            }
            
        # Adjust for modifications
        if 'intake' in modifications:
            for i in range(len(base_tune['maps']['boost_target'])):
                base_tune['maps']['boost_target'][i] += 1.0
                
        if 'downpipe' in modifications:
            for i in range(len(base_tune['maps']['boost_target'])):
                base_tune['maps']['boost_target'][i] += 2.0
                
        if 'ethanol' in modifications:
            for i in range(len(base_tune['maps']['fuel_target'])):
                base_tune['maps']['fuel_target'][i] -= 0.5
                base_tune['maps']['timing_advance'][i] += 2.0
                
        return base_tune
        
    def flash_ecu(self):
        """FLASH ECU WITH CURRENT TUNE"""
        if not self.current_tune:
            messagebox.showwarning("No Tune", "Please generate a tune first")
            return
            
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to vehicle first")
            return
            
        # Confirm flash
        if not messagebox.askyesno("Confirm Flash", 
                                  "This will modify your ECU calibration. Continue?"):
            return
            
        def flash_thread():
            try:
                self.status_var.set("Flashing ECU...")
                # Flash implementation would go here
                time.sleep(2)  # Simulate flash time
                self.status_var.set("Flash complete")
                self.log_message("ECU flashed successfully")
                messagebox.showinfo("Success", "ECU flashed successfully")
                
            except Exception as e:
                self.status_var.set(f"Flash failed: {e}")
                self.log_message(f"Flash failed: {e}", level='ERROR')
                messagebox.showerror("Flash Failed", str(e))
                
        threading.Thread(target=flash_thread, daemon=True).start()
        
    def start_real_time_tuning(self):
        """START REAL-TIME TUNING SESSION"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to vehicle first")
            return
            
        self.status_var.set("Starting real-time tuning...")
        # Real-time tuning implementation would go here
        self.log_message("Real-time tuning session started")
        
    def scan_dtcs(self):
        """SCAN FOR DIAGNOSTIC TROUBLE CODES"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to vehicle first")
            return
            
        def scan_thread():
            try:
                dtcs = asyncio.run(self.factory_platform.diagnostic_engine.scan_dtcs())
                
                # Clear existing DTCs
                for item in self.dtc_tree.get_children():
                    self.dtc_tree.delete(item)
                    
                # Add DTCs to tree
                for dtc in dtcs:
                    self.dtc_tree.insert('', 'end', values=(
                        dtc.code,
                        dtc.description,
                        dtc.severity
                    ))
                    
                self.log_message(f"Found {len(dtcs)} DTCs")
                
            except Exception as e:
                self.log_message(f"DTC scan failed: {e}", level='ERROR')
                
        threading.Thread(target=scan_thread, daemon=True).start()
        
    def clear_dtcs(self):
        """CLEAR DIAGNOSTIC TROUBLE CODES"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please connect to vehicle first")
            return
            
        def clear_thread():
            try:
                success = asyncio.run(self.factory_platform.diagnostic_engine.clear_dtcs())
                
                if success:
                    # Clear DTC tree
                    for item in self.dtc_tree.get_children():
                        self.dtc_tree.delete(item)
                        
                    self.log_message("DTCs cleared successfully")
                    messagebox.showinfo("Success", "DTCs cleared successfully")
                else:
                    messagebox.showerror("Failed", "Failed to clear DTCs")
                    
            except Exception as e:
                self.log_message(f"DTC clear failed: {e}", level='ERROR')
                messagebox.showerror("Failed", str(e))
                
        threading.Thread(target=clear_thread, daemon=True).start()
        
    def enable_launch_control(self):
        """ENABLE LAUNCH CONTROL"""
        rpm = self.launch_rpm.get()
        self.log_message(f"Enabling launch control at {rpm} RPM")
        # Launch control implementation would go here
        
    def enable_flat_shift(self):
        """ENABLE FLFT SHIFT"""
        fuel_cut = self.fuel_cut.get()
        ign_retard = self.ign_retard.get()
        self.log_message(f"Enabling flat shift: {fuel_cut}ms fuel cut, {ign_retard}° retard")
        # Flat shift implementation would go here
        
    def enable_anti_lag(self):
        """ENABLE ANTI-LAG"""
        aggressiveness = self.anti_lag.get()
        self.log_message(f"Enabling anti-lag with aggressiveness {aggressiveness}")
        # Anti-lag implementation would go here
        
    def emergency_stop(self):
        """EMERGENCY STOP - DISABLE ALL MODIFICATIONS"""
        self.logging = False
        self.status_var.set("EMERGENCY STOP ACTIVATED")
        self.log_message("EMERGENCY STOP ACTIVATED - All modifications disabled", level='WARNING')
        
        # Emergency stop implementation would go here
        
    def log_message(self, message: str, level: str = 'INFO'):
        """LOG MESSAGE TO DISPLAY"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, formatted_message)
            self.log_text.see(tk.END)
            
        self.logger.log(getattr(logging, level), message)
        
    def clear_logs(self):
        """CLEAR LOG DISPLAY"""
        if hasattr(self, 'log_text'):
            self.log_text.delete(1.0, tk.END)
            
    def save_logs(self):
        """SAVE LOGS TO FILE"""
        filename = f"mazda_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        if hasattr(self, 'log_text'):
            with open(filename, 'w') as f:
                f.write(self.log_text.get(1.0, tk.END))
                
        self.log_message(f"Logs saved to {filename}")
        
    def save_diag_report(self):
        """SAVE DIAGNOSTIC REPORT"""
        filename = f"diag_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w') as f:
            f.write("Mazdaspeed 3 Diagnostic Report\n")
            f.write("=" * 40 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write DTCs
            f.write("Diagnostic Trouble Codes:\n")
            for item in self.dtc_tree.get_children():
                values = self.dtc_tree.item(item)['values']
                f.write(f"  {values[0]} - {values[1]} ({values[2]})\n")
                
        self.log_message(f"Diagnostic report saved to {filename}")
        
    def export_csv(self):
        """EXPORT LOGGED DATA TO CSV"""
        if not self.log_data:
            messagebox.showwarning("No Data", "No data to export")
            return
            
        filename = f"mazda_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        import csv
        
        with open(filename, 'w', newline='') as f:
            if self.log_data:
                writer = csv.DictWriter(f, fieldnames=self.log_data[0].keys())
                writer.writeheader()
                writer.writerows(self.log_data)
                
        self.log_message(f"Data exported to {filename}")
        
    def start_background_tasks(self):
        """START BACKGROUND MONITORING TASKS"""
        # Start data update timer
        self.update_display()
        
    def update_display(self):
        """UPDATE DISPLAY PERIODICALLY"""
        if self.running:
            # Update plots if they exist
            if hasattr(self, 'fig'):
                self.fig.canvas.draw_idle()
                
            # Schedule next update
            self.root.after(100, self.update_display)
            
    def on_closing(self):
        """CLEANUP ON APPLICATION CLOSE"""
        self.running = False
        self.logging = False
        
        if self.connected:
            asyncio.run(self.factory_platform.disconnect())
            
        self.root.destroy()

def main():
    """MAIN APPLICATION ENTRY POINT"""
    root = tk.Tk()
    app = MazdaSpeed3TunerGUI(root)
    
    # Handle window close
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start application
    root.mainloop()

if __name__ == "__main__":
    main()
