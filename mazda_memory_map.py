"""
MazdaMemoryMap - ECU memory addresses, calibration tables, and flash regions.
Centralized memory layout for 2011 Mazdaspeed 3 MZR DISI 2.3L engine ECU.
Includes safety checks, checksums, and validation to prevent ECU bricking.
"""

import struct
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from models import SecurityLevel, LogEntry


class MemoryRegion(Enum):
    """ECU memory region types."""
    FLASH = "flash"
    EEPROM = "eeprom"
    RAM = "ram"
    CALIBRATION = "calibration"
    DIAGNOSTIC = "diagnostic"
    SECURITY = "security"
    BOOTLOADER = "bootloader"
    UNUSED = "unused"


class AccessType(Enum):
    """Memory access permissions."""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    WRITE_ONCE = "write_once"
    PROTECTED = "protected"
    SECURITY_CRITICAL = "security_critical"


@dataclass
class MemoryRange:
    """ECU memory range definition."""
    name: str
    start_address: int
    end_address: int
    size: int
    region_type: MemoryRegion
    access_type: AccessType
    description: str
    security_level: SecurityLevel = SecurityLevel.READ_ONLY
    checksum_offset: Optional[int] = None
    backup_required: bool = False
    critical: bool = False
    
    def __post_init__(self):
        """Validate memory range."""
        if self.end_address <= self.start_address:
            raise ValueError(f"Invalid memory range: end ({self.end_address}) <= start ({self.start_address})")
        
        calculated_size = self.end_address - self.start_address
        if calculated_size != self.size:
            raise ValueError(f"Size mismatch: calculated {calculated_size}, specified {self.size}")
    
    def contains(self, address: int) -> bool:
        """Check if address is within this range."""
        return self.start_address <= address < self.end_address
    
    def overlaps(self, other: 'MemoryRange') -> bool:
        """Check if this range overlaps with another."""
        return not (self.end_address <= other.start_address or 
                   other.end_address <= self.start_address)
    
    def get_checksum_range(self) -> Tuple[int, int]:
        """Get range for checksum calculation."""
        if self.checksum_offset is not None:
            return (self.start_address, self.checksum_offset)
        return (self.start_address, self.end_address)


@dataclass
class CalibrationTable:
    """ECU calibration table definition."""
    name: str
    address: int
    size: int
    axis_x: Optional[Dict[str, Any]] = None
    axis_y: Optional[Dict[str, Any]] = None
    data_type: str = "uint16"  # uint8, uint16, uint32, float
    description: str = ""
    units: str = ""
    min_value: float = 0.0
    max_value: float = 0.0
    default_values: Optional[List[Union[int, float]]] = None
    safety_limits: Optional[Dict[str, float]] = None
    
    def validate_value(self, value: Union[int, float]) -> bool:
        """Validate value against safety limits."""
        if self.safety_limits:
            return (self.safety_limits.get("min", float('-inf')) <= value <= 
                   self.safety_limits.get("max", float('inf')))
        return True


@dataclass
class FlashSector:
    """Flash sector definition for erasing/programming."""
    number: int
    start_address: int
    size: int
    erase_time_ms: int = 1000  # Typical erase time
    program_time_ms: int = 5   # Typical program time per byte
    protected: bool = False
    
    def contains(self, address: int) -> bool:
        """Check if address is within this sector."""
        return self.start_address <= address < self.start_address + self.size


class MemoryMapError(Exception):
    """Memory map related errors."""
    pass


class MazdaMemoryMap:
    """
    Comprehensive memory map for 2011 Mazdaspeed 3 ECU.
    Includes all memory regions, calibration tables, and safety information.
    """
    
    # 2011 Mazdaspeed 3 MZR DISI 2.3L ECU Memory Layout
    MEMORY_REGIONS = {
        # Main Flash Memory (2MB total)
        "BOOTLOADER": MemoryRange(
            name="Bootloader",
            start_address=0x000000,
            end_address=0x020000,
            size=0x020000,  # 128KB
            region_type=MemoryRegion.BOOTLOADER,
            access_type=AccessType.PROTECTED,
            description="ECU bootloader and recovery code",
            security_level=SecurityLevel.FLASH,
            critical=True,
            backup_required=True
        ),
        
        "CALIBRATION_MAIN": MemoryRange(
            name="Main Calibration",
            start_address=0x020000,
            end_address=0x180000,
            size=0x160000,  # 1.376MB
            region_type=MemoryRegion.CALIBRATION,
            access_type=AccessType.READ_WRITE,
            description="Main fuel, ignition, and boost calibration tables",
            security_level=SecurityLevel.TUNING,
            checksum_offset=0x17FFFC,
            backup_required=True
        ),
        
        "DIAGNOSTIC_DATA": MemoryRange(
            name="Diagnostic Data",
            start_address=0x180000,
            end_address=0x1C0000,
            size=0x040000,  # 256KB
            region_type=MemoryRegion.DIAGNOSTIC,
            access_type=AccessType.READ_WRITE,
            description="Diagnostic trouble codes, freeze frames, and adaptation data",
            security_level=SecurityLevel.DIAGNOSTIC
        ),
        
        "SECURITY_REGION": MemoryRange(
            name="Security Region",
            start_address=0x1C0000,
            end_address=0x1E0000,
            size=0x020000,  # 128KB
            region_type=MemoryRegion.SECURITY,
            access_type=AccessType.SECURITY_CRITICAL,
            description="Immobilizer keys, security seeds, and authentication data",
            security_level=SecurityLevel.ADMIN,
            critical=True,
            backup_required=True
        ),
        
        "VEHICLE_SPECIFIC": MemoryRange(
            name="Vehicle Specific Data",
            start_address=0x1E0000,
            end_address=0x1F0000,
            size=0x010000,  # 64KB
            region_type=MemoryRegion.FLASH,
            access_type=AccessType.WRITE_ONCE,
            description="VIN, configuration data, and vehicle-specific settings",
            security_level=SecurityLevel.ADMIN,
            backup_required=True
        ),
        
        "EEPROM_BACKUP": MemoryRange(
            name="EEPROM Backup",
            start_address=0x1F0000,
            end_address=0x200000,
            size=0x010000,  # 64KB
            region_type=MemoryRegion.EEPROM,
            access_type=AccessType.READ_WRITE,
            description="EEPROM data backup and configuration storage",
            security_level=SecurityLevel.DIAGNOSTIC
        ),
        
        # Internal RAM (256KB)
        "RAM_MAIN": MemoryRange(
            name="Main RAM",
            start_address=0x200000,
            end_address=0x240000,
            size=0x040000,  # 256KB
            region_type=MemoryRegion.RAM,
            access_type=AccessType.READ_WRITE,
            description="Main system RAM for variables and temporary data",
            security_level=SecurityLevel.DIAGNOSTIC
        ),
        
        "RAM_CALIBRATION": MemoryRange(
            name="Calibration RAM",
            start_address=0x240000,
            end_address=0x280000,
            size=0x040000,  # 256KB
            region_type=MemoryRegion.RAM,
            access_type=AccessType.READ_WRITE,
            description="RAM copy of calibration tables for real-time modification",
            security_level=SecurityLevel.TUNING
        ),
    }
    
    # Flash Sector Layout (4KB sectors typical)
    FLASH_SECTORS = [
        FlashSector(i, i * 0x1000, 0x1000, protected=(i < 32))  # First 128KB protected
        for i in range(512)  # 512 sectors * 4KB = 2MB
    ]
    
    # Main Calibration Tables
    CALIBRATION_TABLES = {
        # Fuel System
        "FUEL_BASE_MAP": CalibrationTable(
            name="Fuel Base Map",
            address=0x020000,
            size=0x1000,  # 4KB
            axis_x={"name": "RPM", "size": 16, "values": [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000]},
            axis_y={"name": "Load", "size": 16, "values": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150]},
            data_type="float",
            description="Base fuel injection map",
            units="ms",
            safety_limits={"min": 0.5, "max": 25.0}
        ),
        
        "FUEL_TRIM_MAP": CalibrationTable(
            name="Fuel Trim Map",
            address=0x021000,
            size=0x0800,  # 2KB
            axis_x={"name": "RPM", "size": 16},
            axis_y={"name": "Load", "size": 8},
            data_type="float",
            description="Fuel trim corrections",
            units="%",
            safety_limits={"min": -25.0, "max": 25.0}
        ),
        
        # Ignition System
        "IGNITION_TIMING_MAP": CalibrationTable(
            name="Ignition Timing Map",
            address=0x022000,
            size=0x1000,  # 4KB
            axis_x={"name": "RPM", "size": 16},
            axis_y={"name": "Load", "size": 16},
            data_type="float",
            description="Base ignition timing map",
            units="degrees BTDC",
            safety_limits={"min": -20.0, "max": 60.0}
        ),
        
        "IGNITION_CORRECTION_MAP": CalibrationTable(
            name="Ignition Correction Map",
            address=0x023000,
            size=0x0800,  # 2KB
            axis_x={"name": "RPM", "size": 16},
            axis_y={"name": "IAT", "size": 8},
            data_type="float",
            description="Ignition timing corrections for intake air temperature",
            units="degrees",
            safety_limits={"min": -10.0, "max": 10.0}
        ),
        
        # Boost System
        "BOOST_TARGET_MAP": CalibrationTable(
            name="Boost Target Map",
            address=0x024000,
            size=0x0800,  # 2KB
            axis_x={"name": "RPM", "size": 16},
            axis_y={"name": "Throttle", "size": 8},
            data_type="float",
            description="Target boost pressure map",
            units="psi",
            safety_limits={"min": 0.0, "max": 30.0}
        ),
        
        "WASTEGATE_DUTY_MAP": CalibrationTable(
            name="Wastegate Duty Map",
            address=0x024800,
            size=0x0800,  # 2KB
            axis_x={"name": "RPM", "size": 16},
            axis_y={"name": "Target Boost", "size": 8},
            data_type="float",
            description="Wastegate duty cycle map",
            units="%",
            safety_limits={"min": 0.0, "max": 100.0}
        ),
        
        # Engine Protection
        "REV_LIMITER": CalibrationTable(
            name="Rev Limiter",
            address=0x025000,
            size=0x20,   # 32 bytes
            data_type="uint16",
            description="Engine RPM limiters",
            units="RPM",
            safety_limits={"min": 1000, "max": 8000}
        ),
        
        "BOOST_LIMITER": CalibrationTable(
            name="Boost Limiter",
            address=0x025020,
            size=0x20,   # 32 bytes
            data_type="float",
            description="Maximum boost pressure limits",
            units="psi",
            safety_limits={"min": 0.0, "max": 30.0}
        ),
        
        "TEMP_PROTECTION": CalibrationTable(
            name="Temperature Protection",
            address=0x025040,
            size=0x40,   # 64 bytes
            data_type="uint16",
            description="Engine temperature protection thresholds",
            units="°C",
            safety_limits={"min": 60, "max": 120}
        ),
        
        # Fuel System
        "FUEL_PRESSURE_TARGET": CalibrationTable(
            name="Fuel Pressure Target",
            address=0x025080,
            size=0x40,   # 64 bytes
            data_type="float",
            description="High pressure fuel pump target pressure",
            units="MPa",
            safety_limits={"min": 2.0, "max": 20.0}
        ),
        
        "INJECTOR_SIZING": CalibrationTable(
            name="Injector Sizing",
            address=0x0250C0,
            size=0x40,   # 64 bytes
            data_type="float",
            description="Fuel injector flow rates and dead times",
            units="cc/min",
            safety_limits={"min": 300, "max": 2000}
        ),
        
        # Variable Valve Timing
        "VVT_MAP": CalibrationTable(
            name="Variable Valve Timing Map",
            address=0x025100,
            size=0x0800,  # 2KB
            axis_x={"name": "RPM", "size": 16},
            axis_y={"name": "Load", "size": 16},
            data_type="float",
            description="Variable valve timing map",
            units="degrees",
            safety_limits={"min": -20.0, "max": 60.0}
        ),
        
        # Drive-by-Wire
        "THROTTLE_MAP": CalibrationTable(
            name="Throttle Response Map",
            address=0x025900,
            size=0x0400,  # 1KB
            axis_x={"name": "Pedal Position", "size": 16},
            axis_y={"name": "RPM", "size": 16},
            data_type="float",
            description="Drive-by-wire throttle response map",
            units="%",
            safety_limits={"min": 0.0, "max": 100.0}
        ),
        
        # Diagnostic Tables
        "DTC_THRESHOLDS": CalibrationTable(
            name="DTC Thresholds",
            address=0x180000,
            size=0x2000,  # 8KB
            data_type="float",
            description="Diagnostic trouble code thresholds",
            units="various",
            security_level=SecurityLevel.DIAGNOSTIC
        ),
        
        "ADAPTATION_VALUES": CalibrationTable(
            name="Adaptation Values",
            address=0x182000,
            size=0x1000,  # 4KB
            data_type="float",
            description="Fuel and ignition adaptation values",
            units="various",
            security_level=SecurityLevel.DIAGNOSTIC
        ),
    }
    
    # Critical Memory Addresses
    CRITICAL_ADDRESSES = {
        "VIN": 0x1E0000,
        "CALIBRATION_VERSION": 0x1E0100,
        "ECU_SERIAL": 0x1E0200,
        "IMMOBILIZER_KEY_1": 0x1C0000,
        "IMMOBILIZER_KEY_2": 0x1C0010,
        "SECURITY_SEED": 0x1C0020,
        "FLASH_CHECKSUM": 0x17FFFC,
        "BOOTLOADER_VERSION": 0x000100,
        "SOFTWARE_VERSION": 0x1E0300,
    }
    
    def __init__(self):
        """Initialize memory map."""
        self.logger = logging.getLogger(__name__)
        
        # Validate memory regions don't overlap
        self._validate_memory_regions()
        
        # Build lookup dictionaries
        self._build_lookup_tables()
        
        # Calculate checksums for critical regions
        self._calculate_region_checksums()
        
        self.logger.info("MazdaMemoryMap initialized for 2011 Mazdaspeed 3")
    
    def _validate_memory_regions(self) -> None:
        """Validate that memory regions don't overlap."""
        regions = list(self.MEMORY_REGIONS.values())
        
        for i, region1 in enumerate(regions):
            for region2 in regions[i+1:]:
                if region1.overlaps(region2):
                    raise MemoryMapError(
                        f"Memory regions overlap: {region1.name} ({region1.start_address:06X}-{region1.end_address:06X}) "
                        f"and {region2.name} ({region2.start_address:06X}-{region2.end_address:06X})"
                    )
    
    def _build_lookup_tables(self) -> None:
        """Build lookup tables for fast access."""
        self.address_to_region: Dict[int, MemoryRange] = {}
        self.region_by_name: Dict[str, MemoryRange] = {}
        self.table_by_name: Dict[str, CalibrationTable] = {}
        self.sector_by_address: Dict[int, FlashSector] = {}
        
        # Map addresses to regions
        for region in self.MEMORY_REGIONS.values():
            self.region_by_name[region.name] = region
            for addr in range(region.start_address, region.end_address):
                self.address_to_region[addr] = region
        
        # Map table names
        for table in self.CALIBRATION_TABLES.values():
            self.table_by_name[table.name] = table
        
        # Map addresses to sectors
        for sector in self.FLASH_SECTORS:
            for addr in range(sector.start_address, sector.start_address + sector.size):
                self.sector_by_address[addr] = sector
    
    def _calculate_region_checksums(self) -> None:
        """Calculate expected checksums for critical regions."""
        self.region_checksums: Dict[str, str] = {}
        
        for region in self.MEMORY_REGIONS.values():
            if region.checksum_offset is not None:
                # Create checksum placeholder (would be calculated from actual data)
                checksum_range = region.get_checksum_range()
                checksum_input = f"{region.name}:{checksum_range[0]:06X}-{checksum_range[1]:06X}"
                self.region_checksums[region.name] = hashlib.sha256(checksum_input.encode()).hexdigest()[:16]
    
    def get_region(self, address: int) -> Optional[MemoryRange]:
        """
        Get memory region for address.
        
        Args:
            address: Memory address
            
        Returns:
            MemoryRange containing the address or None
        """
        return self.address_to_region.get(address)
    
    def get_region_by_name(self, name: str) -> Optional[MemoryRange]:
        """
        Get memory region by name.
        
        Args:
            name: Region name
            
        Returns:
            MemoryRange or None if not found
        """
        return self.region_by_name.get(name)
    
    def get_table(self, name: str) -> Optional[CalibrationTable]:
        """
        Get calibration table by name.
        
        Args:
            name: Table name
            
        Returns:
            CalibrationTable or None if not found
        """
        return self.table_by_name.get(name)
    
    def get_sector(self, address: int) -> Optional[FlashSector]:
        """
        Get flash sector for address.
        
        Args:
            address: Memory address
            
        Returns:
            FlashSector containing the address or None
        """
        return self.sector_by_address.get(address)
    
    def get_sectors_for_range(self, start_address: int, end_address: int) -> List[FlashSector]:
        """
        Get all flash sectors that overlap with address range.
        
        Args:
            start_address: Start address
            end_address: End address
            
        Returns:
            List of overlapping FlashSectors
        """
        sectors = []
        for addr in range(start_address, end_address):
            sector = self.get_sector(addr)
            if sector and sector not in sectors:
                sectors.append(sector)
        return sorted(sectors, key=lambda s: s.number)
    
    def validate_access(self, address: int, size: int, 
                       security_level: SecurityLevel = SecurityLevel.READ_ONLY,
                       write_access: bool = False) -> bool:
        """
        Validate memory access permissions.
        
        Args:
            address: Starting address
            size: Size of access
            security_level: User's security level
            write_access: Whether this is a write operation
            
        Returns:
            True if access is allowed
        """
        end_address = address + size
        
        # Check each address in the range
        for addr in range(address, end_address):
            region = self.get_region(addr)
            if not region:
                return False  # Address not in any defined region
            
            # Check security level
            if security_level.value < region.security_level.value:
                return False
            
            # Check write access
            if write_access:
                if region.access_type == AccessType.READ_ONLY:
                    return False
                elif region.access_type == AccessType.PROTECTED:
                    return False
                elif region.access_type == AccessType.SECURITY_CRITICAL:
                    return security_level == SecurityLevel.ADMIN
        
        return True
    
    def is_critical_address(self, address: int) -> bool:
        """
        Check if address is in a critical region.
        
        Args:
            address: Memory address
            
        Returns:
            True if address is critical
        """
        region = self.get_region(address)
        return region.critical if region else False
    
    def requires_backup(self, address: int, size: int) -> bool:
        """
        Check if memory range requires backup before modification.
        
        Args:
            address: Starting address
            size: Size of range
            
        Returns:
            True if backup is required
        """
        end_address = address + size
        
        for addr in range(address, end_address):
            region = self.get_region(addr)
            if region and region.backup_required:
                return True
        
        return False
    
    def get_critical_addresses(self) -> Dict[str, int]:
        """Get dictionary of critical memory addresses."""
        return self.CRITICAL_ADDRESSES.copy()
    
    def get_calibration_tables(self) -> Dict[str, CalibrationTable]:
        """Get all calibration tables."""
        return self.CALIBRATION_TABLES.copy()
    
    def get_memory_regions(self) -> Dict[str, MemoryRange]:
        """Get all memory regions."""
        return self.MEMORY_REGIONS.copy()
    
    def get_flash_sectors(self) -> List[FlashSector]:
        """Get all flash sectors."""
        return self.FLASH_SECTORS.copy()
    
    def calculate_checksum(self, data: bytes, algorithm: str = "crc32") -> str:
        """
        Calculate checksum for data block.
        
        Args:
            data: Data to checksum
            algorithm: Checksum algorithm (crc32, sha256, md5)
            
        Returns:
            Hexadecimal checksum string
        """
        if algorithm == "crc32":
            return format(struct.unpack('>I', struct.pack('>I', 0))[0] ^ 0xFFFFFFFF, '08X')
        elif algorithm == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(data).hexdigest()
        else:
            raise ValueError(f"Unsupported checksum algorithm: {algorithm}")
    
    def validate_table_data(self, table_name: str, data: List[Union[int, float]]) -> List[str]:
        """
        Validate calibration table data against safety limits.
        
        Args:
            table_name: Name of calibration table
            data: Data values to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        table = self.get_table(table_name)
        
        if not table:
            errors.append(f"Unknown calibration table: {table_name}")
            return errors
        
        if len(data) != table.size // 2:  # Assuming 2-byte values
            errors.append(f"Data size mismatch: expected {table.size // 2}, got {len(data)}")
        
        for i, value in enumerate(data):
            if not table.validate_value(value):
                errors.append(f"Value {value} at index {i} exceeds safety limits")
        
        return errors
    
    def get_safe_write_regions(self, security_level: SecurityLevel) -> List[MemoryRange]:
        """
        Get regions that can be safely written with given security level.
        
        Args:
            security_level: User's security level
            
        Returns:
            List of writable MemoryRanges
        """
        writable_regions = []
        
        for region in self.MEMORY_REGIONS.values():
            if (security_level.value >= region.security_level.value and
                region.access_type in [AccessType.READ_WRITE, AccessType.WRITE_ONCE]):
                writable_regions.append(region)
        
        return writable_regions
    
    def export_memory_map(self) -> Dict[str, Any]:
        """
        Export memory map configuration.
        
        Returns:
            Dictionary representation of memory map
        """
        return {
            "memory_regions": {
                name: {
                    "start_address": f"0x{region.start_address:06X}",
                    "end_address": f"0x{region.end_address:06X}",
                    "size": f"0x{region.size:X}",
                    "type": region.region_type.value,
                    "access": region.access_type.value,
                    "security_level": region.security_level.value,
                    "critical": region.critical,
                    "backup_required": region.backup_required,
                }
                for name, region in self.MEMORY_REGIONS.items()
            },
            "calibration_tables": {
                name: {
                    "address": f"0x{table.address:06X}",
                    "size": f"0x{table.size:X}",
                    "data_type": table.data_type,
                    "description": table.description,
                    "units": table.units,
                }
                for name, table in self.CALIBRATION_TABLES.items()
            },
            "critical_addresses": {
                name: f"0x{address:06X}"
                for name, address in self.CRITICAL_ADDRESSES.items()
            },
            "flash_sectors": len(self.FLASH_SECTORS),
            "total_flash_size": f"0x{len(self.FLASH_SECTORS) * 0x1000:X}",
        }
    
    def __del__(self):
        """Cleanup on deletion."""
        self.logger.info("MazdaMemoryMap shutdown")
