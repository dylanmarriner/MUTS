#!/usr/bin/env python3
"""
Mazdaspeed 3 Cobb Access Port Reverse Engineering - Main Interface
Complete deployment-ready system for ECU tuning and diagnostics
"""

import sys
import time
import argparse
from protocols.can_bus import MZRCANProtocol
from ecu.mzr_disaster import MZRECU
from tuning.map_editor import MapEditor3D, RealTimeTuner

def main():
    parser = argparse.ArgumentParser(description='Mazdaspeed 3 Cobb AP Reverse Engineering Suite')
    parser.add_argument('--interface', default='vcan0', help='CAN interface name')
    parser.add_argument('--action', choices=['scan', 'dump', 'tune', 'realtime', 'flash'], required=True)
    parser.add_argument('--table', help='Calibration table name')
    parser.add_argument('--file', help='Calibration file for flashing')
    
    args = parser.parse_args()
    
    # Initialize CAN protocol
    print("[*] Initializing CAN protocol...")
    can_protocol = MZRCANProtocol(channel=args.interface)
    
    # Initialize ECU interface
    ecu = MZRECU(can_protocol)
    
    # Attempt ECU unlock
    print("[*] Unlocking ECU security...")
    if can_protocol.unlock_ecu(can_protocol.TUNING_LEVEL):
        print("[+] ECU unlocked successfully")
    else:
        print("[-] ECU unlock failed")
        return
    
    if args.action == 'scan':
        # Read ECU identification
        print("[*] Scanning ECU identification...")
        ident = can_protocol.read_ecu_identification()
        for key, value in ident.items():
            print(f"    {key}: {value}")
    
    elif args.action == 'dump':
        # Dump calibration data
        print("[*] Dumping calibration tables...")
        calibration_dump = ecu.dump_full_calibration()
        print(f"[+] Dumped {len(calibration_dump)} tables")
        
        # Save to files
        for table_name, data in calibration_dump.items():
            filename = f"{table_name}.bin"
            with open(filename, 'wb') as f:
                f.write(data)
            print(f"    Saved {filename}")
    
    elif args.action == 'tune' and args.table:
        # Table editing mode
        print(f"[*] Loading table: {args.table}")
        editor = MapEditor3D(ecu)
        
        if editor.load_table(args.table):
            print("[+] Table loaded successfully")
            editor.visualize_table_3d()
            
            # Example modification (would be interactive in real implementation)
            editor.modify_cell(5, 5, 1.1)  # Increase fuel at specific cell
            
            if editor.save_table_to_ecu():
                print("[+] Table modifications written to ECU")
            else:
                print("[-] Failed to write table to ECU")
        else:
            print("[-] Failed to load table")
    
    elif args.action == 'realtime':
        # Real-time tuning mode
        print("[*] Entering real-time tuning mode...")
        tuner = RealTimeTuner(ecu)
        
        # Monitor real-time parameters
        try:
            while True:
                rpm = ecu.read_realtime_parameter('ENGINE_RPM')
                boost = ecu.read_realtime_parameter('MANIFOLD_PRESSURE')
                timing = ecu.read_realtime_parameter('IGNITION_TIMING')
                
                print(f"RPM: {rpm:.0f} | Boost: {boost:.1f} psi | Timing: {timing:.1f}°")
                
                # Example: Add timing if not knocking
                knock = ecu.read_realtime_parameter('KNOCK_RETARD')
                if knock < 1.0 and rpm > 3000:
                    tuner.adjust_parameter('IGNITION_TIMING', 0.5)
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n[*] Resetting adjustments...")
            tuner.reset_adjustments()
    
    elif args.action == 'flash' and args.file:
        # Flash calibration file
        print(f"[*] Flashing calibration file: {args.file}")
        if ecu.flash_calibration_file(args.file):
            print("[+] Calibration flashed successfully")
        else:
            print("[-] Flash failed")
    
    print("[*] Operation completed")

if __name__ == "__main__":
    main()