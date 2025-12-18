#!/usr/bin/env python3
"""
Seed OEM baseline constants for BMW, Subaru, and Toyota
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from muts.models.database_models import (
    db, VehicleConstantsPreset, TransmissionType, DrivetrainType, User
)

def create_bmw_presets():
    """Create BMW OEM baseline presets"""
    
    user = db.session.query(User).filter_by(username="system").first()
    if not user:
        user = User(username="system", email="system@muts.local", role="admin")
        db.session.add(user)
        db.session.commit()
    
    presets = []
    
    # BMW 335i (E90) - RWD
    presets.append(VehicleConstantsPreset(
        name="BMW 335i E90 Manual",
        manufacturer="BMW",
        platform="E90",
        model="3 Series",
        generation="E90",
        variant="335i",
        year=2008,
        chassis="E90",
        engine="N54 3.0L Twin-Turbo I6",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.RWD,
        
        vehicle_mass=1545,
        driver_fuel_estimate=95,
        drag_coefficient=0.28,
        frontal_area=2.15,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.318,
        
        drivetrain_efficiency=0.91,  # RWD manual is efficient
        manual_efficiency=0.91,
        
        gear_ratios=[4.06, 2.40, 1.58, 1.19, 1.00, 0.87],
        final_drive_ratio=3.46,
        
        source="BMW E90 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # BMW 335i (E90) - Steptronic
    presets.append(VehicleConstantsPreset(
        name="BMW 335i E90 Steptronic",
        manufacturer="BMW",
        platform="E90",
        model="3 Series",
        generation="E90",
        variant="335i",
        year=2008,
        chassis="E90",
        engine="N54 3.0L Twin-Turbo I6",
        transmission_type=TransmissionType.TORQUE_CONVERTER,
        drivetrain_type=DrivetrainType.RWD,
        
        vehicle_mass=1570,
        driver_fuel_estimate=95,
        drag_coefficient=0.28,
        frontal_area=2.15,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.318,
        
        drivetrain_efficiency=0.88,
        auto_efficiency=0.88,
        
        gear_ratios=[4.06, 2.40, 1.58, 1.19, 1.00, 0.87],
        final_drive_ratio=3.46,
        
        source="BMW E90 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # BMW M3 (E92) - DCT
    presets.append(VehicleConstantsPreset(
        name="BMW M3 E92 DCT",
        manufacturer="BMW",
        platform="E92",
        model="3 Series",
        generation="E92",
        variant="M3",
        year=2011,
        chassis="E92",
        engine="S65 4.0L V8",
        transmission_type=TransmissionType.DSG,  # BMW DCT
        drivetrain_type=DrivetrainType.RWD,
        
        vehicle_mass=1680,
        driver_fuel_estimate=95,
        drag_coefficient=0.32,  # M body kit
        frontal_area=2.18,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.326,
        
        drivetrain_efficiency=0.89,
        auto_efficiency=0.89,
        
        gear_ratios=[4.06, 2.56, 1.81, 1.39, 1.16, 1.00, 0.85],
        final_drive_ratio=3.15,
        
        source="BMW E92 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    return presets

def create_subaru_presets():
    """Create Subaru OEM baseline presets"""
    
    user = db.session.query(User).filter_by(username="system").first()
    
    presets = []
    
    # Subaru WRX STI (GR) - AWD
    presets.append(VehicleConstantsPreset(
        name="Subaru WRX STI GR 6MT",
        manufacturer="Subaru",
        platform="GR",
        model="WRX STI",
        generation="GR",
        variant="STI",
        year=2015,
        chassis="GR",
        engine="EJ257 2.5L Boxer Turbo",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.AWD_FULL,  # Symmetrical AWD
        
        vehicle_mass=1545,
        driver_fuel_estimate=95,
        drag_coefficient=0.35,
        frontal_area=2.22,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.318,
        
        drivetrain_efficiency=0.85,  # AWD penalty
        manual_efficiency=0.85,
        
        gear_ratios=[3.636, 2.375, 1.761, 1.307, 1.031, 0.837],
        final_drive_ratio=4.444,
        
        # Symmetrical AWD torque split
        awd_torque_split_front=0.50,
        awd_torque_split_rear=0.50,
        
        source="Subaru GR OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # Subaru BRZ - RWD
    presets.append(VehicleConstantsPreset(
        name="Subaru BRZ 6MT",
        manufacturer="Subaru",
        platform="ZC6",
        model="BRZ",
        generation="ZC6",
        variant="Base",
        year=2017,
        chassis="ZC6",
        engine="FA20 2.0L Boxer",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.RWD,
        
        vehicle_mass=1230,
        driver_fuel_estimate=95,
        drag_coefficient=0.27,
        frontal_area=2.10,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.305,
        
        drivetrain_efficiency=0.92,  # Lightweight RWD
        manual_efficiency=0.92,
        
        gear_ratios=[3.636, 2.375, 1.761, 1.307, 1.031, 0.837],
        final_drive_ratio=4.10,
        
        source="Subaru ZC6 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    return presets

def create_toyota_presets():
    """Create Toyota OEM baseline presets"""
    
    user = db.session.query(User).filter_by(username="system").first()
    
    presets = []
    
    # Toyota GT86 - RWD
    presets.append(VehicleConstantsPreset(
        name="Toyota GT86 6MT",
        manufacturer="Toyota",
        platform="ZN6",
        model="GT86",
        generation="ZN6",
        variant="Base",
        year=2017,
        chassis="ZN6",
        engine="FA20 2.0L Boxer",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.RWD,
        
        vehicle_mass=1250,
        driver_fuel_estimate=95,
        drag_coefficient=0.27,
        frontal_area=2.10,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.305,
        
        drivetrain_efficiency=0.92,
        manual_efficiency=0.92,
        
        gear_ratios=[3.636, 2.375, 1.761, 1.307, 1.031, 0.837],
        final_drive_ratio=4.10,
        
        source="Toyota ZN6 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # Toyota Supra (A90) - RWD
    presets.append(VehicleConstantsPreset(
        name="Toyota Supra A90 ZF8",
        manufacturer="Toyota",
        platform="A90",
        model="Supra",
        generation="A90",
        variant="3.0",
        year=2020,
        chassis="A90",
        engine="B58 3.0L Turbo I6",
        transmission_type=TransmissionType.TORQUE_CONVERTER,  # ZF 8HP
        drivetrain_type=DrivetrainType.RWD,
        
        vehicle_mass=1535,
        driver_fuel_estimate=95,
        drag_coefficient=0.29,
        frontal_area=2.15,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.326,
        
        drivetrain_efficiency=0.90,  # Modern ZF is efficient
        auto_efficiency=0.90,
        
        gear_ratios=[4.71, 3.14, 2.11, 1.67, 1.29, 1.00, 0.84, 0.67],
        final_drive_ratio=3.15,
        
        source="Toyota A90 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # Toyota Camry (XV70) - FWD
    presets.append(VehicleConstantsPreset(
        name="Toyota Camry XSE 8AT",
        manufacturer="Toyota",
        platform="TNGA-K",
        model="Camry",
        generation="XV70",
        variant="XSE",
        year=2020,
        chassis="XV70",
        engine="A25A-FKS 2.5L I4",
        transmission_type=TransmissionType.TORQUE_CONVERTER,
        drivetrain_type=DrivetrainType.FWD,
        
        vehicle_mass=1590,
        driver_fuel_estimate=95,
        drag_coefficient=0.28,
        frontal_area=2.28,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.324,
        
        drivetrain_efficiency=0.88,
        auto_efficiency=0.88,
        
        gear_ratios=[4.71, 3.14, 2.11, 1.67, 1.29, 1.00, 0.84, 0.67],
        final_drive_ratio=3.18,
        
        source="Toyota XV70 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    return presets

def main():
    """Create all OEM presets"""
    
    all_presets = []
    all_presets.extend(create_bmw_presets())
    all_presets.extend(create_subaru_presets())
    all_presets.extend(create_toyota_presets())
    
    # Add to database
    for preset in all_presets:
        existing = db.session.query(VehicleConstantsPreset).filter_by(
            manufacturer=preset.manufacturer,
            platform=preset.platform,
            model=preset.model,
            generation=preset.generation,
            variant=preset.variant,
            transmission_type=preset.transmission_type
        ).first()
        
        if not existing:
            db.session.add(preset)
            print(f"Created preset: {preset.name}")
        else:
            print(f"Preset already exists: {preset.name}")
    
    db.session.commit()
    print(f"\nBMW, Subaru, and Toyota OEM presets created successfully!")
    print(f"Total presets: {len(all_presets)}")

if __name__ == "__main__":
    from muts.app import create_app
    app = create_app()
    
    with app.app_context():
        main()
