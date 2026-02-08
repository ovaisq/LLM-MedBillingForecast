# encryption.py
# ©2024, Ovais Quraishi

"""This module provides functions for encrypting and decrypting
    text using the Fernet cryptography library.
"""

from cryptography.fernet import Fernet
from config import get_config, get_config_with_defaults, ConfigError

# Try to get config, use defaults if file not found
try:
    CONFIG = get_config()
    ENCRYPTION_KEY = CONFIG.get('service', 'ENCRYPTION_KEY')
except (FileNotFoundError, ConfigError):
    # Use defaults for imports to work
    CONFIG = get_config_with_defaults()
    ENCRYPTION_KEY = CONFIG.get('service', 'ENCRYPTION_KEY')


def load_key():
    """Loads a key used to encrypt and decrypt text.
    """

    filename = ENCRYPTION_KEY
    try:
        with open(filename, 'rb') as key_file:
            key = key_file.read()
        return key
    except FileNotFoundError:
        raise FileNotFoundError(f"Encryption key file '{filename}' not found. "
                               "Create it using: python tools/generate_keys.py")


def encrypt_text(text):
    """Encrypts a piece of text using the loaded key.
    """

    key = load_key()
    cipher_suite = Fernet(key)
    encoded_text = text.encode()
    encrypted_text = cipher_suite.encrypt(encoded_text)
    return encrypted_text


def decrypt_text(encrypted_text):
    """Decrypts a piece of encrypted text using the loaded key.
    """

    key = load_key()
    cipher_suite = Fernet(key)
    decrypted_text = cipher_suite.decrypt(encrypted_text)
    decoded_text = decrypted_text.decode()
    return decoded_text
