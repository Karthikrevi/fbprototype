
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def init_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Create upload directories
    upload_dir = app.config['UPLOAD_DIR']
    for subdir in ['photos', 'videos', 'certificates']:
        os.makedirs(os.path.join(upload_dir, subdir), exist_ok=True)
    
    # Create static QR codes directory
    os.makedirs(os.path.join('static', 'qrcodes'), exist_ok=True)
