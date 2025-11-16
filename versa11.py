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
    
    def do_unlock(self, arg):
        """Unlock ECU security: unlock [level=3]"""
        if not self._check_connection():
            return
        
        level = int(arg.strip() or "3")
        print(f"Unlocking ECU security level {level}...")
        
        if self.security_mgr.unlock_ecu(level):
            status = self.security_mgr.check_security_status()
            print(f"✓ Security unlocked: {status['level_description']}")
        else:
            print("✗ Failed to unlock ECU security")
    
    def do_read_rom(self, arg):
        """Read complete ROM from ECU: read_rom [output_file]"""
        if not self._check_connection():
            return
        
        output_file = arg.strip() or "backup_rom.bin"
        
        def progress_callback(current, total):
            percent = (current / total) * 100
            sys.stdout.write(f"\rReading ROM: {percent:.1f}% ({current}/{total} bytes)")
            sys.stdout.flush()
        
        print("Reading ROM from ECU...")
        rom_data = self.rom_ops.read_complete_rom(progress_callback)
        
        if rom_data:
            self.rom_data = rom_data
            print(f"\n✓ ROM read successfully: {len(rom_data)} bytes")
            
            # Save to file
            try:
                with open(output_file, 'wb') as f:
                    f.write(rom_data)
                print(f"✓ ROM saved to: {output_file}")
            except Exception as e:
                print(f"✗ Failed to save ROM: {e}")
        else:
            print("\n✗ Failed to read ROM")
    
    def do_load_rom(self, arg):
        """Load ROM from file: load_rom <filename>"""
        filename = arg.strip()
        if not filename:
            print("Usage: load_rom <filename>")
            return
        
        try:
            with open(filename, 'rb') as f:
                self.rom_data = f.read()
            print(f"✓ ROM loaded: {len(self.rom_data)} bytes from {filename}")
        except Exception as e:
            print(f"✗ Failed to load ROM: {e}")
    
    def do_verify_rom(self, arg):
        """Verify ROM integrity"""
        if not self.rom_data:
            print("No ROM data loaded")
            return
        
        print("Verifying ROM integrity...")
        results = self.rom_ops.verify_rom_integrity(self.rom_data)
        
        if results['overall_valid']:
            print("✓ ROM verification passed")
        else:
            print("✗ ROM verification failed")
            for error in results['errors']:
                print(f"  - {error}")
    
    def do_list_maps(self, arg):
        """List available tuning maps: list_maps [category]"""
        category = arg.strip() or None
        
        if category:
            maps = self.map_editor.map_manager.get_maps_by_category(category)
            print(f"\nMaps in category '{category}':")
        else:
            categories = self.map_editor.map_manager.get_all_categories()
            print("\nAvailable map categories:")
            for cat in categories:
                maps = self.map_editor.map_manager.get_maps_by_category(cat)
                print(f"  {cat}: {len(maps)} maps")
            return
        
        for map_def in maps:
            print(f"  {map_def.name:30} {map_def.type:10} {map_def.description}")
    
    def do_load_map(self, arg):
        """Load tuning map: load_map <map_name>"""
        if not self.rom_data:
            print("No ROM data loaded. Use 'read_rom' or 'load_rom' first.")
            return
        
        map_name = arg.strip()
        if not map_name:
            print("Usage: load_map <map_name>")
            return
        
        print(f"Loading map: {map_name}")
        map_data = self.map_editor.load_map_from_rom(map_name, self.rom_data)
        
        if map_data:
            self.current_map = map_data
            print(f"✓ Map loaded successfully")
            self._display_map_preview(map_data)
        else:
            print("✗ Failed to load map")
    
    def _display_map_preview(self, map_data):
        """Display preview of loaded map"""
        map_def = map_data.definition
        data = map_data.data
        
        print(f"\nMap: {map_def.name}")
        print(f"Type: {map_def.type}")
        print(f"Units: {map_def.units}")
        print(f"Size: {data.shape}")
        
        if len(data.shape) == 2:
            # 2D map preview
            print("\nPreview (first 4x4 values):")
            for y in range(min(4, data.shape[0])):
                row_vals = [f"{data[y, x]:6.2f}" for x in range(min(4, data.shape[1]))]
                print("  " + " ".join(row_vals))
        elif len(data.shape) == 1:
            # 1D map preview
            print("\nPreview (first 10 values):")
            preview_vals = [f"{val:6.2f}" for val in data[:10]]
            print("  " + " ".join(preview_vals))
        else:
            # Single value
            print(f"\nValue: {data[0]:.2f} {map_def.units}")
    
    def do_modify_map(self, arg):
        """Modify map value: modify_map <x> <y> <value>"""
        if not self.current_map:
            print("No map loaded. Use 'load_map' first.")
            return
        
        try:
            parts = arg.split()
            if len(parts) != 3:
                print("Usage: modify_map <x_index> <y_index> <value>")
                return
            
            x_index = int(parts[0])
            y_index = int(parts[1])
            new_value = float(parts[2])
            
            if self.map_editor.modify_map_value(
                self.current_map.definition.name, x_index, y_index, new_value
            ):
                print("✓ Map value modified successfully")
                self._display_map_preview(self.current_map)
            else:
                print("✗ Failed to modify map value")
                
        except ValueError as e:
            print(f"Invalid arguments: {e}")
    
    def do_global_adjust(self, arg):
        """Apply global adjustment: global_adjust <value> [map_name]"""
        try:
            parts = arg.split()
            if not parts:
                print("Usage: global_adjust <value> [map_name]")
                return
            
            value = float(parts[0])
            map_name = parts[1] if len(parts) > 1 else self.current_map.definition.name
            
            if not map_name:
                print("No map specified and no map loaded")
                return
            
            if self.map_editor.apply_global_adjustment(map_name, value):
                print(f"✓ Global adjustment of {value} applied to {map_name}")
            else:
                print("✗ Failed to apply global adjustment")
                
        except ValueError as e:
            print(f"Invalid value: {e}")
    
    def do_create_tune(self, arg):
        """Create performance tune: create_tune <stage> [output_file]"""
        if not self.rom_data:
            print("No ROM data loaded")
            return
        
        try:
            parts = arg.split()
            if not parts:
                print("Usage: create_tune <stage> [output_file]")
                print("Stages: 1 (+30HP), 2 (+60HP), 3 (+90HP)")
                return
            
            stage = int(parts[0])
            output_file = parts[1] if len(parts) > 1 else f"stage_{stage}_tune.bin"
            
            power_gains = {1: 30, 2: 60, 3: 90}
            if stage not in power_gains:
                print("Invalid stage. Use 1, 2, or 3.")
                return
            
            print(f"Creating Stage {stage} tune (+{power_gains[stage]}HP target)...")
            tuned_rom = self.map_editor.create_performance_tune(self.rom_data, power_gains[stage])
            
            if tuned_rom:
                # Save tuned ROM
                with open(output_file, 'wb') as f:
                    f.write(tuned_rom)
                print(f"✓ Stage {stage} tune created and saved to: {output_file}")
                
                # Show tune details
                tune_info = self.vehicle.get_recommended_tunes(power_gains[stage])
                print(f"  Boost Target: {tune_info['boost_target']} PSI")
                print(f"  Ignition Advance: {tune_info['ignition_advance']}°")
                print(f"  AFR Target: {tune_info['afr_target']}:1")
                print(f"  Rev Limit: {tune_info['rev_limit']} RPM")
                
            else:
                print("✗ Failed to create tune")
                
        except Exception as e:
            print(f"Error creating tune: {e}")
    
    def do_write_rom(self, arg):
        """Write ROM to ECU: write_rom [filename]"""
        if not self._check_connection():
            return
        
        filename = arg.strip()
        rom_data = None
        
        if filename:
            # Load ROM from file
            try:
                with open(filename, 'rb') as f:
                    rom_data = f.read()
                print(f"Loaded ROM from: {filename}")
            except Exception as e:
                print(f"Failed to load ROM file: {e}")
                return
        elif self.rom_data:
            # Use currently loaded ROM
            rom_data = self.rom_data
            print("Using currently loaded ROM")
        else:
            print("No ROM data available. Load ROM first or specify filename.")
            return
        
        # Verify ROM before writing
        print("Verifying ROM before writing...")
        results = self.rom_ops.verify_rom_integrity(rom_data)
        if not results['overall_valid']:
            print("ROM verification failed! Writing aborted.")
            return
        
        # Confirm write operation
        response = input("WARNING: This will overwrite ECU ROM. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Write operation cancelled.")
            return
        
        # Write ROM to ECU
        print("Writing ROM to ECU...")
        
        def progress_callback(current, total):
            percent = (current / total) * 100
            sys.stdout.write(f"\rWriting: {percent:.1f}% ({current}/{total} bytes)")
            sys.stdout.flush()
        
        success = self.rom_ops.write_complete_rom(rom_data, progress_callback)
        
        if success:
            print("\n✓ ROM written to ECU successfully")
        else:
            print("\n✗ Failed to write ROM to ECU")
    
    def do_read_dtcs(self, arg):
        """Read Diagnostic Trouble Codes"""
        if not self._check_connection():
            return
        
        print("Reading DTCs...")
        dtcs = self.ecu_comm.read_dtcs()
        
        if dtcs:
            print(f"\nFound {len(dtcs)} DTC(s):")
            for dtc in dtcs:
                print(f"  {dtc['code']}: {dtc['description']} ({dtc['status']})")
        else:
            print("No DTCs found")
    
    def do_clear_dtcs(self, arg):
        """Clear Diagnostic Trouble Codes"""
        if not self._check_connection():
            return
        
        if self.ecu_comm.clear_dtcs():
            print("✓ DTCs cleared successfully")
        else:
            print("✗ Failed to clear DTCs")
    
    def do_live_data(self, arg):
        """Read live data parameters: live_data [interval=2]"""
        if not self._check_connection():
            return
        
        interval = float(arg.strip() or "2")
        pids = [0x0C, 0x0D, 0x11, 0x05, 0x0F, 0x223365, 0x223456]
        
        print("Reading live data (Ctrl+C to stop)...")
        print("RPM\tSpeed\tThrottle\tBoost\tKnock\tCoolant\tIntake")
        print("-" * 60)
        
        try:
            while True:
                data = {}
                for pid in pids:
                    value = self.ecu_comm.read_live_data(pid)
                    pid_name = self._get_pid_name(pid)
                    data[pid_name] = value
                
                # Format output
                rpm = data.get('rpm', 0)
                speed = data.get('speed', 0)
                throttle = data.get('throttle', 0)
                boost = data.get('boost', 0)
                knock = data.get('knock_correction', 0)
                coolant = data.get('coolant_temp', 0)
                intake = data.get('intake_temp', 0)
                
                print(f"{rpm:.0f}\t{speed:.0f}\t{throttle:.1f}%\t{boost:.1f}\t{knock:.1f}\t{coolant:.0f}°C\t{intake:.0f}°C", end='\r')
                
                import time
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nLive data stopped")
    
    def _get_pid_name(self, pid: int) -> str:
        """Get PID name for display"""
        pid_names = {
            0x0C: 'rpm', 0x0D: 'speed', 0x11: 'throttle',
            0x05: 'coolant_temp', 0x0F: 'intake_temp',
            0x223365: 'boost', 0x223456: 'knock_correction'
        }
        return pid_names.get(pid, 'unknown')
    
    def do_calculate_power(self, arg):
        """Calculate power gains: calculate_power <mod1,mod2,...>"""
        modifications = [mod.strip() for mod in arg.split(',')] if arg else []
        
        results = self.vehicle.calculate_safe_power_gains(modifications)
        
        print("\nPOWER CALCULATION RESULTS")
        print("="*40)
        print(f"Base Power: {self.vehicle.ecu_calibrations['stock_power']['horsepower']} HP")
        print(f"Estimated Power: {results['estimated_horsepower']} HP")
        print(f"Power Gain: +{results['horsepower_gain']} HP ({results['total_gain_percent']}%)")
        print(f"Estimated Torque: {results['estimated_torque']} lb-ft")
        print(f"Modifications: {', '.join(results['modifications']) if results['modifications'] else 'None'}")
    
    def do_maintenance(self, arg):
        """Check maintenance schedule: maintenance <mileage>"""
        try:
            mileage = int(arg.strip())
            schedule = self.vehicle.get_maintenance_schedule(mileage)
            
            print(f"\nMAINTENANCE SCHEDULE - {mileage} miles")
            print("="*50)
            
            if schedule['next_services']:
                print("Next Services:")
                for service in schedule['next_services']:
                    print(f"  ✓ {service}")
            
            if schedule['critical_items']:
                print("\nCritical Items:")
                for item in schedule['critical_items']:
                    print(f"  ⚠ {item}")
            
            if schedule['recommendations']:
                print("\nRecommendations:")
                for rec in schedule['recommendations']:
                    print(f"  • {rec}")
                    
        except ValueError:
            print("Usage: maintenance <mileage>")
    
    def do_export_maps(self, arg):
        """Export all map definitions: export_maps [filename]"""
        filename = arg.strip() or "map_definitions.json"
        
        try:
            self.map_editor.map_manager.export_definitions(filename)
            print(f"✓ Map definitions exported to: {filename}")
        except Exception as e:
            print(f"✗ Failed to export maps: {e}")
    
    def do_quit(self, arg):
        """Exit VersaTuner"""
        if self.is_connected:
            self.ecu_comm.disconnect()
        print("Thank you for using VersaTuner!")
        return True
    
    def _check_connection(self) -> bool:
        """Check if connected to ECU"""
        if not self.is_connected:
            print("Not connected to ECU. Use 'connect' first.")
            return False
        return True
    
    # Aliases for common commands
    def do_exit(self, arg):
        """Exit VersaTuner"""
        return self.do_quit(arg)
    
    def do_help(self, arg):
        """Show help information"""
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show general help
            print("\nVERSATUNER CONSOLE COMMANDS")
            print("="*50)
            print("Connection:")
            print("  connect [interface]    - Connect to ECU")
            print("  disconnect             - Disconnect from ECU")
            print("  vehicle_info           - Show vehicle information")
            print("  unlock [level]         - Unlock ECU security")
            print("")
            print("ROM Operations:")
            print("  read_rom [file]        - Read ROM from ECU")
            print("  load_rom <file>        - Load ROM from file")
            print("  verify_rom             - Verify ROM integrity")
            print("  write_rom [file]       - Write ROM to ECU")
            print("")
            print("Tuning:")
            print("  list_maps [category]   - List available maps")
            print("  load_map <name>        - Load specific map")
            print("  modify_map x y value   - Modify map value")
            print("  global_adjust value    - Apply global adjustment")
            print("  create_tune stage      - Create performance tune")
            print("")
            print("Diagnostics:")
            print("  read_dtcs              - Read trouble codes")
            print("  clear_dtcs             - Clear trouble codes")
            print("  live_data [interval]   - Show live data")
            print("")
            print("Tools:")
            print("  calculate_power mods   - Calculate power gains")
            print("  maintenance mileage    - Check maintenance")
            print("  export_maps [file]     - Export map definitions")
            print("")
            print("Type 'help <command>' for detailed help")
            print("")

def main():
    """Main entry point for console interface"""
    console = TuningConsole()
    console.cmdloop()

if __name__ == "__main__":
    main()