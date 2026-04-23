import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from app.main import app
from app.database import get_connection, set_test_db, init_db
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


class TestFrontendAPIIntegration:

    @pytest.mark.asyncio
    async def test_generate_and_get_quiz_flow(self, temp_db):
        """Testa fluxo completo: gerar quiz e buscar"""
        mock_questions = {
            "questions": [
                {
                    "enunciado": "P1?",
                    "opcoes": ["A", "B", "C", "D"],
                    "resposta_correta": 0,
                    "explicacao": "E1"
                }
            ]
        }

        with patch('app.agents.QuizAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.generate.return_value = mock_questions
            mock_agent_class.return_value = mock_agent

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                gen_response = await client.post("/api/generate", json={
                    "titulo": "Teste Frontend",
                    "conteudo": "Conteúdo para testar"
                })

                assert gen_response.status_code == 200
                quiz_id = gen_response.json()["quiz_id"]

                get_response = await client.get(f"/api/quiz/{quiz_id}")
                assert get_response.status_code == 200
                assert len(get_response.json()["perguntas"]) == 1

    @pytest.mark.asyncio
    async def test_generate_submit_flow(self, temp_db):
        """Testa fluxo: gerar quiz, responder e ver resultado"""
        mock_questions = {
            "questions": [
                {
                    "enunciado": "P1?",
                    "opcoes": ["A", "B", "C", "D"],
                    "resposta_correta": 0,
                    "explicacao": "E1"
                }
            ]
        }

        with patch('app.agents.QuizAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.generate.return_value = mock_questions
            mock_agent_class.return_value = mock_agent

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                gen_response = await client.post("/api/generate", json={
                    "titulo": "Teste Submit",
                    "conteudo": "Conteúdo"
                })

                quiz_id = gen_response.json()["quiz_id"]

                submit_response = await client.post(f"/api/quiz/{quiz_id}/submit", json={
                    "respostas": {"0": 0}
                })

                assert submit_response.status_code == 200
                assert submit_response.json()["acertos"] == 1
                assert submit_response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_categories_flow(self, temp_db):
        """Testa fluxo: criar material, ver categoria"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO materials (hash, filename, content, category, criado_em)
            VALUES ('hash-cat-test', 'test.txt', 'Conteúdo teste', 'Teste Frontend', ?)
        """, (datetime.now().isoformat(),))

        conn.commit()
        conn.close()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/categories")
            assert response.status_code == 200

            category_exists = any(
                c["name"] == "Teste Frontend" for c in response.json()
            )
            assert category_exists

    @pytest.mark.asyncio
    async def test_history_with_results(self, temp_db):
        """Testa que histórico inclui resultados"""
        mock_questions = {
            "questions": [
                {
                    "enunciado": "P1?",
                    "opcoes": ["A", "B", "C", "D"],
                    "resposta_correta": 0,
                    "explicacao": "E1"
                }
            ]
        }

        with patch('app.agents.QuizAgent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.generate.return_value = mock_questions
            mock_agent_class.return_value = mock_agent

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                gen_response = await client.post("/api/generate", json={
                    "titulo": "Quiz com Resultado",
                    "conteudo": "Conteúdo"
                })

                quiz_id = gen_response.json()["quiz_id"]

                await client.post(f"/api/quiz/{quiz_id}/submit", json={
                    "respostas": {"0": 0}
                })

                history_response = await client.get("/api/history")
                assert history_response.status_code == 200

                history = history_response.json()
                quiz_in_history = next(
                    (q for q in history if q["quiz_id"] == quiz_id),
                    None
                )
                assert quiz_in_history is not None
                assert quiz_in_history["acertos"] == 1