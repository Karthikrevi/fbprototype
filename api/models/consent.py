
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..extensions import db


class Consent(db.Model):
    """GDPR consent management model"""
    __tablename__ = 'consents'
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Consent details
    purpose = Column(String(200), nullable=False)  # analytics, marketing, essential, etc.
    purpose_description = Column(Text)
    consent_given = Column(Boolean, nullable=False, default=False)
    
    # Legal basis
    legal_basis = Column(String(100))  # consent, legitimate_interest, contract, etc.
    
    # Collection context
    consent_source = Column(String(100))  # cookie_banner, registration, settings, etc.
    collection_method = Column(String(100))  # web, mobile, api, etc.
    user_agent = Column(Text)
    ip_address = Column(String(45))
    
    # Consent lifecycle
    consent_version = Column(String(50), default='1.0')
    consent_language = Column(String(10), default='en')
    parent_consent_id = Column(Integer, ForeignKey('consents.id'))  # For consent updates
    
    # Withdrawal tracking
    is_withdrawn = Column(Boolean, default=False)
    withdrawn_at = Column(DateTime)
    withdrawal_reason = Column(Text)
    
    # Expiry
    expires_at = Column(DateTime)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="consents", foreign_keys=[user_id])
    parent_consent = relationship("Consent", remote_side=[id])
    child_consents = relationship("Consent", remote_side=[parent_consent_id])
    
    def __repr__(self):
        return f'<Consent {self.purpose} for User {self.user_id}>'
    
    @property
    def is_active(self):
        """Check if consent is currently active"""
        if self.is_withdrawn:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return self.consent_given
    
    @property
    def is_expired(self):
        """Check if consent has expired"""
        return self.expires_at and self.expires_at < datetime.utcnow()
    
    def withdraw(self, reason=None):
        """Withdraw consent"""
        self.is_withdrawn = True
        self.withdrawn_at = datetime.utcnow()
        if reason:
            self.withdrawal_reason = reason
    
    def to_dict(self):
        """Convert consent to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'purpose': self.purpose,
            'purpose_description': self.purpose_description,
            'consent_given': self.consent_given,
            'legal_basis': self.legal_basis,
            'consent_source': self.consent_source,
            'collection_method': self.collection_method,
            'consent_version': self.consent_version,
            'consent_language': self.consent_language,
            'is_withdrawn': self.is_withdrawn,
            'withdrawn_at': self.withdrawn_at.isoformat() if self.withdrawn_at else None,
            'withdrawal_reason': self.withdrawal_reason,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
