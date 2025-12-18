"""
RacingFeatureController - Advanced racing features for performance tuning.

This module provides high-performance racing features including launch control,
flat-shift, anti-lag, and more, with clean UDS implementation for Mazda vehicles.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Awaitable, Any, Tuple

from MazdaCANEngine import MazdaCANEngine
from MazdaSecurityCore import MazdaSecurityCore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureState(Enum):
    """State of a racing feature."""
    DISABLED = auto()
    ARMED = auto()
    ACTIVE = auto()
    FAULT = auto()

class FeatureStatus:
    """Status of a racing feature."""
    def __init__(self, name: str):
        self.name = name
        self.state = FeatureState.DISABLED
        self.last_updated = 0.0
        self.fault_code: Optional[str] = None
        self.metrics: Dict[str, Any] = {}
    
    def update(self, state: FeatureState, **metrics) -> None:
        """Update the feature status."""
        self.state = state
        self.last_updated = time.time()
        self.metrics.update(metrics)
        
        if state == FeatureState.FAULT and "fault_code" in metrics:
            self.fault_code = metrics["fault_code"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert status to dictionary."""
        return {
            "name": self.name,
            "state": self.state.name,
            "last_updated": self.last_updated,
            "fault_code": self.fault_code,
            "metrics": self.metrics
        }

class LaunchControlMode(Enum):
    """Launch control operating modes."""
    OFF = auto()
    STAGE_1 = auto()  # Soft launch (street)
    STAGE_2 = auto()  # Aggressive launch (track)
    STAGE_3 = auto()  # Max performance (drag)
    VALET = auto()    # Reduced power mode

class AntiLagMode(Enum):
    """Anti-lag system modes."""
    OFF = auto()
    MILD = auto()     # Reduced pops, better for street
    SPORT = auto()    # Moderate pops and bangs
    RACE = auto()     # Aggressive anti-lag with loud pops
    DRAG = auto()     # Maximum anti-lag for drag racing

class TwoStepMode(Enum):
    """Two-step rev limiter modes."""
    OFF = auto()
    LAUNCH = auto()   # For standing starts
    FLAT_SHIFT = auto()  # For flat-foot shifting
    BOTH = auto()     # Both modes active

@dataclass
class RacingFeatureConfig:
    """Configuration for racing features."""
    # Launch Control
    launch_control_enabled: bool = False
    launch_rpm: int = 4000
    launch_control_mode: LaunchControlMode = LaunchControlMode.STAGE_1
    launch_retard_deg: float = 5.0
    launch_fuel_add: float = 0.0
    launch_boost_target: float = 0.0  # psi
    
    # Flat-Shift
    flat_shift_enabled: bool = False
    flat_shift_rpm: int = 6500
    flat_shift_cut_time: int = 50  # ms
    flat_shift_retard_deg: float = 3.0
    flat_shift_fuel_cut: float = 0.0  # %
    
    # Anti-Lag
    anti_lag_enabled: bool = False
    anti_lag_mode: AntiLagMode = AntiLagMode.OFF
    anti_lag_rpm_min: int = 1500
    anti_lag_rpm_max: int = 4000
    anti_lag_throttle_threshold: float = 80.0  # %
    anti_lag_ignition_retard: float = 10.0  # degrees
    anti_lag_fuel_add: float = 0.0  # %
    anti_lag_bang_volume: float = 0.5  # 0-1.0
    
    # Pop & Bang
    pop_bang_enabled: bool = False
    pop_bang_rpm_min: int = 3000
    pop_bang_throttle_close_speed: float = 50.0  # %/s
    pop_bang_ignition_cut_deg: float = 15.0
    pop_bang_fuel_add: float = 5.0  # %
    pop_bang_min_speed: float = 20.0  # km/h
    
    # Two-Step
    two_step_enabled: bool = False
    two_step_mode: TwoStepMode = TwoStepMode.OFF
    two_step_launch_rpm: int = 4500
    two_step_flat_shift_rpm: int = 6800
    two_step_retard_deg: float = 5.0
    two_step_fuel_cut: float = 0.0  # %
    
    # Stealth Mode
    stealth_mode_enabled: bool = False
    stealth_exit_strategy: str = "normal"  # normal, gradual, map_switch
    stealth_max_boost: float = 5.0  # psi
    stealth_launch_disabled: bool = True
    stealth_anti_lag_disabled: bool = True
    stealth_pop_bang_disabled: bool = True
    
    # Safety
    max_engine_rpm: int = 7500
    max_boost_psi: float = 25.0
    oil_temp_limit_c: float = 120.0
    coolant_temp_limit_c: float = 110.0
    afr_safety_min: float = 10.0
    afr_safety_max: float = 16.0

class RacingFeatureController:
    """Controller for advanced racing features."""
    
    def __init__(self, can_engine: MazdaCANEngine, security_core: MazdaSecurityCore):
        """Initialize the racing feature controller."""
        self.can_engine = can_engine
        self.security_core = security_core
        
        # Configuration
        self.config = RacingFeatureConfig()
        
        # Feature states
        self.status: Dict[str, FeatureStatus] = {
            "launch_control": FeatureStatus("Launch Control"),
            "flat_shift": FeatureStatus("Flat-Shift"),
            "anti_lag": FeatureStatus("Anti-Lag"),
            "pop_bang": FeatureStatus("Pop & Bang"),
            "two_step": FeatureStatus("Two-Step"),
            "stealth_mode": FeatureStatus("Stealth Mode")
        }
        
        # Runtime state
        self._vehicle_state = {
            "rpm": 0,
            "speed": 0,
            "throttle_pos": 0,
            "gear": 0,
            "clutch": False,
            "brake": False,
            "launch_active": False,
            "flat_shift_active": False,
            "anti_lag_active": False,
            "two_step_active": False
        }
        
        # Event callbacks
        self._callbacks: Dict[str, List[Callable[[str, Dict], Awaitable[None]]]] = {
            "state_change": [],
            "fault": [],
            "launch_activated": [],
            "flat_shift_activated": [],
            "anti_lag_activated": [],
            "pop_bang_triggered": []
        }
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._running = False
    
    # Public API
    
    async def initialize(self) -> None:
        """Initialize the racing feature controller."""
        if self._running:
            return
            
        self._running = True
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._monitor_vehicle_state()),
            asyncio.create_task(self._process_features())
        ]
        
        logger.info("RacingFeatureController initialized")
    
    async def shutdown(self) -> None:
        """Shut down the racing feature controller."""
        self._running = False
        
        # Cancel all background tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Reset all features
        await self._reset_all_features()
        
        logger.info("RacingFeatureController shut down")
    
    def update_config(self, config: RacingFeatureConfig) -> None:
        """Update the racing feature configuration."""
        self.config = config
        
        # Apply immediate configuration changes
        if not config.launch_control_enabled:
            self.status["launch_control"].update(FeatureState.DISABLED)
        
        if not config.flat_shift_enabled:
            self.status["flat_shift"].update(FeatureState.DISABLED)
        
        if not config.anti_lag_enabled:
            self.status["anti_lag"].update(FeatureState.DISABLED)
            self._vehicle_state["anti_lag_active"] = False
        
        if not config.pop_bang_enabled:
            self.status["pop_bang"].update(FeatureState.DISABLED)
        
        if not config.two_step_enabled:
            self.status["two_step"].update(FeatureState.DISABLED)
            self._vehicle_state["two_step_active"] = False
    
    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get the current status of all features."""
        return {name: status.to_dict() for name, status in self.status.items()}
    
    def add_callback(self, event_type: str, callback: Callable[[str, Dict], Awaitable[None]]) -> None:
        """Add an event callback."""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable[[str, Dict], Awaitable[None]]) -> None:
        """Remove an event callback."""
        if event_type in self._callbacks and callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)
    
    # Feature control methods
    
    async def arm_launch_control(self) -> None:
        """Arm the launch control system."""
        if not self.config.launch_control_enabled:
            raise RuntimeError("Launch control is not enabled in configuration")
        
        # Check vehicle conditions
        if self._vehicle_state["speed"] > 5:  # km/h
            raise RuntimeError("Launch control can only be armed when stationary")
        
        if self._vehicle_state["rpm"] > 1500:
            raise RuntimeError("Engine RPM too high to arm launch control")
        
        # Arm launch control
        self.status["launch_control"].update(FeatureState.ARMED)
        
        # Notify listeners
        await self._notify_event("state_change", {
            "feature": "launch_control",
            "state": "armed"
        })
    
    async def activate_launch_control(self) -> None:
        """Activate launch control (called when launch conditions are met)."""
        if self.status["launch_control"].state != FeatureState.ARMED:
            raise RuntimeError("Launch control is not armed")
        
        self.status["launch_control"].update(FeatureState.ACTIVE)
        self._vehicle_state["launch_active"] = True
        
        # Apply launch control parameters
        await self._apply_launch_control_params()
        
        # Notify listeners
        await self._notify_event("launch_activated", {
            "rpm": self._vehicle_state["rpm"],
            "throttle": self._vehicle_state["throttle_pos"]
        })
    
    async def deactivate_launch_control(self) -> None:
        """Deactivate launch control."""
        if self.status["launch_control"].state == FeatureState.DISABLED:
            return
        
        self.status["launch_control"].update(FeatureState.DISABLED)
        self._vehicle_state["launch_active"] = False
        
        # Reset launch control parameters
        await self._reset_launch_control_params()
        
        # Notify listeners
        await self._notify_event("state_change", {
            "feature": "launch_control",
            "state": "disabled"
        })
    
    async def activate_flat_shift(self) -> None:
        """Activate flat-shift (called during gear shifts)."""
        if not self.config.flat_shift_enabled:
            return
            
        if self.status["flat_shift"].state == FeatureState.ACTIVE:
            return
            
        self.status["flat_shift"].update(FeatureState.ACTIVE)
        self._vehicle_state["flat_shift_active"] = True
        
        # Apply flat-shift parameters
        await self._apply_flat_shift_params()
        
        # Notify listeners
        await self._notify_event("flat_shift_activated", {
            "rpm": self._vehicle_state["rpm"],
            "gear": self._vehicle_state["gear"]
        })
    
    async def deactivate_flat_shift(self) -> None:
        """Deactivate flat-shift."""
        if self.status["flat_shift"].state != FeatureState.ACTIVE:
            return
            
        self.status["flat_shift"].update(FeatureState.DISABLED)
        self._vehicle_state["flat_shift_active"] = False
        
        # Reset flat-shift parameters
        await self._reset_flat_shift_params()
    
    async def activate_anti_lag(self) -> None:
        """Activate anti-lag system."""
        if not self.config.anti_lag_enabled:
            return
            
        if self.status["anti_lag"].state == FeatureState.ACTIVE:
            return
            
        # Check conditions
        if not self._check_anti_lag_conditions():
            return
            
        self.status["anti_lag"].update(FeatureState.ACTIVE)
        self._vehicle_state["anti_lag_active"] = True
        
        # Apply anti-lag parameters
        await self._apply_anti_lag_params()
        
        # Notify listeners
        await self._notify_event("anti_lag_activated", {
            "mode": self.config.anti_lag_mode.name,
            "rpm": self._vehicle_state["rpm"]
        })
    
    async def deactivate_anti_lag(self) -> None:
        """Deactivate anti-lag system."""
        if self.status["anti_lag"].state != FeatureState.ACTIVE:
            return
            
        self.status["anti_lag"].update(FeatureState.DISABLED)
        self._vehicle_state["anti_lag_active"] = False
        
        # Reset anti-lag parameters
        await self._reset_anti_lag_params()
    
    async def trigger_pop_bang(self) -> None:
        """Trigger a pop & bang event."""
        if not self.config.pop_bang_enabled:
            return
            
        # Check conditions
        if not self._check_pop_bang_conditions():
            return
            
        # Apply pop & bang parameters
        await self._apply_pop_bang_params()
        
        # Schedule reset
        asyncio.create_task(self._reset_pop_bang_after_delay())
        
        # Notify listeners
        await self._notify_event("pop_bang_triggered", {
            "rpm": self._vehicle_state["rpm"],
            "throttle": self._vehicle_state["throttle_pos"]
        })
    
    async def activate_two_step(self, mode: TwoStepMode) -> None:
        """Activate two-step rev limiter."""
        if not self.config.two_step_enabled:
            return
            
        if mode == TwoStepMode.OFF:
            await self.deactivate_two_step()
            return
            
        if mode == TwoStepMode.LAUNCH and not self._check_launch_conditions():
            return
            
        if mode == TwoStepMode.FLAT_SHIFT and not self._check_flat_shift_conditions():
            return
            
        self.status["two_step"].update(FeatureState.ACTIVE, mode=mode.name)
        self._vehicle_state["two_step_active"] = True
        self._vehicle_state["two_step_mode"] = mode
        
        # Apply two-step parameters
        await self._apply_two_step_params(mode)
    
    async def deactivate_two_step(self) -> None:
        """Deactivate two-step rev limiter."""
        if self.status["two_step"].state != FeatureState.ACTIVE:
            return
            
        self.status["two_step"].update(FeatureState.DISABLED)
        self._vehicle_state["two_step_active"] = False
        
        # Reset two-step parameters
        await self._reset_two_step_params()
    
    async def toggle_stealth_mode(self) -> bool:
        """Toggle stealth mode on/off."""
        new_state = not self.config.stealth_mode_enabled
        self.config.stealth_mode_enabled = new_state
        
        if new_state:
            self.status["stealth_mode"].update(FeatureState.ACTIVE)
            await self._apply_stealth_mode_params()
        else:
            self.status["stealth_mode"].update(FeatureState.DISABLED)
            await self._reset_stealth_mode_params()
        
        return new_state
    
    # Internal methods
    
    async def _monitor_vehicle_state(self) -> None:
        """Monitor vehicle state and trigger features as needed."""
        while self._running:
            try:
                # Read vehicle parameters
                params = await self.can_engine.read_parameters([
                    "rpm", "speed", "throttle_pos", "gear", 
                    "clutch_switch", "brake_switch", "boost_psi",
                    "coolant_temp", "oil_temp", "afr"
                ])
                
                # Update vehicle state
                self._vehicle_state.update({
                    "rpm": params.get("rpm", 0),
                    "speed": params.get("speed", 0),
                    "throttle_pos": params.get("throttle_pos", 0),
                    "gear": params.get("gear", 0),
                    "clutch": bool(params.get("clutch_switch", 0)),
                    "brake": bool(params.get("brake_switch", 0)),
                    "boost_psi": params.get("boost_psi", 0),
                    "coolant_temp": params.get("coolant_temp", 0),
                    "oil_temp": params.get("oil_temp", 0),
                    "afr": params.get("afr", 0)
                })
                
                # Check for fault conditions
                await self._check_fault_conditions()
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.02)  # 50Hz update rate
                
            except Exception as e:
                logger.error(f"Error in vehicle state monitor: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error
    
    async def _process_features(self) -> None:
        """Process and update racing features."""
        while self._running:
            try:
                # Process launch control
                await self._process_launch_control()
                
                # Process flat-shift
                await self._process_flat_shift()
                
                # Process anti-lag
                await self._process_anti_lag()
                
                # Process pop & bang
                await self._process_pop_bang()
                
                # Process two-step
                await self._process_two_step()
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.01)  # 100Hz update rate
                
            except Exception as e:
                logger.error(f"Error in feature processor: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error
    
    async def _process_launch_control(self) -> None:
        """Process launch control logic."""
        if not self.config.launch_control_enabled:
            return
            
        state = self.status["launch_control"].state
        
        # Check for launch activation
        if state == FeatureState.ARMED:
            if (self._vehicle_state["throttle_pos"] > 90 and 
                self._vehicle_state["rpm"] > self.config.launch_rpm * 0.8 and
                self._vehicle_state["clutch"] and 
                self._vehicle_state["speed"] < 5):
                await self.activate_launch_control()
        
        # Check for launch deactivation
        elif state == FeatureState.ACTIVE:
            if (self._vehicle_state["speed"] > 30 or 
                self._vehicle_state["throttle_pos"] < 10):
                await self.deactivate_launch_control()
    
    async def _process_flat_shift(self) -> None:
        """Process flat-shift logic."""
        if not self.config.flat_shift_enabled:
            return
            
        state = self.status["flat_shift"].state
        
        # Check for flat-shift activation
        if (state != FeatureState.ACTIVE and 
            self._vehicle_state["throttle_pos"] > 90 and 
            self._vehicle_state["rpm"] > self.config.flat_shift_rpm * 0.9 and
            self._vehicle_state["clutch"] and
            self._vehicle_state["gear"] > 0):
            await self.activate_flat_shift()
        
        # Check for flat-shift deactivation
        elif state == FeatureState.ACTIVE and not self._vehicle_state["clutch"]:
            await self.deactivate_flat_shift()
    
    async def _process_anti_lag(self) -> None:
        """Process anti-lag logic."""
        if not self.config.anti_lag_enabled:
            return
            
        state = self.status["anti_lag"].state
        
        # Check for anti-lag activation
        if (state != FeatureState.ACTIVE and 
            self._check_anti_lag_conditions()):
            await self.activate_anti_lag()
        
        # Check for anti-lag deactivation
        elif state == FeatureState.ACTIVE and not self._check_anti_lag_conditions():
            await self.deactivate_anti_lag()
    
    async def _process_pop_bang(self) -> None:
        """Process pop & bang logic."""
        if not self.config.pop_bang_enabled:
            return
            
        # Check for throttle lift-off
        if (self._vehicle_state["throttle_pos"] < 10 and 
            self._vehicle_state["rpm"] > self.config.pop_bang_rpm_min and
            self._vehicle_state["speed"] > self.config.pop_bang_min_speed):
            await self.trigger_pop_bang()
    
    async def _process_two_step(self) -> None:
        """Process two-step rev limiter logic."""
        if not self.config.two_step_enabled:
            return
            
        state = self.status["two_step"].state
        
        # Check for two-step activation
        if state != FeatureState.ACTIVE:
            if (self._check_launch_conditions() and 
                self.config.two_step_mode in [TwoStepMode.LAUNCH, TwoStepMode.BOTH]):
                await self.activate_two_step(TwoStepMode.LAUNCH)
            elif (self._check_flat_shift_conditions() and 
                  self.config.two_step_mode in [TwoStepMode.FLAT_SHIFT, TwoStepMode.BOTH]):
                await self.activate_two_step(TwoStepMode.FLAT_SHIFT)
        
        # Check for two-step deactivation
        elif state == FeatureState.ACTIVE:
            current_mode = self._vehicle_state.get("two_step_mode")
            if (current_mode == TwoStepMode.LAUNCH and not self._check_launch_conditions()) or \
               (current_mode == TwoStepMode.FLAT_SHIFT and not self._check_flat_shift_conditions()):
                await self.deactivate_two_step()
    
    # Condition checking methods
    
    def _check_launch_conditions(self) -> bool:
        """Check if launch conditions are met."""
        return (
            self._vehicle_state["speed"] < 5 and
            self._vehicle_state["clutch"] and
            self._vehicle_state["throttle_pos"] > 90
        )
    
    def _check_flat_shift_conditions(self) -> bool:
        """Check if flat-shift conditions are met."""
        return (
            self._vehicle_state["rpm"] > self.config.flat_shift_rpm * 0.9 and
            self._vehicle_state["throttle_pos"] > 90 and
            self._vehicle_state["clutch"] and
            self._vehicle_state["gear"] > 0
        )
    
    def _check_anti_lag_conditions(self) -> bool:
        """Check if anti-lag conditions are met."""
        return (
            self._vehicle_state["rpm"] >= self.config.anti_lag_rpm_min and
            self._vehicle_state["rpm"] <= self.config.anti_lag_rpm_max and
            self._vehicle_state["throttle_pos"] < self.config.anti_lag_throttle_threshold and
            self._vehicle_state["boost_psi"] < 5.0  # Only activate at low boost
        )
    
    def _check_pop_bang_conditions(self) -> bool:
        """Check if pop & bang conditions are met."""
        return (
            self._vehicle_state["rpm"] >= self.config.pop_bang_rpm_min and
            self._vehicle_state["speed"] >= self.config.pop_bang_min_speed and
            self._vehicle_state["throttle_pos"] < 10  # On throttle lift-off
        )
    
    async def _check_fault_conditions(self) -> None:
        """Check for fault conditions that require feature deactivation."""
        # Check for over-rev
        if self._vehicle_state["rpm"] > self.config.max_engine_rpm:
            await self._handle_fault("over_rev", f"Engine over-rev: {self._vehicle_state['rpm']} RPM")
        
        # Check for over-boost
        if self._vehicle_state["boost_psi"] > self.config.max_boost_psi:
            await self._handle_fault("over_boost", f"Over-boost: {self._vehicle_state['boost_psi']} psi")
        
        # Check for high temperatures
        if self._vehicle_state["oil_temp"] > self.config.oil_temp_limit_c:
            await self._handle_fault("high_oil_temp", f"High oil temperature: {self._vehicle_state['oil_temp']}°C")
            
        if self._vehicle_state["coolant_temp"] > self.config.coolant_temp_limit_c:
            await self._handle_fault("high_coolant_temp", f"High coolant temperature: {self._vehicle_state['coolant_temp']}°C")
        
        # Check for AFR safety
        if (self._vehicle_state["afr"] < self.config.afr_safety_min or 
            self._vehicle_state["afr"] > self.config.afr_safety_max):
            await self._handle_fault("unsafe_afr", f"Unsafe AFR: {self._vehicle_state['afr']}")
    
    async def _handle_fault(self, fault_code: str, message: str) -> None:
        """Handle a fault condition."""
        logger.error(f"Fault detected: {message}")
        
        # Update status for all features
        for name, status in self.status.items():
            if status.state == FeatureState.ACTIVE:
                status.update(FeatureState.FAULT, fault_code=fault_code)
        
        # Reset all features
        await self._reset_all_features()
        
        # Notify listeners
        await self._notify_event("fault", {
            "code": fault_code,
            "message": message,
            "timestamp": time.time()
        })
    
    # Parameter application methods
    
    async def _apply_launch_control_params(self) -> None:
        """Apply launch control parameters to the ECU."""
        try:
            # Set ignition retard
            await self.can_engine.set_ignition_timing(
                base_offset=-self.config.launch_retard_deg
            )
            
            # Set fuel enrichment if configured
            if self.config.launch_fuel_add > 0:
                await self.can_engine.set_fuel_enrichment(
                    rpm_range=(0, self.config.launch_rpm * 1.1),
                    load_range=(80, 100),
                    enrichment_pct=self.config.launch_fuel_add
                )
            
            # Set boost target if configured
            if self.config.launch_boost_target > 0:
                await self.can_engine.set_boost_control(
                    target_boost=self.config.launch_boost_target,
                    ramp_rate=100  # Fast ramp for launch
                )
            
            logger.info(f"Launch control activated at {self.config.launch_rpm} RPM")
            
        except Exception as e:
            logger.error(f"Failed to apply launch control parameters: {e}")
            raise
    
    async def _reset_launch_control_params(self) -> None:
        """Reset launch control parameters to normal."""
        try:
            # Reset ignition timing
            await self.can_engine.set_ignition_timing(base_offset=0)
            
            # Reset fuel enrichment
            await self.can_engine.reset_fuel_enrichment()
            
            # Reset boost control if it was modified
            if self.config.launch_boost_target > 0:
                await self.can_engine.reset_boost_control()
            
            logger.info("Launch control deactivated")
            
        except Exception as e:
            logger.error(f"Failed to reset launch control parameters: {e}")
    
    async def _apply_flat_shift_params(self) -> None:
        """Apply flat-shift parameters to the ECU."""
        try:
            # Set ignition cut for flat-shift
            await self.can_engine.set_ignition_cut(
                rpm_threshold=self.config.flat_shift_rpm,
                cut_deg=self.config.flat_shift_retard_deg,
                duration_ms=self.config.flat_shift_cut_time
            )
            
            # Set fuel cut if configured
            if self.config.flat_shift_fuel_cut > 0:
                await self.can_engine.set_fuel_cut(
                    rpm_threshold=self.config.flat_shift_rpm,
                    cut_pct=self.config.flat_shift_fuel_cut,
                    duration_ms=self.config.flat_shift_cut_time
                )
            
            logger.info(f"Flat-shift activated at {self.config.flat_shift_rpm} RPM")
            
        except Exception as e:
            logger.error(f"Failed to apply flat-shift parameters: {e}")
            raise
    
    async def _reset_flat_shift_params(self) -> None:
        """Reset flat-shift parameters to normal."""
        try:
            # Reset ignition cut
            await self.can_engine.reset_ignition_cut()
            
            # Reset fuel cut if it was modified
            if self.config.flat_shift_fuel_cut > 0:
                await self.can_engine.reset_fuel_cut()
            
            logger.info("Flat-shift deactivated")
            
        except Exception as e:
            logger.error(f"Failed to reset flat-shift parameters: {e}")
    
    async def _apply_anti_lag_params(self) -> None:
        """Apply anti-lag parameters to the ECU."""
        try:
            # Set ignition retard for anti-lag
            retard = self.config.anti_lag_ignition_retard
            if self.config.anti_lag_mode == AntiLagMode.MILD:
                retard *= 0.5
            elif self.config.anti_lag_mode == AntiLagMode.RACE:
                retard *= 1.5
            elif self.config.anti_lag_mode == AntiLagMode.DRAG:
                retard *= 2.0
            
            await self.can_engine.set_ignition_timing(
                base_offset=-retard,
                rpm_range=(self.config.anti_lag_rpm_min, self.config.anti_lag_rpm_max)
            )
            
            # Set fuel enrichment for anti-lag
            fuel_add = self.config.anti_lag_fuel_add
            if self.config.anti_lag_mode in [AntiLagMode.RACE, AntiLagMode.DRAG]:
                fuel_add *= 1.5
            
            if fuel_add > 0:
                await self.can_engine.set_fuel_enrichment(
                    rpm_range=(self.config.anti_lag_rpm_min, self.config.anti_lag_rpm_max),
                    load_range=(0, self.config.anti_lag_throttle_threshold),
                    enrichment_pct=fuel_add
                )
            
            # Configure throttle blip for aggressive modes
            if self.config.anti_lag_mode in [AntiLagMode.RACE, AntiLagMode.DRAG]:
                await self.can_engine.set_throttle_blip(
                    rpm_range=(self.config.anti_lag_rpm_min, self.config.anti_lag_rpm_max),
                    throttle_add=5.0,  # 5% throttle blip
                    duration_ms=100
                )
            
            logger.info(f"Anti-lag activated in {self.config.anti_lag_mode.name} mode")
            
        except Exception as e:
            logger.error(f"Failed to apply anti-lag parameters: {e}")
            raise
    
    async def _reset_anti_lag_params(self) -> None:
        """Reset anti-lag parameters to normal."""
        try:
            # Reset ignition timing
            await self.can_engine.reset_ignition_timing()
            
            # Reset fuel enrichment
            await self.can_engine.reset_fuel_enrichment()
            
            # Reset throttle blip if it was modified
            if self.config.anti_lag_mode in [AntiLagMode.RACE, AntiLagMode.DRAG]:
                await self.can_engine.reset_throttle_blip()
            
            logger.info("Anti-lag deactivated")
            
        except Exception as e:
            logger.error(f"Failed to reset anti-lag parameters: {e}")
    
    async def _apply_pop_bang_params(self) -> None:
        """Apply pop & bang parameters to the ECU."""
        try:
            # Set ignition cut for pop & bang
            await self.can_engine.set_ignition_cut(
                rpm_threshold=self._vehicle_state["rpm"],
                cut_deg=self.config.pop_bang_ignition_cut_deg,
                duration_ms=100  # Short duration for pop effect
            )
            
            # Add extra fuel for the bang
            if self.config.pop_bang_fuel_add > 0:
                await self.can_engine.set_fuel_enrichment(
                    rpm_range=(
                        max(0, self._vehicle_state["rpm"] - 500),
                        self._vehicle_state["rpm"] + 500
                    ),
                    load_range=(0, 20),  # Only at low load (throttle lift-off)
                    enrichment_pct=self.config.pop_bang_fuel_add,
                    duration_ms=200  # Slightly longer than ignition cut
                )
            
            logger.info("Pop & bang triggered")
            
        except Exception as e:
            logger.error(f"Failed to apply pop & bang parameters: {e}")
            raise
    
    async def _reset_pop_bang_after_delay(self) -> None:
        """Reset pop & bang parameters after a short delay."""
        await asyncio.sleep(0.2)  # Wait for the pop & bang to complete
        
        try:
            # Reset ignition cut
            await self.can_engine.reset_ignition_cut()
            
            # Reset fuel enrichment
            await self.can_engine.reset_fuel_enrichment()
            
        except Exception as e:
            logger.error(f"Failed to reset pop & bang parameters: {e}")
    
    async def _apply_two_step_params(self, mode: TwoStepMode) -> None:
        """Apply two-step rev limiter parameters to the ECU."""
        try:
            if mode in [TwoStepMode.LAUNCH, TwoStepMode.BOTH]:
                # Set launch control rev limit
                await self.can_engine.set_rev_limit(
                    limit_type="launch",
                    rpm=self.config.two_step_launch_rpm,
                    fuel_cut_pct=self.config.two_step_fuel_cut,
                    ignition_retard_deg=self.config.two_step_retard_deg
                )
            
            if mode in [TwoStepMode.FLAT_SHIFT, TwoStepMode.BOTH]:
                # Set flat-shift rev limit
                await self.can_engine.set_rev_limit(
                    limit_type="flat_shift",
                    rpm=self.config.two_step_flat_shift_rpm,
                    fuel_cut_pct=self.config.two_step_fuel_cut,
                    ignition_retard_deg=self.config.two_step_retard_deg
                )
            
            logger.info(f"Two-step activated in {mode.name} mode")
            
        except Exception as e:
            logger.error(f"Failed to apply two-step parameters: {e}")
            raise
    
    async def _reset_two_step_params(self) -> None:
        """Reset two-step rev limiter parameters to normal."""
        try:
            # Reset rev limits
            await self.can_engine.reset_rev_limit("launch")
            await self.can_engine.reset_rev_limit("flat_shift")
            
            logger.info("Two-step deactivated")
            
        except Exception as e:
            logger.error(f"Failed to reset two-step parameters: {e}")
    
    async def _apply_stealth_mode_params(self) -> None:
        """Apply stealth mode parameters to the ECU."""
        try:
            # Limit boost
            await self.can_engine.set_boost_control(
                target_boost=self.config.stealth_max_boost,
                ramp_rate=50  # Gradual ramp for stealth
            )
            
            # Disable launch control if configured
            if self.config.stealth_launch_disabled:
                await self.deactivate_launch_control()
            
            # Disable anti-lag if configured
            if self.config.stealth_anti_lag_disabled:
                await self.deactivate_anti_lag()
            
            # Disable pop & bang if configured
            if self.config.stealth_pop_bang_disabled:
                self.config.pop_bang_enabled = False
            
            logger.info("Stealth mode activated")
            
        except Exception as e:
            logger.error(f"Failed to apply stealth mode parameters: {e}")
            raise
    
    async def _reset_stealth_mode_params(self) -> None:
        """Reset stealth mode parameters to normal."""
        try:
            # Reset boost control
            await self.can_engine.reset_boost_control()
            
            # Re-enable pop & bang if it was disabled
            self.config.pop_bang_enabled = True
            
            logger.info("Stealth mode deactivated")
            
        except Exception as e:
            logger.error(f"Failed to reset stealth mode parameters: {e}")
    
    async def _reset_all_features(self) -> None:
        """Reset all features to their default state."""
        await self.deactivate_launch_control()
        await self.deactivate_flat_shift()
        await self.deactivate_anti_lag()
        await self.deactivate_two_step()
    
    # Helper methods
    
    async def _notify_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notify all registered callbacks of an event."""
        if event_type not in self._callbacks:
            return
            
        for callback in self._callbacks[event_type]:
            try:
                await callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in {event_type} callback: {e}")

# Example usage
async def example():
    # Initialize CAN engine and security core
    can_engine = MazdaCANEngine()
    security_core = MazdaSecurityCore()
    
    # Create racing feature controller
    controller = RacingFeatureController(can_engine, security_core)
    
    try:
        # Initialize controller
        await controller.initialize()
        
        # Configure features
        config = RacingFeatureConfig(
            launch_control_enabled=True,
            launch_rpm=4000,
            flat_shift_enabled=True,
            flat_shift_rpm=6500,
            anti_lag_enabled=True,
            anti_lag_mode=AntiLagMode.SPORT,
            pop_bang_enabled=True,
            two_step_enabled=True,
            two_step_mode=TwoStepMode.BOTH
        )
        controller.update_config(config)
        
        # Add event callbacks
        async def on_state_change(event_type: str, data: Dict[str, Any]) -> None:
            print(f"State changed: {data}")
        
        controller.add_callback("state_change", on_state_change)
        
        # Main loop
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        pass
    finally:
        await controller.shutdown()

if __name__ == "__main__":
    asyncio.run(example())
