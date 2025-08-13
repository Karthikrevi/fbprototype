
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from ..extensions import db
from ..rbac import Role, Permission, ROLE_PERMISSIONS


class User(db.Model):
    """User model with role-based access control"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    role = Column(Enum(Role), nullable=False, default=Role.PET_PARENT)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    
    # Relationships
    pets = relationship("Pet", back_populates="owner", lazy='dynamic')
    consents = relationship("Consent", back_populates="user", lazy='dynamic')
    dsr_requests = relationship("DSRRequest", back_populates="user", lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        user_permissions = ROLE_PERMISSIONS.get(self.role, [])
        return permission in user_permissions
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role.value,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
