#!/usr/bin/env python3
"""
Vehicle Capability Profile System
Maps manufacturer+model combinations to supported features and protocols
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import json

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SupportStatus(Enum):
    """Feature support status"""
    SUPPORTED = "SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class DiagnosticModule(Enum):
    """Diagnostic modules that can be supported"""
    ENGINE = "ENGINE"
    TRANSMISSION = "TRANSMISSION"
    ABS = "ABS"
    SRS = "SRS"
    BCM = "BCM"
    TCM = "TCM"
    IMMOBILIZER = "IMMOBILIZER"
    CLUSTER = "CLUSTER"


class DiagnosticService(Enum):
    """Diagnostic services that can be supported"""
    DTC_READ = "DTC_READ"
    DTC_CLEAR = "DTC_CLEAR"
    LIVE_DATA = "LIVE_DATA"
    FREEZE_FRAME = "FREEZE_FRAME"
    READINESS = "READINESS"
    ACTUATION_TESTS = "ACTUATION_TESTS"
    CODING = "CODING"
    ADAPTATION = "ADAPTATION"


class InterfaceType(Enum):
    """Interface types required for vehicle communication"""
    OBD2 = "OBD2"
    CAN_DIRECT = "CAN_DIRECT"
    J2534 = "J2534"
    MANUFACTURER_SPECIFIC = "MANUFACTURER_SPECIFIC"


class VehicleCapabilityProfile(Base):
    """Defines capabilities for a specific vehicle model/configuration"""
    __tablename__ = 'vehicle_capability_profiles'
    
    id = Column(Integer, primary_key=True)
    
    # Vehicle identification
    manufacturer = Column(String(50), nullable=False)
    platform = Column(String(50))
    model = Column(String(50), nullable=False)
    generation = Column(String(50))
    body = Column(String(50))  # Wagon, Sedan, etc.
    
    # Configuration identifiers
    engine_code = Column(String(50))
    transmission_type = Column(String(50))
    drivetrain_type = Column(String(50))
    
    # Protocol information
    primary_protocol = Column(String(50))  # e.g., "ISO_15765_4_CAN_11B_500K"
    secondary_protocols = Column(Text)  # JSON array of alternative protocols
    
    # Interface requirements
    required_interface = Column(String(50))  # OBD2, J2534, etc.
    interface_notes = Column(Text)  # Special requirements
    
    # Module capabilities (JSON: {module: {status, reason, services: [...]}})
    module_capabilities = Column(Text, nullable=False)
    
    # Service capabilities (JSON: {service: {status, reason, notes}})
    service_capabilities = Column(Text, nullable=False)
    
    # Special features
    supports_dsg_shifts = Column(Boolean, default=False)
    supports_awd_modeling = Column(Boolean, default=False)
    supports_virtual_dyno = Column(Boolean, default=False)
    
    # Metadata
    confidence_level = Column(Integer, default=0)  # 0-100
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_module_capability(self, module: DiagnosticModule) -> Dict[str, Any]:
        """Get capability for a specific diagnostic module"""
        capabilities = json.loads(self.module_capabilities or '{}')
        return capabilities.get(module.value, {
            'status': SupportStatus.UNKNOWN.value,
            'reason': 'Module not defined'
        })
    
    def get_service_capability(self, service: DiagnosticService) -> Dict[str, Any]:
        """Get capability for a specific diagnostic service"""
        capabilities = json.loads(self.service_capabilities or '{}')
        return capabilities.get(service.value, {
            'status': SupportStatus.UNKNOWN.value,
            'reason': 'Service not defined'
        })
    
    def is_module_supported(self, module: DiagnosticModule) -> bool:
        """Check if a module is supported"""
        capability = self.get_module_capability(module)
        return capability.get('status') == SupportStatus.SUPPORTED.value
    
    def is_service_supported(self, service: DiagnosticService) -> bool:
        """Check if a service is supported"""
        capability = self.get_service_capability(service)
        return capability.get('status') == SupportStatus.SUPPORTED.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'manufacturer': self.manufacturer,
            'platform': self.platform,
            'model': self.model,
            'generation': self.generation,
            'body': self.body,
            'engine_code': self.engine_code,
            'transmission_type': self.transmission_type,
            'drivetrain_type': self.drivetrain_type,
            'primary_protocol': self.primary_protocol,
            'required_interface': self.required_interface,
            'interface_notes': self.interface_notes,
            'module_capabilities': json.loads(self.module_capabilities or '{}'),
            'service_capabilities': json.loads(self.service_capabilities or '{}'),
            'supports_dsg_shifts': self.supports_dsg_shifts,
            'supports_awd_modeling': self.supports_awd_modeling,
            'supports_virtual_dyno': self.supports_virtual_dyno,
            'confidence_level': self.confidence_level,
            'notes': self.notes
        }


def create_vw_golf_capabilities() -> List[Dict[str, Any]]:
    """Create capability profiles for VW Golf models"""
    
    base_capabilities = {
        # Module capabilities
        'module_capabilities': {
            DiagnosticModule.ENGINE.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II and VW-specific protocols',
                'services': [DiagnosticService.DTC_READ.value, DiagnosticService.LIVE_DATA.value]
            },
            DiagnosticModule.TRANSMISSION.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'TCM accessible via CAN',
                'services': [DiagnosticService.DTC_READ.value, DiagnosticService.LIVE_DATA.value]
            },
            DiagnosticModule.ABS.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'Basic DTC read only',
                'services': [DiagnosticService.DTC_READ.value]
            },
            DiagnosticModule.SRS.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Airbag module requires manufacturer-specific security',
                'services': []
            },
            DiagnosticModule.BCM.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Body control module not accessible via OBD-II',
                'services': []
            },
            DiagnosticModule.TCM.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'DSG TCM supports diagnostics',
                'services': [DiagnosticService.DTC_READ.value, DiagnosticService.LIVE_DATA.value]
            }
        },
        # Service capabilities
        'service_capabilities': {
            DiagnosticService.DTC_READ.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II mode 03'
            },
            DiagnosticService.DTC_CLEAR.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II mode 04'
            },
            DiagnosticService.LIVE_DATA.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II mode 01'
            },
            DiagnosticService.FREEZE_FRAME.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'Limited freeze frame support'
            },
            DiagnosticService.READINESS.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II mode 01 PID 01'
            },
            DiagnosticService.ACTUATION_TESTS.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Requires VW-specific security access'
            },
            DiagnosticService.CODING.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Requires manufacturer-level access'
            },
            DiagnosticService.ADAPTATION.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Requires VAG-COM/ODIS'
            }
        }
    }
    
    profiles = []
    
    # VW Golf Mk5/Mk6 (PQ35)
    pq35_profile = VehicleCapabilityProfile(
        manufacturer="Volkswagen",
        platform="PQ35",
        model="Golf",
        generation="Mk5/Mk6",
        primary_protocol="ISO_15765_4_CAN_11B_500K",
        required_interface=InterfaceType.OBD2.value,
        interface_notes="Standard OBD-II port, 500k CAN",
        module_capabilities=json.dumps(base_capabilities['module_capabilities']),
        service_capabilities=json.dumps(base_capabilities['service_capabilities']),
        supports_dsg_shifts=True,
        supports_awd_modeling=True,  # For Mk6 R
        supports_virtual_dyno=True,
        confidence_level=85,
        notes="PQ35 platform with KWP2000/UDS"
    )
    profiles.append(pq35_profile)
    
    # VW Golf Mk7/Mk7.5 (MQB)
    mqb_capabilities = base_capabilities.copy()
    mqb_capabilities['service_capabilities'][DiagnosticService.FREEZE_FRAME.value] = {
        'status': SupportStatus.SUPPORTED.value,
        'reason': 'Full freeze frame support on MQB'
    }
    
    mqb_profile = VehicleCapabilityProfile(
        manufacturer="Volkswagen",
        platform="MQB",
        model="Golf",
        generation="Mk7/Mk7.5",
        primary_protocol="ISO_15765_4_CAN_11B_500K",
        required_interface=InterfaceType.OBD2.value,
        interface_notes="Standard OBD-II port, UDS protocol",
        module_capabilities=json.dumps(mqb_capabilities['module_capabilities']),
        service_capabilities=json.dumps(mqb_capabilities['service_capabilities']),
        supports_dsg_shifts=True,
        supports_awd_modeling=True,  # For Mk7 R
        supports_virtual_dyno=True,
        confidence_level=90,
        notes="MQB platform with UDS/ODX"
    )
    profiles.append(mqb_profile)
    
    return profiles


def create_holden_commodore_capabilities() -> List[Dict[str, Any]]:
    """Create capability profiles for Holden Commodore Wagons"""
    
    base_capabilities = {
        'module_capabilities': {
            DiagnosticModule.ENGINE.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Holden PCM accessible via OBD-II',
                'services': [DiagnosticService.DTC_READ.value, DiagnosticService.LIVE_DATA.value]
            },
            DiagnosticModule.TRANSMISSION.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'GM 4L60E/6L80 TCM supported',
                'services': [DiagnosticService.DTC_READ.value, DiagnosticService.LIVE_DATA.value]
            },
            DiagnosticModule.ABS.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'Basic ABS diagnostics',
                'services': [DiagnosticService.DTC_READ.value]
            },
            DiagnosticModule.SRS.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Airbag module requires Tech2/MDI',
                'services': []
            },
            DiagnosticModule.BCM.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Body control requires GDS2',
                'services': []
            },
            DiagnosticModule.TCM.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Transmission control accessible',
                'services': [DiagnosticService.DTC_READ.value, DiagnosticService.LIVE_DATA.value]
            }
        },
        'service_capabilities': {
            DiagnosticService.DTC_READ.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II and GM enhanced'
            },
            DiagnosticService.DTC_CLEAR.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II mode 04'
            },
            DiagnosticService.LIVE_DATA.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Enhanced GM PIDs available'
            },
            DiagnosticService.FREEZE_FRAME.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'GM freeze frame supported'
            },
            DiagnosticService.READINESS.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'OBD-II monitors supported'
            },
            DiagnosticService.ACTUATION_TESTS.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Requires Tech2/MDI'
            },
            DiagnosticService.CODING.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Requires dealer tools'
            },
            DiagnosticService.ADAPTATION.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Requires dealer tools'
            }
        }
    }
    
    profiles = []
    
    # Holden VT/VX/VY/VZ (1997-2006)
    early_profile = VehicleCapabilityProfile(
        manufacturer="Holden",
        platform="VT/VX/VY/VZ",
        model="Commodore",
        body="Wagon",
        generation="Pre-VE",
        primary_protocol="SAE_J1850_VPW",
        required_interface=InterfaceType.OBD2.value,
        interface_notes="VPW protocol, 10.4k baud",
        module_capabilities=json.dumps(base_capabilities['module_capabilities']),
        service_capabilities=json.dumps(base_capabilities['service_capabilities']),
        supports_dsg_shifts=False,
        supports_awd_modeling=False,
        supports_virtual_dyno=True,
        confidence_level=75,
        notes="Early models with VPW protocol"
    )
    profiles.append(early_profile)
    
    # Holden VE (2006-2013)
    ve_profile = VehicleCapabilityProfile(
        manufacturer="Holden",
        platform="VE",
        model="Commodore",
        body="Wagon",
        generation="VE",
        primary_protocol="ISO_15765_4_CAN_11B_500K",
        required_interface=InterfaceType.OBD2.value,
        interface_notes="CAN protocol, GMLAN",
        module_capabilities=json.dumps(base_capabilities['module_capabilities']),
        service_capabilities=json.dumps(base_capabilities['service_capabilities']),
        supports_dsg_shifts=False,
        supports_awd_modeling=False,
        supports_virtual_dyno=True,
        confidence_level=85,
        notes="VE platform with GMLAN"
    )
    profiles.append(ve_profile)
    
    # Holden VF (2013-2017)
    vf_capabilities = base_capabilities.copy()
    vf_capabilities['module_capabilities'][DiagnosticModule.BCM.value] = {
        'status': SupportStatus.PARTIAL.value,
        'reason': 'Limited BCM access via GDS2',
        'services': [DiagnosticService.DTC_READ.value]
    }
    
    vf_profile = VehicleCapabilityProfile(
        manufacturer="Holden",
        platform="VF",
        model="Commodore",
        body="Wagon",
        generation="VF",
        primary_protocol="ISO_15765_4_CAN_11B_500K",
        required_interface=InterfaceType.OBD2.value,
        interface_notes="GMLAN CAN, enhanced diagnostics",
        module_capabilities=json.dumps(vf_capabilities['module_capabilities']),
        service_capabilities=json.dumps(base_capabilities['service_capabilities']),
        supports_dsg_shifts=False,
        supports_awd_modeling=False,
        supports_virtual_dyno=True,
        confidence_level=90,
        notes="VF platform with enhanced GMLAN"
    )
    profiles.append(vf_profile)
    
    return profiles


def create_alfa_giulietta_capabilities() -> List[Dict[str, Any]]:
    """Create capability profiles for Alfa Romeo Giulietta models"""
    
    base_capabilities = {
        # Module capabilities
        'module_capabilities': {
            DiagnosticModule.ENGINE.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II and Alfa-specific protocols',
                'services': [DiagnosticService.DTC_READ.value, DiagnosticService.LIVE_DATA.value]
            },
            DiagnosticModule.TRANSMISSION.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'TCT requires Alfa-specific diagnostic tool',
                'services': [DiagnosticService.DTC_READ.value, DiagnosticService.LIVE_DATA.value]
            },
            DiagnosticModule.ABS.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'Basic DTC read only via OBD-II',
                'services': [DiagnosticService.DTC_READ.value]
            },
            DiagnosticModule.SRS.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Airbag module requires Alfa Examiner or MSDS',
                'services': []
            },
            DiagnosticModule.BCM.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Body control module requires manufacturer-specific access',
                'services': []
            },
            DiagnosticModule.TCM.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'TCT control limited without Alfa diagnostics',
                'services': [DiagnosticService.DTC_READ.value]
            }
        },
        # Service capabilities
        'service_capabilities': {
            DiagnosticService.DTC_READ.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II mode 03'
            },
            DiagnosticService.DTC_CLEAR.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II mode 04'
            },
            DiagnosticService.LIVE_DATA.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II mode 01 with Alfa PIDs'
            },
            DiagnosticService.FREEZE_FRAME.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'Limited freeze frame support'
            },
            DiagnosticService.READINESS.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Standard OBD-II mode 01 PID 01'
            },
            DiagnosticService.ACTUATION_TESTS.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Requires Alfa Examiner or MSDS'
            },
            DiagnosticService.CODING.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Requires manufacturer-level access'
            },
            DiagnosticService.ADAPTATION.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'Requires Alfa diagnostic software'
            }
        }
    }
    
    profiles = []
    
    # Alfa Romeo Giulietta (C-Evo platform)
    giulietta_profile = VehicleCapabilityProfile(
        manufacturer="Alfa Romeo",
        platform="C-Evo",
        model="Giulietta",
        generation="2012",
        primary_protocol="ISO_15765_4_CAN_11B_500K",
        required_interface=InterfaceType.OBD2.value,
        interface_notes="Standard OBD-II port, 500k CAN with Alfa-specific extensions",
        module_capabilities=json.dumps(base_capabilities['module_capabilities']),
        service_capabilities=json.dumps(base_capabilities['service_capabilities']),
        supports_dsg_shifts=True,  # TCT behaves like DSG for shift detection
        supports_awd_modeling=False,  # FWD only
        supports_virtual_dyno=True,
        confidence_level=85,
        notes="C-Evo platform with MultiAir/TCT technology"
    )
    profiles.append(giulietta_profile)
    
    return profiles


def create_mazda_capabilities() -> List[Dict[str, Any]]:
    """Create capability profiles for existing Mazda models"""
    
    mazda_capabilities = {
        'module_capabilities': {
            DiagnosticModule.ENGINE.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'MZR DISI engine fully supported',
                'services': [
                    DiagnosticService.DTC_READ.value,
                    DiagnosticService.DTC_CLEAR.value,
                    DiagnosticService.LIVE_DATA.value,
                    DiagnosticService.ACTUATION_TESTS.value
                ]
            },
            DiagnosticModule.TRANSMISSION.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Mazda transmission supported',
                'services': [DiagnosticService.DTC_READ.value, DiagnosticService.LIVE_DATA.value]
            },
            DiagnosticModule.ABS.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'ABS module accessible',
                'services': [DiagnosticService.DTC_READ.value]
            },
            DiagnosticModule.SRS.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'Limited SRS access',
                'services': [DiagnosticService.DTC_READ.value]
            },
            DiagnosticModule.BCM.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'Limited BCM functions',
                'services': [DiagnosticService.DTC_READ.value]
            },
            DiagnosticModule.TCM.value: {
                'status': SupportStatus.NOT_SUPPORTED.value,
                'reason': 'No separate TCM on Mazdaspeed3',
                'services': []
            }
        },
        'service_capabilities': {
            DiagnosticService.DTC_READ.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Full DTC support'
            },
            DiagnosticService.DTC_CLEAR.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'DTC clear supported'
            },
            DiagnosticService.LIVE_DATA.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Enhanced PIDs available'
            },
            DiagnosticService.FREEZE_FRAME.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Freeze frame supported'
            },
            DiagnosticService.READINESS.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'OBD-II monitors'
            },
            DiagnosticService.ACTUATION_TESTS.value: {
                'status': SupportStatus.SUPPORTED.value,
                'reason': 'Mazda-specific tests'
            },
            DiagnosticService.CODING.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'Limited coding'
            },
            DiagnosticService.ADAPTATION.value: {
                'status': SupportStatus.PARTIAL.value,
                'reason': 'Some adaptations'
            }
        }
    }
    
    profile = VehicleCapabilityProfile(
        manufacturer="Mazda",
        platform="J36",
        model="Mazdaspeed3",
        generation="2007-2013",
        primary_protocol="ISO_15765_4_CAN_11B_500K",
        required_interface=InterfaceType.OBD2.value,
        interface_notes="Mazda CAN protocol",
        module_capabilities=json.dumps(mazda_capabilities['module_capabilities']),
        service_capabilities=json.dumps(mazda_capabilities['service_capabilities']),
        supports_dsg_shifts=False,
        supports_awd_modeling=False,
        supports_virtual_dyno=True,
        confidence_level=95,
        notes="Mazdaspeed3 with full feature support"
    )
    
    return [profile]
