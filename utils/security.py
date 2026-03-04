import hashlib


def hash_pw(password: str) -> str:
    """Return SHA-256 hex digest of the given plaintext password."""
    return hashlib.sha256(password.encode()).hexdigest()


def is_admin(user: dict) -> bool:
    """Return True if the user dict has the admin role."""
    return (user or {}).get("role", "") == "admin"
