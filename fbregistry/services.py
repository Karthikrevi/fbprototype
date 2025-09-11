
import hashlib
import qrcode
import os
import uuid
from datetime import datetime
from io import BytesIO
import base64
import jwt
from flask import current_app, url_for
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from PIL import Image

def luhn_check_digit(sequence: str) -> str:
    """Calculate Luhn check digit for UDI validation"""
    def luhn_checksum(card_num):
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d*2))
        return checksum % 10
    
    return str((10 - luhn_checksum(int(sequence))) % 10)

def generate_udi(state='KL', district_code='TVM') -> tuple:
    """Generate unique UDI and short ID"""
    # Format: KL-TVM-YYYYMMDD-NNNNC
    # where C is Luhn check digit
    today = datetime.now().strftime('%Y%m%d')
    
    # Generate a random 4-digit number
    random_num = str(uuid.uuid4().int)[:4]
    
    # Construct base UDI without check digit
    base_udi = f"{state}-{district_code}-{today}-{random_num}"
    
    # Calculate check digit for the numeric part only
    numeric_part = today + random_num
    check_digit = luhn_check_digit(numeric_part)
    
    # Final UDI
    udi = f"{base_udi}{check_digit}"
    
    # Short ID (last 8 characters including check digit)
    short_id = f"{random_num}{check_digit}"
    
    return udi, short_id

def make_qr_png(payload_url: str, output_path: str) -> bool:
    """Generate QR code PNG for UDI verification URL"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payload_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        img.save(output_path)
        return True
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return False

def sign_jws(payload: dict) -> str:
    """Sign payload using JWS (JWT with HS256 for now)"""
    secret = current_app.config['QR_SIGNING_SECRET']
    return jwt.encode(payload, secret, algorithm='HS256')

def verify_jws(token: str) -> dict:
    """Verify JWS token"""
    try:
        secret = current_app.config['QR_SIGNING_SECRET']
        return jwt.decode(token, secret, algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return None

def hash_video(file_path: str) -> str:
    """Calculate SHA256 hash of video file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error hashing video: {e}")
        return ""

def generate_certificate_pdf(vaccination_id: int) -> bytes:
    """Generate vaccination certificate PDF"""
    from fbregistry.models import Vaccination, Animal
    
    vaccination = Vaccination.query.get(vaccination_id)
    if not vaccination:
        raise ValueError("Vaccination not found")
    
    animal = vaccination.animal
    
    # Create PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "FurrButler Registry - Vaccination Certificate")
    
    # QR Code area (placeholder)
    qr_y = height - 150
    p.setFont("Helvetica", 10)
    p.drawString(450, qr_y, "Scan QR to verify")
    
    # Certificate details
    p.setFont("Helvetica", 12)
    y_position = height - 200
    
    details = [
        f"UDI: {animal.udi}",
        f"Animal Name: {animal.name or 'Unknown'}",
        f"Type: {'Pet' if animal.type.value == 'p' else 'Stray'}",
        f"Breed: {animal.breed or 'Unknown'}",
        f"",
        f"Vaccination Details:",
        f"Type: {vaccination.type}",
        f"Brand: {vaccination.brand}",
        f"Date: {vaccination.date_time.strftime('%Y-%m-%d %H:%M')}",
        f"Next Due: {vaccination.next_due.strftime('%Y-%m-%d') if vaccination.next_due else 'N/A'}",
        f"",
        f"Verified by: {vaccination.verifier.name if vaccination.verifier else 'System'}",
        f"Status: {vaccination.status.value.title()}",
    ]
    
    for detail in details:
        p.drawString(50, y_position, detail)
        y_position -= 20
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(50, 50, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(50, 35, f"Certificate ID: FBR-{vaccination.id}")
    
    # Add verification URL
    verify_url = url_for('public.verify_udi', udi=animal.udi, _external=True)
    p.drawString(50, 20, f"Verify at: {verify_url}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer.getvalue()

def allowed_file(filename: str, allowed_extensions: set = None) -> bool:
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', set())
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def compress_image(image_path: str, max_size_mb: float = 1.0) -> bool:
    """Compress image to target size"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate target file size in bytes
            target_size = max_size_mb * 1024 * 1024
            
            # Start with quality 85
            quality = 85
            
            while quality > 10:
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                
                if buffer.tell() <= target_size:
                    # Save compressed image
                    with open(image_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    return True
                
                quality -= 5
            
            # If still too large, resize image
            width, height = img.size
            img = img.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)
            img.save(image_path, format='JPEG', quality=70, optimize=True)
            
            return True
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False
