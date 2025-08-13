
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .extensions import db, jwt, mail, limiter
from .config import Config
from .rbac import init_rbac


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    
    # CORS configuration
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['http://localhost:3000']))
    
    # Database migrations
    Migrate(app, db)
    
    # Initialize RBAC
    init_rbac(app)
    
    # Register blueprints
    from .blueprints.auth import bp as auth_bp
    from .blueprints.pets import bp as pets_bp
    from .blueprints.vendors import bp as vendors_bp
    from .blueprints.bookings import bp as bookings_bp
    from .blueprints.passport import bp as passport_bp
    from .blueprints.handlers import bp as handlers_bp
    from .blueprints.isolation import bp as isolation_bp
    from .blueprints.ngo import bp as ngo_bp
    from .blueprints.govt import bp as govt_bp
    from .blueprints.dsr import bp as dsr_bp
    from .blueprints.consent import bp as consent_bp
    from .blueprints.admin import bp as admin_bp
    from .blueprints.files import bp as files_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(pets_bp, url_prefix='/api/pets')
    app.register_blueprint(vendors_bp, url_prefix='/api/vendors')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
    app.register_blueprint(passport_bp, url_prefix='/api/passport')
    app.register_blueprint(handlers_bp, url_prefix='/api/handlers')
    app.register_blueprint(isolation_bp, url_prefix='/api/isolation')
    app.register_blueprint(ngo_bp, url_prefix='/api/ngo')
    app.register_blueprint(govt_bp, url_prefix='/api/govt')
    app.register_blueprint(dsr_bp, url_prefix='/api/dsr')
    app.register_blueprint(consent_bp, url_prefix='/api/consent')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'furrbutler-api'}
    
    # Error handlers
    from .error_handlers import register_error_handlers
    register_error_handlers(app)
    
    return app
