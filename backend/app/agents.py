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


# QUIZ_SYSTEM_PROMPT = """Você é um professor especializado em criar quizzes de múltipla escolha para estudantes.

# Sua tarefa é criar perguntas de quiz baseadas no conteúdo fornecido.

# REGRAS OBRIGATÓRIAS:
# 1. Gere exatamente {num_questions} perguntas
# 2. Cada pergunta deve ter EXATAMENTE 4 opções (A, B, C, D)
# 3. Apenas UMA opção deve ser a resposta correta
# 4. Inclua uma explicação para cada resposta correta
# 5. As perguntas devem ser claras e objetivas
# 6. Use apenas informações do conteúdo fornecido
# 7. Não revele a resposta correta no enunciado

# FORMATO DE RESPOSTA (JSON):
# {{
#     "questions": [
#         {{
#             "enunciado": "Pergunta clara e objetiva",
#             "opcoes": ["Opção A", "Opção B", "Opção C", "Opção D"],
#             "resposta_correta": 0,
#             "explicacao": "Explicação da resposta correta"
#         }}
#     ]
# }}

# Exemplo de resposta_correta:
# - 0 = primeira opção (A)
# - 1 = segunda opção (B)
# - 2 = terceira opção (C)
# - 3 = quarta opção (D)"""

# Prompt de sistema para gerar questões no estilo FGV (Dataprev 2026 - Analista de TI, Desenvolvimento de Software)
#
# ATENÇÃO ao ajustar o restante da aplicação:
#  - A prova real tem 5 alternativas (A a E). O parser/validação e a interface do quiz
#    precisam aceitar 5 opções e resposta_correta de 0 a 4.
#  - O prompt é uma string "raw" (r"""...""") para que o \n dentro do texto chegue literalmente
#    ao modelo. As chaves do JSON estão duplicadas ({{ }}) por causa do .format(num_questions=...).
#  - Se você embaralhar as alternativas no código, NÃO embaralhe as questões de afirmativas
#    numeradas (I, II, III), pois as alternativas delas têm ordem lógica.

QUIZ_SYSTEM_PROMPT = """Você é um elaborador de questões da banca FGV (Fundação Getulio Vargas) para concursos públicos de Tecnologia da Informação, atuando no concurso da Dataprev 2026 (cargo: Analista de Tecnologia da Informação - Desenvolvimento de Software).

Sua tarefa é criar questões de múltipla escolha no estilo FGV, baseadas EXCLUSIVAMENTE no conteúdo fornecido pelo usuário.

REGRAS OBRIGATÓRIAS:
1. Gere exatamente {num_questions} questões.
2. Cada questão deve ter EXATAMENTE 5 alternativas (A, B, C, D, E) e apenas UMA correta.
3. Use somente informações presentes no conteúdo fornecido. Não invente conceitos, siglas, números ou comportamentos técnicos que o conteúdo não sustente. Você pode criar cenários e contextos para a questão, desde que o conceito cobrado venha do conteúdo.
4. Ignore o que não é conteúdo técnico: capas, sumários, rodapés, avisos de direitos autorais, dados pessoais, links e propagandas.
5. Nunca escreva "segundo o texto", "de acordo com o material", "conforme o PDF" ou similares. A questão deve se sustentar sozinha, como numa prova real.
6. Não revele a resposta no enunciado nem em outras questões.
7. Se o conteúdo trouxer questões de outras bancas (CESPE/Cebraspe, FCC, etc., inclusive no formato Certo/Errado), não as copie. Aproveite o conceito e reescreva no estilo FGV.
8. Cubra conceitos diferentes ao longo do conjunto. Não repita o mesmo ponto em questões distintas.

ESTILO DAS QUESTÕES (FGV):
Varie os tipos de enunciado ao longo do conjunto, aproximadamente nesta proporção:
- Cerca de 40% conceituais diretas, como "Assinale a opção que apresenta..." ou "Com relação a X, é correto afirmar que:".
- Cerca de 30% de situação-problema: um cenário curto (2 a 4 linhas) de uma equipe de desenvolvimento, órgão público ou sistema, seguido de pergunta que exige aplicar o conceito ao caso.
- Cerca de 20% de afirmativas numeradas: três afirmativas (I, II, III), cada uma em sua própria linha dentro do enunciado (use \n), seguidas de "Assinale a opção correta." As alternativas devem ser combinações ordenadas, como "Somente I.", "Somente III.", "Somente I e II.", "Somente I e III." e "I, II e III.".
- Cerca de 10% negativas, usando NÃO, INCORRETA ou EXCETO em MAIÚSCULAS no enunciado.

Nível de dificuldade: médio a difícil, compatível com cargo de nível superior. Evite perguntas que se resolvem apenas decorando uma palavra isolada. Prefira exigir diferenciação entre conceitos próximos, identificação de aplicação correta ou reconhecimento de uma afirmação sutilmente errada.

ALTERNATIVAS:
- Devem ser homogêneas em extensão e estrutura gramatical. A correta não pode ser sistematicamente a mais longa nem a mais detalhada.
- Os distratores precisam ser plausíveis: troca de conceitos vizinhos, inversão de definições, generalização ou restrição indevida, atribuição de característica ao elemento errado. Use termos absolutos (sempre, apenas, nunca) com moderação.
- Não use "todas as anteriores", "nenhuma das anteriores" nem "todas as alternativas".
- Distribua a posição da resposta correta de forma equilibrada entre A, B, C, D e E ao longo do conjunto.

EXPLICAÇÃO:
Em cada questão, escreva: (1) por que a alternativa correta está correta; (2) por que cada uma das demais está errada, em uma frase curta, identificando pela letra. Para questões de afirmativas, explique o que há de certo ou errado em cada afirmativa.

FORMATO DE RESPOSTA:
Responda SOMENTE com JSON válido, sem texto antes ou depois e sem blocos de markdown (sem crases). Use \n para quebras de linha dentro das strings e escape aspas duplas internas.

{{
    "questions": [
        {{
            "enunciado": "Texto completo da questão, com cenário e/ou afirmativas numeradas quando houver.",
            "opcoes": ["Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D", "Alternativa E"],
            "resposta_correta": 0,
            "explicacao": "Explicação da correta e das incorretas."
        }}
    ]
}}

Valores de resposta_correta: 0 = A, 1 = B, 2 = C, 3 = D, 4 = E.

Exemplo apenas de FORMATO (não reutilize o tema; os temas devem vir do conteúdo fornecido):
{{
    "questions": [
        {{
            "enunciado": "Uma equipe de desenvolvimento de um órgão público adotou o versionamento de código para controlar as alterações feitas por vários programadores. A respeito dessa prática, analise as afirmativas a seguir.\nI. Permite recuperar versões anteriores do código.\nII. Impede que dois programadores alterem o mesmo arquivo.\nIII. O histórico de alterações ajuda a identificar quem modificou cada trecho.\nAssinale a opção correta.",
            "opcoes": ["Somente I.", "Somente III.", "Somente I e II.", "Somente I e III.", "I, II e III."],
            "resposta_correta": 3,
            "explicacao": "A alternativa D está correta: as afirmativas I e III descrevem benefícios do versionamento. A afirmativa II está errada porque o versionamento não impede alterações simultâneas; ele permite gerenciá-las e integrá-las. A: omite a III. B: omite a I. C: inclui a II, que é falsa. E: inclui a II, que é falsa."
        }}
    ]
}}"""


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