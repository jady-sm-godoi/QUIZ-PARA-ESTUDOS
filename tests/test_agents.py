import pytest
from unittest.mock import patch, MagicMock


class TestQuizAgentStructure:
    """Testa a estrutura e comportamento do agente (sem chamar API real)"""

    def test_quiz_agent_class_exists(self):
        """Classe QuizAgent deve existir"""
        from app.agents import QuizAgent
        agent = QuizAgent()
        assert agent is not None
        assert hasattr(agent, 'model_id')
        assert hasattr(agent, 'agent')

    def test_quiz_agent_has_generate_method(self):
        """QuizAgent deve ter método generate"""
        from app.agents import QuizAgent
        agent = QuizAgent()
        assert hasattr(agent, 'generate')
        assert callable(agent.generate)

    def test_create_quiz_agent_function(self):
        """Função create_quiz_agent deve retornar Agent"""
        from app.agents import create_quiz_agent
        result = create_quiz_agent()
        assert result is not None


class TestQuizAgentMocked:
    """Testa o agente com resposta mockada da API"""

    @patch('app.agents.Agent')
    def test_generate_quiz_with_mock(self, mock_agent_class):
        """Deve processar resposta JSON mockada"""
        from app.agents import QuizAgent

        mock_agent_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '''{
            "questions": [
                {
                    "enunciado": "Qual é a capital do Brasil?",
                    "opcoes": ["São Paulo", "Rio de Janeiro", "Brasília", "Belo Horizonte"],
                    "resposta_correta": 2,
                    "explicacao": "Brasília é a capital do Brasil desde 1960."
                },
                {
                    "enunciado": "Qual é o maior oceano do mundo?",
                    "opcoes": ["Atlântico", "Índico", "Pacífico", "Ártico"],
                    "resposta_correta": 2,
                    "explicacao": "O Oceano Pacífico é o maior."
                }
            ]
        }'''
        mock_agent_instance.run.return_value = mock_response
        mock_agent_class.return_value = mock_agent_instance

        agent = QuizAgent()
        result = agent.generate("Conteúdo de teste", num_questions=2)

        assert "questions" in result
        assert len(result["questions"]) == 2
        assert result["questions"][0]["enunciado"] == "Qual é a capital do Brasil?"
        assert result["questions"][0]["resposta_correta"] == 2

    @patch('app.agents.Agent')
    def test_generate_quiz_with_five_options(self, mock_agent_class):
        """Cada pergunta deve ter 5 opções (estilo FGV)"""
        from app.agents import QuizAgent

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = MagicMock(content='''{
            "questions": [
                {
                    "enunciado": "Teste?",
                    "opcoes": ["A", "B", "C", "D", "E"],
                    "resposta_correta": 0,
                    "explicacao": "Porque sim"
                }
            ]
        }''')
        mock_agent_class.return_value = mock_agent_instance

        agent = QuizAgent()
        result = agent.generate("Conteúdo", num_questions=1)

        assert len(result["questions"][0]["opcoes"]) == 5

    @patch('app.agents.Agent')
    def test_generate_quiz_with_valid_resposta_index(self, mock_agent_class):
        """Resposta correta deve ter índice válido (0-3)"""
        from app.agents import QuizAgent

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = MagicMock(content='''{
            "questions": [
                {"enunciado": "Q?", "opcoes": ["A", "B", "C", "D"], "resposta_correta": 3, "explicacao": ""}
            ]
        }''')
        mock_agent_class.return_value = mock_agent_instance

        agent = QuizAgent()
        result = agent.generate("Conteúdo", num_questions=1)

        assert result["questions"][0]["resposta_correta"] in [0, 1, 2, 3]

    @patch('app.agents.Agent')
    def test_generate_quiz_parses_json_with_code_block(self, mock_agent_class):
        """Deve processar resposta com blocos de código JSON"""
        from app.agents import QuizAgent

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = MagicMock(content='''```json
{
    "questions": [
        {"enunciado": "P?", "opcoes": ["A", "B", "C", "D"], "resposta_correta": 1, "explicacao": ""}
    ]
}
```''')
        mock_agent_class.return_value = mock_agent_instance

        agent = QuizAgent()
        result = agent.generate("Conteúdo", num_questions=1)

        assert "questions" in result
        assert result["questions"][0]["enunciado"] == "P?"

    @patch('app.agents.Agent')
    def test_generate_with_different_num_questions(self, mock_agent_class):
        """Deve aceitar diferentes quantidades de perguntas"""
        from app.agents import QuizAgent

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = MagicMock(content='{"questions": []}')
        mock_agent_class.return_value = mock_agent_instance

        agent = QuizAgent()

        for num in [1, 5, 10]:
            mock_agent_instance.run.reset_mock()
            agent.generate("conteúdo", num_questions=num)
            mock_agent_instance.run.assert_called_once()

    @patch('app.agents.Agent')
    def test_generate_substitutes_num_questions_in_system_prompt(self, mock_agent_class):
        """O placeholder {num_questions} deve ser substituído no system message"""
        from app.agents import QuizAgent

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = MagicMock(content='{"questions": []}')
        mock_agent_class.return_value = mock_agent_instance

        agent = QuizAgent()
        agent.generate("conteúdo", num_questions=7)

        system_prompt = mock_agent_class.call_args.kwargs["system_message"]
        assert "Gere exatamente 7 questões." in system_prompt
        assert "{num_questions}" not in system_prompt

    @patch('app.agents.Agent')
    def test_generate_sends_content_as_user_message(self, mock_agent_class):
        """O material deve ir no user message, separado das regras do sistema"""
        from app.agents import QuizAgent

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = MagicMock(content='{"questions": []}')
        mock_agent_class.return_value = mock_agent_instance

        agent = QuizAgent()
        agent.generate("conteúdo sigiloso", num_questions=7)

        system_prompt = mock_agent_class.call_args.kwargs["system_message"]
        user_message = mock_agent_instance.run.call_args[0][0]

        assert "<material_de_estudo>" in user_message
        assert "</material_de_estudo>" in user_message
        assert "conteúdo sigiloso" in user_message
        assert "conteúdo sigiloso" not in system_prompt
        assert "POLÍTICA DE FONTES E ORIGINALIDADE" in system_prompt
        assert "Gere exatamente 7 questões." not in user_message

    @patch('app.agents.Agent')
    def test_create_quiz_agent_passes_system_message(self, mock_agent_class):
        """create_quiz_agent deve encaminhar o prompt como system_message"""
        from app.agents import create_quiz_agent

        create_quiz_agent(system_prompt="Regras da banca")

        assert mock_agent_class.call_args.kwargs["system_message"] == "Regras da banca"


class TestGenerateQuizContentFunction:
    """Testa a função auxiliar generate_quiz_content"""

    @patch('app.agents.Agent')
    def test_generate_quiz_content_returns_dict(self, mock_agent_class):
        """generate_quiz_content deve retornar dicionário"""
        from app.agents import generate_quiz_content

        mock_agent_instance = MagicMock()
        mock_agent_instance.run.return_value = MagicMock(content='{"questions": []}')
        mock_agent_class.return_value = mock_agent_instance

        result = generate_quiz_content("conteúdo", num_questions=5)

        assert isinstance(result, dict)
        assert "questions" in result