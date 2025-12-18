#!/usr/bin/env python3
"""
Admin Override API Endpoints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from muts.core.override_manager import override_manager, OverrideScope
from muts.models.diagnostics_template import DiagnosticModule, DiagnosticService
from muts.models.database_models import db, User
from muts.models.override_models import OverrideAuditLog

override_bp = Blueprint('admin_overrides', __name__)

@override_bp.route('/admin/overrides/activate', methods=['POST'])
@jwt_required()
def activate_override():
    """Activate an admin override"""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user = db.session.query(User).get(current_user_id)
        
        # Verify admin role
        if not user or user.role.lower() != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        scope_str = data.get('scope')
        reason = data.get('reason', '').strip()
        
        if not scope_str:
            return jsonify({'error': 'Override scope required'}), 400
        
        if not reason:
            return jsonify({'error': 'Override reason required'}), 400
        
        # Parse scope
        try:
            scope = OverrideScope(scope_str.upper())
        except ValueError:
            return jsonify({'error': f'Invalid scope: {scope_str}'}), 400
        
        # Parse module and action if provided
        module = None
        action = None
        
        if scope in [OverrideScope.MODULE, OverrideScope.ACTION]:
            module_str = data.get('module')
            if not module_str:
                return jsonify({'error': 'Module required for this scope'}), 400
            
            try:
                module = DiagnosticModule(module_str.upper())
            except ValueError:
                return jsonify({'error': f'Invalid module: {module_str}'}), 400
        
        if scope == OverrideScope.ACTION:
            action_str = data.get('action')
            if not action_str:
                return jsonify({'error': 'Action required for action scope'}), 400
            
            try:
                action = DiagnosticService(action_str.upper())
            except ValueError:
                return jsonify({'error': f'Invalid action: {action_str}'}), 400
        
        # Get duration and session info
        duration = data.get('duration_minutes', 5)
        session_id = data.get('session_id', '')
        vehicle_profile = data.get('vehicle_profile', '')
        
        # Activate override
        success = override_manager.activate_override(
            user_id=current_user_id,
            scope=scope,
            module=module,
            action=action,
            reason=reason,
            duration_minutes=duration,
            session_id=session_id,
            vehicle_profile=vehicle_profile
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Override activated',
                'scope': scope.value,
                'module': module.value if module else None,
                'action': action.value if action else None,
                'duration_minutes': duration if scope == OverrideScope.MODULE else None
            })
        else:
            return jsonify({'error': 'Failed to activate override'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@override_bp.route('/admin/overrides/revoke', methods=['POST'])
@jwt_required()
def revoke_override():
    """Revoke an admin override"""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user = db.session.query(User).get(current_user_id)
        
        # Verify admin role
        if not user or user.role.lower() != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        data = request.get_json()
        session_id = data.get('session_id', '')
        
        # Revoke override
        success = override_manager.revoke_override(current_user_id, session_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Override revoked'
            })
        else:
            return jsonify({'error': 'No active override to revoke'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@override_bp.route('/admin/overrides/active', methods=['GET'])
@jwt_required()
def get_active_overrides():
    """Get active overrides for current admin"""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user = db.session.query(User).get(current_user_id)
        
        # Verify admin role
        if not user or user.role.lower() != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Get active overrides
        overrides = override_manager.get_active_overrides(current_user_id)
        
        # Format response
        result = []
        for key, override in overrides.items():
            override_data = {
                'key': key,
                'scope': override.scope.value,
                'module': override.module.value if override.module else None,
                'action': override.action.value if override.action else None,
                'expires_at': override.expires_at.isoformat() if override.expires_at else None,
                'reason': override.reason,
                'session_id': override.session_id
            }
            result.append(override_data)
        
        return jsonify({
            'overrides': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@override_bp.route('/admin/overrides/audit', methods=['GET'])
@jwt_required()
def get_audit_logs():
    """Get override audit logs"""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user = db.session.query(User).get(current_user_id)
        
        # Verify admin role
        if not user or user.role.lower() != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # Build query
        query = db.session.query(OverrideAuditLog).order_by(OverrideAuditLog.created_at.desc())
        
        # Apply filters
        admin_id = request.args.get('admin_id', type=int)
        if admin_id:
            query = query.filter(OverrideAuditLog.admin_user_id == admin_id)
        
        scope = request.args.get('scope')
        if scope:
            query = query.filter(OverrideAuditLog.override_scope == scope.upper())
        
        module = request.args.get('module')
        if module:
            query = query.filter(OverrideAuditLog.module == module.upper())
        
        # Paginate
        total = query.count()
        logs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format response
        result = {
            'logs': [log.to_dict() for log in logs],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@override_bp.route('/admin/overrides/audit/export', methods=['GET'])
@jwt_required()
def export_audit_logs():
    """Export override audit logs as CSV"""
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        user = db.session.query(User).get(current_user_id)
        
        # Verify admin role
        if not user or user.role.lower() != 'admin':
            return jsonify({'error': 'Admin privileges required'}), 403
        
        # Get all logs (with optional filters)
        query = db.session.query(OverrideAuditLog).order_by(OverrideAuditLog.created_at.desc())
        
        # Apply filters
        admin_id = request.args.get('admin_id', type=int)
        if admin_id:
            query = query.filter(OverrideAuditLog.admin_user_id == admin_id)
        
        scope = request.args.get('scope')
        if scope:
            query = query.filter(OverrideAuditLog.override_scope == scope.upper())
        
        module = request.args.get('module')
        if module:
            query = query.filter(OverrideAuditLog.module == module.upper())
        
        # Get all logs
        logs = query.all()
        
        # Generate CSV
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Admin User', 'Vehicle VIN', 'Vehicle Profile',
            'Scope', 'Module', 'Action', 'Reason', 'Duration',
            'Result', 'Error', 'Session ID', 'IP Address', 'Created At'
        ])
        
        # Rows
        for log in logs:
            writer.writerow([
                log.id,
                log.admin_user.username if log.admin_user else 'Unknown',
                log.vehicle_vin or '',
                log.vehicle_profile or '',
                log.override_scope,
                log.module or '',
                log.action or '',
                log.reason,
                log.duration_minutes or '',
                log.result,
                log.error_message or '',
                log.session_id or '',
                log.ip_address or '',
                log.created_at.isoformat()
            ])
        
        # Return as file download
        from flask import Response
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=override_audit_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
