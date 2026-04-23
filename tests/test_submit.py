import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_connection, init_db, set_test_db
import tempfile
import os
from datetime import datetime


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
        VALUES ('quiz-submit', 'Quiz Submit', 'hash', ?)
    """, (datetime.now().isoformat(),))

    cursor.execute("""
        INSERT INTO questions (quiz_id, enunciado, opcoes, resposta_correta, explicacao)
        VALUES ('quiz-submit', 'P1?', '["A", "B", "C", "D"]', 0, 'Exp1')
    """)

    cursor.execute("""
        INSERT INTO questions (quiz_id, enunciado, opcoes, resposta_correta, explicacao)
        VALUES ('quiz-submit', 'P2?', '["A", "B", "C", "D"]', 1, 'Exp2')
    """)

    cursor.execute("""
        INSERT INTO questions (quiz_id, enunciado, opcoes, resposta_correta, explicacao)
        VALUES ('quiz-submit', 'P3?', '["A", "B", "C", "D"]', 2, 'Exp3')
    """)

    conn.commit()
    conn.close()

    return "quiz-submit"


@pytest.mark.asyncio
async def test_submit_all_correct(temp_db, db_with_quiz):
    """Deve retornar 100% acerto quando todas respostas corretas"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/quiz/{db_with_quiz}/submit", json={
            "respostas": {0: 0, 1: 1, 2: 2}
        })

    assert response.status_code == 200
    data = response.json()
    assert data["acertos"] == 3
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_submit_all_wrong(temp_db, db_with_quiz):
    """Deve retornar 0 acertos quando todas respostas erradas"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/quiz/{db_with_quiz}/submit", json={
            "respostas": {0: 3, 1: 3, 2: 3}
        })

    assert response.status_code == 200
    data = response.json()
    assert data["acertos"] == 0
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_submit_partial_correct(temp_db, db_with_quiz):
    """Deve calcular corretamente acertos parciais"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/quiz/{db_with_quiz}/submit", json={
            "respostas": {0: 0, 1: 0, 2: 0}
        })

    assert response.status_code == 200
    data = response.json()
    assert data["acertos"] == 1
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_submit_saves_result(temp_db, db_with_quiz):
    """Deve salvar resultado no banco de dados"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/quiz/{db_with_quiz}/submit", json={
            "respostas": {0: 0, 1: 1, 2: 2}
        })

    assert response.status_code == 200
    quiz_id = db_with_quiz

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM results WHERE quiz_id = ?", (quiz_id,))
    result = cursor.fetchone()
    conn.close()

    assert result is not None
    assert result["acertos"] == 3
    assert result["total"] == 3


@pytest.mark.asyncio
async def test_submit_returns_quiz_id(temp_db, db_with_quiz):
    """Deve retornar quiz_id na resposta"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/quiz/{db_with_quiz}/submit", json={
            "respostas": {0: 0, 1: 1, 2: 2}
        })

    assert response.status_code == 200
    data = response.json()
    assert "quiz_id" in data
    assert data["quiz_id"] == db_with_quiz


@pytest.mark.asyncio
async def test_submit_returns_timestamp(temp_db, db_with_quiz):
    """Deve retornar data de conclusão"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/quiz/{db_with_quiz}/submit", json={
            "respostas": {0: 0, 1: 1, 2: 2}
        })

    assert response.status_code == 200
    data = response.json()
    assert "completado_em" in data


@pytest.mark.asyncio
async def test_submit_quiz_not_found(temp_db):
    """Deve retornar 404 para quiz inexistente"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/quiz/nao-existe/submit", json={
            "respostas": {0: 0}
        })

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_with_partial_answers(temp_db, db_with_quiz):
    """Deve funcionar com respostas incompletas"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/quiz/{db_with_quiz}/submit", json={
            "respostas": {0: 0, 1: 1}
        })

    assert response.status_code == 200
    data = response.json()
    assert data["acertos"] == 2
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_submit_updates_existing_result(temp_db, db_with_quiz):
    """Deve atualizar resultado existente"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO results (quiz_id, acertos, total, completado_em)
        VALUES (?, 1, 3, ?)
    """, (db_with_quiz, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/quiz/{db_with_quiz}/submit", json={
            "respostas": {0: 0, 1: 1, 2: 2}
        })

    assert response.status_code == 200
    data = response.json()
    assert data["acertos"] == 3

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT acertos FROM results WHERE quiz_id = ?", (db_with_quiz,))
    results = cursor.fetchall()
    conn.close()
    assert len(results) == 1
    assert results[0]["acertos"] == 3