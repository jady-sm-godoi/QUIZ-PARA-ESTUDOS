# Quiz para Estudos - Plano de Desenvolvimento

## Visão Geral do Projeto

**Quiz para Estudos** é uma aplicação web completa para gerar quizzes de múltipla escolha a partir de materiais de estudo (PDF, TXT, DOCX) usando inteligência artificial (Agno AI com GPT-4o-mini).

### Propósito
- Auxiliar concurseiros e estudantes na preparação para provas
- Gerar perguntas automaticamente baseadas em materiais de estudo
- Organizar materiais por categorias
- Acompanhar histórico de estudos

### Público-alvo
- Estudantes preparing for exams
- Concurseiros
- Professores que querem criar material de estudo

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Port 8000)                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Browser (HTML/CSS/JS)                       │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │   │
│  │  │  Gerar    │  │  Responder │  │ Histórico │  │ Upload    │    │   │
│  │  │   Quiz    │  │   Quiz     │  │  de Quiz  │  │ Material  │    │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│                          API REST (FastAPI)                             │
└──────────────────────────────────┬──────────────────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
   │   SQLite DB   │      │  Agno Agent   │      │  Upload Files │
   │   (quiz.db)   │      │ (GPT-4o-mini) │      │   (PDF/DOCX)  │
   └───────────────┘      └───────────────┘      └───────────────┘
```

### Stack Tecnológico

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Backend | FastAPI | 0.109.0 |
| Servidor | Uvicorn | 0.27.0 |
| Validação | Pydantic | 2.5.3 |
| IA | Agno | 1.8.0 |
| Modelo | OpenAI GPT-4o-mini | - |
| Banco | SQLite | 3.x (Python) |
| Extração PDF | PyPDF2 | 3.0.1 |
| Extração DOCX | python-docx | 1.1.0 |
| Frontend | Vanilla JS | ES6+ |
| Estilos | CSS3 | - |
| Testes Backend | pytest | 7.4.4 |
| Testes Frontend | Playwright | 1.58.0 |

---

## Estrutura de Diretórios

```
quiz-para-estudos/
├── backend/
│   ├── app/
│   │   ├── __init__.py           # Pacote Python
│   │   ├── main.py               # FastAPI app + lifespan + static files
│   │   ├── routes.py             # Todos os endpoints da API (500 linhas)
│   │   ├── models.py             # Modelos Pydantic (requisições/respostas)
│   │   ├── database.py           # Conexão SQLite e init_db()
│   │   ├── agents.py             # QuizAgent (Agno + GPT-4o-mini)
│   │   ├── pdf_utils.py          # Extração de texto (PDF, DOCX, TXT)
│   │   └── config.py             # Configurações (settings)
│   ├── requirements.txt          # Dependências Python
│   ├── .env                      # Variáveis de ambiente (API key)
│   └── quiz.db                   # Banco SQLite (criado automaticamente)
│
├── frontend/
│   ├── index.html                # Interface principal
│   ├── css/
│   │   └── style.css             # Estilos (519 linhas)
│   ├── js/
│   │   └── app.js                # Lógica JS (547 linhas)
│   └── assets/
│       └── tl.webp               # Imagens
│
├── tests/
│   ├── conftest.py               # Fixtures pytest
│   ├── test_api.py               # Testes endpoints básicos
│   ├── test_generate.py          # Testes geração de quiz
│   ├── test_submit.py            # Testes submissão respostas
│   ├── test_upload.py            # Testes upload de arquivos
│   ├── test_categories_history.py # Testes categorias e histórico
│   ├── test_category_materials.py # Testes materiais por categoria
│   ├── test_frontend_playwright.py # Testes E2E frontend (12 testes)
│   └── test_frontend_flows.py    # Testes fluxo completo (API)
│
├── pytest.ini                    # Configuração pytest
├── README.md                     # Guia de uso
├── project_plan.md               # Este documento
└── venv/                         # Ambiente virtual Python
```

---

## Banco de Dados

### Schema SQLite

O banco é inicializado automaticamente em `init_db()` em `backend/app/database.py`.

```sql
-- Tabela principal: quizzes gerados
CREATE TABLE quizzes (
    id TEXT PRIMARY KEY,           -- UUID único
    titulo TEXT NOT NULL,          -- Título do quiz
    material_hash TEXT,            -- Hash do conteúdo usado
    criado_em TIMESTAMP            -- Data de criação
);

-- Perguntas de cada quiz
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id TEXT NOT NULL,         -- FK para quizzes.id
    enunciado TEXT NOT NULL,       -- Texto da pergunta
    opcoes TEXT NOT NULL,          -- JSON array com 4 opções
    resposta_correta INTEGER,      -- Índice 0-3 da resposta correta
    explicacao TEXT DEFAULT '',    -- Explicação da resposta
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
);

-- Resultados dos quizzes respondidos
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id TEXT NOT NULL,         -- FK para quizzes.id
    acertos INTEGER NOT NULL,      -- Número de acertos
    total INTEGER NOT NULL,        -- Total de perguntas
    completado_em TIMESTAMP,       -- Data de submissão
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
);

-- Materiais/materials carregados (cache)
CREATE TABLE materials (
    hash TEXT PRIMARY KEY,         -- MD5 do conteúdo
    filename TEXT,                 -- Nome do arquivo original
    content TEXT,                  -- Texto extraído
    category TEXT,                 -- Categoria do material
    criado_em TIMESTAMP            -- Data de upload
);
```

### Conexão com Banco

**Arquivo:** `backend/app/database.py`

```python
DATABASE_PATH = Path(__file__).parent.parent / "quiz.db"

def get_connection() -> sqlite3.Connection:
    """Retorna conexão com o banco."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
    return conn

def init_db():
    """Cria todas as tabelas se não existirem."""
    # Ver código acima para schema completo
```

### Modo de Testes

O projeto suporta banco de dados temporário para testes:

```python
def set_test_db(path: Optional[str]):
    """Define caminho do banco de testes."""
    _test_db_path = Path(path) if path else None

def is_test_mode() -> bool:
    return _test_db_path is not None
```

---

## API Endpoints

Todos os endpoints usam o prefixo `/api`.

### Endpoints Principais

| Método | Endpoint | Descrição | Corpo da Requisição |
|--------|----------|-----------|---------------------|
| `POST` | `/generate` | Gera quiz de texto | `QuizGenerateRequest` |
| `POST` | `/generate/file` | Gera quiz de arquivo | `FormData` |
| `GET` | `/quiz/{quiz_id}` | Busca quiz por ID | - |
| `POST` | `/quiz/{quiz_id}/submit` | Envia respostas | `QuizResultRequest` |
| `GET` | `/history` | Lista histórico | - |
| `GET` | `/categories` | Lista categorias | - |
| `GET` | `/categories/{category}/materials` | Materiais de categoria | - |
| `POST` | `/upload` | Upload material | `FormData` |

### Modelos de Requisição

**Arquivo:** `backend/app/models.py`

```python
# POST /generate
class QuizGenerateRequest(BaseModel):
    titulo: str                              # Obrigatório, 1-200 chars
    conteudo: Optional[str]                  # Texto do material
    num_perguntas: int = 10                  # 1-50 perguntas
    categoria: Optional[str]                 # Nome da categoria
    part_index: Optional[int]                # Índice para conteúdo grande

# POST /quiz/{id}/submit
class QuizResultRequest(BaseModel):
    respostas: dict[int, int]                # {indice_pergunta: indice_resposta}

# Resposta de categorias
class CategoryResponse(BaseModel):
    name: str
    material_count: int

# Resposta de materiais
class MaterialResponse(BaseModel):
    hash: str
    filename: Optional[str]
    content: Optional[str]
    category: Optional[str]
    criado_em: datetime
```

### Lógica de Geração de Quiz

**Arquivo:** `backend/app/routes.py` - Função `generate_quiz()`

1. **Verifica categoria:** Se `categoria` informada, busca materiais no banco
2. **Concatena conteúdo:** Se há materiais + novo conteúdo, combina os dois
3. **Verifica necessidade de divisão:** Se > 60.000 chars, divide em partes
4. **Trunca se necessário:** Limita a 50.000 chars por chamada à API
5. **Chama Agno Agent:** Gera perguntas usando GPT-4o-mini
6. **Salva no banco:** Cria registro em `quizzes` e `questions`
7. **Retorna:** `QuizResponse` com ID e perguntas

### Lógica de Submissão

**Arquivo:** `backend/app/routes.py` - Função `submit_quiz()`

1. **Busca quiz:** Verifica se quiz existe
2. **Busca perguntas:** Recupera todas as perguntas do banco
3. **Compara respostas:** Para cada pergunta, verifica se resposta do usuário = resposta_correta
4. **Calcula score:** Conta acertos / total
5. **Salva/atualiza resultado:** Cria novo ou atualiza existente em `results`
6. **Retorna:** Score e timestamp

---

## Agente de IA (Agno)

**Arquivo:** `backend/app/agents.py`

### Classe QuizAgent

```python
class QuizAgent:
    def __init__(self, model_id: str = "gpt-4o-mini"):
        self.model_id = model_id
        self.agent = create_quiz_agent(model_id)

    def generate(self, content: str, num_questions: int = 10) -> dict:
        """Gera quiz a partir do conteúdo."""
        # Retorna: {"questions": [...]}
```

### Prompt do Sistema

O agente usa um prompt fixo em `QUIZ_SYSTEM_PROMPT` que:
- Gera exatamente N perguntas
- Cada pergunta tem 4 opções (A, B, C, D)
- Uma única resposta correta
- Inclui explicação para cada resposta
- Formato JSON de saída

### Fallback Parser

Se a API retornar formato inválido, há `_parse_fallback()` que tenta extrair perguntas de texto livre.

### API Key

A chave da OpenAI é obtida de (ordem de prioridade):
1. Variável de ambiente `OPENAI_API_KEY`
2. Arquivo `.env` via `app.config.get_settings()`

---

## Extração de Texto

**Arquivo:** `backend/app/pdf_utils.py`

### Função principal: `extract_text(content: bytes, filename: str) -> str`

| Extensão | Método |
|----------|--------|
| `.pdf` | PyPDF2.PdfReader |
| `.docx` | python-docx.Document |
| `.txt` | Decodificação UTF-8 |
| Outros | Retorna string vazia |

---

## Frontend

**Arquivo:** `frontend/js/app.js`

### Inicialização

```javascript
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initGenerateForm();
    initSubmitQuiz();
    initNewQuiz();
    initUploadForm();
    initHistory();
    initPartsModal();
    initCategoryRadio();
    initFileUpload();
    loadCategories();
});
```

### Funções Principais

| Função | Descrição |
|--------|-----------|
| `initGenerateForm()` | Handler do formulário de geração |
| `initSubmitQuiz()` | Handler de submissão de respostas |
| `loadCategories()` | Carrega categorias do backend |
| `showSection(id)` | Alterna entre seções |
| `toggleCategory(type, value)` | Alterna select/input de categoria |
| `initFileUpload()` | Drag & drop e click para upload |

### UI/UX

- **Paleta de cores:** Amarelo mostarda (#b5ac01), dourado (#ecba09), laranja (#e86e1c), vermelho (#d41e45)
- **Categorias:** Radio buttons para Existing/New
- **Upload:** Drag & drop com feedback visual (classe `dragover`)
- **Formulários:** Validação client-side + server-side

---

## Testes

### Testes Backend (72 testes)

Executar: `pytest tests/ --ignore=tests/test_frontend_playwright.py`

| Arquivo | Qtd | Descrição |
|---------|-----|-----------|
| test_api.py | 5 | Endpoints básicos |
| test_generate.py | 10 | Geração de quiz |
| test_submit.py | 9 | Submissão de respostas |
| test_upload.py | 9 | Upload de arquivos |
| test_categories_history.py | 7 | Categorias e histórico |
| test_category_materials.py | 8 | Materiais por categoria |
| test_quiz_by_id.py | 7 | Busca quiz por ID |
| test_agents.py | 6 | Agente de IA |
| test_database.py | 4 | Banco de dados |
| test_models.py | 3 | Modelos Pydantic |
| test_content_split.py | 4 | Divisão de conteúdo |

### Testes Frontend (12 testes)

Executar: `pytest tests/test_frontend_playwright.py`

Testes cobrem:
- Carregamento da página
- Navegação entre seções
- Toggle de categoria
- Upload de arquivo (drag & drop)
- Elementos do DOM

### Teste Isolation

Os testes de backend usam:
- `tempfile.NamedTemporaryFile` para banco temporário
- `set_test_db(path)` para isolar testes
- `ASGITransport` para testes sem servidor real

Os testes de frontend usam:
- Servidor real em porta 8766 (fixture `server`)
- Playwright para automação de navegador

---

## Configuração

### Variáveis de Ambiente

**Arquivo:** `backend/.env`

```env
OPENAI_API_KEY=sk-sua-chave-aqui
```

### Configurações do Python

**Arquivo:** `backend/app/config.py`

Busca a API key de `OPENAI_API_KEY` ou do `.env`.

---

## Comandos Úteis

```bash
# Ativar ambiente virtual
source venv/bin/activate  # Linux/macOS

# Instalar dependências
cd backend && pip install -r requirements.txt

# Rodar servidor
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Rodar testes backend
pytest tests/ --ignore=tests/test_frontend_playwright.py -v

# Rodar testes frontend
pytest tests/test_frontend_playwright.py -v

# Acessar aplicação
http://localhost:8000
```

---

## Decisões de Design

### Por que FastAPI?
- Assíncrono (performance)
- Validação automática com Pydantic
- Documentação automática (Swagger UI)

### Por que SQLite?
- Zero configuração
-足够 para uso单人
- Portável (arquivo único)

### Por que Vanilla JS?
- Sem build steps
- Sem dependências frontend
- Simplicidade de manutenção

### Por que Agno?
- Abstração sobre LLMs
- Fácil de usar
- Suporte a múltiplos modelos

### Por que GPT-4o-mini?
- Custo baixo
- Boa performance para tarefas simples
- Velocidade adequada

---

## Limitações Conhecidas

1. **Tamanho do conteúdo:** Máximo ~50.000 caracteres por geração
2. **Conteúdo muito grande:** Dividido em partes, usuário deve escolher
3. **Sem autenticação:** Qualquer pessoa pode acessar
4. **Sem persistência de sessões:** Quiz ID é transient
5. **API key necessária:** Sem chave, não gera quizzes

---

## Possíveis Melhorias Futuras

- [ ] Autenticação de usuários
- [ ] Mais formatos de arquivo (EPUB, Markdown)
- [ ] Exportar quiz em PDF
- [ ] Modo de estudo (revisar apenas erradas)
- [ ] Temporizador por pergunta
- [ ] Ranking/pontuação por categoria
- [ ] Importar de URLs
- [ ] Bulk upload de arquivos
- [ ] RAG completo (busca semântica)
- [ ] Cache de quizzes gerados
- [ ] Compartilhar quiz por link

---

## Glossário

| Termo | Definição |
|-------|-----------|
| Quiz | Conjunto de perguntas de múltipla escolha |
| Material | Conteúdo de estudo (arquivo ou texto) |
| Categoria | Agrupador de materiais relacionados |
| Hash | MD5 do conteúdo para cache/deduplicação |
| Part | Parte de um conteúdo grande (split) |
| Agente | Wrapper de IA para geração de conteúdo |
| Score | Porcentagem de acertos (acertos/total) |

---

## Para Agentes de IA Futuros

Ao dar suporte a este projeto:

1. **Leia este documento** para entender a arquitetura
2. **Consulte README.md** para instruções de setup
3. **Execute testes** para verificar mudanças: `pytest tests/ -v`
4. **Backend está em:** `backend/app/`
5. **Frontend está em:** `frontend/`
6. **Testes estão em:** `tests/`
7. **Banco é SQLite em:** `backend/quiz.db`
8. **A API key** é necessária em `backend/.env`

Para modificar algo:
- Endpoints: edite `backend/app/routes.py`
- Modelos: edite `backend/app/models.py`
- Banco: edite `backend/app/database.py`
- IA: edite `backend/app/agents.py`
- UI: edite `frontend/index.html`, `frontend/css/style.css`, `frontend/js/app.js`

Sempre rode os testes após mudanças:
```bash
pytest tests/ --ignore=tests/test_frontend_playwright.py -v
```