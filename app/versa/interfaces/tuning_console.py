#!/usr/bin/env python3
"""
Tuning Console Interface - Command-line interface for VersaTuner
Provides full functionality for users who prefer terminal/scripting
"""

import cmd
import sys
import json
import argparse
from typing import Dict, List, Optional, Any
from ..core.ecu_communication import ECUCommunicator
from ..core.security_access import SecurityManager
from ..core.rom_operations import ROMOperations
from ..tuning.map_editor import MapEditor
from ..tuning.realtime_tuning import RealTimeTuner
from ..vehicle.mazdaspeed3_2011 import Mazdaspeed32011
from ..vehicle.diagnostic_services import DiagnosticManager
from ..utils.logger import VersaLogger
from ..utils.file_operations import FileManager

class TuningConsole(cmd.Cmd):
    """
    VersaTuner Console Interface - Command-line interface with full functionality
    Provides all VersaTuner features through an interactive console
    """
    
    intro = """
╔══════════════════════════════════════════════════════════════╗
║                   VersaTuner Console v1.0                   ║
║          Mazdaspeed 3 2011 Tuning Software                  ║
║         Type 'help' or '?' for command list                 ║
╚══════════════════════════════════════════════════════════════╝
"""
    prompt = 'versatuner> '
    
    def __init__(self):
        super().__init__()
        self.logger = VersaLogger(__name__)
        
        # Initialize core components
        self.ecu_comm = ECUCommunicator()
        self.security_mgr = SecurityManager(self.ecu_comm)
        self.rom_ops = ROMOperations(self.ecu_comm)
        self.map_editor = MapEditor(self.rom_ops)
        self.realtime_tuner = RealTimeTuner(self.ecu_comm)
        self.vehicle = Mazdaspeed32011()
        self.diagnostic_mgr = DiagnosticManager(self.ecu_comm)
        self.file_mgr = FileManager()
        
        # Application state
        self.is_connected = False
        self.rom_data = None
        self.current_map = None
        
    def do_connect(self, arg):
        """Connect to ECU: connect [interface=can0]"""
        interface = arg.strip() or "can0"
        self.ecu_comm.interface = interface
        
        print(f"Connecting to ECU via {interface}...")
        if self.ecu_comm.connect():
            self.is_connected = True
            print("✓ Successfully connected to ECU")
            self._show_vehicle_info()
        else:
            print("✗ Failed to connect to ECU")
    
    def do_disconnect(self, arg):
        """Disconnect from ECU"""
        if self.is_connected:
            self.ecu_comm.disconnect()
            self.is_connected = False
            print("Disconnected from ECU")
        else:
            print("Not connected to ECU")
    
    def do_vehicle_info(self, arg):
        """Display vehicle information"""
        if not self._check_connection():
            return
        
        self._show_vehicle_info()
    
    def _show_vehicle_info(self):
        """Display comprehensive vehicle information"""
        info = self.rom_ops.read_ecu_info()
        vehicle_info = self.vehicle.get_vehicle_info()
        
        print("\n" + "="*50)
        print("VEHICLE INFORMATION")
        print("="*50)
        print(f"VIN: {info.get('vin', 'Unknown')}")
        print(f"ECU Part: {info.get('ecu_part_number', 'Unknown')}")
        print(f"Calibration: {info.get('calibration_id', 'Unknown')}")
        print(f"Software: {info.get('software_version', 'Unknown')}")
        print(f"Model: {vehicle_info['model']} {vehicle_info['year']}")
        print(f"Engine: {vehicle_info['engine_specs']['displacement']}L {vehicle_info['engine_specs']['aspiration']}")
        print(f"Power: {self.vehicle.ecu_calibrations['stock_power']['horsepower']}HP")
        print(f"Torque: {self.vehicle.ecu_calibrations['stock_power']['torque']} lb-ft")
        print("="*50)
    
    def do_security_status(self, arg):
        """Show ECU security status"""
        if not self._check_connection():
            return
        
        status = self.security_mgr.check_security_status()
        print("\nSECURITY STATUS")
        print("-"*30)
        print(f"Unlocked: {'Yes' if status['unlocked'] else 'No'}")
        print(f"Level: {status['current_level']} - {status['level_description']}")
        print(f"Access Counter: {status.get('access_counter', 'Unknown')}")
    
    def do_unlock_ecu(self, arg):
        """Unlock ECU security for programming"""
        if not self._check_connection():
            return
        
        print("Unlocking ECU security...")
        if self.security_mgr.unlock_ecu():
            print("✓ ECU security unlocked successfully")
        else:
            print("✗ Failed to unlock ECU security")
    
    def do_read_rom(self, arg):
        """Read complete ECU ROM to file: read_rom [filename]"""
        if not self._check_connection():
            return
        
        filename = arg.strip() or "mazdaspeed3_rom.bin"
        
        # Unlock security first
        if not self.security_mgr.unlock_ecu():
            print("✗ Failed to unlock ECU - cannot read ROM")
            return
        
        print("Reading ROM from ECU...")
        
        def progress_callback(current, total):
            percent = (current / total) * 100
            print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        self.rom_data = self.rom_ops.read_complete_rom(progress_callback)
        print()  # New line after progress
        
        if self.rom_data:
            # Save to file
            if self.file_mgr.save_rom_file(self.rom_data, filename):
                print(f"✓ ROM read successfully ({len(self.rom_data)} bytes)")
                print(f"✓ Saved to: {filename}")
            else:
                print("✗ Failed to save ROM file")
        else:
            print("✗ Failed to read ROM")
    
    def do_list_maps(self, arg):
        """List all available tuning maps"""
        maps = self.map_editor.map_manager.get_all_maps()
        
        print("\nAVAILABLE MAPS")
        print("-"*50)
        for category, map_names in self.map_editor.map_manager.categories.items():
            print(f"\n{category}:")
            for map_name in map_names:
                map_def = maps[map_name]
                print(f"  {map_name}: {map_def.description}")
    
    def do_load_map(self, arg):
        """Load map from ROM: load_map <map_name>"""
        if not self.rom_data:
            print("✗ No ROM data loaded - read ROM first")
            return
        
        map_name = arg.strip()
        if not map_name:
            print("✗ Please specify a map name")
            return
        
        print(f"Loading map: {map_name}")
        map_data = self.map_editor.load_map_from_rom(map_name, self.rom_data)
        
        if map_data:
            self.current_map = map_data
            print(f"✓ Loaded map: {map_name}")
            print(f"  Size: {map_data.data.shape}")
            print(f"  Range: {map_data.data.min():.2f} - {map_data.data.max():.2f}")
        else:
            print(f"✗ Failed to load map: {map_name}")
    
    def do_show_map(self, arg):
        """Display current map values in grid format"""
        if not self.current_map:
            print("✗ No map loaded")
            return
        
        print(f"\n{self.current_map.definition.name}")
        print(f"Description: {self.current_map.definition.description}")
        print(f"Units: {self.current_map.definition.units}")
        print("-"*50)
        
        data = self.current_map.data
        for i, row in enumerate(data):
            row_str = " ".join(f"{val:8.2f}" for val in row)
            print(row_str)
    
    def do_read_live_data(self, arg):
        """Read live data from ECU"""
        if not self._check_connection():
            return
        
        print("\nLIVE DATA")
        print("-"*30)
        
        # Common PIDs to read
        pids = {
            'RPM': 0x0C,
            'Vehicle Speed': 0x0D,
            'Throttle Position': 0x11,
            'Coolant Temp': 0x05,
            'Intake Air Temp': 0x0F,
            'Boost Pressure': 0x223365,
        }
        
        for name, pid in pids.items():
            value = self.ecu_comm.read_live_data(pid)
            if value is not None:
                print(f"{name}: {value:.1f}")
            else:
                print(f"{name: <15}: --")
    
    def do_read_dtcs(self, arg):
        """Read diagnostic trouble codes"""
        if not self._check_connection():
            return
        
        print("\nDIAGNOSTIC TROUBLE CODES")
        print("-"*40)
        
        dtcs = self.ecu_comm.read_dtcs()
        
        if dtcs:
            for dtc in dtcs:
                print(f"{dtc['code']}: {dtc['description']} [{dtc['status']}]")
        else:
            print("No DTCs found")
    
    def do_clear_dtcs(self, arg):
        """Clear all diagnostic trouble codes"""
        if not self._check_connection():
            return
        
        if input("Clear all DTCs? (y/N): ").lower() == 'y':
            if self.ecu_comm.clear_dtcs():
                print("✓ DTCs cleared successfully")
            else:
                print("✗ Failed to clear DTCs")
    
    def do_start_monitoring(self, arg):
        """Start real-time monitoring"""
        if not self._check_connection():
            return
        
        print("Starting real-time monitoring...")
        self.realtime_tuner.start_monitoring()
        print("✓ Monitoring started (press Ctrl+C to stop)")
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
            self.realtime_tuner.stop_monitoring()
            print("✓ Monitoring stopped")
    
    def do_tune_recommendations(self, arg):
        """Get tune recommendations for power target"""
        try:
            power_target = int(arg.strip())
            if power_target <= 0:
                raise ValueError
        except:
            print("Usage: tune_recommendations <power_gain_hp>")
            return
        
        tune = self.vehicle.get_recommended_tunes(power_target)
        
        print(f"\n{TUNE['name'].upper()} TUNE RECOMMENDATIONS")
        print("-"*50)
        print(f"Description: {tune['description']}")
        print(f"Target Boost: {tune['boost_target']} PSI")
        print(f"Ignition Advance: +{tune['ignition_advance']}°")
        print(f"Target AFR: {tune['afr_target']}")
        print(f"Rev Limit: {tune['rev_limit']} RPM")
        print(f"Estimated Gain: +{tune['estimated_gain']} HP")
        print(f"Required Mods: {', '.join(tune['required_mods'])}")
    
    def do_validate_tune(self, arg):
        """Validate tune parameters against vehicle limits"""
        print("Enter tune parameters (JSON format):")
        print("Example: {\"boost_target\": 20.0, \"ignition_advance\": 2.5}")
        
        try:
            tune_input = input("> ")
            tune_data = json.loads(tune_input)
            
            results = self.vehicle.validate_tune_parameters(tune_data)
            
            print("\nVALIDATION RESULTS")
            print("-"*30)
            print(f"Valid: {'✓' if results['valid'] else '✗'}")
            
            if results['warnings']:
                print("\nWarnings:")
                for warning in results['warnings']:
                    print(f"  - {warning}")
            
            if results['corrections']:
                print("\nCorrections:")
                for param, value in results['corrections'].items():
                    print(f"  {param}: {value}")
                    
        except json.JSONDecodeError:
            print("✗ Invalid JSON format")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def do_save_session(self, arg):
        """Save current tuning session"""
        filename = arg.strip() or f"tuning_session_{int(time.time())}.json"
        
        self.realtime_tuner.save_tuning_session(filename)
        print(f"✓ Session saved to: {filename}")
    
    def do_quit(self, arg):
        """Exit the console"""
        print("Goodbye!")
        return True
    
    def do_exit(self, arg):
        """Exit the console"""
        return self.do_quit(arg)
    
    def _check_connection(self) -> bool:
        """Check if connected to ECU"""
        if not self.is_connected:
            print("✗ Not connected to ECU - use 'connect' first")
            return False
        return True
    
    def run(self):
        """Run the console interface"""
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            if self.is_connected:
                self.ecu_comm.disconnect()

if __name__ == "__main__":
    console = TuningConsole()
    console.run()
