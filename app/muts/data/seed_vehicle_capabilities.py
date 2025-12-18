#!/usr/bin/env python3
"""
Seed Vehicle Capability Profiles
Populates database with capability profiles for all supported vehicles
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from muts.models.database_models import db, User
from muts.models.vehicle_capabilities import (
    VehicleCapabilityProfile,
    create_vw_golf_capabilities,
    create_holden_commodore_capabilities,
    create_alfa_giulietta_capabilities,
    create_mazda_capabilities
)


def seed_vehicle_capabilities():
    """Seed all vehicle capability profiles"""
    
    print("Seeding vehicle capability profiles...")
    
    # Get or create system user
    user = db.session.query(User).filter_by(username="system").first()
    if not user:
        user = User(
            username="system",
            email="system@muts.local",
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
    
    # Clear existing capabilities
    db.session.query(VehicleCapabilityProfile).delete()
    print("Cleared existing capability profiles")
    
    # Create VW Golf profiles
    vw_profiles = create_vw_golf_capabilities()
    for profile in vw_profiles:
        db.session.add(profile)
    print(f"Added {len(vw_profiles)} VW Golf capability profiles")
    
    # Create Holden Commodore profiles
    holden_profiles = create_holden_commodore_capabilities()
    for profile in holden_profiles:
        db.session.add(profile)
    print(f"Added {len(holden_profiles)} Holden Commodore capability profiles")
    
    # Create Alfa Romeo profiles
    alfa_profiles = create_alfa_giulietta_capabilities()
    for profile in alfa_profiles:
        db.session.add(profile)
    print(f"Added {len(alfa_profiles)} Alfa Romeo Giulietta capability profiles")
    
    # Create Mazda profiles
    mazda_profiles = create_mazda_capabilities()
    for profile in mazda_profiles:
        db.session.add(profile)
    print(f"Added {len(mazda_profiles)} Mazda capability profiles")
    
    # Commit all changes
    db.session.commit()
    print("Vehicle capability profiles seeded successfully!")
    
    # Print summary
    print("\n=== VEHICLE CAPABILITY SUMMARY ===")
    all_profiles = db.session.query(VehicleCapabilityProfile).all()
    
    for profile in all_profiles:
        print(f"\n{profile.manufacturer} {profile.model} ({profile.generation})")
        print(f"  Platform: {profile.platform}")
        print(f"  Interface: {profile.required_interface}")
        print(f"  Protocol: {profile.primary_protocol}")
        print(f"  Virtual Dyno: {'Yes' if profile.supports_virtual_dyno else 'No'}")
        print(f"  DSG Shifts: {'Yes' if profile.supports_dsg_shifts else 'No'}")
        print(f"  AWD Modeling: {'Yes' if profile.supports_awd_modeling else 'No'}")
        print(f"  Confidence: {profile.confidence_level}%")


if __name__ == "__main__":
    from app import create_app
    
    app = create_app()
    with app.app_context():
        seed_vehicle_capabilities()
