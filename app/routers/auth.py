"""Маршруты аутентификации: регистрация, вход и выход пользователей."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.security import create_access_token, verify_password
from ..dependencies import get_current_session, get_db
from ..models import AccessToken, User
from ..schemas import LoginRequest, TokenResponse, UserCreate, UserProfile
from ..services import create_user, get_role_by_name, get_user_by_email, serialize_user

router = APIRouter()


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    """Регистрирует нового пользователя и назначает ему базовую роль."""

    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    default_role = get_role_by_name(db, "basic_user")
    if default_role is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Default role missing.")

    user = create_user(
        db,
        first_name=payload.first_name,
        last_name=payload.last_name,
        patronymic=payload.patronymic,
        email=payload.email,
        password=payload.password,
        roles=[default_role],
    )
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Проверяет учётные данные и выдаёт краткоживущий JWT-токен."""

    user = get_user_by_email(db, payload.email)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    token_str, expires_at = create_access_token(subject=str(user.id), roles=[role.name for role in user.roles])
    token = AccessToken(token=token_str, user_id=user.id, expires_at=expires_at)
    db.add(token)
    db.commit()

    expires_in = max(0, int((expires_at - datetime.now(timezone.utc)).total_seconds()))
    return TokenResponse(access_token=token_str, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    session_data: tuple[User, AccessToken] = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    """Отзывает текущий токен пользователя и завершает его сессию."""

    _, token = session_data
    token_db = db.get(AccessToken, token.id)
    if token_db:
        token_db.is_revoked = True
        db.add(token_db)
    db.commit()
    return None