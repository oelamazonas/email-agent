"""
Utilitaires de sécurité
"""
from cryptography.fernet import Fernet
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from shared.config import settings
import base64
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Password hashing - using modern Argon2 (OWASP recommended)
# Argon2 is more secure than bcrypt: memory-hard, no 72-byte limit
password_hash = PasswordHash((Argon2Hasher(),))

def _get_fernet() -> Fernet:
    """Récupère l'instance Fernet configurée"""
    try:
        # Assurer que la clé est au bon format (urlsafe base64)
        # Si la clé hexadécimale est fournie, ou une chaine simple, cela peut nécessiter une adaptation
        # Pour simplifier, on suppose que ENCRYPTION_KEY est une clé Fernet valide
        # ou on la dérive si nécessaire.
        key = settings.ENCRYPTION_KEY
        return Fernet(key)
    except Exception as e:
        logger.error(f"Error initializing Fernet: {e}")
        raise

def encrypt_password(password: str) -> str:
    """Chiffre un mot de passe"""
    if not password:
        return ""
    
    f = _get_fernet()
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str, return_dict: bool = False) -> str:
    """
    Déchiffre un mot de passe ou credentials.

    Args:
        encrypted_password: Données chiffrées
        return_dict: Si True, retourne le JSON parsé (pour credentials OAuth2)

    Returns:
        String déchiffré ou dict si return_dict=True
    """
    if not encrypted_password:
        return "" if not return_dict else {}

    f = _get_fernet()
    decrypted = f.decrypt(encrypted_password.encode()).decode()

    if return_dict:
        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            logger.warning("Failed to parse decrypted data as JSON")
            return {}

    return decrypted


def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """
    Chiffre des credentials (dict) pour stockage en DB.

    Args:
        credentials: Dict avec les credentials (OAuth2, IMAP config, etc.)

    Returns:
        String chiffré base64
    """
    if not credentials:
        return ""

    f = _get_fernet()
    json_str = json.dumps(credentials)
    return f.encrypt(json_str.encode()).decode()


def decrypt_credentials(encrypted_credentials: str) -> Dict[str, Any]:
    """
    Déchiffre des credentials depuis la DB.

    Args:
        encrypted_credentials: String chiffré

    Returns:
        Dict avec les credentials déchiffrés
    """
    if not encrypted_credentials:
        return {}

    f = _get_fernet()
    decrypted = f.decrypt(encrypted_credentials.encode()).decode()

    try:
        return json.loads(decrypted)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse credentials JSON: {e}")
        raise ValueError("Invalid credentials format")


def hash_password(password: str) -> str:
    """
    Hash un mot de passe avec Argon2.

    Argon2 advantages over bcrypt:
    - Memory-hard (resistant to GPU attacks)
    - No password length limit (bcrypt has 72 bytes max)
    - OWASP recommended
    - Won Password Hashing Competition

    Args:
        password: Mot de passe en clair

    Returns:
        Hash Argon2 du mot de passe
    """
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe correspond au hash.

    Supports both Argon2 (new) and bcrypt (legacy) for migration.

    Args:
        plain_password: Mot de passe en clair à vérifier
        hashed_password: Hash Argon2 ou bcrypt stocké en DB

    Returns:
        True si le mot de passe correspond, False sinon
    """
    # pwdlib automatically detects hash type (Argon2 or bcrypt for migration)
    return password_hash.verify(plain_password, hashed_password)
