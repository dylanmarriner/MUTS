"""
MazdaTunerAPI - High-performance async REST API for Mazda vehicle tuning.

This module provides a comprehensive API for interacting with Mazda vehicles,
including diagnostics, tuning, and real-time data streaming.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Awaitable

import aiohttp
import aiohttp.web as web
import aiohttp_jinja2
import aiohttp_session
import aiohttp_session.cookie_storage
import async_timeout
import jwt
from aiohttp import WSMsgType
from aiohttp.web import Request, Response, WebSocketResponse, json_response
from aiohttp.web_exceptions import HTTPException, HTTPUnauthorized, HTTPBadRequest
from aiohttp.web_middlewares import middleware
from aiohttp_swagger import setup_swagger
from cryptography.fernet import Fernet
from dataclasses import dataclass, asdict, field
from enum import Enum
from functools import wraps
from jinja2 import FileSystemLoader

# Import our database and security modules
from SecureDatabase import SecureDatabase, User, Vehicle, TuneSession, DiagnosticLog, SecurityLog, UserRole
from MazdaCANEngine import MazdaCANEngine
from RealTimeAITuner import RealTimeAITuner, FeatureConfig, OutputConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type aliases
JSONType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
RouteHandler = Callable[[Request], Awaitable[Response]]

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 3600  # 1 hour

# API configuration
API_PREFIX = "/api/v1"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# WebSocket configuration
WS_HEARTBEAT = 25.0  # seconds
WS_TIMEOUT = 10.0  # seconds

class APIError(Exception):
    """Base exception for API errors."""
    def __init__(self, message: str, status_code: int = 400, error_code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        super().__init__(self.message)

class AuthError(APIError):
    """Authentication/authorization error."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401, "AUTH_ERROR")

class PermissionDenied(APIError):
    """Permission denied error."""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, 403, "PERMISSION_DENIED")

class ValidationError(APIError):
    """Request validation error."""
    def __init__(self, message: str = "Validation failed", errors: Optional[Dict] = None):
        self.errors = errors or {}
        super().__init__(message, 400, "VALIDATION_ERROR")

class VehicleConnectionError(APIError):
    """Vehicle connection error."""
    def __init__(self, message: str = "Vehicle connection failed"):
        super().__init__(message, 503, "VEHICLE_CONNECTION_ERROR")

class TuningError(APIError):
    """Tuning operation error."""
    def __init__(self, message: str = "Tuning operation failed"):
        super().__init__(message, 500, "TUNING_ERROR")

@dataclass
class UserSession:
    """User session information."""
    user_id: int
    username: str
    role: UserRole
    expires_at: datetime
    token: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role.value,
            "expires_at": self.expires_at.isoformat(),
            "token": self.token
        }
    
    @property
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at

@dataclass
class VehicleConnection:
    """Active vehicle connection."""
    connection_id: str
    vehicle_id: int
    user_id: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    can_engine: Optional[MazdaCANEngine] = None
    ai_tuner: Optional[RealTimeAITuner] = None
    websockets: List[WebSocketResponse] = field(default_factory=list)
    
    async def close(self):
        """Close the vehicle connection and clean up resources."""
        if self.can_engine:
            try:
                await self.can_engine.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting CAN engine: {e}")
        
        # Close all WebSocket connections
        for ws in self.websockets:
            try:
                if not ws.closed:
                    await ws.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        
        self.websockets.clear()
        self.can_engine = None
        self.ai_tuner = None

class MazdaTunerAPI:
    """Mazda Tuner API server."""
    
    def __init__(self, db_path: str = "mazda_tuner.db", host: str = "0.0.0.0", port: int = 8080):
        """Initialize the API server."""
        self.host = host
        self.port = port
        self.app = web.Application(middlewares=[self.error_middleware])
        self.runner = None
        self.site = None
        
        # Initialize database
        self.db = SecureDatabase(db_path)
        
        # Active connections
        self.connections: Dict[str, VehicleConnection] = {}
        self.sessions: Dict[str, UserSession] = {}
        
        # Setup application
        self._setup_middleware()
        self._setup_routes()
        self._setup_cleanup_tasks()
    
    # Middleware
    @web.middleware
    async def error_middleware(self, request: Request, handler: RouteHandler) -> Response:
        """Global error handling middleware."""
        try:
            return await handler(request)
        except APIError as e:
            return json_response(
                status=e.status_code,
                data={
                    "error": {
                        "code": e.error_code,
                        "message": e.message,
                        "details": getattr(e, "errors", None)
                    }
                }
            )
        except HTTPException as e:
            return json_response(
                status=e.status_code,
                data={
                    "error": {
                        "code": f"HTTP_{e.status_code}",
                        "message": e.reason
                    }
                }
            )
        except Exception as e:
            logger.exception("Unexpected error:")
            return json_response(
                status=500,
                data={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred"
                    }
                }
            )
    
    def _setup_middleware(self):
        """Set up application middleware."""
        # Session middleware
        secret_key = Fernet.generate_key()
        aiohttp_session.setup(
            self.app,
            aiohttp_session.cookie_storage.EncryptedCookieStorage(secret_key)
        )
        
        # CORS middleware
        async def cors_middleware(app, handler):
            async def middleware_handler(request):
                # Handle preflight requests
                if request.method == "OPTIONS":
                    response = web.Response()
                else:
                    response = await handler(request)
                
                # Add CORS headers
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                
                return response
            
            return middleware_handler
        
        self.app.middlewares.append(cors_middleware)
        
        # Request logging middleware
        @web.middleware
        async def logging_middleware(request: Request, handler: RouteHandler) -> Response:
            start_time = time.time()
            
            # Log the request
            logger.info(f"{request.method} {request.path} from {request.remote}")
            
            try:
                response = await handler(request)
                process_time = time.time() - start_time
                
                # Log the response
                logger.info(
                    f"{request.method} {request.path} - "
                    f"Status: {response.status} - "
                    f"Time: {process_time:.3f}s"
                )
                
                return response
                
            except Exception as e:
                process_time = time.time() - start_time
                logger.error(
                    f"{request.method} {request.path} - "
                    f"Error: {str(e)} - "
                    f"Time: {process_time:.3f}s"
                )
                raise
        
        self.app.middlewares.append(logging_middleware)
    
    # Route setup
    def _setup_routes(self):
        """Set up API routes."""
        # Auth routes
        self.app.router.add_post(f"{API_PREFIX}/auth/register", self.register)
        self.app.router.add_post(f"{API_PREFIX}/auth/login", self.login)
        self.app.router.add_post(f"{API_PREFIX}/auth/refresh", self.refresh_token)
        self.app.router.add_post(f"{API_PREFIX}/auth/logout", self.logout)
        
        # User routes
        self.app.router.add_get(f"{API_PREFIX}/users/me", self.get_current_user)
        self.app.router.add_put(f"{API_PREFIX}/users/me", self.update_current_user)
        
        # Vehicle routes
        self.app.router.add_post(f"{API_PREFIX}/vehicles/connect", self.connect_vehicle)
        self.app.router.add_post(f"{API_PREFIX}/vehicles/{{vehicle_id}}/disconnect", self.disconnect_vehicle)
        self.app.router.add_get(f"{API_PREFIX}/vehicles", self.list_vehicles)
        self.app.router.add_get(f"{API_PREFIX}/vehicles/{{vehicle_id}}", self.get_vehicle)
        self.app.router.add_post(f"{API_PREFIX}/vehicles", self.add_vehicle)
        self.app.router.add_put(f"{API_PREFIX}/vehicles/{{vehicle_id}}", self.update_vehicle)
        self.app.router.add_delete(f"{API_PREFIX}/vehicles/{{vehicle_id}}", self.delete_vehicle)
        
        # Diagnostic routes
        self.app.router.add_post(f"{API_PREFIX}/vehicles/{{vehicle_id}}/diagnostics/scan", self.scan_diagnostics)
        self.app.router.add_post(f"{API_PREFIX}/vehicles/{{vehicle_id}}/diagnostics/clear", self.clear_diagnostics)
        self.app.router.add_get(f"{API_PREFIX}/vehicles/{{vehicle_id}}/diagnostics", self.get_diagnostic_logs)
        
        # Tuning routes
        self.app.router.add_post(f"{API_PREFIX}/vehicles/{{vehicle_id}}/tunes/generate", self.generate_tune)
        self.app.router.add_post(f"{API_PREFIX}/vehicles/{{vehicle_id}}/tunes/optimize", self.optimize_tune)
        self.app.router.add_post(f"{API_PREFIX}/vehicles/{{vehicle_id}}/tunes/flash", self.flash_tune)
        self.app.router.add_get(f"{API_PREFIX}/vehicles/{{vehicle_id}}/tunes", self.list_tunes)
        self.app.router.add_get(f"{API_PREFIX}/tunes/{{tune_id}}", self.get_tune)
        
        # Real-time data routes
        self.app.router.add_get(f"{API_PREFIX}/vehicles/{{vehicle_id}}/stream", self.data_stream)
        
        # WebSocket endpoint
        self.app.router.add_get(f"{API_PREFIX}/ws", self.websocket_handler)
        
        # Static files and frontend
        self.app.router.add_static("/static", "static")
        self.app.router.add_get("/{path:.*}", self.serve_frontend)
        
        # Setup Swagger documentation
        setup_swagger(
            self.app,
            title="Mazda Tuner API",
            description="REST API for Mazda vehicle tuning and diagnostics",
            api_version="1.0.0",
            ui_version=3,
            swagger_url="/api/docs"
        )
    
    # Helper methods
    async def get_current_user(self, request: Request) -> User:
        """Get the current authenticated user from the request."""
        token = self._get_auth_token(request)
        if not token:
            raise AuthError("No authentication token provided")
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthError("Invalid token")
            
            # Check session cache first
            session = self.sessions.get(token)
            if session and not session.is_expired:
                return session
            
            # Get user from database
            user = self.db.get_user_by_id(user_id)
            if not user:
                raise AuthError("User not found")
            
            # Create new session
            expires_at = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
            session = UserSession(
                user_id=user.id,
                username=user.username,
                role=user.role,
                expires_at=expires_at,
                token=token
            )
            
            # Cache the session
            self.sessions[token] = session
            
            return session
            
        except jwt.ExpiredSignatureError:
            raise AuthError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthError(f"Invalid token: {str(e)}")
    
    def _get_auth_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        
        return None
    
    def _create_jwt_token(self, user: User) -> str:
        """Create a JWT token for the user."""
        expires_at = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
        
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "exp": expires_at
        }
        
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def _validate_vehicle_ownership(self, user: UserSession, vehicle_id: int) -> Vehicle:
        """Validate that the user owns the vehicle."""
        if user.role == UserRole.ADMIN:
            vehicle = self.db.get_vehicle(vehicle_id)
        else:
            vehicle = next(
                (v for v in self.db.get_vehicles_by_owner(user.user_id) if v.id == vehicle_id),
                None
            )
        
        if not vehicle:
            raise PermissionDenied("Vehicle not found or access denied")
        
        return vehicle
    
    def _get_connection(self, connection_id: str) -> VehicleConnection:
        """Get an active vehicle connection."""
        connection = self.connections.get(connection_id)
        if not connection:
            raise VehicleConnectionError("No active connection found")
        
        # Update last active time
        connection.last_active = datetime.utcnow()
        
        return connection
    
    # Auth handlers
    async def register(self, request: Request) -> Response:
        """Register a new user."""
        data = await request.json()
        
        # Validate input
        required_fields = ["username", "email", "password", "first_name", "last_name"]
        if not all(field in data for field in required_fields):
            raise ValidationError("Missing required fields")
        
        # Create user
        try:
            user_id = self.db.create_user(
                username=data["username"],
                password=data["password"],
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=UserRole.USER
            )
            
            # Generate JWT token
            user = self.db.get_user_by_id(user_id)
            token = self._create_jwt_token(user)
            
            return json_response({
                "message": "User registered successfully",
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role.value
                }
            })
            
        except Exception as e:
            raise APIError(str(e), 400, "REGISTRATION_FAILED")
    
    async def login(self, request: Request) -> Response:
        """Authenticate a user and return a JWT token."""
        data = await request.json()
        
        # Validate input
        if "username" not in data or "password" not in data:
            raise ValidationError("Username and password are required")
        
        # Authenticate user
        user = self.db.authenticate_user(
            username=data["username"],
            password=data["password"],
            ip_address=request.remote
        )
        
        if not user:
            raise AuthError("Invalid username or password")
        
        # Generate JWT token
        token = self._create_jwt_token(user)
        
        # Create session
        expires_at = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
        session = UserSession(
            user_id=user.id,
            username=user.username,
            role=user.role,
            expires_at=expires_at,
            token=token
        )
        
        # Cache the session
        self.sessions[token] = session
        
        return json_response({
            "token": token,
            "expires_at": expires_at.isoformat(),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value
            }
        })
    
    async def refresh_token(self, request: Request) -> Response:
        """Refresh an authentication token."""
        token = self._get_auth_token(request)
        if not token:
            raise AuthError("No authentication token provided")
        
        try:
            # Verify the token (ignore expiration)
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": False}
            )
            
            # Get user from database
            user_id = payload.get("sub")
            user = self.db.get_user_by_id(user_id)
            
            if not user:
                raise AuthError("User not found")
            
            # Generate new token
            new_token = self._create_jwt_token(user)
            
            # Update session
            expires_at = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
            session = UserSession(
                user_id=user.id,
                username=user.username,
                role=user.role,
                expires_at=expires_at,
                token=new_token
            )
            
            # Update session cache
            if token in self.sessions:
                del self.sessions[token]
            self.sessions[new_token] = session
            
            return json_response({
                "token": new_token,
                "expires_at": expires_at.isoformat()
            })
            
        except jwt.InvalidTokenError as e:
            raise AuthError(f"Invalid token: {str(e)}")
    
    async def logout(self, request: Request) -> Response:
        """Invalidate the current session."""
        token = self._get_auth_token(request)
        if token and token in self.sessions:
            del self.sessions[token]
        
        return json_response({"message": "Logged out successfully"})
    
    # User handlers
    async def get_current_user(self, request: Request) -> Response:
        """Get the current authenticated user's profile."""
        user = await self.get_current_user(request)
        return json_response({
            "id": user.user_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value
        })
    
    async def update_current_user(self, request: Request) -> Response:
        """Update the current user's profile."""
        user = await self.get_current_user(request)
        data = await request.json()
        
        # Only allow updating certain fields
        allowed_fields = ["email", "first_name", "last_name", "password"]
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            raise ValidationError("No valid fields to update")
        
        # Update user
        success = self.db.update_user(user.user_id, **updates)
        if not success:
            raise APIError("Failed to update user profile")
        
        # Get updated user
        updated_user = self.db.get_user_by_id(user.user_id)
        
        return json_response({
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "first_name": updated_user.first_name,
                "last_name": updated_user.last_name,
                "role": updated_user.role.value
            }
        })
    
    # Vehicle handlers
    async def connect_vehicle(self, request: Request) -> Response:
        """Connect to a vehicle."""
        user = await self.get_current_user(request)
        data = await request.json()
        
        # Validate input
        if "vehicle_id" not in data:
            raise ValidationError("Vehicle ID is required")
        
        vehicle_id = data["vehicle_id"]
        
        # Verify vehicle ownership
        vehicle = self._validate_vehicle_ownership(user, vehicle_id)
        
        # Check for existing connection
        existing_conn = next(
            (conn for conn in self.connections.values() 
             if conn.vehicle_id == vehicle_id and not conn.is_expired),
            None
        )
        
        if existing_conn:
            # Return existing connection
            return json_response({
                "connection_id": existing_conn.connection_id,
                "vehicle_id": existing_conn.vehicle_id,
                "status": "connected",
                "since": existing_conn.created_at.isoformat()
            })
        
        # Create new connection
        connection_id = str(uuid.uuid4())
        
        try:
            # Initialize CAN engine
            can_engine = MazdaCANEngine()
            await can_engine.connect()
            
            # Initialize AI tuner
            ai_tuner = RealTimeAITuner(
                feature_configs={
                    # Example feature configurations
                    "rpm": FeatureConfig("rpm", 0, 8000, 3000, 1500),
                    "throttle": FeatureConfig("throttle", 0, 100),
                    "load": FeatureConfig("load", 0, 100)
                },
                output_configs={
                    "ignition_advance": OutputConfig("ignition_advance", 0, 50, 10.0, 0.01),
                    "fuel_pulse_width": OutputConfig("fuel_pulse_width", 1.0, 20.0, 5.0, 0.005)
                }
            )
            
            # Create connection
            connection = VehicleConnection(
                connection_id=connection_id,
                vehicle_id=vehicle_id,
                user_id=user.user_id,
                can_engine=can_engine,
                ai_tuner=ai_tuner
            )
            
            # Store connection
            self.connections[connection_id] = connection
            
            return json_response({
                "connection_id": connection_id,
                "vehicle_id": vehicle_id,
                "status": "connected",
                "since": connection.created_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to connect to vehicle: {e}")
            raise VehicleConnectionError(f"Failed to connect to vehicle: {str(e)}")
    
    async def disconnect_vehicle(self, request: Request) -> Response:
        """Disconnect from a vehicle."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # Find and close connection
        connection = next(
            (conn for conn in self.connections.values() 
             if conn.vehicle_id == vehicle_id and conn.user_id == user.user_id),
            None
        )
        
        if connection:
            await connection.close()
            if connection.connection_id in self.connections:
                del self.connections[connection.connection_id]
            
            return json_response({
                "message": "Vehicle disconnected successfully",
                "vehicle_id": vehicle_id
            })
        else:
            return json_response({
                "message": "No active connection found for this vehicle",
                "vehicle_id": vehicle_id
            }, status=404)
    
    async def list_vehicles(self, request: Request) -> Response:
        """List all vehicles for the current user."""
        user = await self.get_current_user(request)
        
        if user.role == UserRole.ADMIN:
            # Admins can see all vehicles
            vehicles = self.db.get_all_vehicles()
        else:
            # Regular users can only see their own vehicles
            vehicles = self.db.get_vehicles_by_owner(user.user_id)
        
        return json_response([
            {
                "id": v.id,
                "vin": v.vin,
                "make": v.make,
                "model": v.model,
                "year": v.year,
                "engine": v.engine,
                "owner_id": v.owner_id,
                "notes": v.notes,
                "created_at": v.created_at.isoformat(),
                "updated_at": v.updated_at.isoformat()
            }
            for v in vehicles
        ])
    
    async def get_vehicle(self, request: Request) -> Response:
        """Get details for a specific vehicle."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        
        # Verify vehicle ownership
        vehicle = self._validate_vehicle_ownership(user, vehicle_id)
        
        return json_response({
            "id": vehicle.id,
            "vin": vehicle.vin,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "engine": vehicle.engine,
            "owner_id": vehicle.owner_id,
            "notes": vehicle.notes,
            "created_at": vehicle.created_at.isoformat(),
            "updated_at": vehicle.updated_at.isoformat()
        })
    
    async def add_vehicle(self, request: Request) -> Response:
        """Add a new vehicle."""
        user = await self.get_current_user(request)
        data = await request.json()
        
        # Validate required fields
        required_fields = ["vin", "make", "model", "year", "engine"]
        if not all(field in data for field in required_fields):
            raise ValidationError("Missing required fields")
        
        try:
            # Add vehicle
            vehicle_id = self.db.add_vehicle(
                vin=data["vin"],
                make=data["make"],
                model=data["model"],
                year=data["year"],
                engine=data["engine"],
                owner_id=user.user_id,
                notes=data.get("notes", "")
            )
            
            # Get the created vehicle
            vehicle = self.db.get_vehicle(vehicle_id)
            
            return json_response({
                "message": "Vehicle added successfully",
                "vehicle": {
                    "id": vehicle.id,
                    "vin": vehicle.vin,
                    "make": vehicle.make,
                    "model": vehicle.model,
                    "year": vehicle.year,
                    "engine": vehicle.engine,
                    "owner_id": vehicle.owner_id,
                    "notes": vehicle.notes,
                    "created_at": vehicle.created_at.isoformat(),
                    "updated_at": vehicle.updated_at.isoformat()
                }
            }, status=201)
            
        except Exception as e:
            raise APIError(f"Failed to add vehicle: {str(e)}", 400, "ADD_VEHICLE_FAILED")
    
    async def update_vehicle(self, request: Request) -> Response:
        """Update a vehicle's details."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        data = await request.json()
        
        # Verify vehicle ownership
        vehicle = self._validate_vehicle_ownership(user, vehicle_id)
        
        # Only allow updating certain fields
        allowed_fields = ["make", "model", "year", "engine", "notes"]
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            raise ValidationError("No valid fields to update")
        
        # Update vehicle
        success = self.db.update_vehicle(vehicle_id, **updates)
        if not success:
            raise APIError("Failed to update vehicle")
        
        # Get updated vehicle
        updated_vehicle = self.db.get_vehicle(vehicle_id)
        
        return json_response({
            "message": "Vehicle updated successfully",
            "vehicle": {
                "id": updated_vehicle.id,
                "vin": updated_vehicle.vin,
                "make": updated_vehicle.make,
                "model": updated_vehicle.model,
                "year": updated_vehicle.year,
                "engine": updated_vehicle.engine,
                "owner_id": updated_vehicle.owner_id,
                "notes": updated_vehicle.notes,
                "created_at": updated_vehicle.created_at.isoformat(),
                "updated_at": updated_vehicle.updated_at.isoformat()
            }
        })
    
    async def delete_vehicle(self, request: Request) -> Response:
        """Delete a vehicle."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # Delete vehicle
        success = self.db.delete_vehicle(vehicle_id)
        if not success:
            raise APIError("Failed to delete vehicle")
        
        return json_response({
            "message": "Vehicle deleted successfully",
            "vehicle_id": vehicle_id
        })
    
    # Diagnostic handlers
    async def scan_diagnostics(self, request: Request) -> Response:
        """Perform a diagnostic scan on a vehicle."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # Get active connection
        connection = next(
            (conn for conn in self.connections.values() 
             if conn.vehicle_id == vehicle_id and conn.user_id == user.user_id),
            None
        )
        
        if not connection or not connection.can_engine:
            raise VehicleConnectionError("No active connection to the vehicle")
        
        try:
            # Perform diagnostic scan
            # This is a simplified example - in a real implementation, you would
            # interact with the CAN bus to read diagnostic trouble codes (DTCs)
            dtcs = await connection.can_engine.read_dtc()
            
            # Log the diagnostic scan
            session_id = await self._create_diagnostic_session(vehicle_id, user.user_id)
            
            # Log each DTC
            for dtc in dtcs:
                await self._log_diagnostic(
                    session_id=session_id,
                    code=dtc.code,
                    description=dtc.description,
                    severity=dtc.severity,
                    data={"status": dtc.status}
                )
            
            return json_response({
                "status": "completed",
                "dtcs_found": len(dtcs),
                "dtcs": [{"code": dtc.code, "description": dtc.description} for dtc in dtcs],
                "session_id": session_id
            })
            
        except Exception as e:
            logger.error(f"Diagnostic scan failed: {e}")
            raise APIError(f"Diagnostic scan failed: {str(e)}", 500, "DIAGNOSTIC_SCAN_FAILED")
    
    async def clear_diagnostics(self, request: Request) -> Response:
        """Clear diagnostic trouble codes for a vehicle."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # Get active connection
        connection = next(
            (conn for conn in self.connections.values() 
             if conn.vehicle_id == vehicle_id and conn.user_id == user.user_id),
            None
        )
        
        if not connection or not connection.can_engine:
            raise VehicleConnectionError("No active connection to the vehicle")
        
        try:
            # Clear DTCs
            await connection.can_engine.clear_dtc()
            
            # Log the action
            self.db.log_security_event(
                user_id=user.user_id,
                event_type="diagnostic_clear",
                description=f"Cleared DTCs for vehicle {vehicle_id}",
                ip_address=request.remote
            )
            
            return json_response({
                "status": "completed",
                "message": "Diagnostic trouble codes cleared successfully"
            })
            
        except Exception as e:
            logger.error(f"Failed to clear DTCs: {e}")
            raise APIError(f"Failed to clear DTCs: {str(e)}", 500, "CLEAR_DTC_FAILED")
    
    async def get_diagnostic_logs(self, request: Request) -> Response:
        """Get diagnostic logs for a vehicle."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # Get query parameters
        limit = int(request.query.get("limit", 100))
        offset = int(request.query.get("offset", 0))
        severity = request.query.get("severity")
        
        # Get diagnostic logs
        logs = self.db.get_diagnostic_logs(
            vehicle_id=vehicle_id,
            limit=limit,
            offset=offset,
            severity=severity
        )
        
        return json_response([
            {
                "id": log.id,
                "session_id": log.session_id,
                "timestamp": log.timestamp.isoformat(),
                "code": log.code,
                "description": log.description,
                "severity": log.severity.value,
                "data": log.data
            }
            for log in logs
        ])
    
    # Tuning handlers
    async def generate_tune(self, request: Request) -> Response:
        """Generate a base tune for a vehicle."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        data = await request.json()
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # Get active connection
        connection = next(
            (conn for conn in self.connections.values() 
             if conn.vehicle_id == vehicle_id and conn.user_id == user.user_id),
            None
        )
        
        if not connection or not connection.can_engine:
            raise VehicleConnectionError("No active connection to the vehicle")
        
        try:
            # Get current vehicle parameters
            vehicle_params = await connection.can_engine.read_parameters(["rpm", "load", "ignition_timing"])
            
            # Generate a base tune using the AI tuner
            if not connection.ai_tuner:
                raise TuningError("AI tuner not initialized")
            
            # Create a tuning session
            session_id = self.db.create_tune_session(
                vehicle_id=vehicle_id,
                tuner_id=user.user_id,
                description=data.get("description", "Base tune generation"),
                config={
                    "type": "base_tune",
                    "parameters": vehicle_params,
                    "options": data.get("options", {})
                }
            )
            
            # Generate the tune (simplified example)
            tune_data = {
                "ignition": {
                    "advance": vehicle_params.get("ignition_timing", 10.0),
                    "redline": 7000,
                    "rev_limit": 7500
                },
                "fuel": {
                    "afr_target": 14.7,
                    "cold_start_enrichment": 1.2,
                    "warmup_enrichment": 1.1
                },
                "boost": {
                    "target": 0,  # No boost for NA engines
                    "limit": 0,
                    "control": "disabled"
                },
                "launch_control": {
                    "enabled": False,
                    "rpm_limit": 4000
                },
                "flat_shift": {
                    "enabled": False,
                    "rpm_limit": 7000
                },
                "traction_control": {
                    "enabled": False,
                    "sensitivity": 0.5
                }
            }
            
            # Save the generated tune
            tune_id = self._save_tune(
                session_id=session_id,
                name=data.get("name", f"Base Tune {datetime.now().strftime('%Y%m%d')}"),
                description=data.get("description", "Automatically generated base tune"),
                parameters=tune_data,
                is_base_tune=True
            )
            
            return json_response({
                "status": "completed",
                "message": "Base tune generated successfully",
                "tune_id": tune_id,
                "session_id": session_id,
                "tune": tune_data
            })
            
        except Exception as e:
            logger.error(f"Tune generation failed: {e}")
            raise TuningError(f"Failed to generate tune: {str(e)}")
    
    async def optimize_tune(self, request: Request) -> Response:
        """Optimize a tune using AI."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        data = await request.json()
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # Get active connection
        connection = next(
            (conn for conn in self.connections.values() 
             if conn.vehicle_id == vehicle_id and conn.user_id == user.user_id),
            None
        )
        
        if not connection or not connection.can_engine or not connection.ai_tuner:
            raise VehicleConnectionError("No active connection to the vehicle or AI tuner not available")
        
        try:
            # Get the base tune to optimize
            base_tune_id = data.get("base_tune_id")
            if not base_tune_id:
                raise ValidationError("base_tune_id is required")
            
            # In a real implementation, you would load the base tune and optimize it
            # This is a simplified example
            
            # Create a tuning session
            session_id = self.db.create_tune_session(
                vehicle_id=vehicle_id,
                tuner_id=user.user_id,
                description=data.get("description", "AI Tune Optimization"),
                config={
                    "type": "ai_optimization",
                    "base_tune_id": base_tune_id,
                    "optimization_goals": data.get("goals", ["power", "fuel_efficiency"]),
                    "constraints": data.get("constraints", {"safety_margin": 0.9})
                }
            )
            
            # Start optimization in the background
            asyncio.create_task(self._run_optimization(
                connection=connection,
                session_id=session_id,
                base_tune_id=base_tune_id,
                goals=data.get("goals", ["power", "fuel_efficiency"]),
                constraints=data.get("constraints", {"safety_margin": 0.9})
            ))
            
            return json_response({
                "status": "optimization_started",
                "message": "Tune optimization started in the background",
                "session_id": session_id
            })
            
        except Exception as e:
            logger.error(f"Tune optimization failed: {e}")
            raise TuningError(f"Failed to optimize tune: {str(e)}")
    
    async def flash_tune(self, request: Request) -> Response:
        """Flash a tune to the vehicle's ECU."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        data = await request.json()
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # Get active connection
        connection = next(
            (conn for conn in self.connections.values() 
             if conn.vehicle_id == vehicle_id and conn.user_id == user.user_id),
            None
        )
        
        if not connection or not connection.can_engine:
            raise VehicleConnectionError("No active connection to the vehicle")
        
        try:
            # Get the tune to flash
            tune_id = data.get("tune_id")
            if not tune_id:
                raise ValidationError("tune_id is required")
            
            # In a real implementation, you would:
            # 1. Verify the tune is compatible with the vehicle
            # 2. Put the ECU in programming mode
            # 3. Flash the tune in blocks with verification
            # 4. Reset the ECU and verify the flash
            
            # This is a simplified example
            tune = self._load_tune(tune_id)
            if not tune:
                raise TuningError("Tune not found")
            
            # Log the flash operation
            self.db.log_security_event(
                user_id=user.user_id,
                event_type="tune_flash",
                description=f"Flashed tune {tune_id} to vehicle {vehicle_id}",
                ip_address=request.remote,
                details={"tune_id": tune_id}
            )
            
            return json_response({
                "status": "completed",
                "message": "Tune flashed successfully",
                "tune_id": tune_id
            })
            
        except Exception as e:
            logger.error(f"Tune flash failed: {e}")
            raise TuningError(f"Failed to flash tune: {str(e)}")
    
    async def list_tunes(self, request: Request) -> Response:
        """List all tunes for a vehicle."""
        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # In a real implementation, you would query the database for tunes
        # This is a simplified example
        tunes = self._get_vehicle_tunes(vehicle_id)
        
        return json_response([
            {
                "id": tune["id"],
                "name": tune["name"],
                "description": tune["description"],
                "created_at": tune["created_at"].isoformat(),
                "is_base_tune": tune.get("is_base_tune", False),
                "session_id": tune.get("session_id")
            }
            for tune in tunes
        ])
    
    async def get_tune(self, request: Request) -> Response:
        """Get details for a specific tune."""
        user = await self.get_current_user(request)
        tune_id = request.match_info["tune_id"]
        
        # Get the tune
        tune = self._load_tune(tune_id)
        if not tune:
            raise APIError("Tune not found", 404, "TUNE_NOT_FOUND")
        
        # Verify the user has access to this tune
        if tune["user_id"] != user.user_id and user.role != UserRole.ADMIN:
            raise PermissionDenied("You don't have permission to access this tune")
        
        return json_response(tune)
    
    # Real-time data streaming
    async def data_stream(self, request: Request) -> Response:
        """Stream real-time data from the vehicle."""n        user = await self.get_current_user(request)
        vehicle_id = int(request.match_info["vehicle_id"])
        
        # Verify vehicle ownership
        self._validate_vehicle_ownership(user, vehicle_id)
        
        # Get active connection
        connection = next(
            (conn for conn in self.connections.values() 
             if conn.vehicle_id == vehicle_id and conn.user_id == user.user_id),
            None
        )
        
        if not connection or not connection.can_engine:
            raise VehicleConnectionError("No active connection to the vehicle")
        
        # Set up server-sent events (SSE) response
        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive'}
        )
        
        # Enable chunked encoding for streaming
        await response.prepare(request)
        
        # Get requested parameters (comma-separated list)
        params = request.query.get("params", "")
        if params:
            params = [p.strip() for p in params.split(",") if p.strip()]
        
        # Default parameters if none specified
        if not params:
            params = ["rpm", "speed", "throttle", "load", "ignition_timing", "afr"]
        
        try:
            while True:
                # Read parameters from the vehicle
                values = await connection.can_engine.read_parameters(params)
                
                # Add timestamp
                values["timestamp"] = datetime.utcnow().isoformat()
                
                # Send the data as an SSE event
                data = json.dumps(values)
                await response.write(f"data: {data}\n\n".encode('utf-8'))
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            # Client disconnected
            pass
        except Exception as e:
            logger.error(f"Data stream error: {e}")
        finally:
            try:
                await response.write_eof()
            except Exception:
                pass
        
        return response
    
    # WebSocket handler
    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """WebSocket endpoint for real-time communication."""
        # Authenticate the user
        try:
            user = await self.get_current_user(request)
        except Exception as e:
            # Close the connection if authentication fails
            ws = WebSocketResponse()
            await ws.prepare(request)
            await ws.close(code=4001, message=b'Authentication failed')
            return ws
        
        # Get the connection ID from query parameters
        connection_id = request.query.get("connection_id")
        if not connection_id:
            ws = WebSocketResponse()
            await ws.prepare(request)
            await ws.close(code=4000, message=b'Missing connection_id')
            return ws
        
        # Get the vehicle connection
        connection = self.connections.get(connection_id)
        if not connection or connection.user_id != user.user_id:
            ws = WebSocketResponse()
            await ws.prepare(request)
            await ws.close(code=4002, message=b'Invalid connection_id')
            return ws
        
        # Create WebSocket connection
        ws = WebSocketResponse(heartbeat=WS_HEARTBEAT, timeout=WS_TIMEOUT)
        await ws.prepare(request)
        
        # Add to connection's WebSocket list
        connection.websockets.append(ws)
        
        try:
            # Send initial connection info
            await ws.send_json({
                "type": "connection_established",
                "connection_id": connection_id,
                "vehicle_id": connection.vehicle_id,
                "user_id": user.user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Handle incoming messages
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = msg.json()
                        await self._handle_websocket_message(ws, connection, user, data)
                    except json.JSONDecodeError:
                        await ws.send_json({
                            "type": "error",
                            "message": "Invalid JSON"
                        })
                    except Exception as e:
                        logger.error(f"WebSocket message handling error: {e}")
                        await ws.send_json({
                            "type": "error",
                            "message": str(e)
                        })
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket connection error: {ws.exception()}")
        
        except asyncio.CancelledError:
            # Client disconnected
            pass
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up
            if ws in connection.websockets:
                connection.websockets.remove(ws)
            await ws.close()
        
        return ws
    
    async def _handle_websocket_message(
        self, 
        ws: WebSocketResponse, 
        connection: VehicleConnection, 
        user: UserSession, 
        data: Dict[str, Any]
    ) -> None:
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")
        
        if msg_type == "subscribe":
            # Subscribe to parameter updates
            params = data.get("params", [])
            if not isinstance(params, list):
                await ws.send_json({
                    "type": "error",
                    "message": "Params must be an array"
                })
                return
            
            # Start a task to send parameter updates
            asyncio.create_task(self._send_parameter_updates(ws, connection, params))
            
        elif msg_type == "command":
            # Handle command message
            command = data.get("command")
            args = data.get("args", {})
            
            if command == "start_logging":
                # Start data logging
                await self._handle_start_logging(ws, connection, user, args)
                
            elif command == "stop_logging":
                # Stop data logging
                await self._handle_stop_logging(ws, connection, user, args)
                
            elif command == "get_status":
                # Get connection status
                await self._handle_get_status(ws, connection, user)
                
            else:
                await ws.send_json({
                    "type": "error",
                    "message": f"Unknown command: {command}"
                })
        
        else:
            await ws.send_json({
                "type": "error",
                "message": f"Unknown message type: {msg_type}"
            })
    
    async def _send_parameter_updates(
        self, 
        ws: WebSocketResponse, 
        connection: VehicleConnection, 
        params: List[str]
    ) -> None:
        """Send parameter updates over WebSocket."""
        try:
            while not ws.closed:
                if not connection.can_engine:
                    await ws.send_json({
                        "type": "error",
                        "message": "Not connected to vehicle"
                    })
                    break
                
                # Read parameters
                try:
                    values = await connection.can_engine.read_parameters(params)
                    
                    # Send update
                    await ws.send_json({
                        "type": "parameter_update",
                        "timestamp": datetime.utcnow().isoformat(),
                        "values": values
                    })
                except Exception as e:
                    logger.error(f"Error reading parameters: {e}")
                    await ws.send_json({
                        "type": "error",
                        "message": f"Error reading parameters: {str(e)}"
                    })
                    break
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            # Task was cancelled
            pass
        except Exception as e:
            logger.error(f"Parameter update task error: {e}")
    
    async def _handle_start_logging(
        self, 
        ws: WebSocketResponse, 
        connection: VehicleConnection, 
        user: UserSession, 
        args: Dict[str, Any]
    ) -> None:
        """Handle start logging command."""
        # In a real implementation, you would start logging data to a file
        # and return a log ID that can be used to stop logging later
        log_id = str(uuid.uuid4())
        
        await ws.send_json({
            "type": "logging_started",
            "log_id": log_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def _handle_stop_logging(
        self, 
        ws: WebSocketResponse, 
        connection: VehicleConnection, 
        user: UserSession, 
        args: Dict[str, Any]
    ) -> None:
        """Handle stop logging command."""
        log_id = args.get("log_id")
        if not log_id:
            await ws.send_json({
                "type": "error",
                "message": "Missing log_id"
            })
            return
        
        # In a real implementation, you would stop the logging task
        # and process the log file
        
        await ws.send_json({
            "type": "logging_stopped",
            "log_id": log_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Logging stopped successfully"
        })
    
    async def _handle_get_status(
        self, 
        ws: WebSocketResponse, 
        connection: VehicleConnection, 
        user: UserSession
    ) -> None:
        """Handle get status command."""
        status = {
            "connection_id": connection.connection_id,
            "vehicle_id": connection.vehicle_id,
            "user_id": user.user_id,
            "connected": connection.can_engine is not None,
            "last_active": connection.last_active.isoformat(),
            "websocket_clients": len(connection.websockets)
        }
        
        if connection.can_engine:
            status.update({
                "vehicle_info": await connection.can_engine.get_vehicle_info(),
                "connection_status": await connection.can_engine.get_connection_status()
            })
        
        await ws.send_json({
            "type": "status_update",
            "timestamp": datetime.utcnow().isoformat(),
            "status": status
        })
    
    # Helper methods for tune management
    def _save_tune(
        self, 
        session_id: int, 
        name: str, 
        description: str, 
        parameters: Dict[str, Any],
        is_base_tune: bool = False
    ) -> str:
        """Save a tune to the database."""
        # In a real implementation, you would save the tune to the database
        # This is a simplified example
        tune_id = str(uuid.uuid4())
        tune = {
            "id": tune_id,
            "session_id": session_id,
            "name": name,
            "description": description,
            "parameters": parameters,
            "is_base_tune": is_base_tune,
            "created_at": datetime.utcnow()
        }
        
        # Save to database (simplified)
        # self.db.save_tune(tune)
        
        return tune_id
    
    def _load_tune(self, tune_id: str) -> Optional[Dict[str, Any]]:
        """Load a tune from the database."""
        # In a real implementation, you would load the tune from the database
        # This is a simplified example
        return None
    
    def _get_vehicle_tunes(self, vehicle_id: int) -> List[Dict[str, Any]]:
        """Get all tunes for a vehicle."""
        # In a real implementation, you would query the database
        # This is a simplified example
        return []
    
    # Background tasks
    def _setup_cleanup_tasks(self):
        """Set up background cleanup tasks."""
        # Clean up expired sessions and connections periodically
        async def cleanup():
            while True:
                try:
                    await self._cleanup_expired_sessions()
                    await self._cleanup_inactive_connections()
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")
                
                # Run every 5 minutes
                await asyncio.sleep(300)
        
        # Start the cleanup task
        asyncio.create_task(cleanup())
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired user sessions."""
        now = datetime.utcnow()
        expired = [token for token, session in self.sessions.items() 
                  if session.is_expired]
        
        for token in expired:
            del self.sessions[token]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    async def _cleanup_inactive_connections(self):
        """Clean up inactive vehicle connections."""
        now = datetime.utcnow()
        inactive = []
        
        for conn_id, conn in list(self.connections.items()):
            # Close connections inactive for more than 1 hour
            if (now - conn.last_active).total_seconds() > 3600:
                inactive.append(conn_id)
        
        for conn_id in inactive:
            conn = self.connections.pop(conn_id, None)
            if conn:
                await conn.close()
        
        if inactive:
            logger.info(f"Closed {len(inactive)} inactive connections")
    
    # Background tasks for tune optimization
    async def _run_optimization(
        self, 
        connection: VehicleConnection, 
        session_id: int, 
        base_tune_id: str,
        goals: List[str],
        constraints: Dict[str, Any]
    ) -> None:
        """Run tune optimization in the background."""
        try:
            # Load the base tune
            base_tune = self._load_tune(base_tune_id)
            if not base_tune:
                raise TuningError("Base tune not found")
            
            # Notify optimization started
            await self._notify_optimization_update(
                connection, 
                session_id, 
                "optimization_started",
                {"message": "Optimization started", "progress": 0}
            )
            
            # Simulate optimization process
            # In a real implementation, this would involve:
            # 1. Reading current vehicle parameters
            # 2. Running optimization algorithms
            # 3. Testing different parameter combinations
            # 4. Validating results against constraints
            
            for i in range(1, 11):
                # Simulate progress
                progress = i * 10
                await asyncio.sleep(2)  # Simulate work
                
                # Send progress update
                await self._notify_optimization_update(
                    connection,
                    session_id,
                    "optimization_progress",
                    {
                        "message": f"Running optimization ({progress}% complete)",
                        "progress": progress,
                        "metrics": {
                            "power": 180 + i * 2,
                            "torque": 160 + i * 1.5,
                            "fuel_efficiency": 25 + i * 0.3
                        }
                    }
                )
            
            # Generate optimized tune
            optimized_tune = {
                **base_tune["parameters"],
                "optimization": {
                    "goals": goals,
                    "constraints": constraints,
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
            
            # Save the optimized tune
            tune_id = self._save_tune(
                session_id=session_id,
                name=f"Optimized Tune {datetime.now().strftime('%Y%m%d')}",
                description=f"AI-optimized tune based on {base_tune.get('name', 'base tune')}",
                parameters=optimized_tune,
                is_base_tune=False
            )
            
            # Send completion notification
            await self._notify_optimization_update(
                connection,
                session_id,
                "optimization_completed",
                {
                    "message": "Optimization completed successfully",
                    "progress": 100,
                    "tune_id": tune_id,
                    "metrics": {
                        "power": 200,
                        "torque": 175,
                        "fuel_efficiency": 28
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            
            # Send error notification
            await self._notify_optimization_update(
                connection,
                session_id,
                "optimization_failed",
                {
                    "message": f"Optimization failed: {str(e)}",
                    "error": str(e)
                }
            )
    
    async def _notify_optimization_update(
        self, 
        connection: VehicleConnection, 
        session_id: int, 
        update_type: str, 
        data: Dict[str, Any]
    ) -> None:
        """Send optimization update to all connected WebSocket clients."""
        message = {
            "type": "optimization_update",
            "update_type": update_type,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Send to all WebSocket clients
        for ws in connection.websockets:
            try:
                if not ws.closed:
                    await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
    
    # Diagnostic helpers
    async def _create_diagnostic_session(
        self, 
        vehicle_id: int, 
        user_id: int, 
        description: str = "Diagnostic scan"
    ) -> int:
        """Create a diagnostic session."""
        return self.db.create_tune_session(
            vehicle_id=vehicle_id,
            tuner_id=user_id,
            description=description,
            config={"type": "diagnostic"}
        )
    
    async def _log_diagnostic(
        self, 
        session_id: int, 
        code: str, 
        description: str, 
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a diagnostic event."""
        self.db.log_diagnostic(
            session_id=session_id,
            code=code,
            description=description,
            severity=severity,
            data=data or {}
        )
    
    # Frontend serving
    async def serve_frontend(self, request: Request) -> Response:
        """Serve the frontend application."""
        # In a real implementation, you would serve your frontend files here
        # This is a simplified example that returns a basic HTML page
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mazda Tuner</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px;
                    text-align: center;
                }
                .container { 
                    margin-top: 50px; 
                }
                .btn {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px;
                }
                .btn:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Mazda Tuner API</h1>
                <p>Welcome to the Mazda Tuner API server.</p>
                <div>
                    <a href="/api/docs" class="btn">API Documentation</a>
                </div>
                <p style="margin-top: 50px;">
                    <small>Mazda Tuner &copy; 2023 - All rights reserved</small>
                </p>
            </div>
        </body>
        </html>
        """
        
        return web.Response(text=html, content_type="text/html")
    
    # Server control
    async def start(self):
        """Start the API server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f"Server started at http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the API server."""
        # Close all vehicle connections
        for conn in self.connections.values():
            await conn.close()
        
        # Stop the web server
        if self.runner:
            await self.runner.cleanup()
        
        # Close the database connection
        self.db.close()
        
        logger.info("Server stopped")

async def main():
    """Main entry point for the application."""
    # Create and start the API server
    api = MazdaTunerAPI(host="0.0.0.0", port=8080)
    
    try:
        await api.start()
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
            
    except asyncio.CancelledError:
        # Handle graceful shutdown
        await api.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await api.stop()
        raise

if __name__ == "__main__":
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
