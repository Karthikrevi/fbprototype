
import os
from flask import Flask
from api.extensions import init_extensions
from api.error_handlers import register_error_handlers


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder='../../templates',
                static_folder='../../static')
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    from api.config import config
    app.config.from_object(config[config_name])
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Override config with environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config.get('SECRET_KEY'))
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config.get('JWT_SECRET_KEY'))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', app.config.get('SQLALCHEMY_DATABASE_URI'))
    
    # Initialize extensions
    init_extensions(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    from api.blueprints.auth import bp as auth_bp
    from api.blueprints.pets import bp as pets_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(pets_bp, url_prefix='/api/pets')
    
    return app
