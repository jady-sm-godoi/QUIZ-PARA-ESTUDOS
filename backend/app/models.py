from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# Modelos são estruturas que definem como os dados devem ser. Pense neles como "formulários" que validam informações.


class QuizGenerateRequest(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    conteudo: Optional[str] = None
    num_perguntas: int = Field(default=10, ge=1, le=50)
    categoria: Optional[str] = None


class QuestionModel(BaseModel):
    enunciado: str
    opcoes: list[str]
    resposta_correta: int = Field(ge=0, le=3)
    explicacao: str = ""


class QuizResponse(BaseModel):
    quiz_id: str
    titulo: str
    perguntas: list[QuestionModel]


class QuizResultRequest(BaseModel):
    respostas: dict[int, int]


class QuizResult(BaseModel):
    quiz_id: str
    acertos: int
    total: int
    completado_em: datetime


class CategoryResponse(BaseModel):
    name: str
    material_count: int


class MaterialResponse(BaseModel):
    hash: str
    filename: Optional[str]
    content: Optional[str]
    category: Optional[str]
    criado_em: datetime
