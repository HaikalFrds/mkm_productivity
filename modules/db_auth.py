import os
import hashlib
import threading
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool as pg_pool
from dotenv import load_dotenv

load_dotenv()

_pool = None
_pool_lock = threading.Lock()


def _get_pool() -> pg_pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pg_pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=5,
                    host=os.getenv("DB_HOST"),
                    port=int(os.getenv("DB_PORT", 5432)),
                    dbname=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    sslmode="require",
                    connect_timeout=10,
                )
    return _pool


def get_connection():
    return _get_pool().getconn()


def release_connection(conn):
    try:
        _get_pool().putconn(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


@contextmanager
def db_cursor(commit: bool = False):
    """Context manager: otomatis handle get/release connection dan cursor."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield conn, cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            cur.close()
        except Exception:
            pass
        release_connection(conn)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_login(nik: str, password: str) -> dict | None:
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """SELECT id, name, nik, role
               FROM "user"
               WHERE nik = %s AND password_hash = %s
               LIMIT 1""",
            (nik, hash_password(password)),
        )
        row = cur.fetchone()
        cur.close()
        if row:
            return {"id": row[0], "name": row[1], "nik": row[2], "role": row[3]}
        return None
    except psycopg2.OperationalError as e:
        raise ConnectionError(f"Tidak dapat terhubung ke database: {e}") from e
    finally:
        if conn:
            release_connection(conn)
