#!/usr/bin/env python3
"""
Mazdaspeed 3 Cobb Access Port Reverse Engineering - Main Interface
Complete deployment-ready system for ECU tuning and diagnostics
"""

import sys
import time
import argparse
from .protocols.can_bus import MZRCANProtocol
from .ecu.mzr_ecu import MZRECU

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
        from .tuning.flash_manager import FlashManager
        
        flash_manager = FlashManager(ecu)
        
        # Read current table
        table_data = ecu.read_calibration_table(args.table)
        if table_data:
            print("[+] Table loaded successfully")
            
            # Example modification
            modified_data = bytearray(table_data)
            # Modify a few bytes as example
            for i in range(10, 20):
                modified_data[i] = int(modified_data[i] * 1.1) % 256
            
            # Write back to ECU
            if ecu.write_calibration_table(args.table, bytes(modified_data)):
                print("[+] Table modifications written to ECU")
            else:
                print("[-] Failed to write table to ECU")
        else:
            print("[-] Failed to load table")
    
    elif args.action == 'realtime':
        # Real-time tuning mode
        print("[*] Entering real-time tuning mode...")
        from .tuning.realtime_monitor import RealTimeMonitor
        
        monitor = RealTimeMonitor(ecu)
        monitor.start_monitoring()
        
        try:
            time.sleep(30)  # Monitor for 30 seconds
        except KeyboardInterrupt:
            print("\n[*] Stopping monitor...")
        finally:
            monitor.stop_monitoring()
    
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
