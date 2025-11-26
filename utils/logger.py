#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3 LOGGER UTILITY
Centralized logging system for all MUTS components
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional
import colorama
from colorama import Fore, Back, Style

# Initialize colorama
colorama.init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE + Style.BRIGHT,
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

class VersaLogger:
    """
    VERSATUNER COMPATIBLE LOGGER
    Provides logging functionality compatible with VersaTuner API
    """
    
    def __init__(self, name: str = "versa", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self._setup_logger(level)
    
    def _setup_logger(self, level: str):
        """Setup logger with console and file handlers"""
        try:
            # Clear existing handlers
            self.logger.handlers.clear()
            
            # Set log level
            log_level = getattr(logging, level.upper(), logging.INFO)
            self.logger.setLevel(log_level)
            
            # Console handler with colors
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            
            # File handler
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, f"muts_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Prevent duplicate logs
            self.logger.propagate = False
            
        except Exception as e:
            print(f"Failed to setup logger: {e}")
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    def exception(self, message: str):
        """Log exception with traceback"""
        self.logger.exception(message)

# Global logger instance
versa_logger = VersaLogger()

def get_logger(name: str = "muts") -> VersaLogger:
    """Get logger instance"""
    return VersaLogger(name)
