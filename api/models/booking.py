
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..extensions import db


class Booking(db.Model):
    """Booking model for service appointments"""
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    pet_id = Column(Integer, ForeignKey('pets.id'), nullable=False)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    
    # Booking details
    booking_date = Column(DateTime, nullable=False)
    estimated_duration = Column(Integer)  # in minutes
    
    # Status tracking
    status = Column(SQLEnum(
        'pending', 'confirmed', 'in_progress', 'completed', 
        'cancelled', 'no_show', name='booking_status'
    ), default='pending')
    
    # Pricing
    quoted_price = Column(Float)
    final_price = Column(Float)
    payment_status = Column(SQLEnum(
        'pending', 'partial', 'paid', 'refunded', name='payment_status'
    ), default='pending')
    
    # Notes and communication
    customer_notes = Column(Text)
    vendor_notes = Column(Text)
    cancellation_reason = Column(Text)
    
    # Completion tracking
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pet = relationship("Pet", back_populates="bookings")
    vendor = relationship("Vendor", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    
    def __repr__(self):
        return f'<Booking {self.id}: {self.pet.name} at {self.vendor.business_name}>'
    
    @property
    def actual_duration_minutes(self):
        """Calculate actual duration if completed"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None
    
    def to_dict(self):
        """Convert booking to dictionary"""
        return {
            'id': self.id,
            'pet_id': self.pet_id,
            'vendor_id': self.vendor_id,
            'service_id': self.service_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'estimated_duration': self.estimated_duration,
            'status': self.status,
            'quoted_price': self.quoted_price,
            'final_price': self.final_price,
            'payment_status': self.payment_status,
            'customer_notes': self.customer_notes,
            'vendor_notes': self.vendor_notes,
            'cancellation_reason': self.cancellation_reason,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'actual_duration_minutes': self.actual_duration_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
