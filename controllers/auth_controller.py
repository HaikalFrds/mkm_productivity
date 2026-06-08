"""Auth controller — login & password hashing."""
import hashlib
import logging

from database.session import get_session
from models.user import User


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_login(nik: str, password: str) -> dict | None:
    """
    Verifikasi login. Return dict user jika berhasil, None jika gagal.
    Raise ConnectionError jika tidak bisa koneksi ke DB.
    """
    try:
        with get_session() as session:
            user = (
                session.query(User)
                .filter(User.nik == nik, User.password_hash == hash_password(password))
                .first()
            )
            if user:
                return user.to_dict()
            return None
    except Exception as e:
        logging.error(f"verify_login error: {e}")
        raise ConnectionError(f"Tidak dapat terhubung ke database: {e}") from e
