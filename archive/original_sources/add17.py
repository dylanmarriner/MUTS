from core.ecu_communication import ECUCommunicator, ECUResponse, ECUState
from core.safety_validator import get_safety_validator
from utils.logger import get_logger
#!/usr/bin/env python3
"""
MAZDASPEED 3 TUNING PACKAGE
Complete tuning and diagnostic system for 2011 Mazdaspeed 3
"""

__version__ = "1.0.0"
__author__ = "Mazda Performance Engineering"
__description__ = "Complete tuning system for Mazdaspeed 3 2011 MZR 2.3L DISI Turbo"

# Package imports
from .database.ecu_database import Mazdaspeed3Database, ECUCalibration
from .services.ai_tuner import AITuningSystem
from .services.physics_engine import TurbochargerPhysics, EngineThermodynamics, PerformanceCalculator
from .services.dealer_service import MazdaDealerSecurity
from .services.performance_features import AdvancedPerformanceManager, AntiLagSystem, TwoStepRevLimiter, LaunchControlSystem
from .models.engine_models import IdealGasPhysics, TurbochargerDynamics, EngineCycleAnalysis
from .models.turbo_models import K04Turbocharger, TurboSystemManager
from .utils.calculations import AdvancedCalculations, TuningSecrets

# Export main classes
__all__ = [
    'Mazdaspeed3Database',
    'ECUCalibration', 
    'AITuningSystem',
    'TurbochargerPhysics',
    'EngineThermodynamics',
    'PerformanceCalculator',
    'MazdaDealerSecurity',
    'AdvancedPerformanceManager',
    'AntiLagSystem',
    'TwoStepRevLimiter', 
    'LaunchControlSystem',
    'IdealGasPhysics',
    'TurbochargerDynamics',
    'EngineCycleAnalysis',
    'K04Turbocharger',
    'TurboSystemManager',
    'AdvancedCalculations',
    'TuningSecrets'
]