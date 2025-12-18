#!/usr/bin/env python3
"""
Admin Override System Database Models
"""

from datetime import datetime
from muts.models.database_models import db


class OverrideAuditLog(db.Model):
    """Immutable audit log for all override activity"""
    __tablename__ = 'override_audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Admin who initiated override
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Vehicle identification
    vehicle_vin = db.Column(db.String(17))
    vehicle_profile = db.Column(db.String(255))  # e.g. "Alfa Romeo Giulietta 2012"
    
    # Override details
    override_scope = db.Column(db.String(20), nullable=False)  # ACTION, MODULE, SESSION
    module = db.Column(db.String(50))  # e.g. ENGINE, ABS, SRS
    action = db.Column(db.String(50))  # e.g. READ_DTCS, CLEAR_DTCS, LIVE_DATA
    
    # Override parameters
    reason = db.Column(db.Text, nullable=False)
    duration_minutes = db.Column(db.Integer)  # For MODULE/SESSION overrides
    
    # Execution details
    result = db.Column(db.String(20), nullable=False)  # SUCCESS, FAILURE, ERROR
    error_message = db.Column(db.Text)
    
    # Tracking
    session_id = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    
    # Timestamps (immutable)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    admin_user = db.relationship('User', backref='override_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'admin_user_id': self.admin_user_id,
            'admin_username': self.admin_user.username if self.admin_user else 'Unknown',
            'vehicle_vin': self.vehicle_vin,
            'vehicle_profile': self.vehicle_profile,
            'override_scope': self.override_scope,
            'module': self.module,
            'action': self.action,
            'reason': self.reason,
            'duration_minutes': self.duration_minutes,
            'result': self.result,
            'error_message': self.error_message,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat()
        }
    
    # Prevent updates/deletes - audit log is immutable
    __table_args__ = {
        'sqlite_autoincrement': True
    }
