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


@pytest.mark.asyncio
async def test_upload_txt_file(temp_db):
    """Deve fazer upload de arquivo TXT"""
    content = b"Content of the material in TXT format"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("material.txt", content, "text/plain")},
            data={"category": "Portugues"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "material.txt"
    assert data["category"] == "Portugues"
    assert data["hash"] is not None


@pytest.mark.asyncio
async def test_upload_pdf_file(temp_db):
    """Deve fazer upload de arquivo PDF"""
    content = b"PDF Content here"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("apostila.pdf", content, "application/pdf")},
            data={"category": "Matematica"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "apostila.pdf"


@pytest.mark.asyncio
async def test_upload_saves_to_database(temp_db):
    """Deve salvar material no banco de dados"""
    content = b"Material for testing"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("teste.txt", content, "text/plain")},
            data={"category": "Historia"}
        )

    assert response.status_code == 200
    material_hash = response.json()["hash"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM materials WHERE hash = ?", (material_hash,))
    material = cursor.fetchone()
    conn.close()

    assert material is not None
    assert material["content"] == "Material for testing"
    assert material["category"] == "Historia"


@pytest.mark.asyncio
async def test_upload_without_category(temp_db):
    """Deve permitir upload sem categoria"""
    content = b"Material without category"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("sem_categoria.txt", content, "text/plain")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["category"] is None


@pytest.mark.asyncio
async def test_upload_generates_hash(temp_db):
    """Deve gerar hash unico para o conteudo"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response1 = await client.post(
            "/api/upload",
            files={"file": ("a.txt", b"Unique content", "text/plain")},
            data={"category": "Cat1"}
        )
        response2 = await client.post(
            "/api/upload",
            files={"file": ("b.txt", b"Different content", "text/plain")},
            data={"category": "Cat2"}
        )

    hash1 = response1.json()["hash"]
    hash2 = response2.json()["hash"]

    assert hash1 != hash2
    assert len(hash1) > 0


@pytest.mark.asyncio
async def test_upload_same_content_same_hash(temp_db):
    """Conteudo igual deve gerar hash igual"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response1 = await client.post(
            "/api/upload",
            files={"file": ("a.txt", b"Same content", "text/plain")},
            data={"category": "Cat1"}
        )
        response2 = await client.post(
            "/api/upload",
            files={"file": ("b.txt", b"Same content", "text/plain")},
            data={"category": "Cat2"}
        )

    hash1 = response1.json()["hash"]
    hash2 = response2.json()["hash"]

    assert hash1 == hash2


@pytest.mark.asyncio
async def test_upload_returns_filename(temp_db):
    """Deve retornar o nome do arquivo"""
    content = b"Content here"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("meu_arquivo.pdf", content, "application/pdf")},
            data={"category": "Teste"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "meu_arquivo.pdf"


@pytest.mark.asyncio
async def test_upload_creates_new_material(temp_db):
    """Deve criar novo material no banco"""
    content = b"New material content"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("novo.txt", content, "text/plain")},
            data={"category": "Portugues"}
        )

    assert response.status_code == 200
    new_hash = response.json()["hash"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM materials WHERE hash = ?", (new_hash,))
    count = cursor.fetchone()["count"]
    conn.close()

    assert count == 1


@pytest.mark.asyncio
async def test_upload_empty_file(temp_db):
    """Deve lidar com arquivo vazio"""
    content = b""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("vazio.txt", content, "text/plain")},
            data={"category": "Teste"}
        )

    assert response.status_code == 200