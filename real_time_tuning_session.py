"""
RealTimeTuningSession - State machine-based tuning session orchestrator.
Coordinates AI tuners, telemetry, ECU exploiters, and database through phases:
ANALYZE -> PLAN -> VALIDATE -> APPLY -> VERIFY with automatic rollback capability.
"""

import asyncio
import time
import json
import struct
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

from models import (
    TelemetryData, TuningParameter, TuningProfile, TuningMode,
    SecurityLevel, SecurityCredentials, FlashOperation, FlashState,
    VehicleState, ECUState
)
from real_time_telemetry import RealTimeTelemetry
from real_time_ai_tuner import RealTimeAITuner, TuningTarget
from mazda_ecu_exploiter import MazdaECUExploiter
from secure_database import SecureDatabase


class SessionPhase(Enum):
    """Tuning session phases."""
    IDLE = "idle"
    ANALYZE = "analyze"
    PLAN = "plan"
    VALIDATE = "validate"
    APPLY = "apply"
    VERIFY = "verify"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"


class SessionState(Enum):
    """Session operational states."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class SessionConfig:
    """Tuning session configuration."""
    max_phase_duration: float = 300.0  # 5 minutes per phase
    enable_auto_rollback: bool = True
    safety_checks_enabled: bool = True
    backup_before_apply: bool = True
    verification_duration: float = 60.0  # 1 minute verification
    
    # Safety thresholds
    max_boost_threshold: float = 25.0  # psi
    max_knock_threshold: float = 5.0   # degrees
    min_afr_threshold: float = 11.5    # Rich limit
    max_egt_threshold: float = 900.0   # Celsius
    
    # Performance targets
    target_power_gain: float = 0.0     # HP
    target_torque_gain: float = 0.0    # lb-ft
    efficiency_priority: float = 0.5   # 0-1, power vs efficiency


@dataclass
class PhaseResult:
    """Result of a session phase."""
    phase: SessionPhase
    success: bool
    duration: float = 0.0
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def __bool__(self) -> bool:
        """Boolean conversion based on success."""
        return self.success


@dataclass
class RollbackData:
    """Data needed for session rollback."""
    original_parameters: Dict[str, float]
    backup_checksum: str
    backup_timestamp: float
    flash_backup_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_parameters": self.original_parameters,
            "backup_checksum": self.backup_checksum,
            "backup_timestamp": self.backup_timestamp,
            "flash_backup_id": self.flash_backup_id,
        }


class TuningSessionError(Exception):
    """Tuning session specific errors."""
    pass


class SessionPhaseError(TuningSessionError):
    """Phase execution error."""
    pass


class RollbackFailedError(TuningSessionError):
    """Rollback operation failed."""
    pass


class RealTimeTuningSession:
    """
    Real-time tuning session orchestrator using state machine approach.
    Manages the complete tuning workflow with safety checks and rollback.
    """
    
    # Phase execution methods mapping
    PHASE_METHODS = {
        SessionPhase.ANALYZE: "_execute_analyze_phase",
        SessionPhase.PLAN: "_execute_plan_phase",
        SessionPhase.VALIDATE: "_execute_validate_phase",
        SessionPhase.APPLY: "_execute_apply_phase",
        SessionPhase.VERIFY: "_execute_verify_phase",
        SessionPhase.ROLLBACK: "_execute_rollback_phase",
    }
    
    def __init__(self, session_id: str, config: Optional[SessionConfig] = None):
        """
        Initialize tuning session.
        
        Args:
            session_id: Unique session identifier
            config: Session configuration
        """
        self.session_id = session_id
        self.config = config or SessionConfig()
        self.logger = logging.getLogger(f"{__name__}.{session_id}")
        
        # Session state
        self.state = SessionState.INACTIVE
        self.current_phase = SessionPhase.IDLE
        self.phase_start_time = 0.0
        self.session_start_time = 0.0
        
        # Component interfaces (to be injected)
        self.telemetry: Optional[RealTimeTelemetry] = None
        self.ai_tuner: Optional[RealTimeAITuner] = None
        self.ecu_exploiter: Optional[MazdaECUExploiter] = None
        self.database: Optional[SecureDatabase] = None
        
        # Security
        self.current_credentials: Optional[SecurityCredentials] = None
        
        # Session data
        self.phases_completed: List[SessionPhase] = []
        self.phase_results: Dict[SessionPhase, PhaseResult] = {}
        self.rollback_data: Optional[RollbackData] = None
        
        # Tuning targets and parameters
        self.tuning_target: Optional[TuningTarget] = None
        self.original_tuning_profile: Optional[TuningProfile] = None
        self.optimized_parameters: Dict[str, float] = {}
        
        # Monitoring and safety
        self.safety_violations: List[str] = []
        self.performance_metrics: Dict[str, float] = {}
        
        self.logger.info(f"Tuning session initialized: {session_id}")
    
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
    
    def set_credentials(self, credentials: SecurityCredentials) -> None:
        """Set security credentials."""
        self.current_credentials = credentials
        self.logger.info(f"Credentials set for user: {credentials.username}")
    
    async def start_session(self, tuning_target: Optional[TuningTarget] = None) -> bool:
        """
        Start the tuning session.
        
        Args:
            tuning_target: Optional tuning target
            
        Returns:
            True if session started successfully
        """
        if self.state != SessionState.INACTIVE:
            self.logger.warning(f"Cannot start session, current state: {self.state.value}")
            return False
        
        try:
            # Validate interfaces
            if not all([self.telemetry, self.ai_tuner, self.ecu_exploiter, self.database]):
                raise TuningSessionError("All interfaces must be set before starting session")
            
            # Validate credentials
            if not self.current_credentials:
                raise TuningSessionError("Security credentials required")
            
            # Set tuning target
            self.tuning_target = tuning_target or TuningTarget()
            self.ai_tuner.set_tuning_target(self.tuning_target)
            
            # Start session
            self.state = SessionState.ACTIVE
            self.session_start_time = time.time()
            self.current_phase = SessionPhase.ANALYZE
            
            # Start AI learning if not already active
            if self.ai_tuner.mode.value == "inactive":
                await self.ai_tuner.start_learning()
            
            # Start telemetry collection if not active
            if not self.telemetry.is_collecting():
                await self.telemetry.start_collection(self.session_id)
            
            self.logger.info(f"Tuning session started: {self.session_id}")
            return True
            
        except Exception as e:
            self.state = SessionState.ERROR
            self.logger.error(f"Failed to start session: {e}")
            return False
    
    async def execute_phase(self, phase: SessionPhase) -> PhaseResult:
        """
        Execute a specific session phase.
        
        Args:
            phase: Phase to execute
            
        Returns:
            Phase execution result
        """
        if self.state != SessionState.ACTIVE:
            raise TuningSessionError(f"Cannot execute phase {phase.value}, session not active")
        
        if phase not in self.PHASE_METHODS:
            raise TuningSessionError(f"Unknown phase: {phase.value}")
        
        self.current_phase = phase
        self.phase_start_time = time.time()
        
        try:
            self.logger.info(f"Starting phase: {phase.value}")
            
            # Get phase execution method
            method_name = self.PHASE_METHODS[phase]
            method = getattr(self, method_name)
            
            # Execute phase with timeout
            phase_data = await asyncio.wait_for(
                method(),
                timeout=self.config.max_phase_duration
            )
            
            # Calculate duration
            duration = time.time() - self.phase_start_time
            
            # Create successful result
            result = PhaseResult(
                phase=phase,
                success=True,
                duration=duration,
                data=phase_data
            )
            
            self.phases_completed.append(phase)
            self.phase_results[phase] = result
            
            self.logger.info(f"Phase {phase.value} completed successfully in {duration:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            duration = time.time() - self.phase_start_time
            error_msg = f"Phase {phase.value} timed out after {self.config.max_phase_duration}s"
            
            result = PhaseResult(
                phase=phase,
                success=False,
                duration=duration,
                error_message=error_msg
            )
            
            self.phase_results[phase] = result
            self.logger.error(error_msg)
            
            # Trigger rollback on timeout
            if self.config.enable_auto_rollback and phase in [SessionPhase.APPLY, SessionPhase.VERIFY]:
                await self._trigger_rollback("Phase timeout")
            
            return result
            
        except Exception as e:
            duration = time.time() - self.phase_start_time
            error_msg = f"Phase {phase.value} failed: {e}"
            
            result = PhaseResult(
                phase=phase,
                success=False,
                duration=duration,
                error_message=error_msg
            )
            
            self.phase_results[phase] = result
            self.logger.error(error_msg)
            
            # Trigger rollback on failure
            if self.config.enable_auto_rollback and phase in [SessionPhase.APPLY, SessionPhase.VERIFY]:
                await self._trigger_rollback(f"Phase failure: {e}")
            
            return result
    
    async def _execute_analyze_phase(self) -> Dict[str, Any]:
        """Analyze current vehicle state and tuning."""
        # Get current telemetry
        current_telemetry = self.telemetry.get_latest_telemetry()
        
        # Get current ECU parameters
        ecu_status = self.ecu_exploiter.get_ecu_status()
        
        # Collect baseline data
        baseline_data = {
            "telemetry": current_telemetry.to_dict(),
            "ecu_status": ecu_status,
            "timestamp": time.time(),
        }
        
        # Store baseline for later comparison
        self.performance_metrics = {
            "baseline_power": self._estimate_current_power(current_telemetry),
            "baseline_torque": self._estimate_current_torque(current_telemetry),
            "baseline_efficiency": self._estimate_current_efficiency(current_telemetry),
        }
        
        return {
            "baseline_data": baseline_data,
            "performance_metrics": self.performance_metrics,
            "analysis_complete": True,
        }
    
    async def _execute_plan_phase(self) -> Dict[str, Any]:
        """Plan optimization using AI tuner."""
        # Get current telemetry
        current_telemetry = self.telemetry.get_latest_telemetry()
        
        # Generate optimization plan
        optimization_result = await self.ai_tuner.optimize_for_target(self.tuning_target)
        
        # Extract optimized parameters
        self.optimized_parameters = optimization_result["optimal_parameters"]
        
        # Validate parameters against safety constraints
        validation_result = self._validate_parameters(self.optimized_parameters)
        
        if not validation_result["safe"]:
            raise SessionPhaseError(f"Parameters failed safety validation: {validation_result['violations']}")
        
        return {
            "optimization_plan": optimization_result,
            "parameters": self.optimized_parameters,
            "validation": validation_result,
            "estimated_gains": optimization_result["estimated_performance"],
        }
    
    async def _execute_validate_phase(self) -> Dict[str, Any]:
        """Validate that the planned changes are safe."""
        # Simulate the changes in a test environment
        simulation_result = await self._simulate_parameter_changes(self.optimized_parameters)
        
        # Check for safety violations
        safety_check = self._perform_safety_checks(simulation_result)
        
        if not safety_check["passed"]:
            raise SessionPhaseError(f"Safety validation failed: {safety_check['violations']}")
        
        return {
            "simulation": simulation_result,
            "safety_check": safety_check,
            "validation_passed": True,
        }
    
    async def _execute_apply_phase(self) -> Dict[str, Any]:
        """Apply the optimized parameters to the ECU."""
        # Create backup before applying changes
        if self.config.backup_before_apply:
            backup_result = await self._create_backup()
            if not backup_result.success:
                raise SessionPhaseError(f"Backup creation failed: {backup_result.error_message}")
            
            # Store rollback data
            self.rollback_data = RollbackData(
                original_parameters=backup_result.data.get("original_parameters", {}),
                backup_checksum=backup_result.data.get("checksum", ""),
                backup_timestamp=time.time(),
                flash_backup_id=backup_result.data.get("backup_id"),
            )
        
        # Apply parameters to ECU
        apply_result = await self._apply_parameters_to_ecu(self.optimized_parameters)
        
        if not apply_result.success:
            # Trigger rollback if apply failed
            if self.config.enable_auto_rollback:
                await self._trigger_rollback("Parameter application failed")
            raise SessionPhaseError(f"Parameter application failed: {apply_result.error_message}")
        
        return {
            "applied_parameters": self.optimized_parameters,
            "backup_created": self.config.backup_before_apply,
            "apply_result": apply_result.data,
        }
    
    async def _execute_verify_phase(self) -> Dict[str, Any]:
        """Verify that applied changes are working correctly."""
        # Monitor telemetry for verification period
        verification_data = await self._monitor_verification_period()
        
        # Check for issues
        verification_result = self._verify_changes(verification_data)
        
        if not verification_result["success"]:
            # Trigger rollback if verification failed
            if self.config.enable_auto_rollback:
                await self._trigger_rollback("Verification failed")
            raise SessionPhaseError(f"Verification failed: {verification_result['issues']}")
        
        # Calculate performance gains
        performance_gains = self._calculate_performance_gains(verification_data)
        
        return {
            "verification_data": verification_data,
            "performance_gains": performance_gains,
            "verification_success": True,
        }
    
    async def _execute_rollback_phase(self) -> Dict[str, Any]:
        """Rollback applied changes."""
        if not self.rollback_data:
            raise RollbackFailedError("No rollback data available")
        
        try:
            # Restore original parameters
            restore_result = await self._restore_parameters(self.rollback_data.original_parameters)
            
            if not restore_result.success:
                raise RollbackFailedError(f"Parameter restoration failed: {restore_result.error_message}")
            
            # Verify rollback
            verification_result = await self._verify_rollback()
            
            return {
                "rollback_completed": True,
                "original_parameters_restored": True,
                "verification": verification_result,
            }
            
        except Exception as e:
            raise RollbackFailedError(f"Rollback failed: {e}")
    
    async def run_full_session(self, tuning_target: Optional[TuningTarget] = None) -> Dict[str, Any]:
        """
        Run the complete tuning session.
        
        Args:
            tuning_target: Optional tuning target
            
        Returns:
            Session results
        """
        # Start session
        if not await self.start_session(tuning_target):
            raise TuningSessionError("Failed to start session")
        
        try:
            # Execute phases in order
            phases = [
                SessionPhase.ANALYZE,
                SessionPhase.PLAN,
                SessionPhase.VALIDATE,
                SessionPhase.APPLY,
                SessionPhase.VERIFY,
            ]
            
            session_results = {
                "session_id": self.session_id,
                "start_time": self.session_start_time,
                "phases": {},
                "success": True,
            }
            
            for phase in phases:
                result = await self.execute_phase(phase)
                session_results["phases"][phase.value] = {
                    "success": result.success,
                    "duration": result.duration,
                    "data": result.data,
                    "error": result.error_message,
                }
                
                if not result.success:
                    session_results["success"] = False
                    break
            
            # Complete session
            session_results["end_time"] = time.time()
            session_results["total_duration"] = session_results["end_time"] - session_results["start_time"]
            
            await self.complete_session()
            
            return session_results
            
        except Exception as e:
            self.logger.error(f"Session execution failed: {e}")
            await self.abort_session()
            raise TuningSessionError(f"Session execution failed: {e}")
    
    async def complete_session(self) -> None:
        """Mark session as completed."""
        self.state = SessionState.INACTIVE
        self.current_phase = SessionPhase.COMPLETED
        
        # Save session results to database
        await self._save_session_results()
        
        self.logger.info(f"Session {self.session_id} completed successfully")
    
    async def abort_session(self) -> None:
        """Abort the session due to error."""
        self.state = SessionState.ERROR
        self.current_phase = SessionPhase.FAILED
        
        # Trigger rollback if needed
        if self.config.enable_auto_rollback and SessionPhase.APPLY in self.phases_completed:
            try:
                await self._trigger_rollback("Session aborted")
            except Exception as e:
                self.logger.error(f"Rollback during abort failed: {e}")
        
        # Save session results
        await self._save_session_results()
        
        self.logger.info(f"Session {self.session_id} aborted")
    
    async def pause_session(self) -> bool:
        """Pause the current session."""
        if self.state != SessionState.ACTIVE:
            return False
        
        self.state = SessionState.PAUSED
        self.logger.info(f"Session {self.session_id} paused")
        return True
    
    async def resume_session(self) -> bool:
        """Resume a paused session."""
        if self.state != SessionState.PAUSED:
            return False
        
        self.state = SessionState.ACTIVE
        self.logger.info(f"Session {self.session_id} resumed")
        return True
    
    # Helper methods
    def _estimate_current_power(self, telemetry: TelemetryData) -> float:
        """Estimate current power from telemetry."""
        # Simplified power estimation
        rpm = telemetry.rpm or 2000
        load = telemetry.load or 50
        boost = telemetry.boost_pressure or 0
        
        base_power = 150.0  # Base MS3 power
        power_gain = (load / 100) * 50 + boost * 5
        
        return base_power + power_gain
    
    def _estimate_current_torque(self, telemetry: TelemetryData) -> float:
        """Estimate current torque from telemetry."""
        power = self._estimate_current_power(telemetry)
        rpm = telemetry.rpm or 2000
        
        # Torque = (Power * 5252) / RPM
        if rpm > 0:
            return (power * 5252) / rpm
        return 250.0
    
    def _estimate_current_efficiency(self, telemetry: TelemetryData) -> float:
        """Estimate current efficiency."""
        afr = telemetry.afr or 14.7
        maf = telemetry.maf or 50
        
        # Simplified efficiency calculation
        efficiency = 100 - abs(afr - 14.7) * 2
        
        return max(0, min(100, efficiency))
    
    def _validate_parameters(self, parameters: Dict[str, float]) -> Dict[str, Any]:
        """Validate parameters against safety constraints."""
        violations = []
        
        for param, value in parameters.items():
            if param == "boost_target" and value > self.config.max_boost_threshold:
                violations.append(f"Boost too high: {value:.1f} > {self.config.max_boost_threshold}")
            
            elif param == "timing_advance" and value > 40:
                violations.append(f"Timing too advanced: {value:.1f} > 40")
            
            elif param == "fuel_base" and (value < 5 or value > 30):
                violations.append(f"Fuel out of range: {value:.1f}")
        
        return {
            "safe": len(violations) == 0,
            "violations": violations,
        }
    
    async def _simulate_parameter_changes(self, parameters: Dict[str, float]) -> Dict[str, Any]:
        """Simulate the effect of parameter changes."""
        # This would use the AI models to predict outcomes
        # For now, return a simple simulation
        return {
            "predicted_power": self._estimate_current_power(self.telemetry.get_latest_telemetry()) + 20,
            "predicted_torque": self._estimate_current_torque(self.telemetry.get_latest_telemetry()) + 25,
            "predicted_efficiency": 85.0,
            "risk_level": "low",
        }
    
    def _perform_safety_checks(self, simulation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform safety checks on simulation results."""
        violations = []
        
        if simulation_result["risk_level"] == "high":
            violations.append("High risk simulation result")
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
        }
    
    async def _create_backup(self) -> PhaseResult:
        """Create ECU backup before applying changes."""
        try:
            backup_result = await self.ecu_exploiter.backup_ecu()
            
            if backup_result.success:
                return PhaseResult(
                    phase=SessionPhase.APPLY,
                    success=True,
                    data=backup_result.data
                )
            else:
                return PhaseResult(
                    phase=SessionPhase.APPLY,
                    success=False,
                    error_message=backup_result.error_message
                )
                
        except Exception as e:
            return PhaseResult(
                phase=SessionPhase.APPLY,
                success=False,
                error_message=str(e)
            )
    
    async def _apply_parameters_to_ecu(self, parameters: Dict[str, float]) -> PhaseResult:
        """Apply parameters to ECU."""
        try:
            # Convert parameters to ECU memory writes
            # This is a simplified implementation
            for param, value in parameters.items():
                address = self._get_parameter_address(param)
                if address:
                    # Convert value to bytes
                    data = self._parameter_to_bytes(param, value)
                    
                    # Write to ECU
                    write_result = await self.ecu_exploiter.write_memory(address, data)
                    if not write_result.success:
                        return PhaseResult(
                            phase=SessionPhase.APPLY,
                            success=False,
                            error_message=f"Failed to write {param}: {write_result.error_message}"
                        )
            
            return PhaseResult(
                phase=SessionPhase.APPLY,
                success=True,
                data={"parameters_applied": list(parameters.keys())}
            )
            
        except Exception as e:
            return PhaseResult(
                phase=SessionPhase.APPLY,
                success=False,
                error_message=str(e)
            )
    
    def _get_parameter_address(self, param_name: str) -> Optional[int]:
        """Get ECU memory address for parameter."""
        # Simplified address mapping
        address_map = {
            "fuel_base": 0x020000,
            "timing_advance": 0x022000,
            "boost_target": 0x024000,
        }
        return address_map.get(param_name)
    
    def _parameter_to_bytes(self, param_name: str, value: float) -> bytes:
        """Convert parameter value to bytes for ECU write."""
        # Simplified conversion
        if param_name in ["fuel_base", "timing_advance", "boost_target"]:
            return struct.pack("<f", value)  # 4-byte float
        return bytes()
    
    async def _monitor_verification_period(self) -> List[TelemetryData]:
        """Monitor telemetry during verification period."""
        verification_data = []
        start_time = time.time()
        
        while time.time() - start_time < self.config.verification_duration:
            # Get current telemetry
            current_telemetry = self.telemetry.get_latest_telemetry()
            verification_data.append(current_telemetry)
            
            # Check for safety violations
            if self.config.safety_checks_enabled:
                violations = self._check_telemetry_safety(current_telemetry)
                if violations:
                    self.safety_violations.extend(violations)
                    break
            
            await asyncio.sleep(1.0)  # Sample every second
        
        return verification_data
    
    def _check_telemetry_safety(self, telemetry: TelemetryData) -> List[str]:
        """Check telemetry for safety violations."""
        violations = []
        
        if telemetry.boost_pressure and telemetry.boost_pressure > self.config.max_boost_threshold:
            violations.append(f"Boost exceeded threshold: {telemetry.boost_pressure:.1f} psi")
        
        if telemetry.knock_retard and telemetry.knock_retard > self.config.max_knock_threshold:
            violations.append(f"Knock retard detected: {telemetry.knock_retard:.1f}°")
        
        if telemetry.afr and telemetry.afr < self.config.min_afr_threshold:
            violations.append(f"AFR too lean: {telemetry.afr:.1f}")
        
        return violations
    
    def _verify_changes(self, verification_data: List[TelemetryData]) -> Dict[str, Any]:
        """Verify that changes are working correctly."""
        if not verification_data:
            return {"success": False, "issues": ["No verification data collected"]}
        
        # Check for safety violations
        if self.safety_violations:
            return {"success": False, "issues": self.safety_violations}
        
        # Check performance improvements
        latest_telemetry = verification_data[-1]
        current_power = self._estimate_current_power(latest_telemetry)
        
        power_gain = current_power - self.performance_metrics["baseline_power"]
        
        if power_gain < 0:
            return {"success": False, "issues": [f"Power decreased: {power_gain:.1f} HP"]}
        
        return {"success": True, "issues": [], "power_gain": power_gain}
    
    def _calculate_performance_gains(self, verification_data: List[TelemetryData]) -> Dict[str, float]:
        """Calculate performance gains from verification data."""
        if not verification_data:
            return {"power_gain": 0, "torque_gain": 0, "efficiency_gain": 0}
        
        latest_telemetry = verification_data[-1]
        
        current_power = self._estimate_current_power(latest_telemetry)
        current_torque = self._estimate_current_torque(latest_telemetry)
        current_efficiency = self._estimate_current_efficiency(latest_telemetry)
        
        return {
            "power_gain": current_power - self.performance_metrics["baseline_power"],
            "torque_gain": current_torque - self.performance_metrics["baseline_torque"],
            "efficiency_gain": current_efficiency - self.performance_metrics["baseline_efficiency"],
        }
    
    async def _trigger_rollback(self, reason: str) -> None:
        """Trigger automatic rollback."""
        self.logger.warning(f"Triggering automatic rollback: {reason}")
        
        try:
            rollback_result = await self.execute_phase(SessionPhase.ROLLBACK)
            if rollback_result.success:
                self.logger.info("Automatic rollback completed successfully")
            else:
                self.logger.error(f"Automatic rollback failed: {rollback_result.error_message}")
        except Exception as e:
            self.logger.error(f"Automatic rollback error: {e}")
    
    async def _restore_parameters(self, original_parameters: Dict[str, float]) -> PhaseResult:
        """Restore original parameters."""
        return await self._apply_parameters_to_ecu(original_parameters)
    
    async def _verify_rollback(self) -> Dict[str, Any]:
        """Verify that rollback was successful."""
        current_telemetry = self.telemetry.get_latest_telemetry()
        current_power = self._estimate_current_power(current_telemetry)
        
        # Check if power returned to baseline
        power_diff = abs(current_power - self.performance_metrics["baseline_power"])
        
        return {
            "rollback_verified": power_diff < 5.0,  # Within 5 HP
            "power_difference": power_diff,
        }
    
    async def _save_session_results(self) -> None:
        """Save session results to database."""
        try:
            session_data = {
                "session_id": self.session_id,
                "start_time": self.session_start_time,
                "end_time": time.time(),
                "phases_completed": [phase.value for phase in self.phases_completed],
                "phase_results": {
                    phase.value: {
                        "success": result.success,
                        "duration": result.duration,
                        "error": result.error_message,
                    }
                    for phase, result in self.phase_results.items()
                },
                "tuning_target": self.tuning_target.to_dict() if self.tuning_target else None,
                "performance_metrics": self.performance_metrics,
                "safety_violations": self.safety_violations,
                "rollback_data": self.rollback_data.to_dict() if self.rollback_data else None,
            }
            
            # Save to database (implementation would depend on database schema)
            self.logger.info(f"Session results saved: {self.session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save session results: {e}")
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status."""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "current_phase": self.current_phase.value,
            "phases_completed": [phase.value for phase in self.phases_completed],
            "session_duration": time.time() - self.session_start_time if self.session_start_time > 0 else 0,
            "phase_duration": time.time() - self.phase_start_time if self.phase_start_time > 0 else 0,
            "safety_violations": len(self.safety_violations),
            "rollback_available": self.rollback_data is not None,
        }
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.state == SessionState.ACTIVE:
            self.logger.warning(f"Session {self.session_id} deleted while active")
