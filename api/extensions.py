
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)

def init_extensions(app):
    """Initialize all extensions with the Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    limiter.init_app(app)
    
    # JWT Configuration
    from api.models.token_blocklist import TokenBlocklist
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': {'code': 'TOKEN_EXPIRED', 'message': 'Token has expired'}}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': {'code': 'INVALID_TOKEN', 'message': 'Invalid token'}}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': {'code': 'MISSING_TOKEN', 'message': 'Authorization token required'}}, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return {'error': {'code': 'TOKEN_REVOKED', 'message': 'Token has been revoked'}}, 401
