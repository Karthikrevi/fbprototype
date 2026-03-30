
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from ..extensions import db


class DSRRequest(db.Model):
    """Data Subject Rights (GDPR) request model"""
    __tablename__ = 'dsr_requests'
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    handled_by_user_id = Column(Integer, ForeignKey('users.id'))
    
    # Request details
    request_type = Column(SQLEnum(
        'access', 'rectification', 'erasure', 'portability', 
        'restriction', 'objection', name='dsr_request_type'
    ), nullable=False)
    
    # Request description
    subject_line = Column(String(300), nullable=False)
    description = Column(Text)
    specific_data_requested = Column(Text)  # JSON array of specific data categories
    
    # Contact information
    requester_email = Column(String(255))
    requester_phone = Column(String(20))
    preferred_contact_method = Column(String(50), default='email')
    
    # Verification
    identity_verified = Column(Boolean, default=False)
    verification_method = Column(String(100))
    verification_notes = Column(Text)
    verified_at = Column(DateTime)
    verified_by_user_id = Column(Integer, ForeignKey('users.id'))
    
    # Processing
    status = Column(SQLEnum(
        'submitted', 'under_review', 'identity_verification_required',
        'processing', 'completed', 'rejected', 'partially_fulfilled',
        name='dsr_status'
    ), default='submitted')
    
    priority = Column(SQLEnum('low', 'medium', 'high', 'urgent', name='dsr_priority'), default='medium')
    
    # Timeline
    due_date = Column(DateTime)  # Legal deadline (usually 30 days)
    completed_at = Column(DateTime)
    extension_requested = Column(Boolean, default=False)
    extension_reason = Column(Text)
    extended_due_date = Column(DateTime)
    
    # Response
    response_provided = Column(Text)
    response_format = Column(String(50))  # json, csv, pdf, etc.
    response_file_path = Column(String(500))
    rejection_reason = Column(Text)
    
    # Internal processing
    internal_notes = Column(Text)
    data_sources_checked = Column(Text)  # JSON array of systems checked
    third_party_notifications = Column(Text)  # JSON array of third parties notified
    
    # Communication log
    communication_log = Column(Text)  # JSON array of communications
    
    # Legal compliance
    legal_basis_for_processing = Column(Text)
    legal_basis_for_refusal = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="dsr_requests", foreign_keys=[user_id])
    handled_by = relationship("User", foreign_keys=[handled_by_user_id])
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])
    
    def __init__(self, **kwargs):
        super(DSRRequest, self).__init__(**kwargs)
        # Set due date to 30 days from creation (GDPR requirement)
        self.due_date = datetime.utcnow() + timedelta(days=30)
    
    def __repr__(self):
        return f'<DSRRequest {self.request_type} for User {self.user_id}>'
    
    @property
    def is_overdue(self):
        """Check if request is overdue"""
        deadline = self.extended_due_date or self.due_date
        return deadline and deadline < datetime.utcnow() and self.status not in ['completed', 'rejected']
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        deadline = self.extended_due_date or self.due_date
        if not deadline:
            return None
        delta = deadline - datetime.utcnow()
        return delta.days
    
    def extend_deadline(self, additional_days, reason):
        """Extend the deadline for processing"""
        self.extension_requested = True
        self.extension_reason = reason
        current_due = self.extended_due_date or self.due_date
        self.extended_due_date = current_due + timedelta(days=additional_days)
    
    def complete_request(self, response, response_format='text', file_path=None):
        """Mark request as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.response_provided = response
        self.response_format = response_format
        if file_path:
            self.response_file_path = file_path
    
    def reject_request(self, reason):
        """Reject the request"""
        self.status = 'rejected'
        self.completed_at = datetime.utcnow()
        self.rejection_reason = reason
    
    def to_dict(self):
        """Convert DSR request to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'request_type': self.request_type,
            'subject_line': self.subject_line,
            'description': self.description,
            'requester_email': self.requester_email,
            'requester_phone': self.requester_phone,
            'preferred_contact_method': self.preferred_contact_method,
            'identity_verified': self.identity_verified,
            'verification_method': self.verification_method,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'extended_due_date': self.extended_due_date.isoformat() if self.extended_due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due,
            'response_provided': self.response_provided,
            'response_format': self.response_format,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
