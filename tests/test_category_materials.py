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
def db_with_materials(temp_db):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO materials (hash, filename, content, category, criado_em)
        VALUES ('hash1', 'texto1.txt', 'Conteúdo do primeiro material', 'Português', ?)
    """, (datetime.now().isoformat(),))

    cursor.execute("""
        INSERT INTO materials (hash, filename, content, category, criado_em)
        VALUES ('hash2', 'texto2.pdf', 'Conteúdo do segundo material', 'Português', ?)
    """, (datetime.now().isoformat(),))

    cursor.execute("""
        INSERT INTO materials (hash, filename, content, category, criado_em)
        VALUES ('hash3', 'gramatica.pdf', 'Conteúdo de Português', 'Português', ?)
    """, (datetime.now().isoformat(),))

    cursor.execute("""
        INSERT INTO materials (hash, filename, content, category, criado_em)
        VALUES ('hash4', 'algebra.pdf', 'Conteúdo de Matemática', 'Matemática', ?)
    """, (datetime.now().isoformat(),))

    conn.commit()
    conn.close()

    return "Português"


@pytest.mark.asyncio
async def test_get_materials_by_category(temp_db, db_with_materials):
    """Deve retornar todos os materiais da categoria"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/categories/{db_with_materials}/materials")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_materials_returns_correct_fields(temp_db, db_with_materials):
    """Cada material deve ter campos corretos"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/categories/{db_with_materials}/materials")

    assert response.status_code == 200
    data = response.json()

    material = data[0]
    assert "hash" in material
    assert "filename" in material
    assert "content" in material
    assert "category" in material
    assert "criado_em" in material


@pytest.mark.asyncio
async def test_get_materials_only_returns_category_materials(temp_db, db_with_materials):
    """Deve retornar apenas materiais da categoria especificada"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/categories/{db_with_materials}/materials")

    assert response.status_code == 200
    data = response.json()

    for material in data:
        assert material["category"] == "Português"


@pytest.mark.asyncio
async def test_get_materials_empty_category(temp_db):
    """Deve retornar lista vazia para categoria sem materiais"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/categories/CategoriaVazia/materials")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_materials_content_not_truncated(temp_db, db_with_materials):
    """Deve retornar conteúdo completo (não truncado)"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/categories/{db_with_materials}/materials")

    assert response.status_code == 200
    data = response.json()

    for material in data:
        assert len(material["content"]) > 0


@pytest.mark.asyncio
async def test_get_materials_returns_hash(temp_db, db_with_materials):
    """Deve retornar hash do material"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/categories/{db_with_materials}/materials")

    assert response.status_code == 200
    data = response.json()

    for material in data:
        assert "hash" in material
        assert len(material["hash"]) > 0