from flask import Flask
from api.config import Config
from api.extensions import init_extensions
from api.blueprints import register_blueprints
from api.error_handlers import register_error_handlers

def create_app(config_class=Config):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    return app