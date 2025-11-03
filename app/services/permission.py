"""Сервисные функции для работы с разрешениями."""
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Permission

def get_permissions_by_codes(db: Session, codes: Sequence[str]) -> list[Permission]:
    """Возвращает разрешения, соответствующие указанным кодам."""
    return list(db.scalars(select(Permission).where(Permission.code.in_(codes))).all())


def list_permissions(db: Session) -> list[Permission]:
    """Возвращает список всех разрешений системы."""
    return list(db.scalars(select(Permission)).all())
