#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAZDASPEED3 CONNECTION HEALTH MONITOR
Monitors CAN bus connection and provides auto-reconnect
"""

import threading
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from core.ecu_communication import ECUCommunicator, ECUState
from core.app_state import get_app_state
from utils.logger import get_logger

logger = get_logger(__name__)

class ConnectionHealth(Enum):
    """Connection health status"""
    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    last_message_time: float = 0.0
    messages_per_second: float = 0.0
    error_rate: float = 0.0
    response_time_ms: float = 0.0
    consecutive_failures: int = 0
    total_messages: int = 0
    failed_messages: int = 0

class ConnectionHealthMonitor:
    """
    MONITORS CAN BUS CONNECTION HEALTH AND PROVIDES AUTO-RECONNECT
    Critical for production reliability
    """
    
    def __init__(self, ecu_communicator: ECUCommunicator):
        self.ecu_comm = ecu_communicator
        self.app_state = get_app_state()
        
        # Health monitoring
        self.metrics = ConnectionMetrics()
        self.health_status = ConnectionHealth.DISCONNECTED
        self.monitoring = False
        self.auto_reconnect_enabled = True
        
        # Threading
        self._lock = threading.RLock()
        self._monitor_thread = None
        self._shutdown_flag = threading.Event()
        
        # Configuration
        self.check_interval = 1.0  # seconds
        self.max_consecutive_failures = 5
        self.response_timeout = 2.0  # seconds
        self.reconnect_delay = 3.0  # seconds
        
        # Callbacks
        self.health_callbacks: List[Callable[[ConnectionHealth], None]] = []
        
        logger.info("Connection health monitor initialized")
    
    def start_monitoring(self):
        """Start connection health monitoring"""
        try:
            with self._lock:
                if self.monitoring:
                    logger.warning("Health monitoring already started")
                    return
                
                self.monitoring = True
                self._shutdown_flag.clear()
                self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self._monitor_thread.start()
                
                logger.info("Connection health monitoring started")
                
        except Exception as e:
            logger.error(f"Failed to start health monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop connection health monitoring"""
        try:
            with self._lock:
                if not self.monitoring:
                    return
                
                self.monitoring = False
                self._shutdown_flag.set()
                
                if self._monitor_thread and self._monitor_thread.is_alive():
                    self._monitor_thread.join(timeout=5.0)
                
                logger.info("Connection health monitoring stopped")
                
        except Exception as e:
            logger.error(f"Error stopping health monitoring: {e}")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while not self._shutdown_flag.is_set():
            try:
                self._check_connection_health()
                self._update_health_status()
                self._auto_reconnect_if_needed()
                
                # Sleep until next check
                self._shutdown_flag.wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")
                time.sleep(1.0)
    
    def _check_connection_health(self):
        """Check current connection health"""
        try:
            current_time = time.time()
            
            # Test connection with simple ping
            start_time = time.time()
            response = self.ecu_comm.send_request(0x10, 0x01, timeout=self.response_timeout)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            with self._lock:
                if response.success:
                    # Update success metrics
                    self.metrics.last_message_time = current_time
                    self.metrics.total_messages += 1
                    self.metrics.response_time_ms = response_time
                    self.metrics.consecutive_failures = 0
                    
                    # Calculate messages per second
                    if self.metrics.last_message_time > 0:
                        time_diff = current_time - self.metrics.last_message_time
                        if time_diff > 0:
                            self.metrics.messages_per_second = 1.0 / time_diff
                    
                    # Update error rate
                    if self.metrics.total_messages > 0:
                        self.metrics.error_rate = self.metrics.failed_messages / self.metrics.total_messages
                    
                else:
                    # Update failure metrics
                    self.metrics.failed_messages += 1
                    self.metrics.consecutive_failures += 1
                    
                    logger.warning(f"Connection test failed: {self.metrics.consecutive_failures} consecutive failures")
            
        except Exception as e:
            logger.error(f"Error checking connection health: {e}")
            with self._lock:
                self.metrics.consecutive_failures += 1
                self.metrics.failed_messages += 1
    
    def _update_health_status(self):
        """Update health status based on metrics"""
        try:
            with self._lock:
                old_status = self.health_status
                
                if self.metrics.consecutive_failures == 0:
                    if self.metrics.error_rate < 0.01 and self.metrics.response_time_ms < 100:
                        self.health_status = ConnectionHealth.EXCELLENT
                    elif self.metrics.error_rate < 0.05 and self.metrics.response_time_ms < 500:
                        self.health_status = ConnectionHealth.GOOD
                    else:
                        self.health_status = ConnectionHealth.POOR
                elif self.metrics.consecutive_failures >= self.max_consecutive_failures:
                    self.health_status = ConnectionHealth.DISCONNECTED
                else:
                    self.health_status = ConnectionHealth.ERROR
                
                # Notify callbacks if status changed
                if old_status != self.health_status:
                    self._notify_health_change(self.health_status)
                    logger.info(f"Connection health changed: {old_status.value} -> {self.health_status.value}")
            
        except Exception as e:
            logger.error(f"Error updating health status: {e}")
    
    def _auto_reconnect_if_needed(self):
        """Attempt auto-reconnect if connection is lost"""
        try:
            if (self.auto_reconnect_enabled and 
                self.health_status == ConnectionHealth.DISCONNECTED and
                self.ecu_comm.get_state() == ECUState.DISCONNECTED):
                
                logger.info("Attempting auto-reconnect...")
                
                # Wait before reconnect attempt
                time.sleep(self.reconnect_delay)
                
                # Try to reconnect
                if self.ecu_comm.connect():
                    logger.info("Auto-reconnect successful")
                    self.metrics.consecutive_failures = 0
                else:
                    logger.error("Auto-reconnect failed")
            
        except Exception as e:
            logger.error(f"Error during auto-reconnect: {e}")
    
    def _notify_health_change(self, health: ConnectionHealth):
        """Notify registered callbacks of health change"""
        for callback in self.health_callbacks:
            try:
                callback(health)
            except Exception as e:
                logger.error(f"Error in health callback: {e}")
    
    def register_health_callback(self, callback: Callable[[ConnectionHealth], None]):
        """Register callback for health changes"""
        with self._lock:
            self.health_callbacks.append(callback)
    
    def unregister_health_callback(self, callback: Callable[[ConnectionHealth], None]):
        """Unregister health callback"""
        with self._lock:
            if callback in self.health_callbacks:
                self.health_callbacks.remove(callback)
    
    def get_connection_metrics(self) -> ConnectionMetrics:
        """Get current connection metrics"""
        with self._lock:
            return self.metrics
    
    def get_health_status(self) -> ConnectionHealth:
        """Get current health status"""
        with self._lock:
            return self.health_status
    
    def enable_auto_reconnect(self, enabled: bool = True):
        """Enable or disable auto-reconnect"""
        with self._lock:
            self.auto_reconnect_enabled = enabled
            logger.info(f"Auto-reconnect {'enabled' if enabled else 'disabled'}")
    
    def force_health_check(self) -> bool:
        """Force immediate health check"""
        try:
            self._check_connection_health()
            self._update_health_status()
            return self.health_status in [ConnectionHealth.EXCELLENT, ConnectionHealth.GOOD]
        except Exception as e:
            logger.error(f"Error during forced health check: {e}")
            return False
