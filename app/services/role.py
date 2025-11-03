"""Сервисные функции для работы с ролями."""
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from ..models import Permission, Role


def get_role_by_name(db: Session, role_name: str) -> Role | None:
    """Возвращает роль по её уникальному имени."""
    return (
        db.execute(select(Role).where(Role.name == role_name)).unique().scalar_one_or_none()
    )


def get_roles_by_ids(db: Session, role_ids: Sequence[int]) -> list[Role]:
    """Возвращает роли, соответствующие указанным идентификаторам."""
    result = db.execute(select(Role).where(Role.id.in_(role_ids)))
    return list(result.unique().scalars().all())


def list_roles(db: Session) -> list[Role]:
    """Возвращает список ролей с загруженными разрешениями."""
    result = db.execute(select(Role).options(selectinload(Role.permissions)))
    return list(result.unique().scalars().all())


def create_role(
    db: Session,
    *,
    name: str,
    description: str | None,
    permissions: Sequence[Permission],
) -> Role:
    """Создаёт роль и привязывает к ней заданные разрешения."""
    role = Role(name=name, description=description)
    role.permissions = list(permissions)
    db.add(role)
    db.flush()
    return role


def update_role(
    db: Session,
    role: Role,
    name: str | None = None,
    description: str | None = None,
    permissions: Sequence[Permission] | None = None,
) -> Role:
    """Обновляет параметры роли и при необходимости её разрешения."""
    if name is not None:
        role.name = name
    if description is not None:
        role.description = description
    if permissions is not None:
        role.permissions = list(permissions)
    db.flush()
    return role


def delete_role(db: Session, role: Role) -> None:
    """Удаляет роль из базы данных."""
    db.delete(role)
    db.flush()