#!/usr/bin/env python3
"""
API endpoints for vehicle profile management
"""

from flask import Blueprint, request, jsonify
from muts.models.vehicle_profile import VehicleProfile
from muts.models.database_models import User
from muts.models.vehicle_constants import VehicleConstantsPreset
from muts.models.diagnostics_registry import template_registry
from muts.auth.decorators import require_auth
from muts import db
import logging

logger = logging.getLogger(__name__)

vehicle_bp = Blueprint('vehicles', __name__, url_prefix='/api/vehicles')


@vehicle_bp.route('/my-vehicles', methods=['GET'])
@require_auth
def get_my_vehicles():
    """Get current user's saved vehicle profiles"""
    try:
        user_id = request.user.id
        profiles = VehicleProfile.query.filter_by(user_id=user_id, is_active=True).all()
        
        vehicles = []
        for profile in profiles:
            vehicle_data = profile.to_dict()
            # Add constants info
            constants = profile.get_constants()
            if constants:
                vehicle_data['constants'] = {
                    'id': constants.id,
                    'version': constants.version,
                    'has_overrides': constants.has_overrides(),
                    'confidence_score': constants.get_confidence_score()
                }
            vehicles.append(vehicle_data)
        
        return jsonify(vehicles)
    except Exception as e:
        logger.error(f"Failed to get user vehicles: {e}")
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/profile', methods=['POST'])
@require_auth
def create_vehicle_profile():
    """Create a new vehicle profile"""
    try:
        user_id = request.user.id
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['vin', 'plate', 'engine_number', 'year', 'make', 'model', 'submodel', 'body']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if VIN already exists
        existing = VehicleProfile.query.filter_by(vin=data['vin']).first()
        if existing:
            return jsonify({'error': 'Vehicle with this VIN already exists'}), 409
        
        # Find matching constants preset
        preset = None
        if data['make'] == 'Holden' and 'Commodore' in data['model']:
            preset = VehicleConstantsPreset.query.filter_by(
                manufacturer='Holden',
                model='Commodore',
                generation='VF'
            ).first()
        elif data['make'] == 'Volkswagen' and 'Golf' in data['model']:
            preset = VehicleConstantsPreset.query.filter_by(
                manufacturer='Volkswagen',
                model='Golf',
                generation='Mk6'
            ).first()
        
        # Create profile
        profile = VehicleProfile(
            vin=data['vin'].upper(),
            plate=data['plate'],
            engine_number=data['engine_number'],
            year=data['year'],
            make=data['make'],
            model=data['model'],
            submodel=data['submodel'],
            body=data['body'],
            displacement=data.get('displacement'),
            fuel_type=data.get('fuel_type'),
            colour=data.get('colour'),
            user_id=user_id,
            constants_preset_id=preset.id if preset else None
        )
        
        db.session.add(profile)
        
        # Create initial vehicle constants if we have a preset
        if preset:
            from muts.models.vehicle_constants import VehicleConstants
            constants = VehicleConstants(
                vehicle_id=profile.vin,
                preset_id=preset.id,
                version=1,
                note='Initial constants',
                created_by=user_id,
                is_active=True
            )
            db.session.add(constants)
        
        db.session.commit()
        
        return jsonify(profile.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Failed to create vehicle profile: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/profile/<vin>', methods=['DELETE'])
@require_auth
def delete_vehicle_profile(vin):
    """Delete a vehicle profile"""
    try:
        user_id = request.user.id
        profile = VehicleProfile.query.filter_by(vin=vin, user_id=user_id).first()
        
        if not profile:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        # Soft delete
        profile.is_active = False
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Failed to delete vehicle profile: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/manufacturers', methods=['GET'])
def get_manufacturers():
    """Get list of available manufacturers"""
    try:
        manufacturers = set()
        for template in template_registry.templates:
            manufacturers.add(template.manufacturer)
        
        return jsonify(sorted(list(manufacturers)))
    except Exception as e:
        logger.error(f"Failed to get manufacturers: {e}")
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/models', methods=['GET'])
def get_models():
    """Get models for a manufacturer"""
    try:
        manufacturer = request.args.get('manufacturer')
        if not manufacturer:
            return jsonify({'error': 'Manufacturer required'}), 400
        
        models = set()
        for template in template_registry.templates:
            if template.manufacturer == manufacturer:
                models.add(template.model)
        
        return jsonify(sorted(list(models)))
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/generations', methods=['GET'])
def get_generations():
    """Get generations for a manufacturer/model"""
    try:
        manufacturer = request.args.get('manufacturer')
        model = request.args.get('model')
        
        if not manufacturer or not model:
            return jsonify({'error': 'Manufacturer and model required'}), 400
        
        generations = set()
        for template in template_registry.templates:
            if (template.manufacturer == manufacturer and 
                template.model == model):
                generations.add(template.generation)
        
        return jsonify(sorted(list(generations)))
    except Exception as e:
        logger.error(f"Failed to get generations: {e}")
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/variants', methods=['GET'])
def get_variants():
    """Get variants for manufacturer/model/generation"""
    try:
        manufacturer = request.args.get('manufacturer')
        model = request.args.get('model')
        generation = request.args.get('generation')
        
        if not all([manufacturer, model, generation]):
            return jsonify({'error': 'Manufacturer, model, and generation required'}), 400
        
        variants = []
        for template in template_registry.templates:
            if (template.manufacturer == manufacturer and 
                template.model == model and 
                template.generation == generation):
                variants.append({
                    'id': f"{manufacturer}_{model}_{generation}",
                    'name': template.variant or f"{manufacturer} {model} {generation}",
                    'year_range': template.year_range,
                    'body_type': template.body_type,
                    'transmission_type': template.transmission_type.value if template.transmission_type else None,
                    'drivetrain_type': template.drivetrain_type.value if template.drivetrain_type else None
                })
        
        return jsonify(variants)
    except Exception as e:
        logger.error(f"Failed to get variants: {e}")
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/variant/<variant_id>', methods=['GET'])
def get_variant_details(variant_id):
    """Get detailed information about a variant"""
    try:
        # Parse variant_id
        parts = variant_id.split('_')
        if len(parts) < 3:
            return jsonify({'error': 'Invalid variant ID'}), 400
        
        manufacturer, model, generation = parts[0], parts[1], parts[2]
        
        # Find matching template
        template = None
        for t in template_registry.templates:
            if (t.manufacturer == manufacturer and 
                t.model == model and 
                t.generation == generation):
                template = t
                break
        
        if not template:
            return jsonify({'error': 'Variant not found'}), 404
        
        # Build variant details
        details = {
            'id': variant_id,
            'manufacturer': template.manufacturer,
            'model': template.model,
            'generation': template.generation,
            'variant': template.variant,
            'year_range': template.year_range,
            'body_type': template.body_type,
            'transmission_type': template.transmission_type.value if template.transmission_type else None,
            'drivetrain_type': template.drivetrain_type.value if template.drivetrain_type else None,
            'modules': {}
        }
        
        # Add module capabilities
        for module, capability in template.modules.items():
            details['modules'][module.value] = {
                'status': capability.status.value,
                'protocol_info': capability.protocol_info,
                'notes': capability.notes
            }
        
        return jsonify(details)
    except Exception as e:
        logger.error(f"Failed to get variant details: {e}")
        return jsonify({'error': str(e)}), 500


@vehicle_bp.route('/profile/<vin>/constants', methods=['GET'])
@require_auth
def get_vehicle_constants(vin):
    """Get vehicle constants for a VIN"""
    try:
        user_id = request.user.id
        profile = VehicleProfile.query.filter_by(vin=vin, user_id=user_id).first()
        
        if not profile:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        constants = profile.get_constants()
        if not constants:
            return jsonify({'error': 'No constants found for vehicle'}), 404
        
        # Get effective constants
        effective = constants.get_effective_constants()
        
        return jsonify({
            'constants_id': constants.id,
            'version': constants.version,
            'preset_id': constants.preset_id,
            'preset_name': constants.preset.name if constants.preset else None,
            'effective_constants': effective,
            'has_overrides': constants.has_overrides(),
            'confidence_score': constants.get_confidence_score(),
            'confidence_level': constants.get_confidence_level(),
            'confidence_deductions': constants.get_confidence_deductions(),
            'note': constants.note
        })
    except Exception as e:
        logger.error(f"Failed to get vehicle constants: {e}")
        return jsonify({'error': str(e)}), 500
