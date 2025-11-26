"""
COMPLETE MAZDASPEED 3 TUNING DATABASE
All factory calibration data, performance maps, and proprietary tuning knowledge
"""

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

Base = declarative_base()

class PerformanceTuningMap(Base):
    """Performance tuning maps and modifications"""
    __tablename__ = 'performance_tuning_maps'

    id = Column(Integer, primary_key=True)
    map_name = Column(String(100), nullable=False)
    description = Column(Text)
    vehicle_model = Column(String(20), nullable=False)
    performance_level = Column(String(20))  # 'stage1', 'stage2', 'stage3'
    required_modifications = Column(Text)   # JSON list of required mods

    # Tuning parameters
    ignition_advance_map = Column(Text)     # Ignition timing adjustments
    boost_target_increase = Column(Text)    # Boost pressure increases
    fuel_requirement_adjustments = Column(Text)  # Fuel map modifications
    vvt_optimization_maps = Column(Text)    # VVT timing optimizations

    # Safety limits
    safety_limits = Column(Text)            # Tuning-specific safety limits
    recommended_octane = Column(String(10)) # '91', '93', 'e85'
    max_power = Column(Float)               # Estimated maximum power
    max_torque = Column(Float)              # Estimated maximum torque

    # Validation data
    dyno_results = Column(Text)             # JSON dyno data
    real_world_testing = Column(Text)       # Real-world validation data
    created_date = Column(DateTime, default=datetime.utcnow)

class TurbochargerDatabase(Base):
    """Complete K04 turbocharger specifications and performance data"""
    __tablename__ = 'turbocharger_data'

    id = Column(Integer, primary_key=True)
    turbo_model = Column(String(50), nullable=False)  # 'Mitsubishi TD04-HL-15T-6'
    application = Column(String(100))  # 'Mazdaspeed 3 2011 MZR 2.3L DISI'

    # Compressor specifications
    compressor_wheel_inducer = Column(Float)  # mm
    compressor_wheel_exducer = Column(Float)  # mm
    compressor_trim = Column(Float)           # Trim calculation
    compressor_max_flow = Column(Float)       # kg/s
    compressor_max_efficiency = Column(Float) # %
    compressor_max_pressure_ratio = Column(Float)

    # Turbine specifications
    turbine_wheel_diameter = Column(Float)    # mm
    turbine_housing_ar = Column(Float)        # A/R ratio
    turbine_max_efficiency = Column(Float)    # %
    turbine_moment_of_inertia = Column(Float) # kg·m²

    # Performance maps (JSON)
    compressor_performance_map = Column(Text)  # Complete compressor map data
    turbine_performance_map = Column(Text)     # Complete turbine map data
    efficiency_maps = Column(Text)             # Efficiency across operating range

    # Mechanical specifications
    bearing_type = Column(String(50))
    max_speed_rpm = Column(Float)
    weight = Column(Float)  # kg
    oil_requirements = Column(Text)

    # Upgrade compatibility
    compatible_upgrades = Column(Text)        # JSON list of compatible upgrades
    common_failures = Column(Text)            # Common failure modes and solutions

class EngineComponentDatabase(Base):
    """Complete engine component specifications and limits"""
    __tablename__ = 'engine_components'

    id = Column(Integer, primary_key=True)
    component_type = Column(String(50), nullable=False)  # 'piston', 'rod', 'valve', etc.
    component_name = Column(String(100), nullable=False)
    oem_part_number = Column(String(50))

    # Material specifications
    material = Column(String(50))
    tensile_strength = Column(Float)  # MPa
    yield_strength = Column(Float)    # MPa
    hardness = Column(String(20))

    # Physical specifications
    weight = Column(Float)            # grams
    dimensions = Column(Text)         # JSON dimensions
    clearance_specs = Column(Text)    # Installation clearances

    # Performance limits
    max_temperature = Column(Float)   # °C
    max_pressure = Column(Float)      # bar
    max_rpm = Column(Float)           # RPM
    fatigue_life = Column(Text)       # Fatigue life data

    # Failure analysis
    common_failure_modes = Column(Text)
    failure_analysis = Column(Text)
    upgrade_recommendations = Column(Text)

class TuningSecret(Base):
    """Proprietary tuning secrets and techniques"""
    __tablename__ = 'tuning_secrets'

    id = Column(Integer, primary_key=True)
    secret_name = Column(String(100), nullable=False)
    category = Column(String(50))  # 'boost', 'ignition', 'vvt', 'fuel'
    description = Column(Text)

    # Technical implementation
    technical_basis = Column(Text)    # Physics/engineering basis
    implementation_method = Column(Text)  # How to implement
    expected_benefits = Column(Text)  # Expected performance gains
    potential_risks = Column(Text)    # Potential risks or downsides

    # Application parameters
    applicable_conditions = Column(Text)  # When to use this technique
    vehicle_specific_notes = Column(Text) # Mazdaspeed 3 specific notes
    validation_data = Column(Text)        # Testing and validation results

    # Safety considerations
    safety_limits = Column(Text)      # Safety limits for this technique
    monitoring_requirements = Column(Text)  # What to monitor during use

    created_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DiagnosticTroubleCode(Base):
    """Complete diagnostic trouble code database"""
    __tablename__ = 'diagnostic_trouble_codes'

    id = Column(Integer, primary_key=True)
    code = Column(String(5), nullable=False)  # 'P0301', 'P0234', etc.
    description = Column(String(200), nullable=False)
    severity = Column(String(20))  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'

    # Technical details
    system_affected = Column(String(50))
    possible_causes = Column(Text)        # JSON list of possible causes
    diagnostic_procedure = Column(Text)   # Step-by-step diagnosis
    repair_procedures = Column(Text)      # Repair instructions

    # Mazdaspeed 3 specific
    common_on_mazdaspeed3 = Column(Boolean, default=False)
    ms3_specific_causes = Column(Text)    # MS3-specific common causes
    ms3_repair_tips = Column(Text)        # MS3-specific repair tips

    # Related data
    related_codes = Column(Text)          # JSON list of related DTCs
    required_tools = Column(Text)         # Tools needed for diagnosis
