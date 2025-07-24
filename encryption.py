
#!/usr/bin/env python3
"""
GDPR-Compliant Encryption Module
===============================

This module provides Fernet-based encryption for protecting PII data
in compliance with GDPR requirements. It handles encryption/decryption
of sensitive user data like emails and phone numbers.

Features:
- Fernet symmetric encryption (AES 128 in CBC mode)
- Automatic key generation and loading
- Proper string/bytes conversion for SQLite storage
- GDPR-compliant data protection
"""

import os
from cryptography.fernet import Fernet
from typing import Union, Optional

# Constants
KEY_FILE = 'secret.key'

def generate_key() -> bytes:
    """
    Generate a new Fernet encryption key.
    
    This should only be called once during initial setup.
    The key is used for all encryption/decryption operations.
    
    Returns:
        bytes: A 32-byte base64-encoded key suitable for Fernet
    """
    return Fernet.generate_key()

def save_key(key: bytes) -> bool:
    """
    Save the encryption key to a file.
    
    Args:
        key (bytes): The Fernet key to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(key)
        
        # Set restrictive permissions (readable only by owner)
        os.chmod(KEY_FILE, 0o600)
        return True
        
    except Exception as e:
        print(f"❌ Error saving key: {e}")
        return False

def load_key() -> Optional[bytes]:
    """
    Load the encryption key from file.
    
    If the key file doesn't exist, generates a new key and saves it.
    
    Returns:
        Optional[bytes]: The Fernet key, or None if loading fails
    """
    try:
        # Check if key file exists
        if not os.path.exists(KEY_FILE):
            print("🔑 Key file not found. Generating new encryption key...")
            
            # Generate new key
            new_key = generate_key()
            
            # Save the key
            if save_key(new_key):
                print(f"✅ New encryption key generated and saved to {KEY_FILE}")
                return new_key
            else:
                print("❌ Failed to save new key")
                return None
        
        # Load existing key
        with open(KEY_FILE, 'rb') as key_file:
            key = key_file.read()
            
        print("✅ Encryption key loaded successfully")
        return key
        
    except Exception as e:
        print(f"❌ Error loading key: {e}")
        return None

def get_fernet_cipher() -> Optional[Fernet]:
    """
    Get a Fernet cipher instance with the loaded key.
    
    Returns:
        Optional[Fernet]: Fernet cipher instance, or None if key loading fails
    """
    key = load_key()
    if key is None:
        return None
        
    try:
        return Fernet(key)
    except Exception as e:
        print(f"❌ Error creating Fernet cipher: {e}")
        return None

def encrypt_data(data: Union[str, bytes]) -> Optional[str]:
    """
    Encrypt data using Fernet encryption.
    
    Args:
        data (Union[str, bytes]): The data to encrypt (string or bytes)
        
    Returns:
        Optional[str]: Encrypted data as a base64-encoded string suitable 
                      for SQLite storage, or None if encryption fails
    """
    if data is None:
        return None
        
    try:
        # Get Fernet cipher
        cipher = get_fernet_cipher()
        if cipher is None:
            return None
        
        # Convert string to bytes if necessary
        if isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
            
        # Encrypt the data
        encrypted_bytes = cipher.encrypt(data_bytes)
        
        # Convert to string for SQLite storage
        encrypted_string = encrypted_bytes.decode('utf-8')
        
        return encrypted_string
        
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        return None

def decrypt_data(token: Union[str, bytes]) -> Optional[str]:
    """
    Decrypt data using Fernet decryption.
    
    Args:
        token (Union[str, bytes]): The encrypted token to decrypt
        
    Returns:
        Optional[str]: Decrypted data as a string, or None if decryption fails
    """
    if token is None:
        return None
        
    try:
        # Get Fernet cipher
        cipher = get_fernet_cipher()
        if cipher is None:
            return None
            
        # Convert string to bytes if necessary
        if isinstance(token, str):
            token_bytes = token.encode('utf-8')
        else:
            token_bytes = token
            
        # Decrypt the data
        decrypted_bytes = cipher.decrypt(token_bytes)
        
        # Convert back to string
        decrypted_string = decrypted_bytes.decode('utf-8')
        
        return decrypted_string
        
    except Exception as e:
        print(f"❌ Decryption error: {e}")
        return None

def is_encryption_available() -> bool:
    """
    Check if encryption is properly configured and available.
    
    Returns:
        bool: True if encryption is ready to use, False otherwise
    """
    try:
        cipher = get_fernet_cipher()
        return cipher is not None
    except:
        return False

def test_encryption() -> bool:
    """
    Test the encryption/decryption functionality.
    
    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        # Test data
        test_data = "test@example.com"
        
        print("🧪 Testing encryption functionality...")
        
        # Encrypt
        encrypted = encrypt_data(test_data)
        if encrypted is None:
            print("❌ Encryption test failed")
            return False
            
        print(f"✅ Encryption successful: {encrypted[:20]}...")
        
        # Decrypt
        decrypted = decrypt_data(encrypted)
        if decrypted is None:
            print("❌ Decryption test failed")
            return False
            
        print(f"✅ Decryption successful: {decrypted}")
        
        # Verify
        if decrypted == test_data:
            print("✅ Encryption/decryption test passed!")
            return True
        else:
            print("❌ Data mismatch in encryption test")
            return False
            
    except Exception as e:
        print(f"❌ Encryption test error: {e}")
        return False

if __name__ == "__main__":
    """
    Run encryption tests when script is executed directly.
    """
    print("🔐 GDPR-Compliant Encryption Module")
    print("=" * 40)
    
    # Check if encryption is available
    if is_encryption_available():
        print("✅ Encryption system is ready")
        
        # Run test
        test_encryption()
        
    else:
        print("❌ Encryption system not available")
        
    print("\n📝 Usage in your Flask app:")
    print("from encryption import encrypt_data, decrypt_data")
    print("encrypted_email = encrypt_data('user@example.com')")
    print("original_email = decrypt_data(encrypted_email)")
