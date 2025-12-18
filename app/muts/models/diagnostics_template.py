#!/usr/bin/env python3
"""
Diagnostics Capability Template System
Defines standardized modules and services for vehicle diagnostics
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import json


class DiagnosticModule(Enum):
    """Standardized diagnostic modules"""
    ENGINE = "ENGINE"
    TRANSMISSION = "TRANSMISSION"
    ABS = "ABS"
    SRS = "SRS"
    BCM = "BCM"
    CLUSTER = "CLUSTER"
    TCM = "TCM"  # Separate Transmission Control Module for DSG/TCT


class DiagnosticService(Enum):
    """Standardized diagnostic services"""
    READ_DTCS = "READ_DTCS"
    CLEAR_DTCS = "CLEAR_DTCS"
    LIVE_DATA = "LIVE_DATA"
    FREEZE_FRAME = "FREEZE_FRAME"
    READINESS = "READINESS"
    CODING = "CODING"
    ADAPTATION = "ADAPTATION"
    SERVICE_FUNCTIONS = "SERVICE_FUNCTIONS"


class ServiceStatus(Enum):
    """Service support status"""
    SUPPORTED = "SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    LIMITED = "LIMITED"
    UNKNOWN = "UNKNOWN"  # Treated as NOT_SUPPORTED


@dataclass
class ServiceCapability:
    """Capability definition for a single service"""
    status: ServiceStatus
    reason: str
    details: Optional[Dict[str, Any]] = None  # For additional context


@dataclass
class ModuleCapability:
    """Capability definition for a diagnostic module"""
    services: Dict[DiagnosticService, ServiceCapability]
    notes: str
    protocol_info: Optional[str] = None


class DiagnosticsCapabilityTemplate:
    """
    Unified diagnostics capability template system
    Defines exact module->service support per vehicle
    """
    
    def __init__(self, 
                 manufacturer: str,
                 platform: Optional[str] = None,
                 model: Optional[str] = None,
                 generation: Optional[str] = None,
                 year_range: Optional[tuple] = None,
                 engine_variants: Optional[List[str]] = None,
                 transmission_variants: Optional[List[str]] = None):
        
        self.manufacturer = manufacturer
        self.platform = platform
        self.model = model
        self.generation = generation
        self.year_range = year_range  # (start_year, end_year)
        self.engine_variants = engine_variants or []
        self.transmission_variants = transmission_variants or []
        
        # Module capabilities: {module: ModuleCapability}
        self.modules: Dict[DiagnosticModule, ModuleCapability] = {}
        
    def add_module(self, module: DiagnosticModule, 
                   services: Dict[DiagnosticService, ServiceCapability],
                   notes: str = "",
                   protocol_info: Optional[str] = None):
        """Add a module with its service capabilities"""
        self.modules[module] = ModuleCapability(
            services=services,
            notes=notes,
            protocol_info=protocol_info
        )
    
    def get_service_status(self, module: DiagnosticModule, 
                          service: DiagnosticService) -> ServiceCapability:
        """Get the status of a specific service for a module"""
        if module not in self.modules:
            return ServiceCapability(
                status=ServiceStatus.NOT_SUPPORTED,
                reason=f"Module {module.value} not defined for this vehicle"
            )
        
        module_cap = self.modules[module]
        if service not in module_cap.services:
            return ServiceCapability(
                status=ServiceStatus.NOT_SUPPORTED,
                reason=f"Service {service.value} not defined for {module.value}"
            )
        
        return module_cap.services[service]
    
    def is_service_supported(self, module: DiagnosticModule, 
                           service: DiagnosticService) -> bool:
        """Check if a service is supported"""
        status = self.get_service_status(module, service).status
        return status == ServiceStatus.SUPPORTED
    
    def get_supported_modules(self) -> Set[DiagnosticModule]:
        """Get list of modules with at least one supported service"""
        supported = set()
        for module, cap in self.modules.items():
            for service, service_cap in cap.services.items():
                if service_cap.status == ServiceStatus.SUPPORTED:
                    supported.add(module)
                    break
        return supported
    
    def to_json(self) -> str:
        """Convert template to JSON for storage"""
        data = {
            'manufacturer': self.manufacturer,
            'platform': self.platform,
            'model': self.model,
            'generation': self.generation,
            'year_range': self.year_range,
            'engine_variants': self.engine_variants,
            'transmission_variants': self.transmission_variants,
            'modules': {}
        }
        
        for module, cap in self.modules.items():
            module_data = {
                'notes': cap.notes,
                'protocol_info': cap.protocol_info,
                'services': {}
            }
            
            for service, service_cap in cap.services.items():
                module_data['services'][service.value] = {
                    'status': service_cap.status.value,
                    'reason': service_cap.reason,
                    'details': service_cap.details
                }
            
            data['modules'][module.value] = module_data
        
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DiagnosticsCapabilityTemplate':
        """Create template from JSON"""
        data = json.loads(json_str)
        
        template = cls(
            manufacturer=data['manufacturer'],
            platform=data.get('platform'),
            model=data.get('model'),
            generation=data.get('generation'),
            year_range=tuple(data.get('year_range', [])),
            engine_variants=data.get('engine_variants', []),
            transmission_variants=data.get('transmission_variants', [])
        )
        
        for module_name, module_data in data.get('modules', {}).items():
            module = DiagnosticModule(module_name)
            
            services = {}
            for service_name, service_data in module_data.get('services', {}).items():
                service = DiagnosticService(service_name)
                services[service] = ServiceCapability(
                    status=ServiceStatus(service_data['status']),
                    reason=service_data['reason'],
                    details=service_data.get('details')
                )
            
            template.add_module(
                module=module,
                services=services,
                notes=module_data.get('notes', ''),
                protocol_info=module_data.get('protocol_info')
            )
        
        return template
    
    def matches_vehicle(self, manufacturer: str, platform: Optional[str] = None,
                       model: Optional[str] = None, generation: Optional[str] = None,
                       year: Optional[int] = None, engine: Optional[str] = None,
                       transmission: Optional[str] = None) -> bool:
        """Check if this template matches a vehicle specification"""
        if self.manufacturer != manufacturer:
            return False
        
        if self.platform and platform and self.platform != platform:
            return False
        
        if self.model and model and self.model != model:
            return False
        
        if self.generation and generation and self.generation != generation:
            return False
        
        if self.year_range and year:
            start, end = self.year_range
            if year < start or year > end:
                return False
        
        if self.engine_variants and engine and engine not in self.engine_variants:
            return False
        
        if self.transmission_variants and transmission and transmission not in self.transmission_variants:
            return False
        
        return True
