import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.fernet import Fernet

from app.config import settings

_fernet = Fernet(settings.encryption_key.encode())


def encrypt_password(raw: str) -> str:
    return _fernet.encrypt(raw.encode()).decode()


def decrypt_password(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()


def generate_magic_link_token() -> tuple[str, str, datetime]:
    """Returns (raw_token, token_hash, expires_at). Only the hash is persisted."""
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.magic_link_ttl_minutes)
    return raw, token_hash, expires_at


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def create_session_jwt(user_id: uuid.UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=settings.session_ttl_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_session_jwt(token: str) -> uuid.UUID | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
