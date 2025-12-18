"""
MUTS - Mazdaspeed 3 Universal Tuning System
Complete ECU tuning and performance optimization platform
"""

__version__ = "1.0.0"
__author__ = "MUTS Development Team"

# Import main components
from .database.ecu_database import Mazdaspeed3Database
from .services.ai_tuner import AITuningSystem
from .services.physics_engine import TurbochargerPhysics, EngineThermodynamics
from .services.dealer_service import MazdaDealerSecurity
from .services.performance_features import AntiLagSystem, TwoStepRevLimiter, LaunchControlSystem
from .models.engine_models import IdealGasPhysics, TurbochargerDynamics
from .models.turbo_models import K04Turbocharger
from .utils.calculations import AdvancedCalculations, TuningSecrets
from .utils.security import SecurityManager

__all__ = [
    'Mazdaspeed3Database',
    'AITuningSystem', 
    'TurbochargerPhysics',
    'EngineThermodynamics',
    'MazdaDealerSecurity',
    'AntiLagSystem',
    'TwoStepRevLimiter',
    'LaunchControlSystem',
    'IdealGasPhysics',
    'TurbochargerDynamics',
    'K04Turbocharger',
    'AdvancedCalculations',
    'TuningSecrets',
    'SecurityManager'
]
