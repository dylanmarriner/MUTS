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
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mode': self.mode,
            'boost_maps': self.get_boost_maps(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }