
from extensions import db
from datetime import datetime
from enum import Enum as PyEnum
import json

class AnimalType(PyEnum):
    PET = 'p'
    STRAY = 's'

class VaccinationMode(PyEnum):
    OUTDOOR = 'outdoor'
    INDOOR = 'indoor'

class VaccinationStatus(PyEnum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'

class BeneficiaryType(PyEnum):
    UDI = 'UDI'
    DRIVE = 'Drive'
    NGO = 'NGO'

class UtilizationStatus(PyEnum):
    PENDING = 'pending'
    COMPLETE = 'complete'

class UserRole(PyEnum):
    NGO_ADMIN = 'ngo_admin'
    NGO_FIELD = 'ngo_field'
    VET = 'vet'
    GOV = 'gov'
    ADMIN = 'admin'

class AggressionLevel(PyEnum):
    FRIENDLY = 'Friendly'
    CAUTIOUS = 'Cautious'
    DO_NOT_APPROACH = 'DoNotApproach'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.Enum(UserRole), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    password_hash = db.Column(db.String(255))
    otp_secret = db.Column(db.String(32))
    ngo_id = db.Column(db.Integer, db.ForeignKey('ngos.id'))
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    ngo = db.relationship('NGO', backref='users')

class NGO(db.Model):
    __tablename__ = 'ngos'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    registration_number = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    district = db.Column(db.String(50))
    state = db.Column(db.String(50), default='Kerala')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Animal(db.Model):
    __tablename__ = 'animals'
    
    id = db.Column(db.Integer, primary_key=True)
    udi = db.Column(db.String(20), unique=True, nullable=False)
    short_id = db.Column(db.String(10), unique=True)
    type = db.Column(db.Enum(AnimalType), nullable=False)
    name = db.Column(db.String(100))
    sex = db.Column(db.String(10))
    color = db.Column(db.String(50))
    breed = db.Column(db.String(100))
    approx_age = db.Column(db.String(20))
    photos_json = db.Column(db.Text)  # JSON array of photo URLs
    aggression_marker = db.Column(db.Enum(AggressionLevel), default=AggressionLevel.FRIENDLY)
    owner_id = db.Column(db.Integer)  # Optional for pets
    ngo_id = db.Column(db.Integer, db.ForeignKey('ngos.id'))
    
    # Geolocation
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    accuracy_m = db.Column(db.Float)
    ward_id = db.Column(db.String(50))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    ngo = db.relationship('NGO', backref='animals')
    creator = db.relationship('User', backref='created_animals')
    
    @property
    def photos(self):
        return json.loads(self.photos_json) if self.photos_json else []
    
    @photos.setter
    def photos(self, value):
        self.photos_json = json.dumps(value)

class Vaccination(db.Model):
    __tablename__ = 'vaccinations'
    
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    type = db.Column(db.String(100), nullable=False)  # Vaccine type
    brand = db.Column(db.String(100))
    batch = db.Column(db.String(50))
    expiry = db.Column(db.Date)
    dose_ml = db.Column(db.Float)
    route = db.Column(db.String(50))  # SC, IM, etc.
    site = db.Column(db.String(100))  # injection site
    date_time = db.Column(db.DateTime, nullable=False)
    next_due = db.Column(db.Date)
    mode = db.Column(db.Enum(VaccinationMode), nullable=False)
    verifier_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    video_url = db.Column(db.String(255))
    video_sha256 = db.Column(db.String(64))
    vet_esign_id = db.Column(db.String(100))
    cert_url = db.Column(db.String(255))
    
    # Geolocation for outdoor vaccinations
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    accuracy_m = db.Column(db.Float)
    
    status = db.Column(db.Enum(VaccinationStatus), default=VaccinationStatus.PENDING)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    review_comments = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    animal = db.relationship('Animal', backref='vaccinations')
    verifier = db.relationship('User', foreign_keys=[verifier_id], backref='verified_vaccinations')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], backref='reviewed_vaccinations')

class Microchip(db.Model):
    __tablename__ = 'microchips'
    
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    chip_id = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    vet_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    animal = db.relationship('Animal', backref='microchips')
    vet = db.relationship('User', backref='microchipped_animals')

class Sterilization(db.Model):
    __tablename__ = 'sterilizations'
    
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    vet_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)
    attachments_json = db.Column(db.Text)  # JSON array of attachment URLs
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    animal = db.relationship('Animal', backref='sterilizations')
    vet = db.relationship('User', backref='sterilized_animals')
    
    @property
    def attachments(self):
        return json.loads(self.attachments_json) if self.attachments_json else []
    
    @attachments.setter
    def attachments(self, value):
        self.attachments_json = json.dumps(value)

class BloodType(db.Model):
    __tablename__ = 'blood_types'
    
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    type_dea = db.Column(db.String(20), nullable=False)  # DEA type
    verified_on = db.Column(db.Date, nullable=False)
    vet_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    animal = db.relationship('Animal', backref='blood_types')
    vet = db.relationship('User', backref='verified_blood_types')

class Donation(db.Model):
    __tablename__ = 'donations'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    donor_public = db.Column(db.Boolean, default=False)
    donor_name = db.Column(db.String(100))
    donor_email = db.Column(db.String(120))
    beneficiary_type = db.Column(db.Enum(BeneficiaryType), nullable=False)
    beneficiary_ref = db.Column(db.String(100))  # UDI, Drive ID, or NGO ID
    date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_ref = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DonationUtilization(db.Model):
    __tablename__ = 'donation_utilizations'
    
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False)
    status = db.Column(db.Enum(UtilizationStatus), default=UtilizationStatus.PENDING)
    amount_utilized = db.Column(db.Float, nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    proof_urls_json = db.Column(db.Text)  # JSON array of receipt/photo URLs
    notes = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    donation = db.relationship('Donation', backref='utilizations')
    updater = db.relationship('User', backref='updated_utilizations')
    
    @property
    def proof_urls(self):
        return json.loads(self.proof_urls_json) if self.proof_urls_json else []
    
    @proof_urls.setter
    def proof_urls(self, value):
        self.proof_urls_json = json.dumps(value)
