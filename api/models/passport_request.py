
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from ..extensions import db


class PassportRequest(db.Model):
    """FurrWings passport request model for international travel"""
    __tablename__ = 'passport_requests'
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    pet_id = Column(Integer, ForeignKey('pets.id'), nullable=False)
    requested_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_handler_id = Column(Integer, ForeignKey('users.id'))
    
    # Travel details
    origin_country = Column(String(100), nullable=False, default='India')
    destination_country = Column(String(100), nullable=False)
    departure_date = Column(DateTime)
    return_date = Column(DateTime)
    travel_purpose = Column(String(200))
    
    # Status tracking
    status = Column(SQLEnum(
        'draft', 'submitted', 'documents_review', 'health_check_pending',
        'handler_assigned', 'in_transit', 'quarantine', 'completed', 
        'cancelled', 'rejected', name='passport_status'
    ), default='draft')
    
    # Pricing
    estimated_cost = Column(Float)
    final_cost = Column(Float)
    payment_status = Column(SQLEnum(
        'pending', 'partial', 'paid', 'refunded', name='payment_status'
    ), default='pending')
    
    # Requirements checklist (JSON)
    requirements_checklist = Column(Text)  # JSON object
    completion_percentage = Column(Integer, default=0)
    
    # Communication
    customer_notes = Column(Text)
    handler_notes = Column(Text)
    rejection_reason = Column(Text)
    
    # Timeline tracking
    submitted_at = Column(DateTime)
    approved_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # QR code for tracking
    qr_code = Column(String(100), unique=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pet = relationship("Pet", back_populates="passport_requests")
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    assigned_handler = relationship("User", foreign_keys=[assigned_handler_id])
    handler_tasks = relationship("HandlerTask", back_populates="passport_request", lazy='dynamic')
    
    def __repr__(self):
        return f'<PassportRequest {self.id}: {self.pet.name} to {self.destination_country}>'
    
    def generate_qr_code(self):
        """Generate unique QR code for tracking"""
        import secrets
        self.qr_code = f"FB-{self.id}-{secrets.token_hex(4).upper()}"
    
    def to_dict(self):
        """Convert passport request to dictionary"""
        return {
            'id': self.id,
            'pet_id': self.pet_id,
            'origin_country': self.origin_country,
            'destination_country': self.destination_country,
            'departure_date': self.departure_date.isoformat() if self.departure_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'travel_purpose': self.travel_purpose,
            'status': self.status,
            'estimated_cost': self.estimated_cost,
            'final_cost': self.final_cost,
            'payment_status': self.payment_status,
            'completion_percentage': self.completion_percentage,
            'customer_notes': self.customer_notes,
            'handler_notes': self.handler_notes,
            'rejection_reason': self.rejection_reason,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'qr_code': self.qr_code,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
