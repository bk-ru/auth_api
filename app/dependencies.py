"""Зависимости FastAPI для работы с БД и проверки прав доступа."""
from collections.abc import Callable, Generator
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from . import models
from .core.security import decode_token
from .db.session import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """Открывает сессию SQLAlchemy и отдаёт её обработчику FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))],
    db: Annotated[Session, Depends(get_db)],
) -> models.AccessToken:
    """Проверяет токен из заголовка Authorization и возвращает активную запись."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    token_str = credentials.credentials
    try:
        decode_token(token_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from None

    token = (
        db.query(models.AccessToken)
        .filter(models.AccessToken.token == token_str, models.AccessToken.is_revoked.is_(False))
        .one_or_none()
    )
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked or unknown.")

    user = db.query(models.User).filter(models.User.id == token.user_id).one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found.")

    return token


def get_current_user(
    token: Annotated[models.AccessToken, Depends(get_current_token)],
    db: Annotated[Session, Depends(get_db)],
) -> models.User:
    """Возвращает активного пользователя, связанного с проверенным токеном."""
    user = db.get(models.User, token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found.")
    return user


def get_current_session(
    token: Annotated[models.AccessToken, Depends(get_current_token)],
    user: Annotated[models.User, Depends(get_current_user)],
) -> tuple[models.User, models.AccessToken]:
    """Возвращает кортеж из пользователя и токена."""
    return user, token


def require_permissions(*required_codes: str) -> Callable[[models.User], models.User]:
    """Создаёт зависимость, проверяющую наличие у пользователя нужных прав."""
    def dependency(user: Annotated[models.User, Depends(get_current_user)]) -> models.User:
        user_permissions = {perm.code for role in user.roles for perm in role.permissions}
        if not set(required_codes).issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: insufficient permissions.",
            )
        return user
    return dependency