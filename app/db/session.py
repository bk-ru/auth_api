"""Инструменты подключения к базе данных и управления сессиями SQLAlchemy."""
from contextlib import contextmanager
from typing import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from ..core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, echo=settings.debug, future=True)

class Base(DeclarativeBase):
    pass
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

@contextmanager
def session_scope() -> Iterator[Session]:
    """Предоставляет сессию БД с автоматическим коммитом или откатом."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
