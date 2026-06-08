"""
DDL migrations — tabel opsional dan kolom tambahan.
Dipanggil sekali saat startup via initialize_tables().
"""
import logging
from sqlalchemy import text
from database.session import engine


def initialize_tables() -> None:
    """Pastikan semua tabel & kolom opsional sudah ada di database."""
    ddl_statements = [
        # shop_model
        """
        CREATE TABLE IF NOT EXISTS shop_model (
            id           SERIAL PRIMARY KEY,
            section_id   INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE,
            model_name   VARCHAR(100) NOT NULL,
            working_hour FLOAT DEFAULT 0,
            UNIQUE(section_id, model_name)
        )
        """,
        # kolom tambahan shop_model
        "ALTER TABLE shop_model ADD COLUMN IF NOT EXISTS working_hour FLOAT DEFAULT 0",
        "ALTER TABLE shop_model ADD COLUMN IF NOT EXISTS cycle_time   FLOAT DEFAULT 0",
        # work_center
        """
        CREATE TABLE IF NOT EXISTS work_center (
            id         SERIAL PRIMARY KEY,
            section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE,
            name       VARCHAR(100) NOT NULL,
            UNIQUE(section_id, name)
        )
        """,
        # kolom tambahan shift
        "ALTER TABLE shift ADD COLUMN IF NOT EXISTS preparation_min FLOAT DEFAULT 15",
        "ALTER TABLE shift ADD COLUMN IF NOT EXISTS other_min       FLOAT DEFAULT 10",
        # op_number per shop
        """
        CREATE TABLE IF NOT EXISTS op_number (
            id         SERIAL PRIMARY KEY,
            section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE,
            op_no      VARCHAR(100) NOT NULL,
            UNIQUE(section_id, op_no)
        )
        """,
    ]

    with engine.begin() as conn:
        for stmt in ddl_statements:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                logging.warning(f"DDL skipped (mungkin sudah ada): {e}")
