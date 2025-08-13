
from datetime import datetime
from api.extensions import db

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, jti):
        self.jti = jti
    
    @classmethod
    def is_token_revoked(cls, jti):
        """Check if a token is revoked."""
        return cls.query.filter_by(jti=jti).first() is not None
    
    @classmethod
    def revoke_token(cls, jti):
        """Add token to blocklist."""
        if not cls.is_token_revoked(jti):
            revoked_token = cls(jti=jti)
            db.session.add(revoked_token)
            db.session.commit()
    
    def __repr__(self):
        return f'<TokenBlocklist {self.jti}>'
