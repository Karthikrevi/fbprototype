
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import bp
from ...extensions import db
from ...models.pet import Pet
from ...models.user import User
from ...models.audit_log import AuditLog
from ...rbac import require_permission, Permission


@bp.route('/', methods=['GET'])
@jwt_required()
@require_permission(Permission.VIEW_PETS)
def get_pets():
    """Get user's pets"""
    current_user_id = get_jwt_identity()
    
    pets = Pet.query.filter_by(owner_id=current_user_id, is_active='active').all()
    
    return jsonify({
        'pets': [pet.to_dict() for pet in pets]
    }), 200


@bp.route('/', methods=['POST'])
@jwt_required()
@require_permission(Permission.MANAGE_PETS)
def create_pet():
    """Create a new pet profile"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name') or not data.get('species'):
        return jsonify({'error': 'Pet name and species are required'}), 400
    
    try:
        pet = Pet(
            owner_id=current_user_id,
            name=data['name'],
            species=data['species'],
            breed=data.get('breed'),
            gender=data.get('gender'),
            date_of_birth=data.get('date_of_birth'),
            weight=data.get('weight'),
            color=data.get('color'),
            distinctive_marks=data.get('distinctive_marks'),
            microchip_id=data.get('microchip_id'),
            blood_type=data.get('blood_type'),
            allergies=data.get('allergies'),
            medical_conditions=data.get('medical_conditions'),
            special_needs=data.get('special_needs')
        )
        
        db.session.add(pet)
        db.session.commit()
        
        # Log pet creation
        AuditLog.log_action(
            user_id=current_user_id,
            action='CREATE_PET',
            resource_type='pet',
            resource_id=pet.id,
            operation_type='CREATE',
            success=True
        )
        
        return jsonify({
            'message': 'Pet created successfully',
            'pet': pet.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Pet creation failed'}), 500


@bp.route('/<int:pet_id>', methods=['GET'])
@jwt_required()
@require_permission(Permission.VIEW_PETS)
def get_pet(pet_id):
    """Get specific pet details"""
    current_user_id = get_jwt_identity()
    
    pet = Pet.query.filter_by(id=pet_id, owner_id=current_user_id).first()
    if not pet:
        return jsonify({'error': 'Pet not found'}), 404
    
    # Log pet access
    AuditLog.log_data_access(
        user_id=current_user_id,
        resource_type='pet',
        resource_id=pet.id,
        sensitive_data=True
    )
    
    return jsonify({'pet': pet.to_dict()}), 200


@bp.route('/<int:pet_id>', methods=['PUT'])
@jwt_required()
@require_permission(Permission.MANAGE_PETS)
def update_pet(pet_id):
    """Update pet profile"""
    current_user_id = get_jwt_identity()
    
    pet = Pet.query.filter_by(id=pet_id, owner_id=current_user_id).first()
    if not pet:
        return jsonify({'error': 'Pet not found'}), 404
    
    data = request.get_json()
    old_values = pet.to_dict()
    
    # Update allowed fields
    updatable_fields = [
        'name', 'breed', 'weight', 'color', 'distinctive_marks',
        'allergies', 'medical_conditions', 'special_needs'
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(pet, field, data[field])
    
    try:
        db.session.commit()
        
        # Log pet update
        AuditLog.log_data_modification(
            user_id=current_user_id,
            resource_type='pet',
            resource_id=pet.id,
            old_values=old_values,
            new_values=pet.to_dict()
        )
        
        return jsonify({
            'message': 'Pet updated successfully',
            'pet': pet.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Pet update failed'}), 500


# TODO: Port legacy logic - add routes for:
# - Pet photo upload
# - Pet medical records
# - Pet vaccination history
# - Pet document management
