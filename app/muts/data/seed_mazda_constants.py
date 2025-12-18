#!/usr/bin/env python3
"""
Seed Mazda vehicle constants into the database.

Run this script to populate the database with verified Mazda defaults.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from muts.models.database_models import VehicleConstantsPreset, VehicleConstants, Vehicle, User
from muts.models.database import db


def seed_mazda_preset():
    """Create the Mazda 3 MPS 2011 BL preset with verified constants"""
    
    # Check if preset already exists
    existing = VehicleConstantsPreset.query.filter_by(
        manufacturer='Mazda',
        model='3 MPS',
        year=2011,
        chassis='BL'
    ).first()
    
    if existing:
        print(f"Mazda 3 MPS preset already exists (ID: {existing.id})")
        return existing
    
    # Create the preset with exact values from requirements
    preset = VehicleConstantsPreset(
        name='Mazda 3 MPS 2011 BL',
        manufacturer='Mazda',
        model='3 MPS',
        year=2011,
        chassis='BL',
        engine='MZR 2.3L DISI Turbo',
        drivetrain='FWD, 6MT',
        
        # Physics constants (as specified in requirements)
        vehicle_mass=1425,  # Curb weight in kg
        driver_fuel_estimate=95,  # Driver + fuel in kg
        drag_coefficient=0.33,  # Cd
        frontal_area=2.20,  # m²
        rolling_resistance=0.013,  # Crr
        air_density=1.225,  # kg/m³
        wheel_radius=0.318,  # m
        drivetrain_efficiency=0.88,  # η
        road_grade=0.0,  # degrees (flat road assumption)
        gravity=9.80665,  # m/s²
        
        # Transmission (as specified in requirements)
        gear_ratios='[3.538, 2.238, 1.535, 1.171, 0.971, 0.756]',
        final_drive_ratio=3.529,
        
        # Metadata
        source='Mazda BL OEM / Engineering Estimate',
        editable=True,
        created_at=datetime.utcnow()
    )
    
    db.session.add(preset)
    db.session.commit()
    
    print(f"Created Mazda 3 MPS preset (ID: {preset.id})")
    return preset


def create_vehicle_constants_for_existing_vehicles(preset):
    """Create vehicle constants for existing vehicles using the Mazda preset"""
    
    # Find all existing vehicles
    vehicles = Vehicle.query.all()
    
    for vehicle in vehicles:
        # Check if constants already exist
        existing = VehicleConstants.query.filter_by(vehicle_id=vehicle.id).first()
        if existing:
            print(f"Vehicle {vehicle.id} already has constants (version {existing.version})")
            continue
        
        # Create new constants version
        max_version = db.session.query(db.func.max(VehicleConstants.version)).filter_by(
            vehicle_id=vehicle.id
        ).scalar() or 0
        
        constants = VehicleConstants(
            vehicle_id=vehicle.id,
            preset_id=preset.id,
            version=max_version + 1,
            note='Initial setup with Mazda defaults',
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        # Deactivate any previous versions
        VehicleConstants.query.filter_by(vehicle_id=vehicle.id).update({'is_active': False})
        
        db.session.add(constants)
        print(f"Created constants for vehicle {vehicle.id} (version {constants.version})")
    
    db.session.commit()


def main():
    """Main seeding function"""
    print("Seeding Mazda vehicle constants...")
    
    # Create the Mazda preset
    mazda_preset = seed_mazda_preset()
    
    # Create constants for existing vehicles
    create_vehicle_constants_for_existing_vehicles(mazda_preset)
    
    print("\nSeeding complete!")
    print(f"\nMazda preset ID: {mazda_preset.id}")
    print("All existing vehicles have been assigned the Mazda preset as version 1.")
    print("\nNote: Users can modify these constants through the UI, which will create new versions.")


if __name__ == '__main__':
    # Initialize the app context
    from muts import create_app
    app = create_app()
    
    with app.app_context():
        main()
