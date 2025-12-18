#!/usr/bin/env python3
"""
Forensic Replay System Database Models
Immutable storage for diagnostic session reconstruction
"""

from datetime import datetime
from muts.models.database_models import db
import hashlib


class ForensicSession(db.Model):
    """Immutable forensic session for admin override diagnostics"""
    __tablename__ = 'forensic_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Session identification
    session_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(255), nullable=False)  # Electron session ID
    
    # Admin and vehicle info
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_vin = db.Column(db.String(17))
    vehicle_profile = db.Column(db.String(255))
    
    # Override details
    override_scope = db.Column(db.String(20))  # ACTION, MODULE, SESSION
    override_reason = db.Column(db.Text)
    
    # Session timing
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    # Session state
    session_type = db.Column(db.String(20), default='OVERRIDE')  # OVERRIDE, DRY_RUN, LIVE
    was_dry_run = db.Column(db.Boolean, default=False)
    
    # Integrity
    event_count = db.Column(db.Integer, default=0)
    integrity_hash = db.Column(db.String(64))
    
    # Relationships
    admin_user = db.relationship('User', backref='forensic_sessions')
    events = db.relationship('ForensicEvent', backref='session', lazy='dynamic', 
                           order_by='ForensicEvent.sequence_number')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_hash': self.session_hash,
            'session_id': self.session_id,
            'admin_user_id': self.admin_user_id,
            'admin_username': self.admin_user.username if self.admin_user else 'Unknown',
            'vehicle_vin': self.vehicle_vin,
            'vehicle_profile': self.vehicle_profile,
            'override_scope': self.override_scope,
            'override_reason': self.override_reason,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'session_type': self.session_type,
            'was_dry_run': self.was_dry_run,
            'event_count': self.event_count,
            'integrity_hash': self.integrity_hash
        }
    
    def calculate_integrity(self):
        """Calculate integrity hash from all events"""
        hash_input = f"{self.id}:{self.session_hash}:{self.started_at.isoformat()}"
        
        for event in self.events.order_by(ForensicEvent.sequence_number):
            hash_input += f":{event.sequence_number}:{event.event_hash}"
        
        return hashlib.sha256(hash_input.encode()).hexdigest()


class ForensicEvent(db.Model):
    """Immutable forensic event within a session"""
    __tablename__ = 'forensic_events'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('forensic_sessions.id'), nullable=False)
    sequence_number = db.Column(db.Integer, nullable=False)
    
    # Event identification
    event_hash = db.Column(db.String(64), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # DIAGNOSTIC, OVERRIDE, ERROR
    
    # Timing
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Diagnostic details
    module = db.Column(db.String(50))  # ENGINE, ABS, SRS, etc.
    service = db.Column(db.String(50))  # READ_DTCS, CLEAR_DTCS, etc.
    
    # Capability state
    capability_supported = db.Column(db.Boolean)
    capability_reason = db.Column(db.Text)
    
    # Override state
    override_active = db.Column(db.Boolean, default=False)
    override_scope = db.Column(db.String(20))
    override_reason = db.Column(db.Text)
    
    # Execution state
    execution_mode = db.Column(db.String(20), default='LIVE')  # LIVE, DRY_RUN, BLOCKED
    would_execute = db.Column(db.Boolean)  # For dry-run predictions
    
    # Command details (redacted if sensitive)
    command_payload = db.Column(db.Text)  # Raw command sent
    command_response = db.Column(db.Text)  # Raw ECU response
    
    # Result
    result_status = db.Column(db.String(20))  # SUCCESS, FAILURE, BLOCKED
    result_data = db.Column(db.Text)  # JSON result data
    error_message = db.Column(db.Text)
    
    # UI context
    ui_action = db.Column(db.String(100))  # Button clicked, etc.
    ui_context = db.Column(db.Text)  # Additional UI state
    
    # Write protection
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally including sensitive data"""
        data = {
            'id': self.id,
            'session_id': self.session_id,
            'sequence_number': self.sequence_number,
            'event_hash': self.event_hash,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'module': self.module,
            'service': self.service,
            'capability_supported': self.capability_supported,
            'capability_reason': self.capability_reason,
            'override_active': self.override_active,
            'override_scope': self.override_scope,
            'override_reason': self.override_reason,
            'execution_mode': self.execution_mode,
            'would_execute': self.would_execute,
            'result_status': self.result_status,
            'result_data': self.result_data,
            'error_message': self.error_message,
            'ui_action': self.ui_action,
            'ui_context': self.ui_context,
            'created_at': self.created_at.isoformat()
        }
        
        # Only include sensitive data if explicitly requested
        if include_sensitive:
            data['command_payload'] = self.command_payload
            data['command_response'] = self.command_response
        else:
            # Redact sensitive data
            if self.command_payload:
                data['command_payload'] = '[REDACTED]'
            if self.command_response:
                data['command_response'] = '[REDACTED]'
        
        return data
    
    def calculate_hash(self):
        """Calculate event hash for integrity verification"""
        hash_input = (
            f"{self.session_id}:{self.sequence_number}:{self.event_type}:"
            f"{self.timestamp.isoformat()}:{self.module}:{self.service}:"
            f"{self.execution_mode}:{self.result_status}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    # Prevent updates - forensic data is immutable
    __table_args__ = {
        'sqlite_autoincrement': True,
        'sqlite_autoincrement': True
    }


class DryRunSession(db.Model):
    """Track dry-run diagnostic sessions"""
    __tablename__ = 'dry_run_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_profile = db.Column(db.String(255))
    
    # Session state
    is_active = db.Column(db.Boolean, default=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    # Statistics
    actions_attempted = db.Column(db.Integer, default=0)
    actions_blocked = db.Column(db.Integer, default=0)
    writes_prevented = db.Column(db.Integer, default=0)
    
    # Relationships
    user = db.relationship('User', backref='dry_run_sessions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'vehicle_profile': self.vehicle_profile,
            'is_active': self.is_active,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'actions_attempted': self.actions_attempted,
            'actions_blocked': self.actions_blocked,
            'writes_prevented': self.writes_prevented
        }
