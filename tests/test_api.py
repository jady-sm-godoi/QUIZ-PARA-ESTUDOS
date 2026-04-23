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
async def test_generate_quiz_returns_quiz():
    """Deve retornar quiz ao gerar (com mock)"""
    from unittest.mock import patch, MagicMock

    mock_questions = {
        "questions": [
            {"enunciado": "P1?", "opcoes": ["A", "B", "C", "D"], "resposta_correta": 0, "explicacao": ""}
        ]
    }

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Test Quiz",
                "conteudo": "Sample content"
            })
            assert response.status_code == 200
            assert "quiz_id" in response.json()


@pytest.mark.asyncio
async def test_get_quiz_returns_404_for_nonexistent():
    """Deve retornar 404 para quiz inexistente"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/quiz/nao-existe")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_quiz_not_implemented():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/quiz/123/submit", json={
            "respostas": {0: 1, 1: 2}
        })
        assert response.status_code == 501


@pytest.mark.asyncio
async def test_categories_returns_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/categories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)