#!/usr/bin/env python3
"""
Flash Service - Independent flash operation management
Handles ECU flashing with connection resilience and rollback capabilities
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class FlashState(Enum):
    """Flash operation states"""
    IDLE = "idle"
    PREPARING = "preparing"
    BACKING_UP = "backing_up"
    VERIFYING_BACKUP = "verifying_backup"
    FLASHING = "flashing"
    VERIFYING_FLASH = "verifying_flash"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    ROLLING_BACK = "rolling_back"

@dataclass
class FlashOperation:
    """Flash operation data structure"""
    id: str
    tune_id: int
    tune_data: bytes
    state: FlashState
    progress: float
    message: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    backup_data: Optional[bytes] = None
    checksum: Optional[str] = None
    rollback_available: bool = False

class FlashService:
    """
    Independent flash service that handles ECU flashing operations
    with connection resilience and automatic rollback capabilities
    """
    
    def __init__(self, state_dir: str = "./flash_state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        self.current_operation: Optional[FlashOperation] = None
        self.operation_history: Dict[str, FlashOperation] = {}
        self.progress_callbacks: List[Callable[[FlashOperation], None]] = []
        self._flash_lock = asyncio.Lock()
        
        # Load existing state
        self._load_state()
        
        # Start background monitoring
        self._monitor_thread = None
        self._stop_monitoring = False
        self._start_monitoring()
    
    def add_progress_callback(self, callback: Callable[[FlashOperation], None]):
        """Add callback for progress updates"""
        self.progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[FlashOperation], None]):
        """Remove progress callback"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)
    
    def _notify_progress(self, operation: FlashOperation):
        """Notify all callbacks of progress update"""
        for callback in self.progress_callbacks:
            try:
                callback(operation)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    async def start_flash(self, tune_id: int, tune_data: bytes) -> str:
        """
        Start a new flash operation
        
        Args:
            tune_id: ID of tune to flash
            tune_data: ROM data to flash
            
        Returns:
            str: Operation ID
        """
        async with self._flash_lock:
            if self.current_operation and self.current_operation.state in [FlashState.PREPARING, FlashState.FLASHING]:
                raise Exception("Flash operation already in progress")
            
            # Create operation
            operation_id = f"flash_{int(time.time())}_{tune_id}"
            checksum = hashlib.sha256(tune_data).hexdigest()
            
            self.current_operation = FlashOperation(
                id=operation_id,
                tune_id=tune_id,
                tune_data=tune_data,
                state=FlashState.PREPARING,
                progress=0.0,
                message="Initializing flash operation...",
                started_at=datetime.now(),
                checksum=checksum
            )
            
            # Save initial state
            self._save_operation(self.current_operation)
            
            # Start flash in background
            asyncio.create_task(self._execute_flash(self.current_operation))
            
            return operation_id
    
    async def _execute_flash(self, operation: FlashOperation):
        """Execute flash operation with error handling and rollback"""
        try:
            logger.info(f"Starting flash operation {operation.id}")
            
            # Phase 1: Preparation
            await self._update_operation_state(operation, FlashState.PREPARING, 5.0, "Preparing flash operation...")
            await asyncio.sleep(0.5)  # Simulate preparation
            
            # Phase 2: Backup current ROM
            await self._update_operation_state(operation, FlashState.BACKING_UP, 10.0, "Backing up current ROM...")
            backup_data = await self._backup_current_rom()
            operation.backup_data = backup_data
            operation.rollback_available = True
            await asyncio.sleep(1.0)  # Simulate backup
            
            # Phase 3: Verify backup
            await self._update_operation_state(operation, FlashState.VERIFYING_BACKUP, 15.0, "Verifying backup integrity...")
            if not await self._verify_backup(backup_data):
                raise Exception("Backup verification failed")
            await asyncio.sleep(0.5)
            
            # Phase 4: Flash new tune
            await self._update_operation_state(operation, FlashState.FLASHING, 20.0, "Flashing new tune...")
            
            # Simulate flash progress
            for i in range(20, 80):
                if operation.state == FlashState.PAUSED:
                    logger.info(f"Flash operation {operation.id} paused")
                    await self._wait_for_resume(operation)
                
                if operation.state == FlashState.FAILED:
                    break
                
                await self._update_operation_state(operation, FlashState.FLASHING, float(i), 
                                                   f"Flashing... {i}%")
                await asyncio.sleep(0.1)
            
            if operation.state == FlashState.FAILED:
                return
            
            # Phase 5: Verify flash
            await self._update_operation_state(operation, FlashState.VERIFYING_FLASH, 85.0, "Verifying flash integrity...")
            if not await self._verify_flash(operation.tune_data):
                raise Exception("Flash verification failed")
            
            # Phase 6: Complete
            await self._update_operation_state(operation, FlashState.COMPLETED, 100.0, "Flash completed successfully!")
            operation.completed_at = datetime.now()
            
            logger.info(f"Flash operation {operation.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Flash operation {operation.id} failed: {e}")
            await self._update_operation_state(operation, FlashState.FAILED, operation.progress, 
                                               f"Flash failed: {str(e)}")
            operation.error = str(e)
            
            # Attempt rollback if backup available
            if operation.rollback_available and operation.backup_data:
                logger.info(f"Attempting rollback for operation {operation.id}")
                await self._rollback_flash(operation)
    
    async def _backup_current_rom(self) -> bytes:
        """Backup current ROM from ECU"""
        # Mock backup - in real implementation, read from ECU
        await asyncio.sleep(0.5)
        return b"MOCK_BACKUP_ROM_DATA_" + str(int(time.time())).encode()
    
    async def _verify_backup(self, backup_data: bytes) -> bool:
        """Verify backup integrity"""
        # Mock verification - in real implementation, verify checksums
        await asyncio.sleep(0.2)
        return len(backup_data) > 0
    
    async def _verify_flash(self, tune_data: bytes) -> bool:
        """Verify flashed ROM integrity"""
        # Mock verification - in real implementation, read back and verify
        await asyncio.sleep(0.5)
        return True
    
    async def _rollback_flash(self, operation: FlashOperation):
        """Rollback to backup ROM"""
        try:
            await self._update_operation_state(operation, FlashState.ROLLING_BACK, 90.0, "Rolling back to backup...")
            
            # Simulate rollback process
            for i in range(90, 100):
                await self._update_operation_state(operation, FlashState.ROLLING_BACK, float(i), 
                                                   f"Rolling back... {i-90}%")
                await asyncio.sleep(0.05)
            
            await self._update_operation_state(operation, FlashState.FAILED, 100.0, 
                                               "Flash failed - rolled back to backup")
            
        except Exception as e:
            logger.error(f"Rollback failed for operation {operation.id}: {e}")
            await self._update_operation_state(operation, FlashState.FAILED, 100.0, 
                                               f"Critical: Flash failed and rollback failed: {str(e)}")
    
    async def _update_operation_state(self, operation: FlashOperation, state: FlashState, 
                                     progress: float, message: str):
        """Update operation state and notify callbacks"""
        operation.state = state
        operation.progress = progress
        operation.message = message
        
        # Save state to disk
        self._save_operation(operation)
        
        # Notify callbacks
        self._notify_progress(operation)
    
    async def _wait_for_resume(self, operation: FlashOperation):
        """Wait for operation to be resumed"""
        while operation.state == FlashState.PAUSED:
            await asyncio.sleep(0.1)
    
    def pause_operation(self, operation_id: str) -> bool:
        """Pause a flash operation"""
        if self.current_operation and self.current_operation.id == operation_id:
            if self.current_operation.state in [FlashState.FLASHING, FlashState.PREPARING]:
                self.current_operation.state = FlashState.PAUSED
                self.current_operation.message = "Operation paused"
                self._save_operation(self.current_operation)
                self._notify_progress(self.current_operation)
                return True
        return False
    
    def resume_operation(self, operation_id: str) -> bool:
        """Resume a paused flash operation"""
        if self.current_operation and self.current_operation.id == operation_id:
            if self.current_operation.state == FlashState.PAUSED:
                self.current_operation.state = FlashState.FLASHING
                self.current_operation.message = "Operation resumed"
                self._save_operation(self.current_operation)
                self._notify_progress(self.current_operation)
                return True
        return False
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a flash operation"""
        if self.current_operation and self.current_operation.id == operation_id:
            if self.current_operation.state in [FlashState.PREPARING, FlashState.FLASHING, FlashState.PAUSED]:
                self.current_operation.state = FlashState.FAILED
                self.current_operation.error = "Operation cancelled by user"
                self.current_operation.message = "Operation cancelled"
                self._save_operation(self.current_operation)
                self._notify_progress(self.current_operation)
                return True
        return False
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a flash operation"""
        # Check current operation
        if self.current_operation and self.current_operation.id == operation_id:
            return self._operation_to_dict(self.current_operation)
        
        # Check history
        if operation_id in self.operation_history:
            return self._operation_to_dict(self.operation_history[operation_id])
        
        return None
    
    def get_all_operations(self) -> List[Dict[str, Any]]:
        """Get all flash operations"""
        operations = []
        
        if self.current_operation:
            operations.append(self._operation_to_dict(self.current_operation))
        
        operations.extend([self._operation_to_dict(op) for op in self.operation_history.values()])
        
        return operations
    
    def _operation_to_dict(self, operation: FlashOperation) -> Dict[str, Any]:
        """Convert operation to dictionary"""
        data = asdict(operation)
        data['state'] = operation.state.value
        if operation.started_at:
            data['started_at'] = operation.started_at.isoformat()
        if operation.completed_at:
            data['completed_at'] = operation.completed_at.isoformat()
        return data
    
    def _save_operation(self, operation: FlashOperation):
        """Save operation state to disk"""
        try:
            state_file = self.state_dir / f"{operation.id}.json"
            with open(state_file, 'w') as f:
                json.dump(self._operation_to_dict(operation), f, indent=2)
            
            # Update in-memory history
            self.operation_history[operation.id] = operation
            
        except Exception as e:
            logger.error(f"Failed to save operation state: {e}")
    
    def _load_state(self):
        """Load existing operation states from disk"""
        try:
            for state_file in self.state_dir.glob("*.json"):
                with open(state_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct operation
                operation = FlashOperation(
                    id=data['id'],
                    tune_id=data['tune_id'],
                    tune_data=bytes.fromhex(data.get('tune_data_hex', '')),
                    state=FlashState(data['state']),
                    progress=data['progress'],
                    message=data['message'],
                    error=data.get('error'),
                    checksum=data.get('checksum'),
                    rollback_available=data.get('rollback_available', False)
                )
                
                if data.get('started_at'):
                    operation.started_at = datetime.fromisoformat(data['started_at'])
                if data.get('completed_at'):
                    operation.completed_at = datetime.fromisoformat(data['completed_at'])
                
                # Check if this is a currently running operation
                if operation.state in [FlashState.PREPARING, FlashState.FLASHING, FlashState.PAUSED]:
                    self.current_operation = operation
                    logger.warning(f"Resumed interrupted flash operation: {operation.id}")
                    # Resume the operation
                    asyncio.create_task(self._execute_flash(operation))
                else:
                    self.operation_history[operation.id] = operation
                    
        except Exception as e:
            logger.error(f"Failed to load flash state: {e}")
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while not self._stop_monitoring:
            try:
                # Check for stale operations and cleanup
                current_time = datetime.now()
                
                # Clean up old completed operations (older than 24 hours)
                stale_operations = []
                for op_id, operation in self.operation_history.items():
                    if (operation.state in [FlashState.COMPLETED, FlashState.FAILED] and 
                        operation.completed_at and 
                        (current_time - operation.completed_at).days >= 1):
                        stale_operations.append(op_id)
                
                for op_id in stale_operations:
                    del self.operation_history[op_id]
                    try:
                        (self.state_dir / f"{op_id}.json").unlink()
                    except:
                        pass
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(60)
    
    def cleanup(self):
        """Cleanup resources"""
        self._stop_monitoring = True
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)

# Global flash service instance
flash_service = FlashService()

# WebSocket integration
def get_flash_status_for_websocket() -> Dict[str, Any]:
    """Get flash status formatted for WebSocket broadcast"""
    if flash_service.current_operation:
        return {
            "type": "flash_status",
            "operation": flash_service.get_operation_status(flash_service.current_operation.id)
        }
    return {"type": "flash_status", "operation": None}

# Add progress callback for WebSocket broadcasting
def flash_progress_websocket_callback(operation: FlashOperation):
    """Callback to broadcast flash progress via WebSocket"""
    from main import manager
    try:
        message = get_flash_status_for_websocket()
        asyncio.create_task(manager.broadcast(json.dumps(message)))
    except:
        pass

# Register callback
flash_service.add_progress_callback(flash_progress_websocket_callback)
