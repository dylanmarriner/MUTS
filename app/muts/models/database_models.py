from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from enum import Enum

# Enums for vehicle classification
class TransmissionType(Enum):
    MANUAL = "MANUAL"
    DSG = "DSG"  # Volkswagen dual-clutch
    TCT = "TCT"  # Alfa Romeo Twin Clutch Transmission
    TORQUE_CONVERTER = "TORQUE_CONVERTER"
    CVT = "CVT"

class DrivetrainType(Enum):
    FWD = "FWD"
    RWD = "RWD"
    AWD_HALDEX = "AWD_HALDEX"  # Volkswagen Haldex system
    AWD_FULL = "AWD_FULL"  # Permanent AWD
    AWD_PART_TIME = "AWD_PART_TIME"

class User(db.Model):
    """User model for multi-user support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user, viewer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='user', lazy=True)
    sessions = db.relationship('UserSession', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

class UserSession(db.Model):
    """User session tracking"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'ip_address': self.ip_address,
            'is_active': self.is_active
        }

class AIModel(db.Model):
    """AI model tracking"""
    __tablename__ = 'ai_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # tuning, performance, diagnostic
    status = db.Column(db.String(20), default='inactive')  # active, inactive, training
    model_path = db.Column(db.String(255))
    training_data_count = db.Column(db.Integer, default=0)
    last_training = db.Column(db.DateTime)
    accuracy = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'model_type': self.model_type,
            'status': self.status,
            'training_data_count': self.training_data_count,
            'last_training': self.last_training.isoformat() if self.last_training else None,
            'accuracy': self.accuracy,
            'created_at': self.created_at.isoformat()
        }

class TrainingData(db.Model):
    """AI training data tracking"""
    __tablename__ = 'training_data'
    
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('ai_models.id'), nullable=False)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=True)
    data_type = db.Column(db.String(50), nullable=False)  # performance, diagnostic, tuning
    raw_data = db.Column(db.Text, nullable=False)  # JSON string
    labels = db.Column(db.Text)  # JSON string of labels
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_in_training = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_id': self.model_id,
            'data_type': self.data_type,
            'created_at': self.created_at.isoformat(),
            'used_in_training': self.used_in_training
        }

class SecurityEvent(db.Model):
    """Security event logging"""
    __tablename__ = 'security_events'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)  # login, flash, tuning, access_denied
    severity = db.Column(db.String(20), default='info')  # info, warning, critical
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'ip_address': self.ip_address,
            'success': self.success,
            'created_at': self.created_at.isoformat()
        }

class TelemetrySession(db.Model):
    """Telemetry data collection sessions"""
    __tablename__ = 'telemetry_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=False)
    name = db.Column(db.String(100))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # seconds
    data_points = db.Column(db.Integer, default=0)
    file_path = db.Column(db.String(255))  # Path to raw data file
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'name': self.name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'data_points': self.data_points,
            'file_path': self.file_path
        }

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


class DynoRun(Base):
    """Virtual dyno run results and metadata"""
    __tablename__ = 'dyno_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    telemetry_session_id = db.Column(db.Integer, db.ForeignKey('telemetry_sessions.id'))
    tuning_profile_id = db.Column(db.Integer, db.ForeignKey('tuning_profiles.id'))
    vehicle_constants_id = db.Column(db.Integer, db.ForeignKey('vehicle_constants.id'), nullable=False)
    
    # Run metadata
    run_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='PENDING')  # PENDING, PROCESSING, ACCEPTED, REJECTED
    rejection_reason = db.Column(db.Text)
    
    # Pull detection
    pull_start_time = db.Column(db.Float)
    pull_end_time = db.Column(db.Float)
    pulls_detected = db.Column(db.Integer, default=0)
    
    # Data quality
    sample_count = db.Column(db.Integer, default=0)
    valid_sample_count = db.Column(db.Integer, default=0)
    data_quality_score = db.Column(db.Float, default=0)
    
    # Confidence scoring
    confidence_score = db.Column(db.Float, default=0)
    confidence_rating = db.Column(db.String(10), default='LOW')  # HIGH, MEDIUM, LOW
    confidence_factors = db.Column(db.Text)  # JSON array of factors
    
    # Results (JSON encoded for flexibility)
    torque_curve = db.Column(db.Text)  # JSON array of [rpm, torque] pairs
    power_curve = db.Column(db.Text)  # JSON array of [rpm, power] pairs
    smoothed_torque_curve = db.Column(db.Text)
    smoothed_power_curve = db.Column(db.Text)
    
    # Peak values
    peak_torque = db.Column(db.Float)
    peak_torque_rpm = db.Column(db.Float)
    peak_power = db.Column(db.Float)
    peak_power_rpm = db.Column(db.Float)
    
    # Processing options
    smoothing_enabled = db.Column(db.Boolean, default=False)
    smoothing_window = db.Column(db.Integer, default=5)
    correction_factor = db.Column(db.Float, default=1.0)
    
    # Safety flags
    knock_detected = db.Column(db.Boolean, default=False)
    over_temp_detected = db.Column(db.Boolean, default=False)
    unsafe_afr_detected = db.Column(db.Boolean, default=False)
    
    # Relationships
    vehicle = db.relationship('Vehicle', backref='dyno_runs')
    telemetry_session = db.relationship('TelemetrySession')
    tuning_profile = db.relationship('TuningProfile')
    vehicle_constants = db.relationship('VehicleConstants')
    shift_events = db.relationship('DynoShiftEvent', back_populates='dyno_run')
    
    def get_torque_curve(self):
        if self.torque_curve:
            return json.loads(self.torque_curve)
        return []
    
    def set_torque_curve(self, curve):
        self.torque_curve = json.dumps(curve)
    
    def get_power_curve(self):
        if self.power_curve:
            return json.loads(self.power_curve)
        return []
    
    def set_power_curve(self, curve):
        self.power_curve = json.dumps(curve)
    
    def get_smoothed_torque_curve(self):
        if self.smoothed_torque_curve:
            return json.loads(self.smoothed_torque_curve)
        return []
    
    def set_smoothed_torque_curve(self, curve):
        self.smoothed_torque_curve = json.dumps(curve)
    
    def get_smoothed_power_curve(self):
        if self.smoothed_power_curve:
            return json.loads(self.smoothed_power_curve)
        return []
    
    def set_smoothed_power_curve(self, curve):
        self.smoothed_power_curve = json.dumps(curve)
    
    def get_confidence_factors(self):
        if self.confidence_factors:
            return json.loads(self.confidence_factors)
        return []
    
    def set_confidence_factors(self, factors):
        self.confidence_factors = json.dumps(factors)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'telemetry_session_id': self.telemetry_session_id,
            'tuning_profile_id': self.tuning_profile_id,
            'vehicle_constants_id': self.vehicle_constants_id,
            'vehicle_constants_version': self.vehicle_constants.version if self.vehicle_constants else None,
            'run_time': self.run_time.isoformat() if self.run_time else None,
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'pull_start_time': self.pull_start_time,
            'pull_end_time': self.pull_end_time,
            'pulls_detected': self.pulls_detected,
            'sample_count': self.sample_count,
            'valid_sample_count': self.valid_sample_count,
            'data_quality_score': self.data_quality_score,
            'confidence_score': self.confidence_score,
            'confidence_rating': self.confidence_rating,
            'confidence_factors': self.get_confidence_factors(),
            'torque_curve': self.get_torque_curve(),
            'power_curve': self.get_power_curve(),
            'smoothed_torque_curve': self.get_smoothed_torque_curve(),
            'smoothed_power_curve': self.get_smoothed_power_curve(),
            'peak_torque': self.peak_torque,
            'peak_torque_rpm': self.peak_torque_rpm,
            'peak_power': self.peak_power,
            'peak_power_rpm': self.peak_power_rpm,
            'sample_count': self.sample_count,
            'valid_sample_count': self.valid_sample_count,
            'data_quality_score': self.data_quality_score,
            'smoothing_enabled': self.smoothing_enabled,
            'smoothing_window': self.smoothing_window,
            'correction_factor': self.correction_factor
        }


class DynoShiftEvent(Base):
    """Stores detected shift events during dyno runs"""
    __tablename__ = 'dyno_shift_events'
    
    id = db.Column(db.Integer, primary_key=True)
    dyno_run_id = db.Column(db.Integer, db.ForeignKey('dyno_runs.id'), nullable=False)
    
    # Shift timing
    timestamp_start = db.Column(db.Float, nullable=False)  # seconds from run start
    timestamp_end = db.Column(db.Float, nullable=False)    # seconds from run start
    timestamp_peak = db.Column(db.Float)                   # Peak shift point
    
    # Shift metrics
    gear_ratio_before = db.Column(db.Float)  # Effective gear ratio before shift
    gear_ratio_after = db.Column(db.Float)   # Effective gear ratio after shift
    ratio_change_rate = db.Column(db.Float)   # Maximum |dG_eff/dt| during shift
    
    # Detection parameters
    detection_threshold = db.Column(db.Float, default=0.5)  # Threshold used for detection
    guard_window = db.Column(db.Float, default=0.5)        # Guard window duration
    
    # Shift characteristics
    shift_type = db.Column(db.String(20))  # UP/DOWN based on ratio change
    confidence = db.Column(db.Float, default=1.0)  # Detection confidence 0-1
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    dyno_run = db.relationship("DynoRun", back_populates="shift_events")


class VehicleConstantsPreset(Base):
    """Vehicle constants presets with hierarchical organization"""
    __tablename__ = 'vehicle_constants_presets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    
    # Hierarchical organization
    manufacturer = Column(String(100), nullable=False)
    platform = Column(String(100))
    model = Column(String(100), nullable=False)
    body = Column(String(50))  # Wagon, Sedan, Hatchback, Coupe, SUV, etc.
    generation = Column(String(50))
    variant = Column(String(100))
    year = Column(Integer)
    
    # Additional identifiers
    chassis = Column(String(50))
    engine = Column(String(100))
    
    # Transmission and drivetrain
    transmission_type = Column(Enum(TransmissionType))
    drivetrain_type = Column(Enum(DrivetrainType))
    
    # Mass properties
    vehicle_mass = Column(Float, nullable=False)  # Curb mass (kg)
    driver_fuel_estimate = Column(Float, default=95)  # Driver + fuel estimate (kg)
    
    # Aerodynamic properties
    drag_coefficient = Column(Float, nullable=False)
    frontal_area = Column(Float, nullable=False)  # m²
    
    # Rolling resistance
    rolling_resistance = Column(Float, nullable=False)
    
    # Environmental conditions
    air_density = Column(Float, default=1.225)  # kg/m³ at sea level, 15°C
    
    # Wheel properties
    wheel_radius = Column(Float, nullable=False)  # meters
    
    # Drivetrain properties
    drivetrain_efficiency = Column(Float, nullable=False)  # Base efficiency (0-1)
    coupling_loss_factor = Column(Float)  # Additional loss for AWD coupling systems
    manual_efficiency = Column(Float, default=0.90)  # Typical manual efficiency
    auto_efficiency = Column(Float, default=0.85)  # Typical auto efficiency
    
    # Test conditions
    road_grade = Column(Float, default=0.0)  # degrees
    gravity = Column(Float, default=9.80665)  # m/s²
    
    # Gearing
    final_drive_ratio = Column(Float, nullable=False)
    gear_ratios = Column(JSON)  # List of gear ratios
    
    # AWD specific
    awd_torque_split_front = Column(Float)  # 0-1 for AWD vehicles
    awd_torque_split_rear = Column(Float)  # 0-1 for AWD vehicles
    
    # Metadata
    source = Column(String(100))  # Source of data (OEM, measured, estimated)
    source_type = Column(String(20), default='OEM')  # OEM, USER_IMPORT, MEASURED
    notes = Column(Text)
    confidence_score = Column(Integer, default=100)  # 0-100
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    constants = relationship("VehicleConstants", back_populates="preset")
    
    def set_gear_ratios(self, ratios):
        """Set gear ratios from list"""
        self.gear_ratios = ratios
    
    def get_gear_ratios(self):
        """Get gear ratios as list"""
        return self.gear_ratios or []
    
    def to_dict(self):
        """Convert to dictionary with enum values"""
        return {
            'id': self.id,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'platform': self.platform,
            'model': self.model,
            'body': self.body,
            'generation': self.generation,
            'variant': self.variant,
            'year': self.year,
            'chassis': self.chassis,
            'engine': self.engine,
            'transmission_type': self.transmission_type.value if self.transmission_type else None,
            'drivetrain_type': self.drivetrain_type.value if self.drivetrain_type else None,
            'vehicle_mass': self.vehicle_mass,
            'driver_fuel_estimate': self.driver_fuel_estimate,
            'drag_coefficient': self.drag_coefficient,
            'frontal_area': self.frontal_area,
            'rolling_resistance': self.rolling_resistance,
            'air_density': self.air_density,
            'wheel_radius': self.wheel_radius,
            'drivetrain_efficiency': self.drivetrain_efficiency,
            'manual_efficiency': self.manual_efficiency,
            'auto_efficiency': self.auto_efficiency,
            'road_grade': self.road_grade,
            'gravity': self.gravity,
            'final_drive_ratio': self.final_drive_ratio,
            'gear_ratios': self.get_gear_ratios(),
            'awd_torque_split_front': self.awd_torque_split_front,
            'awd_torque_split_rear': self.awd_torque_split_rear,
            'source': self.source,
            'source_type': self.source_type,
            'notes': self.notes,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class VehicleConstants(db.Model):
    """Vehicle constants instances linked to specific vehicles with versioning"""
    __tablename__ = 'vehicle_constants'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=False)
    preset_id = db.Column(db.Integer, db.ForeignKey('vehicle_constants_presets.id'))
    version = db.Column(db.Integer, nullable=False)
    
    # Override values (NULL = use preset)
    override_vehicle_mass = db.Column(db.Float)
    override_driver_fuel_estimate = db.Column(db.Float)
    override_drag_coefficient = db.Column(db.Float)
    override_frontal_area = db.Column(db.Float)
    override_rolling_resistance = db.Column(db.Float)
    override_air_density = db.Column(db.Float)
    override_wheel_radius = db.Column(db.Float)
    override_drivetrain_efficiency = db.Column(db.Float)
    override_road_grade = db.Column(db.Float)
    override_gravity = db.Column(db.Float)
    override_gear_ratios = db.Column(db.Text)  # JSON
    override_final_drive_ratio = db.Column(db.Float)
    
    # Metadata
    note = db.Column(db.Text)  # Reason for modification
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=False)  # Only one version active per vehicle
    
    # Relationships
    vehicle = db.relationship('Vehicle', backref='constants_versions')
    preset = db.relationship('VehicleConstantsPreset')
    
    def get_effective_constants(self):
        """Get the effective constants (preset with overrides applied)"""
        if not self.preset:
            raise ValueError("Vehicle constants must have a preset")
        
        # Start with preset values
        constants = self.preset.to_dict()
        
        # Apply overrides
        if self.override_vehicle_mass is not None:
            constants['vehicle_mass'] = self.override_vehicle_mass
        if self.override_driver_fuel_estimate is not None:
            constants['driver_fuel_estimate'] = self.override_driver_fuel_estimate
        if self.override_drag_coefficient is not None:
            constants['drag_coefficient'] = self.override_drag_coefficient
        if self.override_frontal_area is not None:
            constants['frontal_area'] = self.override_frontal_area
        if self.override_rolling_resistance is not None:
            constants['rolling_resistance'] = self.override_rolling_resistance
        if self.override_air_density is not None:
            constants['air_density'] = self.override_air_density
        if self.override_wheel_radius is not None:
            constants['wheel_radius'] = self.override_wheel_radius
        if self.override_drivetrain_efficiency is not None:
            constants['drivetrain_efficiency'] = self.override_drivetrain_efficiency
        if self.override_road_grade is not None:
            constants['road_grade'] = self.override_road_grade
        if self.override_gravity is not None:
            constants['gravity'] = self.override_gravity
        if self.override_gear_ratios:
            constants['gear_ratios'] = json.loads(self.override_gear_ratios)
        if self.override_final_drive_ratio is not None:
            constants['final_drive_ratio'] = self.override_final_drive_ratio
        
        # Recalculate total mass
        constants['total_mass'] = constants['vehicle_mass'] + constants['driver_fuel_estimate']
        
        return constants
    
    def has_overrides(self):
        """Check if any overrides are set"""
        return any([
            self.override_vehicle_mass is not None,
            self.override_driver_fuel_estimate is not None,
            self.override_drag_coefficient is not None,
            self.override_frontal_area is not None,
            self.override_rolling_resistance is not None,
            self.override_air_density is not None,
            self.override_wheel_radius is not None,
            self.override_drivetrain_efficiency is not None,
            self.override_road_grade is not None,
            self.override_gravity is not None,
            self.override_gear_ratios is not None,
            self.override_final_drive_ratio is not None
        ])
    
    def get_confidence_score(self):
        """Calculate confidence score based on data completeness and source"""
        score = 100
        
        # Check if we have an OEM baseline
        if not self.preset or self.preset.source_type != 'OEM':
            score -= 20
        
        # Check for assumed values (overrides)
        if self.override_vehicle_mass is not None:
            # If mass differs significantly from OEM, mark as assumed
            if self.preset and abs(self.override_vehicle_mass - self.preset.vehicle_mass) > (self.preset.vehicle_mass * 0.1):
                score -= 15
        
        # Check for assumed aerodynamics
        if self.override_drag_coefficient is not None:
            score -= 10
        if self.override_frontal_area is not None:
            score -= 10
        
        # Check drivetrain efficiency
        if self.override_drivetrain_efficiency is not None:
            score -= 10
        
        # Check road grade (non-zero affects accuracy)
        effective_constants = self.get_effective_constants()
        if effective_constants.get('road_grade', 0) != 0:
            score -= 5
        
        # Check for large deviations from OEM baseline
        if self.preset:
            deviations = 0
            if abs(effective_constants['vehicle_mass'] - self.preset.vehicle_mass) > (self.preset.vehicle_mass * 0.1):
                deviations += 1
            if abs(effective_constants['drag_coefficient'] - self.preset.drag_coefficient) > (self.preset.drag_coefficient * 0.1):
                deviations += 1
            if abs(effective_constants['frontal_area'] - self.preset.frontal_area) > (self.preset.frontal_area * 0.1):
                deviations += 1
            
            if deviations >= 2:
                score -= 10
        
        # Check if this is an imported profile (not wizard-reviewed)
        if self.preset and self.preset.source_type == 'USER_IMPORT':
            score -= 5
        
        return max(0, score)
    
    def get_confidence_level(self):
        """Get confidence level as string"""
        score = self.get_confidence_score()
        if score >= 85:
            return 'HIGH'
        elif score >= 65:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_confidence_deductions(self):
        """Get list of confidence deductions for UI display"""
        deductions = []
        score = 100
        
        if not self.preset or self.preset.source_type != 'OEM':
            deductions.append("Missing OEM baseline (-20)")
            score -= 20
        
        if self.override_vehicle_mass is not None:
            if self.preset and abs(self.override_vehicle_mass - self.preset.vehicle_mass) > (self.preset.vehicle_mass * 0.1):
                deductions.append("Assumed mass (-15)")
                score -= 15
        
        if self.override_drag_coefficient is not None:
            deductions.append("Assumed drag coefficient (-10)")
            score -= 10
        if self.override_frontal_area is not None:
            deductions.append("Assumed frontal area (-10)")
            score -= 10
        
        if self.override_drivetrain_efficiency is not None:
            deductions.append("Unknown drivetrain efficiency (-10)")
            score -= 10
        
        effective_constants = self.get_effective_constants()
        if effective_constants.get('road_grade', 0) != 0:
            deductions.append("Unknown road grade (-5)")
            score -= 5
        
        if self.preset:
            deviations = 0
            if abs(effective_constants['vehicle_mass'] - self.preset.vehicle_mass) > (self.preset.vehicle_mass * 0.1):
                deviations += 1
            if abs(effective_constants['drag_coefficient'] - self.preset.drag_coefficient) > (self.preset.drag_coefficient * 0.1):
                deviations += 1
            if abs(effective_constants['frontal_area'] - self.preset.frontal_area) > (self.preset.frontal_area * 0.1):
                deviations += 1
            
            if deviations >= 2:
                deductions.append("Large deviation from OEM (-10)")
                score -= 10
        
        if self.preset and self.preset.source_type == 'USER_IMPORT':
            deductions.append("Imported profile (-5)")
            score -= 5
        
        return deductions
    
    def to_dict(self):
        effective = self.get_effective_constants()
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'preset_id': self.preset_id,
            'preset_name': self.preset.name if self.preset else None,
            'version': self.version,
            'constants': effective,
            'has_overrides': self.has_overrides(),
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'confidence_score': self.get_confidence_score(),
            'confidence_level': self.get_confidence_level(),
            'confidence_deductions': self.get_confidence_deductions()
        }
    """Individual telemetry samples used in dyno calculations"""
    __tablename__ = 'dyno_samples'
    
    id = db.Column(db.Integer, primary_key=True)
    dyno_run_id = db.Column(db.Integer, db.ForeignKey('dyno_runs.id'), nullable=False)
    
    # Timestamp
    timestamp = db.Column(db.Float, nullable=False)  # seconds from start
    
    # Raw telemetry inputs (must be stored)
    rpm = db.Column(db.Float, nullable=False)
    vehicle_speed = db.Column(db.Float, nullable=False)  # m/s
    throttle_position = db.Column(db.Float, nullable=False)  # 0-100%
    boost_pressure = db.Column(db.Float, nullable=False)  # kPa gauge
    afr = db.Column(db.Float, nullable=False)  # lambda or afr
    ignition_timing = db.Column(db.Float, nullable=False)  # degrees BTDC
    engine_load = db.Column(db.Float, nullable=False)  # 0-100%
    intake_temp = db.Column(db.Float, nullable=False)  # Celsius
    coolant_temp = db.Column(db.Float, nullable=False)  # Celsius
    
    # Calculated values
    acceleration = db.Column(db.Float)  # m/s^2
    wheel_torque = db.Column(db.Float)  # Nm
    engine_torque = db.Column(db.Float)  # Nm
    wheel_power = db.Column(db.Float)  # kW
    engine_power = db.Column(db.Float)  # kW
    
    # Force components (for transparency)
    force_tractive = db.Column(db.Float)  # N
    force_rolling_resistance = db.Column(db.Float)  # N
    force_aerodynamic = db.Column(db.Float)  # N
    force_grade = db.Column(db.Float)  # N
    gear_ratio = db.Column(db.Float)  # Detected gear ratio
    
    # Validation
    is_valid = db.Column(db.Boolean, default=False)
    rejection_flags = db.Column(db.Text)  # JSON array of rejection reasons
    
    def set_rejection_flags(self, flags):
        if flags:
            self.rejection_flags = json.dumps(flags)
        else:
            self.rejection_flags = None
    
    def get_rejection_flags(self):
        if self.rejection_flags:
            return json.loads(self.rejection_flags)
        return []
    
    def to_dict(self):
        return {
            'id': self.id,
            'dyno_run_id': self.dyno_run_id,
            'timestamp': self.timestamp,
            'rpm': self.rpm,
            'vehicle_speed': self.vehicle_speed,
            'throttle_position': self.throttle_position,
            'boost_pressure': self.boost_pressure,
            'afr': self.afr,
            'ignition_timing': self.ignition_timing,
            'engine_load': self.engine_load,
            'intake_temp': self.intake_temp,
            'coolant_temp': self.coolant_temp,
            'acceleration': self.acceleration,
            'wheel_torque': self.wheel_torque,
            'engine_torque': self.engine_torque,
            'wheel_power': self.wheel_power,
            'engine_power': self.engine_power,
            'force_tractive': self.force_tractive,
            'force_rolling_resistance': self.force_rolling_resistance,
            'force_aerodynamic': self.force_aerodynamic,
            'force_grade': self.force_grade,
            'gear_ratio': self.gear_ratio,
            'is_valid': self.is_valid,
            'rejection_flags': self.get_rejection_flags()
        }
