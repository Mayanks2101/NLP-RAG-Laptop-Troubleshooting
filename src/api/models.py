# src/api/models.py
"""
Pydantic models for API request/response validation.

This module defines the data structures for our API endpoints.
Pydantic automatically:
- Validates incoming request data
- Converts types (e.g., string "5" → integer 5)
- Generates OpenAPI documentation (shown at /docs)
- Serializes responses to JSON

Beginner tip: Think of these as "contracts" - they define exactly
what data the API expects to receive and send back.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# === Request Models (What clients send TO our API) ===

class QueryRequest(BaseModel):
    """
    Request body for POST /query endpoint.

    Example JSON:
    {
        "question": "My laptop won't turn on, what should I check?"
    }
    """
    question: str = Field(
        ...,  # ... means this field is required
        min_length=1,
        max_length=500,
        description="The user's troubleshooting question",
        examples=["My laptop battery is not charging", "Screen is black but power light is on"]
    )

    @field_validator("question")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing spaces from question"""
        return v.strip()


class AdvancedQueryRequest(BaseModel):
    """
    Request body for POST /advanced_query endpoint (multi-query + reranking).
    Optionally includes a session_id for conversation memory.

    Example JSON:
    {
        "question": "My screen flickers when I move the lid",
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The user's troubleshooting question",
        examples=["My laptop battery is not charging", "Screen flickers when I open the lid"]
    )
    session_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional session UUID for multi-turn conversation memory. "
            "Omit (or send null) for stateless single-turn queries. "
            "Generate a UUID4 on the client and reuse it across turns."
        ),
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )

    @field_validator("question")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class IngestRequest(BaseModel):
    """
    Request body for POST /ingest endpoint.
    
    Note: File uploads are handled via FastAPI's UploadFile,
    but we use this model for metadata if needed in future.
    """
    filename: Optional[str] = Field(
        default=None,
        description="Optional: custom name for the ingested file"
    )
    overwrite: bool = Field(
        default=False,
        description="If True, replace existing chunk with same filename"
    )


class ResetRequest(BaseModel):
    """
    Request body for DELETE /reset endpoint.
    
    Added confirmation field to prevent accidental database deletion.
    """
    confirm: bool = Field(
        ...,
        description="Must be True to confirm database reset (safety measure)"
    )
    
    @field_validator("confirm")
    @classmethod
    def must_be_true(cls, v: bool) -> bool:
        """Ensure user explicitly confirms the dangerous action"""
        if not v:
            raise ValueError("Must set confirm=true to reset database")
        return v


# === Response Models (What our API sends BACK to clients) ===

class QueryResponse(BaseModel):
    """
    Response for POST /query endpoint.
    
    Example:
    {
        "question": "My laptop battery is not charging",
        "answer": "1. Check AC adapter connection...\n2. Reseat battery...",
        "processing_time_seconds": 2.34,
        "chunks_used": 3
    }
    """
    question: str = Field(description="Echo of the user's question")
    answer: str = Field(description="LLM-generated troubleshooting answer")
    processing_time_seconds: float = Field(
        description="Total time to process the request (retrieval + generation)",
        ge=0.0  # Must be >= 0
    )
    chunks_used: int = Field(
        default=0,
        description="Number of knowledge chunks used to generate answer"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this response was generated"
    )


class IngestResponse(BaseModel):
    """
    Response for POST /ingest endpoint.
    
    Example:
    {
        "status": "success",
        "filename": "dell_battery_guide.txt",
        "chunks_created": 1,
        "vectors_added": 1,
        "processing_time_seconds": 1.23,
        "message": "File ingested successfully"
    }
    """
    status: str = Field(
        description="Operation status: 'success' or 'error'"
    )
    filename: str = Field(description="Name of the processed file")
    chunks_created: int = Field(description="Number of chunks created (always 1 for .txt files)")
    vectors_added: int = Field(description="Number of vectors added to Qdrant")
    processing_time_seconds: float = Field(description="Total ingestion time")
    message: Optional[str] = Field(default=None, description="Additional info or error message")


class HealthResponse(BaseModel):
    """
    Response for GET /health endpoint.
    
    Example:
    {
        "status": "healthy",
        "components": {
            "qdrant": {"status": "connected", "latency_ms": 12},
            "groq_api": {"status": "available"},
            "embedding_model": {"status": "loaded"}
        },
        "timestamp": "2024-01-15T10:30:00"
    }
    """
    status: str = Field(
        description="Overall system health: 'healthy', 'degraded', or 'unhealthy'"
    )
    components: dict = Field(
        description="Status of each critical component"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When health check was performed"
    )


class StatsResponse(BaseModel):
    """
    Response for GET /stats endpoint.
    
    Example:
    {
        "collection_name": "laptop_troubleshooting",
        "total_vectors": 1250,
        "total_files": 1250,
        "vector_dimension": 768,
        "last_updated": "2024-01-15T09:00:00"
    }
    """
    collection_name: str
    total_vectors: int = Field(description="Total vectors in Qdrant collection")
    total_files: int = Field(description="Number of .txt files indexed (1 file = 1 vector)")
    vector_dimension: int = Field(description="Size of each embedding vector")
    last_updated: Optional[datetime] = Field(
        default=None,
        description="When the collection was last modified"
    )


class ResetResponse(BaseModel):
    """
    Response for DELETE /reset endpoint.

    Example:
    {
        "status": "success",
        "message": "Collection 'laptop_troubleshooting' deleted",
        "vectors_deleted": 1250
    }
    """
    status: str
    message: str
    vectors_deleted: Optional[int] = Field(default=None)


class AdvancedQueryResponse(BaseModel):
    """
    Response for POST /advanced_query endpoint.

    Includes everything QueryResponse has, plus:
    - generated_queries: the N alternative queries the LLM created
    - retrieved_contexts: the final reranked chunks (with reranker_score)
    - session_id: echoed back so the client can correlate with its state
    - turn_number: which turn in this conversation this is

    Example:
    {
        "question": "My screen flickers",
        "answer": "1. Check the display cable...",
        "generated_queries": ["screen flickering loose cable", "display flicker gpu driver"],
        "chunks_used": 3,
        "processing_time_seconds": 3.21,
        "session_id": "550e8400...",
        "turn_number": 2
    }
    """
    question: str = Field(description="Echo of the user's question")
    answer: str = Field(description="LLM-generated troubleshooting answer")
    generated_queries: List[str] = Field(
        default_factory=list,
        description="Alternative queries generated from the original question"
    )
    chunks_used: int = Field(
        default=0,
        description="Number of reranked knowledge chunks fed to the LLM"
    )
    processing_time_seconds: float = Field(
        description="Total pipeline latency (query gen + retrieval + rerank + LLM)",
        ge=0.0
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID echoed from request (null for stateless queries)"
    )
    turn_number: int = Field(
        default=1,
        description="Which turn in this conversation (1 = first turn)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When this response was generated"
    )


class AdvancedQueryDebugResponse(AdvancedQueryResponse):
    """
    Extended response for POST /advanced_query_debug — includes raw chunks.
    """
    retrieved_contexts: List[dict] = Field(
        default_factory=list,
        description="Reranked chunks with text, source, bi-encoder score, and reranker_score"
    )


class ClearHistoryResponse(BaseModel):
    """
    Response for DELETE /session/{session_id} endpoint.
    """
    status: str = Field(description="'cleared' or 'not_found'")
    session_id: str
    message: str


class QueryDebugResponse(QueryResponse):
    """
    Extended response for POST /query_debug endpoint.
    Includes retrieved contexts for debugging/inspection.
    
    Inherits all fields from QueryResponse plus:
    """
    retrieved_contexts: List[dict] = Field(
        default_factory=list,
        description="List of chunks used to generate the answer"
    )
    """
    Each context item looks like:
    {
        "text": "## Battery Issues\n1. Check AC adapter...",
        "score": 0.89,
        "source": "dell_battery_guide.txt"
    }
    """


# === Error Response Model (Standardized error format) ===

class ErrorResponse(BaseModel):
    """
    Standard error response for all endpoints.
    
    Example:
    {
        "error": "ValidationError",
        "message": "Question cannot be empty",
        "details": {...}  # Optional additional info
    }
    """
    error: str = Field(description="Error type/class name")
    message: str = Field(description="Human-readable error message")
    details: Optional[dict] = Field(default=None, description="Additional error context")