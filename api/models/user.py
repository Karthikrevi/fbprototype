
from datetime import datetime
from enum import Enum
from api.extensions import db, bcrypt
from email_validator import validate_email, EmailNotValidError

class UserRole(Enum):
    PET_PARENT = 'pet_parent'
    VENDOR_GROOMER = 'vendor_groomer'
    VENDOR_BOARDING = 'vendor_boarding'
    VET = 'vet'
    PHARMACY = 'pharmacy'
    HANDLER = 'handler'
    ISOLATION = 'isolation'
    NGO = 'ngo'
    GOV_VIEW = 'gov_view'
    ADMIN = 'admin'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PET_PARENT)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Additional profile fields
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    def __init__(self, email, password, role=UserRole.PET_PARENT, **kwargs):
        self.email = self.validate_email(email)
        self.set_password(password)
        self.role = role
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @staticmethod
    def validate_email(email):
        """Validate email format."""
        try:
            validated_email = validate_email(email)
            return validated_email.email
        except EmailNotValidError:
            raise ValueError(f"Invalid email address: {email}")
    
    def set_password(self, password):
        """Hash and set password."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'email': self.email,
            'role': self.role.value,
            'is_email_verified': self.is_email_verified,
            'is_active': self.is_active,
            'full_name': self.full_name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'
