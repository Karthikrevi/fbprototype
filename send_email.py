
from flask import url_for
import os

def send_verification_email(email, token):
    """
    Mock email sending function that prints verification URL to console.
    In production, this would integrate with an email service like SendGrid, 
    Amazon SES, or SMTP.
    
    Args:
        email (str): Recipient email address
        token (str): Verification token
    """
    # Generate the full verification URL
    # Using the current Replit domain or localhost for development
    base_url = os.environ.get('REPL_SLUG', 'localhost:5000')
    if not base_url.startswith('http'):
        if 'replit' in base_url or 'repl.co' in base_url:
            base_url = f"https://{base_url}"
        else:
            base_url = f"http://{base_url}"
    
    verification_url = f"{base_url}/verify_email/{token}"
    
    # Mock email content
    email_subject = "🐾 FurrButler - Verify Your Email Address"
    email_body = f"""
Dear FurrButler User,

Thank you for registering with FurrButler! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 10 minutes for security reasons.

If you didn't create an account with FurrButler, please ignore this email.

Best regards,
The FurrButler Team
🐶🐱
    """
    
    # Print to console (mock email sending)
    print("=" * 60)
    print("📧 MOCK EMAIL SENT")
    print("=" * 60)
    print(f"To: {email}")
    print(f"Subject: {email_subject}")
    print(f"Body:\n{email_body}")
    print("=" * 60)
    print(f"🔗 VERIFICATION URL: {verification_url}")
    print("=" * 60)
    
    return True
