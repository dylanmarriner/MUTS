"""
HardwareFactory - Factory pattern for creating hardware-specific implementations.
Provides pluggable backends for CAN and OBD communication devices.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

from mazda_can_engine import MazdaCANEngine, CANInterfaceType
from mazda_obd_service import MazdaOBDService, OBDCommandMode
from python_can_engine import PythonCANEngine
from j2534_can_engine import J2534CANEngine
from python_obd_service import PythonOBDService
from j2534_obd_service import J2534OBDService


class HardwareBackend(Enum):
    """Available hardware backends."""
    PYTHON_CAN = "python-can"
    J2534_PASSTHRU = "j2534-passthru"


class HardwareFactory:
    """
    Factory for creating hardware-specific CAN and OBD implementations.
    Supports runtime hardware selection and configuration.
    """
    
    # Backend registry
    CAN_BACKENDS = {
        HardwareBackend.PYTHON_CAN: PythonCANEngine,
        HardwareBackend.J2534_PASSTHRU: J2534CANEngine,
    }
    
    OBD_BACKENDS = {
        HardwareBackend.PYTHON_CAN: PythonOBDService,
        HardwareBackend.J2534_PASSTHRU: J2534OBDService,
    }
    
    def __init__(self):
        """Initialize hardware factory."""
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def get_available_backends() -> Dict[str, Dict[str, Any]]:
        """Get information about available hardware backends."""
        return {
            "can_backends": {
                backend.value: {
                    "class": cls.__name__,
                    "description": cls.__doc__.strip() if cls.__doc__ else "No description"
                }
                for backend, cls in HardwareFactory.CAN_BACKENDS.items()
            },
            "obd_backends": {
                backend.value: {
                    "class": cls.__name__,
                    "description": cls.__doc__.strip() if cls.__doc__ else "No description"
                }
                for backend, cls in HardwareFactory.OBD_BACKENDS.items()
            }
        }
    
    def create_can_engine(self, 
                         backend: HardwareBackend,
                         config: Optional[Dict[str, Any]] = None) -> MazdaCANEngine:
        """
        Create CAN engine with specified backend.
        
        Args:
            backend: Hardware backend to use
            config: Backend-specific configuration
            
        Returns:
            Configured CAN engine instance
        """
        if backend not in self.CAN_BACKENDS:
            raise ValueError(f"Unsupported CAN backend: {backend.value}")
        
        try:
            engine_class = self.CAN_BACKENDS[backend]
            engine = engine_class(config or {})
            
            self.logger.info(f"Created CAN engine with {backend.value} backend")
            return engine
            
        except Exception as e:
            self.logger.error(f"Failed to create CAN engine with {backend.value}: {e}")
            raise
    
    def create_obd_service(self,
                          backend: HardwareBackend,
                          config: Optional[Dict[str, Any]] = None) -> MazdaOBDService:
        """
        Create OBD service with specified backend.
        
        Args:
            backend: Hardware backend to use
            config: Backend-specific configuration
            
        Returns:
            Configured OBD service instance
        """
        if backend not in self.OBD_BACKENDS:
            raise ValueError(f"Unsupported OBD backend: {backend.value}")
        
        try:
            service_class = self.OBD_BACKENDS[backend]
            service = service_class(config or {})
            
            self.logger.info(f"Created OBD service with {backend.value} backend")
            return service
            
        except Exception as e:
            self.logger.error(f"Failed to create OBD service with {backend.value}: {e}")
            raise
    
    def create_hardware_pair(self,
                           backend: HardwareBackend,
                           can_config: Optional[Dict[str, Any]] = None,
                           obd_config: Optional[Dict[str, Any]] = None) -> tuple:
        """
        Create matching CAN engine and OBD service pair.
        
        Args:
            backend: Hardware backend to use for both
            can_config: CAN-specific configuration
            obd_config: OBD-specific configuration
            
        Returns:
            Tuple of (CAN engine, OBD service)
        """
        can_engine = self.create_can_engine(backend, can_config)
        obd_service = self.create_obd_service(backend, obd_config)
        
        return can_engine, obd_service
    
    def auto_detect_hardware(self) -> Optional[HardwareBackend]:
        """
        Auto-detect available hardware and return appropriate backend.
        
        Returns:
            Detected hardware backend or None if nothing found
        """
        # Try python-can first (most common for development)
        try:
            import can
            # Test if we can create a bus
            test_bus = can.interface.Bus(interface='socketcan', channel='can0')
            test_bus.shutdown()
            return HardwareBackend.PYTHON_CAN
        except Exception:
            pass
        
        # Try J2534 passthru
        try:
            import j2534
            # Test if we can load J2534 library
            j2534.j2534()
            return HardwareBackend.J2534_PASSTHRU
        except Exception:
            pass
        
        self.logger.warning("No compatible hardware detected")
        return None
    
    def validate_backend_compatibility(self, 
                                     can_backend: HardwareBackend,
                                     obd_backend: HardwareBackend) -> bool:
        """
        Validate if CAN and OBD backends are compatible.
        
        Args:
            can_backend: CAN backend
            obd_backend: OBD backend
            
        Returns:
            True if backends are compatible
        """
        # For now, require same backend for simplicity
        # In the future, this could be more sophisticated
        return can_backend == obd_backend


# Global factory instance
_factory_instance: Optional[HardwareFactory] = None


def get_factory() -> HardwareFactory:
    """Get global hardware factory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = HardwareFactory()
    return _factory_instance


def create_default_hardware() -> tuple:
    """
    Create default hardware configuration.
    
    Returns:
        Tuple of (CAN engine, OBD service) using auto-detected hardware
    """
    factory = get_factory()
    
    # Auto-detect hardware
    backend = factory.auto_detect_hardware()
    if backend is None:
        # Fallback to python-can
        backend = HardwareBackend.PYTHON_CAN
        logging.warning("Using python-can as fallback backend")
    
    return factory.create_hardware_pair(backend)
