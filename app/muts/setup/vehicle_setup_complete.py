#!/usr/bin/env python3
"""
Complete Vehicle Setup Script
Runs migration, seeds data, and verifies implementation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from muts import create_app, db
from muts.models.database_models import User
from muts.models.vehicle_profile import VehicleProfile
from muts.models.vehicle_constants import VehicleConstantsPreset, VehicleConstants
from muts.models.diagnostics_registry import template_registry
from muts.models.diagnostics_template import DiagnosticModule, ServiceStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """Run database migrations"""
    print("\n=== Database Setup ===")
    
    try:
        # Import migration runner
        from flask_migrate import upgrade as migrate_upgrade
        
        app = create_app()
        with app.app_context():
            # Run migrations
            print("Running database migrations...")
            migrate_upgrade()
            print("✅ Migrations completed")
            
            return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def seed_test_data():
    """Seed OEM constants and vehicle profiles"""
    print("\n=== Seeding Test Data ===")
    
    try:
        # Import seed functions
        from muts.data.seed_oem_constants_flask import create_all
        
        app = create_app()
        with app.app_context():
            # Create all data
            success = create_all()
            
            if success:
                print("✅ Test data seeded successfully")
                return True
            else:
                print("❌ Failed to seed test data")
                return False
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_implementation():
    """Verify the complete implementation"""
    print("\n=== Verification ===")
    
    app = create_app()
    with app.app_context():
        # Check 1: Vehicle profiles exist
        print("\n1. Checking vehicle profiles...")
        holden = VehicleProfile.query.filter_by(vin='6G1FA8E53FL100333').first()
        vw = VehicleProfile.query.filter_by(vin='WVWZZZ1KZBW232050').first()
        
        if holden and vw:
            print(f"✅ Holden VF: {holden.make} {holden.model} {holden.submodel}")
            print(f"✅ VW Golf: {vw.make} {vw.model} {vw.submodel}")
        else:
            print("❌ Vehicle profiles missing")
            return False
        
        # Check 2: Constants linked
        print("\n2. Checking constants linkage...")
        holden_constants = holden.get_constants()
        vw_constants = vw.get_constants()
        
        if holden_constants and vw_constants:
            print(f"✅ Holden constants: Version {holden_constants.version}")
            print(f"✅ VW constants: Version {vw_constants.version}")
        else:
            print("❌ Constants not linked")
            return False
        
        # Check 3: Capability templates
        print("\n3. Checking capability templates...")
        holden_template = template_registry.find_template('Holden', 'Commodore', 2015, 'Zeta')
        vw_template = template_registry.find_template('Volkswagen', 'Golf', 2011, 'A6')
        
        if holden_template and vw_template:
            print(f"✅ Holden template found: {holden_template.manufacturer} {holden_template.model}")
            print(f"✅ VW template found: {vw_template.manufacturer} {vw_template.model}")
            
            # Check specific modules
            holden_tcm = holden_template.get_module_capability(DiagnosticModule.TCM)
            vw_tcm = vw_template.get_module_capability(DiagnosticModule.TCM)
            
            print(f"   Holden TCM: {holden_tcm.status.value}")
            print(f"   VW TCM: {vw_tcm.status.value}")
        else:
            print("❌ Templates not found")
            return False
        
        # Check 4: DSG detection
        print("\n4. Checking DSG detection...")
        try:
            from muts.dyno.dsg_shift_detector import DSGShiftDetector
            
            detector = DSGShiftDetector()
            vw_preset = vw_constants.preset
            
            if vw_preset and vw_preset.transmission_type.value == 'DSG':
                print(f"✅ DSG detector ready: {len(vw_preset.get_gear_ratios())} gears")
            else:
                print("❌ DSG not configured for VW")
                return False
        except Exception as e:
            print(f"❌ DSG detection error: {e}")
            return False
        
        # Check 5: RWD for Holden
        print("\n5. Checking RWD drivetrain...")
        holden_preset = holden_constants.preset
        
        if holden_preset and holden_preset.drivetrain_type.value == 'RWD':
            print(f"✅ Holden RWD confirmed: {holden_preset.drivetrain_type.value}")
        else:
            print("❌ Holden not RWD")
            return False
        
        return True


def print_final_summary():
    """Print final implementation summary"""
    print("\n" + "="*60)
    print("IMPLEMENTATION SUMMARY")
    print("="*60)
    
    print("\n📋 Vehicle Profiles Created:")
    print("   1. Holden Commodore VF Evoke Wagon V6 3.0 6AT (2015)")
    print("      VIN: 6G1FA8E53FL100333")
    print("      Mass: 1780kg | Drivetrain: RWD | Transmission: 6AT")
    
    print("\n   2. Volkswagen Golf Mk6 TSI 90kW 1.4 7DSG (2011)")
    print("      VIN: WVWZZZ1KZBW232050")
    print("      Mass: 1295kg | Drivetrain: FWD | Transmission: DSG")
    
    print("\n✅ Key Features Implemented:")
    print("   • DB-backed vehicle profiles with VIN linkage")
    print("   • OEM constants packs with real specifications")
    print("   • Conservative diagnostics templates")
    print("   • Hybrid UI selector (Browse/My Vehicles)")
    print("   • DSG shift detection support")
    print("   • RWD drivetrain configuration")
    print("   • End-to-end smoke tests")
    
    print("\n📁 Files Created/Modified:")
    print("   /app/muts/models/vehicle_profile.py")
    print("   /app/muts/data/seed_oem_constants_flask.py")
    print("   /app/muts/api/vehicles.py")
    print("   /electron-app/vehicle_selector.html")
    print("   /app/muts/tests/vehicle_smoke_test.py")
    print("   + DB migration and styles")
    
    print("\n🔧 Next Steps:")
    print("   1. Run: flask db upgrade")
    print("   2. Run: flask shell < seed_oem_constants_flask.py")
    print("   3. Test UI vehicle selector")
    print("   4. Run smoke tests for validation")
    
    print("\n" + "="*60)
    print("✅ VEHICLE SUPPORT FULLY IMPLEMENTED")
    print("="*60 + "\n")


def main():
    """Run complete setup"""
    print("\n" + "="*60)
    print("COMPLETE VEHICLE SETUP")
    print("="*60)
    
    # Step 1: Database setup
    if not setup_database():
        print("\n❌ Setup failed at database migration")
        sys.exit(1)
    
    # Step 2: Seed data
    if not seed_test_data():
        print("\n❌ Setup failed at data seeding")
        sys.exit(1)
    
    # Step 3: Verify
    if not verify_implementation():
        print("\n❌ Setup failed verification")
        sys.exit(1)
    
    # Success
    print_final_summary()


if __name__ == '__main__':
    main()
