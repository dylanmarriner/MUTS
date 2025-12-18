#!/usr/bin/env python3
"""
Forensic Recorder for Diagnostic Sessions
Captures complete timeline of admin override sessions
"""

import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from muts.models.database_models import db
from muts.models.forensic_models import ForensicSession, ForensicEvent, DryRunSession
from muts.models.diagnostics_template import DiagnosticModule, DiagnosticService

logger = logging.getLogger(__name__)


class ForensicRecorder:
    """Records diagnostic sessions for forensic analysis"""
    
    def __init__(self):
        self.active_sessions: Dict[str, int] = {}  # session_id -> forensic_session_id
        self.active_dry_runs: Dict[str, int] = {}  # session_id -> dry_run_session_id
    
    def start_forensic_session(self, session_id: str, admin_user_id: int,
                             vehicle_vin: str = None, vehicle_profile: str = None,
                             override_scope: str = None, override_reason: str = None,
                             is_dry_run: bool = False) -> str:
        """
        Start a new forensic recording session
        
        Returns:
            Session hash for identification
        """
        try:
            # Create session hash
            hash_input = f"{session_id}:{admin_user_id}:{datetime.utcnow().isoformat()}"
            session_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            # Create forensic session
            forensic_session = ForensicSession(
                session_hash=session_hash,
                session_id=session_id,
                admin_user_id=admin_user_id,
                vehicle_vin=vehicle_vin,
                vehicle_profile=vehicle_profile,
                override_scope=override_scope,
                override_reason=override_reason,
                session_type='DRY_RUN' if is_dry_run else 'OVERRIDE',
                was_dry_run=is_dry_run
            )
            
            db.session.add(forensic_session)
            db.session.commit()
            
            # Track active session
            self.active_sessions[session_id] = forensic_session.id
            
            # Log session start
            self._record_event(
                session_id=forensic_session.id,
                event_type='SESSION_START',
                module=None,
                service=None,
                execution_mode='DRY_RUN' if is_dry_run else 'LIVE',
                result_status='SUCCESS',
                ui_action='Session started',
                ui_context=json.dumps({
                    'override_scope': override_scope,
                    'override_reason': override_reason,
                    'vehicle_profile': vehicle_profile
                })
            )
            
            logger.info(f"Forensic session started: {session_hash}")
            return session_hash
            
        except Exception as e:
            logger.error(f"Failed to start forensic session: {e}")
            db.session.rollback()
            return None
    
    def end_forensic_session(self, session_id: str):
        """End a forensic recording session"""
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"No active forensic session for {session_id}")
                return
            
            forensic_session_id = self.active_sessions[session_id]
            forensic_session = db.session.query(ForensicSession).get(forensic_session_id)
            
            if forensic_session:
                forensic_session.ended_at = datetime.utcnow()
                forensic_session.event_count = forensic_session.events.count()
                forensic_session.integrity_hash = forensic_session.calculate_integrity()
                db.session.commit()
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"Forensic session ended: {forensic_session.session_hash}")
            
        except Exception as e:
            logger.error(f"Failed to end forensic session: {e}")
            db.session.rollback()
    
    def record_diagnostic_action(self, session_id: str, module: DiagnosticModule,
                               service: DiagnosticService, capability_supported: bool,
                               capability_reason: str, override_active: bool = False,
                               override_scope: str = None, override_reason: str = None,
                               execution_mode: str = 'LIVE', would_execute: bool = True,
                               command_payload: str = None, command_response: str = None,
                               result_status: str = 'SUCCESS', result_data: Dict = None,
                               error_message: str = None, ui_action: str = None):
        """Record a diagnostic action in the forensic timeline"""
        try:
            if session_id not in self.active_sessions:
                logger.warning(f"No active forensic session for {session_id}")
                return
            
            forensic_session_id = self.active_sessions[session_id]
            
            # Serialize result data
            result_json = json.dumps(result_data) if result_data else None
            
            # Record the event
            self._record_event(
                session_id=forensic_session_id,
                event_type='DIAGNOSTIC',
                module=module.value if module else None,
                service=service.value if service else None,
                capability_supported=capability_supported,
                capability_reason=capability_reason,
                override_active=override_active,
                override_scope=override_scope,
                override_reason=override_reason,
                execution_mode=execution_mode,
                would_execute=would_execute,
                command_payload=command_payload,
                command_response=command_response,
                result_status=result_status,
                result_data=result_json,
                error_message=error_message,
                ui_action=ui_action
            )
            
        except Exception as e:
            logger.error(f"Failed to record diagnostic action: {e}")
    
    def start_dry_run_session(self, session_id: str, user_id: int, vehicle_profile: str = None):
        """Start tracking a dry-run session"""
        try:
            dry_run = DryRunSession(
                session_id=session_id,
                user_id=user_id,
                vehicle_profile=vehicle_profile,
                is_active=True
            )
            
            db.session.add(dry_run)
            db.session.commit()
            
            self.active_dry_runs[session_id] = dry_run.id
            logger.info(f"Dry-run session started: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to start dry-run session: {e}")
            db.session.rollback()
    
    def end_dry_run_session(self, session_id: str):
        """End a dry-run session"""
        try:
            if session_id not in self.active_dry_runs:
                return
            
            dry_run_id = self.active_dry_runs[session_id]
            dry_run = db.session.query(DryRunSession).get(dry_run_id)
            
            if dry_run:
                dry_run.is_active = False
                dry_run.ended_at = datetime.utcnow()
                db.session.commit()
            
            del self.active_dry_runs[session_id]
            logger.info(f"Dry-run session ended: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to end dry-run session: {e}")
            db.session.rollback()
    
    def update_dry_run_stats(self, session_id: str, attempted: int = 0,
                           blocked: int = 0, writes_prevented: int = 0):
        """Update dry-run session statistics"""
        try:
            if session_id not in self.active_dry_runs:
                return
            
            dry_run_id = self.active_dry_runs[session_id]
            dry_run = db.session.query(DryRunSession).get(dry_run_id)
            
            if dry_run:
                dry_run.actions_attempted += attempted
                dry_run.actions_blocked += blocked
                dry_run.writes_prevented += writes_prevented
                db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update dry-run stats: {e}")
            db.session.rollback()
    
    def _record_event(self, session_id: int, event_type: str, module: str = None,
                     service: str = None, capability_supported: bool = None,
                     capability_reason: str = None, override_active: bool = False,
                     override_scope: str = None, override_reason: str = None,
                     execution_mode: str = 'LIVE', would_execute: bool = True,
                     command_payload: str = None, command_response: str = None,
                     result_status: str = 'SUCCESS', result_data: str = None,
                     error_message: str = None, ui_action: str = None,
                     ui_context: str = None):
        """Record an individual forensic event"""
        try:
            # Get next sequence number
            last_event = db.session.query(ForensicEvent).filter_by(
                session_id=session_id
            ).order_by(ForensicEvent.sequence_number.desc()).first()
            
            sequence_number = (last_event.sequence_number + 1) if last_event else 1
            
            # Create event
            event = ForensicEvent(
                session_id=session_id,
                sequence_number=sequence_number,
                event_type=event_type,
                module=module,
                service=service,
                capability_supported=capability_supported,
                capability_reason=capability_reason,
                override_active=override_active,
                override_scope=override_scope,
                override_reason=override_reason,
                execution_mode=execution_mode,
                would_execute=would_execute,
                command_payload=command_payload,
                command_response=command_response,
                result_status=result_status,
                result_data=result_data,
                error_message=error_message,
                ui_action=ui_action,
                ui_context=ui_context
            )
            
            # Calculate and set event hash
            event.event_hash = event.calculate_hash()
            
            db.session.add(event)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to record forensic event: {e}")
            db.session.rollback()
    
    def get_session_events(self, session_hash: str, include_sensitive: bool = False):
        """Get all events for a forensic session"""
        try:
            session = db.session.query(ForensicSession).filter_by(
                session_hash=session_hash
            ).first()
            
            if not session:
                return None
            
            events = session.events.all()
            return {
                'session': session.to_dict(),
                'events': [e.to_dict(include_sensitive) for e in events]
            }
            
        except Exception as e:
            logger.error(f"Failed to get session events: {e}")
            return None
    
    def verify_session_integrity(self, session_hash: str) -> bool:
        """Verify the integrity of a forensic session"""
        try:
            session = db.session.query(ForensicSession).filter_by(
                session_hash=session_hash
            ).first()
            
            if not session:
                return False
            
            # Recalculate integrity hash
            calculated_hash = session.calculate_integrity()
            
            return calculated_hash == session.integrity_hash
            
        except Exception as e:
            logger.error(f"Failed to verify session integrity: {e}")
            return False


# Global forensic recorder instance
forensic_recorder = ForensicRecorder()
