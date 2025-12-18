#!/usr/bin/env python3
"""
Seed Alfa Romeo Giulietta OEM baseline constants for Virtual Dyno
Supports 2012 model year with C-Evo platform
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from muts.models.database_models import (
    db, VehicleConstantsPreset, TransmissionType, DrivetrainType, User
)

def create_alfa_giulietta_presets():
    """Create Alfa Romeo Giulietta OEM baseline presets"""
    
    # Get or create default user
    user = db.session.query(User).filter_by(username="system").first()
    if not user:
        user = User(
            username="system",
            email="system@muts.local",
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
    
    presets = []
    
    # === Alfa Romeo Giulietta 1.4T MultiAir ===
    # Base model with turbocharged petrol engine
    presets.append(VehicleConstantsPreset(
        name="Alfa Romeo Giulietta 1.4T MultiAir 6MT",
        manufacturer="Alfa Romeo",
        platform="C-Evo",
        model="Giulietta",
        body="Hatchback",
        generation="2012",
        variant="1.4T MultiAir",
        year=2012,
        chassis="940",
        engine="1.4L MultiAir Turbo I4",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.FWD,
        
        # Physics constants (OEM specifications)
        vehicle_mass=1290,  # Curb weight (kg) - 6MT
        driver_fuel_estimate=95,
        drag_coefficient=0.31,  # Cd for Giulietta
        frontal_area=2.15,  # m²
        rolling_resistance=0.010,  # Crr for performance tires
        air_density=1.225,
        wheel_radius=0.309,  # 16" OEM wheel (195/65 R15)
        
        # Efficiency
        drivetrain_efficiency=0.90,  # Manual transmission
        manual_efficiency=0.90,
        
        # Transmission (6-speed manual)
        gear_ratios=[3.58, 2.06, 1.30, 0.97, 0.80, 0.69],
        final_drive_ratio=3.73,
        
        # Metadata
        source="Alfa Romeo C-Evo OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    presets.append(VehicleConstantsPreset(
        name="Alfa Romeo Giulietta 1.4T MultiAir TCT",
        manufacturer="Alfa Romeo",
        platform="C-Evo",
        model="Giulietta",
        body="Hatchback",
        generation="2012",
        variant="1.4T MultiAir",
        year=2012,
        chassis="940",
        engine="1.4L MultiAir Turbo I4",
        transmission_type=TransmissionType.TCT,
        drivetrain_type=DrivetrainType.FWD,
        
        # Physics constants
        vehicle_mass=1320,  # TCT adds ~30kg
        driver_fuel_estimate=95,
        drag_coefficient=0.31,
        frontal_area=2.15,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.309,
        
        # Efficiency (TCT slightly lower than manual)
        drivetrain_efficiency=0.87,
        auto_efficiency=0.87,
        
        # Transmission (6-speed TCT dry dual-clutch)
        gear_ratios=[3.73, 2.14, 1.36, 1.01, 0.83, 0.69],
        final_drive_ratio=3.73,
        
        # Metadata
        source="Alfa Romeo C-Evo OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # === Alfa Romeo Giulietta 1.75TBi QV ===
    # Quadrifoglio Verde performance model
    presets.append(VehicleConstantsPreset(
        name="Alfa Romeo Giulietta 1.75TBi QV 6MT",
        manufacturer="Alfa Romeo",
        platform="C-Evo",
        model="Giulietta",
        body="Hatchback",
        generation="2012",
        variant="1.75TBi QV",
        year=2012,
        chassis="940",
        engine="1.75L TBi Turbo I4",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.FWD,
        
        # Physics constants
        vehicle_mass=1390,  # QV package weight
        driver_fuel_estimate=95,
        drag_coefficient=0.32,  # QV has different bumpers/aero
        frontal_area=2.18,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.318,  # 17" OEM wheel (225/45 R17)
        
        # Efficiency
        drivetrain_efficiency=0.90,
        manual_efficiency=0.90,
        
        # Transmission (6-speed manual - close ratio)
        gear_ratios=[3.73, 2.14, 1.45, 1.07, 0.86, 0.72],
        final_drive_ratio=3.73,
        
        # Metadata
        source="Alfa Romeo C-Evo OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    presets.append(VehicleConstantsPreset(
        name="Alfa Romeo Giulietta 1.75TBi QV TCT",
        manufacturer="Alfa Romeo",
        platform="C-Evo",
        model="Giulietta",
        body="Hatchback",
        generation="2012",
        variant="1.75TBi QV",
        year=2012,
        chassis="940",
        engine="1.75L TBi Turbo I4",
        transmission_type=TransmissionType.TCT,
        drivetrain_type=DrivetrainType.FWD,
        
        # Physics constants
        vehicle_mass=1420,  # QV + TCT
        driver_fuel_estimate=95,
        drag_coefficient=0.32,
        frontal_area=2.18,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.318,
        
        # Efficiency
        drivetrain_efficiency=0.87,
        auto_efficiency=0.87,
        
        # Transmission (6-speed TCT - performance tuned)
        gear_ratios=[3.73, 2.14, 1.45, 1.07, 0.86, 0.72],
        final_drive_ratio=3.73,
        
        # Metadata
        source="Alfa Romeo C-Evo OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # === Alfa Romeo Giulietta 2.0 JTDm ===
    # Diesel variant
    presets.append(VehicleConstantsPreset(
        name="Alfa Romeo Giulietta 2.0 JTDm 6MT",
        manufacturer="Alfa Romeo",
        platform="C-Evo",
        model="Giulietta",
        body="Hatchback",
        generation="2012",
        variant="2.0 JTDm",
        year=2012,
        chassis="940",
        engine="2.0L JTDm Turbo I4 Diesel",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.FWD,
        
        # Physics constants
        vehicle_mass=1425,  # Diesel engine heavier
        driver_fuel_estimate=95,
        drag_coefficient=0.31,
        frontal_area=2.15,
        rolling_resistance=0.011,  # Slightly higher for diesel tires
        air_density=1.225,
        wheel_radius=0.309,
        
        # Efficiency
        drivetrain_efficiency=0.88,  # Diesel drivetrain losses
        manual_efficiency=0.88,
        
        # Transmission (6-speed manual - diesel specific ratios)
        gear_ratios=[3.73, 2.14, 1.36, 1.01, 0.83, 0.69],
        final_drive_ratio=3.56,
        
        # Metadata
        source="Alfa Romeo C-Evo OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    presets.append(VehicleConstantsPreset(
        name="Alfa Romeo Giulietta 2.0 JTDm TCT",
        manufacturer="Alfa Romeo",
        platform="C-Evo",
        model="Giulietta",
        body="Hatchback",
        generation="2012",
        variant="2.0 JTDm",
        year=2012,
        chassis="940",
        engine="2.0L JTDm Turbo I4 Diesel",
        transmission_type=TransmissionType.TCT,
        drivetrain_type=DrivetrainType.FWD,
        
        # Physics constants
        vehicle_mass=1455,  # Diesel + TCT
        driver_fuel_estimate=95,
        drag_coefficient=0.31,
        frontal_area=2.15,
        rolling_resistance=0.011,
        air_density=1.225,
        wheel_radius=0.309,
        
        # Efficiency
        drivetrain_efficiency=0.85,  # Diesel + TCT losses
        auto_efficiency=0.85,
        
        # Transmission (6-speed TCT - diesel specific)
        gear_ratios=[3.73, 2.14, 1.36, 1.01, 0.83, 0.69],
        final_drive_ratio=3.56,
        
        # Metadata
        source="Alfa Romeo C-Evo OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # Add all presets to database
    for preset in presets:
        # Check if already exists
        existing = db.session.query(VehicleConstantsPreset).filter_by(
            manufacturer=preset.manufacturer,
            platform=preset.platform,
            model=preset.model,
            variant=preset.variant,
            transmission_type=preset.transmission_type
        ).first()
        
        if not existing:
            db.session.add(preset)
            print(f"Added: {preset.name}")
        else:
            print(f"Already exists: {preset.name}")
    
    db.session.commit()
    print(f"\nAlfa Romeo Giulietta presets seeded successfully!")
    print(f"Total presets: {len(presets)}")
    
    return presets


if __name__ == "__main__":
    from app import create_app
    
    app = create_app()
    with app.app_context():
        create_alfa_giulietta_presets()
