import os
import hashlib
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="require",
        connect_timeout=10,
    )

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
            conn.close()