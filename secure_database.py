"""
SecureDatabase - SQLite-based persistence layer with SecurityCore integration.
Provides secure storage for tuning profiles, telemetry data, user credentials,
and application configuration with encryption for sensitive data.
"""

import sqlite3
import json
import time
import threading
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import asyncio
from contextlib import asynccontextmanager, contextmanager

from models import (
    SecurityLevel, SecurityCredentials, LogEntry, TelemetryData,
    DiagnosticTroubleCode, TuningParameter, TuningProfile, FlashOperation,
    VehicleState, TuningMode
)
from mazda_security_core import MazdaSecurityCore


class DatabaseError(Exception):
    """Database operation errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Database connection errors."""
    pass


class DatabaseSecurityError(DatabaseError):
    """Database security errors."""
    pass


@dataclass
class DatabaseConfig:
    """Database configuration."""
    db_path: str = "muts_database.db"
    enable_encryption: bool = True
    enable_wal: bool = True
    connection_timeout: float = 30.0
    max_connections: int = 10
    auto_vacuum: bool = True
    foreign_keys: bool = True
    
    # Security settings
    encrypt_sensitive_data: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = 24


class SecureDatabase:
    """
    Secure SQLite database with encryption integration.
    Provides thread-safe operations and automatic backup functionality.
    """
    
    # Database schema version
    SCHEMA_VERSION = 1
    
    # Table definitions
    TABLES = {
        "schema_version": """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """,
        
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                security_level INTEGER NOT NULL,
                permissions TEXT,
                created_at REAL NOT NULL,
                last_login REAL,
                active BOOLEAN DEFAULT 1
            )
        """,
        
        "sessions": """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at REAL NOT NULL,
                created_at REAL NOT NULL,
                last_accessed REAL NOT NULL,
                data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """,
        
        "tuning_profiles": """
            CREATE TABLE IF NOT EXISTS tuning_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mode TEXT NOT NULL,
                parameters_encrypted TEXT,
                created_at REAL NOT NULL,
                modified_at REAL NOT NULL,
                version TEXT DEFAULT '1.0',
                author TEXT,
                description TEXT,
                checksum TEXT,
                backup_id TEXT
            )
        """,
        
        "telemetry_data": """
            CREATE TABLE IF NOT EXISTS telemetry_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp REAL NOT NULL,
                data_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                processed BOOLEAN DEFAULT 0
            )
        """,
        
        "diagnostic_codes": """
            CREATE TABLE IF NOT EXISTS diagnostic_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                first_occurrence REAL NOT NULL,
                last_occurrence REAL NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                freeze_frame_data TEXT,
                created_at REAL NOT NULL
            )
        """,
        
        "flash_operations": """
            CREATE TABLE IF NOT EXISTS flash_operations (
                id TEXT PRIMARY KEY,
                operation_type TEXT NOT NULL,
                state TEXT NOT NULL,
                progress REAL DEFAULT 0.0,
                start_time REAL NOT NULL,
                estimated_completion REAL,
                error_message TEXT,
                backup_created BOOLEAN DEFAULT 0,
                checksum_verified BOOLEAN DEFAULT 0,
                metadata TEXT
            )
        """,
        
        "vehicle_info": """
            CREATE TABLE IF NOT EXISTS vehicle_info (
                id INTEGER PRIMARY KEY,
                vin TEXT UNIQUE,
                ecu_serial TEXT,
                software_version TEXT,
                calibration_version TEXT,
                hardware_version TEXT,
                last_updated REAL NOT NULL,
                metadata TEXT
            )
        """,
        
        "application_logs": """
            CREATE TABLE IF NOT EXISTS application_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                level TEXT NOT NULL,
                module TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                created_at REAL NOT NULL
            )
        """,
        
        "backups": """
            CREATE TABLE IF NOT EXISTS backups (
                id TEXT PRIMARY KEY,
                backup_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                size INTEGER NOT NULL,
                checksum TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL,
                metadata TEXT
            )
        """,
    }
    
    def __init__(self, config: Optional[DatabaseConfig] = None,
                 security_core: Optional[MazdaSecurityCore] = None):
        """
        Initialize secure database.
        
        Args:
            config: Database configuration
            security_core: Security core for encryption
        """
        self.config = config or DatabaseConfig()
        self.security_core = security_core or MazdaSecurityCore()
        self.logger = logging.getLogger(__name__)
        
        # Database path and connection management
        self.db_path = Path(self.config.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connection pooling
        self._connections: Dict[int, sqlite3.Connection] = {}
        self._connection_lock = threading.Lock()
        self._connection_count = 0
        
        # Background tasks
        self._backup_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Initialize database
        self._initialize_database()
        
        self.logger.info(f"SecureDatabase initialized: {self.db_path}")
    
    def _initialize_database(self) -> None:
        """Initialize database schema and perform migrations."""
        with self._get_connection() as conn:
            # Enable SQLite features
            if self.config.enable_wal:
                conn.execute("PRAGMA journal_mode=WAL")
            
            if self.config.auto_vacuum:
                conn.execute("PRAGMA auto_vacuum=FULL")
            
            if self.config.foreign_keys:
                conn.execute("PRAGMA foreign_keys=ON")
            
            # Create tables
            for table_name, create_sql in self.TABLES.items():
                conn.execute(create_sql)
                self.logger.debug(f"Created table: {table_name}")
            
            # Initialize schema version
            conn.execute("""
                INSERT OR IGNORE INTO schema_version (version, created_at, updated_at)
                VALUES (?, ?, ?)
            """, (self.SCHEMA_VERSION, time.time(), time.time()))
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection from pool."""
        thread_id = threading.get_ident()
        
        with self._connection_lock:
            if thread_id not in self._connections:
                if self._connection_count >= self.config.max_connections:
                    raise DatabaseConnectionError("Maximum connections reached")
                
                conn = sqlite3.connect(
                    str(self.db_path),
                    timeout=self.config.connection_timeout,
                    check_same_thread=False
                )
                conn.row_factory = sqlite3.Row
                
                self._connections[thread_id] = conn
                self._connection_count += 1
            
            yield self._connections[thread_id]
    
    def _encrypt_data(self, data: Union[str, bytes, dict]) -> str:
        """Encrypt sensitive data using SecurityCore."""
        if not self.config.encrypt_sensitive_data:
            if isinstance(data, dict):
                return json.dumps(data)
            return str(data)
        
        try:
            if isinstance(data, dict):
                data_bytes = json.dumps(data).encode()
            elif isinstance(data, str):
                data_bytes = data.encode()
            else:
                data_bytes = data
            
            encrypted = self.security_core.encrypt_data(data_bytes)
            return encrypted.decode()
            
        except Exception as e:
            self.logger.error(f"Data encryption failed: {e}")
            raise DatabaseSecurityError(f"Encryption failed: {e}")
    
    def _decrypt_data(self, encrypted_data: str) -> Union[str, dict]:
        """Decrypt sensitive data using SecurityCore."""
        if not self.config.encrypt_sensitive_data:
            # Try to parse as JSON, fallback to string
            try:
                return json.loads(encrypted_data)
            except (json.JSONDecodeError, TypeError):
                return encrypted_data
        
        try:
            decrypted = self.security_core.decrypt_data(encrypted_data.encode())
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted.decode())
            except (json.JSONDecodeError, TypeError):
                return decrypted.decode()
                
        except Exception as e:
            self.logger.error(f"Data decryption failed: {e}")
            raise DatabaseSecurityError(f"Decryption failed: {e}")
    
    # User Management
    async def create_user(self, username: str, password_hash: str,
                         security_level: SecurityLevel,
                         permissions: List[str]) -> bool:
        """
        Create new user account.
        
        Args:
            username: Username
            password_hash: Password hash
            security_level: Security level
            permissions: List of permissions
            
        Returns:
            True if user created successfully
        """
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (username, password_hash, security_level, permissions, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    username,
                    password_hash,
                    security_level.value,
                    json.dumps(permissions),
                    time.time()
                ))
                conn.commit()
                
                self.logger.info(f"User created: {username}")
                return True
                
        except sqlite3.IntegrityError:
            self.logger.warning(f"User already exists: {username}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")
            return False
    
    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information by username."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM users WHERE username = ? AND active = 1
                """, (username,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row["id"],
                        "username": row["username"],
                        "password_hash": row["password_hash"],
                        "security_level": SecurityLevel(row["security_level"]),
                        "permissions": json.loads(row["permissions"]),
                        "created_at": row["created_at"],
                        "last_login": row["last_login"],
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get user: {e}")
            return None
    
    # Session Management
    async def create_session(self, session_id: str, user_id: int,
                           expires_at: float, data: Optional[Dict] = None) -> bool:
        """Create user session."""
        try:
            encrypted_data = self._encrypt_data(data) if data else None
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO sessions (id, user_id, expires_at, created_at, last_accessed, data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    user_id,
                    expires_at,
                    time.time(),
                    time.time(),
                    encrypted_data
                ))
                conn.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM sessions WHERE id = ? AND expires_at > ?
                """, (session_id, time.time()))
                
                row = cursor.fetchone()
                if row:
                    # Update last accessed
                    conn.execute("""
                        UPDATE sessions SET last_accessed = ? WHERE id = ?
                    """, (time.time(), session_id))
                    conn.commit()
                    
                    return {
                        "id": row["id"],
                        "user_id": row["user_id"],
                        "expires_at": row["expires_at"],
                        "created_at": row["created_at"],
                        "last_accessed": row["last_accessed"],
                        "data": self._decrypt_data(row["data"]) if row["data"] else None,
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get session: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM sessions WHERE id = ?
                """, (session_id,))
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to delete session: {e}")
            return False
    
    # Tuning Profiles
    async def save_tuning_profile(self, profile: TuningProfile) -> bool:
        """Save tuning profile to database."""
        try:
            # Serialize parameters
            parameters_data = {
                name: asdict(param) for name, param in profile.parameters.items()
            }
            
            encrypted_params = self._encrypt_data(parameters_data)
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tuning_profiles 
                    (name, mode, parameters_encrypted, created_at, modified_at, 
                     version, author, description, checksum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile.name,
                    profile.mode.value,
                    encrypted_params,
                    profile.created_at.timestamp(),
                    profile.modified_at.timestamp(),
                    profile.version,
                    profile.author,
                    profile.description,
                    self._calculate_profile_checksum(profile)
                ))
                conn.commit()
                
                self.logger.info(f"Tuning profile saved: {profile.name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save tuning profile: {e}")
            return False
    
    async def load_tuning_profile(self, name: str) -> Optional[TuningProfile]:
        """Load tuning profile from database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM tuning_profiles WHERE name = ?
                """, (name,))
                
                row = cursor.fetchone()
                if row:
                    # Decrypt parameters
                    parameters_data = self._decrypt_data(row["parameters_encrypted"])
                    
                    # Reconstruct TuningParameter objects
                    parameters = {}
                    for param_name, param_data in parameters_data.items():
                        parameters[param_name] = TuningParameter(**param_data)
                    
                    return TuningProfile(
                        name=row["name"],
                        mode=TuningMode(row["mode"]),
                        parameters=parameters,
                        created_at=time.time(),  # Will be updated from timestamp
                        modified_at=time.time(),
                        version=row["version"],
                        author=row["author"],
                        description=row["description"]
                    )
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to load tuning profile: {e}")
            return None
    
    async def list_tuning_profiles(self) -> List[Dict[str, Any]]:
        """List all tuning profiles."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT name, mode, version, author, description, modified_at
                    FROM tuning_profiles
                    ORDER BY modified_at DESC
                """)
                
                profiles = []
                for row in cursor.fetchall():
                    profiles.append({
                        "name": row["name"],
                        "mode": row["mode"],
                        "version": row["version"],
                        "author": row["author"],
                        "description": row["description"],
                        "modified_at": row["modified_at"],
                    })
                
                return profiles
                
        except Exception as e:
            self.logger.error(f"Failed to list tuning profiles: {e}")
            return []
    
    # Telemetry Data
    async def save_telemetry_data(self, session_id: str, 
                                 telemetry: TelemetryData) -> bool:
        """Save telemetry data to database."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO telemetry_data (session_id, timestamp, data_json, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    session_id,
                    telemetry.timestamp,
                    json.dumps(telemetry.to_dict()),
                    time.time()
                ))
                conn.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save telemetry data: {e}")
            return False
    
    async def get_telemetry_data(self, session_id: str, 
                               limit: int = 1000,
                               start_time: Optional[float] = None,
                               end_time: Optional[float] = None) -> List[TelemetryData]:
        """Get telemetry data for session."""
        try:
            with self._get_connection() as conn:
                query = """
                    SELECT data_json FROM telemetry_data 
                    WHERE session_id = ?
                """
                params = [session_id]
                
                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time)
                
                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                
                telemetry_data = []
                for row in cursor.fetchall():
                    data_dict = json.loads(row["data_json"])
                    telemetry = TelemetryData(**data_dict)
                    telemetry_data.append(telemetry)
                
                return telemetry_data
                
        except Exception as e:
            self.logger.error(f"Failed to get telemetry data: {e}")
            return []
    
    # Diagnostic Codes
    async def save_dtc(self, dtc: DiagnosticTroubleCode) -> bool:
        """Save diagnostic trouble code."""
        try:
            freeze_frame_json = json.dumps(dtc.freeze_frame.to_dict()) if dtc.freeze_frame else None
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO diagnostic_codes
                    (code, description, status, first_occurrence, last_occurrence,
                     occurrence_count, freeze_frame_data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dtc.code,
                    dtc.description,
                    dtc.status,
                    dtc.first_occurrence.timestamp(),
                    dtc.last_occurrence.timestamp(),
                    dtc.occurrence_count,
                    freeze_frame_json,
                    time.time()
                ))
                conn.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save DTC: {e}")
            return False
    
    async def get_dtcs(self, status: Optional[str] = None) -> List[DiagnosticTroubleCode]:
        """Get diagnostic trouble codes."""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM diagnostic_codes"
                params = []
                
                if status:
                    query += " WHERE status = ?"
                    params.append(status)
                
                query += " ORDER BY last_occurrence DESC"
                
                cursor = conn.execute(query, params)
                
                dtcs = []
                for row in cursor.fetchall():
                    freeze_frame = None
                    if row["freeze_frame_data"]:
                        freeze_frame_dict = json.loads(row["freeze_frame_data"])
                        freeze_frame = TelemetryData(**freeze_frame_dict)
                    
                    dtc = DiagnosticTroubleCode(
                        code=row["code"],
                        description=row["description"],
                        status=row["status"],
                        first_occurrence=time.time(),  # Will be updated from timestamp
                        last_occurrence=time.time(),
                        occurrence_count=row["occurrence_count"],
                        freeze_frame=freeze_frame
                    )
                    dtcs.append(dtc)
                
                return dtcs
                
        except Exception as e:
            self.logger.error(f"Failed to get DTCs: {e}")
            return []
    
    # Flash Operations
    async def save_flash_operation(self, operation: FlashOperation) -> bool:
        """Save flash operation."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO flash_operations
                    (id, operation_type, state, progress, start_time, estimated_completion,
                     error_message, backup_created, checksum_verified, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    operation.operation_id,
                    operation.state.value,
                    operation.progress,
                    operation.start_time.timestamp(),
                    operation.estimated_completion.timestamp() if operation.estimated_completion else None,
                    operation.error_message,
                    operation.backup_created,
                    operation.checksum_verified,
                    json.dumps({"elapsed_time": operation.elapsed_time})
                ))
                conn.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save flash operation: {e}")
            return False
    
    async def get_flash_operation(self, operation_id: str) -> Optional[FlashOperation]:
        """Get flash operation."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM flash_operations WHERE id = ?
                """, (operation_id,))
                
                row = cursor.fetchone()
                if row:
                    return FlashOperation(
                        operation_id=row["id"],
                        state=FlashState(row["state"]),
                        progress=row["progress"],
                        start_time=time.time(),  # Will be updated from timestamp
                        estimated_completion=time.time() if row["estimated_completion"] else None,
                        error_message=row["error_message"],
                        backup_created=bool(row["backup_created"]),
                        checksum_verified=bool(row["checksum_verified"])
                    )
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get flash operation: {e}")
            return None
    
    # Vehicle Information
    async def save_vehicle_info(self, vin: str, ecu_info: Dict[str, Any]) -> bool:
        """Save vehicle information."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO vehicle_info
                    (id, vin, ecu_serial, software_version, calibration_version,
                     hardware_version, last_updated, metadata)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vin,
                    ecu_info.get("serial", ""),
                    ecu_info.get("software_version", ""),
                    ecu_info.get("calibration_version", ""),
                    ecu_info.get("hardware_version", ""),
                    time.time(),
                    json.dumps(ecu_info)
                ))
                conn.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save vehicle info: {e}")
            return False
    
    async def get_vehicle_info(self) -> Optional[Dict[str, Any]]:
        """Get vehicle information."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM vehicle_info WHERE id = 1
                """)
                
                row = cursor.fetchone()
                if row:
                    metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                    return {
                        "vin": row["vin"],
                        "ecu_serial": row["ecu_serial"],
                        "software_version": row["software_version"],
                        "calibration_version": row["calibration_version"],
                        "hardware_version": row["hardware_version"],
                        "last_updated": row["last_updated"],
                        "metadata": metadata,
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get vehicle info: {e}")
            return None
    
    # Application Logs
    async def save_log_entry(self, entry: LogEntry) -> bool:
        """Save application log entry."""
        try:
            data_json = json.dumps(entry.data) if entry.data else None
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO application_logs
                    (timestamp, level, module, message, data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entry.timestamp.timestamp(),
                    entry.level,
                    entry.module,
                    entry.message,
                    data_json,
                    time.time()
                ))
                conn.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save log entry: {e}")
            return False
    
    async def get_log_entries(self, level: Optional[str] = None,
                            module: Optional[str] = None,
                            limit: int = 1000) -> List[LogEntry]:
        """Get application log entries."""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM application_logs WHERE 1=1"
                params = []
                
                if level:
                    query += " AND level = ?"
                    params.append(level)
                
                if module:
                    query += " AND module = ?"
                    params.append(module)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                
                entries = []
                for row in cursor.fetchall():
                    data = json.loads(row["data"]) if row["data"] else None
                    entry = LogEntry(
                        timestamp=time.time(),  # Will be updated from timestamp
                        level=row["level"],
                        module=row["module"],
                        message=row["message"],
                        data=data
                    )
                    entries.append(entry)
                
                return entries
                
        except Exception as e:
            self.logger.error(f"Failed to get log entries: {e}")
            return []
    
    # Database Maintenance
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM sessions WHERE expires_at < ?
                """, (time.time(),))
                conn.commit()
                
                count = cursor.rowcount
                if count > 0:
                    self.logger.info(f"Cleaned up {count} expired sessions")
                
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """Clean up old log entries."""
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM application_logs WHERE created_at < ?
                """, (cutoff_time,))
                conn.commit()
                
                count = cursor.rowcount
                if count > 0:
                    self.logger.info(f"Cleaned up {count} old log entries")
                
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")
            return 0
    
    def _calculate_profile_checksum(self, profile: TuningProfile) -> str:
        """Calculate checksum for tuning profile."""
        profile_data = {
            "name": profile.name,
            "mode": profile.mode.value,
            "parameters": {name: asdict(param) for name, param in profile.parameters.items()},
            "version": profile.version,
        }
        return self.security_core.secure_hash(json.dumps(profile_data).encode())
    
    async def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """Create database backup."""
        try:
            if not backup_path:
                timestamp = int(time.time())
                backup_path = f"muts_backup_{timestamp}.db"
            
            # SQLite backup
            with self._get_connection() as source:
                backup_conn = sqlite3.connect(backup_path)
                source.backup(backup_conn)
                backup_conn.close()
            
            self.logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self._get_connection() as conn:
                stats = {}
                
                # Table row counts
                for table_name in self.TABLES.keys():
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    stats[f"{table_name}_count"] = cursor.fetchone()[0]
                
                # Database size
                stats["database_size_bytes"] = self.db_path.stat().st_size
                
                # Connection info
                stats["active_connections"] = self._connection_count
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def close(self) -> None:
        """Close all database connections."""
        with self._connection_lock:
            for conn in self._connections.values():
                try:
                    conn.close()
                except Exception:
                    pass
            
            self._connections.clear()
            self._connection_count = 0
        
        self.logger.info("Database connections closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except Exception:
            pass
