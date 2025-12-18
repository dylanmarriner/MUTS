from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from muts.models.vehicle_capabilities import VehicleCapabilityProfile
from muts.models.diagnostics_registry import template_registry
from muts.models.diagnostics_template import ServiceStatus

vehicle_bp = Blueprint('vehicle_capabilities', __name__)

@vehicle_bp.route('/vehicle-capabilities', methods=['POST'])
@jwt_required()
def get_vehicle_capabilities():
    """Get vehicle capabilities based on manufacturer and model"""
    try:
        data = request.get_json()
        
        manufacturer = data.get('manufacturer')
        model = data.get('model')
        generation = data.get('generation')
        body = data.get('body')
        transmission = data.get('transmission')
        year = data.get('year')
        engine = data.get('engine')
        
        if not manufacturer or not model:
            return jsonify({'error': 'Manufacturer and model required'}), 400
        
        # First try to find template
        template = template_registry.find_template(
            manufacturer=manufacturer,
            model=model,
            generation=generation,
            year=year,
            engine=engine,
            transmission=transmission
        )
        
        if template:
            # Convert template to response format
            capabilities = {
                'manufacturer': template.manufacturer,
                'platform': template.platform,
                'model': template.model,
                'generation': template.generation,
                'primary_protocol': None,
                'required_interface': 'OBD2',
                'interface_notes': None,
                'modules': {},
                'services': {},
                'supports_dsg_shifts': False,
                'supports_awd_modeling': False,
                'supports_virtual_dyno': True,
                'confidence_level': 85,
                'status': 'SUPPORTED',
                'notes': template.notes
            }
            
            # Convert module capabilities
            for module, module_cap in template.modules.items():
                capabilities['modules'][module.value] = {
                    'status': 'SUPPORTED' if any(s.status == ServiceStatus.SUPPORTED for s in module_cap.services.values()) else 'NOT_SUPPORTED',
                    'reason': module_cap.notes,
                    'protocol_info': module_cap.protocol_info,
                    'services': {}
                }
                
                for service, service_cap in module_cap.services.items():
                    capabilities['modules'][module.value]['services'][service.value] = {
                        'status': service_cap.status.value,
                        'reason': service_cap.reason,
                        'supported': service_cap.status == ServiceStatus.SUPPORTED
                    }
            
            # Extract protocol info from first module
            if template.modules:
                first_module = list(template.modules.values())[0]
                if first_module.protocol_info:
                    capabilities['primary_protocol'] = first_module.protocol_info
                    capabilities['interface_notes'] = first_module.protocol_info
            
            # Set feature flags based on manufacturer
            if manufacturer == "Volkswagen":
                capabilities['supports_dsg_shifts'] = transmission == "DSG"
                capabilities['supports_awd_modeling'] = "R" in model or "AWD" in model
            elif manufacturer == "Alfa Romeo":
                capabilities['supports_dsg_shifts'] = transmission == "TCT"
            
            return jsonify(capabilities)
        
        # Fallback to database profiles
        from app import create_app
        app = create_app()
        with app.app_context():
            from muts.models.database_models import db
            
            profile = db.session.query(VehicleCapabilityProfile).filter_by(
                manufacturer=manufacturer,
                model=model
            ).first()
            
            if not profile:
                return jsonify({
                    'status': 'UNKNOWN',
                    'message': 'Vehicle capabilities not defined'
                })
            
            # Return capability summary
            return jsonify(profile.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
