"""
MazdaTunerAPI - FastAPI web interface for the Mazdaspeed 3 tuning suite.
Provides REST endpoints for telemetry, AI tuning, ECU operations, and session management.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from models import (
    TelemetryData, TuningParameter, TuningProfile, TuningMode,
    SecurityLevel, SecurityCredentials, FlashOperation, FlashState,
    VehicleState, ECUState, DiagnosticTroubleCode
)
from real_time_telemetry import RealTimeTelemetry, TelemetryConfig
from real_time_ai_tuner import RealTimeAITuner, TuningTarget
from real_time_tuning_session import RealTimeTuningSession, SessionConfig
from mazda_ecu_exploiter import MazdaECUExploiter
from secure_database import SecureDatabase
from mazda_security_core import MazdaSecurityCore


# Pydantic models for API requests/responses
class TelemetryResponse(BaseModel):
    """Telemetry data response model."""
    timestamp: float
    rpm: Optional[float] = None
    vehicle_speed: Optional[float] = None
    throttle_position: Optional[float] = None
    pedal_position: Optional[float] = None
    boost_pressure: Optional[float] = None
    map: Optional[float] = None
    maf: Optional[float] = None
    ect: Optional[float] = None
    iat: Optional[float] = None
    oil_pressure: Optional[float] = None
    fuel_pressure: Optional[float] = None
    stft: Optional[float] = None
    ltft: Optional[float] = None
    afr: Optional[float] = None
    timing_advance: Optional[float] = None
    load: Optional[float] = None
    knock_retard: Optional[float] = None
    gear: Optional[int] = None


class TuningTargetRequest(BaseModel):
    """Tuning target request model."""
    target_power: float = Field(default=0.0, description="Target horsepower")
    target_torque: float = Field(default=0.0, description="Target torque")
    target_boost: float = Field(default=0.0, description="Target boost pressure")
    target_afr: float = Field(default=14.7, description="Target air-fuel ratio")
    efficiency_weight: float = Field(default=0.5, description="Efficiency vs power weight")
    safety_margin: float = Field(default=0.1, description="Safety margin")


class SessionStartRequest(BaseModel):
    """Session start request model."""
    tuning_target: Optional[TuningTargetRequest] = None
    enable_auto_rollback: bool = Field(default=True, description="Enable automatic rollback")
    safety_checks_enabled: bool = Field(default=True, description="Enable safety checks")


class SessionResponse(BaseModel):
    """Session response model."""
    session_id: str
    state: str
    current_phase: str
    phases_completed: List[str]
    session_duration: float
    phase_duration: float
    safety_violations: int
    rollback_available: bool


class APIResponse(BaseModel):
    """Generic API response model."""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: float = Field(default_factory=time.time)


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: str
    timestamp: float = Field(default_factory=time.time)


class MazdaTunerAPI:
    """
    FastAPI web interface for the Mazdaspeed 3 tuning suite.
    Provides REST endpoints for all tuning operations.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Initialize the API server.
        
        Args:
            host: Host address
            port: Port number
        """
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # FastAPI app
        self.app = FastAPI(
            title="Mazda Tuner API",
            description="REST API for 2011 Mazdaspeed 3 tuning suite",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Security
        self.security = HTTPBearer()
        self.security_core = MazdaSecurityCore()
        
        # Component interfaces
        self.telemetry: Optional[RealTimeTelemetry] = None
        self.ai_tuner: Optional[RealTimeAITuner] = None
        self.ecu_exploiter: Optional[MazdaECUExploiter] = None
        self.database: Optional[SecureDatabase] = None
        
        # Active sessions
        self.active_sessions: Dict[str, RealTimeTuningSession] = {}
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
        
        self.logger.info(f"MazdaTunerAPI initialized on {host}:{port}")
    
    def _setup_middleware(self) -> None:
        """Setup FastAPI middleware."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self) -> None:
        """Setup API routes."""
        
        # Health check
        @self.app.get("/health", response_model=APIResponse)
        async def health_check():
            """Health check endpoint."""
            return APIResponse(
                success=True,
                message="Mazda Tuner API is running",
                data={"version": "1.0.0", "timestamp": time.time()}
            )
        
        # Authentication
        @self.app.post("/auth/login", response_model=APIResponse)
        async def login(username: str, password: str):
            """User authentication."""
            try:
                # Validate credentials
                credentials = SecurityCredentials(
                    username=username,
                    password_hash="",  # Will be validated by security core
                    security_level=SecurityLevel.USER,
                    permissions=["read", "write"]
                )
                
                # Authenticate user
                auth_result = await self.security_core.authenticate_user(username, password)
                
                if auth_result:
                    # Create session token
                    session_token = self.security_core.create_session_token(credentials)
                    
                    return APIResponse(
                        success=True,
                        message="Authentication successful",
                        data={
                            "token": session_token,
                            "user": username,
                            "permissions": credentials.permissions
                        }
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid credentials"
                    )
                    
            except Exception as e:
                self.logger.error(f"Authentication error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed"
                )
        
        # Telemetry endpoints
        @self.app.get("/telemetry/latest", response_model=TelemetryResponse)
        async def get_latest_telemetry(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get latest telemetry data."""
            await self._validate_token(credentials.credentials)
            
            if not self.telemetry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Telemetry system not available"
                )
            
            try:
                telemetry = self.telemetry.get_latest_telemetry()
                return TelemetryResponse(**telemetry.__dict__)
                
            except Exception as e:
                self.logger.error(f"Failed to get telemetry: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve telemetry data"
                )
        
        @self.app.get("/telemetry/history", response_model=List[TelemetryResponse])
        async def get_telemetry_history(
            count: int = 100,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get telemetry history."""
            await self._validate_token(credentials.credentials)
            
            if not self.telemetry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Telemetry system not available"
                )
            
            try:
                history = self.telemetry.get_telemetry_history(count)
                return [TelemetryResponse(**t.__dict__) for t in history]
                
            except Exception as e:
                self.logger.error(f"Failed to get telemetry history: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve telemetry history"
                )
        
        @self.app.post("/telemetry/start", response_model=APIResponse)
        async def start_telemetry(
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Start telemetry collection."""
            await self._validate_token(credentials.credentials)
            
            if not self.telemetry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Telemetry system not available"
                )
            
            try:
                session_id = f"api_session_{int(time.time())}"
                success = await self.telemetry.start_collection(session_id)
                
                if success:
                    return APIResponse(
                        success=True,
                        message="Telemetry collection started",
                        data={"session_id": session_id}
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to start telemetry collection"
                    )
                    
            except Exception as e:
                self.logger.error(f"Failed to start telemetry: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to start telemetry collection"
                )
        
        @self.app.post("/telemetry/stop", response_model=APIResponse)
        async def stop_telemetry(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Stop telemetry collection."""
            await self._validate_token(credentials.credentials)
            
            if not self.telemetry:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Telemetry system not available"
                )
            
            try:
                success = await self.telemetry.stop_collection()
                
                if success:
                    return APIResponse(
                        success=True,
                        message="Telemetry collection stopped"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to stop telemetry collection"
                    )
                    
            except Exception as e:
                self.logger.error(f"Failed to stop telemetry: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to stop telemetry collection"
                )
        
        # AI Tuning endpoints
        @self.app.post("/ai/optimize", response_model=APIResponse)
        async def optimize_tuning(
            target: TuningTargetRequest,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get AI tuning optimization."""
            await self._validate_token(credentials.credentials)
            
            if not self.ai_tuner:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI tuner not available"
                )
            
            try:
                # Convert request to TuningTarget
                tuning_target = TuningTarget(
                    target_power=target.target_power,
                    target_torque=target.target_torque,
                    target_boost=target.target_boost,
                    target_afr=target.target_afr,
                    efficiency_weight=target.efficiency_weight,
                    safety_margin=target.safety_margin
                )
                
                # Get current telemetry
                current_telemetry = self.telemetry.get_latest_telemetry()
                
                # Optimize parameters
                optimization_result = await self.ai_tuner.optimize_for_target(tuning_target)
                
                return APIResponse(
                    success=True,
                    message="Optimization completed",
                    data=optimization_result
                )
                
            except Exception as e:
                self.logger.error(f"AI optimization failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AI optimization failed"
                )
        
        @self.app.post("/ai/start-learning", response_model=APIResponse)
        async def start_ai_learning(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Start AI learning mode."""
            await self._validate_token(credentials.credentials)
            
            if not self.ai_tuner:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI tuner not available"
                )
            
            try:
                success = await self.ai_tuner.start_learning()
                
                if success:
                    return APIResponse(
                        success=True,
                        message="AI learning started"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to start AI learning"
                    )
                    
            except Exception as e:
                self.logger.error(f"Failed to start AI learning: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to start AI learning"
                )
        
        @self.app.get("/ai/models", response_model=APIResponse)
        async def get_model_info(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get AI model information."""
            await self._validate_token(credentials.credentials)
            
            if not self.ai_tuner:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI tuner not available"
                )
            
            try:
                model_info = self.ai_tuner.get_model_info()
                return APIResponse(
                    success=True,
                    message="Model information retrieved",
                    data=model_info
                )
                
            except Exception as e:
                self.logger.error(f"Failed to get model info: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve model information"
                )
        
        # ECU Operations endpoints
        @self.app.get("/ecu/status", response_model=APIResponse)
        async def get_ecu_status(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get ECU status."""
            await self._validate_token(credentials.credentials)
            
            if not self.ecu_exploiter:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ECU exploiter not available"
                )
            
            try:
                ecu_status = self.ecu_exploiter.get_ecu_status()
                return APIResponse(
                    success=True,
                    message="ECU status retrieved",
                    data=ecu_status
                )
                
            except Exception as e:
                self.logger.error(f"Failed to get ECU status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve ECU status"
                )
        
        @self.app.post("/ecu/backup", response_model=APIResponse)
        async def backup_ecu(
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Create ECU backup."""
            await self._validate_token(credentials.credentials)
            
            if not self.ecu_exploiter:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ECU exploiter not available"
                )
            
            try:
                backup_result = await self.ecu_exploiter.backup_ecu()
                
                if backup_result.success:
                    return APIResponse(
                        success=True,
                        message="ECU backup created",
                        data=backup_result.data
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"ECU backup failed: {backup_result.error_message}"
                    )
                    
            except Exception as e:
                self.logger.error(f"Failed to backup ECU: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create ECU backup"
                )
        
        @self.app.get("/ecu/dtc", response_model=APIResponse)
        async def get_dtc_codes(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get diagnostic trouble codes."""
            await self._validate_token(credentials.credentials)
            
            if not self.ecu_exploiter:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ECU exploiter not available"
                )
            
            try:
                dtc_codes = await self.ecu_exploiter.read_dtcs()
                return APIResponse(
                    success=True,
                    message="DTC codes retrieved",
                    data=[dtc.__dict__ for dtc in dtc_codes]
                )
                
            except Exception as e:
                self.logger.error(f"Failed to get DTC codes: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve DTC codes"
                )
        
        # Tuning Session endpoints
        @self.app.post("/session/start", response_model=APIResponse)
        async def start_tuning_session(
            request: SessionStartRequest,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Start a new tuning session."""
            await self._validate_token(credentials.credentials)
            
            try:
                # Generate session ID
                session_id = f"session_{int(time.time())}"
                
                # Create session config
                session_config = SessionConfig(
                    enable_auto_rollback=request.enable_auto_rollback,
                    safety_checks_enabled=request.safety_checks_enabled
                )
                
                # Create session
                session = RealTimeTuningSession(session_id, session_config)
                
                # Setup session interfaces
                session.set_telemetry(self.telemetry)
                session.set_ai_tuner(self.ai_tuner)
                session.set_ecu_exploiter(self.ecu_exploiter)
                session.set_database(self.database)
                
                # Convert tuning target
                tuning_target = None
                if request.tuning_target:
                    tuning_target = TuningTarget(
                        target_power=request.tuning_target.target_power,
                        target_torque=request.tuning_target.target_torque,
                        target_boost=request.tuning_target.target_boost,
                        target_afr=request.tuning_target.target_afr,
                        efficiency_weight=request.tuning_target.efficiency_weight,
                        safety_margin=request.tuning_target.safety_margin
                    )
                
                # Start session
                success = await session.start_session(tuning_target)
                
                if success:
                    self.active_sessions[session_id] = session
                    return APIResponse(
                        success=True,
                        message="Tuning session started",
                        data={"session_id": session_id}
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to start tuning session"
                    )
                    
            except Exception as e:
                self.logger.error(f"Failed to start tuning session: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to start tuning session"
                )
        
        @self.app.get("/session/{session_id}/status", response_model=SessionResponse)
        async def get_session_status(
            session_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get session status."""
            await self._validate_token(credentials.credentials)
            
            if session_id not in self.active_sessions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            try:
                session = self.active_sessions[session_id]
                status = session.get_session_status()
                return SessionResponse(**status)
                
            except Exception as e:
                self.logger.error(f"Failed to get session status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve session status"
                )
        
        @self.app.post("/session/{session_id}/run", response_model=APIResponse)
        async def run_full_session(
            session_id: str,
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Run full tuning session."""
            await self._validate_token(credentials.credentials)
            
            if session_id not in self.active_sessions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            try:
                session = self.active_sessions[session_id]
                
                # Run session in background
                background_tasks.add_task(self._run_session_background, session)
                
                return APIResponse(
                    success=True,
                    message="Full session execution started",
                    data={"session_id": session_id}
                )
                
            except Exception as e:
                self.logger.error(f"Failed to run session: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to start session execution"
                )
        
        @self.app.post("/session/{session_id}/abort", response_model=APIResponse)
        async def abort_session(
            session_id: str,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Abort tuning session."""
            await self._validate_token(credentials.credentials)
            
            if session_id not in self.active_sessions:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
            
            try:
                session = self.active_sessions[session_id]
                await session.abort_session()
                
                # Remove from active sessions
                del self.active_sessions[session_id]
                
                return APIResponse(
                    success=True,
                    message="Session aborted"
                )
                
            except Exception as e:
                self.logger.error(f"Failed to abort session: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to abort session"
                )
        
        # Database endpoints
        @self.app.get("/database/stats", response_model=APIResponse)
        async def get_database_stats(
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Get database statistics."""
            await self._validate_token(credentials.credentials)
            
            if not self.database:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database not available"
                )
            
            try:
                stats = self.database.get_database_stats()
                return APIResponse(
                    success=True,
                    message="Database statistics retrieved",
                    data=stats
                )
                
            except Exception as e:
                self.logger.error(f"Failed to get database stats: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve database statistics"
                )
        
        @self.app.get("/database/backup", response_model=APIResponse)
        async def backup_database(
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """Create database backup."""
            await self._validate_token(credentials.credentials)
            
            if not self.database:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database not available"
                )
            
            try:
                # Run backup in background
                background_tasks.add_task(self._backup_database_background)
                
                return APIResponse(
                    success=True,
                    message="Database backup started"
                )
                
            except Exception as e:
                self.logger.error(f"Failed to start database backup: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to start database backup"
                )
    
    async def _validate_token(self, token: str) -> None:
        """Validate authentication token."""
        try:
            # Validate token with security core
            is_valid = self.security_core.validate_session_token(token)
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
                
        except Exception as e:
            self.logger.error(f"Token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )
    
    async def _run_session_background(self, session: RealTimeTuningSession) -> None:
        """Run session in background task."""
        try:
            await session.run_full_session()
            self.logger.info(f"Background session completed: {session.session_id}")
        except Exception as e:
            self.logger.error(f"Background session failed: {e}")
            await session.abort_session()
    
    async def _backup_database_background(self) -> None:
        """Create database backup in background."""
        try:
            success = await self.database.backup_database()
            if success:
                self.logger.info("Database backup completed")
            else:
                self.logger.error("Database backup failed")
        except Exception as e:
            self.logger.error(f"Database backup error: {e}")
    
    def set_telemetry(self, telemetry: RealTimeTelemetry) -> None:
        """Set telemetry interface."""
        self.telemetry = telemetry
        self.logger.info("Telemetry interface set")
    
    def set_ai_tuner(self, ai_tuner: RealTimeAITuner) -> None:
        """Set AI tuner interface."""
        self.ai_tuner = ai_tuner
        self.logger.info("AI tuner interface set")
    
    def set_ecu_exploiter(self, ecu_exploiter: MazdaECUExploiter) -> None:
        """Set ECU exploiter interface."""
        self.ecu_exploiter = ecu_exploiter
        self.logger.info("ECU exploiter interface set")
    
    def set_database(self, database: SecureDatabase) -> None:
        """Set database interface."""
        self.database = database
        self.logger.info("Database interface set")
    
    def run(self) -> None:
        """Start the API server."""
        self.logger.info(f"Starting Mazda Tuner API on {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")
    
    def get_app(self) -> FastAPI:
        """Get FastAPI app instance."""
        return self.app


# Global API instance
_api_instance: Optional[MazdaTunerAPI] = None


def get_api() -> MazdaTunerAPI:
    """Get global API instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = MazdaTunerAPI()
    return _api_instance


def create_app() -> FastAPI:
    """Create FastAPI application."""
    api = get_api()
    return api.get_app()


if __name__ == "__main__":
    # Run API server
    api = get_api()
    api.run()
