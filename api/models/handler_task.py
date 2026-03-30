
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from ..extensions import db


class HandlerTask(db.Model):
    """Handler task model for travel coordination activities"""
    __tablename__ = 'handler_tasks'
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    passport_request_id = Column(Integer, ForeignKey('passport_requests.id'), nullable=False)
    handler_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_by_user_id = Column(Integer, ForeignKey('users.id'))
    
    # Task details
    task_type = Column(String(100), nullable=False)  # pickup, transport, documentation, delivery
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(SQLEnum('low', 'medium', 'high', 'urgent', name='task_priority'), default='medium')
    
    # Status tracking
    status = Column(SQLEnum(
        'pending', 'accepted', 'in_progress', 'completed', 
        'cancelled', 'failed', name='task_status'
    ), default='pending')
    
    # Scheduling
    scheduled_date = Column(DateTime)
    estimated_duration = Column(Integer)  # in minutes
    
    # Location data
    pickup_location = Column(Text)
    delivery_location = Column(Text)
    current_location = Column(Text)
    
    # GPS coordinates
    pickup_latitude = Column(Float)
    pickup_longitude = Column(Float)
    delivery_latitude = Column(Float)
    delivery_longitude = Column(Float)
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    milestone_checklist = Column(Text)  # JSON array of milestones
    
    # Communication
    handler_notes = Column(Text)
    customer_updates = Column(Text)
    
    # Timestamps
    assigned_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    passport_request = relationship("PassportRequest", back_populates="handler_tasks")
    handler = relationship("User", foreign_keys=[handler_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])
    
    def __repr__(self):
        return f'<HandlerTask {self.title} for PassportRequest {self.passport_request_id}>'
    
    def update_progress(self, percentage, notes=None):
        """Update task progress"""
        self.progress_percentage = min(100, max(0, percentage))
        if notes:
            self.handler_notes = notes
        if percentage >= 100:
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert handler task to dictionary"""
        return {
            'id': self.id,
            'passport_request_id': self.passport_request_id,
            'handler_id': self.handler_id,
            'task_type': self.task_type,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'estimated_duration': self.estimated_duration,
            'pickup_location': self.pickup_location,
            'delivery_location': self.delivery_location,
            'current_location': self.current_location,
            'progress_percentage': self.progress_percentage,
            'handler_notes': self.handler_notes,
            'customer_updates': self.customer_updates,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
