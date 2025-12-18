"""
SecureDatabase - Encrypted SQLite database for MUTS (Mazda Universal Tuning System).

This module provides a secure, encrypted SQLite database with tables for users, vehicles,
tuning sessions, diagnostic logs, and security events. All sensitive data is encrypted
using Fernet (AES-128-CBC with PKCS7 padding).
"""

import sqlite3
import json
import logging
import os
import base64
import hashlib
import secrets
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, TypeVar, Type, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path

# Cryptography imports
from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type aliases
T = TypeVar('T')
JSONType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

class DatabaseError(Exception):
    """Base exception for database errors."""
    pass

class SecurityError(DatabaseError):
    """Raised when a security-related error occurs."""
    pass

class UserRole(str, Enum):
    """User roles with different permission levels."""
    ADMIN = "admin"
    TUNER = "tuner"
    USER = "user"
    READONLY = "readonly"

class LogSeverity(str, Enum):
    """Severity levels for diagnostic logs."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class SecurityEventType(str, Enum):
    """Types of security events."""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_DENIED = "permission_denied"
    CONFIG_CHANGE = "config_change"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"

@dataclass
class User:
    """User account information."""
    id: int = field(init=False)
    username: str
    email: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['role'] = self.role.value
        result['last_login'] = self.last_login.isoformat() if self.last_login else None
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create from dictionary."""
        user = cls(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole(data.get('role', 'user')),
            is_active=bool(data.get('is_active', True))
        )
        if 'id' in data:
            user.id = data['id']
        if 'last_login' in data and data['last_login']:
            user.last_login = datetime.fromisoformat(data['last_login'])
        if 'created_at' in data:
            user.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            user.updated_at = datetime.fromisoformat(data['updated_at'])
        return user

@dataclass
class Vehicle:
    """Vehicle information."""
    id: int = field(init=False)
    vin: str
    make: str
    model: str
    year: int
    engine: str
    owner_id: int
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Vehicle':
        """Create from dictionary."""
        vehicle = cls(
            vin=data['vin'],
            make=data['make'],
            model=data['model'],
            year=int(data['year']),
            engine=data['engine'],
            owner_id=int(data['owner_id']),
            notes=data.get('notes', '')
        )
        if 'id' in data:
            vehicle.id = data['id']
        if 'created_at' in data:
            vehicle.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            vehicle.updated_at = datetime.fromisoformat(data['updated_at'])
        return vehicle

@dataclass
class TuneSession:
    """Tuning session information."""
    id: int = field(init=False)
    vehicle_id: int
    tuner_id: int
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    description: str = ""
    notes: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat() if self.end_time else None
        result['config'] = json.dumps(self.config) if isinstance(self.config, dict) else self.config
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TuneSession':
        """Create from dictionary."""
        config = data.get('config', {})
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}
        
        session = cls(
            vehicle_id=int(data['vehicle_id']),
            tuner_id=int(data['tuner_id']),
            start_time=datetime.fromisoformat(data.get('start_time', datetime.utcnow().isoformat())),
            description=data.get('description', ''),
            notes=data.get('notes', ''),
            config=config,
            is_complete=bool(data.get('is_complete', False))
        )
        
        if 'id' in data:
            session.id = data['id']
        if 'end_time' in data and data['end_time']:
            session.end_time = datetime.fromisoformat(data['end_time'])
        
        return session

@dataclass
class DiagnosticLog:
    """Diagnostic log entry."""
    id: int = field(init=False)
    session_id: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    code: str
    description: str
    severity: LogSeverity = LogSeverity.INFO
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['severity'] = self.severity.value
        result['data'] = json.dumps(self.data) if self.data else '{}'
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DiagnosticLog':
        """Create from dictionary."""
        log_data = data.get('data', {})
        if isinstance(log_data, str):
            try:
                log_data = json.loads(log_data)
            except json.JSONDecodeError:
                log_data = {}
        
        log = cls(
            session_id=int(data['session_id']),
            code=data['code'],
            description=data['description'],
            severity=LogSeverity(data.get('severity', 'info')),
            data=log_data
        )
        
        if 'id' in data:
            log.id = data['id']
        if 'timestamp' in data and data['timestamp']:
            log.timestamp = datetime.fromisoformat(data['timestamp'])
        
        return log

@dataclass
class SecurityLog:
    """Security event log entry."""
    id: int = field(init=False)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: SecurityEventType
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['event_type'] = self.event_type.value
        result['details'] = json.dumps(self.details) if self.details else '{}'
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityLog':
        """Create from dictionary."""
        details = data.get('details', {})
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except json.JSONDecodeError:
                details = {}
        
        log = cls(
            event_type=SecurityEventType(data['event_type']),
            user_id=data.get('user_id'),
            ip_address=data.get('ip_address'),
            description=data.get('description', ''),
            details=details
        )
        
        if 'id' in data:
            log.id = data['id']
        if 'timestamp' in data and data['timestamp']:
            log.timestamp = datetime.fromisoformat(data['timestamp'])
        
        return log

class SecureDatabase:
    """Secure SQLite database with encryption for sensitive data."""
    
    # Schema version
    SCHEMA_VERSION = 1
    
    # SQL statements for schema creation
    SCHEMA = [
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vin TEXT UNIQUE NOT NULL,
            make TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            engine TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            notes TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tune_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            tuner_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            description TEXT,
            notes TEXT,
            config_encrypted BLOB,
            is_complete BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles (id) ON DELETE CASCADE,
            FOREIGN KEY (tuner_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS diagnostic_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            code TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            data_encrypted BLOB,
            FOREIGN KEY (session_id) REFERENCES tune_sessions (id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            ip_address TEXT,
            description TEXT,
            details_encrypted BLOB,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
        """,
        # Indexes
        "CREATE INDEX IF NOT EXISTS idx_vehicles_owner ON vehicles(owner_id)",
        "CREATE INDEX IF NOT EXISTS idx_tune_sessions_vehicle ON tune_sessions(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_tune_sessions_tuner ON tune_sessions(tuner_id)",
        "CREATE INDEX IF NOT EXISTS idx_diagnostic_logs_session ON diagnostic_logs(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_security_logs_user ON security_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_security_logs_event_type ON security_logs(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp ON security_logs(timestamp)",
    ]
    
    def __init__(self, db_path: str, encryption_key: Optional[bytes] = None):
        """
        Initialize the secure database.
        
        Args:
            db_path: Path to the SQLite database file
            encryption_key: Optional Fernet key for encryption. If not provided, a new key will be generated.
        ""
        self.db_path = db_path
        self.connection = None
        self._in_transaction = False
        
        # Initialize encryption
        self._init_encryption(encryption_key)
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        
        # Connect to the database and initialize schema
        self._connect()
        self._init_schema()
    
    def _init_encryption(self, encryption_key: Optional[bytes] = None) -> None:
        """Initialize encryption components."""
        if encryption_key:
            if not isinstance(encryption_key, bytes):
                raise ValueError("Encryption key must be bytes")
            self._encryption_key = encryption_key
        else:
            # Generate a new key if none provided
            self._encryption_key = Fernet.generate_key()
            logger.warning("No encryption key provided, using a newly generated key")
        
        self._fernet = Fernet(self._encryption_key)
    
    def _connect(self) -> None:
        """Connect to the SQLite database."""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                isolation_level=None,  # Manual transaction control
                check_same_thread=False  # Allow access from multiple threads
            )
            
            # Enable foreign key constraints
            self.connection.execute("PRAGMA foreign_keys = ON")
            
            # Optimize for better performance
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA synchronous = NORMAL")
            self.connection.execute("PRAGMA cache_size = -2000")  # 2MB cache
            
            # Register custom functions
            self.connection.create_function("ENCRYPT", 1, self._encrypt_value)
            self.connection.create_function("DECRYPT", 1, self._decrypt_value)
            
            logger.info(f"Connected to database: {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
    
    def _init_schema(self) -> None:
        """Initialize the database schema."""
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            cursor = self.connection.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create tables if they don't exist
            for statement in self.SCHEMA:
                cursor.execute(statement)
            
            # Check schema version
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            
            # Get current schema version
            cursor.execute("SELECT value FROM meta WHERE key = 'schema_version'")
            result = cursor.fetchone()
            
            if result is None:
                # New database, set schema version
                cursor.execute(
                    "INSERT INTO meta (key, value) VALUES (?, ?)",
                    ('schema_version', str(self.SCHEMA_VERSION))
                )
                logger.info(f"Database schema initialized to version {self.SCHEMA_VERSION}")
            else:
                current_version = int(result[0])
                if current_version < self.SCHEMA_VERSION:
                    self._migrate_schema(current_version)
                elif current_version > self.SCHEMA_VERSION:
                    logger.warning(
                        f"Database schema version ({current_version}) is newer than "
                        f"the application supports ({self.SCHEMA_VERSION})"
                    )
            
            self.connection.commit()
            
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Failed to initialize database schema: {e}")
            raise DatabaseError(f"Schema initialization failed: {e}")
    
    def _migrate_schema(self, from_version: int) -> None:
        """Migrate the database schema from an older version."""
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        logger.info(f"Migrating database schema from version {from_version} to {self.SCHEMA_VERSION}")
        
        try:
            cursor = self.connection.cursor()
            
            # Example migration (add more as needed)
            if from_version < 1:
                # Add any schema changes for version 1
                pass
            
            # Update schema version
            cursor.execute(
                "UPDATE meta SET value = ? WHERE key = 'schema_version'",
                (str(self.SCHEMA_VERSION),)
            )
            
            self.connection.commit()
            logger.info(f"Database schema migrated to version {self.SCHEMA_VERSION}")
            
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Schema migration failed: {e}")
            raise DatabaseError(f"Schema migration failed: {e}")
    
    def _encrypt_value(self, value: str) -> bytes:
        """Encrypt a string value."""
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        return self._fernet.encrypt(value.encode('utf-8'))
    
    def _decrypt_value(self, encrypted: bytes) -> str:
        """Decrypt an encrypted value to a string."""
        if encrypted is None:
            return None
        try:
            return self._fernet.decrypt(encrypted).decode('utf-8')
        except (InvalidToken, ValueError) as e:
            logger.error(f"Decryption failed: {e}")
            raise SecurityError("Failed to decrypt value")
    
    def _encrypt_json(self, data: Dict[str, Any]) -> bytes:
        """Encrypt a JSON-serializable dictionary."""
        if data is None:
            return None
        json_str = json.dumps(data, ensure_ascii=False)
        return self._fernet.encrypt(json_str.encode('utf-8'))
    
    def _decrypt_json(self, encrypted: bytes) -> Dict[str, Any]:
        """Decrypt an encrypted JSON string to a dictionary."""
        if encrypted is None:
            return {}
        try:
            json_str = self._fernet.decrypt(encrypted).decode('utf-8')
            return json.loads(json_str)
        except (InvalidToken, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to decrypt JSON: {e}")
            raise SecurityError("Failed to decrypt JSON data")
    
    def _hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Hash a password with a salt."""
        if salt is None:
            salt = os.urandom(16)  # 128-bit salt
        
        # Use PBKDF2 with SHA-256 for key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=100000,  # Adjust based on performance requirements
            backend=default_backend()
        )
        
        # Generate the hash
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        return key, salt
    
    def _verify_password(self, password: str, password_hash: bytes, salt: bytes) -> bool:
        """Verify a password against a hash and salt."""
        try:
            new_hash, _ = self._hash_password(password, salt)
            return secrets.compare_digest(new_hash, password_hash)
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        cursor = None
        try:
            if not self._in_transaction:
                cursor = self.connection.cursor()
                cursor.execute("BEGIN")
                self._in_transaction = True
            
            yield self.connection.cursor()
            
            if not self._in_transaction:
                return
                
            self.connection.commit()
            self._in_transaction = False
            
        except Exception as e:
            if self._in_transaction:
                self.connection.rollback()
                self._in_transaction = False
            logger.error(f"Transaction failed: {e}")
            raise DatabaseError(f"Transaction failed: {e}")
        finally:
            if cursor:
                cursor.close()
    
    # User management
    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        first_name: str,
        last_name: str,
        role: Union[UserRole, str] = UserRole.USER,
        is_active: bool = True
    ) -> int:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            email: User's email address
            first_name: User's first name
            last_name: User's last name
            role: User role (default: user)
            is_active: Whether the account is active
            
        Returns:
            The ID of the newly created user
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        if isinstance(role, str):
            role = UserRole(role.lower())
        
        # Generate salt and hash password
        salt = os.urandom(16)
        password_hash, _ = self._hash_password(password, salt)
        
        try:
            with self.transaction() as cursor:
                cursor.execute("""
                    INSERT INTO users (
                        username, email, password_hash, password_salt,
                        first_name, last_name, role, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    email,
                    password_hash,
                    salt,
                    first_name,
                    last_name,
                    role.value,
                    int(is_active),
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                
                user_id = cursor.lastrowid
                
                # Log the event
                self._log_security_event(
                    event_type=SecurityEventType.CONFIG_CHANGE,
                    description=f"User account created: {username}",
                    user_id=user_id
                )
                
                return user_id
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: users.username" in str(e):
                raise DatabaseError(f"Username '{username}' already exists") from e
            elif "UNIQUE constraint failed: users.email" in str(e):
                raise DatabaseError(f"Email '{email}' is already registered") from e
            raise DatabaseError(f"Failed to create user: {e}") from e
        except Exception as e:
            raise DatabaseError(f"Failed to create user: {e}") from e
    
    def authenticate_user(self, username: str, password: str, ip_address: Optional[str] = None) -> Optional[User]:
        """
        Authenticate a user by username and password.
        
        Args:
            username: Username
            password: Plain text password
            ip_address: Optional IP address for logging
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                # Get user by username
                cursor.execute(
                    "SELECT id, username, password_hash, password_salt, is_active FROM users WHERE username = ?",
                    (username,)
                )
                result = cursor.fetchone()
                
                if not result:
                    # User not found
                    self._log_security_event(
                        event_type=SecurityEventType.LOGIN_FAILED,
                        description=f"Failed login attempt for unknown user: {username}",
                        ip_address=ip_address
                    )
                    return None
                
                user_id, db_username, db_hash, db_salt, is_active = result
                
                # Check if account is active
                if not is_active:
                    self._log_security_event(
                        event_type=SecurityEventType.LOGIN_FAILED,
                        description=f"Login attempt for inactive account: {username}",
                        user_id=user_id,
                        ip_address=ip_address
                    )
                    return None
                
                # Verify password
                if not self._verify_password(password, db_hash, db_salt):
                    self._log_security_event(
                        event_type=SecurityEventType.LOGIN_FAILED,
                        description=f"Invalid password for user: {username}",
                        user_id=user_id,
                        ip_address=ip_address
                    )
                    return None
                
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (datetime.utcnow(), user_id)
                )
                
                # Get full user details
                user = self.get_user_by_id(user_id)
                
                # Log successful login
                self._log_security_event(
                    event_type=SecurityEventType.LOGIN,
                    description=f"User logged in: {username}",
                    user_id=user_id,
                    ip_address=ip_address
                )
                
                return user
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                cursor.execute(
                    """
                    SELECT id, username, email, first_name, last_name, role, 
                           is_active, last_login, created_at, updated_at
                    FROM users WHERE id = ?
                    """,
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return User(
                    id=result[0],
                    username=result[1],
                    email=result[2],
                    first_name=result[3],
                    last_name=result[4],
                    role=UserRole(result[5]),
                    is_active=bool(result[6]),
                    last_login=result[7],
                    created_at=result[8],
                    updated_at=result[9]
                )
                
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                cursor.execute(
                    """
                    SELECT id, username, email, first_name, last_name, role, 
                           is_active, last_login, created_at, updated_at
                    FROM users WHERE username = ?
                    """,
                    (username,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                return User(
                    id=result[0],
                    username=result[1],
                    email=result[2],
                    first_name=result[3],
                    last_name=result[4],
                    role=UserRole(result[5]),
                    is_active=bool(result[6]),
                    last_login=result[7],
                    created_at=result[8],
                    updated_at=result[9]
                )
                
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}")
            return None
    
    def update_user(self, user_id: int, **updates) -> bool:
        """
        Update user information.
        
        Args:
            user_id: ID of the user to update
            **updates: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        if not updates:
            return True  # Nothing to update
        
        allowed_fields = {
            'email', 'first_name', 'last_name', 'role', 'is_active', 'password'
        }
        
        # Filter allowed fields
        updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if not updates:
            return False
        
        try:
            with self.transaction() as cursor:
                # Handle password update separately
                new_password = updates.pop('password', None)
                
                # Build update query
                set_clause = ", ".join(f"{field} = ?" for field in updates.keys())
                set_clause += ", updated_at = ?"  # Always update the updated_at field
                
                # Add password fields if needed
                if new_password:
                    salt = os.urandom(16)
                    password_hash, _ = self._hash_password(new_password, salt)
                    set_clause += ", password_hash = ?, password_salt = ?"
                
                # Build parameter list
                params = list(updates.values())
                params.append(datetime.utcnow())
                
                # Add password parameters if needed
                if new_password:
                    params.extend([password_hash, salt])
                
                # Add user_id for WHERE clause
                params.append(user_id)
                
                # Execute update
                cursor.execute(
                    f"UPDATE users SET {set_clause} WHERE id = ?",
                    params
                )
                
                if cursor.rowcount == 0:
                    return False
                
                # Log the update
                self._log_security_event(
                    event_type=SecurityEventType.CONFIG_CHANGE,
                    description=f"Updated user account: {user_id}",
                    user_id=user_id
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user account.
        
        Args:
            user_id: ID of the user to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                # Get username for logging
                cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                username = result[0] if result else str(user_id)
                
                # Delete the user (foreign key constraints will handle related records)
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                
                if cursor.rowcount == 0:
                    return False
                
                # Log the deletion
                self._log_security_event(
                    event_type=SecurityEventType.CONFIG_CHANGE,
                    description=f"Deleted user account: {username}",
                    user_id=user_id
                )
                
                return True
                
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to delete user due to integrity error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False
    
    # Vehicle management
    def add_vehicle(
        self,
        vin: str,
        make: str,
        model: str,
        year: int,
        engine: str,
        owner_id: int,
        notes: str = ""
    ) -> int:
        """
        Add a new vehicle to the database.
        
        Args:
            vin: Vehicle Identification Number
            make: Vehicle make (e.g., "Mazda")
            model: Vehicle model (e.g., "MX-5")
            year: Model year
            engine: Engine type/description
            owner_id: ID of the user who owns this vehicle
            notes: Optional notes about the vehicle
            
        Returns:
            The ID of the newly created vehicle record
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                cursor.execute("""
                    INSERT INTO vehicles (
                        vin, make, model, year, engine, owner_id, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vin.upper(),  # Standardize VIN case
                    make,
                    model,
                    year,
                    engine,
                    owner_id,
                    notes,
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                
                vehicle_id = cursor.lastrowid
                
                # Log the event
                self._log_security_event(
                    event_type=SecurityEventType.DATA_MODIFICATION,
                    description=f"Added vehicle: {make} {model} ({vin})",
                    user_id=owner_id
                )
                
                return vehicle_id
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: vehicles.vin" in str(e):
                raise DatabaseError(f"Vehicle with VIN '{vin}' already exists") from e
            raise DatabaseError(f"Failed to add vehicle: {e}") from e
        except Exception as e:
            raise DatabaseError(f"Failed to add vehicle: {e}") from e
    
    def get_vehicle(self, vehicle_id: int) -> Optional[Vehicle]:
        """
        Get a vehicle by ID.
        
        Args:
            vehicle_id: ID of the vehicle to retrieve
            
        Returns:
            Vehicle object if found, None otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                cursor.execute("""
                    SELECT id, vin, make, model, year, engine, owner_id, notes, created_at, updated_at
                    FROM vehicles WHERE id = ?
                """, (vehicle_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return Vehicle(
                    id=result[0],
                    vin=result[1],
                    make=result[2],
                    model=result[3],
                    year=result[4],
                    engine=result[5],
                    owner_id=result[6],
                    notes=result[7] or "",
                    created_at=result[8],
                    updated_at=result[9]
                )
                
        except Exception as e:
            logger.error(f"Failed to get vehicle: {e}")
            return None
    
    def get_vehicles_by_owner(self, owner_id: int) -> List[Vehicle]:
        """
        Get all vehicles owned by a user.
        
        Args:
            owner_id: ID of the owner
            
        Returns:
            List of Vehicle objects
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                cursor.execute("""
                    SELECT id, vin, make, model, year, engine, owner_id, notes, created_at, updated_at
                    FROM vehicles WHERE owner_id = ?
                    ORDER BY make, model, year
                """, (owner_id,))
                
                vehicles = []
                for row in cursor.fetchall():
                    vehicles.append(Vehicle(
                        id=row[0],
                        vin=row[1],
                        make=row[2],
                        model=row[3],
                        year=row[4],
                        engine=row[5],
                        owner_id=row[6],
                        notes=row[7] or "",
                        created_at=row[8],
                        updated_at=row[9]
                    ))
                
                return vehicles
                
        except Exception as e:
            logger.error(f"Failed to get vehicles by owner: {e}")
            return []
    
    def update_vehicle(self, vehicle_id: int, **updates) -> bool:
        """
        Update vehicle information.
        
        Args:
            vehicle_id: ID of the vehicle to update
            **updates: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        if not updates:
            return True  # Nothing to update
        
        allowed_fields = {
            'vin', 'make', 'model', 'year', 'engine', 'owner_id', 'notes'
        }
        
        # Filter allowed fields
        updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if not updates:
            return False
        
        # Standardize VIN case if present
        if 'vin' in updates and updates['vin']:
            updates['vin'] = updates['vin'].upper()
        
        try:
            with self.transaction() as cursor:
                # Build update query
                set_clause = ", ".join(f"{field} = ?" for field in updates.keys())
                set_clause += ", updated_at = ?"  # Always update the updated_at field
                
                # Build parameter list
                params = list(updates.values())
                params.append(datetime.utcnow())
                
                # Add vehicle_id for WHERE clause
                params.append(vehicle_id)
                
                # Execute update
                cursor.execute(
                    f"UPDATE vehicles SET {set_clause} WHERE id = ?",
                    params
                )
                
                if cursor.rowcount == 0:
                    return False
                
                # Log the update
                self._log_security_event(
                    event_type=SecurityEventType.DATA_MODIFICATION,
                    description=f"Updated vehicle: {vehicle_id}",
                    details=updates
                )
                
                return True
                
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: vehicles.vin" in str(e):
                raise DatabaseError("A vehicle with this VIN already exists") from e
            raise DatabaseError(f"Failed to update vehicle: {e}") from e
        except Exception as e:
            logger.error(f"Failed to update vehicle: {e}")
            return False
    
    def delete_vehicle(self, vehicle_id: int) -> bool:
        """
        Delete a vehicle and all associated data.
        
        Args:
            vehicle_id: ID of the vehicle to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                # Get vehicle details for logging
                cursor.execute("SELECT make, model, vin FROM vehicles WHERE id = ?", (vehicle_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                make, model, vin = result
                
                # Delete the vehicle (foreign key constraints will handle related records)
                cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
                
                if cursor.rowcount == 0:
                    return False
                
                # Log the deletion
                self._log_security_event(
                    event_type=SecurityEventType.DATA_MODIFICATION,
                    description=f"Deleted vehicle: {make} {model} ({vin})",
                    details={"vehicle_id": vehicle_id}
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete vehicle: {e}")
            return False
    
    # Tune session management
    def create_tune_session(
        self,
        vehicle_id: int,
        tuner_id: int,
        description: str = "",
        notes: str = "",
        config: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a new tuning session.
        
        Args:
            vehicle_id: ID of the vehicle being tuned
            tuner_id: ID of the user performing the tuning
            description: Brief description of the session
            notes: Additional notes
            config: Optional configuration dictionary
            
        Returns:
            The ID of the newly created session
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        config = config or {}
        
        try:
            with self.transaction() as cursor:
                # Encrypt the config data
                config_encrypted = self._encrypt_json(config)
                
                cursor.execute("""
                    INSERT INTO tune_sessions (
                        vehicle_id, tuner_id, start_time, description, 
                        notes, config_encrypted, is_complete
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    vehicle_id,
                    tuner_id,
                    datetime.utcnow(),
                    description,
                    notes,
                    config_encrypted,
                    False  # is_complete
                ))
                
                session_id = cursor.lastrowid
                
                # Log the event
                self._log_security_event(
                    event_type=SecurityEventType.DATA_MODIFICATION,
                    description=f"Started tuning session: {description}",
                    user_id=tuner_id,
                    details={
                        "vehicle_id": vehicle_id,
                        "session_id": session_id
                    }
                )
                
                return session_id
                
        except Exception as e:
            logger.error(f"Failed to create tune session: {e}")
            raise DatabaseError(f"Failed to create tune session: {e}") from e
    
    def get_tune_session(self, session_id: int) -> Optional[TuneSession]:
        """
        Get a tuning session by ID.
        
        Args:
            session_id: ID of the tuning session
            
        Returns:
            TuneSession object if found, None otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                cursor.execute("""
                    SELECT id, vehicle_id, tuner_id, start_time, end_time, 
                           description, notes, config_encrypted, is_complete
                    FROM tune_sessions WHERE id = ?
                """, (session_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                # Decrypt the config data
                config_encrypted = result[7]
                config = self._decrypt_json(config_encrypted) if config_encrypted else {}
                
                return TuneSession(
                    id=result[0],
                    vehicle_id=result[1],
                    tuner_id=result[2],
                    start_time=result[3],
                    end_time=result[4],
                    description=result[5] or "",
                    notes=result[6] or "",
                    config=config,
                    is_complete=bool(result[8])
                )
                
        except Exception as e:
            logger.error(f"Failed to get tune session: {e}")
            return None
    
    def get_tune_sessions(
        self,
        vehicle_id: Optional[int] = None,
        tuner_id: Optional[int] = None,
        is_complete: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TuneSession]:
        """
        Get a list of tuning sessions with optional filters.
        
        Args:
            vehicle_id: Filter by vehicle ID
            tuner_id: Filter by tuner ID
            is_complete: Filter by completion status
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of TuneSession objects
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                # Build the query
                query = """
                    SELECT id, vehicle_id, tuner_id, start_time, end_time, 
                           description, notes, config_encrypted, is_complete
                    FROM tune_sessions
                    WHERE 1=1
                """
                
                params = []
                
                # Add filters
                if vehicle_id is not None:
                    query += " AND vehicle_id = ?"
                    params.append(vehicle_id)
                
                if tuner_id is not None:
                    query += " AND tuner_id = ?"
                    params.append(tuner_id)
                
                if is_complete is not None:
                    query += " AND is_complete = ?"
                    params.append(int(is_complete))
                
                # Add sorting and pagination
                query += " ORDER BY start_time DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                # Execute the query
                cursor.execute(query, params)
                
                sessions = []
                for row in cursor.fetchall():
                    # Decrypt the config data
                    config_encrypted = row[7]
                    config = self._decrypt_json(config_encrypted) if config_encrypted else {}
                    
                    sessions.append(TuneSession(
                        id=row[0],
                        vehicle_id=row[1],
                        tuner_id=row[2],
                        start_time=row[3],
                        end_time=row[4],
                        description=row[5] or "",
                        notes=row[6] or "",
                        config=config,
                        is_complete=bool(row[8])
                    ))
                
                return sessions
                
        except Exception as e:
            logger.error(f"Failed to get tune sessions: {e}")
            return []
    
    def update_tune_session(self, session_id: int, **updates) -> bool:
        """
        Update a tuning session.
        
        Args:
            session_id: ID of the session to update
            **updates: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        if not updates:
            return True  # Nothing to update
        
        allowed_fields = {
            'description', 'notes', 'config', 'is_complete', 'end_time'
        }
        
        # Filter allowed fields
        updates = {k: v for k, v in updates.items() if k in allowed_fields}
        if not updates:
            return False
        
        try:
            with self.transaction() as cursor:
                # Handle config encryption
                if 'config' in updates:
                    config = updates.pop('config')
                    updates['config_encrypted'] = self._encrypt_json(config)
                
                # Handle end_time special case (set to current time if True is passed)
                if updates.get('end_time') is True:
                    updates['end_time'] = datetime.utcnow()
                
                # Build update query
                set_clause = ", ".join(
                    f"{field} = ?" if field != 'config_encrypted' else 'config_encrypted = ?'
                    for field in updates.keys()
                )
                
                # Add updated_at field
                set_clause += ", updated_at = ?"
                
                # Build parameter list
                params = list(updates.values())
                params.append(datetime.utcnow())
                
                # Add session_id for WHERE clause
                params.append(session_id)
                
                # Execute update
                cursor.execute(
                    f"UPDATE tune_sessions SET {set_clause} WHERE id = ?",
                    params
                )
                
                if cursor.rowcount == 0:
                    return False
                
                # Log the update
                self._log_security_event(
                    event_type=SecurityEventType.DATA_MODIFICATION,
                    description=f"Updated tune session: {session_id}",
                    details={"updated_fields": list(updates.keys())}
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to update tune session: {e}")
            return False
    
    def end_tune_session(self, session_id: int) -> bool:
        """
        Mark a tuning session as complete and set the end time.
        
        Args:
            session_id: ID of the session to end
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_tune_session(
            session_id,
            is_complete=True,
            end_time=True  # Will be converted to current time in update method
        )
    
    def delete_tune_session(self, session_id: int) -> bool:
        """
        Delete a tuning session and all associated data.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            with self.transaction() as cursor:
                # Get session details for logging
                cursor.execute("""
                    SELECT ts.id, ts.description, v.make, v.model, v.vin
                    FROM tune_sessions ts
                    JOIN vehicles v ON ts.vehicle_id = v.id
                    WHERE ts.id = ?
                """, (session_id,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                session_id, description, make, model, vin = result
                
                # Delete the session (foreign key constraints will handle related records)
                cursor.execute("DELETE FROM tune_sessions WHERE id = ?", (session_id,))
                
                if cursor.rowcount == 0:
                    return False
                
                # Log the deletion
                self._log_security_event(
                    event_type=SecurityEventType.DATA_MODIFICATION,
                    description=f"Deleted tune session: {description}",
                    details={
                        "session_id": session_id,
                        "vehicle": f"{make} {model} ({vin})"
                    }
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete tune session: {e}")
            return False
    
    # Diagnostic logs
    def log_diagnostic(
        self,
        session_id: int,
        code: str,
        description: str,
        severity: Union[LogSeverity, str] = LogSeverity.INFO,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> int:
        """
        Add a diagnostic log entry.
        
        Args:
            session_id: ID of the tuning session
            code: Diagnostic code (e.g., "P0172")
            description: Description of the issue
            severity: Severity level (default: INFO)
            data: Optional additional data
            timestamp: Optional timestamp (default: current time)
            
        Returns:
            The ID of the newly created log entry
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        if isinstance(severity, str):
            severity = LogSeverity(severity.lower())
        
        data = data or {}
        timestamp = timestamp or datetime.utcnow()
        
        try:
            with self.transaction() as cursor:
                # Encrypt the data
                data_encrypted = self._encrypt_json(data)
                
                cursor.execute("""
                    INSERT INTO diagnostic_logs (
                        session_id, timestamp, code, description, severity, data_encrypted
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    timestamp,
                    code,
                    description,
                    severity.value,
                    data_encrypted
                ))
                
                log_id = cursor.lastrowid
                
                # Log the event
                self._log_security_event(
                    event_type=SecurityEventType.DATA_ACCESS,
                    description=f"Added diagnostic log: {code} - {description}",
                    details={
                        "session_id": session_id,
                        "code": code,
                        "severity": severity.value
                    }
                )
                
                return log_id
                
        except Exception as e:
            logger.error(f"Failed to add diagnostic log: {e}")
            raise DatabaseError(f"Failed to add diagnostic log: {e}") from e
    
    def get_diagnostic_logs(
        self,
        session_id: Optional[int] = None,
        code: Optional[str] = None,
        severity: Optional[Union[LogSeverity, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DiagnosticLog]:
        """
        Get diagnostic logs with optional filters.
        
        Args:
            session_id: Filter by tuning session ID
            code: Filter by diagnostic code
            severity: Filter by severity level
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of DiagnosticLog objects
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        if isinstance(severity, str):
            severity = LogSeverity(severity.lower())
        
        try:
            with self.transaction() as cursor:
                # Build the query
                query = """
                    SELECT id, session_id, timestamp, code, description, 
                           severity, data_encrypted
                    FROM diagnostic_logs
                    WHERE 1=1
                """
                
                params = []
                
                # Add filters
                if session_id is not None:
                    query += " AND session_id = ?"
                    params.append(session_id)
                
                if code is not None:
                    query += " AND code = ?"
                    params.append(code.upper())
                
                if severity is not None:
                    query += " AND severity = ?"
                    params.append(severity.value)
                
                if start_time is not None:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                
                if end_time is not None:
                    query += " AND timestamp <= ?"
                    params.append(end_time)
                
                # Add sorting and pagination
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                # Execute the query
                cursor.execute(query, params)
                
                logs = []
                for row in cursor.fetchall():
                    # Decrypt the data
                    data_encrypted = row[6]
                    data = self._decrypt_json(data_encrypted) if data_encrypted else {}
                    
                    logs.append(DiagnosticLog(
                        id=row[0],
                        session_id=row[1],
                        timestamp=row[2],
                        code=row[3],
                        description=row[4],
                        severity=LogSeverity(row[5]),
                        data=data
                    ))
                
                return logs
                
        except Exception as e:
            logger.error(f"Failed to get diagnostic logs: {e}")
            return []
    
    def delete_diagnostic_logs(
        self,
        session_id: Optional[int] = None,
        code: Optional[str] = None,
        severity: Optional[Union[LogSeverity, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        Delete diagnostic logs matching the specified criteria.
        
        Args:
            session_id: Filter by tuning session ID
            code: Filter by diagnostic code
            severity: Filter by severity level
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            
        Returns:
            Number of logs deleted
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        if isinstance(severity, str):
            severity = LogSeverity(severity.lower())
        
        try:
            with self.transaction() as cursor:
                # Build the query
                query = "DELETE FROM diagnostic_logs WHERE 1=1"
                params = []
                
                # Add filters
                if session_id is not None:
                    query += " AND session_id = ?"
                    params.append(session_id)
                
                if code is not None:
                    query += " AND code = ?"
                    params.append(code.upper())
                
                if severity is not None:
                    query += " AND severity = ?"
                    params.append(severity.value)
                
                if start_time is not None:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                
                if end_time is not None:
                    query += " AND timestamp <= ?"
                    params.append(end_time)
                
                # Execute the query
                cursor.execute(query, params)
                deleted_count = cursor.rowcount
                
                # Log the deletion
                if deleted_count > 0:
                    self._log_security_event(
                        event_type=SecurityEventType.DATA_MODIFICATION,
                        description=f"Deleted {deleted_count} diagnostic logs",
                        details={
                            "session_id": session_id,
                            "code": code,
                            "severity": severity.value if severity else None,
                            "start_time": start_time.isoformat() if start_time else None,
                            "end_time": end_time.isoformat() if end_time else None
                        }
                    )
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to delete diagnostic logs: {e}")
            return 0
    
    # Security logs
    def _log_security_event(
        self,
        event_type: Union[SecurityEventType, str],
        description: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Internal method to log security events.
        
        Args:
            event_type: Type of security event
            description: Description of the event
            user_id: ID of the user associated with the event
            ip_address: IP address where the event originated
            details: Additional details about the event
            
        Returns:
            The ID of the newly created log entry
        """
        if not self.connection:
            return -1  # Don't raise an error if we can't log
        
        if isinstance(event_type, str):
            event_type = SecurityEventType(event_type.lower())
        
        details = details or {}
        
        try:
            with self.transaction() as cursor:
                # Encrypt the details
                details_encrypted = self._encrypt_json(details)
                
                cursor.execute("""
                    INSERT INTO security_logs (
                        timestamp, event_type, user_id, ip_address, 
                        description, details_encrypted
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    datetime.utcnow(),
                    event_type.value,
                    user_id,
                    ip_address,
                    description,
                    details_encrypted
                ))
                
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return -1
    
    def get_security_logs(
        self,
        event_type: Optional[Union[SecurityEventType, str]] = None,
        user_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SecurityLog]:
        """
        Get security logs with optional filters.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            ip_address: Filter by IP address
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of SecurityLog objects
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        if isinstance(event_type, str):
            event_type = SecurityEventType(event_type.lower())
        
        try:
            with self.transaction() as cursor:
                # Build the query
                query = """
                    SELECT id, timestamp, event_type, user_id, ip_address, 
                           description, details_encrypted
                    FROM security_logs
                    WHERE 1=1
                """
                
                params = []
                
                # Add filters
                if event_type is not None:
                    query += " AND event_type = ?"
                    params.append(event_type.value)
                
                if user_id is not None:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                if start_time is not None:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                
                if end_time is not None:
                    query += " AND timestamp <= ?"
                    params.append(end_time)
                
                if ip_address is not None:
                    query += " AND ip_address = ?"
                    params.append(ip_address)
                
                # Add sorting and pagination
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                # Execute the query
                cursor.execute(query, params)
                
                logs = []
                for row in cursor.fetchall():
                    # Decrypt the details
                    details_encrypted = row[6]
                    details = self._decrypt_json(details_encrypted) if details_encrypted else {}
                    
                    logs.append(SecurityLog(
                        id=row[0],
                        timestamp=row[1],
                        event_type=SecurityEventType(row[2]),
                        user_id=row[3],
                        ip_address=row[4],
                        description=row[5] or "",
                        details=details
                    ))
                
                return logs
                
        except Exception as e:
            logger.error(f"Failed to get security logs: {e}")
            return []
    
    # Backup and restore
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path to save the backup file
            
        Returns:
            True if backup was successful, False otherwise
        """
        if not self.connection:
            raise DatabaseError("Not connected to database")
        
        try:
            # Ensure the backup directory exists
            backup_dir = os.path.dirname(os.path.abspath(backup_path))
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create a backup using SQLite's backup API
            backup_conn = sqlite3.connect(backup_path)
            with backup_conn:
                self.connection.backup(backup_conn, pages=1)
            backup_conn.close()
            
            logger.info(f"Database backup created at: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Restore the database from a backup.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if restore was successful, False otherwise
        """
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        try:
            # Close the current connection
            if self.connection:
                self.connection.close()
            
            # Make a temporary copy of the current database
            import shutil
            import tempfile
            import os
            
            # Create secure temporary directory with restricted permissions
            temp_dir = tempfile.mkdtemp(mode=0o700, dir='/tmp')
            temp_backup = os.path.join(temp_dir, "temp_backup.db")
            
            try:
                # Copy the current database to a temporary location
                if os.path.exists(self.db_path):
                    shutil.copy2(self.db_path, temp_backup)
                
                # Replace the current database with the backup
                shutil.copy2(backup_path, self.db_path)
                
                # Reconnect to the database
                self._connect()
                
                logger.info(f"Database restored from backup: {backup_path}")
                return True
                
            except Exception as e:
                # Restore from the temporary backup if something goes wrong
                logger.error(f"Restore failed, attempting to restore from temporary backup: {e}")
                
                if os.path.exists(temp_backup):
                    shutil.copy2(temp_backup, self.db_path)
                    logger.info("Restored from temporary backup")
                
                # Reconnect to the database
                self._connect()
                
                return False
                
            finally:
                # Clean up the temporary directory
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary directory: {e}")
            
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            
            # Try to reconnect to the database
            try:
                self._connect()
            except Exception as conn_error:
                logger.critical(f"Failed to reconnect to database: {conn_error}")
            
            return False
    
    # Context manager methods
    def __enter__(self):
        """Enter the runtime context related to this object."""
        if not self.connection:
            self._connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context and close the database connection."""
        self.close()
    
    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            try:
                if self._in_transaction:
                    self.connection.rollback()
                    self._in_transaction = False
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self.connection = None
    
    def __del__(self):
        """Ensure the database connection is closed when the object is destroyed."""
        self.close()

# Example usage
def example_usage():
    """Example of how to use the SecureDatabase class."""
    # Initialize the database
    db = SecureDatabase("secure_tunes.db", encryption_key=b"your-secret-key-here")
    
    try:
        # Create a user
        user_id = db.create_user(
            username="tuner1",
            password="securepassword123",
            email="tuner@example.com",
            first_name="John",
            last_name="Tuner",
            role=UserRole.TUNER
        )
        print(f"Created user with ID: {user_id}")
        
        # Add a vehicle
        vehicle_id = db.add_vehicle(
            vin="JM1NDAM72K0303030",
            make="Mazda",
            model="MX-5",
            year=2019,
            engine="2.0L Skyactiv-G",
            owner_id=user_id,
            notes="Track day car"
        )
        print(f"Added vehicle with ID: {vehicle_id}")
        
        # Create a tuning session
        session_id = db.create_tune_session(
            vehicle_id=vehicle_id,
            tuner_id=user_id,
            description="ECU remap stage 1",
            config={"tune_version": "1.0", "octane": 93}
        )
        print(f"Created tuning session with ID: {session_id}")
        
        # Add some diagnostic logs
        db.log_diagnostic(
            session_id=session_id,
            code="P0172",
            description="System too rich (bank 1)",
            severity=LogSeverity.WARNING,
            data={"bank": 1, "fuel_trim": -12.5}
        )
        
        # Complete the tuning session
        db.end_tune_session(session_id)
        
        # Query the data
        sessions = db.get_tune_sessions(vehicle_id=vehicle_id)
        print(f"Found {len(sessions)} tuning sessions")
        
        for session in sessions:
            print(f"\nSession: {session.description}")
            print(f"  Start: {session.start_time}")
            print(f"  End: {session.end_time}")
            print(f"  Config: {session.config}")
            
            # Get diagnostic logs for this session
            logs = db.get_diagnostic_logs(session_id=session.id)
            print(f"  Found {len(logs)} diagnostic logs")
            
            for log in logs:
                print(f"    {log.code}: {log.description} ({log.severity.value})")
        
        # Get security logs
        security_logs = db.get_security_logs(limit=5)
        print("\nRecent security events:")
        for log in security_logs:
            print(f"  {log.timestamp} - {log.event_type.value}: {log.description}")
        
    finally:
        # Close the database connection
        db.close()

if __name__ == "__main__":
    example_usage()
