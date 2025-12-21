"""
Authentication utilities for password hashing and verification
"""
import hashlib
import secrets


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with a salt

    Args:
        password: Plain text password

    Returns:
        Hashed password string with salt
    """
    # Generate a random salt
    salt = secrets.token_hex(16)

    # Hash password with salt
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()

    # Return salt:hash format
    return f"{salt}:{pwd_hash}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        password: Plain text password to verify
        hashed_password: Stored hash in format salt:hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        # Split salt and hash
        salt, pwd_hash = hashed_password.split(":")

        # Hash the provided password with the stored salt
        test_hash = hashlib.sha256((password + salt).encode()).hexdigest()

        # Compare hashes
        return test_hash == pwd_hash
    except Exception:
        return False
