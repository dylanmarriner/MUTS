#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTILS MODULE MOCK
Provides minimal implementations for missing utils dependencies
"""

import logging

def get_logger(name: str):
    """Get logger instance"""
    return logging.getLogger(name)
