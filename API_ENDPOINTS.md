# API Endpoints — NLP RAG Laptop Troubleshooting

This document lists the API endpoints exposed under `/api/v1`, the expected request format, and example (dummy) responses. Use this as a quick reference for integrating with the API or writing tests.

Base URL: http://localhost:8000/api/v1

---

## POST /ingest
Description: Upload a single `.txt` file to index it into Qdrant.

Request (multipart/form-data):
- file: The `.txt` file to upload (required)
- Optional form fields (handled by `IngestRequest`):
  - filename (string)
  - overwrite (boolean)

Example curl:
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -F "file=@path/to/manual.txt"
```

Dummy Response (200 OK, IngestResponse):
```json
{
  "status": "success",
  "filename": "manual.txt",
  "chunks_created": 1,
  "vectors_added": 1,
  "processing_time_seconds": 1.23,
  "message": "File indexed successfully"
}
```

Error (400/500): returns FastAPI error format or ErrorResponse for standardized errors.

---

## POST /query
Description: Stateless question-answering endpoint that runs retrieval + LLM generation.

Request (application/json) — body matches `QueryRequest`:
```json
{
  "question": "My laptop won't turn on; what should I check?"
}
```

Dummy Response (200 OK, QueryResponse):
```json
{
  "question": "My laptop won't turn on; what should I check?",
  "answer": "1. Verify AC adapter and cable are connected.\n2. Try removing the battery and starting with AC only.\n3. Check for beep codes or LED indicators.",
  "processing_time_seconds": 2.34,
  "chunks_used": 3,
  "timestamp": "2026-04-29T12:00:00"
}
```

On internal failure the endpoint returns a fallback QueryResponse with a generic message.

---

## POST /query_debug
Description: Like `/query` but returns retrieved contexts (for debugging and inspection).

Request body: same as `/query`.

Dummy Response (200 OK, QueryDebugResponse):
```json
{
  "question": "How do I replace the hard drive on Acer Aspire 5100?",
  "answer": "1. Power down and disconnect battery.\n2. Remove access panel.\n3. Unscrew drive bracket and swap drive.",
  "processing_time_seconds": 3.21,
  "chunks_used": 2,
  "retrieved_contexts": [
    {
      "text": "1. Remove battery...\n2. Unscrew two screws holding HDD bracket...",
      "score": 0.92,
      "source": "Acer Aspire 5100 Hard Drive Replacement.txt"
    },
    {
      "text": "HDD replacement steps: remove bezel, slide out the drive...",
      "score": 0.88,
      "source": "Acer Aspire 5100 Hard Drive Replacement.txt"
    }
  ],
  "timestamp": "2026-04-29T12:00:00"
}
```

---

## GET /health
Description: Health check that returns status of key components (Qdrant, Groq API, embedding model).

Request: none

Dummy Response (200 OK, HealthResponse):
```json
{
  "status": "healthy",
  "components": {
    "qdrant": {"status": "connected", "latency_ms": 12},
    "groq_api": {"status": "available"},
    "embedding_model": {"status": "loaded", "model": "BAAI/bge-base-en-v1.5"}
  },
  "timestamp": "2026-04-29T12:00:00"
}
```

---

## GET /stats
Description: Returns collection statistics (count, vector dimension).

Request: none

Dummy Response (200 OK, StatsResponse):
```json
{
  "collection_name": "laptop_troubleshooting",
  "total_vectors": 1234,
  "total_files": 1234,
  "vector_dimension": 1536,
  "last_updated": "2026-04-29T11:50:00"
}
```

---

## DELETE /reset
Description: Delete the Qdrant collection. Must include `confirm: true` in the request body to proceed.

Request (application/json) — ResetRequest:
```json
{
  "confirm": true
}
```

Dummy Response (200 OK, ResetResponse):
```json
{
  "status": "success",
  "message": "Collection 'laptop_troubleshooting' deleted successfully",
  "vectors_deleted": 1234
}
```

Error (400): If `confirm` is not true, returns a validation error.

---

## POST /advanced_query
Description: Advanced multi-query + reranking pipeline supporting optional conversation memory via `session_id`.

Request (application/json) — AdvancedQueryRequest:
```json
{
  "question": "My laptop screen flickers when I move the lid",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

Dummy Response (200 OK, AdvancedQueryResponse):
```json
{
  "question": "My laptop screen flickers when I move the lid",
  "answer": "1. Check display cable connection at the hinge.\n2. Update GPU/display drivers.\n3. Inspect for loose hinge or damaged flex cable.",
  "generated_queries": [
    "screen flickers when lid moves",
    "display flicker hinge cable"
  ],
  "chunks_used": 4,
  "processing_time_seconds": 4.56,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "turn_number": 2,
  "timestamp": "2026-04-29T12:00:00"
}
```

---

## POST /advanced_query_debug
Description: Same as `/advanced_query` but includes raw reranked chunks in `retrieved_contexts` for inspection. Does not save memory.

Request body: same as `/advanced_query`.

Dummy Response (200 OK, AdvancedQueryDebugResponse):
```json
{
  "question": "My laptop screen flickers when I move the lid",
  "answer": "...",
  "generated_queries": ["screen flicker hinge","display cable loose"],
  "chunks_used": 4,
  "processing_time_seconds": 4.56,
  "session_id": null,
  "turn_number": 1,
  "retrieved_contexts": [
    {"text": "...", "source": "file.txt", "bi_score": 0.91, "reranker_score": 0.83}
  ],
  "timestamp": "2026-04-29T12:00:00"
}
```

---

## DELETE /session/{session_id}
Description: Clear conversation history for a session ID.

Request: none (session_id path parameter)

Dummy Response (200 OK, ClearHistoryResponse):
```json
{
  "status": "cleared",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Conversation history for session '550e8400-e29b-41d4-a716-446655440000' has been cleared."
}
```

---

## Error format
All standardized errors use the `ErrorResponse` model when returned intentionally by the application. Example:
```json
{
  "error": "ValidationError",
  "message": "Question cannot be empty",
  "details": {"field": "question"}
}
```

---

If you'd like, I can also:
- Generate a Postman collection from these endpoints
- Add example request/response tests in `tests/` folder
- Add these endpoints to `README.md` instead of a separate file

Tell me which of those you'd like next.