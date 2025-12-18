#!/usr/bin/env python3
"""
VersaTuner Main Application Entry Point
Complete reverse engineering of VersaTuner for Mazdaspeed 3 2011
"""

import sys
import os
import argparse
import logging
from .gui.main_interface import VersaTunerGUI
from .interfaces.tuning_console import TuningConsole
from .utils.logger import setup_application_logger

def main():
    """
    Main entry point for VersaTuner application
    Supports both GUI and console interfaces
    """
    parser = argparse.ArgumentParser(description='VersaTuner - Mazdaspeed 3 Tuning Software')
    parser.add_argument('--gui', action='store_true', help='Launch GUI interface')
    parser.add_argument('--console', action='store_true', help='Launch console interface')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    logger = setup_application_logger(log_level)
    
    logger.info("Starting VersaTuner for Mazdaspeed 3 2011")
    
    try:
        if args.console:
            # Launch console interface
            console = TuningConsole()
            console.run()
        else:
            # Launch GUI interface (default)
            app = VersaTunerGUI()
            app.run()
            
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.critical(f"Application crashed: {e}")
        sys.exit(1)
    
    logger.info("VersaTuner application closed")

if __name__ == "__main__":
    main()
