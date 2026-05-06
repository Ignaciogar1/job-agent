# db.py — toda la lógica de persistencia

import sqlite3
from datetime import datetime
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # acceso por nombre de columna
    return conn


def init_db():
    """Crea las tablas si no existen. Seguro llamarlo siempre al arrancar."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,  -- hash de url+titulo
                title       TEXT NOT NULL,
                company     TEXT,
                location    TEXT,
                source      TEXT,
                url         TEXT,
                description TEXT,
                score       REAL,             -- similitud con perfil (se rellena en fase 2)
                notified    INTEGER DEFAULT 0, -- 0/1
                fecha_vista TEXT NOT NULL
            )
        """)
        conn.commit()


def job_exists(job_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return row is not None


def insert_job(job: dict):
    """Inserta una oferta. Si ya existe, no hace nada (INSERT OR IGNORE)."""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO jobs
                (id, title, company, location, source, url, description, score, notified, fecha_vista)
            VALUES
                (:id, :title, :company, :location, :source, :url, :description, :score, :notified, :fecha_vista)
        """, job)
        conn.commit()


def get_unnotified_above_threshold(threshold: float) -> list:
    """Devuelve ofertas con score >= threshold que aún no se han notificado."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM jobs
            WHERE score >= ? AND notified = 0
            ORDER BY score DESC
        """, (threshold,)).fetchall()
        return [dict(row) for row in rows]


def mark_as_notified(job_id: str):
    with get_connection() as conn:
        conn.execute("UPDATE jobs SET notified = 1 WHERE id = ?", (job_id,))
        conn.commit()


def update_score(job_id: str, score: float):
    with get_connection() as conn:
        conn.execute("UPDATE jobs SET score = ? WHERE id = ?", (score, job_id))
        conn.commit()


def get_jobs_without_score() -> list:
    """Ofertas nuevas que aún no tienen score calculado."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM jobs WHERE score IS NULL
        """).fetchall()
        return [dict(row) for row in rows]


def stats() -> dict:
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        notified = conn.execute("SELECT COUNT(*) FROM jobs WHERE notified = 1").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM jobs WHERE score IS NULL").fetchone()[0]
        return {"total": total, "notified": notified, "pending_score": pending}
