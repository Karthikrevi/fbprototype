
from itsdangerous import URLSafeTimedSerializer
import os
from datetime import datetime

# Use your app's secret key or generate one
SECRET_KEY = 'furrbutler_secret_key'  # In production, use environment variable

def generate_email_token(email):
    """Generate a secure, time-limited email verification token"""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt='email-verification')

def confirm_email_token(token, max_age=600):  # 10 minutes = 600 seconds
    """Confirm email token and return email if valid"""
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt='email-verification', max_age=max_age)
        return email
    except Exception as e:
        return None

def send_verification_email(email, token):
    """Mock email sending - in production, integrate with your email service"""
    verification_link = f"http://localhost:5000/verify_email/{token}"
    
    # For now, just print to console (replace with actual email sending)
    print(f"""
📧 EMAIL VERIFICATION
===================
To: {email}
Subject: Verify your FurrButler account

Please click the link below to verify your email address:
{verification_link}

This link will expire in 10 minutes.

Best regards,
FurrButler Team
    """)
    
    return True
