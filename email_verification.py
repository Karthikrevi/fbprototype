
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app
import os

# Use app secret key or create a dedicated email verification secret
EMAIL_SECRET_KEY = os.environ.get('EMAIL_SECRET_KEY', 'email_verification_secret_key_2024')

def generate_email_token(email):
    """
    Generate a secure, time-limited email verification token.
    
    Args:
        email (str): Email address to generate token for
        
    Returns:
        str: Secure token that expires in 10 minutes
    """
    serializer = URLSafeTimedSerializer(EMAIL_SECRET_KEY)
    return serializer.dumps(email, salt='email-verification')

def confirm_email_token(token, expiration=600):
    """
    Confirm email verification token and return the email address.
    
    Args:
        token (str): The token to verify
        expiration (int): Token expiration time in seconds (default: 600 = 10 minutes)
        
    Returns:
        str: Email address if token is valid
        
    Raises:
        SignatureExpired: If token has expired
        BadSignature: If token is invalid
    """
    serializer = URLSafeTimedSerializer(EMAIL_SECRET_KEY)
    
    try:
        email = serializer.loads(token, salt='email-verification', max_age=expiration)
        return email
    except SignatureExpired:
        raise SignatureExpired("The verification link has expired. Please request a new one.")
    except BadSignature:
        raise BadSignature("Invalid verification token. Please check the link or request a new one.")
