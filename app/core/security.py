"""Функции безопасности: хеширование паролей и работа с JWT."""
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from passlib.context import CryptContext
from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

def hash_password(password: str) -> str:
    """Возвращает bcrypt-хеш для переданного пароля."""
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля ранее сохранённому хешу."""
    return pwd_context.verify(password, hashed_password)

def create_access_token(
    subject: str,
    expires_minutes: int | None = None,
    **claims: Any,
) -> tuple[str, datetime]:
    """Создаёт JWT-токен с заданным сроком жизни и дополнительными claim'ами."""
    expire_minutes = expires_minutes or settings.access_token_expire_minutes
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire_at,
        "iat": datetime.now(timezone.utc),
    }
    payload.update(claims)
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expire_at

def decode_token(token: str) -> dict[str, Any]:
    """Декодирует и валидирует JWT, возвращая исходные claim'ы."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "sub"]},
    )