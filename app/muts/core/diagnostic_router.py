#!/usr/bin/env python3
"""
Manufacturer-Agnostic Diagnostic Router
Routes diagnostic requests based on vehicle capability profiles
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from muts.models.vehicle_capabilities import (
    VehicleCapabilityProfile, DiagnosticModule, DiagnosticService, 
    SupportStatus, InterfaceType
)
from muts.models.diagnostics_registry import template_registry, DiagnosticsCapabilityTemplate
from muts.models.diagnostics_template import ServiceStatus
from muts.models.database_models import Vehicle
from muts.core.override_manager import override_manager, OverrideScope
from muts.core.forensic_recorder import forensic_recorder

logger = logging.getLogger(__name__)


class DiagnosticRouter:
    """
    Routes diagnostic requests to appropriate handlers based on vehicle capabilities
    Replaces hardcoded Mazda-specific routing
    """
    
    def __init__(self, capability_db_session):
        self.db = capability_db_session
        self.active_handlers = {}
        self._initialize_handlers()
    
    def _initialize_handlers(self):
        """Initialize manufacturer-specific handlers"""
        # Import handlers lazily to avoid circular imports
        try:
            from mds.vehicle.vehicle_specific import VehicleSpecific as MazdaHandler
            self.active_handlers['Mazda'] = MazdaHandler
        except ImportError:
            logger.warning("Mazda handler not available")
        
        # VW handler would be added here when implemented
        # Holden handler would be added here when implemented
        
        # Generic OBD-II fallback
        from muts.services.obd_service import GenericOBDService
        self.active_handlers['GENERIC'] = GenericOBDService
    
    def get_vehicle_template(self, vehicle: Vehicle) -> Optional[DiagnosticsCapabilityTemplate]:
        """Get diagnostics template for a vehicle"""
        # Extract vehicle details
        manufacturer = getattr(vehicle, 'manufacturer', 'Unknown')
        model = getattr(vehicle, 'model', 'Unknown')
        generation = getattr(vehicle, 'generation', None)
        year = getattr(vehicle, 'year', None)
        engine = getattr(vehicle, 'engine', None)
        transmission = getattr(vehicle, 'transmission', None)
        
        # Find matching template
        template = template_registry.find_template(
            manufacturer=manufacturer,
            model=model,
            generation=generation,
            year=year,
            engine=engine,
            transmission=transmission
        )
        
        return template
    
    def get_vehicle_capability(self, vehicle: Vehicle) -> Optional[VehicleCapabilityProfile]:
        """Get capability profile for a vehicle"""
        # Try to match by manufacturer and model
        profile = self.db.query(VehicleCapabilityProfile).filter_by(
            manufacturer=vehicle.manufacturer if hasattr(vehicle, 'manufacturer') else 'Mazda',
            model=vehicle.model.split()[0] if vehicle.model else 'Mazdaspeed'
        ).first()
        
        return profile
    
    def is_service_supported(self, vehicle: Vehicle, module: DiagnosticModule, 
                           service: DiagnosticService) -> Tuple[bool, str]:
        """
        Check if a diagnostic service is supported for the vehicle
        
        Returns:
            (is_supported, reason)
        """
        # First check the new template system
        template = self.get_vehicle_template(vehicle)
        if template:
            service_cap = template.get_service_status(module, service)
            if service_cap.status == ServiceStatus.SUPPORTED:
                return True, service_cap.reason
            else:
                return False, service_cap.reason
        
        # Fallback to legacy capability profile
        capability = self.get_vehicle_capability(vehicle)
        if not capability:
            return False, "Vehicle capability profile not found"
        
        service_cap = capability.get_service_capability(service)
        status = service_cap.get('status', SupportStatus.UNKNOWN.value)
        reason = service_cap.get('reason', 'Unknown')
        
        return status == SupportStatus.SUPPORTED.value, reason
    
    def is_module_supported(self, vehicle: Vehicle, module: DiagnosticModule) -> Tuple[bool, str]:
        """
        Check if a diagnostic module is supported for the vehicle
        
        Returns:
            (is_supported, reason)
        """
        # First check the new template system
        template = self.get_vehicle_template(vehicle)
        if template:
            # Check if module has any supported services
            if module in template.modules:
                # Module exists, check if any service is supported
                for service_cap in template.modules[module].services.values():
                    if service_cap.status == ServiceStatus.SUPPORTED:
                        return True, template.modules[module].notes
                return False, f"Module {module.value} exists but no services are supported"
            else:
                return False, f"Module {module.value} not defined for this vehicle"
        
        # Fallback to legacy capability profile
        capability = self.get_vehicle_capability(vehicle)
        if not capability:
            return False, "Vehicle capability profile not found"
        
        module_cap = capability.get_module_capability(module)
        status = module_cap.get('status', SupportStatus.UNKNOWN.value)
        reason = module_cap.get('reason', 'Unknown')
        
        return status == SupportStatus.SUPPORTED.value, reason
    
    def get_diagnostic_handler(self, vehicle: Vehicle):
        """
        Get the appropriate diagnostic handler for a vehicle
        
        Returns:
            Diagnostic handler instance or None if not supported
        """
        capability = self.get_vehicle_capability(vehicle)
        
        if not capability:
            logger.error(f"No capability profile found for vehicle: {vehicle.model}")
            return None
        
        # Check required interface
        if not self._check_interface_available(capability.required_interface):
            logger.error(f"Required interface not available: {capability.required_interface}")
            return None
        
        # Get manufacturer-specific handler
        manufacturer = capability.manufacturer
        if manufacturer in self.active_handlers:
            handler_class = self.active_handlers[manufacturer]
            return handler_class()
        
        # Fall back to generic OBD-II
        if capability.required_interface == InterfaceType.OBD2.value:
            return self.active_handlers['GENERIC']()
        
        return None
    
    def _check_interface_available(self, interface_type: str) -> bool:
        """Check if the required interface is available"""
        if interface_type == InterfaceType.OBD2.value:
            # Check for OBD-II interface
            try:
                import serial.tools.list_ports
                ports = list(serial.tools.list_ports.comports())
                return len(ports) > 0
            except:
                return False
        
        elif interface_type == InterfaceType.J2534.value:
            # Check for J2534 interface
            try:
                from mds.interface.j2534_interface import J2534Interface
                interface = J2534Interface()
                return interface.detect_device()
            except:
                return False
        
        return False
    
    def _execute_dry_run(self, vehicle: Vehicle, service: str, module: DiagnosticModule,
                        service_type: DiagnosticService, capability_supported: bool,
                        capability_reason: str, override_active: bool, override_reason: str,
                        user_id: int = None, session_id: str = None, **kwargs) -> Dict[str, Any]:
        """Execute diagnostic action in dry-run mode (no ECU communication)"""
        
        # Determine if this would be a write operation
        write_operations = {
            DiagnosticService.DTC_CLEAR,
            DiagnosticService.CODING,
            DiagnosticService.ADAPTATION,
            DiagnosticService.ACTUATION_TESTS
        }
        
        is_write = service_type in write_operations
        would_execute = capability_supported or override_active
        
        # Update dry-run statistics
        if session_id:
            forensic_recorder.update_dry_run_stats(
                session_id=session_id,
                attempted=1,
                blocked=0 if would_execute else 1,
                writes_prevented=1 if is_write and would_execute else 0
            )
        
        # Record forensic event
        if session_id:
            forensic_recorder.record_diagnostic_action(
                session_id=session_id,
                module=module,
                service=service_type,
                capability_supported=capability_supported,
                capability_reason=capability_reason,
                override_active=override_active,
                override_scope=override_reason.split(':')[0] if override_reason else None,
                override_reason=override_reason,
                execution_mode='DRY_RUN',
                would_execute=would_execute,
                result_status='BLOCKED' if not would_execute else 'SUCCESS',
                ui_action=f'Dry-run {service}',
                error_message=None if would_execute else f'Blocked: {capability_reason}'
            )
        
        # Build dry-run response
        response = {
            'dry_run': True,
            'would_execute': would_execute,
            'module': module.value if module else None,
            'service': service,
            'capability_supported': capability_supported,
            'override_active': override_active,
            'write_risk': 'HIGH' if is_write else 'NONE',
            'execution_mode': 'DRY_RUN',
            'status': 'BLOCKED' if not would_execute else 'SUCCESS'
        }
        
        if not would_execute:
            response['error'] = f'Blocked in dry-run: {capability_reason}'
            response['block_reason'] = capability_reason
        else:
            # Simulate what would happen
            if is_write:
                response['warning'] = 'WRITE OPERATION BLOCKED BY DRY-RUN'
                response['simulated_result'] = f'Would {service.lower()} on {module.value if module else "ECU"}'
            else:
                response['simulated_result'] = f'Would read {service.lower()} from {module.value if module else "ECU"}'
            
            # Add protocol info
            handler = self.get_diagnostic_handler(vehicle)
            if handler:
                response['protocol'] = getattr(handler, 'protocol', 'Standard OBD-II')
        
        return response
    
    def _execute_with_override(self, vehicle: Vehicle, service: str, module: DiagnosticModule,
                            service_type: DiagnosticService, override_reason: str, **kwargs) -> Dict[str, Any]:
        """Execute diagnostic action with override flag"""
        # Get appropriate handler
        handler = self.get_diagnostic_handler(vehicle)
        if not handler:
            return {
                'status': 'ERROR',
                'error': 'No diagnostic handler available'
            }
        
        # Execute the service
        try:
            # Add override context to kwargs
            kwargs['override_active'] = True
            kwargs['override_reason'] = override_reason
            
            # Call the handler method
            method = getattr(handler, service, None)
            if not method:
                return {
                    'status': 'ERROR',
                    'error': f'Service method not found: {service}'
                }
            
            result = method(vehicle, **kwargs)
            
            # Add override flags to result
            if isinstance(result, dict):
                result['override_active'] = True
                result['override_reason'] = override_reason
                result['warning'] = 'EXECUTED WITH ADMIN OVERRIDE - UNSUPPORTED ACTION'
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing overridden service {service}: {e}")
            return {
                'status': 'ERROR',
                'error': str(e),
                'override_active': True,
                'override_reason': override_reason
            }
    
    def route_diagnostic_request(self, vehicle: Vehicle, service: str, module: str = None,
                           user_id: int = None, session_id: str = None, 
                           dry_run: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Route a diagnostic request to the appropriate handler
        
        Args:
            vehicle: Vehicle object
            service: Service name (e.g., 'scan_dtcs', 'clear_dtcs', 'live_data')
            module: Module name (e.g., 'ENGINE', 'TRANSMISSION', 'ABS')
            user_id: User ID for override checking
            session_id: Session ID for override scoping
            dry_run: If True, simulate without sending ECU commands
            **kwargs: Additional parameters
            
        Returns:
            Response dictionary with status and data/error
        """
        # Convert service string to enum
        service_map = {
            'scan_dtcs': DiagnosticService.DTC_READ,
            'clear_dtcs': DiagnosticService.DTC_CLEAR,
            'live_data': DiagnosticService.LIVE_DATA,
            'freeze_frame': DiagnosticService.FREEZE_FRAME,
            'readiness': DiagnosticService.READINESS,
            'actuation_tests': DiagnosticService.ACTUATION_TESTS,
            'coding': DiagnosticService.CODING,
            'adaptation': DiagnosticService.ADAPTATION
        }
        
        if service not in service_map:
            return {
                'status': 'ERROR',
                'error': f'Unknown service: {service}'
            }
        
        diagnostic_service = service_map[service]
        
        # Convert module string to enum if provided
        diagnostic_module = None
        if module:
            module_map = {
                'ENGINE': DiagnosticModule.ENGINE,
                'TRANSMISSION': DiagnosticModule.TRANSMISSION,
                'TCM': DiagnosticModule.TCM,
                'ABS': DiagnosticModule.ABS,
                'SRS': DiagnosticModule.SRS,
                'BCM': DiagnosticModule.BCM,
                'CLUSTER': DiagnosticModule.CLUSTER
            }
            diagnostic_module = module_map.get(module.upper())
            
            if not diagnostic_module:
                return {
                    'status': 'ERROR',
                    'error': f'Unknown module: {module}'
                }
        
        # Check if module is supported (if specified)
        capability_supported = True
        capability_reason = ""
        override_active = False
        override_reason = ""
        
        if diagnostic_module:
            is_mod_supported, mod_reason = self.is_module_supported(vehicle, diagnostic_module)
            if not is_mod_supported:
                capability_supported = False
                capability_reason = mod_reason
                
                # Check for admin override
                if user_id and session_id:
                    can_override, ov_reason = override_manager.can_override(
                        user_id, diagnostic_module, diagnostic_service, session_id
                    )
                    if can_override:
                        override_active = True
                        override_reason = ov_reason
                
                if not override_active and not dry_run:
                    return {
                        'status': 'NOT_SUPPORTED',
                        'error': f'Module not supported: {capability_reason}'
                    }
        
        # Check if service is supported for the module
        if capability_supported:
            is_svc_supported, svc_reason = self.is_service_supported(vehicle, diagnostic_module or DiagnosticModule.ENGINE, diagnostic_service)
            if not is_svc_supported:
                capability_supported = False
                capability_reason = svc_reason
                
                # Check for admin override
                if user_id and session_id:
                    can_override, ov_reason = override_manager.can_override(
                        user_id, diagnostic_module or DiagnosticModule.ENGINE, diagnostic_service, session_id
                    )
                    if can_override:
                        override_active = True
                        override_reason = ov_reason
                
                if not override_active and not dry_run:
                    return {
                        'status': 'NOT_SUPPORTED',
                        'error': f'Service not supported: {capability_reason}'
                    }
        
        # Handle dry-run mode
        if dry_run:
            return self._execute_dry_run(
                vehicle, service, diagnostic_module, diagnostic_service,
                capability_supported, capability_reason,
                override_active, override_reason,
                user_id, session_id, **kwargs
            )
        
        # Get appropriate handler
        handler = self.get_diagnostic_handler(vehicle)
        if not handler:
            return {
                'status': 'ERROR',
                'error': 'No diagnostic handler available'
            }
        
        # Execute the service
        try:
            if service == 'scan_dtcs':
                result = self._scan_dtcs(handler, vehicle, **kwargs)
            elif service == 'clear_dtcs':
                result = self._clear_dtcs(handler, vehicle, **kwargs)
            elif service == 'live_data':
                result = self._get_live_data(handler, vehicle, **kwargs)
            else:
                result = {
                    'status': 'NOT_SUPPORTED',
                    'error': f'Service {service} not implemented for this vehicle'
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Diagnostic service {service} failed: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _scan_dtcs(self, handler, vehicle: Vehicle, **kwargs) -> Dict[str, Any]:
        """Scan for diagnostic trouble codes"""
        if hasattr(handler, 'connect'):
            if not handler.connect():
                return {'status': 'ERROR', 'error': 'Failed to connect to vehicle'}
        
        try:
            if hasattr(handler, 'read_dtcs'):
                dtcs = handler.read_dtcs()
                return {
                    'status': 'SUCCESS',
                    'data': dtcs
                }
            else:
                return {'status': 'NOT_SUPPORTED', 'error': 'DTC scanning not supported'}
        finally:
            if hasattr(handler, 'disconnect'):
                handler.disconnect()
    
    def _clear_dtcs(self, handler, vehicle: Vehicle, **kwargs) -> Dict[str, Any]:
        """Clear diagnostic trouble codes"""
        if hasattr(handler, 'connect'):
            if not handler.connect():
                return {'status': 'ERROR', 'error': 'Failed to connect to vehicle'}
        
        try:
            if hasattr(handler, 'clear_dtcs'):
                success = handler.clear_dtcs()
                return {
                    'status': 'SUCCESS' if success else 'ERROR',
                    'message': 'DTCs cleared successfully' if success else 'Failed to clear DTCs'
                }
            else:
                return {'status': 'NOT_SUPPORTED', 'error': 'DTC clearing not supported'}
        finally:
            if hasattr(handler, 'disconnect'):
                handler.disconnect()
    
    def _get_live_data(self, handler, vehicle: Vehicle, **kwargs) -> Dict[str, Any]:
        """Get live data from vehicle"""
        if hasattr(handler, 'connect'):
            if not handler.connect():
                return {'status': 'ERROR', 'error': 'Failed to connect to vehicle'}
        
        try:
            if hasattr(handler, 'get_live_data'):
                data = handler.get_live_data()
                return {
                    'status': 'SUCCESS',
                    'data': data
                }
            else:
                return {'status': 'NOT_SUPPORTED', 'error': 'Live data not supported'}
        finally:
            if hasattr(handler, 'disconnect'):
                handler.disconnect()
    
    def get_vehicle_capabilities_summary(self, vehicle: Vehicle) -> Dict[str, Any]:
        """Get a summary of vehicle capabilities for UI display"""
        capability = self.get_vehicle_capability(vehicle)
        
        if not capability:
            return {
                'status': 'UNKNOWN',
                'message': 'Vehicle capabilities not defined'
            }
        
        # Build module summary
        modules = {}
        for module in DiagnosticModule:
            is_supported, reason = self.is_module_supported(vehicle, module)
            modules[module.value] = {
                'supported': is_supported,
                'status': capability.get_module_capability(module).get('status'),
                'reason': reason
            }
        
        # Build service summary
        services = {}
        for service in DiagnosticService:
            is_supported, reason = self.is_service_supported(vehicle, service)
            services[service.value] = {
                'supported': is_supported,
                'status': capability.get_service_capability(service).get('status'),
                'reason': reason
            }
        
        return {
            'status': 'DEFINED',
            'vehicle_info': {
                'manufacturer': capability.manufacturer,
                'platform': capability.platform,
                'model': capability.model,
                'generation': capability.generation,
                'body': capability.body
            },
            'interface': {
                'required': capability.required_interface,
                'protocol': capability.primary_protocol,
                'notes': capability.interface_notes
            },
            'modules': modules,
            'services': services,
            'features': {
                'dsg_shifts': capability.supports_dsg_shifts,
                'awd_modeling': capability.supports_awd_modeling,
                'virtual_dyno': capability.supports_virtual_dyno
            },
            'confidence': capability.confidence_level,
            'notes': capability.notes
        }
