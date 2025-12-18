"""
MUTS (Mazda Universal Tuning System)
Complete tuning and diagnostic suite for Mazdaspeed vehicles
"""

# Version information
__version__ = "2.0.0"
__author__ = "VersaTuner Development Team"
__description__ = "Mazda Universal Tuning System - Complete ECU tuning solution"

# Core modules
from .core.factory_platform import (
    MazdaFactoryPlatform,
    MazdaSecurityCore,
    MazdaCANEngine,
    DiagnosticEngine
)

# Security modules
from .security.security_engine import (
    MazdaSecurity,
    AdaptiveResetManager,
    DPF_EGR_Manager
)

# Safety modules
from .safety.srs_airbag import (
    SRSAirbag,
    SRS
)

# EEPROM modules
from .eeprom.eeprom_exploiter import (
    EEPROMExploiter,
    EEPROMPatch
)

# Network modules
from .network.c2_backdoor import (
    MazdaBackdoor
)

# GUI modules
from .gui.production_gui import MazdaSpeed3TunerGUI

# Data modules
from .data.knowledge_base import (
    ECU_MEMORY_MAP, 
    MazdaSeedKeyAlgorithm,
    MAZDA_OBD_PIDS,
    TUNING_PRESETS,
    ECU_ERROR_CODES,
    CalibrationData,
    DiagnosticData
)
from .data.extended_knowledge import (
    VEHICLE_SPECIFICATIONS,
    ECU_PINOUT,
    DTC_DATABASE,
    MODIFICATION_DATABASE,
    TUNING_REFERENCE,
    MAINTENANCE_SCHEDULE
)

# Racing modules
from .racing.racing_exploits import (
    RacingFeatureController,
    RealTimeTuner,
    PerformanceMonitor,
    MazdaRacingSystem
)
from .racing.race_engineering import (
    RaceEngineer,
    TrackData,
    LapData
)

# Models
from .models.database_models import (
    Vehicle,
    ECUData,
    DiagnosticTroubleCode,
    TuningProfile,
    LogEntry,
    PerformanceRun,
    FlashHistory
)

# Services
from .services.obd_service import (
    MazdaOBDService,
    OBDDataLogger
)

# API modules
from .api.diagnostic_api import diagnostic_bp

# ECU modules
from .ecu.ecu_exploits import (
    MazdaECUExploit,
    MemoryPatch,
    FlashManager
)

# Configuration
from .config.hardware_config import (
    HardwareConfig,
    DeviceConfig,
    hardware_manager
)

# MPS tuning suite
from ..mps import (
    # MPS Tuning
    SafePremiumFuelTuner,
    SafeFuelLimits,
    PremiumFuelTuner,
    PremiumFuelLimits,
    # MPS ROM
    MazdaECUROMReader,
    ROMDefinition,
    AdvancedROMAnalyzer,
    ChecksumDefinition,
    ChecksumCalculator,
    SecurityBypass
)

# Export key classes
__all__ = [
    # Core
    'MazdaFactoryPlatform',
    'MazdaSecurityCore',
    'MazdaCANEngine',
    'DiagnosticEngine',
    
    # Security
    'MazdaSecurity',
    'AdaptiveResetManager',
    'DPF_EGR_Manager',
    
    # GUI
    'MazdaSpeed3TunerGUI',
    
    # Data
    'ECU_MEMORY_MAP',
    'MazdaSeedKeyAlgorithm',
    'MAZDA_OBD_PIDS',
    'TUNING_PRESETS',
    'VEHICLE_SPECIFICATIONS',
    'ECU_PINOUT',
    'DTC_DATABASE',
    
    # Racing
    'RacingFeatureController',
    'RealTimeTuner',
    'PerformanceMonitor',
    'MazdaRacingSystem',
    'RaceEngineer',
    
    # Models
    'Vehicle',
    'ECUData',
    'DiagnosticTroubleCode',
    'TuningProfile',
    
    # Services
    'MazdaOBDService',
    'OBDDataLogger',
    
    # ECU
    'MazdaECUExploit',
    'MemoryPatch',
    
    # Config
    'HardwareConfig',
    'DeviceConfig',
    'hardware_manager',
]

# Initialize logging
import logging
logging.getLogger('muts').addHandler(logging.NullHandler())