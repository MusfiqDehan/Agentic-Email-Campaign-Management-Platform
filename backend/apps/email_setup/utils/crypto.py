import base64
import hashlib
from django.conf import settings
from cryptography.fernet import Fernet


def get_encryption_key():
    """
    Derives a 32-byte key from Django's SECRET_KEY for Fernet.
    In a production environment, it's recommended to generate a key using
    Fernet.generate_key() and store it securely.
    """
    # Check if a dedicated encryption key is provided
    if hasattr(settings, 'EMAIL_CONFIG_ENCRYPTION_KEY'):
        encryption_key = settings.EMAIL_CONFIG_ENCRYPTION_KEY
        # If it's already a proper Fernet key, return it
        if isinstance(encryption_key, str) and len(encryption_key) == 44:
            try:
                # Validate it's a proper base64 key by trying to create a Fernet instance
                Fernet(encryption_key.encode())
                return encryption_key.encode()
            except Exception:
                pass
    
    # Fallback: derive from SECRET_KEY
    secret_key = settings.SECRET_KEY
    if not secret_key:
        raise ValueError("Django SECRET_KEY is not configured")
    
    # Use SHA-256 to hash the secret key to a 32-byte value, then base64 encode
    key_bytes = hashlib.sha256(secret_key.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_data(data: str) -> str:
    """Encrypts a string."""
    if not data:
        return data
    
    try:
        encryption_key = get_encryption_key()
        f = Fernet(encryption_key)
        encrypted_data = f.encrypt(data.encode('utf-8'))
        return encrypted_data.decode('utf-8')
    except Exception as e:
        # For debugging, include the actual error in logs
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Encryption failed: {e}")
        # In production, you might want to raise the exception instead of returning original data
        raise ValueError(f"Failed to encrypt data: {str(e)}")


def decrypt_data(encrypted_data: str) -> str:
    """Decrypts an encrypted string."""
    if not encrypted_data:
        return encrypted_data
        
    try:
        encryption_key = get_encryption_key()
        f = Fernet(encryption_key)
        decrypted_data = f.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_data.decode('utf-8')
    except Exception as e:
        # For debugging, include the actual error in logs
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Decryption failed, might be legacy unencrypted data: {e}")
        # If decryption fails (e.g., data is not encrypted or key is wrong),
        # return the original data. This handles legacy non-encrypted passwords.
        return encrypted_data