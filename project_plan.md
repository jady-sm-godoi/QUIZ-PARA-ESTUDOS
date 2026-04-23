# Quiz Generator com Agno AI

## Visão Geral

Aplicação web para gerar quizzes de múltipla escolha a partir de materiais de estudo usando inteligência artificial. Ideal para concurseiros e estudantes.

---

## Arquitetura

```
Frontend (Vanilla JS) ──▶ Backend (FastAPI) ──▶ Agno AI (GPT-4o-mini)
                               │
                               ▼
                          SQLite DB + Cache
```

---

## Funcionalidades Implementadas

### Core
- [x] Upload de arquivos (PDF, TXT, MD)
- [x] Cola de conteúdo direto no textarea
- [x] Geração de quiz via Agno Agent
- [x] Feedback imediato ao carregar arquivo
- [x] Resposta correta/errada com cores
- [x] Explicação da resposta correta
- [x] Resultado final com score
- [x] Histórico de quizzes

### Sistema de Categorias
- [x] Criar categorias para organizar materiais
- [x] Selecionar categoria existente
- [x] Concatenar múltiplos materiais na mesma categoria
- [x] Gerar quiz sobre todos os materiais da categoria
- [x] Cache de materiais para economia de tokens

### Segurança e Performance
- [x] Truncagem de conteúdo para evitar limite de tokens
- [x] Cache de materiais por hash MD5
- [x] Não reutilizar perguntas geradas (cada quiz é único)

---

## Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Serve frontend estático |
| `POST` | `/generate` | Gera quiz (com/sem categoria) |
| `GET` | `/quiz/{id}` | Busca quiz por ID |
| `POST` | `/quiz/{id}/submit` | Envia respostas e calcula resultado |
| `GET` | `/history` | Lista histórico de quizzes |
| `GET` | `/categories` | Lista categorias existentes |
| `GET` | `/categories/{category}/materials` | Lista materiais de uma categoria |

---

## Estrutura do Projeto

```
quiz-para-estudo/
├── backend/
│   ├── main.py              # FastAPI app + endpoints
│   ├── models.py           # Pydantic models
│   ├── database.py         # SQLite setup + migrations
│   ├── agents.py           # Agno Agent para gerar quizzes
│   ├── uploads/            # Arquivos salvos por categoria
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Interface principal
│   ├── css/style.css       # Estilos
│   └── js/app.js           # Lógica frontend
├── data/
│   └── quiz.db             # Banco SQLite
├── docs/
│   └── plano.md            # Este arquivo
├── .env.example
└── README.md
```

---

## Database Schema

```sql
-- Quizzes gerados
CREATE TABLE quizzes (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL,
    material_hash TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Perguntas do quiz
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id TEXT NOT NULL,
    enunciado TEXT NOT NULL,
    opcoes TEXT NOT NULL,
    resposta_correta INTEGER NOT NULL,
    explicacao TEXT DEFAULT '',
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
);

-- Resultados dos quizzes
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id TEXT NOT NULL,
    acertos INTEGER NOT NULL,
    total INTEGER NOT NULL,
    completado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
);

-- Materiais/carregados (cache)
CREATE TABLE materials (
    hash TEXT PRIMARY KEY,
    filename TEXT,
    content TEXT,
    category TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Fluxo de Uso

### Cenário 1: Novo Material
1. Selecionar "-- Digitar nova categoria"
2. Digitar nome da categoria (ex: "Português")
3. Carregar arquivo ou colar conteúdo
4. Gerar quiz

### Cenário 2: Categoria Existente (sem novo material)
1. Selecionar categoria no dropdown
2. Gerar quiz (usa todos os materiais da categoria)

### Cenário 3: Complementar Categoria
1. Selecionar categoria existente
2. Carregar novo material
3. Gerar quiz (materiais antigos + novo)

---

## Modelos Pydantic

```python
QuizGenerateRequest:
    - titulo: str
    - conteudo: Optional[str]
    - num_perguntas: int = 10
    - categoria: Optional[str]

QuizResponse:
    - quiz_id: str
    - titulo: str
    - perguntas: List[dict]  # enunciado, opcoes, resposta_correta, explicacao

QuizResult:
    - quiz_id: str
    - acertos: int
    - total: int
    - completado_em: datetime
```

---

## Comandos

```bash
# Instalar dependências
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar API key
cp .env.example .env
# Editar .env e adicionar OPENAI_API_KEY

# Rodar aplicação
uvicorn main:app --reload --host 0.0.0.0

# Acessar: http://localhost:8000
```

---

## Próximas Melhorias Possíveis

- [ ] Suporte a mais formatos (DOCX, EPUB)
- [ ] Exportar quiz em PDF
- [ ] Modo de estudo (revisar erradas)
- [ ] Temporizador por pergunta
- [ ] Ranking de pontuação por categoria
- [ ] Importar de URLs
- [ ] Bulk upload de arquivos
- [ ] RAG completo (busca semântica)