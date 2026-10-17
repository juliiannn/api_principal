from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError

from app.config.settings import settings


class JwtService:
    """Genera y valida los tokens JWT."""

    @property
    def expiration_minutes(self) -> int:
        return settings.JWT_EXPIRATION_MINUTES

    def create_access_token(self, email: str, role: str) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
        payload = {"sub": email, "role": role, "exp": expire, "iat": now}
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except JWTError:
            return None
