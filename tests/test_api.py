import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


@pytest.mark.asyncio
async def test_generate_quiz_not_implemented():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/generate", json={
            "titulo": "Test Quiz",
            "conteudo": "Sample content"
        })
        assert response.status_code == 501


@pytest.mark.asyncio
async def test_get_quiz_not_implemented():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/quiz/123")
        assert response.status_code == 501


@pytest.mark.asyncio
async def test_submit_quiz_not_implemented():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/quiz/123/submit", json={
            "respostas": {0: 1, 1: 2}
        })
        assert response.status_code == 501


@pytest.mark.asyncio
async def test_categories_not_implemented():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/categories")
        assert response.status_code == 501