import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
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
async def test_generate_quiz_success(temp_db):
    """Deve gerar quiz com sucesso e salvar no banco"""
    mock_questions = {
        "questions": [
            {
                "enunciado": "Qual é a capital do Brasil?",
                "opcoes": ["São Paulo", "Rio de Janeiro", "Brasília", "Belo Horizonte"],
                "resposta_correta": 2,
                "explicacao": "Brasília é a capital desde 1960."
            }
        ]
    }

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Quiz de Geografia",
                "conteudo": "A capital do Brasil é Brasília desde 1960.",
                "num_perguntas": 1
            })

        assert response.status_code == 200
        data = response.json()
        assert "quiz_id" in data
        assert data["titulo"] == "Quiz de Geografia"
        assert len(data["perguntas"]) == 1
        assert data["perguntas"][0]["enunciado"] == "Qual é a capital do Brasil?"


@pytest.mark.asyncio
async def test_generate_quiz_saves_to_database(temp_db):
    """Deve salvar quiz e perguntas no banco de dados"""
    mock_questions = {
        "questions": [
            {
                "enunciado": "P1",
                "opcoes": ["A", "B", "C", "D"],
                "resposta_correta": 1,
                "explicacao": "Explicação"
            }
        ]
    }

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Teste DB",
                "conteudo": "Conteúdo de teste"
            })

        assert response.status_code == 200
        quiz_id = response.json()["quiz_id"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quizzes WHERE id = ?", (quiz_id,))
        quiz = cursor.fetchone()
        conn.close()

        assert quiz is not None
        assert quiz["titulo"] == "Teste DB"


@pytest.mark.asyncio
async def test_generate_quiz_saves_questions(temp_db):
    """Deve salvar perguntas do quiz no banco"""
    mock_questions = {
        "questions": [
            {"enunciado": "P1", "opcoes": ["A", "B", "C", "D"], "resposta_correta": 0, "explicacao": "E1"},
            {"enunciado": "P2", "opcoes": ["A", "B", "C", "D"], "resposta_correta": 1, "explicacao": "E2"},
        ]
    }

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Teste Perguntas",
                "conteudo": "Conteúdo"
            })

        quiz_id = response.json()["quiz_id"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM questions WHERE quiz_id = ?", (quiz_id,))
        count = cursor.fetchone()["count"]
        conn.close()

        assert count == 2


@pytest.mark.asyncio
async def test_generate_quiz_with_category(temp_db):
    """Deve gerar quiz com categoria"""
    mock_questions = {"questions": []}

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Quiz com Categoria",
                "conteudo": "Conteúdo",
                "categoria": "Português"
            })

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_generate_quiz_default_num_questions(temp_db):
    """Deve usar 10 perguntas por padrão"""
    mock_questions = {"questions": [{"enunciado": "P", "opcoes": ["A", "B", "C", "D"], "resposta_correta": 0, "explicacao": ""}]}

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Teste",
                "conteudo": "Conteúdo"
            })

        assert response.status_code == 200
        mock_agent.generate.assert_called_once()
        call_args = mock_agent.generate.call_args
        assert call_args[1]["num_questions"] == 10


@pytest.mark.asyncio
async def test_generate_quiz_response_structure(temp_db):
    """Resposta deve ter estrutura correta"""
    mock_questions = {
        "questions": [
            {
                "enunciado": "Teste?",
                "opcoes": ["A", "B", "C", "D"],
                "resposta_correta": 2,
                "explicacao": "Explicação"
            }
        ]
    }

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Teste",
                "conteudo": "Conteúdo"
            })

        data = response.json()
        assert "quiz_id" in data
        assert "titulo" in data
        assert "perguntas" in data
        assert isinstance(data["perguntas"], list)

        pergunta = data["perguntas"][0]
        assert "enunciado" in pergunta
        assert "opcoes" in pergunta
        assert "resposta_correta" in pergunta
        assert "explicacao" in pergunta