#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORE PACKAGE INITIALIZATION
Provides access to core ECU communication and safety validation modules
"""

import logging
from .ecu_communication import ECUCommunicator, ECUResponse, ECUState
from .safety_validator import SafetyValidator, get_safety_validator, create_safety_validator

__all__ = [
    'ECUCommunicator',
    'ECUResponse', 
    'ECUState',
    'SafetyValidator',
    'get_safety_validator',
    'create_safety_validator'
]

logger = logging.getLogger(__name__)
logger.info("Core package initialized")
