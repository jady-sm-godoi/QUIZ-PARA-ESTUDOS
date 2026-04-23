import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

DATABASE_PATH = Path(__file__).parent.parent / "quiz.db"
_test_db_path: Optional[Path] = None


def set_test_db(path: Optional[str]):
    global _test_db_path
    _test_db_path = Path(path) if path else None


def is_test_mode() -> bool:
    return _test_db_path is not None


def get_connection() -> sqlite3.Connection:
    path = _test_db_path if _test_db_path else DATABASE_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id TEXT PRIMARY KEY,
            titulo TEXT NOT NULL,
            material_hash TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id TEXT NOT NULL,
            enunciado TEXT NOT NULL,
            opcoes TEXT NOT NULL,
            resposta_correta INTEGER NOT NULL,
            explicacao TEXT DEFAULT '',
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id TEXT NOT NULL,
            acertos INTEGER NOT NULL,
            total INTEGER NOT NULL,
            completado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            hash TEXT PRIMARY KEY,
            filename TEXT,
            content TEXT,
            category TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def compute_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()