
from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash

from . import bp
from ...extensions import db, limiter
from ...models.user import User
from ...models.audit_log import AuditLog


@bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """User registration endpoint"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User already exists'}), 409
    
    # TODO: Port legacy logic - validate password strength, email format, etc.
    
    # Create new user
    try:
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            first_name=data['first_name'],
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            role=data['role']
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Log registration
        AuditLog.log_action(
            user_id=user.id,
            user_email=user.email,
            action='USER_REGISTRATION',
            operation_type='CREATE',
            success=True,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """User login endpoint"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        # Log failed login attempt
        AuditLog.log_login_attempt(
            email=data['email'],
            success=False,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            error_message='Invalid credentials'
        )
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    # Update last login
    user.last_login_at = db.func.now()
    db.session.commit()
    
    # Log successful login
    AuditLog.log_login_attempt(
        email=user.email,
        success=True,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 404
    
    new_token = create_access_token(identity=current_user_id)
    return jsonify({'access_token': new_token}), 200


@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Track changes for audit log
    old_values = user.to_dict()
    
    # Update allowed fields
    updatable_fields = ['first_name', 'last_name', 'phone']
    for field in updatable_fields:
        if field in data:
            setattr(user, field, data[field])
    
    try:
        db.session.commit()
        
        # Log profile update
        AuditLog.log_data_modification(
            user_id=user.id,
            user_email=user.email,
            resource_type='user',
            resource_id=user.id,
            old_values=old_values,
            new_values=user.to_dict()
        )
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {str(e)}")
        return jsonify({'error': 'Profile update failed'}), 500


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint (token blacklisting would be implemented here)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user:
        # Log logout
        AuditLog.log_action(
            user_id=user.id,
            user_email=user.email,
            action='USER_LOGOUT',
            operation_type='LOGOUT',
            success=True,
            ip_address=request.remote_addr
        )
    
    # TODO: Port legacy logic - implement token blacklisting
    return jsonify({'message': 'Logged out successfully'}), 200
