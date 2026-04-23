import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_connection, init_db, set_test_db
import tempfile
import os
from datetime import datetime
import json


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    set_test_db(db_path)
    init_db()

    yield db_path

    set_test_db(None)
    os.unlink(db_path)


@pytest.fixture
def db_with_quiz(temp_db):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quizzes (id, titulo, material_hash, criado_em)
        VALUES ('quiz-123', 'Quiz Teste', 'hash123', ?)
    """, (datetime.now().isoformat(),))

    cursor.execute("""
        INSERT INTO questions (quiz_id, enunciado, opcoes, resposta_correta, explicacao)
        VALUES ('quiz-123', 'Qual é a capital?', '["SP", "RJ", "Brasília", "BH"]', 2, 'Brasília é a capital.')
    """)

    cursor.execute("""
        INSERT INTO questions (quiz_id, enunciado, opcoes, resposta_correta, explicacao)
        VALUES ('quiz-123', 'Maior oceano?', '["Atlântico", "Índico", "Pacífico", "Ártico"]', 2, 'Pacífico é o maior.')
    """)

    conn.commit()
    conn.close()

    return "quiz-123"


@pytest.mark.asyncio
async def test_get_quiz_by_id_success(temp_db, db_with_quiz):
    """Deve retornar quiz quando encontrado"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/quiz/{db_with_quiz}")

    assert response.status_code == 200
    data = response.json()
    assert data["quiz_id"] == "quiz-123"
    assert data["titulo"] == "Quiz Teste"


@pytest.mark.asyncio
async def test_get_quiz_returns_questions(temp_db, db_with_quiz):
    """Deve retornar perguntas do quiz"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/quiz/{db_with_quiz}")

    assert response.status_code == 200
    data = response.json()
    assert "perguntas" in data
    assert len(data["perguntas"]) == 2


@pytest.mark.asyncio
async def test_get_quiz_question_structure(temp_db, db_with_quiz):
    """Cada pergunta deve ter estrutura correta"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/quiz/{db_with_quiz}")

    assert response.status_code == 200
    data = response.json()

    pergunta = data["perguntas"][0]
    assert "enunciado" in pergunta
    assert "opcoes" in pergunta
    assert "resposta_correta" in pergunta
    assert "explicacao" in pergunta


@pytest.mark.asyncio
async def test_get_quiz_parses_opcoes_json(temp_db, db_with_quiz):
    """Deve converter opções de JSON para lista"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/quiz/{db_with_quiz}")

    assert response.status_code == 200
    data = response.json()

    primeira = data["perguntas"][0]
    assert isinstance(primeira["opcoes"], list)
    assert primeira["opcoes"] == ["SP", "RJ", "Brasília", "BH"]


@pytest.mark.asyncio
async def test_get_quiz_not_found(temp_db):
    """Deve retornar 404 quando quiz não existe"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/quiz/nao-existe")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_quiz_resposta_correta_index(temp_db, db_with_quiz):
    """Resposta correta deve ser índice válido"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/quiz/{db_with_quiz}")

    assert response.status_code == 200
    data = response.json()

    for pergunta in data["perguntas"]:
        assert pergunta["resposta_correta"] in [0, 1, 2, 3]


@pytest.mark.asyncio
async def test_get_quiz_with_results(temp_db):
    """Quiz com resultado deve retornar informações de resultado"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quizzes (id, titulo, material_hash, criado_em)
        VALUES ('quiz-resultado', 'Quiz com Resultado', 'hash', ?)
    """, (datetime.now().isoformat(),))

    cursor.execute("""
        INSERT INTO questions (quiz_id, enunciado, opcoes, resposta_correta, explicacao)
        VALUES ('quiz-resultado', 'P?', '["A", "B", "C", "D"]', 0, '')
    """)

    cursor.execute("""
        INSERT INTO results (quiz_id, acertos, total, completado_em)
        VALUES ('quiz-resultado', 8, 10, ?)
    """, (datetime.now().isoformat(),))

    conn.commit()
    conn.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/quiz/quiz-resultado")

    assert response.status_code == 200
    data = response.json()
    assert "resultado" in data or "resultado_id" in data