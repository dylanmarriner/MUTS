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
        
        # Security status
        security_frame = ttk.LabelFrame(connection_frame, text="Security Status", padding=10)
        security_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.security_info_text = tk.Text(vehicle_frame, height=4, width=80)
        self.security_info_text.pack(fill=tk.X, padx=5, pady=5)
    
    def _create_dashboard_tab(self):
        """Create real-time dashboard tab"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Create gauge frame
        gauge_frame = ttk.LabelFrame(dashboard_frame, text="Live Data", padding=10)
        gauge_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create gauges
        self._create_gauges(gauge_frame)
    
    def _create_gauges(self, parent):
        """Create data display gauges"""
        # RPM gauge
        rpm_frame = ttk.Frame(parent)
        rpm_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(rpm_frame, text="RPM", font=('Arial', 12, 'bold')).pack()
        self.rpm_label = ttk.Label(rpm_frame, text="0", font=('Arial', 24))
        self.rpm_label.pack()
        
        # Boost gauge
        boost_frame = ttk.Frame(parent)
        boost_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(boost_frame, text="Boost (PSI)", font=('Arial', 12, 'bold')).pack()
        self.boost_label = ttk.Label(boost_frame, text="0.0", font=('Arial', 24))
        self.boost_label.pack()
        
        # Throttle position
        throttle_frame = ttk.Frame(parent)
        throttle_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(throttle_frame, text="Throttle %", font=('Arial', 12, 'bold')).pack()
        self.throttle_label = ttk.Label(throttle_frame, text="0", font=('Arial', 24))
        self.throttle_label.pack()
        
        # Coolant temperature
        temp_frame = ttk.Frame(parent)
        temp_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(temp_frame, text="Coolant (°C)", font=('Arial', 12, 'bold')).pack()
        self.temp_label = ttk.Label(temp_frame, text="0", font=('Arial', 24))
        self.temp_label.pack()
    
    def _create_tuning_tab(self):
        """Create map tuning tab"""
        tuning_frame = ttk.Frame(self.notebook)
        self.notebook.add(tuning_frame, text="Tuning")
        
        # Map selection
        map_select_frame = ttk.LabelFrame(tuning_frame, text="Map Selection", padding=10)
        map_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(map_select_frame, text="Select Map:").pack(side=tk.LEFT)
        self.map_var = tk.StringVar()
        self.map_combo = ttk.Combobox(map_select_frame, textvariable=self.map_var, width=30)
        self.map_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(map_select_frame, text="Load Map", 
                  command=self._load_map).pack(side=tk.LEFT, padx=5)
        
        # Map display
        map_display_frame = ttk.LabelFrame(tuning_frame, text="Map Display", padding=10)
        map_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.map_canvas = tk.Canvas(map_display_frame, bg='white')
        self.map_canvas.pack(fill=tk.BOTH, expand=True)
    
    def _create_diagnostic_tab(self):
        """Create diagnostic tab"""
        diagnostic_frame = ttk.Frame(self.notebook)
        self.notebook.add(diagnostic_frame, text="Diagnostics")
        
        # DTC display
        dtc_frame = ttk.LabelFrame(diagnostic_frame, text="Diagnostic Trouble Codes", padding=10)
        dtc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # DTC list
        self.dtc_tree = ttk.Treeview(dtc_frame, columns=('Code', 'Description', 'Status'), 
                                     show='headings')
        self.dtc_tree.heading('Code', text='Code')
        self.dtc_tree.heading('Description', text='Description')
        self.dtc_tree.heading('Status', text='Status')
        self.dtc_tree.pack(fill=tk.BOTH, expand=True)
        
        # DTC controls
        dtc_control_frame = ttk.Frame(dtc_frame)
        dtc_control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(dtc_control_frame, text="Read DTCs", 
                  command=self._read_dtcs).pack(side=tk.LEFT, padx=5)
        ttk.Button(dtc_control_frame, text="Clear DTCs", 
                  command=self._clear_dtcs).pack(side=tk.LEFT, padx=5)
    
    def _create_flashing_tab(self):
        """Create ROM flashing tab"""
        flashing_frame = ttk.Frame(self.notebook)
        self.notebook.add(flashing_frame, text="Flashing")
        
        # ROM operations
        rom_frame = ttk.LabelFrame(flashing_frame, text="ROM Operations", padding=10)
        rom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(rom_frame, text="Read ROM", 
                  command=self._read_rom).pack(side=tk.LEFT, padx=5)
        ttk.Button(rom_frame, text="Write ROM", 
                  command=self._write_rom).pack(side=tk.LEFT, padx=5)
        ttk.Button(rom_frame, text="Verify ROM", 
                  command=self._verify_rom).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(flashing_frame, variable=self.progress_var,
                                           maximum=100, length=400)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=10)
    
    def _create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Logging settings
        log_frame = ttk.LabelFrame(settings_frame, text="Logging", padding=10)
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.log_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_frame, text="Enable Logging", 
                       variable=self.log_enabled_var).pack(anchor=tk.W)
        
        # Real-time tuning settings
        rt_frame = ttk.LabelFrame(settings_frame, text="Real-time Tuning", padding=10)
        rt_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.adaptive_tuning_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(rt_frame, text="Enable Adaptive Tuning", 
                       variable=self.adaptive_tuning_var,
                       command=self._toggle_adaptive_tuning).pack(anchor=tk.W)
    
    def _create_status_bar(self, parent):
        """Create status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.connection_label = ttk.Label(status_frame, text="Disconnected", 
                                        relief=tk.SUNKEN, foreground='red')
        self.connection_label.pack(side=tk.RIGHT, padx=(5, 0))
    
    def _start_background_tasks(self):
        """Start background update tasks"""
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
    
    def _update_loop(self):
        """Main update loop for GUI"""
        while True:
            try:
                if self.is_connected:
                    self._update_live_data()
                
                time.sleep(0.1)  # 10Hz update rate
                
            except Exception as e:
                self.logger.error(f"Update loop error: {e}")
                time.sleep(1.0)
    
    def _update_live_data(self):
        """Update live data displays"""
        try:
            # Read sensor data
            rpm = self.ecu_comm.read_live_data(0x0C)
            boost = self.ecu_comm.read_live_data(0x223365)
            throttle = self.ecu_comm.read_live_data(0x11)
            coolant = self.ecu_comm.read_live_data(0x05)
            
            # Update labels in main thread
            self.root.after(0, self._update_gauges, rpm, boost, throttle, coolant)
            
        except Exception as e:
            self.logger.debug(f"Live data update error: {e}")
    
    def _update_gauges(self, rpm, boost, throttle, coolant):
        """Update gauge displays"""
        if rpm is not None:
            self.rpm_label.config(text=f"{int(rpm)}")
        if boost is not None:
            self.boost_label.config(text=f"{boost:.1f}")
        if throttle is not None:
            self.throttle_label.config(text=f"{int(throttle)}")
        if coolant is not None:
            self.temp_label.config(text=f"{int(coolant)}")
    
    def _on_tab_changed(self, event):
        """Handle tab change event"""
        selected_tab = event.widget.tab('current')['text']
        self.current_tab = selected_tab
        
        if selected_tab == "Diagnostics":
            self._read_dtcs()
        elif selected_tab == "Connection":
            self._update_vehicle_info()
    
    def _connect_ecu(self):
        """Connect to ECU"""
        try:
            interface = self.interface_var.get()
            
            if self.ecu_comm.connect():
                self.is_connected = True
                self.connection_label.config(text="Connected", foreground='green')
                self.status_label.config(text=f"Connected to ECU on {interface}")
                
                # Update vehicle info
                self._update_vehicle_info()
                
                messagebox.showinfo("Success", "Connected to ECU successfully!")
            else:
                messagebox.showerror("Error", "Failed to connect to ECU")
                
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {e}")
    
    def _disconnect_ecu(self):
        """Disconnect from ECU"""
        try:
            self.ecu_comm.disconnect()
            self.is_connected = False
            self.connection_label.config(text="Disconnected", foreground='red')
            self.status_label.config(text="Disconnected from ECU")
            
            # Clear displays
            self._clear_displays()
            
        except Exception as e:
            messagebox.showerror("Error", f"Disconnect error: {e}")
    
    def _update_vehicle_info(self):
        """Update vehicle information display"""
        try:
            info = self.rom_ops.read_ecu_info()
            
            self.vehicle_info_text.delete(1.0, tk.END)
            self.vehicle_info_text.insert(tk.END, f"VIN: {info.get('vin', 'Unknown')}\n")
            self.vehicle_info_text.insert(tk.END, f"ECU Part Number: {info.get('ecu_part_number', 'Unknown')}\n")
            self.vehicle_info_text.insert(tk.END, f"Calibration ID: {info.get('calibration_id', 'Unknown')}\n")
            self.vehicle_info_text.insert(tk.END, f"Software Version: {info.get('software_version', 'Unknown')}\n")
            
            # Update security status
            security_status = self.security_mgr.check_security_status()
            self.security_info_text.delete(1.0, tk.END)
            self.security_info_text.insert(tk.END, f"Security Level: {security_status['level_description']}\n")
            self.security_info_text.insert(tk.END, f"Unlocked: {'Yes' if security_status['unlocked'] else 'No'}\n")
            
        except Exception as e:
            self.logger.error(f"Failed to update vehicle info: {e}")
    
    def _load_map(self):
        """Load selected map"""
        map_name = self.map_var.get()
        if not map_name:
            messagebox.showwarning("Warning", "Please select a map to load")
            return
        
        if not self.rom_data:
            messagebox.showwarning("Warning", "Please read ROM first")
            return
        
        try:
            map_data = self.map_editor.load_map_from_rom(map_name, self.rom_data)
            if map_data:
                self._display_map(map_data)
                self.status_label.config(text=f"Loaded map: {map_name}")
            else:
                messagebox.showerror("Error", f"Failed to load map: {map_name}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Map load error: {e}")
    
    def _display_map(self, map_data):
        """Display map on canvas"""
        # Clear canvas
        self.map_canvas.delete("all")
        
        # Get canvas dimensions
        width = self.map_canvas.winfo_width()
        height = self.map_canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            self.root.after(100, lambda: self._display_map(map_data))
            return
        
        # Draw map grid
        cell_width = width / map_data.data.shape[1]
        cell_height = height / map_data.data.shape[0]
        
        for i in range(map_data.data.shape[0]):
            for j in range(map_data.data.shape[1]):
                x1 = j * cell_width
                y1 = i * cell_height
                x2 = x1 + cell_width
                y2 = y1 + cell_height
                
                # Color based on value
                value = map_data.data[i, j]
                normalized = (value - map_data.definition.min_value) / \
                           (map_data.definition.max_value - map_data.definition.min_value)
                color = self._value_to_color(normalized)
                
                self.map_canvas.create_rectangle(x1, y1, x2, y2, 
                                              fill=color, outline='gray')
                
                # Add text for larger cells
                if cell_width > 40 and cell_height > 20:
                    self.map_canvas.create_text((x1+x2)/2, (y1+y2)/2,
                                              text=f"{value:.1f}",
                                              font=('Arial', 8))
    
    def _value_to_color(self, normalized):
        """Convert normalized value to color"""
        # Blue to red gradient
        if normalized < 0.5:
            r = int(255 * (normalized * 2))
            g = int(255 * (normalized * 2))
            b = 255
        else:
            r = 255
            g = int(255 * (2 - normalized * 2))
            b = int(255 * (2 - normalized * 2))
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _read_dtcs(self):
        """Read diagnostic trouble codes"""
        try:
            dtcs = self.ecu_comm.read_dtcs()
            
            # Clear existing items
            for item in self.dtc_tree.get_children():
                self.dtc_tree.delete(item)
            
            # Add DTCs to tree
            for dtc in dtcs:
                self.dtc_tree.insert('', 'end', values=(
                    dtc['code'],
                    dtc['description'],
                    dtc['status']
                ))
            
            self.status_label.config(text=f"Read {len(dtcs)} DTC(s)")
            
        except Exception as e:
            messagebox.showerror("Error", f"DTC read error: {e}")
    
    def _clear_dtcs(self):
        """Clear diagnostic trouble codes"""
        try:
            if messagebox.askyesno("Confirm", "Clear all DTCs?"):
                if self.ecu_comm.clear_dtcs():
                    messagebox.showinfo("Success", "DTCs cleared successfully")
                    self._read_dtcs()
                else:
                    messagebox.showerror("Error", "Failed to clear DTCs")
                    
        except Exception as e:
            messagebox.showerror("Error", f"DTC clear error: {e}")
    
    def _read_rom(self):
        """Read ECU ROM"""
        try:
            if not self.is_connected:
                messagebox.showwarning("Warning", "Please connect to ECU first")
                return
            
            # Unlock security for ROM access
            if not self.security_mgr.unlock_ecu():
                messagebox.showerror("Error", "Failed to unlock ECU security")
                return
            
            # Enter programming mode
            if not self.security_mgr.enter_programming_mode():
                messagebox.showerror("Error", "Failed to enter programming mode")
                return
            
            # Read ROM with progress callback
            def progress_callback(current, total):
                progress = (current / total) * 100
                self.progress_var.set(progress)
                self.root.update()
            
            self.rom_data = self.rom_ops.read_complete_rom(progress_callback)
            
            if self.rom_data:
                messagebox.showinfo("Success", f"ROM read successfully ({len(self.rom_data)} bytes)")
                self.status_label.config(text="ROM read complete")
                
                # Populate map list
                maps = self.map_editor.map_manager.get_all_maps()
                self.map_combo['values'] = list(maps.keys())
            else:
                messagebox.showerror("Error", "Failed to read ROM")
            
            # Reset progress bar
            self.progress_var.set(0)
            
        except Exception as e:
            messagebox.showerror("Error", f"ROM read error: {e}")
            self.progress_var.set(0)
    
    def _write_rom(self):
        """Write ROM to ECU"""
        messagebox.showinfo("Info", "ROM writing not implemented in this version")
    
    def _verify_rom(self):
        """Verify ROM integrity"""
        if not self.rom_data:
            messagebox.showwarning("Warning", "Please read ROM first")
            return
        
        try:
            results = self.rom_ops.verify_rom_integrity(self.rom_data)
            
            if results['overall_valid']:
                messagebox.showinfo("Success", "ROM verification passed")
            else:
                errors = '\n'.join(results['errors'])
                messagebox.showwarning("Warning", f"ROM verification failed:\n{errors}")
                
        except Exception as e:
            messagebox.showerror("Error", f"ROM verification error: {e}")
    
    def _toggle_adaptive_tuning(self):
        """Toggle adaptive tuning"""
        if self.adaptive_tuning_var.get():
            self.realtime_tuner.start_adaptive_tuning()
            self.status_label.config(text="Adaptive tuning enabled")
        else:
            self.realtime_tuner.stop_adaptive_tuning()
            self.status_label.config(text="Adaptive tuning disabled")
    
    def _clear_displays(self):
        """Clear all data displays"""
        self.rpm_label.config(text="0")
        self.boost_label.config(text="0.0")
        self.throttle_label.config(text="0")
        self.temp_label.config(text="0")
        self.vehicle_info_text.delete(1.0, tk.END)
        self.security_info_text.delete(1.0, tk.END)
        self.map_canvas.delete("all")
    
    def run(self):
        """Run the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("GUI terminated by user")
        finally:
            # Cleanup
            if self.is_connected:
                self._disconnect_ecu()
