"""Настройка подключения к базе данных и фабрики сессий SQLAlchemy."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# SQLite для учебного проекта.
# Для PostgreSQL замените на:
# postgresql+psycopg://user:password@localhost:5432/cookbook
DATABASE_URL = "sqlite:///./cookbook.db"

engine = create_engine(
    DATABASE_URL,
    # Нужно только для SQLite, чтобы разрешить доступ из нескольких потоков.
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

def get_db() -> Iterator[Session]:
    """Предоставляет сессию SQLAlchemy для одного HTTP-запроса.

    Сессия гарантированно закрывается после завершения запроса.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()