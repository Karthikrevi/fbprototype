
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..extensions import db


class Document(db.Model):
    """Document model for file management and verification"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    
    # Foreign keys
    pet_id = Column(Integer, ForeignKey('pets.id'))
    uploaded_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Document details
    document_type = Column(String(100), nullable=False)  # microchip, vaccination, health_cert, etc.
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Metadata
    title = Column(String(200))
    description = Column(Text)
    tags = Column(Text)  # JSON array of tags
    
    # Verification & compliance
    verification_status = Column(SQLEnum(
        'pending', 'verified', 'rejected', 'expired', name='verification_status'
    ), default='pending')
    verified_by_user_id = Column(Integer, ForeignKey('users.id'))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    
    # Digital signature (F-DSC)
    is_digitally_signed = Column(Boolean, default=False)
    signature_hash = Column(String(256))
    signed_by_user_id = Column(Integer, ForeignKey('users.id'))
    signed_at = Column(DateTime)
    
    # Access control
    is_public = Column(Boolean, default=False)
    access_level = Column(String(50), default='private')  # private, restricted, public
    
    # Retention policy
    retention_days = Column(Integer)
    expires_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pet = relationship("Pet", back_populates="documents")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])
    signed_by = relationship("User", foreign_keys=[signed_by_user_id])
    
    def __repr__(self):
        return f'<Document {self.title or self.original_filename}>'
    
    @property
    def is_expired(self):
        """Check if document is expired"""
        return self.expires_at and self.expires_at < datetime.utcnow()
    
    def to_dict(self):
        """Convert document to dictionary"""
        return {
            'id': self.id,
            'pet_id': self.pet_id,
            'document_type': self.document_type,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'title': self.title,
            'description': self.description,
            'verification_status': self.verification_status,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verification_notes': self.verification_notes,
            'is_digitally_signed': self.is_digitally_signed,
            'signed_at': self.signed_at.isoformat() if self.signed_at else None,
            'is_public': self.is_public,
            'access_level': self.access_level,
            'is_expired': self.is_expired,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
