#!/usr/bin/env python3
"""
Logging Utility - Professional logging system for VersaTuner
Provides comprehensive logging with file rotation and different log levels
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

class VersaLogger:
    """
    VersaTuner logging class with professional formatting and multiple handlers
    """
    
    def __init__(self, name: str, log_level: int = logging.INFO, 
                 log_to_file: bool = True, max_file_size: int = 10*1024*1024):
        """
        Initialize logger
        
        Args:
            name: Logger name (typically __name__)
            log_level: Minimum log level
            log_to_file: Whether to log to file
            max_file_size: Maximum log file size in bytes
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers(log_level, log_to_file, max_file_size)
    
    def _setup_handlers(self, log_level: int, log_to_file: bool, max_file_size: int):
        """Setup console and file handlers"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (with rotation)
        if log_to_file:
            log_dir = self._get_log_directory()
            log_file = os.path.join(log_dir, 'versatuner.log')
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=5
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _get_log_directory(self) -> str:
        """Get log directory, create if it doesn't exist"""
        log_dir = os.path.join(os.path.expanduser('~'), '.versatuner', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    
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
        """Log exception with stack trace"""
        self.logger.exception(message)

# Global application logger
def setup_application_logger(level: int = logging.INFO) -> VersaLogger:
    """
    Setup application-wide logger
    
    Args:
        level: Logging level
        
    Returns:
        VersaLogger instance
    """
    return VersaLogger('versatuner', level)
