#!/usr/bin/env python3
"""
Forensic Replay Engine
View-only reconstruction of diagnostic sessions
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from muts.models.database_models import db
from muts.models.forensic_models import ForensicSession, ForensicEvent

logger = logging.getLogger(__name__)


class ForensicReplayEngine:
    """Replays diagnostic sessions for forensic analysis"""
    
    def __init__(self):
        self.current_session: Optional[ForensicSession] = None
        self.current_events: List[ForensicEvent] = []
        self.current_position: int = 0
    
    def load_session(self, session_hash: str) -> Dict[str, Any]:
        """
        Load a forensic session for replay
        
        Returns:
            Session data with events or error
        """
        try:
            # Get session
            session = db.session.query(ForensicSession).filter_by(
                session_hash=session_hash
            ).first()
            
            if not session:
                return {
                    'error': 'Session not found',
                    'session_hash': session_hash
                }
            
            # Get events
            events = session.events.order_by(ForensicEvent.sequence_number).all()
            
            # Verify integrity
            if not self._verify_session_integrity(session):
                logger.warning(f"Session integrity check failed: {session_hash}")
                return {
                    'error': 'Session integrity compromised',
                    'session_hash': session_hash
                }
            
            # Set current session
            self.current_session = session
            self.current_events = events
            self.current_position = 0
            
            # Build session summary
            summary = self._build_session_summary(session, events)
            
            return {
                'session': session.to_dict(),
                'events': [e.to_dict() for e in events],
                'summary': summary,
                'position': 0,
                'total_events': len(events)
            }
            
        except Exception as e:
            logger.error(f"Failed to load session {session_hash}: {e}")
            return {
                'error': str(e),
                'session_hash': session_hash
            }
    
    def get_session_list(self, admin_user_id: int = None, vehicle_vin: str = None,
                        start_date: datetime = None, end_date: datetime = None,
                        page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """
        Get list of forensic sessions with filtering
        """
        try:
            # Build query
            query = db.session.query(ForensicSession)
            
            # Apply filters
            if admin_user_id:
                query = query.filter(ForensicSession.admin_user_id == admin_user_id)
            
            if vehicle_vin:
                query = query.filter(ForensicSession.vehicle_vin == vehicle_vin)
            
            if start_date:
                query = query.filter(ForensicSession.started_at >= start_date)
            
            if end_date:
                query = query.filter(ForensicSession.started_at <= end_date)
            
            # Order by most recent
            query = query.order_by(ForensicSession.started_at.desc())
            
            # Paginate
            total = query.count()
            sessions = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Build response
            session_list = []
            for session in sessions:
                session_data = session.to_dict()
                session_data['integrity_valid'] = self._verify_session_integrity(session)
                session_list.append(session_data)
            
            return {
                'sessions': session_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get session list: {e}")
            return {
                'error': str(e),
                'sessions': []
            }
    
    def get_event_at_position(self, position: int) -> Dict[str, Any]:
        """Get event at specific position in current session"""
        if not self.current_session or position < 0 or position >= len(self.current_events):
            return {'error': 'Invalid position'}
        
        event = self.current_events[position]
        context = self._get_event_context(event)
        
        return {
            'event': event.to_dict(include_sensitive=False),
            'context': context,
            'position': position,
            'total': len(self.current_events)
        }
    
    def get_session_timeline(self) -> List[Dict[str, Any]]:
        """Get timeline summary of current session"""
        if not self.current_session:
            return []
        
        timeline = []
        for event in self.current_events:
            timeline.append({
                'sequence': event.sequence_number,
                'timestamp': event.timestamp.isoformat(),
                'type': event.event_type,
                'module': event.module,
                'service': event.service,
                'execution_mode': event.execution_mode,
                'result': event.result_status,
                'override_active': event.override_active
            })
        
        return timeline
    
    def analyze_session(self, session_hash: str = None) -> Dict[str, Any]:
        """Analyze session for patterns and issues"""
        try:
            # Use current session if none provided
            if session_hash:
                result = self.load_session(session_hash)
                if 'error' in result:
                    return result
            elif not self.current_session:
                return {'error': 'No session loaded'}
            
            # Analyze events
            analysis = {
                'total_events': len(self.current_events),
                'execution_modes': {},
                'modules_accessed': {},
                'services_used': {},
                'override_usage': {
                    'active': False,
                    'scope': None,
                    'events_with_override': 0
                },
                'dry_run_events': 0,
                'blocked_actions': 0,
                'write_operations': 0,
                'errors': 0,
                'duration': None
            }
            
            # Process events
            if self.current_events:
                start_time = self.current_events[0].timestamp
                end_time = self.current_events[-1].timestamp
                analysis['duration'] = str(end_time - start_time)
                
                for event in self.current_events:
                    # Count execution modes
                    mode = event.execution_mode
                    analysis['execution_modes'][mode] = analysis['execution_modes'].get(mode, 0) + 1
                    
                    # Count modules
                    if event.module:
                        analysis['modules_accessed'][event.module] = \
                            analysis['modules_accessed'].get(event.module, 0) + 1
                    
                    # Count services
                    if event.service:
                        analysis['services_used'][event.service] = \
                            analysis['services_used'].get(event.service, 0) + 1
                    
                    # Override usage
                    if event.override_active:
                        analysis['override_usage']['active'] = True
                        analysis['override_usage']['scope'] = event.override_scope
                        analysis['override_usage']['events_with_override'] += 1
                    
                    # Special counts
                    if event.execution_mode == 'DRY_RUN':
                        analysis['dry_run_events'] += 1
                    elif event.result_status == 'BLOCKED':
                        analysis['blocked_actions'] += 1
                    
                    # Write operations
                    write_services = ['CLEAR_DTCS', 'CODING', 'ADAPTATION', 'ACTUATION_TESTS']
                    if event.service in write_services:
                        analysis['write_operations'] += 1
                    
                    # Errors
                    if event.result_status == 'FAILURE' or event.error_message:
                        analysis['errors'] += 1
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze session: {e}")
            return {'error': str(e)}
    
    def export_session(self, session_hash: str, format: str = 'json',
                      include_sensitive: bool = False) -> Dict[str, Any]:
        """Export session data in specified format"""
        try:
            # Load session
            result = self.load_session(session_hash)
            if 'error' in result:
                return result
            
            # Export based on format
            if format.lower() == 'json':
                return {
                    'format': 'json',
                    'data': result,
                    'exported_at': datetime.utcnow().isoformat()
                }
            
            elif format.lower() == 'csv':
                # Convert to CSV format
                csv_data = []
                headers = [
                    'Sequence', 'Timestamp', 'Event Type', 'Module', 'Service',
                    'Execution Mode', 'Capability Supported', 'Override Active',
                    'Result Status', 'UI Action', 'Error Message'
                ]
                
                csv_data.append(headers)
                
                for event in self.current_events:
                    row = [
                        event.sequence_number,
                        event.timestamp.isoformat(),
                        event.event_type,
                        event.module or '',
                        event.service or '',
                        event.execution_mode,
                        'Yes' if event.capability_supported else 'No',
                        'Yes' if event.override_active else 'No',
                        event.result_status,
                        event.ui_action or '',
                        event.error_message or ''
                    ]
                    csv_data.append(row)
                
                return {
                    'format': 'csv',
                    'data': csv_data,
                    'exported_at': datetime.utcnow().isoformat()
                }
            
            elif format.lower() == 'report':
                # Human-readable report
                report = self._generate_report(result)
                return {
                    'format': 'report',
                    'data': report,
                    'exported_at': datetime.utcnow().isoformat()
                }
            
            else:
                return {'error': f'Unsupported format: {format}'}
                
        except Exception as e:
            logger.error(f"Failed to export session: {e}")
            return {'error': str(e)}
    
    def _verify_session_integrity(self, session: ForensicSession) -> bool:
        """Verify session integrity hash"""
        try:
            if not session.integrity_hash:
                return False
            
            calculated = session.calculate_integrity()
            return calculated == session.integrity_hash
            
        except Exception as e:
            logger.error(f"Failed to verify integrity: {e}")
            return False
    
    def _build_session_summary(self, session: ForensicSession, events: List[ForensicEvent]) -> Dict[str, Any]:
        """Build session summary statistics"""
        summary = {
            'total_events': len(events),
            'session_type': session.session_type,
            'was_dry_run': session.was_dry_run,
            'override_scope': session.override_scope,
            'duration': None,
            'modules_accessed': set(),
            'services_used': set(),
            'execution_modes': set(),
            'has_errors': False,
            'has_overrides': False
        }
        
        if events:
            start_time = events[0].timestamp
            end_time = events[-1].timestamp
            summary['duration'] = str(end_time - start_time)
            
            for event in events:
                if event.module:
                    summary['modules_accessed'].add(event.module)
                if event.service:
                    summary['services_used'].add(event.service)
                summary['execution_modes'].add(event.execution_mode)
                
                if event.result_status == 'FAILURE' or event.error_message:
                    summary['has_errors'] = True
                
                if event.override_active:
                    summary['has_overrides'] = True
            
            # Convert sets to lists
            summary['modules_accessed'] = list(summary['modules_accessed'])
            summary['services_used'] = list(summary['services_used'])
            summary['execution_modes'] = list(summary['execution_modes'])
        
        return summary
    
    def _get_event_context(self, event: ForensicEvent) -> Dict[str, Any]:
        """Get context information for an event"""
        context = {
            'previous_event': None,
            'next_event': None,
            'session_progress': None
        }
        
        if self.current_events:
            # Find position
            position = -1
            for i, e in enumerate(self.current_events):
                if e.id == event.id:
                    position = i
                    break
            
            if position >= 0:
                context['session_progress'] = f"{position + 1}/{len(self.current_events)}"
                
                # Previous event
                if position > 0:
                    context['previous_event'] = self.current_events[position - 1].to_dict()
                
                # Next event
                if position < len(self.current_events) - 1:
                    context['next_event'] = self.current_events[position + 1].to_dict()
        
        return context
    
    def _generate_report(self, session_data: Dict[str, Any]) -> str:
        """Generate human-readable report"""
        report = []
        report.append("=" * 60)
        report.append("FORENSIC SESSION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Session info
        session = session_data['session']
        report.append("SESSION INFORMATION:")
        report.append(f"  Hash: {session['session_hash']}")
        report.append(f"  Admin: {session['admin_username']}")
        report.append(f"  Vehicle: {session['vehicle_profile']}")
        report.append(f"  Started: {session['started_at']}")
        report.append(f"  Ended: {session['ended_at']}")
        report.append(f"  Type: {session['session_type']}")
        report.append(f"  Override Scope: {session['override_scope']}")
        report.append("")
        
        # Summary
        summary = session_data['summary']
        report.append("SESSION SUMMARY:")
        report.append(f"  Total Events: {summary['total_events']}")
        report.append(f"  Duration: {summary['duration']}")
        report.append(f"  Modules Accessed: {', '.join(summary['modules_accessed'])}")
        report.append(f"  Services Used: {', '.join(summary['services_used'])}")
        report.append(f"  Execution Modes: {', '.join(summary['execution_modes'])}")
        report.append(f"  Had Errors: {summary['has_errors']}")
        report.append(f"  Had Overrides: {summary['has_overrides']}")
        report.append("")
        
        # Event timeline
        report.append("EVENT TIMELINE:")
        for event in session_data['events']:
            report.append(f"  [{event['sequence_number']}] {event['timestamp']}")
            report.append(f"      Type: {event['event_type']}")
            report.append(f"      Module: {event['module'] or 'N/A'}")
            report.append(f"      Service: {event['service'] or 'N/A'}")
            report.append(f"      Mode: {event['execution_mode']}")
            report.append(f"      Result: {event['result_status']}")
            if event['error_message']:
                report.append(f"      Error: {event['error_message']}")
            report.append("")
        
        report.append("=" * 60)
        report.append("END OF REPORT")
        report.append("=" * 60)
        
        return "\n".join(report)


# Global forensic replay engine instance
forensic_replay_engine = ForensicReplayEngine()
