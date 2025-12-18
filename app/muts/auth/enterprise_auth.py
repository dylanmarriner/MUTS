"""
Enterprise Authentication Module for MUTS
Provides JWT-based authentication, role-based access control, and SSO integration
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from functools import wraps
from flask import request, jsonify, current_app
from muts.models.database_models import User, db
import logging

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Authentication error"""
    pass


class Role:
    """User roles for RBAC"""
    ADMIN = "admin"
    TECHNICIAN = "technician"
    VIEWER = "viewer"
    
    @classmethod
    def all(cls) -> List[str]:
        return [cls.ADMIN, cls.TECHNICIAN, cls.VIEWER]
    
    @classmethod
    def hierarchy(cls) -> Dict[str, int]:
        """Role hierarchy for permission checking"""
        return {
            cls.VIEWER: 1,
            cls.TECHNICIAN: 2,
            cls.ADMIN: 3
        }


class Permission:
    """System permissions"""
    # Vehicle operations
    VEHICLE_READ = "vehicle:read"
    VEHICLE_WRITE = "vehicle:write"
    VEHICLE_DELETE = "vehicle:delete"
    
    # Diagnostics
    DIAGNOSTICS_RUN = "diagnostics:run"
    DIAGNOSTICS_ADVANCED = "diagnostics:advanced"
    
    # Tuning
    TUNING_READ = "tuning:read"
    TUNING_WRITE = "tuning:write"
    TUNING_FLASH = "tuning:flash"
    
    # System
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"
    AUDIT_VIEW = "audit:view"
    
    @classmethod
    def role_permissions(cls) -> Dict[str, List[str]]:
        """Map roles to permissions"""
        return {
            Role.VIEWER: [
                cls.VEHICLE_READ,
                cls.DIAGNOSTICS_RUN,
                cls.TUNING_READ
            ],
            Role.TECHNICIAN: [
                cls.VEHICLE_READ,
                cls.VEHICLE_WRITE,
                cls.DIAGNOSTICS_RUN,
                cls.DIAGNOSTICS_ADVANCED,
                cls.TUNING_READ,
                cls.TUNING_WRITE
            ],
            Role.ADMIN: [
                cls.VEHICLE_READ,
                cls.VEHICLE_WRITE,
                cls.VEHICLE_DELETE,
                cls.DIAGNOSTICS_RUN,
                cls.DIAGNOSTICS_ADVANCED,
                cls.TUNING_READ,
                cls.TUNING_WRITE,
                cls.TUNING_FLASH,
                cls.USER_MANAGE,
                cls.SYSTEM_CONFIG,
                cls.AUDIT_VIEW
            ]
        }


class EnterpriseAuth:
    """Enterprise authentication manager"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        app.config.setdefault('JWT_SECRET_KEY', app.config.get('SECRET_KEY'))
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=1))
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
        app.config.setdefault('BCRYPT_LOG_ROUNDS', 12)
        
        # SSO configuration
        app.config.setdefault('SSO_ENABLED', False)
        app.config.setdefault('SSO_PROVIDER', None)
        app.config.setdefault('SSO_CLIENT_ID', None)
        app.config.setdefault('SSO_CLIENT_SECRET', None)
        
        self.app = app
    
    def generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate access and refresh tokens"""
        now = datetime.utcnow()
        
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'permissions': self.get_user_permissions(user),
            'iat': now,
            'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'type': 'access'
        }
        
        refresh_payload = {
            'user_id': user.id,
            'iat': now,
            'exp': now + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
            'type': 'refresh'
        }
        
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())
        }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Check token type
            if payload.get('type') != 'access':
                raise AuthError("Invalid token type")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthError("Invalid token")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Generate new access token from refresh token"""
        try:
            payload = jwt.decode(
                refresh_token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            if payload.get('type') != 'refresh':
                raise AuthError("Invalid token type")
            
            user = User.query.get(payload['user_id'])
            if not user or not user.is_active:
                raise AuthError("User not found or inactive")
            
            tokens = self.generate_tokens(user)
            return {'access_token': tokens['access_token']}
        except jwt.ExpiredSignatureError:
            raise AuthError("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise AuthError("Invalid refresh token")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.is_active:
            return None
        
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return user
    
    def create_user(self, username: str, password: str, email: str, role: str = Role.VIEWER) -> User:
        """Create a new user"""
        # Validate role
        if role not in Role.all():
            raise ValueError(f"Invalid role: {role}")
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists")
        
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already exists")
        
        # Hash password
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=current_app.config['BCRYPT_LOG_ROUNDS'])
        ).decode('utf-8')
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"Created user: {username} with role: {role}")
        return user
    
    def get_user_permissions(self, user: User) -> List[str]:
        """Get user permissions based on role"""
        return Permission.role_permissions().get(user.role, [])
    
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.get_user_permissions(user)
    
    def can_access_role(self, current_user: User, target_role: str) -> bool:
        """Check if user can manage target role (hierarchy check)"""
        current_level = Role.hierarchy().get(current_user.role, 0)
        target_level = Role.hierarchy().get(target_role, 0)
        return current_level >= target_level


# Decorators for authentication
def require_auth(f):
    """Require authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': 'Invalid authorization header'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            auth = EnterpriseAuth(current_app)
            payload = auth.verify_token(token)
            request.current_user = User.query.get(payload['user_id'])
            request.user_permissions = payload.get('permissions', [])
        except AuthError as e:
            return jsonify({'error': str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated


def require_permission(permission: str):
    """Require specific permission decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'user_permissions'):
                return jsonify({'error': 'Authentication required'}), 401
            
            if permission not in request.user_permissions:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def require_role(role: str):
    """Require specific role decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
        
        if request.current_user.role != role and request.current_user.role != Role.ADMIN:
            return jsonify({'error': 'Insufficient role'}), 403
        
        return f(*args, **kwargs)
    return decorated


# SSO Integration (placeholder for actual implementation)
class SSOProvider:
    """Base class for SSO providers"""
    
    def authenticate(self, code: str) -> Dict[str, Any]:
        """Authenticate with SSO provider using authorization code"""
        raise NotImplementedError
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from SSO provider"""
        raise NotImplementedError


class SAMLProvider(SSOProvider):
    """SAML SSO provider"""
    
    def authenticate(self, saml_response: str) -> Dict[str, Any]:
        """Process SAML response"""
        # Implementation would go here
        pass


class OIDCProvider(SSOProvider):
    """OpenID Connect SSO provider"""
    
    def authenticate(self, code: str) -> Dict[str, Any]:
        """Process OIDC authorization code"""
        # Implementation would go here
        pass
