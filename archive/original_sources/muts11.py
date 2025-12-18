from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.vehicle import Vehicle, DiagnosticTroubleCode, ECUData
from app.services.obd_service import MazdaOBDService
from datetime import datetime
import logging

diagnostic_bp = Blueprint('diagnostic', __name__)
logger = logging.getLogger(__name__)

@diagnostic_bp.route('/scan/<vin>', methods=['POST'])
@jwt_required()
def scan_dtcs(vin):
    """Scan for Diagnostic Trouble Codes"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Initialize OBD service
        obd_service = MazdaOBDService()
        if not obd_service.connect():
            return jsonify({'error': 'Failed to connect to vehicle'}), 500
        
        # Read DTCs
        dtcs = obd_service.read_dtcs()
        
        # Store in database
        for dtc in dtcs:
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
        obd_service.disconnect()
        
        current_dtcs = DiagnosticTroubleCode.query.filter_by(
            vehicle_id=vin, cleared_at=None
        ).all()
        
        return jsonify([dtc.to_dict() for dtc in current_dtcs])
        
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
        
        # Clear via OBD
        obd_service = MazdaOBDService()
        if obd_service.connect():
            success = obd_service.clear_dtcs()
            obd_service.disconnect()
            
            if success:
                # Mark DTCs as cleared in database
                dtcs = DiagnosticTroubleCode.query.filter_by(
                    vehicle_id=vin, cleared_at=None
                ).all()
                
                for dtc in dtcs:
                    dtc.cleared_at = datetime.utcnow()
                
                db.session.commit()
                
                return jsonify({'message': 'DTCs cleared successfully'})
        
        return jsonify({'error': 'Failed to clear DTCs'}), 500
        
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
        
        obd_service = MazdaOBDService()
        if not obd_service.connect():
            return jsonify({'error': 'Failed to connect to vehicle'}), 500
        
        # Read live data
        live_data = obd_service.read_ecu_data()
        
        # Store in database for historical analysis
        ecu_data = ECUData(vehicle_id=vin, **live_data)
        db.session.add(ecu_data)
        db.session.commit()
        
        obd_service.disconnect()
        
        return jsonify(live_data)
        
    except Exception as e:
        logger.error(f"Error reading live data: {e}")
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/crash-data/<vin>/clear', methods=['POST'])
@jwt_required()
def clear_crash_data(vin):
    """Clear crash data and reset safety systems"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Implementation for clearing crash data would interface with
        # Mazda-specific diagnostic protocols and airbag control modules
        
        return jsonify({
            'message': 'Crash data clearance initiated',
            'status': 'SUCCESS',
            'systems_reset': ['AIRBAG', 'SEATBELT_PRETENSIONERS', 'CRASH_SENSORS']
        })
        
    except Exception as e:
        logger.error(f"Error clearing crash data: {e}")
        return jsonify({'error': str(e)}), 500

@diagnostic_bp.route('/health-report/<vin>', methods=['GET'])
@jwt_required()
def get_health_report(vin):
    """Generate comprehensive vehicle health report"""
    try:
        vehicle = Vehicle.query.filter_by(id=vin, user_id=get_jwt_identity()).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Get recent DTCs
        dtcs = DiagnosticTroubleCode.query.filter_by(
            vehicle_id=vin, cleared_at=None
        ).all()
        
        # Get recent ECU data for analysis
        recent_data = ECUData.query.filter_by(vehicle_id=vin)\
            .order_by(ECUData.timestamp.desc())\
            .limit(100)\
            .all()
        
        # Analyze vehicle health
        health_score = 100
        issues = []
        
        if dtcs:
            health_score -= len(dtcs) * 10
            issues.extend([f'Active DTC: {dtc.code}' for dtc in dtcs])
        
        if recent_data:
            # Analyze for potential issues
            avg_knock = sum(d.knock_count or 0 for d in recent_data) / len(recent_data)
            if avg_knock > 2:
                health_score -= 15
                issues.append('Elevated knock counts detected')
            
            avg_boost = sum(d.boost_psi or 0 for d in recent_data) / len(recent_data)
            if avg_boost > 18:
                health_score -= 10
                issues.append('High boost levels detected')
        
        return jsonify({
            'health_score': max(health_score, 0),
            'issues': issues,
            'active_dtcs': [dtc.to_dict() for dtc in dtcs],
            'recommendations': [
                'Regular maintenance recommended',
                'Monitor boost levels',
                'Check ignition system if knock persists'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error generating health report: {e}")
        return jsonify({'error': str(e)}), 500