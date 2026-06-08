"""
SQLAlchemy engine + session factory.
Semua layer (models, controllers) import dari sini.
"""
import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()


class Base(DeclarativeBase):
    pass


def _build_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME"),
        query={"sslmode": "require"},
    )


engine = create_engine(
    _build_url(),
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_pre_ping=True,          # cek koneksi sebelum pakai (auto-reconnect)
    connect_args={"connect_timeout": 10},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_session():
    """
    Context manager: buat session, auto-commit on success, rollback on error.

    Usage:
        with get_session() as session:
            obj = session.get(Model, id)
            session.add(new_obj)
        # commit otomatis di sini
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
