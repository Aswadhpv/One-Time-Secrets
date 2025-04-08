import os
from cryptography.fernet import Fernet

# Use an environment variable for the encryption key or generate one if not set.
encryption_key = os.environ.get("ENCRYPTION_KEY")
if not encryption_key:
    # For production, ensure you set a persistent encryption key.
    encryption_key = Fernet.generate_key().decode()

fernet = Fernet(encryption_key.encode())

def encrypt_secret(plain_text: str) -> str:
    return fernet.encrypt(plain_text.encode()).decode()

def decrypt_secret(encrypted_text: str) -> str:
    return fernet.decrypt(encrypted_text.encode()).decode()
