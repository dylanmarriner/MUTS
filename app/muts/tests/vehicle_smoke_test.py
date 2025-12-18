#!/usr/bin/env python3
"""
Vehicle Integration Smoke Test
Validates end-to-end support for Holden Commodore VF and VW Golf Mk6
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from muts.models.database_models import db, TransmissionType, DrivetrainType
from muts.models.vehicle_profile import VehicleProfile
from muts.models.vehicle_constants import VehicleConstantsPreset, VehicleConstants
from muts.models.diagnostics_registry import template_registry
from muts.models.diagnostics_template import DiagnosticModule, ServiceStatus
from muts.models.dyno_models import DynoRun
from sqlalchemy import text


class VehicleSmokeTest:
    """Comprehensive validation for vehicle implementations"""
    
    def __init__(self):
        self.test_results = []
        self.errors = []
    
    def log(self, test, passed, details=None):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test,
            'passed': passed,
            'details': details
        })
        print(f"{status}: {test}")
        if details:
            print(f"    {details}")
        if not passed:
            self.errors.append(test)
    
    def run_all_tests(self):
        """Run all smoke tests"""
        print("\n" + "="*60)
        print("VEHICLE INTEGRATION SMOKE TEST")
        print("="*60 + "\n")
        
        # Test 1: Database Models
        self.test_database_models()
        
        # Test 2: VIN Profiles
        self.test_vin_profiles()
        
        # Test 3: OEM Constants
        self.test_oem_constants()
        
        # Test 4: Capability Templates
        self.test_capability_templates()
        
        # Test 5: DSG Detection for VW
        self.test_dsg_detection()
        
        # Test 6: RWD for Holden
        self.test_rwd_drivetrain()
        
        # Test 7: Vehicle Switching
        self.test_vehicle_switching()
        
        # Test 8: Dyno Integration
        self.test_dyno_integration()
        
        # Summary
        self.print_summary()
        
        return len(self.errors) == 0
    
    def test_database_models(self):
        """Test database models exist and are properly configured"""
        print("\n--- Database Models ---")
        
        # Check VehicleProfile model
        try:
            # Test column types
            profile_columns = VehicleProfile.__table__.columns
            assert 'vin' in profile_columns
            assert str(profile_columns['vin'].type) == 'VARCHAR(17)'
            assert 'plate' in profile_columns
            assert 'engine_number' in profile_columns
            
            self.log("VehicleProfile model structure", True)
        except Exception as e:
            self.log("VehicleProfile model structure", False, str(e))
        
        # Check foreign key relationships
        try:
            assert hasattr(VehicleProfile, 'vehicle')
            assert hasattr(VehicleProfile, 'constants_preset')
            assert hasattr(VehicleProfile, 'constants_versions')
            
            self.log("VehicleProfile relationships", True)
        except Exception as e:
            self.log("VehicleProfile relationships", False, str(e))
    
    def test_vin_profiles(self):
        """Test VIN profiles exist in database"""
        print("\n--- VIN Profiles ---")
        
        test_vins = {
            '6G1FA8E53FL100333': 'Holden Commodore VF',
            'WVWZZZ1KZBW232050': 'VW Golf Mk6'
        }
        
        for vin, expected in test_vins.items():
            try:
                profile = VehicleProfile.query.filter_by(vin=vin).first()
                if profile:
                    assert expected in profile.model
                    assert profile.plate in ['JBG175', 'GBF28']
                    assert profile.engine_number in ['LFW142510158', 'CAX767625']
                    
                    self.log(f"VIN {vin[-4:]} profile exists", True, 
                            f"{profile.make} {profile.model}")
                else:
                    self.log(f"VIN {vin[-4:]} profile exists", False, "Not found")
            except Exception as e:
                self.log(f"VIN {vin[-4:]} profile exists", False, str(e))
    
    def test_oem_constants(self):
        """Test OEM constants are properly configured"""
        print("\n--- OEM Constants ---")
        
        # Test Holden constants
        try:
            holden_preset = VehicleConstantsPreset.query.filter_by(
                manufacturer='Holden',
                model='Commodore',
                generation='VF'
            ).first()
            
            if holden_preset:
                assert holden_preset.vehicle_mass == 1780
                assert holden_preset.drivetrain_type == DrivetrainType.RWD
                assert holden_preset.transmission_type == TransmissionType.TORQUE_CONVERTER
                assert len(holden_preset.get_gear_ratios()) == 6
                
                self.log("Holden VF OEM constants", True,
                        f"Mass: {holden_preset.vehicle_mass}kg, Drivetrain: {holden_preset.drivetrain_type.value}")
            else:
                self.log("Holden VF OEM constants", False, "Preset not found")
        except Exception as e:
            self.log("Holden VF OEM constants", False, str(e))
        
        # Test VW constants
        try:
            vw_preset = VehicleConstantsPreset.query.filter_by(
                manufacturer='Volkswagen',
                model='Golf',
                generation='Mk6'
            ).first()
            
            if vw_preset:
                assert vw_preset.vehicle_mass == 1295
                assert vw_preset.drivetrain_type == DrivetrainType.FWD
                assert vw_preset.transmission_type == TransmissionType.DSG
                assert len(vw_preset.get_gear_ratios()) == 7
                
                self.log("VW Golf Mk6 OEM constants", True,
                        f"Mass: {vw_preset.vehicle_mass}kg, Transmission: {vw_preset.transmission_type.value}")
            else:
                self.log("VW Golf Mk6 OEM constants", False, "Preset not found")
        except Exception as e:
            self.log("VW Golf Mk6 OEM constants", False, str(e))
    
    def test_capability_templates(self):
        """Test diagnostics capability templates"""
        print("\n--- Capability Templates ---")
        
        # Test Holden template
        try:
            holden_template = template_registry.find_template(
                'Holden', 'Commodore', 2015, 'Zeta'
            )
            
            if holden_template:
                # Check modules
                engine_cap = holden_template.get_module_capability(DiagnosticModule.ENGINE)
                assert engine_cap.status == ServiceStatus.SUPPORTED
                
                tcm_cap = holden_template.get_module_capability(DiagnosticModule.TCM)
                assert tcm_cap.status == ServiceStatus.SUPPORTED
                
                cluster_cap = holden_template.get_module_capability(DiagnosticModule.CLUSTER)
                assert cluster_cap.status == ServiceStatus.UNKNOWN
                
                self.log("Holden VF capability template", True,
                        f"Engine: {engine_cap.status.value}, TCM: {tcm_cap.status.value}")
            else:
                self.log("Holden VF capability template", False, "Template not found")
        except Exception as e:
            self.log("Holden VF capability template", False, str(e))
        
        # Test VW template
        try:
            vw_template = template_registry.find_template(
                'Volkswagen', 'Golf', 2011, 'A6'
            )
            
            if vw_template:
                # Check modules
                engine_cap = vw_template.get_module_capability(DiagnosticModule.ENGINE)
                assert engine_cap.status == ServiceStatus.SUPPORTED
                
                tcm_cap = vw_template.get_module_capability(DiagnosticModule.TCM)
                assert tcm_cap.status == ServiceStatus.SUPPORTED
                
                cluster_cap = vw_template.get_module_capability(DiagnosticModule.CLUSTER)
                assert cluster_cap.status == ServiceStatus.NOT_SUPPORTED
                
                self.log("VW Golf Mk6 capability template", True,
                        f"Engine: {engine_cap.status.value}, TCM: {tcm_cap.status.value}")
            else:
                self.log("VW Golf Mk6 capability template", False, "Template not found")
        except Exception as e:
            self.log("VW Golf Mk6 capability template", False, str(e))
    
    def test_dsg_detection(self):
        """Test DSG shift detection is available for VW"""
        print("\n--- DSG Shift Detection ---")
        
        try:
            # Check if DSG detector exists
            from muts.dyno.dsg_shift_detector import DSGShiftDetector
            
            detector = DSGShiftDetector()
            assert detector.ratio_change_threshold > 0
            assert detector.guard_window > 0
            
            # Check VW constants have DSG transmission
            vw_preset = VehicleConstantsPreset.query.filter_by(
                manufacturer='Volkswagen',
                model='Golf',
                generation='Mk6'
            ).first()
            
            if vw_preset:
                assert vw_preset.transmission_type == TransmissionType.DSG
                
                self.log("DSG shift detection for VW", True,
                        f"Detector initialized, DSG confirmed in constants")
            else:
                self.log("DSG shift detection for VW", False, "VW preset not found")
        except Exception as e:
            self.log("DSG shift detection for VW", False, str(e))
    
    def test_rwd_drivetrain(self):
        """Test RWD drivetrain for Holden"""
        print("\n--- RWD Drivetrain ---")
        
        try:
            holden_preset = VehicleConstantsPreset.query.filter_by(
                manufacturer='Holden',
                model='Commodore',
                generation='VF'
            ).first()
            
            if holden_preset:
                assert holden_preset.drivetrain_type == DrivetrainType.RWD
                
                # Check no AWD torque split values
                assert holden_preset.awd_torque_split_front is None
                assert holden_preset.awd_torque_split_rear is None
                
                self.log("Holden VF RWD drivetrain", True,
                        f"Drivetrain: {holden_preset.drivetrain_type.value}")
            else:
                self.log("Holden VF RWD drivetrain", False, "Holden preset not found")
        except Exception as e:
            self.log("Holden VF RWD drivetrain", False, str(e))
    
    def test_vehicle_switching(self):
        """Test switching between vehicles doesn't leak state"""
        print("\n--- Vehicle Switching ---")
        
        try:
            # Get both vehicles
            holden = VehicleProfile.query.filter_by(vin='6G1FA8E53FL100333').first()
            vw = VehicleProfile.query.filter_by(vin='WVWZZZ1KZBW232050').first()
            
            if holden and vw:
                # Load Holden constants
                holden_constants = holden.get_constants()
                holden_effective = holden_constants.get_effective_constants()
                
                # Load VW constants
                vw_constants = vw.get_constants()
                vw_effective = vw_constants.get_effective_constants()
                
                # Verify no leakage
                assert holden_effective['vehicle_mass'] != vw_effective['vehicle_mass']
                assert holden_effective['drivetrain_type'] != vw_effective['drivetrain_type']
                assert holden_effective['transmission_type'] != vw_effective['transmission_type']
                
                self.log("Vehicle switching isolation", True,
                        "Constants differ between vehicles")
            else:
                self.log("Vehicle switching isolation", False, "Vehicles not found")
        except Exception as e:
            self.log("Vehicle switching isolation", False, str(e))
    
    def test_dyno_integration(self):
        """Test dyno integration with constants"""
        print("\n--- Dyno Integration ---")
        
        try:
            # Check DynoRun model references vehicle_constants
            dyno_columns = DynoRun.__table__.columns
            assert 'vehicle_constants_id' in dyno_columns
            
            # Verify it's a foreign key
            assert str(dyno_columns['vehicle_constants_id'].foreign_keys).pop().column.name == 'vehicle_constants.id'
            
            self.log("Dyno constants reference", True,
                    "DynoRun references vehicle_constants_id")
            
            # Test confidence scoring
            holden_constants = VehicleConstants.query.filter_by(
                vehicle_id='6G1FA8E53FL100333'
            ).first()
            
            if holden_constants:
                confidence = holden_constants.get_confidence_score()
                level = holden_constants.get_confidence_level()
                
                assert confidence >= 0 and confidence <= 100
                assert level in ['HIGH', 'MEDIUM', 'LOW']
                
                self.log("Constants confidence scoring", True,
                        f"Score: {confidence}, Level: {level}")
            else:
                self.log("Constants confidence scoring", False, "No constants found")
        except Exception as e:
            self.log("Dyno integration", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("SMOKE TEST SUMMARY")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = len(self.errors)
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if self.errors:
            print("\nFailed Tests:")
            for error in self.errors:
                print(f"  ❌ {error}")
        
        print("\n" + "="*60)
        
        if failed == 0:
            print("✅ ALL TESTS PASSED - Vehicles properly integrated!")
        else:
            print("❌ SOME TESTS FAILED - Fix issues before proceeding")
        
        print("="*60 + "\n")


def main():
    """Run smoke tests"""
    # Create app context
    from muts import create_app
    app = create_app()
    
    with app.app_context():
        # Run tests
        tester = VehicleSmokeTest()
        success = tester.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
