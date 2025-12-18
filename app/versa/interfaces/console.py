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
                print(f"ECU unlocked to level {level}")
            else:
                print("Failed to unlock ECU")
        except Exception as e:
            print(f"Unlock error: {e}")
    
    def do_read_rom(self, arg):
        """
        Read ECU ROM
        Usage: read_rom [filename]
        """
        if not self.is_connected:
            print("Not connected to ECU")
            return
            
        filename = arg.strip() or "rom.bin"
        
        try:
            # Unlock ECU first
            if not self.security_mgr.unlock_ecu():
                print("Failed to unlock ECU")
                return
            
            print("Reading ROM...")
            rom_data = self.rom_ops.read_complete_rom()
            
            if rom_data:
                with open(filename, 'wb') as f:
                    f.write(rom_data)
                print(f"ROM saved to {filename}")
                self.rom_data = rom_data
            else:
                print("Failed to read ROM")
        except Exception as e:
            print(f"ROM read error: {e}")
    
    def do_list_maps(self, arg):
        """
        List available tuning maps
        Usage: list_maps
        """
        maps = self.map_manager.get_all_maps()
        
        print("\nAvailable Maps:")
        print("-" * 40)
        for name, map_def in maps.items():
            print(f"{name}: {map_def.description}")
    
    def do_quit(self, arg):
        """Exit the console"""
        if self.is_connected:
            self.do_disconnect("")
        print("Goodbye!")
        return True
    
    def run(self):
        """Run the console interface"""
        try:
            self.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")
            self.do_quit("")
