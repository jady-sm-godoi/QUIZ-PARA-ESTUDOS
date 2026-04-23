import pytest
from pydantic import ValidationError
from app.models import (
    QuizGenerateRequest,
    QuestionModel,
    QuizResponse,
    QuizResult,
    QuizResultRequest,
)


class TestQuizModels:

    def test_quiz_generate_request_valid(self):
        request = QuizGenerateRequest(
            titulo="Quiz de Português",
            conteudo="O texto fala sobre gramática.",
            num_perguntas=5,
            categoria="Português"
        )
        assert request.titulo == "Quiz de Português"
        assert request.num_perguntas == 5

    def test_quiz_generate_request_without_conteudo(self):
        request = QuizGenerateRequest(titulo="Quiz sem conteúdo")
        assert request.conteudo is None
        assert request.num_perguntas == 10

    def test_quiz_generate_request_invalid_num_perguntas(self):
        with pytest.raises(ValidationError):
            QuizGenerateRequest(titulo="Teste", num_perguntas=0)

        with pytest.raises(ValidationError):
            QuizGenerateRequest(titulo="Teste", num_perguntas=100)

    def test_question_model_valid(self):
        question = QuestionModel(
            enunciado="Qual é a capital do Brasil?",
            opcoes=["São Paulo", "Rio de Janeiro", "Brasília", "Belo Horizonte"],
            resposta_correta=2,
            explicacao="Brasília é a capital do Brasil desde 1960."
        )
        assert question.resposta_correta == 2
        assert len(question.opcoes) == 4

    def test_question_model_invalid_resposta_correta(self):
        with pytest.raises(ValidationError):
            QuestionModel(
                enunciado="Pergunta",
                opcoes=["A", "B", "C", "D"],
                resposta_correta=5
            )

    def test_quiz_result_request(self):
        request = QuizResultRequest(
            respostas={0: 2, 1: 1, 2: 0, 3: 3}
        )
        assert len(request.respostas) == 4