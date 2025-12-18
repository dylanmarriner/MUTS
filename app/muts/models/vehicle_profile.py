#!/usr/bin/env python3
"""
Vehicle Profile model for specific vehicle instances
Links VIN-based vehicles to constants presets and stores additional identifiers
"""

from datetime import datetime
from muts.models.database_models import db, User, VehicleConstantsPreset, VehicleConstants


class VehicleProfile(db.Model):
    """Specific vehicle instance profile with exact identifiers"""
    __tablename__ = 'vehicle_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Vehicle identification
    vin = db.Column(db.String(17), db.ForeignKey('vehicles.id'), nullable=False, unique=True)
    plate = db.Column(db.String(20), nullable=False)
    engine_number = db.Column(db.String(50), nullable=False)
    
    # Vehicle details
    year = db.Column(db.Integer, nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    submodel = db.Column(db.String(100), nullable=False)
    body = db.Column(db.String(50), nullable=False)
    
    # Engine details
    displacement = db.Column(db.Integer)  # cc
    fuel_type = db.Column(db.String(20))
    colour = db.Column(db.String(30))
    
    # Relationships to existing models
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    constants_preset_id = db.Column(db.Integer, db.ForeignKey('vehicle_constants_presets.id'))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    user = db.relationship('User', backref='vehicle_profiles')
    vehicle = db.relationship('Vehicle', backref='profile', uselist=False)
    constants_preset = db.relationship('VehicleConstantsPreset')
    constants_versions = db.relationship('VehicleConstants', backref='profile')
    
    def get_display_name(self):
        """Get formatted display name for UI"""
        return f"{self.make} {self.model} {self.submodel} ({self.year}) {self.body} [{self.vin[-4:]}]"
    
    def get_constants(self):
        """Get active vehicle constants"""
        active_constants = VehicleConstants.query.filter_by(
            vehicle_id=self.vin,
            is_active=True
        ).first()
        return active_constants
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'vin': self.vin,
            'plate': self.plate,
            'engine_number': self.engine_number,
            'year': self.year,
            'make': self.make,
            'model': self.model,
            'submodel': self.submodel,
            'body': self.body,
            'displacement': self.displacement,
            'fuel_type': self.fuel_type,
            'colour': self.colour,
            'user_id': self.user_id,
            'constants_preset_id': self.constants_preset_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'display_name': self.get_display_name()
        }
