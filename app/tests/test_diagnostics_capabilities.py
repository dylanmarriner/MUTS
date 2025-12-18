#!/usr/bin/env python3
"""
Diagnostics Capability Template Integration Tests
Verifies that capability enforcement works correctly across all vehicles
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from muts.models.database_models import db, User, Vehicle
from muts.models.diagnostics_registry import template_registry
from muts.models.diagnostics_template import DiagnosticModule, DiagnosticService, ServiceStatus
from muts.core.diagnostic_router import DiagnosticRouter


class DiagnosticsCapabilityTester:
    """Tests diagnostics capability enforcement"""
    
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
    
    def test_01_template_registry_loaded(self):
        """Test that all manufacturer templates are loaded"""
        print("\n=== Testing Template Registry ===")
        
        templates = template_registry.get_all_templates()
        
        # Check for required manufacturers
        manufacturers = set()
        for template in templates:
            manufacturers.add(template.manufacturer)
        
        expected_manufacturers = {"Alfa Romeo", "Volkswagen", "Holden"}
        for manufacturer in expected_manufacturers:
            self.log_test(
                f"Registry has {manufacturer} templates",
                manufacturer in manufacturers,
                f"Missing {manufacturer} templates"
            )
        
        # Check specific templates
        expected_templates = [
            ("Alfa Romeo", "Giulietta", "2012"),
            ("Volkswagen", "Golf", "Mk5/Mk6"),
            ("Volkswagen", "Golf", "Mk7/Mk7.5"),
            ("Holden", "Commodore", "VT/VX/VY/VZ"),
            ("Holden", "Commodore", "VE/VF")
        ]
        
        for manufacturer, model, generation in expected_templates:
            found = False
            for template in templates:
                if (template.manufacturer == manufacturer and 
                    template.model == model and 
                    template.generation == generation):
                    found = True
                    break
            
            self.log_test(
                f"Template found: {manufacturer} {model} {generation}",
                found,
                "Expected template not found"
            )
    
    def test_02_alfa_giulietta_capabilities(self):
        """Test Alfa Romeo Giulietta specific capabilities"""
        print("\n=== Testing Alfa Romeo Giulietta Capabilities ===")
        
        # Create mock Alfa vehicle
        alfa_vehicle = self._create_mock_vehicle(
            manufacturer="Alfa Romeo",
            model="Giulietta",
            generation="2012",
            year=2012,
            transmission="TCT"
        )
        
        # Get template
        template = self.router.get_vehicle_template(alfa_vehicle)
        self.log_test(
            "Alfa template found",
            template is not None,
            "No template found for Alfa Giulietta"
        )
        
        if template:
            # Test Engine ECU capabilities
            self.log_test(
                "Engine DTC Read supported",
                template.is_service_supported(DiagnosticModule.ENGINE, DiagnosticService.READ_DTCS),
                "Engine DTC reading should be supported"
            )
            
            self.log_test(
                "Engine Live Data limited",
                template.get_service_status(DiagnosticModule.ENGINE, DiagnosticService.LIVE_DATA).status == ServiceStatus.LIMITED,
                "Engine live data should be limited"
            )
            
            self.log_test(
                "Engine Coding not supported",
                not template.is_service_supported(DiagnosticModule.ENGINE, DiagnosticService.CODING),
                "Engine coding should not be supported"
            )
            
            # Test TCT capabilities
            self.log_test(
                "TCT DTC Read supported",
                template.is_service_supported(DiagnosticModule.TCM, DiagnosticService.READ_DTCS),
                "TCT DTC reading should be supported"
            )
            
            self.log_test(
                "TCT Service Functions not supported",
                not template.is_service_supported(DiagnosticModule.TCM, DiagnosticService.SERVICE_FUNCTIONS),
                "TCT service functions should not be supported"
            )
            
            # Test SRS capabilities
            self.log_test(
                "SRS not supported",
                not template.is_service_supported(DiagnosticModule.SRS, DiagnosticService.READ_DTCS),
                "SRS should not be supported without Alfa Examiner"
            )
            
            # Test BCM capabilities
            self.log_test(
                "BCM not supported",
                not template.is_service_supported(DiagnosticModule.BCM, DiagnosticService.READ_DTCS),
                "BCM should not be supported without manufacturer access"
            )
    
    def test_03_vw_golf_capabilities(self):
        """Test Volkswagen Golf specific capabilities"""
        print("\n=== Testing Volkswagen Golf Capabilities ===")
        
        # Test PQ35 platform
        vw_pq35 = self._create_mock_vehicle(
            manufacturer="Volkswagen",
            model="Golf",
            generation="Mk5/Mk6",
            year=2008,
            transmission="DSG"
        )
        
        template = self.router.get_vehicle_template(vw_pq35)
        self.log_test(
            "VW PQ35 template found",
            template is not None,
            "No template found for VW Golf PQ35"
        )
        
        if template:
            # Test DSG capabilities
            self.log_test(
                "DSG DTC Read supported",
                template.is_service_supported(DiagnosticModule.TCM, DiagnosticService.READ_DTCS),
                "DSG DTC reading should be supported"
            )
            
            self.log_test(
                "DSG Coding not supported",
                not template.is_service_supported(DiagnosticModule.TCM, DiagnosticService.CODING),
                "DSG coding should not be supported without VCDS"
            )
        
        # Test MQB platform
        vw_mqb = self._create_mock_vehicle(
            manufacturer="Volkswagen",
            model="Golf",
            generation="Mk7/Mk7.5",
            year=2015,
            transmission="DSG"
        )
        
        template = self.router.get_vehicle_template(vw_mqb)
        self.log_test(
            "VW MQB template found",
            template is not None,
            "No template found for VW Golf MQB"
        )
        
        if template:
            # Test protocol differences
            self.log_test(
                "MQB uses UDS protocol",
                "UDS" in template.modules[DiagnosticModule.ENGINE].protocol_info,
                "MQB should use UDS protocol"
            )
    
    def test_04_holden_commodore_capabilities(self):
        """Test Holden Commodore specific capabilities"""
        print("\n=== Testing Holden Commodore Capabilities ===")
        
        # Test VT-VZ (pre-CAN)
        holden_early = self._create_mock_vehicle(
            manufacturer="Holden",
            model="Commodore",
            generation="VT/VX/VY/VZ",
            year=2004,
            transmission="Auto"
        )
        
        template = self.router.get_vehicle_template(holden_early)
        self.log_test(
            "Holden early template found",
            template is not None,
            "No template found for Holden VT-VZ"
        )
        
        if template:
            # Test VPW protocol
            self.log_test(
                "VT-VZ uses VPW protocol",
                "VPW" in template.modules[DiagnosticModule.ENGINE].protocol_info,
                "VT-VZ should use VPW protocol"
            )
            
            self.log_test(
                "Freeze Frame not supported on VPW",
                not template.is_service_supported(DiagnosticModule.ENGINE, DiagnosticService.FREEZE_FRAME),
                "Freeze frame should not be supported on VPW"
            )
        
        # Test VE-VF (CAN)
        holden_can = self._create_mock_vehicle(
            manufacturer="Holden",
            model="Commodore",
            generation="VE/VF",
            year=2012,
            transmission="Auto"
        )
        
        template = self.router.get_vehicle_template(holden_can)
        self.log_test(
            "Holden CAN template found",
            template is not None,
            "No template found for Holden VE-VF"
        )
        
        if template:
            # Test GMLAN protocol
            self.log_test(
                "VE-VF uses GMLAN protocol",
                "GMLAN" in template.modules[DiagnosticModule.ENGINE].protocol_info,
                "VE-VF should use GMLAN protocol"
            )
            
            self.log_test(
                "Freeze Frame supported on CAN",
                template.is_service_supported(DiagnosticModule.ENGINE, DiagnosticService.FREEZE_FRAME),
                "Freeze frame should be supported on CAN"
            )
    
    def test_05_service_level_enforcement(self):
        """Test that DiagnosticRouter enforces service-level capabilities"""
        print("\n=== Testing Service Level Enforcement ===")
        
        # Test Alfa Romeo - SRS should be blocked
        alfa_vehicle = self._create_mock_vehicle(
            manufacturer="Alfa Romeo",
            model="Giulietta",
            generation="2012"
        )
        
        # Check SRS DTC read
        is_supported, reason = self.router.is_service_supported(
            alfa_vehicle, DiagnosticModule.SRS, DiagnosticService.READ_DTCS
        )
        
        self.log_test(
            "SRS DTC Read blocked for Alfa",
            not is_supported,
            f"SRS should be blocked: {reason}"
        )
        
        # Check Engine DTC read
        is_supported, reason = self.router.is_service_supported(
            alfa_vehicle, DiagnosticModule.ENGINE, DiagnosticService.READ_DTCS
        )
        
        self.log_test(
            "Engine DTC Read allowed for Alfa",
            is_supported,
            f"Engine DTC should be supported: {reason}"
        )
        
        # Test VW - DSG coding should be blocked
        vw_vehicle = self._create_mock_vehicle(
            manufacturer="Volkswagen",
            model="Golf",
            generation="Mk7/Mk7.5",
            transmission="DSG"
        )
        
        is_supported, reason = self.router.is_service_supported(
            vw_vehicle, DiagnosticModule.TCM, DiagnosticService.CODING
        )
        
        self.log_test(
            "DSG Coding blocked for VW",
            not is_supported,
            f"DSG coding should be blocked: {reason}"
        )
    
    def test_06_no_capability_leakage(self):
        """Test that switching vehicles doesn't leak capabilities"""
        print("\n=== Testing No Capability Leakage ===")
        
        # Start with VW
        vw_vehicle = self._create_mock_vehicle(
            manufacturer="Volkswagen",
            model="Golf",
            generation="Mk7/Mk7.5"
        )
        
        vw_template = self.router.get_vehicle_template(vw_vehicle)
        
        # Switch to Alfa
        alfa_vehicle = self._create_mock_vehicle(
            manufacturer="Alfa Romeo",
            model="Giulietta",
            generation="2012"
        )
        
        alfa_template = self.router.get_vehicle_template(alfa_vehicle)
        
        # Switch to Holden
        holden_vehicle = self._create_mock_vehicle(
            manufacturer="Holden",
            model="Commodore",
            generation="VE/VF"
        )
        
        holden_template = self.router.get_vehicle_template(holden_vehicle)
        
        # Verify templates are different
        self.log_test(
            "VW and Alfa templates differ",
            vw_template != alfa_template,
            "Templates should be different for different manufacturers"
        )
        
        self.log_test(
            "Alfa and Holden templates differ",
            alfa_template != holden_template,
            "Templates should be different for different manufacturers"
        )
        
        # Verify specific capability differences
        vw_dsg_supported = vw_template.is_service_supported(
            DiagnosticModule.TCM, DiagnosticService.READ_DTCS
        )
        alfa_dsg_supported = alfa_template.is_service_supported(
            DiagnosticModule.TCM, DiagnosticService.READ_DTCS
        )
        
        self.log_test(
            "DSG capabilities don't leak",
            vw_dsg_supported != alfa_dsg_supported,
            "DSG capabilities should differ between vehicles"
        )
    
    def test_07_unknown_vehicle_fallback(self):
        """Test behavior with unknown vehicles"""
        print("\n=== Testing Unknown Vehicle Fallback ===")
        
        unknown_vehicle = self._create_mock_vehicle(
            manufacturer="Unknown",
            model="Unknown",
            generation="Unknown"
        )
        
        template = self.router.get_vehicle_template(unknown_vehicle)
        self.log_test(
            "Unknown vehicle has no template",
            template is None,
            "Unknown vehicles should not have templates"
        )
        
        # Should fallback to legacy system or return not supported
        is_supported, reason = self.router.is_service_supported(
            unknown_vehicle, DiagnosticModule.ENGINE, DiagnosticService.READ_DTCS
        )
        
        self.log_test(
            "Unknown vehicle services not supported",
            not is_supported,
            f"Unknown vehicles should not support services: {reason}"
        )
    
    def _create_mock_vehicle(self, **kwargs):
        """Create a mock vehicle object for testing"""
        class MockVehicle:
            def __init__(self, **kwargs):
                self.manufacturer = kwargs.get('manufacturer', 'Unknown')
                self.model = kwargs.get('model', 'Unknown')
                self.generation = kwargs.get('generation', None)
                self.year = kwargs.get('year', None)
                self.engine = kwargs.get('engine', None)
                self.transmission = kwargs.get('transmission', None)
        
        return MockVehicle(**kwargs)
    
    def run_all_tests(self):
        """Run all diagnostics capability tests"""
        print("=" * 60)
        print("DIAGNOSTICS CAPABILITY INTEGRATION TESTS")
        print("=" * 60)
        print(f"Started at: {datetime.utcnow().isoformat()}")
        
        # Run all test suites
        self.test_01_template_registry_loaded()
        self.test_02_alfa_giulietta_capabilities()
        self.test_03_vw_golf_capabilities()
        self.test_04_holden_commodore_capabilities()
        self.test_05_service_level_enforcement()
        self.test_06_no_capability_leakage()
        self.test_07_unknown_vehicle_fallback()
        
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
        results_file = os.path.join(os.path.dirname(__file__), 'diagnostics_capability_test_results.json')
        import json
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
    """Run the diagnostics capability integration tests"""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Create tester and run tests
        tester = DiagnosticsCapabilityTester(db.session)
        success = tester.run_all_tests()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
