
from .auth import auth_bp
from .pets import pets_bp

def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(pets_bp)
