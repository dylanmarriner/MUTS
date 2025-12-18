"""
Enterprise Audit Logging System for MUTS
Tracks all user actions, system events, and security incidents
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, g
from muts.models.database_models import db, User
import hashlib
import hmac


class AuditEvent:
    """Audit event types"""
    
    # Authentication
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    LOGIN_FAILED = "auth.login_failed"
    PASSWORD_CHANGE = "auth.password_change"
    
    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ROLE_CHANGE = "user.role_change"
    
    # Vehicle Operations
    VEHICLE_CREATE = "vehicle.create"
    VEHICLE_UPDATE = "vehicle.update"
    VEHICLE_DELETE = "vehicle.delete"
    VEHICLE_SELECT = "vehicle.select"
    
    # Diagnostics
    DIAGNOSTICS_START = "diagnostics.start"
    DIAGNOSTICS_COMPLETE = "diagnostics.complete"
    DIAGNOSTICS_ERROR = "diagnostics.error"
    DIAGNOSTICS_OVERRIDE = "diagnostics.override"
    
    # Tuning
    TUNING_READ = "tuning.read"
    TUNING_WRITE = "tuning.write"
    TUNING_FLASH = "tuning.flash"
    TUNING_EXPORT = "tuning.export"
    
    # System
    SYSTEM_CONFIG = "system.config"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"
    
    # Security
    SECURITY_VIOLATION = "security.violation"
    SECURITY_BLOCKED = "security.blocked"
    PRIVACY_ACCESS = "privacy.access"
    
    # Data
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    DATA_DELETE = "data.delete"


class AuditLogger:
    """Enterprise audit logging system"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        # Configure audit logger
        self.logger = logging.getLogger('muts.audit')
        
        # Create file handler for audit logs
        handler = logging.FileHandler(
            app.config.get('AUDIT_LOG_FILE', 'logs/audit.log')
        )
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
        
        # Store in app context
        app.audit_logger = self
    
    def log_event(self, event_type: str, details: Dict[str, Any] = None, 
                  user_id: Optional[int] = None, session_id: Optional[str] = None):
        """Log an audit event"""
        
        # Get context information
        if not user_id and hasattr(g, 'current_user'):
            user_id = g.current_user.id
        
        if not session_id:
            session_id = getattr(request, 'session_id', 'unknown')
        
        # Build audit record
        audit_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'session_id': session_id,
            'ip_address': self._get_client_ip(),
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'details': details or {}
        }
        
        # Add checksum for integrity
        audit_record['checksum'] = self._calculate_checksum(audit_record)
        
        # Log to file
        self.logger.info(json.dumps(audit_record))
        
        # Also store in database for querying
        self._store_in_database(audit_record)
    
    def log_auth_event(self, event_type: str, username: str, success: bool = True,
                       details: Dict[str, Any] = None):
        """Log authentication event"""
        self.log_event(
            event_type,
            {
                'username': username,
                'success': success,
                **(details or {})
            }
        )
    
    def log_vehicle_operation(self, event_type: str, vin: str, user_id: int,
                             details: Dict[str, Any] = None):
        """Log vehicle-related operation"""
        self.log_event(
            event_type,
            {
                'vin': vin,
                **(details or {})
            },
            user_id=user_id
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any] = None):
        """Log security-related event"""
        self.log_event(
            event_type,
            details,
            user_id=getattr(g, 'current_user', {}).get('id')
        )
    
    def log_data_access(self, resource_type: str, resource_id: str, 
                       action: str, user_id: int):
        """Log data access for privacy compliance"""
        self.log_event(
            f"privacy.{action}",
            {
                'resource_type': resource_type,
                'resource_id': resource_id
            },
            user_id=user_id
        )
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
        if request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        
        return request.remote_addr or 'unknown'
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for audit record integrity"""
        # Create a consistent string representation
        data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        
        # Calculate HMAC using app secret key
        secret = current_app.config.get('SECRET_KEY', 'default').encode()
        checksum = hmac.new(
            secret,
            data_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return checksum
    
    def _store_in_database(self, audit_record: Dict[str, Any]):
        """Store audit record in database for querying"""
        try:
            # This would use an AuditLog model if implemented
            # For now, just log to file
            pass
        except Exception as e:
            # Don't let audit logging failures break the app
            self.logger.error(f"Failed to store audit record: {e}")


# Decorators for automatic audit logging
def audit_action(event_type: str, get_details=None):
    """Decorator to automatically audit function calls"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Get user from context
            user_id = getattr(g, 'current_user', {}).get('id')
            
            # Get details if provided
            details = None
            if get_details:
                details = get_details(*args, **kwargs)
            
            # Log the action
            audit_logger = current_app.audit_logger
            audit_logger.log_event(event_type, details, user_id)
            
            # Execute the function
            return f(*args, **kwargs)
        return decorated
    return decorator


class AuditQuery:
    """Query interface for audit logs"""
    
    def __init__(self, logger: AuditLogger):
        self.logger = logger
    
    def by_user(self, user_id: int, start_date: datetime = None, 
                end_date: datetime = None) -> list:
        """Query audit logs by user"""
        # Implementation would parse log files or query database
        pass
    
    def by_event_type(self, event_type: str, start_date: datetime = None,
                      end_date: datetime = None) -> list:
        """Query audit logs by event type"""
        # Implementation would parse log files or query database
        pass
    
    def by_resource(self, resource_type: str, resource_id: str) -> list:
        """Query audit logs by resource"""
        # Implementation would parse log files or query database
        pass
    
    def security_events(self, start_date: datetime = None,
                       end_date: datetime = None) -> list:
        """Query security-related events"""
        security_events = [
            AuditEvent.SECURITY_VIOLATION,
            AuditEvent.SECURITY_BLOCKED,
            AuditEvent.LOGIN_FAILED,
            AuditEvent.PRIVACY_ACCESS
        ]
        
        results = []
        for event_type in security_events:
            results.extend(self.by_event_type(event_type, start_date, end_date))
        
        return results
    
    def export_logs(self, format: str = 'json', start_date: datetime = None,
                   end_date: datetime = None) -> str:
        """Export audit logs for compliance"""
        # Implementation would gather and format logs
        pass


# Initialize audit logger
audit_logger = AuditLogger()


# Convenience functions
def log_auth(event_type: str, username: str, success: bool = True, **kwargs):
    """Log authentication event"""
    audit_logger.log_auth_event(event_type, username, success, kwargs)


def log_vehicle(event_type: str, vin: str, **kwargs):
    """Log vehicle event"""
    user_id = getattr(g, 'current_user', {}).get('id')
    audit_logger.log_vehicle_operation(event_type, vin, user_id, kwargs)


def log_security(event_type: str, **kwargs):
    """Log security event"""
    audit_logger.log_security_event(event_type, kwargs)


def log_data_access(resource_type: str, resource_id: str, action: str):
    """Log data access"""
    user_id = getattr(g, 'current_user', {}).get('id')
    audit_logger.log_data_access(resource_type, resource_id, action, user_id)
