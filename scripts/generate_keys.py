#!/usr/bin/env python3
"""
Generate secure keys for Email Agent AI configuration.

Usage:
    python scripts/generate_keys.py
"""
import secrets
from cryptography.fernet import Fernet


def generate_secret_key() -> str:
    """Generate a secure SECRET_KEY (hex format)"""
    return secrets.token_hex(32)


def generate_encryption_key() -> str:
    """Generate a valid Fernet ENCRYPTION_KEY (base64 format)"""
    return Fernet.generate_key().decode()


def main():
    print("=" * 60)
    print("Email Agent AI - Key Generator")
    print("=" * 60)
    print()
    print("Add these to your .env file:")
    print()
    print("# JWT and session signing")
    print(f"SECRET_KEY={generate_secret_key()}")
    print()
    print("# Fernet encryption for credentials")
    print(f"ENCRYPTION_KEY={generate_encryption_key()}")
    print()
    print("=" * 60)
    print("⚠️  WARNING: Changing ENCRYPTION_KEY will make existing")
    print("    encrypted data unreadable. Only change during setup")
    print("    or if you're resetting the database.")
    print("=" * 60)


if __name__ == "__main__":
    main()
