"""Сервисные операции для работы с пользователями."""
from collections.abc import Iterable
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from ..core.security import hash_password
from ..models import AccessToken, Role, User
from ..schemas import UserProfile

def get_user_by_email(db: Session, email: str) -> User | None:
    """Возвращает пользователя по адресу электронной почты или `None`."""
    return db.scalar(select(User).where(User.email == email))


def get_user(db: Session, user_id: int) -> User | None:
    """Находит пользователя по идентификатору без подгрузки зависимостей."""
    return db.get(User, user_id)


def get_user_with_roles(db: Session, user_id: int) -> User | None:
    """Загружает пользователя вместе с ролями и их разрешениями."""
    return db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user_id)
    )


def create_user(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    patronymic: str | None,
    email: str,
    password: str,
    roles: Sequence[Role] | None = None,
) -> User:
    """Создаёт нового пользователя, хеширует пароль и назначает роли."""
    user = User(
        first_name=first_name,
        last_name=last_name,
        patronymic=patronymic,
        email=email,
        password_hash=hash_password(password),
        is_active=True,
    )
    if roles:
        user.roles = list(roles)
    db.add(user)
    db.flush()
    return user


def list_users(db: Session) -> Iterable[User]:
    return db.scalars(select(User).options(selectinload(User.roles))).all()


def update_user(db: Session, user: User, data: dict[str, object]) -> User:
    """Применяет частичное обновление атрибутов пользователя."""
    if "first_name" in data:
        user.first_name = data["first_name"]
    if "last_name" in data:
        user.last_name = data["last_name"]
    if "patronymic" in data:
        user.patronymic = data["patronymic"]
    if "email" in data:
        user.email = data["email"]
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    db.flush()
    return user

def soft_delete_user(db: Session, user: User) -> None:
    """Деактивирует пользователя и отзывает все его токены."""
    user.is_active = False
    db.query(AccessToken).filter(AccessToken.user_id == user.id).update({"is_revoked": True})
    db.flush()


def serialize_user(user: User) -> UserProfile:
    """Преобразует ORM-модель пользователя в Pydantic-схему."""
    return UserProfile(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        patronymic=user.patronymic,
        email=user.email,
        is_active=user.is_active,
        roles=[role.name for role in user.roles],
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
