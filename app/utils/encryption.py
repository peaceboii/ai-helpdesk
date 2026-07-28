import base64
import hashlib
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# We derive a secure 32-byte Fernet key from the SECRET_KEY in .env.
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-ai-helpdesk-2026")

def _get_fernet_key(secret: str) -> bytes:
    # Use SHA-256 to hash the secret key to exactly 32 bytes
    hashed = hashlib.sha256(secret.encode("utf-8")).digest()
    # Base64 encode the 32 bytes for Fernet
    return base64.urlsafe_b64encode(hashed)

# Initialize the cipher
cipher = Fernet(_get_fernet_key(SECRET_KEY))

def encrypt_string(plain_text: str) -> str:
    """Encrypts a plain text string and returns a base64 encoded cipher text string."""
    if not plain_text:
        return ""
    try:
        encrypted_bytes = cipher.encrypt(plain_text.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except Exception as e:
        print(f"Encryption error: {e}")
        return plain_text

def decrypt_string(cipher_text: str) -> str:
    """Decrypts a base64 encoded cipher text string and returns the decrypted plain text."""
    if not cipher_text:
        return ""
    try:
        decrypted_bytes = cipher.decrypt(cipher_text.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        # If decryption fails (e.g. because it wasn't encrypted, or key changed),
        # return the original text as a fallback.
        print(f"Decryption error: {e}. Returning original.")
        return cipher_text
