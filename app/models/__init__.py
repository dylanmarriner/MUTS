"""
Models module for MUTS
Contains engine and turbocharger models
"""

from .engine_models import IdealGasPhysics, TurbochargerDynamics
from .turbo_models import K04Turbocharger

__all__ = [
    'IdealGasPhysics',
    'TurbochargerDynamics',
    'K04Turbocharger'
]
