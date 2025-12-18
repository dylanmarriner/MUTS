from app import db
from datetime import datetime
import json

class Vehicle(db.Model):
    """Vehicle model for Mazdaspeed 3 2011 specific data"""
    __tablename__ = 'vehicles'
    
    id = db.Column(db.String(17), primary_key=True)  # VIN
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model = db.Column(db.String(50), nullable=False)  # 'Mazdaspeed 3 2011'
    ecu_type = db.Column(db.String(50), default='MZR 2.3L DISI TURBO')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ecu_data = db.relationship('ECUData', backref='vehicle', lazy=True)
    dtcs = db.relationship('DiagnosticTroubleCode', backref='vehicle', lazy=True)
    tuning_profiles = db.relationship('TuningProfile', backref='vehicle', lazy=True)
    
    def to_dict(self):
        return {
            'vin': self.id,
            'model': self.model,
            'ecu_type': self.ecu_type,
            'created_at': self.created_at.isoformat()
        }

class ECUData(db.Model):
    """Real-time ECU data storage"""
    __tablename__ = 'ecu_data'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Engine parameters
    rpm = db.Column(db.Integer)
    boost_psi = db.Column(db.Float)
    throttle_position = db.Column(db.Float)
    ignition_timing = db.Column(db.Float)
    fuel_trim_long = db.Column(db.Float)
    fuel_trim_short = db.Column(db.Float)
    maf_voltage = db.Column(db.Float)
    afr = db.Column(db.Float)
    coolant_temp = db.Column(db.Float)
    intake_temp = db.Column(db.Float)
    
    # Calculated parameters
    knock_count = db.Column(db.Integer)
    vvt_advance = db.Column(db.Float)
    calculated_load = db.Column(db.Float)
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class DiagnosticTroubleCode(db.Model):
    """DTC storage with Mazda-specific codes"""
    __tablename__ = 'trouble_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=False)
    code = db.Column(db.String(5), nullable=False)  # P0301, etc.
    description = db.Column(db.Text)
    severity = db.Column(db.String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    cleared_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'code': self.code,
            'description': self.description,
            'severity': self.severity,
            'detected_at': self.detected_at.isoformat(),
            'cleared_at': self.cleared_at.isoformat() if self.cleared_at else None
        }

class TuningProfile(db.Model):
    """Tuning profiles for different driving modes"""
    __tablename__ = 'tuning_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # 'Performance', 'Economy', etc.
    mode = db.Column(db.String(20), nullable=False)  # PERFORMANCE, ECONOMY, STOCK, HIGHWAY
    
    # Tuning parameters (JSON encoded)
    boost_maps = db.Column(db.Text)  # JSON string of boost targets
    fuel_maps = db.Column(db.Text)   # JSON string of fuel adjustments
    timing_maps = db.Column(db.Text) # JSON string of ignition timing
    vvt_maps = db.Column(db.Text)    # JSON string of VVT adjustments
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    
    def get_boost_maps(self):
        return json.loads(self.boost_maps) if self.boost_maps else {}
    
    def set_boost_maps(self, maps_dict):
        self.boost_maps = json.dumps(maps_dict)
    
    def get_fuel_maps(self):
        return json.loads(self.fuel_maps) if self.fuel_maps else {}
    
    def set_fuel_maps(self, maps_dict):
        self.fuel_maps = json.dumps(maps_dict)
    
    def get_timing_maps(self):
        return json.loads(self.timing_maps) if self.timing_maps else {}
    
    def set_timing_maps(self, maps_dict):
        self.timing_maps = json.dumps(maps_dict)
    
    def get_vvt_maps(self):
        return json.loads(self.vvt_maps) if self.vvt_maps else {}
    
    def set_vvt_maps(self, maps_dict):
        self.vvt_maps = json.dumps(maps_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mode': self.mode,
            'boost_maps': self.get_boost_maps(),
            'fuel_maps': self.get_fuel_maps(),
            'timing_maps': self.get_timing_maps(),
            'vvt_maps': self.get_vvt_maps(),
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

class LogEntry(db.Model):
    """Log entries for debugging and analysis"""
    __tablename__ = 'log_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    level = db.Column(db.String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    module = db.Column(db.String(50))  # Module that generated the log
    message = db.Column(db.Text, nullable=False)
    data = db.Column(db.Text)  # Additional data as JSON
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'module': self.module,
            'message': self.message,
            'data': json.loads(self.data) if self.data else None
        }

class PerformanceRun(db.Model):
    """Performance tracking data"""
    __tablename__ = 'performance_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=False)
    run_type = db.Column(db.String(20), nullable=False)  # 0-60, 1/4 mile, lap time
    
    # Run data
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Float)  # Duration in seconds
    
    # Environmental conditions
    ambient_temp = db.Column(db.Float)
    humidity = db.Column(db.Float)
    altitude = db.Column(db.Float)
    barometric_pressure = db.Column(db.Float)
    
    # Vehicle conditions
    fuel_type = db.Column(db.String(20))
    tire_pressure = db.Column(db.String(50))
    modification_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'run_type': self.run_type,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration': self.duration,
            'ambient_temp': self.ambient_temp,
            'humidity': self.humidity,
            'altitude': self.altitude,
            'barometric_pressure': self.barometric_pressure,
            'fuel_type': self.fuel_type,
            'tire_pressure': self.tire_pressure,
            'modification_notes': self.modification_notes,
            'created_at': self.created_at.isoformat()
        }

class FlashHistory(db.Model):
    """ECU flash history tracking"""
    __tablename__ = 'flash_history'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=False)
    
    # Flash details
    flash_type = db.Column(db.String(20), nullable=False)  # FULL, PARTIAL, CALIBRATION
    calibration_id = db.Column(db.String(50))
    software_version = db.Column(db.String(20))
    
    # Flash status
    status = db.Column(db.String(20), nullable=False)  # SUCCESS, FAILED, IN_PROGRESS
    error_message = db.Column(db.Text)
    
    # Timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # Duration in seconds
    
    # Metadata
    notes = db.Column(db.Text)
    backup_path = db.Column(db.String(255))  # Path to backup file
    
    def to_dict(self):
        return {
            'id': self.id,
            'flash_type': self.flash_type,
            'calibration_id': self.calibration_id,
            'software_version': self.software_version,
            'status': self.status,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'notes': self.notes,
            'backup_path': self.backup_path
        }
