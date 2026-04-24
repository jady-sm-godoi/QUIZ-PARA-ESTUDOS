# Quiz para Estudos

Aplicação web para gerar quizzes de múltipla escolha a partir de materiais de estudo usando inteligência artificial (Agno AI + GPT-4o-mini). Ideal para concurseiros e estudantes.

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Instalação](#instalação)
4. [Configuração](#configuração)
5. [Rodando a Aplicação](#rodando-a-aplicação)
6. [Testes](#testes)
7. [API Endpoints](#api-endpoints)
8. [Estrutura do Projeto](#estrutura-do-projeto)
9. [Funcionalidades](#funcionalidades)
10. [Tecnologias](#tecnologias)

---

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (HTML/JS)                       │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│   │  Upload de   │   │   Geração    │   │  Histórico   │       │
│   │   Arquivos   │   │    de Quiz   │   │   de Quiz    │       │
│   └──────────────┘   └──────────────┘   └──────────────┘       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                           │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│   │   REST API   │   │   Agno AI    │   │   SQLite     │       │
│   │   Endpoints  │ ─▶│  (GPT-4o)    │   │   Database   │       │
│   └──────────────┘   └──────────────┘   └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Pré-requisitos

- **Python** 3.10+
- **pip** (gerenciador de pacotes Python)
- **git** (controle de versão)
- **Navegador web** moderno (Chrome, Firefox, Edge)
- **Chave da API OpenAI** (para geração de quizzes)

---

## Instalação

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd quiz-para-estudos
```

### 2. Crie um ambiente virtual (recomendado)

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
# Navegue para o diretório backend
cd backend

# Instale as dependências
pip install -r requirements.txt
```

### 4. Instale dependências de teste (opcional)

```bash
# Volte para o diretório raiz
cd ..

# Instale Playwright para testes de frontend
pip install pytest-playwright playwright

# Instale os navegadores do Playwright
playwright install chromium
```

---

## Configuração

### 1. Configure a variável de ambiente para a API da OpenAI

Crie um arquivo `.env` na pasta `backend/`:

```bash
cd backend
cp .env.example .env
```

Edite o arquivo `.env` e adicione sua chave da API:

```env
OPENAI_API_KEY=sk-sua-chave-aqui
```

**Como obter a chave:**
1. Acesse [OpenAI Platform](https://platform.openai.com/)
2. Crie uma conta ou faça login
3. Vá em API Keys
4. Crie uma nova chave

### 2. Entendendo a estrutura do banco de dados

O SQLite criará automaticamente o banco de dados `quiz.db` na pasta `backend/` quando a aplicação iniciar pela primeira vez.

---

## Rodando a Aplicação

### Servidor de Desenvolvimento

```bash
# Ative o ambiente virtual (se ainda não ativo)
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows

# Navegue para o backend
cd backend

# Inicie o servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Acesse a aplicação

Abra seu navegador e vá para:

```
http://localhost:8000
```

### Funcionalidades disponíveis

1. **Gerar Quiz**: Cole texto ou faça upload de arquivo (PDF, TXT, DOCX)
2. **Categorias**: Organize materiais por categoria ou crie novas
3. **Responder Quiz**: Responda perguntas de múltipla escolha
4. **Ver Resultados**: Acompanhe acertos e explicações
5. **Histórico**: Veja quizzes anteriores

---

## Testes

### Executando testes do backend (72 testes)

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute os testes do backend
pytest tests/ --ignore=tests/test_frontend_playwright.py -v
```

### Executando testes do frontend (12 testes)

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute os testes do frontend (inicia servidor automaticamente)
pytest tests/test_frontend_playwright.py -v
```

### Executando todos os testes

```bash
# Execute todos os testes separadamente (recomendado)
pytest tests/ --ignore=tests/test_frontend_playwright.py -v
pytest tests/test_frontend_playwright.py -v
```

### Verbosidade dos testes

```bash
# Saída detalhada
pytest -v

# Mostrar print statements
pytest -v -s

# Parar no primeiro erro
pytest -x
```

---

## API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Serve o frontend estático |
| `GET` | `/api/categories` | Lista todas as categorias |
| `GET` | `/api/categories/{category}/materials` | Lista materiais de uma categoria |
| `POST` | `/api/generate` | Gera quiz a partir de texto |
| `POST` | `/api/generate/file` | Gera quiz a partir de arquivo |
| `GET` | `/api/quiz/{quiz_id}` | Busca quiz por ID |
| `POST` | `/api/quiz/{quiz_id}/submit` | Envia respostas e calcula resultado |
| `GET` | `/api/history` | Lista histórico de quizzes |
| `POST` | `/api/upload` | Faz upload de material para uma categoria |

### Exemplos de uso

#### Gerar quiz com texto
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "titulo": "Quiz de Português",
    "conteudo": "Texto do material de estudo...",
    "num_perguntas": 10,
    "categoria": "Português"
  }'
```

#### Listar categorias
```bash
curl http://localhost:8000/api/categories
```

#### Ver histórico
```bash
curl http://localhost:8000/api/history
```

---

## Estrutura do Projeto

```
quiz-para-estudos/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app principal
│   │   ├── routes.py            # Endpoints da API
│   │   ├── models.py            # Modelos Pydantic
│   │   ├── database.py          # SQLite conexão e queries
│   │   ├── agents.py            # Agno Agent (GPT-4o-mini)
│   │   ├── pdf_utils.py         # Extração de texto (PDF/DOCX)
│   │   └── config.py            # Configurações
│   ├── requirements.txt         # Dependências Python
│   ├── .env                     # Variáveis de ambiente
│   └── quiz.db                  # Banco SQLite (criado automaticamente)
│
├── frontend/
│   ├── index.html               # Interface principal
│   ├── css/
│   │   └── style.css            # Estilos CSS
│   ├── js/
│   │   └── app.js               # Lógica JavaScript
│   └── assets/
│       └── tl.webp              # Imagens
│
├── tests/                       # Testes automatizados
│   ├── test_api.py
│   ├── test_generate.py
│   ├── test_submit.py
│   ├── test_upload.py
│   ├── test_categories_history.py
│   ├── test_frontend_playwright.py
│   ├── conftest.py
│   └── __init__.py
│
├── venv/                        # Ambiente virtual Python
├── pytest.ini                   # Configuração do pytest
├── .gitignore
├── project_plan.md              # Plano do projeto
└── README.md                    # Este arquivo
```

---

## Funcionalidades

### Core

- [x] Upload de arquivos (PDF, TXT, DOCX)
- [x] Cola de conteúdo direto no textarea
- [x] Geração de quiz via Agno Agent (GPT-4o-mini)
- [x] Feedback imediato ao carregar arquivo
- [x] Resposta correta/errada com cores (verde/vermelho)
- [x] Explicação da resposta correta
- [x] Resultado final com score
- [x] Histórico de quizzes

### Sistema de Categorias

- [x] Criar categorias para organizar materiais
- [x] Selecionar categoria existente
- [x] Concatenar múltiplos materiais na mesma categoria
- [x] Gerar quiz sobre todos os materiais da categoria
- [x] Cache de materiais para economia de tokens
- [x] Usar material existente sem fazer novo upload

### Interface

- [x] Seleção de categoria via radio buttons
- [x] Toggle entre categoria existente e nova
- [x] Drag and drop para upload de arquivos
- [x] Design responsivo
- [x] Paleta de cores customizada

### Segurança e Performance

- [x] Truncagem de conteúdo para evitar limite de tokens (50.000 chars)
- [x] Cache de materiais por hash MD5
- [x] Divisão de conteúdo grande em partes
- [x] Cada quiz é único (não reutiliza perguntas)

---

## Paleta de Cores

O projeto usa uma paleta de cores única:

| Cor | Hex | Uso |
|-----|-----|-----|
| Amarelo Mostarda | `#b5ac01` | Cor principal, botões, acertos |
| Amarelo Dourado | `#ecba09` | Títulos, destaque |
| Laranja | `#e86e1c` | Botões secundários |
| Vermelho | `#d41e45` | Erros, alertas |
| Preto Escuro | `#1b1521` | Header, texto principal |
| Cinza Claro | `#f5f5f0` | Fundo da página |

---

## Tecnologias

### Backend
- **FastAPI** - Framework web moderno e rápido
- **SQLite** - Banco de dados leve
- **Agno** - Agentes de IA
- **OpenAI** - GPT-4o-mini para geração de conteúdo
- **PyPDF2** - Extração de texto de PDF
- **python-docx** - Extração de texto de DOCX

### Frontend
- **Vanilla JavaScript** - Sem frameworks
- **HTML5** - Semântica e estrutura
- **CSS3** - Estilos e responsividade

### Testes
- **pytest** - Framework de testes Python
- **pytest-asyncio** - Testes assíncronos
- **pytest-playwright** - Testes E2E de navegador
- **Playwright** - Automação de navegador

---

## Solução de Problemas

### "OPENAI_API_KEY not found"

Configure sua chave no arquivo `.env`:
```bash
cd backend
echo "OPENAI_API_KEY=sua-chave-aqui" > .env
```

### Porta em uso

Se a porta 8000 estiver em uso:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Testes falhando

Certifique-se de que o ambiente virtual está ativado:
```bash
source venv/bin/activate
pytest tests/ --ignore=tests/test_frontend_playwright.py -v
```

### Banco de dados corrompido

Delete o banco e reinicie:
```bash
rm backend/quiz.db
uvicorn app.main:app --reload
```

---

## Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## Licença

MIT License

---

## Autor

Desenvolvido para ajudar estudantes e concurseiros a estudar de forma eficiente usando IA.