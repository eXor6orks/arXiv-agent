# arXiv-agent

Fetches the latest arXiv papers, chunks them, embeds them, and indexes them in Qdrant to enable semantic search. Exposed via an HTTP API designed to be called by an external chatbot.

## Architecture

```
core/          Business logic (arXiv, text cleaning, chunking, embeddings, Qdrant, auth, DB)
config/        Default configuration values + access to runtime config (SQLite)
api/           FastAPI application (auth, search, ingest, config, users)
scripts/       Operational scripts (Docker bootstrap, entrypoint, smoke test)
main.py        CLI (ingestion, search, user management)
```

- `core/` only contains reusable functions/classes, never `print`/program-level logic.
- `main.py` and `api/` are the two entry points that call into `core/`.
- Config editable from the API (`ARXIV_RESEARCH_QUERY`, `EMBEDDING_MODEL`, `COLLECTION`, ...) is stored in SQLite (key/value), falling back to the defaults in `config/config.py` when absent.

## Requirements

- Docker + Docker Compose
- A reachable [Ollama](https://ollama.com) server, with the embedding model pulled (`ollama pull nomic-embed-text`)

## Getting started

1. Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `JWT_SECRET_KEY` | Signing key for JWT tokens. Generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_USERNAME` | Username of the admin account created on first startup |
| `ADMIN_PASSWORD` | Password of the admin account created on first startup |

2. Start the stack:

```bash
docker compose up -d --build
```

On first startup, the `app` container automatically initializes the SQLite database (default config + admin account). This is idempotent: restarting won't create duplicates.

3. Verify everything works:

```bash
python scripts/test_api.py --password <ADMIN_PASSWORD>
```

### Data persistence

Data doesn't live in managed Docker volumes but directly inside the project folder:

- `data/app.db` — runtime config + users (SQLite)
- `qdrant_storage/` — indexed vectors (Qdrant)

These folders are git-ignored (`.gitignore`). To migrate to another machine, just copy them. To start fresh, delete them and re-run `docker compose up -d --build`.

## API

All routes except `/auth/login` require an `Authorization: Bearer <token>` header. `/config`, `/ingest`, and `/users` additionally require an **admin** account.

| Method | Route | Required role | Description |
|---|---|---|---|
| POST | `/auth/login` | — | Authenticates a user, returns a JWT token (valid 12h) |
| POST | `/search` | user | Semantic search over indexed chunks. Body: `{"question": str, "top_k": int}` |
| POST | `/ingest` | admin | Triggers a background arXiv ingestion. Body: `{"max_results": int}` |
| GET | `/config` | admin | Lists current runtime parameters |
| PUT | `/config/{key}` | admin | Updates a parameter. Body: `{"value": ...}` |
| GET | `/users` | admin | Lists users |
| POST | `/users` | admin | Creates a user. Body: `{"username": str, "password": str, "is_admin": bool}` |
| DELETE | `/users/{username}` | admin | Deletes a user |

Interactive documentation (Swagger) available at `/docs` once the API is running.

### Configuration parameters

| Key | Default | Description |
|---|---|---|
| `ARXIV_RESEARCH_QUERY` | `["cat:cs.AI"]` | List of arXiv queries (combined with OR) used for ingestion |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Ollama model used for embedding |
| `EMBEDDING_DIMENSION` | `{"nomic-embed-text": 768}` | Vector dimension per model (must contain an entry for `EMBEDDING_MODEL`) |
| `COLLECTION` | `documentation` | Qdrant collection name |
| `DOWNLOAD_PDF` | `false` | (reserved) |
| `ENVIRONMENT` | `0` | (reserved) |

## CLI (`main.py`)

```bash
python main.py ingest --max-results 20          # fetches and indexes arXiv papers
python main.py search "your question" --top-k 5 # searches the vector database
python main.py create-user <username> <password> [--admin]   # creates a user
```

## Local development (without Docker)

```bash
pip install -r requirements.txt
cp .env.example .env
python main.py create-user admin <password> --admin
uvicorn api.main:app --reload
```

Requires Qdrant and Ollama reachable locally (`localhost:6333` and `localhost:11434` by default — overridable via `QDRANT_HOST`/`QDRANT_PORT`/`OLLAMA_HOST`).

## Known limitations

See the "Known issues" section of the [CHANGELOG](CHANGELOG.md).
