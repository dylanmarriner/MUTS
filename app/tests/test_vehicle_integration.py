#!/usr/bin/env python3
"""
Vehicle Integration Smoke Tests
Validates that all supported vehicles are properly integrated
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from muts.models.database_models import db, User
from muts.models.vehicle_capabilities import VehicleCapabilityProfile
from muts.core.diagnostic_router import DiagnosticRouter, DiagnosticService, DiagnosticModule
from muts.data.seed_vw_constants import create_vw_golf_presets
from muts.data.seed_holden_constants import create_holden_wagon_presets
from muts.data.seed_alfa_constants import create_alfa_giulietta_presets
from muts.data.seed_mazda_constants import create_mazda_presets


class VehicleIntegrationTester:
    """Tests vehicle integration across the entire application"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.router = DiagnosticRouter(db_session)
        self.test_results = []
        self.passed = 0
        self.failed = 0
        
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log a test result"""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
            
        print(f"[{status}] {test_name}")
        if message:
            print(f"    {message}")
    
    def test_01_vehicle_constants_presets(self):
        """Test that all vehicle constants presets are properly defined"""
        print("\n=== Testing Vehicle Constants Presets ===")
        
        # Check VW presets
        vw_presets = create_vw_golf_presets()
        expected_vw_models = [
            "VW Golf Mk5 GTI Manual",
            "VW Golf Mk5 GTI DSG",
            "VW Golf Mk6 GTI Manual",
            "VW Golf Mk6 GTI DSG",
            "VW Golf Mk6 R DSG",
            "VW Golf Mk7 GTI Manual",
            "VW Golf Mk7 GTI DSG",
            "VW Golf Mk7.5 GTI DSG",
            "VW Golf Mk7 R DSG",
            "VW Golf Mk7 1.8T TSI"
        ]
        
        actual_vw_models = [p.name for p in vw_presets]
        for model in expected_vw_models:
            self.log_test(
                f"VW Preset: {model}",
                model in actual_vw_models,
                "Missing expected VW preset" if model not in actual_vw_models else ""
            )
        
        # Check Holden presets
        holden_presets = create_holden_wagon_presets()
        expected_holden_models = [
            "Holden Commodore VT Wagon V6",
            "Holden Commodore VX Wagon V6",
            "Holden Commodore VY Wagon V6",
            "Holden Commodore VZ Wagon V6",
            "Holden Commodore VE Wagon V6",
            "Holden Commodore VF Wagon V6"
        ]
        
        actual_holden_models = [p.name for p in holden_presets]
        for model in expected_holden_models:
            self.log_test(
                f"Holden Preset: {model}",
                model in actual_holden_models,
                "Missing expected Holden preset" if model not in actual_holden_models else ""
            )
        
        # Check Alfa Romeo presets
        alfa_presets = create_alfa_giulietta_presets()
        expected_alfa_models = [
            "Alfa Romeo Giulietta 1.4T MultiAir 6MT",
            "Alfa Romeo Giulietta 1.4T MultiAir TCT",
            "Alfa Romeo Giulietta 1.75TBi QV 6MT",
            "Alfa Romeo Giulietta 1.75TBi QV TCT",
            "Alfa Romeo Giulietta 2.0 JTDm 6MT",
            "Alfa Romeo Giulietta 2.0 JTDm TCT"
        ]
        
        actual_alfa_models = [p.name for p in alfa_presets]
        for model in expected_alfa_models:
            self.log_test(
                f"Alfa Preset: {model}",
                model in actual_alfa_models,
                "Missing expected Alfa preset" if model not in actual_alfa_models else ""
            )
        
        # Check Mazda presets
        mazda_presets = create_mazda_presets()
        expected_mazda_models = ["Mazdaspeed3 2011"]
        actual_mazda_models = [p.name for p in mazda_presets]
        for model in expected_mazda_models:
            self.log_test(
                f"Mazda Preset: {model}",
                model in actual_mazda_models,
                "Missing expected Mazda preset" if model not in actual_mazda_models else ""
            )
    
    def test_02_capability_profiles_exist(self):
        """Test that capability profiles exist for all vehicles"""
        print("\n=== Testing Capability Profiles ===")
        
        expected_profiles = [
            ("Volkswagen", "Golf", "Mk5/Mk6"),
            ("Volkswagen", "Golf", "Mk7/Mk7.5"),
            ("Holden", "Commodore", "Pre-VE"),
            ("Holden", "Commodore", "VE"),
            ("Holden", "Commodore", "VF"),
            ("Alfa Romeo", "Giulietta", "2012"),
            ("Mazda", "Mazdaspeed3", "2007-2013")
        ]
        
        for manufacturer, model, generation in expected_profiles:
            profile = self.db.query(VehicleCapabilityProfile).filter_by(
                manufacturer=manufacturer,
                model=model,
                generation=generation
            ).first()
            
            self.log_test(
                f"Capability Profile: {manufacturer} {model} {generation}",
                profile is not None,
                "No capability profile found" if profile is None else ""
            )
    
    def test_03_no_mock_data_paths(self):
        """Test that no mock data or hardcoded values exist"""
        print("\n=== Testing for Mock Data ===")
        
        # Check diagnostic router for manufacturer-specific routing
        from muts.core.diagnostic_router import DiagnosticRouter
        import inspect
        
        router_source = inspect.getsource(DiagnosticRouter)
        
        # Look for hardcoded vehicle references
        mock_indicators = [
            "Mazdaspeed3",
            "fake",
            "mock",
            "simulated",
            "placeholder",
            "random.randint",
            "test_data"
        ]
        
        for indicator in mock_indicators:
            found = indicator in router_source
            self.log_test(
                f"No Mock Data: {indicator}",
                not found,
                f"Found potential mock data: {indicator}" if found else ""
            )
    
    def test_04_unsupported_features_blocked(self):
        """Test that unsupported features are properly blocked"""
        print("\n=== Testing Unsupported Feature Blocking ===")
        
        # Create a mock vehicle object
        class MockVehicle:
            def __init__(self, manufacturer, model):
                self.id = "TEST_VIN"
                self.manufacturer = manufacturer
                self.model = model
                self.user_id = 1
        
        # Test VW Golf SRS (should be not supported)
        vw_vehicle = MockVehicle("Volkswagen", "Golf")
        is_supported, reason = self.router.is_module_supported(vw_vehicle, DiagnosticModule.SRS)
        
        self.log_test(
            "VW SRS Not Supported",
            not is_supported,
            f"SRS should not be supported: {reason}" if is_supported else f"Correctly blocked: {reason}"
        )
        
        # Test Holden BCM (should be not supported)
        holden_vehicle = MockVehicle("Holden", "Commodore")
        is_supported, reason = self.router.is_module_supported(holden_vehicle, DiagnosticModule.BCM)
        
        self.log_test(
            "Holden BCM Not Supported",
            not is_supported,
            f"BCM should not be supported: {reason}" if is_supported else f"Correctly blocked: {reason}"
        )
        
        # Test VW coding (should be not supported)
        is_supported, reason = self.router.is_service_supported(vw_vehicle, DiagnosticService.CODING)
        
        self.log_test(
            "VW Coding Not Supported",
            not is_supported,
            f"Coding should not be supported: {reason}" if is_supported else f"Correctly blocked: {reason}"
        )
    
    def test_05_interface_requirements(self):
        """Test that interface requirements are properly defined"""
        print("\n=== Testing Interface Requirements ===")
        
        profiles = self.db.query(VehicleCapabilityProfile).all()
        
        for profile in profiles:
            has_interface = profile.required_interface is not None
            has_protocol = profile.primary_protocol is not None
            
            self.log_test(
                f"Interface Defined: {profile.manufacturer} {profile.model}",
                has_interface and has_protocol,
                f"Missing interface or protocol" if not (has_interface and has_protocol) else ""
            )
    
    def test_06_dsg_awd_features(self):
        """Test DSG and AWD features are properly flagged"""
        print("\n=== Testing DSG/AWD Features ===")
        
        # VW Golf R should support AWD
        vw_r_profile = self.db.query(VehicleCapabilityProfile).filter_by(
            manufacturer="Volkswagen",
            model="Golf",
            variant="R"
        ).first()
        
        if vw_r_profile:
            self.log_test(
                "VW Golf R AWD Support",
                vw_r_profile.supports_awd_modeling,
                "AWD modeling should be supported for VW Golf R" if not vw_r_profile.supports_awd_modeling else ""
            )
        
        # VW DSG models should support DSG shifts
        vw_dsg_profiles = self.db.query(VehicleCapabilityProfile).filter_by(
            manufacturer="Volkswagen"
        ).filter(VehicleCapabilityProfile.transmission_type.like('%DSG%')).all()
        
        for profile in vw_dsg_profiles:
            self.log_test(
                f"VW DSG Support: {profile.generation}",
                profile.supports_dsg_shifts,
                "DSG shifts should be supported" if not profile.supports_dsg_shifts else ""
            )
        
        # Holden models should NOT support DSG
        holden_profiles = self.db.query(VehicleCapabilityProfile).filter_by(
            manufacturer="Holden"
        ).all()
        
        for profile in holden_profiles:
            self.log_test(
                f"Holden No DSG: {profile.generation}",
                not profile.supports_dsg_shifts,
                "DSG should not be supported for Holden" if profile.supports_dsg_shifts else ""
            )
    
    def test_07_confidence_scoring(self):
        """Test that confidence scores are reasonable"""
        print("\n=== Testing Confidence Scoring ===")
        
        profiles = self.db.query(VehicleCapabilityProfile).all()
        
        for profile in profiles:
            confidence_valid = 0 <= profile.confidence_level <= 100
            has_reason = profile.notes is not None and len(profile.notes.strip()) > 0
            
            self.log_test(
                f"Confidence Score: {profile.manufacturer} {profile.model}",
                confidence_valid and has_reason,
                f"Invalid confidence or missing notes" if not (confidence_valid and has_reason) else ""
            )
    
    def run_all_tests(self):
        """Run all smoke tests"""
        print("=" * 60)
        print("VEHICLE INTEGRATION SMOKE TESTS")
        print("=" * 60)
        print(f"Started at: {datetime.utcnow().isoformat()}")
        
        # Run all test suites
        self.test_01_vehicle_constants_presets()
        self.test_02_capability_profiles_exist()
        self.test_03_no_mock_data_paths()
        self.test_04_unsupported_features_blocked()
        self.test_05_interface_requirements()
        self.test_06_dsg_awd_features()
        self.test_07_confidence_scoring()
        
        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        if self.failed > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\nCompleted at: {datetime.utcnow().isoformat()}")
        
        # Save results to file
        results_file = os.path.join(os.path.dirname(__file__), 'integration_test_results.json')
        with open(results_file, 'w') as f:
            json.dump({
                'summary': {
                    'total': self.passed + self.failed,
                    'passed': self.passed,
                    'failed': self.failed,
                    'success_rate': (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        
        return self.failed == 0


def main():
    """Run the integration smoke tests"""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Create tester and run tests
        tester = VehicleIntegrationTester(db.session)
        success = tester.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
