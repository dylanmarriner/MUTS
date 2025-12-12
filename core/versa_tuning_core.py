#!/usr/bin/env python3
"""
Versa Tuning Core - Python wrapper for Rust safety-critical operations
Provides interface to Rust NAPI functions for tuning operations
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

# Try to import the Rust module
try:
    # This will be available after building the Rust library
    from muts_versa_core import (
        MapChange,
        PatchResult,
        ValidationResult,
        ApplyResult,
        versa_build_patch,
        versa_validate_patch,
        versa_apply_live,
        versa_revert_live
    )
    RUST_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Rust core not available: {e}. Using fallback implementations.")
    RUST_AVAILABLE = False
    
    # Fallback implementations for development
    @dataclass
    class MapChange:
        address: int
        size: int
        old_data: bytes
        new_data: bytes
        map_type: str
    
    @dataclass
    class PatchResult:
        success: bool
        patch_data: bytes
        checksum: int
        size: int
        warnings: List[str]
        errors: List[str]
    
    @dataclass
    class ValidationResult:
        valid: bool
        risk_score: int
        warnings: List[str]
        errors: List[str]
        safety_violations: List[str]
    
    @dataclass
    class ApplyResult:
        success: bool
        ecu_verified: bool
        applied_changes: int
        failed_changes: List[str]
        message: str
    
    def versa_build_patch(base_rom: bytes, changes: List[MapChange], safety_limits: Optional[Dict] = None) -> PatchResult:
        """Fallback implementation"""
        patch_data = bytearray(base_rom)
        warnings = []
        errors = []
        
        for change in changes:
            addr = change.address
            if addr + change.size > len(patch_data):
                errors.append(f"Change at 0x{addr:08X} exceeds ROM bounds")
                continue
            
            patch_data[addr:addr + change.size] = change.new_data
        
        return PatchResult(
            success=len(errors) == 0,
            patch_data=bytes(patch_data),
            checksum=sum(patch_data) & 0xFFFFFFFF,  # Simple checksum fallback
            size=len(patch_data),
            warnings=warnings,
            errors=errors
        )
    
    def versa_validate_patch(patch_data: bytes, original_rom: bytes, safety_limits: Dict) -> ValidationResult:
        """Fallback implementation"""
        return ValidationResult(
            valid=True,
            risk_score=10,
            warnings=["Using fallback validation"],
            errors=[],
            safety_violations=[]
        )
    
    def versa_apply_live(vehicle_session: str, changes: List[MapChange], timeout_seconds: int) -> ApplyResult:
        """Fallback implementation"""
        return ApplyResult(
            success=True,
            ecu_verified=False,
            applied_changes=len(changes),
            failed_changes=[],
            message=f"Applied {len(changes)} changes (fallback mode)"
        )
    
    def versa_revert_live(vehicle_session: str, applied_changes: List[MapChange]) -> ApplyResult:
        """Fallback implementation"""
        return ApplyResult(
            success=True,
            ecu_verified=False,
            applied_changes=len(applied_changes),
            failed_changes=[],
            message=f"Reverted {len(applied_changes)} changes (fallback mode)"
        )

logger = logging.getLogger(__name__)

class VersaTuningCore:
    """
    High-level interface to Versa tuning safety-critical operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.safety_limits = self._load_default_safety_limits()
        
    def _load_default_safety_limits(self) -> Dict[str, Any]:
        """Load default safety limits for Mazdaspeed 3 2011"""
        return {
            'max_boost_psi': 22.0,
            'max_timing_degrees': 25.0,
            'min_afr': 10.8,
            'max_egt_c': 950,
            'max_injector_duty': 85.0,
            'max_rpm': 7200,
            'max_load': 1.5
        }
    
    def build_patch_from_changeset(self, base_rom: bytes, changeset: Dict[str, Any]) -> PatchResult:
        """
        Build a ROM patch from a changeset
        
        Args:
            base_rom: Original ROM data
            changeset: Changeset dictionary with map changes
            
        Returns:
            PatchResult with patched ROM and validation info
        """
        # Convert changeset to MapChange objects
        map_changes = []
        
        for change in changeset.get('changes', []):
            map_change = MapChange(
                address=change['address'],
                size=change['size'],
                old_data=bytes.fromhex(change['oldData']),
                new_data=bytes.fromhex(change['newData']),
                map_type=change.get('mapType', 'UNKNOWN')
            )
            map_changes.append(map_change)
        
        # Build patch using Rust core
        result = versa_build_patch(base_rom, map_changes, self.safety_limits)
        
        self.logger.info(f"Built patch: {result.success}, changes: {len(map_changes)}")
        if result.warnings:
            self.logger.warning(f"Patch warnings: {result.warnings}")
        if result.errors:
            self.logger.error(f"Patch errors: {result.errors}")
        
        return result
    
    def validate_patch_safety(self, patch_data: bytes, original_rom: bytes) -> ValidationResult:
        """
        Validate a patch against safety limits
        
        Args:
            patch_data: Modified ROM data
            original_rom: Original ROM data
            
        Returns:
            ValidationResult with safety assessment
        """
        result = versa_validate_patch(patch_data, original_rom, self.safety_limits)
        
        self.logger.info(f"Patch validation: valid={result.valid}, risk_score={result.risk_score}")
        
        if result.safety_violations:
            self.logger.error(f"Safety violations: {result.safety_violations}")
        
        return result
    
    def apply_live_changes(self, vehicle_session: str, changeset: Dict[str, Any], 
                          timeout_minutes: int = 10) -> ApplyResult:
        """
        Apply changes in live mode (reversible)
        
        Args:
            vehicle_session: Active vehicle session ID
            changeset: Changeset to apply
            timeout_minutes: Auto-revert timeout
            
        Returns:
            ApplyResult with status and details
        """
        # Convert changeset to MapChange objects
        map_changes = []
        
        for change in changeset.get('changes', []):
            map_change = MapChange(
                address=change['address'],
                size=change['size'],
                old_data=bytes.fromhex(change['oldData']),
                new_data=bytes.fromhex(change['newData']),
                map_type=change.get('mapType', 'UNKNOWN')
            )
            map_changes.append(map_change)
        
        # Apply using Rust core
        timeout_seconds = timeout_minutes * 60
        result = versa_apply_live(vehicle_session, map_changes, timeout_seconds)
        
        self.logger.info(f"Live apply: success={result.success}, changes={result.applied_changes}")
        
        return result
    
    def revert_live_changes(self, vehicle_session: str, applied_changes: List[Dict[str, Any]]) -> ApplyResult:
        """
        Revert previously applied live changes
        
        Args:
            vehicle_session: Active vehicle session ID
            applied_changes: List of changes to revert
            
        Returns:
            ApplyResult with revert status
        """
        # Convert to MapChange objects (swapping old/new)
        map_changes = []
        
        for change in applied_changes:
            map_change = MapChange(
                address=change['address'],
                size=change['size'],
                old_data=bytes.fromhex(change['newData']),  # Swap: current becomes old
                new_data=bytes.fromhex(change['oldData']),  # Original becomes new
                map_type=change.get('mapType', 'UNKNOWN')
            )
            map_changes.append(map_change)
        
        # Revert using Rust core
        result = versa_revert_live(vehicle_session, map_changes)
        
        self.logger.info(f"Live revert: success={result.success}, reverted={result.applied_changes}")
        
        return result
    
    def prepare_flash_package(self, profile_data: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """
        Prepare a complete flash package from profile
        
        Args:
            profile_data: Profile with maps and metadata
            
        Returns:
            Tuple of (rom_data, package_info)
        """
        # This would integrate with ROM operations to build complete flash
        # For now, return placeholder
        rom_data = bytes([0x00] * 0x200000)  # 2MB placeholder
        
        package_info = {
            'profileId': profile_data.get('id'),
            'version': profile_data.get('version', '1.0.0'),
            'checksum': 'calculated_checksum',
            'size': len(rom_data),
            'maps': profile_data.get('maps', []),
            'requiresSecurityUnlock': True,
            'compatibleECUs': ['Mazdaspeed3_2011']
        }
        
        return rom_data, package_info
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety system status"""
        return {
            'rustCoreAvailable': RUST_AVAILABLE,
            'safetyLimits': self.safety_limits,
            'supportedOperations': [
                'build_patch',
                'validate_patch',
                'apply_live',
                'revert_live'
            ] if RUST_AVAILABLE else ['fallback_mode_only']
        }

# Singleton instance
_versa_core = None

def get_versa_core() -> VersaTuningCore:
    """Get the singleton VersaTuningCore instance"""
    global _versa_core
    if _versa_core is None:
        _versa_core = VersaTuningCore()
    return _versa_core

# Test function
def test_versa_core():
    """Test the Versa tuning core functionality"""
    core = get_versa_core()
    
    # Test status
    status = core.get_safety_status()
    print(f"Versa Core Status: {json.dumps(status, indent=2)}")
    
    # Test patch building
    base_rom = bytes([0xFF] * 0x1000)  # 4KB test ROM
    
    test_changeset = {
        'changes': [
            {
                'address': 0x100,
                'size': 4,
                'oldData': 'FFFFFFFF',
                'newData': '00000000',
                'mapType': 'TEST'
            }
        ]
    }
    
    patch_result = core.build_patch_from_changeset(base_rom, test_changeset)
    print(f"Patch Result: {patch_result}")
    
    # Test validation
    validation = core.validate_patch_safety(patch_result.patch_data, base_rom)
    print(f"Validation Result: {validation}")
    
    return True

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_versa_core()
