# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-12

### Added

- arXiv fetching: retrieves the N most recent papers for a given subject/category.
- Qdrant storage: chunks are embedded and stored in a vector database (cosine distance).
- Search: vector similarity search over indexed chunks.
- API (FastAPI):
    - Trigger ingestion (`POST /ingest`)
    - Search the vector database (`POST /search`)
    - Read/update runtime parameters, stored in SQLite (`GET/PUT /config`)
    - User management with admin/standard roles (`GET/POST/DELETE /users`)
    - JWT authentication (`POST /auth/login`)
- Docker: containerized app + Qdrant via docker-compose, with persistent local storage (`data/`, `qdrant_storage/`) and an idempotent bootstrap script that seeds default config and the admin account on first start.

### Known issues

- `clean_appendix` (core/clean_text.py) never matches real "Appendix" headings (case-sensitive, requires `appendix[`/`appendix]`) — appendix content is never stripped before indexing.
- `retirer_html` (core/clean_text.py) strips everything between any `<` and the next `>`, which also deletes real text between two math comparisons (e.g. `n < N ... f(x) > 0`).
- `load_paper` (core/ingest.py) only falls back to PDF on `RuntimeError`; other exceptions from the LaTeX path (HTTP errors, network errors, corrupt archives) abort the whole ingestion batch instead of skipping that one paper.
- File handles opened in `core/latex.py` (`_resoudre_includes`, `_trouver_fichier_principal`) are never closed, leaking file descriptors on papers with many `\input`/`\include` files.
- `_extraire_argument` (core/latex.py) assumes `\section{...}` with no space before the brace; `\section {Title}` produces a corrupted title.
- `core/search.py` caches its Qdrant/Embedder clients for the process lifetime, so changing `COLLECTION` or `EMBEDDING_MODEL` via `PUT /config` has no effect on `/search` until the app restarts (while `/ingest` picks the change up immediately) — a search/ingest split-brain.
- No validation on config values written via `PUT /config/{key}`: an invalid `EMBEDDING_MODEL` or a non-list `ARXIV_RESEARCH_QUERY` breaks `/search` and `/ingest` until manually fixed in the database.
- `POST /users` has a check-then-create race: two concurrent requests for the same username can both pass validation and the second crashes with an unhandled `sqlite3.IntegrityError` instead of a clean 409.
- `core/auth.py` password hashing has no length guard; bcrypt raises an unhandled `ValueError` for passwords over 72 bytes.

### Fixed

### Changed

### Removed

## [Unreleased]

## [0.2.0] - 2027-01-

### Added

- Batch embedding
- Per-chunk weighting
- Re-ranking
- Hybrid search (dense + sparse/BM25 vectors in Qdrant)
- Metadata filtering exposed on `/search` (category, date, author)
- Structure-aware chunking (split on section boundaries instead of a fixed word count)
- Structured logging (replace `print()` with `logging`)
- `/ingest` status endpoint (progress, success/failure, papers processed)
- Rate limiting on `/search` and `/auth/login`
- Deduplication across paper versions (same `arxiv_id`, different version)
- Automated tests (pytest)
- CI pipeline (lint, tests, Docker build) on push