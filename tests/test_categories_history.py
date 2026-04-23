import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import get_connection, init_db, set_test_db
from datetime import datetime
import tempfile
import os


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    set_test_db(db_path)
    init_db()

    yield db_path

    set_test_db(None)
    os.unlink(db_path)


@pytest.mark.asyncio
async def test_get_categories_empty(temp_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


@pytest.mark.asyncio
async def test_get_history_empty(temp_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


@pytest.mark.asyncio
async def test_get_history_with_quizzes(temp_db):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO quizzes (id, titulo, material_hash, criado_em)
        VALUES ('test-001', 'Quiz de Teste', 'abc123', ?)
    """, (datetime.now().isoformat(),))

    cursor.execute("""
        INSERT INTO results (quiz_id, acertos, total, completado_em)
        VALUES ('test-001', 8, 10, ?)
    """, (datetime.now().isoformat(),))

    conn.commit()
    conn.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

        quiz = data[0]
        assert quiz["quiz_id"] == "test-001"
        assert quiz["titulo"] == "Quiz de Teste"
        assert "resultado_id" in quiz
        assert quiz["acertos"] == 8
        assert quiz["total"] == 10


@pytest.mark.asyncio
async def test_get_categories_with_materials(temp_db):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO materials (hash, filename, content, category, criado_em)
        VALUES ('hash1', 'arquivo1.txt', 'conteúdo', 'Português', ?)
    """, (datetime.now().isoformat(),))

    cursor.execute("""
        INSERT INTO materials (hash, filename, content, category, criado_em)
        VALUES ('hash2', 'arquivo2.txt', 'conteúdo', 'Português', ?)
    """, (datetime.now().isoformat(),))

    cursor.execute("""
        INSERT INTO materials (hash, filename, content, category, criado_em)
        VALUES ('hash3', 'arquivo3.txt', 'conteúdo', 'Matemática', ?)
    """, (datetime.now().isoformat(),))

    conn.commit()
    conn.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        categories_by_name = {c["name"]: c for c in data}
        assert categories_by_name["Português"]["material_count"] == 2
        assert categories_by_name["Matemática"]["material_count"] == 1