"""
Copyright (c) 2025 Monster Spawned Studios | https://monsterspawned.studio | All rights reserved.

A utility module to handle security-related tasks.
"""

import hashlib
import os
import string
from typing import Optional
from urllib.parse import urlparse

from .logger import get_logger

logger = get_logger("Security Utils")


async def is_safe_url(url: str) -> bool:
    """
    Check if a URL is safe to access.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is safe, False otherwise.
    """
    try:
        parsed_url = urlparse(url)
        return parsed_url.scheme in ["http", "https"] and parsed_url.netloc
    except ValueError:
        return False

def generate_key() -> str:
    """
    Generate a 256-bit key for AES-GCM encryption.

    Returns:
        str: The hex-encoded key.
    """
    return os.urandom(32).hex()


def encrypt_string(data: str, key: str) -> str:
    """
    Encrypt a string using AES-256-GCM.

    Args:
        data (str): The string to encrypt.
        key (str): The hex-encoded encryption key.

    Returns:
        str: The encrypted string (nonce + ciphertext) encoded in hex.
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        logger.error("Cryptography library not found. Please install it using 'pip install cryptography' through the terminal or using the 'pipinstall cryptography' command in the RedBot console.")
        return ""

    if not data or not key:
        return ""

    try:
        key_bytes = bytes.fromhex(key)
        aesgcm = AESGCM(key_bytes)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
        return (nonce + ciphertext).hex()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return ""


def decrypt_string(data: str, key: str) -> str:
    """
    Decrypt a string using AES-256-GCM.

    Args:
        data (str): The hex-encoded encrypted string (nonce + ciphertext).
        key (str): The hex-encoded encryption key.

    Returns:
        str: The decrypted string.
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        logger.error("Cryptography library not found. Please install it using 'pip install cryptography' through the terminal or using the 'pipinstall cryptography' command in the RedBot console.")
        return ""

    if not data or not key:
        return ""

    try:
        key_bytes = bytes.fromhex(key)
        aesgcm = AESGCM(key_bytes)
        data_bytes = bytes.fromhex(data)
        nonce = data_bytes[:12]
        ciphertext = data_bytes[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return ""

