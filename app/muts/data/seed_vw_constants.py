#!/usr/bin/env python3
"""
Seed VW Golf OEM baseline constants for Virtual Dyno
Supports Mk5/Mk6 (PQ35) and Mk7/Mk7.5 (MQB) platforms
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from muts.models.database_models import (
    db, VehicleConstantsPreset, TransmissionType, DrivetrainType, User
)

def create_vw_golf_presets():
    """Create VW Golf OEM baseline presets"""
    
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
    
    # === VW Golf Mk5 GTI (PQ35) ===
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk5 GTI Manual",
        manufacturer="Volkswagen",
        platform="PQ35",
        model="Golf",
        generation="Mk5",
        variant="GTI",
        year=2006,
        chassis="1K",
        engine="EA113 2.0L TSI",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.FWD,
        
        # Physics constants (OEM specifications)
        vehicle_mass=1362,  # Curb weight (kg)
        driver_fuel_estimate=95,
        drag_coefficient=0.32,  # Cd for Mk5 GTI
        frontal_area=2.20,  # m²
        rolling_resistance=0.010,  # Crr for performance tires
        air_density=1.225,
        wheel_radius=0.315,  # 18" OEM wheel
        
        # Efficiency
        drivetrain_efficiency=0.90,  # Manual transmission
        manual_efficiency=0.90,
        
        # Transmission (6-speed manual MQ250-6F)
        gear_ratios=[3.36, 1.99, 1.33, 1.03, 0.84, 0.69],
        final_drive_ratio=4.24,
        
        # Metadata
        source="VW PQ35 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk5 GTI DSG",
        manufacturer="Volkswagen",
        platform="PQ35",
        model="Golf",
        generation="Mk5",
        variant="GTI",
        year=2006,
        chassis="1K",
        engine="EA113 2.0L TSI",
        transmission_type=TransmissionType.DSG,
        drivetrain_type=DrivetrainType.FWD,
        
        # Physics constants
        vehicle_mass=1382,  # DSG adds ~20kg
        driver_fuel_estimate=95,
        drag_coefficient=0.32,
        frontal_area=2.20,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.315,
        
        # Efficiency (DSG slightly lower than manual)
        drivetrain_efficiency=0.87,
        auto_efficiency=0.87,
        
        # Transmission (6-speed DSG DQ250)
        gear_ratios=[3.58, 2.11, 1.43, 1.12, 0.89, 0.74],
        final_drive_ratio=4.24,
        
        # Metadata
        source="VW PQ35 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # === VW Golf Mk6 GTI (PQ35) ===
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk6 GTI Manual",
        manufacturer="Volkswagen",
        platform="PQ35",
        model="Golf",
        generation="Mk6",
        variant="GTI",
        year=2010,
        chassis="1K",
        engine="EA113 2.0L TSI",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.FWD,
        
        vehicle_mass=1370,
        driver_fuel_estimate=95,
        drag_coefficient=0.31,  # Slightly improved over Mk5
        frontal_area=2.20,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.315,
        
        drivetrain_efficiency=0.90,
        manual_efficiency=0.90,
        
        gear_ratios=[3.36, 1.99, 1.33, 1.03, 0.84, 0.69],
        final_drive_ratio=4.24,
        
        source="VW PQ35 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk6 GTI DSG",
        manufacturer="Volkswagen",
        platform="PQ35",
        model="Golf",
        generation="Mk6",
        variant="GTI",
        year=2010,
        chassis="1K",
        engine="EA113 2.0L TSI",
        transmission_type=TransmissionType.DSG,
        drivetrain_type=DrivetrainType.FWD,
        
        vehicle_mass=1390,
        driver_fuel_estimate=95,
        drag_coefficient=0.31,
        frontal_area=2.20,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.315,
        
        drivetrain_efficiency=0.87,
        auto_efficiency=0.87,
        
        gear_ratios=[3.58, 2.11, 1.43, 1.12, 0.89, 0.74],
        final_drive_ratio=4.24,
        
        source="VW PQ35 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # === VW Golf Mk6 R (PQ35) ===
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk6 R DSG",
        manufacturer="Volkswagen",
        platform="PQ35",
        model="Golf",
        generation="Mk6",
        variant="R",
        year=2012,
        chassis="1K",
        engine="EA113 2.0L TSI",
        transmission_type=TransmissionType.DSG,
        drivetrain_type=DrivetrainType.AWD_HALDEX,
        
        vehicle_mass=1545,  # AWD adds significant weight
        driver_fuel_estimate=95,
        drag_coefficient=0.33,  # R has different bumpers/aero
        frontal_area=2.22,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.315,
        
        # AWD efficiency penalty
        drivetrain_efficiency=0.85,
        auto_efficiency=0.85,
        
        # DSG with AWD
        gear_ratios=[3.58, 2.11, 1.43, 1.12, 0.89, 0.74],
        final_drive_ratio=3.69,  # Different final drive for AWD
        
        # Haldex torque split (predominantly FWD)
        awd_torque_split_front=0.65,
        awd_torque_split_rear=0.35,
        
        source="VW PQ35 OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # === VW Golf Mk7 GTI (MQB) ===
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk7 GTI Manual",
        manufacturer="Volkswagen",
        platform="MQB",
        model="Golf",
        generation="Mk7",
        variant="GTI",
        year=2015,
        chassis="AU",
        engine="EA888 2.0L TSI",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.FWD,
        
        vehicle_mass=1355,  # Weight reduction with MQB
        driver_fuel_estimate=95,
        drag_coefficient=0.30,  # Improved aerodynamics
        frontal_area=2.20,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.318,  # 18" "Serron" wheels
        
        drivetrain_efficiency=0.90,
        manual_efficiency=0.90,
        
        # 6-speed manual MQ350
        gear_ratios=[3.64, 2.24, 1.53, 1.16, 0.95, 0.79],
        final_drive_ratio=3.69,
        
        source="VW MQB OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk7 GTI DSG",
        manufacturer="Volkswagen",
        platform="MQB",
        model="Golf",
        generation="Mk7",
        variant="GTI",
        year=2015,
        chassis="AU",
        engine="EA888 2.0L TSI",
        transmission_type=TransmissionType.DSG,
        drivetrain_type=DrivetrainType.FWD,
        
        vehicle_mass=1375,
        driver_fuel_estimate=95,
        drag_coefficient=0.30,
        frontal_area=2.20,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.318,
        
        drivetrain_efficiency=0.87,
        auto_efficiency=0.87,
        
        # 6-speed DSG DQ381
        gear_ratios=[3.85, 2.42, 1.62, 1.23, 1.00, 0.83],
        final_drive_ratio=3.69,
        
        source="VW MQB OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # === VW Golf Mk7.5 GTI (MQB refresh) ===
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk7.5 GTI DSG",
        manufacturer="Volkswagen",
        platform="MQB",
        model="Golf",
        generation="Mk7.5",
        variant="GTI",
        year=2018,
        chassis="AU",
        engine="EA888 2.0L TSI Gen3",
        transmission_type=TransmissionType.DSG,
        drivetrain_type=DrivetrainType.FWD,
        
        vehicle_mass=1385,
        driver_fuel_estimate=95,
        drag_coefficient=0.30,
        frontal_area=2.20,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.318,
        
        drivetrain_efficiency=0.87,
        auto_efficiency=0.87,
        
        gear_ratios=[3.85, 2.42, 1.62, 1.23, 1.00, 0.83],
        final_drive_ratio=3.69,
        
        source="VW MQB OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # === VW Golf Mk7 R (MQB) ===
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk7 R DSG",
        manufacturer="Volkswagen",
        platform="MQB",
        model="Golf",
        generation="Mk7",
        variant="R",
        year=2015,
        chassis="AU",
        engine="EA888 2.0L TSI",
        transmission_type=TransmissionType.DSG,
        drivetrain_type=DrivetrainType.AWD_HALDEX,
        
        vehicle_mass=1520,
        driver_fuel_estimate=95,
        drag_coefficient=0.32,
        frontal_area=2.22,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.318,
        
        # AWD with DSG efficiency
        drivetrain_efficiency=0.85,
        auto_efficiency=0.85,
        
        # DSG with AWD
        gear_ratios=[3.85, 2.42, 1.62, 1.23, 1.00, 0.83],
        final_drive_ratio=3.16,
        
        # Haldex 5 (more rear bias than previous)
        awd_torque_split_front=0.60,
        awd_torque_split_rear=0.40,
        
        source="VW MQB OEM / Engineering Estimate",
        source_type="OEM",
        confidence_score=100,
        created_by=user.id
    ))
    
    # === VW Golf Mk7 TSI (base model) ===
    presets.append(VehicleConstantsPreset(
        name="VW Golf Mk7 1.8T TSI",
        manufacturer="Volkswagen",
        platform="MQB",
        model="Golf",
        generation="Mk7",
        variant="TSI",
        year=2015,
        chassis="AU",
        engine="EA888 1.8L TSI",
        transmission_type=TransmissionType.MANUAL,
        drivetrain_type=DrivetrainType.FWD,
        
        vehicle_mass=1290,  # Lighter than GTI
        driver_fuel_estimate=95,
        drag_coefficient=0.29,  # Better Cd without GTI body kit
        frontal_area=2.20,
        rolling_resistance=0.010,
        air_density=1.225,
        wheel_radius=0.315,  # 17" wheels standard
        
        drivetrain_efficiency=0.90,
        manual_efficiency=0.90,
        
        # 5-speed manual for 1.8T
        gear_ratios=[3.45, 1.94, 1.29, 0.97, 0.80],
        final_drive_ratio=3.69,
        
        source="VW MQB OEM / Engineering Estimate",
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
            generation=preset.generation,
            variant=preset.variant,
            transmission_type=preset.transmission_type
        ).first()
        
        if not existing:
            db.session.add(preset)
            print(f"Created preset: {preset.name}")
        else:
            print(f"Preset already exists: {preset.name}")
    
    # Commit changes
    db.session.commit()
    print(f"\nVW Golf OEM presets created successfully!")
    print(f"Total presets: {len(presets)}")

if __name__ == "__main__":
    from muts.app import create_app
    app = create_app()
    
    with app.app_context():
        create_vw_golf_presets()
