"""
Database layer — env-gated.

With DATABASE_URL set (Neon Postgres): full persistence.
Without it: db_enabled() is False and callers fall back to in-memory
behavior, so local dev works with zero setup.
"""
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

_engine = None
_SessionLocal: Optional[sessionmaker] = None


def db_enabled() -> bool:
    return bool(settings.DATABASE_URL)


def init_db():
    """Create engine + tables. Called once at startup."""
    global _engine, _SessionLocal
    if not db_enabled():
        return
    url = settings.DATABASE_URL
    # Neon gives postgres://; SQLAlchemy wants postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    _engine = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)
    from app.models.tables import Base
    Base.metadata.create_all(_engine)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)


@contextmanager
def db_session() -> Session:
    if _SessionLocal is None:
        raise RuntimeError("DB not initialized — check DATABASE_URL")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
