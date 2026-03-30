
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Float, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from ..extensions import db


class IsolationStay(db.Model):
    """Isolation stay model for quarantine and isolation management"""
    __tablename__ = 'isolation_stays'
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    pet_id = Column(Integer, ForeignKey('pets.id'), nullable=False)
    facility_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Isolation center user
    passport_request_id = Column(Integer, ForeignKey('passport_requests.id'))
    
    # Stay details
    stay_type = Column(String(50), nullable=False)  # quarantine, isolation, boarding
    check_in_date = Column(Date, nullable=False)
    planned_checkout_date = Column(Date)
    actual_checkout_date = Column(Date)
    
    # Status tracking
    status = Column(SQLEnum(
        'booked', 'checked_in', 'in_progress', 'ready_for_checkout', 
        'checked_out', 'cancelled', 'emergency_exit', name='stay_status'
    ), default='booked')
    
    # Facility details
    facility_name = Column(String(200), nullable=False)
    room_number = Column(String(50))
    room_type = Column(String(100))
    
    # Health monitoring
    health_status = Column(String(50), default='good')  # good, fair, poor, critical
    daily_health_notes = Column(Text)
    temperature_log = Column(Text)  # JSON array of daily temperatures
    weight_log = Column(Text)  # JSON array of daily weights
    
    # Care requirements
    special_instructions = Column(Text)
    medication_schedule = Column(Text)  # JSON object
    feeding_schedule = Column(Text)  # JSON object
    exercise_requirements = Column(Text)
    
    # Media and documentation
    daily_photos = Column(Text)  # JSON array of photo URLs
    daily_videos = Column(Text)  # JSON array of video URLs
    incident_reports = Column(Text)  # JSON array of incident reports
    
    # Pricing
    daily_rate = Column(Float)
    total_cost = Column(Float)
    payment_status = Column(SQLEnum(
        'pending', 'partial', 'paid', 'refunded', name='payment_status'
    ), default='pending')
    
    # Emergency contacts
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(20))
    emergency_vet_name = Column(String(200))
    emergency_vet_phone = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    checked_in_at = Column(DateTime)
    checked_out_at = Column(DateTime)
    
    # Relationships
    pet = relationship("Pet")
    facility = relationship("User", foreign_keys=[facility_user_id])
    passport_request = relationship("PassportRequest")
    
    def __repr__(self):
        return f'<IsolationStay {self.pet.name} at {self.facility_name}>'
    
    @property
    def duration_days(self):
        """Calculate duration of stay"""
        end_date = self.actual_checkout_date or date.today()
        return (end_date - self.check_in_date).days
    
    @property
    def is_active(self):
        """Check if stay is currently active"""
        return self.status in ['checked_in', 'in_progress']
    
    def add_daily_log(self, log_type, data):
        """Add daily log entry"""
        # TODO: Port legacy logic for daily logging
        pass
    
    def to_dict(self):
        """Convert isolation stay to dictionary"""
        return {
            'id': self.id,
            'pet_id': self.pet_id,
            'passport_request_id': self.passport_request_id,
            'stay_type': self.stay_type,
            'check_in_date': self.check_in_date.isoformat() if self.check_in_date else None,
            'planned_checkout_date': self.planned_checkout_date.isoformat() if self.planned_checkout_date else None,
            'actual_checkout_date': self.actual_checkout_date.isoformat() if self.actual_checkout_date else None,
            'status': self.status,
            'facility_name': self.facility_name,
            'room_number': self.room_number,
            'room_type': self.room_type,
            'health_status': self.health_status,
            'daily_health_notes': self.daily_health_notes,
            'special_instructions': self.special_instructions,
            'daily_rate': self.daily_rate,
            'total_cost': self.total_cost,
            'payment_status': self.payment_status,
            'duration_days': self.duration_days,
            'is_active': self.is_active,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'checked_in_at': self.checked_in_at.isoformat() if self.checked_in_at else None,
            'checked_out_at': self.checked_out_at.isoformat() if self.checked_out_at else None
        }
