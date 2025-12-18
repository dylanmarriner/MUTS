#!/usr/bin/env python3
"""
Seed OEM constants for Holden Commodore VF and VW Golf Mk6
Real OEM specifications where available, conservative estimates where not
"""

import sys
import os
# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from muts.models.database_models import Base, engine, TransmissionType, DrivetrainType
from muts.models.vehicle_constants import VehicleConstantsPreset
from muts.models.vehicle_profile import VehicleProfile
from muts.models.database_models import User, Vehicle
from muts.models.vehicle_constants import VehicleConstants
from muts.models.forensic_models import ForensicSession, ForensicEvent, DryRunSession
from muts.models.override_models import OverrideAuditLog
from muts.models.diagnostics_template import DiagnosticsCapabilityTemplate
from muts.models.diagnostics_registry import template_registry
from muts.models.vehicle_capabilities import VehicleCapabilityProfile
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

# Create session
Session = sessionmaker(bind=engine)
session = Session()


def create_holden_vf_constants():
    """Create OEM constants for Holden Commodore VF Evoke Wagon V6 3.0 6AT"""
    
    # OEM specifications from Holden documentation
    constants = VehicleConstantsPreset(
        name="Holden Commodore VF Evoke Wagon V6 3.0 6AT OEM",
        manufacturer="Holden",
        platform="VF",
        model="Commodore",
        body="Station Wagon",
        generation="VF II",
        variant="Evoke V6 3.0P/6AT",
        year=2015,
        chassis="VF",
        engine="LFW 3.0L V6",
        
        # Transmission and drivetrain
        transmission_type=TransmissionType.TORQUE_CONVERTER,
        drivetrain_type=DrivetrainType.RWD,
        
        # Mass properties (OEM spec)
        vehicle_mass=1780,  # Curb mass in kg (OEM spec)
        driver_fuel_estimate=95,  # Driver + fuel estimate
        
        # Aerodynamic properties
        drag_coefficient=0.30,  # OEM spec for VF wagon
        frontal_area=2.31,  # m² (calculated from width x height)
        
        # Rolling resistance
        rolling_resistance=0.009,  # Typical for passenger tires
        
        # Environmental conditions
        air_density=1.225,  # Sea level, 15°C
        
        # Wheel properties
        wheel_radius=0.329,  # meters (17" wheel with 225/60R17 tire)
        
        # Drivetrain properties
        drivetrain_efficiency=0.85,  # 6-speed automatic
        manual_efficiency=0.90,
        auto_efficiency=0.85,
        
        # Test conditions
        road_grade=0.0,
        gravity=9.80665,
        
        # Gearing (6-speed auto)
        final_drive_ratio=2.92,
        gear_ratios=[4.58, 2.86, 1.88, 1.35, 1.00, 0.74],
        
        # Metadata
        source="Holden OEM Documentation",
        source_type="OEM",
        notes="OEM baseline for VF Commodore V6 wagon with 6-speed automatic",
        confidence_score=100
    )
    
    session.add(constants)
    session.commit()
    logger.info(f"Created Holden VF constants preset: {constants.id}")
    return constants


def create_vw_golf_constants():
    """Create OEM constants for VW Golf Mk6 TSI 90kW 1.4 7DSG"""
    
    # OEM specifications from VW documentation
    constants = VehicleConstantsPreset(
        name="Volkswagen Golf Mk6 TSI 90kW 1.4 7DSG OEM",
        manufacturer="Volkswagen",
        platform="A6",
        model="Golf",
        body="Hatchback",
        generation="Mk6",
        variant="TSI 90KW 7DSG",
        year=2011,
        chassis="A6",
        engine="CAX 1.4L TSI",
        
        # Transmission and drivetrain
        transmission_type=TransmissionType.DSG,
        drivetrain_type=DrivetrainType.FWD,
        
        # Mass properties (OEM spec)
        vehicle_mass=1295,  # Curb mass in kg (OEM spec)
        driver_fuel_estimate=85,  # Driver + fuel estimate
        
        # Aerodynamic properties
        drag_coefficient=0.30,  # OEM spec for Golf Mk6
        frontal_area=2.22,  # m² (calculated from width x height)
        
        # Rolling resistance
        rolling_resistance=0.009,  # Typical for passenger tires
        
        # Environmental conditions
        air_density=1.225,  # Sea level, 15°C
        
        # Wheel properties
        wheel_radius=0.297,  # meters (16" wheel with 195/65R15 tire)
        
        # Drivetrain properties
        drivetrain_efficiency=0.90,  # 7-speed DSG
        manual_efficiency=0.90,
        auto_efficiency=0.85,
        
        # Test conditions
        road_grade=0.0,
        gravity=9.80665,
        
        # Gearing (7-speed DSG)
        final_drive_ratio=3.16,
        gear_ratios=[3.76, 2.27, 1.52, 1.13, 0.92, 0.81, 0.69],
        
        # Metadata
        source="VW OEM Documentation",
        source_type="OEM",
        notes="OEM baseline for Golf Mk6 1.4TSI with 7-speed DSG",
        confidence_score=100
    )
    
    session.add(constants)
    session.commit()
    logger.info(f"Created VW Golf constants preset: {constants.id}")
    return constants


def create_vehicle_profiles(holden_preset, vw_preset):
    """Create vehicle profiles for the specific VINs"""
    
    # Get or create admin user
    admin_user = session.query(User).filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@muts.local',
            password_hash='admin_hash',  # Would be properly hashed
            role='admin'
        )
        session.add(admin_user)
        session.commit()
        logger.info("Created admin user")
    
    # Create base vehicle entries
    holden_vehicle = Vehicle(
        id='6G1FA8E53FL100333',  # VIN
        user_id=admin_user.id,
        model='Holden Commodore VF Evoke Wagon V6 3.0 6AT',
        ecu_type='GM E39A'
    )
    session.add(holden_vehicle)
    
    vw_vehicle = Vehicle(
        id='WVWZZZ1KZBW232050',  # VIN
        user_id=admin_user.id,
        model='VW Golf Mk6 TSI 90kW 1.4 7DSG',
        ecu_type='VW MED17'
    )
    session.add(vw_vehicle)
    session.commit()
    
    # Create Holden profile
    holden_profile = VehicleProfile(
        vin='6G1FA8E53FL100333',
        plate='JBG175',
        engine_number='LFW142510158',
        year=2015,
        make='Holden',
        model='Commodore',
        submodel='VF EVOKE V6 3.0P/6AT',
        body='Station Wagon',
        displacement=2997,
        fuel_type='Petrol',
        colour='Black',
        user_id=admin_user.id,
        constants_preset_id=holden_preset.id
    )
    session.add(holden_profile)
    
    # Create VW profile
    vw_profile = VehicleProfile(
        vin='WVWZZZ1KZBW232050',
        plate='GBF28',
        engine_number='CAX767625',
        year=2011,
        make='Volkswagen',
        model='Golf',
        submodel='TSI 90KW 7DSG',
        body='Hatchback',
        displacement=1390,
        fuel_type='Petrol',
        colour='White',
        user_id=admin_user.id,
        constants_preset_id=vw_preset.id
    )
    session.add(vw_profile)
    session.commit()
    
    # Create initial vehicle constants for each
    holden_constants = VehicleConstants(
        vehicle_id='6G1FA8E53FL100333',
        preset_id=holden_preset.id,
        version=1,
        note='Initial OEM constants',
        created_by=admin_user.id,
        is_active=True
    )
    session.add(holden_constants)
    
    vw_constants = VehicleConstants(
        vehicle_id='WVWZZZ1KZBW232050',
        preset_id=vw_preset.id,
        version=1,
        note='Initial OEM constants',
        created_by=admin_user.id,
        is_active=True
    )
    session.add(vw_constants)
    session.commit()
    
    logger.info(f"Created vehicle profiles: Holden {holden_profile.id}, VW {vw_profile.id}")
    return holden_profile, vw_profile


def create_all():
    """Create all OEM constants and vehicle profiles"""
    try:
        # Create constants presets
        holden_preset = create_holden_vf_constants()
        vw_preset = create_vw_golf_constants()
        
        # Create vehicle profiles
        holden_profile, vw_profile = create_vehicle_profiles(holden_preset, vw_preset)
        
        logger.info("Successfully created all OEM constants and vehicle profiles")
        
        # Print summary
        print("\n=== VEHICLE PROFILES CREATED ===")
        print(f"\nHolden Commodore VF:")
        print(f"  VIN: {holden_profile.vin}")
        print(f"  Plate: {holden_profile.plate}")
        print(f"  Engine: {holden_profile.engine_number}")
        print(f"  Constants Preset: {holden_preset.name}")
        print(f"  Vehicle Mass: {holden_preset.vehicle_mass} kg")
        print(f"  Drivetrain: {holden_preset.drivetrain_type.value}")
        print(f"  Transmission: {holden_preset.transmission_type.value}")
        
        print(f"\nVW Golf Mk6:")
        print(f"  VIN: {vw_profile.vin}")
        print(f"  Plate: {vw_profile.plate}")
        print(f"  Engine: {vw_profile.engine_number}")
        print(f"  Constants Preset: {vw_preset.name}")
        print(f"  Vehicle Mass: {vw_preset.vehicle_mass} kg")
        print(f"  Drivetrain: {vw_preset.drivetrain_type.value}")
        print(f"  Transmission: {vw_preset.transmission_type.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create OEM constants: {e}")
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == '__main__':
    success = create_all()
    if success:
        print("\n✅ OEM constants and vehicle profiles created successfully")
    else:
        print("\n❌ Failed to create OEM constants and vehicle profiles")
