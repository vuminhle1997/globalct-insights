# Backend

A FastAPI-based REST API that powers the GlobalCT Insights platform. It integrates Azure Entra ID for authentication, LlamaIndex for RAG pipelines, ChromaDB for vector search, Redis for session management, and PostgreSQL for relational data.

---

## Table of Contents

1. [Features](#features)
2. [Architecture Overview](#architecture-overview)
3. [Project Structure](#project-structure)
4. [Quickstart](#quickstart)
5. [Environment Variables](#environment-variables)
6. [Running the Server](#running-the-server)
7. [Database Migrations](#database-migrations)
8. [Running Tests](#running-tests)
9. [Developer Guide](#developer-guide)
10. [Required Services](#required-services)

---

## Features

- **FastAPI** — High-performance async REST API
- **Azure Entra ID** — Secure authentication via OAuth2 / MSAL. No local passwords
- **LlamaIndex** — Document indexing, RAG pipelines, and SQL-to-text queries
- **ChromaDB** — Vector database for semantic document search
- **Redis** — Session management (stores Azure access tokens)
- **PostgreSQL** — Primary relational database
- **MySQL** — Optional: import MySQL/MariaDB dumps and migrate them to PostgreSQL
- **Arize Phoenix** — Tracing and observability for LLM operations
- **Multiple LLM Providers** — IONOS, Ollama (local), Google GenAI

---

## Architecture Overview

```
frontend  ──HTTP──▶  FastAPI (backend/)
                         │
               ┌─────────┴─────────────────────┐
               │                               │
          routers/api/                   services/
          ├─ auth.py          ────────▶  session_service.py
          ├─ chats.py         ────────▶  chat_service.py
          ├─ chat_inference.py ───────▶  llm_agent.py
          ├─ favourites.py               llm_factory.py
          ├─ messages.py                 indexer.py
          ├─ models.py                   sql_dump_service.py
          └─ avatar.py                   tasks.py (bg)
                │                        rag/
                │                        └─ pandas/, polars/
                │
           core/
           ├─ config.py       (all env vars in one place)
           └─ serializers.py  (shared dict helpers)
                │
          dependencies.py     (DB session, Redis, Chroma DI factories)
```

**Authentication flow:** The user signs in via Azure → the access token is stored in Redis under a `session_id` cookie → every protected endpoint calls `verify_session_and_get_user_id` from `services/session_service.py` to decode the token and extract the Azure OID.

---

## Project Structure

```
backend/
├── alembic/               # Database migration scripts
├── core/
│   ├── config.py          # Single source of truth for all environment variables
│   └── serializers.py     # Shared dict serialization helpers
├── dependencies.py        # FastAPI dependency injectors (DB, Redis, Chroma)
├── logging_config.py      # Structured logging setup
├── main.py                # App factory: CORS, routers, LLM init, Phoenix tracing
├── models/                # SQLAlchemy / SQLModel ORM models
│   ├── chat.py
│   ├── chat_file.py
│   ├── chat_message.py
│   └── favourite.py
├── routers/
│   ├── api/
│   │   ├── auth.py        # Azure sign-in, logout, /me, /profile-picture
│   │   ├── avatar.py      # User avatar upload
│   │   ├── chats.py       # Chat CRUD
│   │   ├── chat_inference.py  # AI chat endpoints (streaming, file upload)
│   │   ├── favourites.py  # Favourite chats
│   │   ├── messages.py    # Chat message history
│   │   └── models.py      # Available LLM model listing
│   └── route.py           # Mounts all /api/* sub-routers
├── services/
│   ├── chat_service.py       # LLM resolution, tool building, history building
│   ├── indexer.py            # Document/spreadsheet/SQL indexing into ChromaDB
│   ├── llm_agent.py          # ReActAgent factory
│   ├── llm_factory.py        # create_llm() / create_embed_model() — provider-agnostic
│   ├── memory.py             # LlamaIndex chat memory helpers
│   ├── rag/                  # Custom pandas/polars query engines (sandboxed eval)
│   │   ├── pandas/
│   │   └── polars/
│   ├── session_service.py    # decode_jwt, verify_session_*, check_property_belongs_to_user
│   ├── sql_dump_service.py   # SQL dump loading, MySQL→PG migration, DB utilities
│   ├── tasks.py              # Background task: process SQL dump → index
│   └── tools_initializer.py  # LlamaIndex tool factories (RAG, SQL, Pandas, URL, web)
├── tests/                 # pytest test suite
├── utils/
│   └── __init__.py        # Backward-compat re-exports from session_service
├── .env.example           # Template for all required environment variables
├── Dockerfile
├── alembic.ini
├── pytest.ini
└── requirements.txt
```

---

## Quickstart

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/) (recommended) _or_ pip
- Running instances of: PostgreSQL, Redis, ChromaDB
- An Azure Entra ID app registration (for auth)

### 1. Clone and enter the backend directory

```bash
cd backend
```

### 2. Create and activate a virtual environment

**With Poetry (recommended):**
```bash
poetry install
poetry shell
```

**With pip:**
```bash
python -m venv venv
source venv/bin/activate          # macOS/Linux
venv\Scripts\activate             # Windows
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values. See [Environment Variables](#environment-variables) for the full reference.

### 4. Run database migrations

```bash
poetry run alembic upgrade head
# or: alembic upgrade head  (if already in the virtualenv)
```

### 5. Start the server

```bash
poetry run hypercorn main:app --bind 0.0.0.0:4000 --reload
```

The API will be available at `http://localhost:4000`.  
Interactive API docs: `http://localhost:4000/docs`

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
# ── Azure Entra ID (required) ─────────────────────────────────────────────
CLIENT_ID=<your Azure app client ID>
CLIENT_SECRET=<your Azure app client secret>
TENANT_ID=<your Azure tenant ID>
REDIRECT_URI=http://localhost:4000/redirect
FRONTEND_URL=http://localhost:3000
ALLOWED_GROUPS_IDS=<comma-separated Azure group IDs allowed to access the app>

# ── App ───────────────────────────────────────────────────────────────────
PORT=4000
ENV=development          # development | production

# ── Redis (session storage) ───────────────────────────────────────────────
REDIS_HOST=localhost
REDIS_PORT=6379

# ── PostgreSQL (primary database) ────────────────────────────────────────
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=password
PG_COLLECTION=llama-rag

# ── MySQL (optional — only for SQL dump migration) ────────────────────────
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password

# ── ChromaDB (vector store) ───────────────────────────────────────────────
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=llama-rag

# ── LLM provider (choose one) ─────────────────────────────────────────────
LLM_PROVIDER=OLLAMA           # OLLAMA | IONOS | GOOGLE_GENAI

# Ollama (local)
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.1
OLLAMA_EMBED_MODEL=mxbai-embed-large

# IONOS Cloud Inference
IONOS_API_KEY=<your IONOS API key>
IONOS_BASE_URL=https://openai.inference.de-txl.ionos.com/v1

# Google GenAI
GOOGLE_API_KEY=<your Google API key>
GOOGLE_MODEL=gemini-2.0-flash

# ── Observability (optional) ──────────────────────────────────────────────
PHOENIX_API_KEY=<your Arize Phoenix API key>
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006
```

---

## Running the Server

```bash
# Development (auto-reload on file changes)
poetry run hypercorn main:app --bind 0.0.0.0:4000 --reload

# Production
poetry run hypercorn main:app --bind 0.0.0.0:${PORT}
```

---

## Database Migrations

The project uses **Alembic** for schema migrations.

```bash
# Apply all pending migrations
poetry run alembic upgrade head

# Create a new migration after changing a model
poetry run alembic revision --autogenerate -m "add column foo to chat"

# Review history
poetry run alembic history

# Roll back one revision
poetry run alembic downgrade -1
```

> **Note:** In development you can use `create_db_and_tables()` (from `dependencies.py`) for a quick table setup, but always use Alembic in production to keep schema changes versioned and reproducible.

---

## Running Tests

```bash
poetry run pytest
# or with coverage:
poetry run pytest --cov=backend
```

---

## Developer Guide

### Adding a new API endpoint

1. Create or extend a router file under `routers/api/`.
2. Add business logic to the appropriate service in `services/` — keep routers thin (validation + HTTP concern only).
3. Register the router in `routers/route.py` (or `main.py` for top-level routes like `/signin`).
4. Add tests in `tests/`.

### Adding a new LLM provider

1. Add the provider's env vars to `core/config.py`.
2. Add a new `elif provider_upper == "MY_PROVIDER":` branch in both `create_llm()` and `create_embed_model()` in `services/llm_factory.py`.
3. Update `LLM_PROVIDER` in your `.env`.

### Adding a new database model

1. Define the model class in `models/` (inherit from `Base` / `SQLModel`).
2. Generate and review the Alembic migration: `poetry run alembic revision --autogenerate -m "..."`.
3. Add serializer helpers to `core/serializers.py` if the model is returned by API responses.

### Session / auth pattern

Every protected endpoint should call one of these (imported from `services/session_service`):

```python
from backend.services.session_service import verify_session_and_get_user_id

user_id, session_id = verify_session_and_get_user_id(request, redis_client)
```

To also verify ownership of a resource (e.g., a `Chat`):

```python
from backend.services.session_service import check_property_belongs_to_user

belongs, user_id = check_property_belongs_to_user(request, redis_client, db_chat)
if not belongs:
    raise HTTPException(status_code=404, detail="Not found")
```

---

## Required Services

| Service | Purpose | Default port |
|---|---|---|
| PostgreSQL | Primary relational database | 5432 |
| Redis | Session storage | 6379 |
| ChromaDB | Vector store for RAG | 8000 |
| Ollama _(optional)_ | Local LLM & embedding inference | 11434 |
| Arize Phoenix _(optional)_ | LLM tracing & observability | 6006 |
| Azure Entra ID | Authentication & authorization | — |
| MySQL _(optional)_ | Only needed for SQL dump import/migration | 3306 |

> All services can be started locally via Docker Compose. See the root `docker-compose.yml` for reference.
