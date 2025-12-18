#!/usr/bin/env python3
"""
Console Interface - Command-line interface for VersaTuner
Provides full functionality without GUI for advanced users and scripting
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
from ..tuning.map_definitions import MapDefinitionManager
from ..vehicle.mazdaspeed3_2011 import Mazdaspeed32011
from ..utils.logger import VersaLogger

class TuningConsole(cmd.Cmd):
    """
    VersaTuner Console Interface - Full command-line functionality
    Provides complete tuning capabilities without GUI dependencies
    """
    
    intro = 'Welcome to VersaTuner Console. Type help or ? to list commands.\n'
    prompt = 'versatuner> '
    
    def __init__(self):
        super().__init__()
        self.logger = VersaLogger(__name__)
        
        # Initialize core components
        self.ecu_comm = ECUCommunicator()
        self.security_mgr = SecurityManager(self.ecu_comm)
        self.rom_ops = ROMOperations(self.ecu_comm)
        self.map_editor = MapEditor(self.rom_ops)
        self.map_manager = MapDefinitionManager()
        self.vehicle = Mazdaspeed32011()
        
        # Application state
        self.is_connected = False
        self.rom_data = None
        self.current_map = None
        
        self.logger.info("VersaTuner Console initialized")
    
    def do_connect(self, arg):
        """
        Connect to ECU
        Usage: connect [interface=can0]
        """
        args = arg.split()
        interface = args[0] if args else 'can0'
        
        try:
            self.ecu_comm.interface = interface
            if self.ecu_comm.connect():
                self.is_connected = True
                print(f"Connected to ECU on {interface}")
                self._update_vehicle_info()
            else:
                print("Failed to connect to ECU")
        except Exception as e:
            print(f"Connection error: {e}")
    
    def do_disconnect(self, arg):
        """
        Disconnect from ECU
        Usage: disconnect
        """
        if self.is_connected:
            self.ecu_comm.disconnect()
            self.is_connected = False
            print("Disconnected from ECU")
        else:
            print("Not connected to ECU")
    
    def _update_vehicle_info(self):
        """Update and display vehicle information"""
        if not self.is_connected:
            return
            
        info = self.rom_ops.read_ecu_info()
        print("\n=== Vehicle Information ===")
        print(f"VIN: {info.get('vin', 'Unknown')}")
        print(f"ECU Part: {info.get('ecu_part_number', 'Unknown')}")
        print(f"Calibration: {info.get('calibration_id', 'Unknown')}")
        print(f"Software: {info.get('software_version', 'Unknown')}")
    
    def do_unlock(self, arg):
        """
        Unlock ECU security access
        Usage: unlock [level=3]
        """
        if not self.is_connected:
            print("Not connected to ECU")
            return
            
        level = int(arg) if arg else 3
        
        try:
            if self.security_mgr.unlock_ecu(level):
                status = self.security_mgr.check_security_status()
                print(f"Security unlocked: Level {status['current_level']}")
            else:
                print("Failed to unlock ECU security")
        except Exception as e:
            print(f"Unlock error: {e}")
    
    def do_read_rom(self, arg):
        """
        Read complete ROM from ECU
        Usage: read_rom [output_file]
        """
        if not self.is_connected:
            print("Not connected to ECU")
            return
            
        try:
            print("Reading ROM from ECU...")
            
            def progress_callback(current, total):
                percent = (current / total) * 100
                print(f"Progress: {percent:.1f}%", end='\r')
            
            self.rom_data = self.rom_ops.read_complete_rom(progress_callback)
            
            if self.rom_data:
                print(f"\nROM read complete: {len(self.rom_data)} bytes")
                
                # Save to file if specified
                if arg:
                    with open(arg, 'wb') as f:
                        f.write(self.rom_data)
                    print(f"ROM saved to: {arg}")
            else:
                print("Failed to read ROM")
                
        except Exception as e:
            print(f"ROM read error: {e}")
    
    def do_save_rom(self, arg):
        """
        Save current ROM to file
        Usage: save_rom <filename>
        """
        if not self.rom_data:
            print("No ROM data loaded")
            return
            
        if not arg:
            print("Please specify filename")
            return
            
        try:
            with open(arg, 'wb') as f:
                f.write(self.rom_data)
            print(f"ROM saved to: {arg}")
        except Exception as e:
            print(f"Save error: {e}")
    
    def do_load_rom(self, arg):
        """
        Load ROM from file
        Usage: load_rom <filename>
        """
        if not arg:
            print("Please specify filename")
            return
            
        try:
            with open(arg, 'rb') as f:
                self.rom_data = f.read()
            print(f"ROM loaded: {len(self.rom_data)} bytes")
        except Exception as e:
            print(f"Load error: {e}")
    
    def do_list_maps(self, arg):
        """
        List available tuning maps
        Usage: list_maps [category]
        """
        args = arg.split()
        category = args[0] if args else None
        
        if category:
            maps = self.map_manager.get_maps_by_category(category)
            print(f"\n=== Maps in category: {category} ===")
        else:
            categories = self.map_manager.get_all_categories()
            print("\n=== All Map Categories ===")
            for cat in categories:
                maps = self.map_manager.get_maps_by_category(cat)
                print(f"{cat}: {len(maps)} maps")
            return
        
        for map_def in maps:
            print(f"{map_def.name:30} {map_def.type:10} {map_def.description}")
    
    def do_load_map(self, arg):
        """
        Load specific map from ROM
        Usage: load_map <map_name>
        """
        if not self.rom_data:
            print("No ROM data loaded")
            return
            
        if not arg:
            print("Please specify map name")
            return
            
        try:
            map_data = self.map_editor.load_map_from_rom(arg, self.rom_data)
            if map_data:
                self.current_map = map_data
                print(f"Map loaded: {arg}")
                self._display_map_info(map_data)
            else:
                print(f"Failed to load map: {arg}")
        except Exception as e:
            print(f"Map load error: {e}")
    
    def _display_map_info(self, map_data):
        """Display map information"""
        print(f"\n=== Map Information ===")
        print(f"Name: {map_data.definition.name}")
        print(f"Type: {map_data.definition.type}")
        print(f"Address: 0x{map_data.definition.address:06X}")
        print(f"Size: {map_data.definition.size} bytes")
        print(f"Units: {map_data.definition.units}")
        print(f"Range: {map_data.definition.min_value} to {map_data.definition.max_value}")
        
        # Display sample data
        print(f"\nSample Data:")
        if len(map_data.data.shape) == 2:
            # 2D map - show corner values
            rows, cols = map_data.data.shape
            print(f"Shape: {rows}x{cols}")
            print("Top-left corner values:")
            for i in range(min(3, rows)):
                for j in range(min(3, cols)):
                    print(f"  [{i},{j}]: {map_data.data[i,j]:.2f}")
        else:
            # 1D or single value
            print(f"Values: {map_data.data}")
    
    def do_show_map(self, arg):
        """
        Display current map data
        Usage: show_map
        """
        if not self.current_map:
            print("No map loaded")
            return
            
        self._display_map_data(self.current_map)
    
    def _display_map_data(self, map_data):
        """Display complete map data"""
        if len(map_data.data.shape) == 2:
            # 2D map - display as table
            rows, cols = map_data.data.shape
            print(f"\nMap Data ({rows}x{cols}):")
            
            # Header row
            header = "      "
            for j in range(cols):
                header += f"{j:8}"
            print(header)
            print("      " + "-" * (cols * 8))
            
            # Data rows
            for i in range(rows):
                row_str = f"{i:3} | "
                for j in range(cols):
                    row_str += f"{map_data.data[i,j]:7.2f} "
                print(row_str)
                
        elif len(map_data.data.shape) == 1:
            # 1D map
            print(f"\n1D Map Data:")
            for i, value in enumerate(map_data.data):
                print(f"  [{i}]: {value:.2f}")
        else:
            # Single value
            print(f"Value: {map_data.data[0]:.2f}")
    
    def do_set_value(self, arg):
        """
        Set map value at specific coordinates
        Usage: set_value <x> <y> <value>
        For 2D maps: set_value <row> <col> <value>
        For 1D maps: set_value <index> 0 <value>
        """
        if not self.current_map:
            print("No map loaded")
            return
            
        args = arg.split()
        if len(args) != 3:
            print("Usage: set_value <x> <y> <value>")
            return
            
        try:
            x = int(args[0])
            y = int(args[1])
            value = float(args[2])
            
            if self.map_editor.modify_map_value(self.current_map.definition.name, x, y, value):
                print(f"Value set: [{x},{y}] = {value}")
            else:
                print("Failed to set value")
                
        except Exception as e:
            print(f"Set value error: {e}")
    
    def do_adjust_map(self, arg):
        """
        Apply global adjustment to current map
        Usage: adjust_map <adjustment_value>
        """
        if not self.current_map:
            print("No map loaded")
            return
            
        if not arg:
            print("Please specify adjustment value")
            return
            
        try:
            adjustment = float(arg)
            map_name = self.current_map.definition.name
            
            if self.map_editor.apply_global_adjustment(map_name, adjustment):
                print(f"Applied global adjustment: {adjustment}")
            else:
                print("Failed to apply adjustment")
                
        except Exception as e:
            print(f"Adjustment error: {e}")
    
    def do_write_rom(self, arg):
        """
        Write modified ROM to ECU
        Usage: write_rom
        """
        if not self.rom_data:
            print("No ROM data loaded")
            return
            
        if not self.is_connected:
            print("Not connected to ECU")
            return
            
        try:
            # Generate patched ROM with all modifications
            patched_rom = self.map_editor.generate_patch_rom(self.rom_data)
            patched_rom = self.rom_ops.patch_checksums(patched_rom)
            
            print("Writing ROM to ECU...")
            
            def progress_callback(current, total):
                percent = (current / total) * 100
                print(f"Progress: {percent:.1f}%", end='\r')
            
            if self.rom_ops.write_complete_rom(patched_rom, progress_callback):
                print("\nROM written successfully")
                self.rom_data = patched_rom  # Update current ROM
            else:
                print("\nFailed to write ROM")
                
        except Exception as e:
            print(f"Write error: {e}")
    
    def do_read_dtcs(self, arg):
        """
        Read Diagnostic Trouble Codes
        Usage: read_dtcs
        """
        if not self.is_connected:
            print("Not connected to ECU")
            return
            
        try:
            dtcs = self.ecu_comm.read_dtcs()
            
            if dtcs:
                print("\n=== Diagnostic Trouble Codes ===")
                for dtc in dtcs:
                    print(f"{dtc['code']}: {dtc['description']} ({dtc['status']})")
            else:
                print("No DTCs found")
                
        except Exception as e:
            print(f"DTC read error: {e}")
    
    def do_clear_dtcs(self, arg):
        """
        Clear Diagnostic Trouble Codes
        Usage: clear_dtcs
        """
        if not self.is_connected:
            print("Not connected to ECU")
            return
            
        try:
            if self.ecu_comm.clear_dtcs():
                print("DTCs cleared successfully")
            else:
                print("Failed to clear DTCs")
        except Exception as e:
            print(f"DTC clear error: {e}")
    
    def do_live_data(self, arg):
        """
        Read live data parameters
        Usage: live_data [pid1 pid2 ...]
        """
        if not self.is_connected:
            print("Not connected to ECU")
            return
            
        # Default PIDs to read
        default_pids = [0x0C, 0x0D, 0x11, 0x05, 0x0F, 0x223365]
        
        try:
            if arg:
                # Parse custom PIDs
                pids = [int(pid, 0) for pid in arg.split()]
            else:
                pids = default_pids
            
            print("\n=== Live Data ===")
            for pid in pids:
                value = self.ecu_comm.read_live_data(pid)
                pid_name = self._get_pid_name(pid)
                print(f"{pid_name:20} {value}")
                
        except Exception as e:
            print(f"Live data error: {e}")
    
    def _get_pid_name(self, pid: int) -> str:
        """Get human-readable name for PID"""
        pid_names = {
            0x0C: 'Engine RPM',
            0x0D: 'Vehicle Speed',
            0x11: 'Throttle Position',
            0x05: 'Coolant Temp',
            0x0F: 'Intake Air Temp',
            0x223365: 'Boost Pressure',
            0x223456: 'Knock Correction'
        }
        return pid_names.get(pid, f'PID_{pid:04X}')
    
    def do_create_tune(self, arg):
        """
        Create performance tune
        Usage: create_tune <power_gain>
        """
        if not self.rom_data:
            print("No ROM data loaded")
            return
            
        if not arg:
            print("Please specify power gain (HP)")
            return
            
        try:
            power_gain = int(arg)
            tuned_rom = self.map_editor.create_performance_tune(self.rom_data, power_gain)
            
            if tuned_rom:
                self.rom_data = tuned_rom
                print(f"Performance tune created: +{power_gain}HP")
                
                # Show tune recommendations
                recommendations = self.vehicle.get_recommended_tunes(power_gain)
                print(f"\nTune: {recommendations['name']}")
                print(f"Description: {recommendations['description']}")
                print(f"Required mods: {', '.join(recommendations['required_mods'])}")
            else:
                print("Failed to create tune")
                
        except Exception as e:
            print(f"Tune creation error: {e}")
    
    def do_vehicle_info(self, arg):
        """
        Display vehicle information and specifications
        Usage: vehicle_info
        """
        info = self.vehicle.get_vehicle_info()
        
        print("\n=== Vehicle Specifications ===")
        print(f"Model: {info['model']} {info['year']}")
        print(f"Engine: {info['engine_code']}")
        print(f"Transmission: {info['transmission']}")
        print(f"Drivetrain: {info['drivetrain']}")
        
        print(f"\nEngine Specs:")
        specs = info['engine_specs']
        print(f"  Displacement: {specs['displacement']}L")
        print(f"  Configuration: {specs['configuration']}")
        print(f"  Aspiration: {specs['aspiration']}")
        print(f"  Compression: {specs['compression_ratio']}:1")
        print(f"  Redline: {specs['redline']} RPM")
        
        print(f"\nPerformance Limits:")
        limits = info['performance_limits']
        print(f"  Max Boost: {limits['max_boost']} PSI")
        print(f"  Max Timing: {limits['max_timing']}°")
        print(f"  Min AFR: {limits['min_afr']}:1")
        print(f"  Max RPM: {limits['max_rpm']}")
    
    def do_verify_rom(self, arg):
        """
        Verify ROM integrity and checksums
        Usage: verify_rom
        """
        if not self.rom_data:
            print("No ROM data loaded")
            return
            
        try:
            results = self.rom_ops.verify_rom_integrity(self.rom_data)
            
            print("\n=== ROM Verification ===")
            print(f"Overall Valid: {results['overall_valid']}")
            
            print("\nChecksums:")
            for checksum_name, valid in results['checksums'].items():
                status = "PASS" if valid else "FAIL"
                print(f"  {checksum_name}: {status}")
            
            if results['errors']:
                print("\nErrors:")
                for error in results['errors']:
                    print(f"  {error}")
                    
        except Exception as e:
            print(f"Verification error: {e}")
    
    def do_quit(self, arg):
        """
        Exit VersaTuner Console
        Usage: quit
        """
        if self.is_connected:
            self.ecu_comm.disconnect()
        print("Goodbye!")
        return True
    
    def do_exit(self, arg):
        """Exit VersaTuner Console"""
        return self.do_quit(arg)
    
    def emptyline(self):
        """Do nothing on empty line"""
        pass
    
    def default(self, line):
        """Handle unknown commands"""
        print(f"Unknown command: {line}")
        print("Type 'help' for available commands")

def main():
    """Main entry point for console interface"""
    console = TuningConsole()
    console.cmdloop()

if __name__ == "__main__":
    main()