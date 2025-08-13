
from enum import Enum
from functools import wraps
from flask import current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .models.user import User


class Role(Enum):
    """User roles in the system"""
    ADMIN = "admin"
    PET_PARENT = "pet_parent"
    VET = "vet"
    HANDLER = "handler"
    ISOLATION_CENTER = "isolation_center"
    NGO = "ngo"
    GOVERNMENT = "government"


class Permission(Enum):
    """System permissions"""
    # Pet management
    VIEW_PETS = "view_pets"
    MANAGE_PETS = "manage_pets"
    
    # Vendor/Services
    VIEW_VENDORS = "view_vendors"
    MANAGE_VENDOR_PROFILE = "manage_vendor_profile"
    
    # Bookings
    CREATE_BOOKINGS = "create_bookings"
    MANAGE_BOOKINGS = "manage_bookings"
    VIEW_ALL_BOOKINGS = "view_all_bookings"
    
    # Passport/FurrWings
    REQUEST_PASSPORT = "request_passport"
    ISSUE_HEALTH_CERT = "issue_health_cert"
    MANAGE_TRAVEL_DOCS = "manage_travel_docs"
    
    # Handler operations
    MANAGE_HANDLER_TASKS = "manage_handler_tasks"
    UPDATE_TRAVEL_STATUS = "update_travel_status"
    
    # Isolation center
    MANAGE_ISOLATION_STAYS = "manage_isolation_stays"
    LOG_DAILY_ACTIVITIES = "log_daily_activities"
    
    # NGO operations
    REGISTER_STRAYS = "register_strays"
    MANAGE_NGO_DATA = "manage_ngo_data"
    
    # Government access
    VIEW_AGGREGATE_DATA = "view_aggregate_data"
    EXPORT_COMPLIANCE_DATA = "export_compliance_data"
    
    # Admin
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_SYSTEM = "manage_system"
    
    # Data rights
    HANDLE_DSR_REQUESTS = "handle_dsr_requests"
    MANAGE_CONSENTS = "manage_consents"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [perm for perm in Permission],  # Admin has all permissions
    
    Role.PET_PARENT: [
        Permission.VIEW_PETS, Permission.MANAGE_PETS,
        Permission.VIEW_VENDORS, Permission.CREATE_BOOKINGS,
        Permission.REQUEST_PASSPORT
    ],
    
    Role.VET: [
        Permission.VIEW_PETS, Permission.MANAGE_VENDOR_PROFILE,
        Permission.MANAGE_BOOKINGS, Permission.ISSUE_HEALTH_CERT
    ],
    
    Role.HANDLER: [
        Permission.MANAGE_HANDLER_TASKS, Permission.UPDATE_TRAVEL_STATUS,
        Permission.MANAGE_TRAVEL_DOCS
    ],
    
    Role.ISOLATION_CENTER: [
        Permission.MANAGE_ISOLATION_STAYS, Permission.LOG_DAILY_ACTIVITIES
    ],
    
    Role.NGO: [
        Permission.REGISTER_STRAYS, Permission.MANAGE_NGO_DATA
    ],
    
    Role.GOVERNMENT: [
        Permission.VIEW_AGGREGATE_DATA, Permission.EXPORT_COMPLIANCE_DATA
    ]
}


def init_rbac(app):
    """Initialize RBAC system"""
    
    @app.before_request
    def load_user():
        """Load user context for request"""
        # This will be called on each request
        pass


def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # TODO: Port legacy logic - load user and check permissions
            # user = User.query.get(user_id)
            # if not user or not user.has_permission(permission):
            #     return {'error': 'Insufficient permissions'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            
            # TODO: Port legacy logic - load user and check role
            # user = User.query.get(user_id)
            # if not user or user.role != role.value:
            #     return {'error': 'Insufficient permissions'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
