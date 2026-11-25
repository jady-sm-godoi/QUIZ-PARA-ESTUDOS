import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from app.main import app
from app.database import get_connection, init_db, set_test_db
from app.prompts import DEFAULT_PROMPT
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


@pytest.mark.asyncio
async def test_generate_quiz_uses_selected_prompt(temp_db):
    """O prompt escolhido deve ser repassado ao QuizAgent."""
    mock_questions = {"questions": []}

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Teste Prompt",
                "conteudo": "Conteúdo",
                "prompt_name": DEFAULT_PROMPT
            })

        assert response.status_code == 200
        mock_agent_class.assert_called_once_with(prompt_name=DEFAULT_PROMPT)


@pytest.mark.asyncio
async def test_generate_quiz_rejects_invalid_prompt(temp_db):
    """Prompt inexistente deve retornar 400 sem chamar o agente."""
    with patch('app.agents.QuizAgent') as mock_agent_class:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Teste Prompt Inválido",
                "conteudo": "Conteúdo",
                "prompt_name": "nao_existe"
            })

        assert response.status_code == 400
        assert "nao_existe" in response.json()["detail"]
        mock_agent_class.assert_not_called()


@pytest.mark.asyncio
async def test_generate_file_uses_selected_prompt(temp_db):
    """A rota de arquivo deve repassar o prompt escolhido."""
    mock_questions = {"questions": []}

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/generate/file",
                files={"file": ("material.txt", b"Conteudo do material", "text/plain")},
                data={
                    "titulo": "Teste Arquivo",
                    "num_perguntas": "1",
                    "prompt_name": DEFAULT_PROMPT
                }
            )

        assert response.status_code == 200
        mock_agent_class.assert_called_once_with(prompt_name=DEFAULT_PROMPT)


@pytest.mark.asyncio
async def test_generate_large_content_returns_parts(temp_db):
    """Conteúdo acima de 60k deve retornar as partes sem chamar a IA."""
    content = "A" * 70000

    with patch('app.agents.QuizAgent') as mock_agent_class:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Material Grande",
                "conteudo": content,
                "num_perguntas": 10
            })

        assert response.status_code == 200
        data = response.json()
        assert data["total_parts"] == 2
        assert len(data["parts"]) == 2
        assert all(part["needs_split"] is True for part in data["parts"])
        assert data["parts"][0]["part_index"] == 0
        assert data["parts"][1]["char_count"] == 20000
        mock_agent_class.assert_not_called()


@pytest.mark.asyncio
async def test_generate_large_content_with_part_index(temp_db):
    """part_index deve gerar o quiz apenas da parte escolhida."""
    content = "A" * 70000
    mock_questions = {"questions": []}

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/generate", json={
                "titulo": "Material Grande - Parte 2",
                "conteudo": content,
                "num_perguntas": 1,
                "part_index": 1
            })

        assert response.status_code == 200
        sent_content = mock_agent.generate.call_args[0][0]
        assert sent_content == "A" * 20000


@pytest.mark.asyncio
async def test_generate_large_file_returns_parts(temp_db):
    """Arquivo grande deve retornar as partes sem chamar a IA."""
    content = b"A" * 70000

    with patch('app.agents.QuizAgent') as mock_agent_class:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/generate/file",
                files={"file": ("grande.txt", content, "text/plain")},
                data={"titulo": "Arquivo Grande", "num_perguntas": "10"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total_parts"] == 2
        assert all(part["needs_split"] is True for part in data["parts"])
        mock_agent_class.assert_not_called()


@pytest.mark.asyncio
async def test_generate_large_file_with_part_index(temp_db):
    """part_index na rota de arquivo deve gerar o quiz da parte escolhida."""
    content = b"A" * 70000
    mock_questions = {"questions": []}

    with patch('app.agents.QuizAgent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.generate.return_value = mock_questions
        mock_agent_class.return_value = mock_agent

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/generate/file",
                files={"file": ("grande.txt", content, "text/plain")},
                data={
                    "titulo": "Arquivo Grande - Parte 2",
                    "num_perguntas": "1",
                    "part_index": "1"
                }
            )

        assert response.status_code == 200
        sent_content = mock_agent.generate.call_args[0][0]
        assert sent_content == "A" * 20000


@pytest.mark.asyncio
async def test_generate_part_index_out_of_range(temp_db):
    """part_index inválido deve retornar 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/generate", json={
            "titulo": "Parte Inválida",
            "conteudo": "A" * 70000,
            "num_perguntas": 1,
            "part_index": 5
        })

    assert response.status_code == 400


def test_normalize_option_comments():
    """Os comentários devem sempre ter o mesmo tamanho das opções."""
    from app.routes import normalize_option_comments

    assert normalize_option_comments(["a", "b"], 4) == ["a", "b", "", ""]
    assert normalize_option_comments({"A": "a", "C": "c"}, 3) == ["a", "", "c"]
    assert normalize_option_comments(None, 2) == ["", ""]
    assert normalize_option_comments(["a", "b", "c"], 2) == ["a", "b"]


@pytest.mark.asyncio
async def test_generate_saves_and_returns_option_comments(temp_db):
    """Os comentários por alternativa devem ser salvos e devolvidos pela API."""
    comments = ["A errada", "B correta", "C errada", "D errada", "E errada"]
    mock_questions = {
        "questions": [
            {
                "enunciado": "P?",
                "opcoes": ["A", "B", "C", "D", "E"],
                "resposta_correta": 1,
                "explicacao": "Resumo",
                "comentarios_opcoes": comments
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
                "titulo": "Teste Comentários",
                "conteudo": "Conteúdo"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["perguntas"][0]["comentarios_opcoes"] == comments

            get_response = await client.get(f"/api/quiz/{data['quiz_id']}")
            assert get_response.status_code == 200
            assert get_response.json()["perguntas"][0]["comentarios_opcoes"] == comments