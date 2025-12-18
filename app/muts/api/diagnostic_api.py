from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.vehicle import Vehicle, DiagnosticTroubleCode, ECUData
from muts.core.diagnostic_router import DiagnosticRouter, DiagnosticService, DiagnosticModule
from muts.models.vehicle_capabilities import SupportStatus
from datetime import datetime
import logging

diagnostic_bp = Blueprint('diagnostic', __name__)
logger = logging.getLogger(__name__)

@diagnostic_bp.route('/capabilities/<vin>', methods=['GET'])
@jwt_required()
def get_vehicle_capabilities(vin):
    """Get vehicle capability matrix"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        router = DiagnosticRouter(db.session)
        capabilities = router.get_vehicle_capabilities_summary(vehicle)
        
        return jsonify(capabilities)
        
    except Exception as e:
        logger.error(f"Error getting vehicle capabilities: {e}")
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/scan/<vin>', methods=['POST'])
@jwt_required()
def scan_dtcs(vin):
    """Scan for Diagnostic Trouble Codes"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Use capability-based routing
        router = DiagnosticRouter(db.session)
        result = router.route_diagnostic_request(vehicle, 'scan_dtcs')
        
        if result['status'] == 'SUCCESS':
            # Store DTCs in database
            for dtc in result['data']:
                existing_dtc = DiagnosticTroubleCode.query.filter_by(
                    vehicle_id=vin, code=dtc['code'], cleared_at=None
                ).first()
                
                if not existing_dtc:
                    new_dtc = DiagnosticTroubleCode(
                        vehicle_id=vin,
                        code=dtc['code'],
                        description=dtc['description'],
                        severity=dtc.get('severity', 'MEDIUM')
                    )
                    db.session.add(new_dtc)
            
            db.session.commit()
        
        # Return current DTCs from database if successful
        if result['status'] == 'SUCCESS':
            current_dtcs = DiagnosticTroubleCode.query.filter_by(
                vehicle_id=vin, cleared_at=None
            ).all()
            return jsonify([dtc.to_dict() for dtc in current_dtcs])
        else:
            return jsonify(result), 400 if result['status'] == 'NOT_SUPPORTED' else 500
        
    except Exception as e:
        logger.error(f"Error scanning DTCs: {e}")
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/clear-dtcs/<vin>', methods=['POST'])
@jwt_required()
def clear_dtcs(vin):
    """Clear all Diagnostic Trouble Codes"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Use capability-based routing
        router = DiagnosticRouter(db.session)
        result = router.route_diagnostic_request(vehicle, 'clear_dtcs')
        
        if result['status'] == 'SUCCESS':
            # Mark DTCs as cleared in database
            dtcs = DiagnosticTroubleCode.query.filter_by(
                vehicle_id=vin, cleared_at=None
            ).all()
            
            for dtc in dtcs:
                dtc.cleared_at = datetime.utcnow()
            
            db.session.commit()
            return jsonify({'message': 'DTCs cleared successfully'})
        else:
            return jsonify(result), 400 if result['status'] == 'NOT_SUPPORTED' else 500
        
    except Exception as e:
        logger.error(f"Error clearing DTCs: {e}")
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/live-data/<vin>', methods=['GET'])
@jwt_required()
def get_live_data(vin):
    """Get real-time ECU data"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Use capability-based routing
        router = DiagnosticRouter(db.session)
        result = router.route_diagnostic_request(vehicle, 'live_data')
        
        if result['status'] == 'SUCCESS':
            # Store sample in database
            if 'data' in result:
                ecu_data = ECUData(
                    vehicle_id=vin,
                    timestamp=datetime.utcnow(),
                    rpm=result['data'].get('rpm', 0),
                    speed=result['data'].get('speed', 0),
                    throttle=result['data'].get('throttle', 0),
                    boost=result['data'].get('boost', 0),
                    afr=result['data'].get('afr', 14.7),
                    timing=result['data'].get('timing', 0),
                    load=result['data'].get('load', 0),
                    iat=result['data'].get('iat', 20),
                    ect=result['data'].get('ect', 90)
                )
                db.session.add(ecu_data)
                db.session.commit()
            
            return jsonify(result['data'] if result['status'] == 'SUCCESS' else result)
        else:
            return jsonify(result), 400 if result['status'] == 'NOT_SUPPORTED' else 500
        
    except Exception as e:
        logger.error(f"Error getting live data: {e}")
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/module-scan/<vin>', methods=['POST'])
@jwt_required()
def scan_modules(vin):
    """Scan all supported modules on vehicle"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        router = DiagnosticRouter(db.session)
        scan_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'modules': {},
            'unsupported': []
        }
        
        # Check each module
        for module in DiagnosticModule:
            is_supported, reason = router.is_module_supported(vehicle, module)
            
            if is_supported:
                # Try to communicate with module
                try:
                    module_result = router.route_diagnostic_request(vehicle, 'scan_dtcs', module=module.value)
                    scan_results['modules'][module.value] = {
                        'status': 'ONLINE',
                        'dtcs': module_result.get('data', [])
                    }
                except Exception as e:
                    scan_results['modules'][module.value] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
            else:
                scan_results['unsupported'].append({
                    'module': module.value,
                    'reason': reason
                })
        
        return jsonify(scan_results)
        
    except Exception as e:
        logger.error(f"Error scanning modules: {e}")
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/history/<vin>', methods=['GET'])
@jwt_required()
def get_data_history(vin):
    """Get historical ECU data"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = ECUData.query.filter_by(vehicle_id=vin)
        
        if start_date:
            query = query.filter(ECUData.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(ECUData.timestamp <= datetime.fromisoformat(end_date))
        
        # Get data
        data = query.order_by(ECUData.timestamp.desc()).limit(limit).all()
        
        return jsonify([d.to_dict() for d in data])
        
    except Exception as e:
        logger.error(f"Error getting data history: {e}")
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/dtc-history/<vin>', methods=['GET'])
@jwt_required()
def get_dtc_history(vin):
    """Get DTC history"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        dtcs = DiagnosticTroubleCode.query.filter_by(vehicle_id=vin).all()
        
        return jsonify([dtc.to_dict() for dtc in dtcs])
        
    except Exception as e:
        logger.error(f"Error getting DTC history: {e}")
        return jsonify({'error': str(e)}), 500
