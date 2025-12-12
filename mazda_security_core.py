"""
MazdaSecurityCore - Authentication, encryption, and access control for ECU operations.
Provides security layer for all tuning operations with role-based access control.
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import json
import logging

from models import (
    SecurityLevel, SecurityCredentials, LogEntry,
    SecurityContext, TuningParameter, FlashOperation
)


class SecurityError(Exception):
    """Security-related exceptions."""
    pass


class AuthenticationError(SecurityError):
    """Authentication failed."""
    pass


class AuthorizationError(SecurityError):
    """Insufficient permissions for operation."""
    pass


class MazdaSecurityCore:
    """
    Core security module for Mazda ECU access and tuning operations.
    Handles authentication, authorization, encryption, and audit logging.
    """
    
    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize security core.
        
        Args:
            master_key: Optional master encryption key. Generated if not provided.
        """
        self.logger = logging.getLogger(__name__)
        
        # Generate or use provided master key
        self.master_key = master_key or self._generate_master_key()
        
        # Initialize encryption components
        self.fernet = Fernet(self.master_key)
        self.backend = default_backend()
        
        # Security configuration
        self.session_timeout = 3600  # 1 hour
        self.max_failed_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        
        # Runtime state
        self.active_sessions: Dict[str, SecurityCredentials] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.access_log: List[LogEntry] = []
        
        # Default users (in production, use secure database)
        self.users = {
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "security_level": SecurityLevel.ADMIN,
                "permissions": ["all"]
            },
            "tuner": {
                "password_hash": self._hash_password("tuner456"),
                "security_level": SecurityLevel.TUNING,
                "permissions": ["read", "tune", "diagnose"]
            },
            "diagnostic": {
                "password_hash": self._hash_password("diag789"),
                "security_level": SecurityLevel.DIAGNOSTIC,
                "permissions": ["read", "diagnose"]
            }
        }
        
        self.logger.info("MazdaSecurityCore initialized")
    
    def _generate_master_key(self) -> bytes:
        """Generate cryptographically secure master key."""
        return Fernet.generate_key()
    
    def _hash_password(self, password: str, salt: Optional[bytes] = None) -> str:
        """
        Hash password using PBKDF2.
        
        Args:
            password: Plain text password
            salt: Optional salt bytes
            
        Returns:
            Hex-encoded hash with salt
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        
        hash_bytes = kdf.derive(password.encode())
        return base64.b64encode(salt + hash_bytes).decode()
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            stored_hash: Stored password hash
            
        Returns:
            True if password matches
        """
        try:
            decoded = base64.b64decode(stored_hash.encode())
            salt = decoded[:32]
            stored_hash_bytes = decoded[32:]
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            
            hash_bytes = kdf.derive(password.encode())
            return secrets.compare_digest(hash_bytes, stored_hash_bytes)
        except Exception:
            return False
    
    def _is_account_locked(self, username: str) -> bool:
        """
        Check if account is locked due to failed attempts.
        
        Args:
            username: Username to check
            
        Returns:
            True if account is locked
        """
        if username not in self.failed_attempts:
            return False
        
        recent_attempts = [
            attempt for attempt in self.failed_attempts[username]
            if datetime.now() - attempt < timedelta(seconds=self.lockout_duration)
        ]
        
        return len(recent_attempts) >= self.max_failed_attempts
    
    def _record_failed_attempt(self, username: str) -> None:
        """Record failed login attempt."""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        
        self.failed_attempts[username].append(datetime.now())
        
        # Clean old attempts
        cutoff = datetime.now() - timedelta(seconds=self.lockout_duration)
        self.failed_attempts[username] = [
            attempt for attempt in self.failed_attempts[username]
            if attempt > cutoff
        ]
    
    def _generate_session_token(self) -> str:
        """Generate cryptographically secure session token."""
        return secrets.token_urlsafe(32)
    
    def _log_access(self, level: str, module: str, message: str, 
                   data: Optional[Dict[str, Any]] = None) -> None:
        """Log security access event."""
        entry = LogEntry(
            level=level,
            module=module,
            message=message,
            data=data
        )
        self.access_log.append(entry)
        
        # Keep log size manageable
        if len(self.access_log) > 10000:
            self.access_log = self.access_log[-5000:]
    
    def authenticate(self, username: str, password: str) -> SecurityCredentials:
        """
        Authenticate user and create session.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            SecurityCredentials object
            
        Raises:
            AuthenticationError: If authentication fails
            SecurityError: If account is locked
        """
        if self._is_account_locked(username):
            self._log_access("WARNING", "AUTH", 
                           f"Login attempt on locked account: {username}")
            raise SecurityError(f"Account {username} is locked")
        
        if username not in self.users:
            self._record_failed_attempt(username)
            self._log_access("WARNING", "AUTH", 
                           f"Login attempt with invalid username: {username}")
            raise AuthenticationError("Invalid username or password")
        
        user_data = self.users[username]
        if not self._verify_password(password, user_data["password_hash"]):
            self._record_failed_attempt(username)
            self._log_access("WARNING", "AUTH", 
                           f"Failed password attempt for user: {username}")
            raise AuthenticationError("Invalid username or password")
        
        # Clear failed attempts on successful login
        if username in self.failed_attempts:
            del self.failed_attempts[username]
        
        # Create session
        session_token = self._generate_session_token()
        credentials = SecurityCredentials(
            username=username,
            password_hash=user_data["password_hash"],
            security_level=user_data["security_level"],
            session_token=session_token,
            expires_at=datetime.now() + timedelta(seconds=self.session_timeout),
            permissions=user_data["permissions"]
        )
        
        self.active_sessions[session_token] = credentials
        self._log_access("INFO", "AUTH", f"User authenticated: {username}")
        
        return credentials
    
    def validate_session(self, session_token: str) -> SecurityContext:
        """
        Validate session token and return credentials.
        
        Args:
            session_token: Session token to validate
            
        Returns:
            SecurityCredentials if valid, None if expired/invalid
        """
        if session_token not in self.active_sessions:
            self._log_access("WARNING", "AUTH", "Invalid session token used")
            return None
        
        credentials = self.active_sessions[session_token]
        
        if credentials.is_expired():
            del self.active_sessions[session_token]
            self._log_access("INFO", "AUTH", 
                           f"Session expired for user: {credentials.username}")
            return None
        
        # Extend session timeout
        credentials.expires_at = datetime.now() + timedelta(seconds=self.session_timeout)
        return credentials
    
    def authorize_operation(self, credentials: SecurityCredentials, 
                           required_level: SecurityLevel,
                           operation: str) -> bool:
        """
        Check if user is authorized for specific operation.
        
        Args:
            credentials: User credentials
            required_level: Minimum security level required
            operation: Operation description
            
        Returns:
            True if authorized
            
        Raises:
            AuthorizationError: If not authorized
        """
        if not credentials or credentials.is_expired():
            self._log_access("WARNING", "AUTH", 
                           f"Authorization attempt with invalid credentials")
            raise AuthorizationError("Invalid or expired credentials")
        
        if credentials.security_level.value < required_level.value:
            self._log_access("WARNING", "AUTH", 
                           f"User {credentials.username} denied access to {operation}")
            raise AuthorizationError(f"Insufficient privileges for {operation}")
        
        self._log_access("INFO", "AUTH", 
                       f"User {credentials.username} authorized for {operation}")
        return True
    
    def encrypt_data(self, data: bytes, context: Optional[bytes] = None) -> bytes:
        """
        Encrypt data using Fernet symmetric encryption.
        
        Args:
            data: Data to encrypt
            context: Optional context for additional security
            
        Returns:
            Encrypted data
        """
        if context:
            # Add context to data before encryption
            data_with_context = context + data
            return self.fernet.encrypt(data_with_context)
        return self.fernet.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes, 
                    context: Optional[bytes] = None) -> bytes:
        """
        Decrypt data using Fernet symmetric encryption.
        
        Args:
            encrypted_data: Data to decrypt
            context: Optional context that was added during encryption
            
        Returns:
            Decrypted data
        """
        decrypted = self.fernet.decrypt(encrypted_data)
        
        if context:
            # Remove context from data
            if decrypted.startswith(context):
                return decrypted[len(context):]
            else:
                raise SecurityError("Invalid context in decrypted data")
        
        return decrypted
    
    def secure_hash(self, data: bytes, salt: Optional[bytes] = None) -> str:
        """
        Generate secure hash of data.
        
        Args:
            data: Data to hash
            salt: Optional salt
            
        Returns:
            Hex-encoded hash
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        hash_obj = hashlib.sha256(salt + data)
        return base64.b64encode(salt + hash_obj.digest()).decode()
    
    def verify_hash(self, data: bytes, stored_hash: str) -> bool:
        """
        Verify data against stored hash.
        
        Args:
            data: Data to verify
            stored_hash: Stored hash
            
        Returns:
            True if data matches hash
        """
        try:
            decoded = base64.b64decode(stored_hash.encode())
            salt = decoded[:16]
            stored_hash_bytes = decoded[16:]
            
            hash_obj = hashlib.sha256(salt + data)
            computed_hash = hash_obj.digest()
            
            return secrets.compare_digest(computed_hash, stored_hash_bytes)
        except Exception:
            return False
    
    def logout(self, session_token: str) -> bool:
        """
        Logout user and invalidate session.
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if logout successful
        """
        if session_token in self.active_sessions:
            username = self.active_sessions[session_token].username
            del self.active_sessions[session_token]
            self._log_access("INFO", "AUTH", f"User logged out: {username}")
            return True
        return False
    
    def get_active_sessions(self) -> List[SecurityCredentials]:
        """Get list of active sessions."""
        return list(self.active_sessions.values())
    
    def get_access_log(self, level: Optional[str] = None,
                      since: Optional[datetime] = None) -> List[LogEntry]:
        """
        Get filtered access log.
        
        Args:
            level: Filter by log level
            since: Filter entries since this time
            
        Returns:
            Filtered log entries
        """
        filtered_log = self.access_log
        
        if level:
            filtered_log = [entry for entry in filtered_log if entry.level == level]
        
        if since:
            filtered_log = [entry for entry in filtered_log if entry.timestamp >= since]
        
        return filtered_log
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_tokens = []
        
        for token, credentials in self.active_sessions.items():
            if credentials.is_expired():
                expired_tokens.append(token)
        
        for token in expired_tokens:
            username = self.active_sessions[token].username
            del self.active_sessions[token]
            self._log_access("INFO", "AUTH", 
                           f"Expired session cleaned up: {username}")
        
        return len(expired_tokens)
    
    def validate_tuning_parameter(self, credentials: SecurityCredentials,
                                 parameter: TuningParameter) -> bool:
        """
        Validate if user can modify specific tuning parameter.
        
        Args:
            credentials: User credentials
            parameter: Tuning parameter to validate
            
        Returns:
            True if parameter can be modified
            
        Raises:
            AuthorizationError: If not authorized
        """
        self.authorize_operation(credentials, parameter.security_level,
                                f"modify parameter {parameter.name}")
        return parameter.validate()
    
    def validate_flash_operation(self, credentials: SecurityCredentials,
                                operation: FlashOperation) -> bool:
        """
        Validate if user can perform flash operation.
        
        Args:
            credentials: User credentials
            operation: Flash operation to validate
            
        Returns:
            True if operation is authorized
            
        Raises:
            AuthorizationError: If not authorized
        """
        self.authorize_operation(credentials, SecurityLevel.FLASH,
                                f"flash operation {operation.operation_id}")
        return True
    
    def export_security_config(self) -> Dict[str, Any]:
        """
        Export security configuration (without sensitive data).
        
        Returns:
            Security configuration dictionary
        """
        return {
            "session_timeout": self.session_timeout,
            "max_failed_attempts": self.max_failed_attempts,
            "lockout_duration": self.lockout_duration,
            "active_sessions": len(self.active_sessions),
            "users": list(self.users.keys()),
        }
    
    def __del__(self):
        """Cleanup on deletion."""
        # Clear all sessions
        self.active_sessions.clear()
        self.logger.info("MazdaSecurityCore shutdown")
