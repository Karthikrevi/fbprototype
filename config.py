
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET = os.environ.get('JWT_SECRET') or 'jwt-secret-key-change-in-production'
    QR_SIGNING_SECRET = os.environ.get('QR_SIGNING_SECRET') or 'qr-signing-secret'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///fbr.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    ALLOWED_EXTENSIONS = {'mp4', 'jpg', 'jpeg', 'png', 'pdf'}
    
    # JWT settings
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_COOKIE_SECURE = False  # Set to True in production with HTTPS
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_COOKIE_CSRF_PROTECT = False  # Simplified for development
    
    # Map settings
    MAPBOX_TOKEN = os.environ.get('MAPBOX_TOKEN', '')
    
    # State/District codes
    DEFAULT_STATE_CODE = 'KL'
    DEFAULT_DISTRICT_CODE = 'TVM'
