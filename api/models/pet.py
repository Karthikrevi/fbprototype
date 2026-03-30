
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..extensions import db


class Pet(db.Model):
    """Pet model for pet profile management"""
    __tablename__ = 'pets'
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Basic info
    name = Column(String(100), nullable=False)
    species = Column(String(50), nullable=False)  # Dog, Cat, Bird, etc.
    breed = Column(String(100))
    gender = Column(String(10))  # Male, Female, Unknown
    date_of_birth = Column(Date)
    
    # Physical characteristics
    weight = Column(Float)  # in kg
    color = Column(String(100))
    distinctive_marks = Column(Text)
    
    # Identification
    microchip_id = Column(String(50), unique=True)
    registration_number = Column(String(100))
    
    # Health info
    blood_type = Column(String(10))
    allergies = Column(Text)
    medical_conditions = Column(Text)
    special_needs = Column(Text)
    
    # Media
    photo_url = Column(String(500))
    
    # Status
    is_active = Column(SQLEnum('active', 'inactive', 'deceased', name='pet_status'), default='active')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="pets")
    bookings = relationship("Booking", back_populates="pet", lazy='dynamic')
    passport_requests = relationship("PassportRequest", back_populates="pet", lazy='dynamic')
    documents = relationship("Document", back_populates="pet", lazy='dynamic')
    
    def __repr__(self):
        return f'<Pet {self.name} ({self.species})>'
    
    @property
    def age_years(self):
        """Calculate pet's age in years"""
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def to_dict(self):
        """Convert pet to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'species': self.species,
            'breed': self.breed,
            'gender': self.gender,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age_years': self.age_years,
            'weight': self.weight,
            'color': self.color,
            'distinctive_marks': self.distinctive_marks,
            'microchip_id': self.microchip_id,
            'registration_number': self.registration_number,
            'blood_type': self.blood_type,
            'allergies': self.allergies,
            'medical_conditions': self.medical_conditions,
            'special_needs': self.special_needs,
            'photo_url': self.photo_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
