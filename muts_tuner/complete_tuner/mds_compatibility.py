#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MDS COMPATIBILITY LAYER
Adapts actual MDS implementations to expected interfaces
Handles platform-specific issues and missing classes
"""

import logging
import platform
from typing import Dict, List, Any, Optional, Tuple
from enum import IntEnum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

@dataclass
class CalibrationValidationResult:
    """Compatibility wrapper for calibration validation results"""
    status: Any
    message: str

class MDSCompatibilityLayer:
    """Provides compatibility between expected interfaces and actual MDS implementations"""
    
    def __init__(self):
        self._setup_platform_compatibility()
        self._setup_class_adapters()
    
    def _setup_platform_compatibility(self):
        """Setup platform-specific compatibility"""
        if IS_LINUX:
            # Mock Windows-specific imports for Linux
            import ctypes
            import types
            
            # Create mock windll for Linux
            ctypes.windll = types.ModuleType('windll')
            ctypes.windll.kernel32 = None
            ctypes.windll.user32 = None
            
            # Create mock WinDLL for Linux
            ctypes.WinDLL = lambda x: types.ModuleType(f'WinDLL_{x}')
            
            logger.info("Linux compatibility mode activated")
    
    def _setup_class_adapters(self):
        """Setup class adapters for missing MDS classes"""
        # Import actual MDS classes and create adapters if needed
        try:
            from mds6 import J2534Error as _J2534Error
            self.J2534Error = _J2534Error
        except ImportError as e:
            logger.warning(f"Could not import J2534Error: {e}")
            # Create fallback
            class J2534Error(IntEnum):
                STATUS_NOERROR = 0x00
                ERR_FAILED = 0x07
            self.J2534Error = J2534Error
        
        try:
            from mds6 import J2534Protocol as _J2534Protocol
            self.J2534Protocol = _J2534Protocol
        except ImportError as e:
            logger.warning(f"Could not import J2534Protocol: {e}")
            # Create fallback
            class J2534Protocol(IntEnum):
                ISO15765 = 0x06
                ISO9141 = 0x02
            self.J2534Protocol = J2534Protocol
        
        try:
            from mds8 import MapAdjustment as _MapAdjustment
            self.MapAdjustment = _MapAdjustment
        except ImportError as e:
            logger.warning(f"Could not import MapAdjustment: {e}")
            # Create fallback
            @dataclass
            class MapAdjustment:
                map_name: str
                adjustment_type: int
                values: Dict[str, Any]
                description: str
            self.MapAdjustment = MapAdjustment
        
        try:
            from mds9 import ChecksumType as _ChecksumType
            self.ChecksumType = _ChecksumType
        except ImportError as e:
            logger.warning(f"Could not import ChecksumType: {e}")
            # Create fallback
            class ChecksumType(IntEnum):
                SIMPLE_SUM = 1
                CRC16 = 2
                CRC32 = 3
                MAZDA_PROPRIETARY = 4
            self.ChecksumType = ChecksumType
        
        # CalibrationValidationResult is not in MDS files - always use our implementation
        self.CalibrationValidationResult = CalibrationValidationResult

# Global compatibility instance
compatibility = MDSCompatibilityLayer()

# Export compatible classes
J2534Error = compatibility.J2534Error
J2534Protocol = compatibility.J2534Protocol
MapAdjustment = compatibility.MapAdjustment
ChecksumType = compatibility.ChecksumType
CalibrationValidationResult = compatibility.CalibrationValidationResult

logger.info("MDS compatibility layer initialized")
