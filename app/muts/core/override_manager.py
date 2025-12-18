#!/usr/bin/env python3
"""
Admin Override Manager
Handles admin-only diagnostic overrides with safety and logging
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Set
from enum import Enum
from dataclasses import dataclass
from muts.models.database_models import db, User
from muts.models.override_models import OverrideAuditLog
from muts.models.diagnostics_template import DiagnosticModule, DiagnosticService
from muts.core.forensic_recorder import forensic_recorder

logger = logging.getLogger(__name__)


class OverrideScope(Enum):
    """Override scope types"""
    ACTION = "ACTION"      # Single diagnostics action
    MODULE = "MODULE"      # One ECU/module for time limit
    SESSION = "SESSION"    # Current session only


@dataclass
class ActiveOverride:
    """Represents an active override"""
    admin_id: int
    scope: OverrideScope
    module: Optional[DiagnosticModule]
    action: Optional[DiagnosticService]
    expires_at: Optional[datetime]
    reason: str
    session_id: str


class OverrideManager:
    """Manages admin-only diagnostic overrides"""
    
    def __init__(self):
        # Active overrides stored in memory (auto-clear on restart)
        self._active_overrides: Dict[str, ActiveOverride] = {}  # key: session_id or admin_id
        
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        user = db.session.query(User).get(user_id)
        return user and user.role.lower() == 'admin'
    
    def can_override(self, user_id: int, module: DiagnosticModule, 
                    service: DiagnosticService, session_id: str) -> Tuple[bool, str]:
        """
        Check if admin can override for this module/service
        
        Returns:
            (can_override, reason)
        """
        # Check admin role
        if not self.is_admin(user_id):
            return False, "Admin privileges required"
        
        # Check for active overrides
        override = self._get_active_override(user_id, session_id, module, service)
        if override:
            # Validate override hasn't expired
            if override.expires_at and datetime.utcnow() > override.expires_at:
                self._revoke_override(user_id, session_id)
                return False, "Override expired"
            
            # Check scope validity
            if override.scope == OverrideScope.ACTION:
                if override.action != service:
                    return False, "Action override not valid for this service"
            elif override.scope == OverrideScope.MODULE:
                if override.module != module:
                    return False, "Module override not valid for this module"
            # SESSION scope allows anything
            
            return True, f"Override active: {override.reason}"
        
        return False, "No active override"
    
    def activate_override(self, user_id: int, scope: OverrideScope,
                        module: Optional[DiagnosticModule] = None,
                        action: Optional[DiagnosticService] = None,
                        reason: str = "", duration_minutes: int = 5,
                        session_id: str = "", vehicle_profile: str = "") -> bool:
        """
        Activate an admin override
        
        Returns:
            True if override activated, False if failed
        """
        # Validate admin
        if not self.is_admin(user_id):
            logger.error(f"Non-admin user {user_id} attempted override activation")
            return False
        
        # Validate scope requirements
        if scope == OverrideScope.MODULE and not module:
            logger.error("Module override requires module parameter")
            return False
        
        if scope == OverrideScope.ACTION and (not module or not action):
            logger.error("Action override requires module and action parameters")
            return False
        
        # Calculate expiration
        expires_at = None
        if scope == OverrideScope.MODULE:
            expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
        elif scope == OverrideScope.SESSION:
            expires_at = None  # Expires on session end
        
        # Create override
        override_key = f"{user_id}_{session_id}" if session_id else str(user_id)
        self._active_overrides[override_key] = ActiveOverride(
            admin_id=user_id,
            scope=scope,
            module=module,
            action=action,
            expires_at=expires_at,
            reason=reason,
            session_id=session_id
        )
        
        # Start forensic session for admin overrides
        forensic_session_hash = forensic_recorder.start_forensic_session(
            session_id=session_id,
            admin_user_id=user_id,
            vehicle_profile=vehicle_profile,
            override_scope=scope.value,
            override_reason=reason,
            is_dry_run=False
        )
        
        # Log activation
        self._log_override(
            admin_user_id=user_id,
            scope=scope.value,
            module=module.value if module else None,
            action=action.value if action else None,
            reason=f"ACTIVATED: {reason}",
            duration_minutes=duration_minutes,
            result="SUCCESS",
            session_id=session_id,
            vehicle_profile=vehicle_profile
        )
        
        logger.warning(f"Admin override activated: user={user_id}, scope={scope.value}, "
                      f"module={module.value if module else 'None'}, reason={reason}")
        
        return True
    
    def revoke_override(self, user_id: int, session_id: str = "") -> bool:
        """Revoke active override"""
        revoked = self._revoke_override(user_id, session_id)
        
        # End forensic session if override was active
        if revoked:
            forensic_recorder.end_forensic_session(session_id or str(user_id))
        
        return revoked
    
    def revoke_all_overrides(self) -> int:
        """Revoke all active overrides (e.g., on disconnect)"""
        count = len(self._active_overrides)
        self._active_overrides.clear()
        logger.info(f"Revoked all {count} active overrides")
        return count
    
    def get_active_overrides(self, user_id: int = None) -> Dict[str, ActiveOverride]:
        """Get active overrides (all or for specific user)"""
        if user_id:
            return {k: v for k, v in self._active_overrides.items() if v.admin_id == user_id}
        return self._active_overrides.copy()
    
    def log_execution(self, admin_user_id: int, module: DiagnosticModule,
                     action: DiagnosticService, result: str, error: str = "",
                     session_id: str = "", vehicle_vin: str = "",
                     vehicle_profile: str = ""):
        """Log execution of overridden action"""
        override = self._get_active_override(admin_user_id, session_id, module, action)
        if not override:
            return
        
        self._log_override(
            admin_user_id=admin_user_id,
            scope=override.scope.value,
            module=module.value,
            action=action.value,
            reason=f"EXECUTED: {override.reason}",
            result=result,
            error_message=error,
            session_id=session_id,
            vehicle_vin=vehicle_vin,
            vehicle_profile=vehicle_profile
        )
    
    def _get_active_override(self, user_id: int, session_id: str,
                           module: DiagnosticModule, service: DiagnosticService) -> Optional[ActiveOverride]:
        """Get applicable active override"""
        # Check session-specific override first
        if session_id:
            session_key = f"{user_id}_{session_id}"
            if session_key in self._active_overrides:
                override = self._active_overrides[session_key]
                if self._override_applies(override, module, service):
                    return override
        
        # Check user-level override
        user_key = str(user_id)
        if user_key in self._active_overrides:
            override = self._active_overrides[user_key]
            if self._override_applies(override, module, service):
                return override
        
        return None
    
    def _override_applies(self, override: ActiveOverride, module: DiagnosticModule,
                         service: DiagnosticService) -> bool:
        """Check if override applies to module/service"""
        if override.scope == OverrideScope.SESSION:
            return True
        elif override.scope == OverrideScope.MODULE:
            return override.module == module
        elif override.scope == OverrideScope.ACTION:
            return override.module == module and override.action == service
        return False
    
    def _revoke_override(self, user_id: int, session_id: str = "") -> bool:
        """Internal revoke method"""
        revoked = False
        
        # Revoke session-specific
        if session_id:
            session_key = f"{user_id}_{session_id}"
            if session_key in self._active_overrides:
                override = self._active_overrides[session_key]
                del self._active_overrides[session_key]
                self._log_override(
                    admin_user_id=user_id,
                    scope=override.scope.value,
                    module=override.module.value if override.module else None,
                    action=override.action.value if override.action else None,
                    reason=f"REVOKED: {override.reason}",
                    result="SUCCESS",
                    session_id=session_id
                )
                revoked = True
        
        # Revoke user-level
        user_key = str(user_id)
        if user_key in self._active_overrides:
            override = self._active_overrides[user_key]
            del self._active_overrides[user_key]
            self._log_override(
                admin_user_id=user_id,
                scope=override.scope.value,
                module=override.module.value if override.module else None,
                action=override.action.value if override.action else None,
                reason=f"REVOKED: {override.reason}",
                result="SUCCESS",
                session_id=session_id
            )
            revoked = True
        
        if revoked:
            logger.info(f"Admin override revoked: user={user_id}")
        
        return revoked
    
    def _log_override(self, admin_user_id: int, scope: str, module: str = None,
                     action: str = None, reason: str = "", duration_minutes: int = None,
                     result: str = "", error_message: str = "", session_id: str = "",
                     vehicle_vin: str = "", vehicle_profile: str = ""):
        """Log override activity to database"""
        try:
            log = OverrideAuditLog(
                admin_user_id=admin_user_id,
                vehicle_vin=vehicle_vin,
                vehicle_profile=vehicle_profile,
                override_scope=scope,
                module=module,
                action=action,
                reason=reason,
                duration_minutes=duration_minutes,
                result=result,
                error_message=error_message,
                session_id=session_id
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log override activity: {e}")
            db.session.rollback()


# Global override manager instance
override_manager = OverrideManager()
