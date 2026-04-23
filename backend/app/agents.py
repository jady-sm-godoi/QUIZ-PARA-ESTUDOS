from agno.agent import Agent
from agno.models.openai import OpenAIChat
import json
import os


MODEL_ID = "gpt-4o-mini"


def get_api_key() -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        try:
            from app.config import get_settings
            settings = get_settings()
            api_key = settings.openai_api_key
        except:
            pass
    return api_key


def create_quiz_agent(model_id: str = MODEL_ID) -> Agent:
    api_key = get_api_key()
    return Agent(
        model=OpenAIChat(id=model_id, api_key=api_key),
        markdown=False,
    )


QUIZ_SYSTEM_PROMPT = """Você é um professor especializado em criar quizzes de múltipla escolha para estudantes.

Sua tarefa é criar perguntas de quiz baseadas no conteúdo fornecido.

REGRAS OBRIGATÓRIAS:
1. Gere exatamente {num_questions} perguntas
2. Cada pergunta deve ter EXATAMENTE 4 opções (A, B, C, D)
3. Apenas UMA opção deve ser a resposta correta
4. Inclua uma explicação para cada resposta correta
5. As perguntas devem ser claras e objetivas
6. Use apenas informações do conteúdo fornecido
7. Não revele a resposta correta no enunciado

FORMATO DE RESPOSTA (JSON):
{{
    "questions": [
        {{
            "enunciado": "Pergunta clara e objetiva",
            "opcoes": ["Opção A", "Opção B", "Opção C", "Opção D"],
            "resposta_correta": 0,
            "explicacao": "Explicação da resposta correta"
        }}
    ]
}}

Exemplo de resposta_correta:
- 0 = primeira opção (A)
- 1 = segunda opção (B)
- 2 = terceira opção (C)
- 3 = quarta opção (D)"""


class QuizAgent:
    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id
        self.agent = create_quiz_agent(model_id)

    def generate(self, content: str, num_questions: int = 10) -> dict:
        prompt = QUIZ_SYSTEM_PROMPT.format(num_questions=num_questions)
        prompt += f"\n\nCONTEÚDO:\n{content}"

        response = self.agent.run(prompt)

        try:
            text = response.content.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            result = json.loads(text.strip())
            return result
        except json.JSONDecodeError:
            return {"questions": self._parse_fallback(response.content, num_questions)}

    def _parse_fallback(self, content: str, num_questions: int) -> list:
        questions = []
        lines = content.split("\n")
        current_question = None
        options = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line[0].isdigit() and "." in line[:3]:
                if current_question and len(options) >= 4:
                    questions.append({
                        "enunciado": current_question,
                        "opcoes": options[:4],
                        "resposta_correta": 0,
                        "explicacao": ""
                    })
                current_question = line.split(".", 1)[1].strip() if "." in line else line
                options = []
            elif line.startswith(("A)", "A-", "A.")) or (len(line) > 1 and line[0] == "A" and line[1] in ")-."):
                options.append(line[2:].strip() if len(line) > 2 else line)
            elif line.startswith(("B)", "B-", "B.")) or (len(line) > 1 and line[0] == "B" and line[1] in ")-."):
                options.append(line[2:].strip() if len(line) > 2 else line)
            elif line.startswith(("C)", "C-", "C.")) or (len(line) > 1 and line[0] == "C" and line[1] in ")-."):
                options.append(line[2:].strip() if len(line) > 2 else line)
            elif line.startswith(("D)", "D-", "D.")) or (len(line) > 1 and line[0] == "D" and line[1] in ")-."):
                options.append(line[2:].strip() if len(line) > 2 else line)

        if current_question and len(options) >= 4:
            questions.append({
                "enunciado": current_question,
                "opcoes": options[:4],
                "resposta_correta": 0,
                "explicacao": ""
            })

        return questions[:num_questions]


def generate_quiz_content(content: str, num_questions: int = 10) -> dict:
    agent = QuizAgent()
    return agent.generate(content, num_questions)


def generate_quiz_with_category(content: str, category: str, num_questions: int = 10) -> dict:
    prompt = QUIZ_SYSTEM_PROMPT.format(num_questions=num_questions)
    prompt += f"\n\nCATEGORIA: {category}"
    prompt += f"\n\nCONTEÚDO:\n{content}"

    agent = create_quiz_agent()
    response = agent.run(prompt)

    try:
        text = response.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        result = json.loads(text.strip())
        return result
    except json.JSONDecodeError:
        return {"questions": []}