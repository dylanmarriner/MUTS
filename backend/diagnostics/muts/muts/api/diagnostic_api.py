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
        if obd_service.connect():
            data = obd_service.read_ecu_data()
            obd_service.disconnect()
            
            # Store in database
            ecu_data = ECUData(
                vehicle_id=vin,
                **data
            )
            db.session.add(ecu_data)
            db.session.commit()
            
            return jsonify(data)
        
        return jsonify({'error': 'Failed to read ECU data'}), 500
        
    except Exception as e:
        logger.error(f"Error reading live data: {e}")
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
