import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()

# We expect a base64 encoded 32-byte (256-bit) key
_ENCRYPTION_KEY_B64 = os.getenv("ENCRYPTION_MASTER_KEY")
_key = base64.b64decode(_ENCRYPTION_KEY_B64) if _ENCRYPTION_KEY_B64 else None

def get_aesgcm() -> AESGCM:
    """Returns the AESGCM cipher initialized with the Master Key."""
    if not _key:
        raise ValueError("ENCRYPTION_MASTER_KEY is not set in the environment variables.")
    return AESGCM(_key)

def encrypt_text(plain_text: str) -> str:
    """
    Encrypts plain text using true AES-256-GCM and returns a base64 encoded 
    string containing the generated nonce + ciphertext.
    """
    if not plain_text:
        return plain_text
    
    aesgcm = get_aesgcm()
    # GCM strongly recommends a 96-bit (12-byte) random nonce
    nonce = os.urandom(12)  
    data = plain_text.encode('utf-8')
    
    # Encrypt the data. The authentication tag is automatically appended to the ciphertext.
    ciphertext = aesgcm.encrypt(nonce, data, associated_data=None)
    
    # Prepend the nonce to the ciphertext so we can extract it during decryption
    encrypted_blob = nonce + ciphertext
    return base64.b64encode(encrypted_blob).decode('utf-8')

def decrypt_text(encrypted_b64: str) -> str:
    """
    Decrypts a base64 encoded string containing the nonce + ciphertext using AES-256-GCM.
    Automatically verifies data integrity using the GCM auth tag.
    """
    if not encrypted_b64:
        return encrypted_b64
        
    aesgcm = get_aesgcm()
    encrypted_blob = base64.b64decode(encrypted_b64)
    
    # Extract the 12-byte nonce from the beginning of the blob
    nonce = encrypted_blob[:12]
    ciphertext = encrypted_blob[12:]
    
    # Decrypt and verify integrity
    decrypted_data = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    return decrypted_data.decode('utf-8')

def generate_master_key() -> str:
    """
    Helper to generate a new 256-bit key. 
    Use this once to set the ENCRYPTION_MASTER_KEY in your .env file.
    """
    key = AESGCM.generate_key(bit_length=256)
    return base64.b64encode(key).decode('utf-8')
