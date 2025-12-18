#!/usr/bin/env python3
"""
MDS Package - Mazda IDS/M-MDS Integration
Complete implementation of Mazda diagnostic and programming software
"""

from .core.ids_software import MazdaIDS
from .protocols.diagnostic_protocols import MazdaProtocol, DiagnosticSession
from .security.security_algorithms import MazdaSecurityAccess
from .diagnostics.diagnostic_database import DiagnosticDatabase
from .calibration.calibration_manager import CalibrationManager
from .programming.programming_routines import ProgrammingManager
from .interface.j2534_interface import J2534Interface
from .utils.checksum_routines import ChecksumCalculator
from .data.data_structures import MDSDataStructures
from .vehicle.vehicle_specific import VehicleSpecific
from .advanced.advanced_features import AdvancedFeatures

__version__ = "1.0.0"
__all__ = [
    'MazdaIDS',
    'MazdaProtocol',
    'DiagnosticSession',
    'MazdaSecurityAccess',
    'DiagnosticDatabase',
    'CalibrationManager',
    'ProgrammingManager',
    'J2534Interface',
    'ChecksumCalculator',
    'MDSDataStructures',
    'VehicleSpecific',
    'AdvancedFeatures'
]
