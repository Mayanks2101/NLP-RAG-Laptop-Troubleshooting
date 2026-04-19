# NLP RAG Project Flow and File-by-File Working

## 1. Project Purpose

This project is a Retrieval-Augmented Generation (RAG) system for laptop troubleshooting.

It does two main things:

1. Ingest troubleshooting text files into a vector database (Qdrant).
2. Answer user questions by retrieving relevant chunks and generating grounded responses with Groq LLM.

---

## 2. End-to-End Flow

### Flow A: Data Ingestion (offline or admin workflow)

1. Place `.txt` files in `data/raw/` (or pass a custom folder to the script).
2. Run `scripts/ingest_texts.py`.
3. The script loads file contents and metadata.
4. Texts are converted to embeddings via SentenceTransformers.
5. Embeddings are uploaded to Qdrant collection (`laptop_troubleshooting` by default).
6. System logs timing/statistics and prints final ingestion summary.

### Flow B: Question Answering (online API workflow)

1. Start API server with `uvicorn src.api.app:app --reload`.
2. Client sends a question to `POST /api/v1/query`.
3. Query is embedded and searched in Qdrant (top-k + threshold filter).
4. Retrieved contexts are merged into a prompt.
5. Prompt is sent to Groq LLM (`llama-3.1-8b-instant` by default).
6. API returns answer, chunk count, and processing time.

### Flow C: Debug and Operations

1. `POST /api/v1/query_debug` returns answer plus retrieved contexts.
2. `GET /api/v1/health` checks Qdrant and Groq availability.
3. `GET /api/v1/stats` returns collection/vector stats.
4. `DELETE /api/v1/reset` deletes the collection (with explicit confirmation).

---

## 3. Runtime Architecture

- FastAPI layer: request validation, routing, health/stats endpoints.
- Dependency layer: singleton/lazy-loaded shared clients (Qdrant, embedding model, Groq).
- Retrieval layer: semantic search in Qdrant.
- Generation layer: prompt building + LLM call + retry logic.
- Ingestion layer: file loading + embedding + indexing.
- Utility layer: config, logging, timing.

---

## 4. File-by-File Working

## Root files

### `docker-compose.yml`

- Currently empty.
- Intended to define multi-container setup (typically API + Qdrant).

### `Dockerfile`

- Currently empty.
- Intended to define container build for the API service.

### `README.md`

- Currently empty.
- Intended for setup, architecture, and usage documentation.

### `requirements.txt`

- Python dependencies for vector DB, embeddings, LLM client, FastAPI, config, logging, and utilities.
- Includes `qdrant-client`, `sentence-transformers`, `groq`, `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `python-dotenv`, `loguru`, `tqdm`, `numpy`, and `aiofiles`.

### `steps.txt`

- Manual runbook with commands for install, env setup, Qdrant startup, ingestion, and API testing.

---

## Data and logs

### `data/raw/`

- Source input directory for ingestion (`.txt` files expected).
- Controlled by `settings.DATA_DIR` default (`./data/raw`).

### `data/processed/`

- Processed artifacts/cache directory (`settings.PROCESSED_DIR`).
- Currently contains preprocessed troubleshooting chunks.

### `data/processed/mac.json_4_powerbook_g3_wallstreet_hard_drive_replacement_step_1.txt`

### `data/processed/mac.json_4_powerbook_g3_wallstreet_hard_drive_replacement_step_2.txt`

### `data/processed/mac.json_4_powerbook_g3_wallstreet_hard_drive_replacement_step_3.txt`

### `data/processed/mac.json_4_powerbook_g3_wallstreet_hard_drive_replacement_step_4.txt`

### `data/processed/mac.json_4_powerbook_g3_wallstreet_hard_drive_replacement_step_5.txt`

- Example knowledge chunks (step-wise docs).
- These are the type of files the system embeds and indexes.

### `logs/`

- Target directory for log files from API and scripts.
- Created automatically by config/logger when missing.

---

## Scripts

### `scripts/ingest_texts.py`

- Standalone ingestion orchestrator.
- Parses CLI args (`--data-dir`, `--batch-size`, `--upload-batch`, `--dry-run`).
- Executes 3 phases: load files, generate embeddings, upload vectors.
- Produces pipeline summary and handles interrupts/fatal errors.

### `scripts/test_query.py`

- Quick end-to-end smoke test for RAG.
- Initializes dependencies, builds Retriever + LLM client + QA pipeline.
- Runs fixed sample troubleshooting questions and prints results.

---

## API package: `src/api/`

### `src/api/__init__.py`

- Empty package marker.

### `src/api/app.py`

- FastAPI application entry point.
- Configures logger, app metadata, CORS, and request-logging middleware.
- Registers lifespan startup/shutdown hooks.
- Preloads expensive resources on startup (embedding model, Qdrant, Groq).
- Mounts router from `routes.py`.
- Exposes root endpoints `/` and `/health`.

### `src/api/dependencies.py`

- Dependency injection and shared resource management.
- Lazy singleton creation for embedding model, Qdrant client, and Groq client.
- Provides FastAPI dependency wrappers (`Depends(...)` targets).
- Includes health helper checks for Qdrant and Groq.

### `src/api/models.py`

- Pydantic request/response models used by API endpoints.
- Enforces validation constraints (length, ranges, required fields).
- Defines schemas for query, ingest, health, stats, reset, debug, and error responses.

### `src/api/routes.py`

- Main API endpoint definitions under `/api/v1`.
- `POST /ingest`: single file upload and indexing.
- `POST /query`: normal RAG response.
- `POST /query_debug`: RAG response with retrieved contexts.
- `GET /health`: service/component health.
- `GET /stats`: Qdrant collection statistics.
- `DELETE /reset`: dangerous collection delete with confirmation.
- Includes catch-all exception handler returning standardized JSON errors.

---

## Generation package: `src/generation/`

### `src/generation/__init__.py`

- Package exports for generation components.

### `src/generation/prompt_templates.py`

- Central prompt definitions.
- Contains strict `SYSTEM_PROMPT`, `FALLBACK_RESPONSE`, and `build_prompt(...)` to inject retrieved contexts.

### `src/generation/llm_client.py`

- Groq chat-completion wrapper.
- Sends system/user prompts to configured model.
- Includes retry logic for rate limits and API failures.

### `src/generation/qa_chain.py`

- End-to-end QA orchestrator class (`QAPipeline`).
- Steps: retrieve contexts -> fallback if empty -> build prompt -> generate answer.
- Returns answer + contexts + chunk count + processing time.

---

## Ingestion package: `src/ingestion/`

### `src/ingestion/__init__.py`

- Package exports for ingestion components.

### `src/ingestion/text_loader.py`

- Generator-based `.txt` loader.
- Recursively scans directory, reads UTF-8 content, skips empty/bad files.
- Yields `(filename, text, metadata)` for memory-efficient processing.

### `src/ingestion/embedder.py`

- Embedding generation wrapper (`TextEmbedder`).
- Lazy-loads sentence-transformer model.
- Encodes text in batches with normalized embeddings for cosine search.

### `src/ingestion/indexer.py`

- Qdrant indexing wrapper (`VectorIndexer`).
- Connects to Qdrant, ensures collection exists, batch-upserts points.
- Handles upload failures per batch without stopping all progress.

---

## Retrieval package: `src/retrieval/`

### `src/retrieval/__init__.py`

- Package export for retriever class.

### `src/retrieval/retriever.py`

- Semantic retrieval logic (`Retriever`).
- Encodes user query, performs vector search in Qdrant, returns structured contexts with scores.
- Applies configurable `TOP_K` and `SCORE_THRESHOLD`.

---

## Utility package: `src/utils/`

### `src/utils/__init__.py`

- Empty package marker.

### `src/utils/config.py`

- Centralized settings using `pydantic-settings`.
- Loads env variables (including `.env`), validates types/ranges, creates key directories.
- Holds defaults for model names, DB host/port, retrieval and LLM settings, and log config.

### `src/utils/logger.py`

- Loguru configuration helper.
- Creates console and rotating file handlers.
- Provides `setup_logger(...)` and `get_logger(...)`.

### `src/utils/timer.py`

- Timing helpers.
- `@timing` decorator for function duration logging.
- `timer(...)` context manager for scoped timing.
- `format_duration(...)` for human-readable elapsed times.

---

## Tests

### `tests/`

- Present but currently no test files.
- Good place to add unit tests for retriever, prompt builder, and API endpoints.

---

## 5. Key Configuration and Defaults

- Embedding model: `BAAI/bge-base-en-v1.5`
- LLM model: `llama-3.1-8b-instant`
- Vector DB: Qdrant at `localhost:6333`
- Collection: `laptop_troubleshooting`
- Retrieval defaults: `TOP_K=5`, `SCORE_THRESHOLD=0.7`

---

## 6. Practical Execution Order

1. Install dependencies from `requirements.txt`.
2. Create and fill `.env` (must include `GROQ_API_KEY`).
3. Start Qdrant.
4. Run `scripts/ingest_texts.py` to populate vectors.
5. Start API (`uvicorn src.api.app:app --reload`).
6. Test `POST /api/v1/query` via Swagger (`/docs`) or `scripts/test_query.py`.

---

## 7. Notes on Current Repository State

- `README.md`, `Dockerfile`, and `docker-compose.yml` are currently empty placeholders.
- Core business logic is implemented in `src/` and operational scripts are in `scripts/`.
- The architecture is already modular and ready for adding tests and deployment files.
