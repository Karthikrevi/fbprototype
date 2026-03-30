
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..extensions import db


class Vendor(db.Model):
    """Vendor model for service providers"""
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Business info
    business_name = Column(String(200), nullable=False)
    business_type = Column(String(100))  # grooming, boarding, veterinary, etc.
    license_number = Column(String(100))
    tax_id = Column(String(50))
    
    # Contact & location
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default='India')
    phone = Column(String(20))
    
    # Geographic coordinates
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Business details
    description = Column(Text)
    website = Column(String(500))
    logo_url = Column(String(500))
    
    # Status & settings
    is_online = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    account_status = Column(SQLEnum('active', 'suspended', 'on_break', name='vendor_status'), default='active')
    
    # Business hours (JSON or separate table)
    business_hours = Column(Text)  # JSON string for now
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="vendor_profile")
    services = relationship("Service", back_populates="vendor", lazy='dynamic')
    bookings = relationship("Booking", back_populates="vendor", lazy='dynamic')
    
    def __repr__(self):
        return f'<Vendor {self.business_name}>'
    
    def to_dict(self):
        """Convert vendor to dictionary"""
        return {
            'id': self.id,
            'business_name': self.business_name,
            'business_type': self.business_type,
            'license_number': self.license_number,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'phone': self.phone,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'description': self.description,
            'website': self.website,
            'logo_url': self.logo_url,
            'is_online': self.is_online,
            'is_verified': self.is_verified,
            'account_status': self.account_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Service(db.Model):
    """Service model for vendor offerings"""
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)
    
    # Service details
    name = Column(String(200), nullable=False)
    category = Column(String(100))  # grooming, boarding, veterinary, etc.
    description = Column(Text)
    
    # Pricing
    base_price = Column(Float, nullable=False)
    price_unit = Column(String(50), default='per_service')  # per_service, per_hour, per_day
    
    # Duration
    duration_minutes = Column(Integer)
    
    # Availability
    is_active = Column(Boolean, default=True)
    is_online_bookable = Column(Boolean, default=True)
    
    # Requirements
    requirements = Column(Text)  # JSON string for special requirements
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="services")
    bookings = relationship("Booking", back_populates="service", lazy='dynamic')
    
    def __repr__(self):
        return f'<Service {self.name} by {self.vendor.business_name}>'
    
    def to_dict(self):
        """Convert service to dictionary"""
        return {
            'id': self.id,
            'vendor_id': self.vendor_id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'base_price': self.base_price,
            'price_unit': self.price_unit,
            'duration_minutes': self.duration_minutes,
            'is_active': self.is_active,
            'is_online_bookable': self.is_online_bookable,
            'requirements': self.requirements,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
