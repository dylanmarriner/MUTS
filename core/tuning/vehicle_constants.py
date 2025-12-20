#!/usr/bin/env python3
"""
Vehicle Constants Manager
Manages vehicle constants with database persistence, versioning, and validation
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ConstantsError(Exception):
    """Raised when constants validation fails"""
    pass

@dataclass
class VehicleConstants:
    """Vehicle constants for dyno calculations"""
    # Basic vehicle properties
    vehicle_mass: float  # kg - curb weight
    driver_fuel_mass: float  # kg - driver + fuel estimate
    
    # Aerodynamics
    drag_coefficient: float  # Cd - dimensionless
    frontal_area: float  # m² - frontal area
    air_density: float  # kg/m³ - air density at sea level
    
    # Rolling resistance
    rolling_resistance: float  # Crr - coefficient
    
    # Drivetrain
    gear_ratios: List[float]  # gear ratios
    final_drive_ratio: float  # final drive ratio
    drivetrain_efficiency: float  # η - efficiency (0-1)
    
    # Tires
    tire_radius: float  # m - loaded tire radius
    
    # Environment
    gravity: float  # m/s² - gravitational acceleration
    road_grade: float  # degrees - road grade (0 for flat)
    
    # Metadata
    version: int = 1
    source: str = ""
    created_at: Optional[datetime] = None
    is_active: bool = True
    
    def validate(self) -> List[str]:
        """Validate constants and return list of errors"""
        errors = []
        
        # Check required fields
        if self.vehicle_mass <= 0:
            errors.append("Vehicle mass must be positive")
        if self.vehicle_mass > 10000:
            errors.append("Vehicle mass seems too high (>10,000 kg)")
            
        if self.driver_fuel_mass < 0:
            errors.append("Driver/fuel mass cannot be negative")
        if self.driver_fuel_mass > 500:
            errors.append("Driver/fuel mass seems too high (>500 kg)")
            
        if self.drag_coefficient <= 0 or self.drag_coefficient > 2:
            errors.append("Drag coefficient must be between 0 and 2")
            
        if self.frontal_area <= 0 or self.frontal_area > 10:
            errors.append("Frontal area must be between 0 and 10 m²")
            
        if self.air_density <= 0:
            errors.append("Air density must be positive")
            
        if self.rolling_resistance < 0 or self.rolling_resistance > 0.1:
            errors.append("Rolling resistance must be between 0 and 0.1")
            
        if not self.gear_ratios or len(self.gear_ratios) < 5:
            errors.append("Must have at least 5 gear ratios")
        if any(g <= 0 for g in self.gear_ratios):
            errors.append("All gear ratios must be positive")
            
        if self.final_drive_ratio <= 0:
            errors.append("Final drive ratio must be positive")
            
        if self.drivetrain_efficiency <= 0 or self.drivetrain_efficiency > 1:
            errors.append("Drivetrain efficiency must be between 0 and 1")
            
        if self.tire_radius <= 0 or self.tire_radius > 1:
            errors.append("Tire radius must be between 0 and 1 meter")
            
        if self.gravity <= 0:
            errors.append("Gravity must be positive")
            
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VehicleConstants':
        """Create from dictionary"""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
    
    def get_total_mass(self) -> float:
        """Get total vehicle mass including driver and fuel"""
        return self.vehicle_mass + self.driver_fuel_mass

class VehicleConstantsManager:
    """Manages vehicle constants with database persistence"""
    
    def __init__(self, db_path: str = "vehicle_constants.db"):
        self.db_path = db_path
        self._init_database()
        self._cache: Dict[str, VehicleConstants] = {}
        
        logger.info(f"VehicleConstantsManager initialized with DB: {db_path}")
    
    def _init_database(self) -> None:
        """Initialize the database schema"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_constants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    constants_json TEXT NOT NULL,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    UNIQUE(vehicle_id, version)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS presets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manufacturer TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year INTEGER,
                    chassis TEXT,
                    engine TEXT,
                    constants_json TEXT NOT NULL,
                    editable BOOLEAN DEFAULT 1
                )
            """)
            
            conn.commit()
    
    def save_constants(self, vehicle_id: str, constants: VehicleConstants) -> int:
        """Save constants to database"""
        import sqlite3
        
        # Validate first
        errors = constants.validate()
        if errors:
            raise ConstantsError(f"Validation failed: {'; '.join(errors)}")
        
        with sqlite3.connect(self.db_path) as conn:
            # Deactivate previous versions
            conn.execute(
                "UPDATE vehicle_constants SET is_active = 0 WHERE vehicle_id = ?",
                (vehicle_id,)
            )
            
            # Insert new version
            cursor = conn.execute("""
                INSERT INTO vehicle_constants 
                (vehicle_id, version, constants_json, source, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (
                vehicle_id,
                constants.version,
                json.dumps(constants.to_dict()),
                constants.source,
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            const_id = cursor.lastrowid
            
        # Update cache
        cache_key = f"{vehicle_id}:v{constants.version}"
        self._cache[cache_key] = constants
        
        logger.info(f"Saved constants for {vehicle_id} version {constants.version}")
        return const_id
    
    def load_constants(self, vehicle_id: str, version: Optional[int] = None) -> VehicleConstants:
        """Load constants from database"""
        import sqlite3
        
        # Check cache first
        cache_key = f"{vehicle_id}:v{version}" if version else f"{vehicle_id}:active"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        with sqlite3.connect(self.db_path) as conn:
            if version:
                cursor = conn.execute("""
                    SELECT constants_json FROM vehicle_constants
                    WHERE vehicle_id = ? AND version = ?
                """, (vehicle_id, version))
            else:
                cursor = conn.execute("""
                    SELECT constants_json FROM vehicle_constants
                    WHERE vehicle_id = ? AND is_active = 1
                """, (vehicle_id,))
            
            row = cursor.fetchone()
            if not row:
                raise ConstantsError(f"No constants found for {vehicle_id}" + 
                                   (f" version {version}" if version else ""))
            
            data = json.loads(row[0])
            constants = VehicleConstants.from_dict(data)
            
            # Cache it
            self._cache[cache_key] = constants
            return constants
    
    def list_versions(self, vehicle_id: str) -> List[Tuple[int, datetime, str, bool]]:
        """List all versions for a vehicle"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT version, created_at, source, is_active
                FROM vehicle_constants
                WHERE vehicle_id = ?
                ORDER BY version DESC
            """, (vehicle_id,))
            
            return [
                (row[0] if row[0] is not None else 0, 
                 datetime.fromisoformat(row[1]) if row[1] else datetime.utcnow(), 
                 row[2] if row[2] is not None else "", 
                 bool(row[3]) if row[3] is not None else False)
                for row in cursor.fetchall()
            ]
    
    def save_preset(self, manufacturer: str, model: str, year: int,
                   chassis: str, engine: str, constants: VehicleConstants,
                   editable: bool = True) -> int:
        """Save a preset"""
        import sqlite3
        
        # Validate first
        errors = constants.validate()
        if errors:
            raise ConstantsError(f"Validation failed: {'; '.join(errors)}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO presets 
                (manufacturer, model, year, chassis, engine, constants_json, editable)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                manufacturer, model, year, chassis, engine,
                json.dumps(constants.to_dict()),
                editable
            ))
            
            conn.commit()
            return cursor.lastrowid or 0
    
    def load_preset(self, manufacturer: str, model: str, year: int,
                   chassis: Optional[str] = None) -> VehicleConstants:
        """Load a preset"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            if chassis:
                cursor = conn.execute("""
                    SELECT constants_json FROM presets
                    WHERE manufacturer = ? AND model = ? AND year = ? AND chassis = ?
                    LIMIT 1
                """, (manufacturer, model, year, chassis))
            else:
                cursor = conn.execute("""
                    SELECT constants_json FROM presets
                    WHERE manufacturer = ? AND model = ? AND year = ?
                    ORDER BY chassis DESC
                    LIMIT 1
                """, (manufacturer, model, year))
            
            row = cursor.fetchone()
            if not row:
                raise ConstantsError(f"No preset found for {manufacturer} {model} {year}")
            
            data = json.loads(row[0])
            return VehicleConstants.from_dict(data)
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """List all available presets"""
        import sqlite3
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT manufacturer, model, year, chassis, engine, editable
                FROM presets
                ORDER BY manufacturer, model, year
            """)
            
            return [
                {
                    'manufacturer': row[0],
                    'model': row[1],
                    'year': row[2],
                    'chassis': row[3],
                    'engine': row[4],
                    'editable': bool(row[5])
                }
                for row in cursor.fetchall()
            ]

# Global instance
_constants_manager: Optional[VehicleConstantsManager] = None

def get_constants_manager() -> VehicleConstantsManager:
    """Get the global constants manager"""
    global _constants_manager
    if _constants_manager is None:
        _constants_manager = VehicleConstantsManager()
    return _constants_manager

# Mazda Mazdaspeed 3 constants preset
MAZDASPEED3_CONSTANTS = VehicleConstants(
    vehicle_mass=1425,  # kg
    driver_fuel_mass=95,  # kg
    drag_coefficient=0.33,
    frontal_area=2.20,  # m²
    air_density=1.225,  # kg/m³
    rolling_resistance=0.013,
    gear_ratios=[3.538, 2.238, 1.535, 1.171, 0.971, 0.756],
    final_drive_ratio=3.529,
    drivetrain_efficiency=0.88,
    tire_radius=0.318,  # m
    gravity=9.80665,  # m/s²
    road_grade=0.0,
    source="Mazda BL OEM / Engineering Estimate",
    created_at=datetime.utcnow()
)
