import hashlib
import sqlite3
from pathlib import Path

# SQLite é um banco de dados leve e simples, salvo em um único arquivo (quiz.db). Ele é fácil de usar e não requer configuração de servidor, perfeito para projetos pequenos e médios. O código abaixo define as funções para criar as tabelas necessárias e calcular o hash do conteúdo dos materiais.
DATABASE_PATH = Path(__file__).parent.parent / "quiz.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
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
