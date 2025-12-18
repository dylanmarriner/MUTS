#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MUTS Main Launcher
Sets up Python path and launches the main application
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main launcher function"""
    try:
        logger.info("Starting MUTS - Mazda Universal Tuning Suite")
        
        # Import and launch GUI
        from gui.main_window import main as gui_main
        gui_main()
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"Failed to import required modules: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install python-can PyQt5 colorama")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
