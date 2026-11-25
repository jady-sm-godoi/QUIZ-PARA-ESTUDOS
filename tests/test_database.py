import pytest
import sqlite3
from pathlib import Path
import tempfile
import os


class TestDatabase:

    @pytest.fixture
    def temp_db(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        original_path = Path(__file__).parent.parent / "backend" / "app" / "database.py"
        with open(original_path, "r") as f:
            content = f.read()

        with open(original_path, "w") as f:
            f.write(content.replace(
                'DATABASE_PATH = Path(__file__).parent.parent / "quiz.db"',
                f'DATABASE_PATH = Path("{db_path}")'
            ))

        yield db_path

        with open(original_path, "w") as f:
            f.write(content)

        os.unlink(db_path)

    def test_database_tables_exist(self, temp_db):
        from app.database import get_connection, init_db

        init_db()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "quizzes" in tables
        assert "questions" in tables
        assert "results" in tables
        assert "materials" in tables

    def test_compute_hash(self):
        from app.database import compute_hash

        hash1 = compute_hash("conteúdo de teste")
        hash2 = compute_hash("conteúdo de teste")
        hash3 = compute_hash("outro conteúdo")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 32

    def test_init_db_migrates_option_comments_column(self):
        from app.database import set_test_db, init_db, get_connection

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quiz_id TEXT NOT NULL,
                    enunciado TEXT NOT NULL,
                    opcoes TEXT NOT NULL,
                    resposta_correta INTEGER NOT NULL,
                    explicacao TEXT DEFAULT ''
                )
            """)
            conn.commit()
            conn.close()

            set_test_db(db_path)
            init_db()

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(questions)")
            columns = {row["name"] for row in cursor.fetchall()}
            conn.close()

            assert "comentarios_opcoes" in columns
        finally:
            set_test_db(None)
            os.unlink(db_path)