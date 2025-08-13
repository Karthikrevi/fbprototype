
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jwt_identity,
    jwt_required, get_jwt
)
from email_validator import EmailNotValidError
from api.extensions import db, limiter
from api.models.user import User, UserRole
from api.models.token_blocklist import TokenBlocklist

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body must be JSON'
                }
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role_str = data.get('role', 'pet_parent')
        
        # Validate required fields
        if not email or not password:
            return jsonify({
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'Email and password are required'
                }
            }), 400
        
        # Validate role
        try:
            role = UserRole(role_str)
        except ValueError:
            return jsonify({
                'error': {
                    'code': 'INVALID_ROLE',
                    'message': f'Invalid role. Valid roles: {[r.value for r in UserRole]}'
                }
            }), 400
        
        # Restrict high-privilege roles (can be modified by admin later)
        restricted_roles = [UserRole.ADMIN, UserRole.GOV_VIEW]
        if role in restricted_roles:
            return jsonify({
                'error': {
                    'code': 'RESTRICTED_ROLE',
                    'message': 'Cannot register with this role. Contact administrator.'
                }
            }), 403
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'error': {
                    'code': 'EMAIL_EXISTS',
                    'message': 'User with this email already exists'
                }
            }), 409
        
        # Create new user
        try:
            user = User(
                email=email,
                password=password,
                role=role,
                full_name=data.get('full_name'),
                phone=data.get('phone')
            )
            db.session.add(user)
            db.session.commit()
            
            return jsonify({
                'message': 'User registered successfully',
                'user': user.to_dict()
            }), 201
            
        except ValueError as e:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e)
                }
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': {
                'code': 'REGISTRATION_FAILED',
                'message': 'Failed to register user'
            }
        }), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login user and return JWT tokens."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Request body must be JSON'
                }
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'error': {
                    'code': 'MISSING_CREDENTIALS',
                    'message': 'Email and password are required'
                }
            }), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid email or password'
                }
            }), 401
        
        if not user.is_active:
            return jsonify({
                'error': {
                    'code': 'ACCOUNT_DISABLED',
                    'message': 'Account has been disabled'
                }
            }), 401
        
        # Create JWT tokens with additional claims
        additional_claims = {
            'role': user.role.value,
            'email': user.email,
            'is_email_verified': user.is_email_verified
        }
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'LOGIN_FAILED',
                'message': 'Login failed'
            }
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found or inactive'
                }
            }), 404
        
        # Create new access token
        additional_claims = {
            'role': user.role.value,
            'email': user.email,
            'is_email_verified': user.is_email_verified
        }
        
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'REFRESH_FAILED',
                'message': 'Failed to refresh token'
            }
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required(optional=True)
def logout():
    """Logout user by revoking token."""
    try:
        token = get_jwt()
        if token:
            jti = token['jti']
            TokenBlocklist.revoke_token(jti)
            return jsonify({'message': 'Successfully logged out'}), 200
        else:
            return jsonify({'message': 'No token provided'}), 200
            
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'LOGOUT_FAILED',
                'message': 'Failed to logout'
            }
        }), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user profile."""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 'FETCH_USER_FAILED',
                'message': 'Failed to fetch user profile'
            }
        }), 500
