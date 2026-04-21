# src/api/dependencies.py
"""
Dependency injection module for FastAPI.

This module manages shared resources that are expensive to create:
- Qdrant client (database connection)
- Embedding model (loads ~500MB into memory)
- Groq LLM client
- QA chain (combines retrieval + generation)

Key pattern: Singleton with lazy initialization
- Resources are created ONCE on first use
- Then reused for all subsequent requests
- Saves memory and startup time

Beginner tip: Think of dependencies as "shared tools" that
multiple API endpoints can borrow without each creating their own.
"""

from functools import lru_cache
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from groq import Groq

from src.utils.config import settings
from src.utils.logger import get_logger
from src.retrieval.reranker import Reranker

logger = get_logger(__name__)


# === Global caches for expensive resources ===
# These are module-level variables that persist across requests

_embedding_model: Optional[SentenceTransformer] = None
_qdrant_client: Optional[QdrantClient] = None
_groq_client: Optional[Groq] = None
_reranker: Optional[Reranker] = None


def get_embedding_model() -> SentenceTransformer:
    """
    Get or create the embedding model instance.
    
    Uses lazy initialization: model is loaded only on first call.
    Subsequent calls return the cached instance.
    
    Returns:
        SentenceTransformer model for BAAI/bge-base-en-v1.5
    """
    global _embedding_model
    
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        # Load model from HuggingFace
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("✓ Embedding model loaded successfully")
    
    return _embedding_model


def get_qdrant_client() -> QdrantClient:
    """
    Get or create the Qdrant database client.
    
    Connects to Qdrant running locally via Docker.
    Reuses connection across requests for efficiency.
    
    Returns:
        QdrantClient instance connected to our collection
    """
    global _qdrant_client
    
    if _qdrant_client is None:
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        _qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            prefer_grpc=False  # Use HTTP for easier debugging
        )
        # Test connection
        _qdrant_client.get_collections()
        logger.info("✓ Connected to Qdrant successfully")
    
    return _qdrant_client


def get_groq_client() -> Groq:
    """
    Get or create the Groq API client for LLM calls.
    
    Initializes with API key from environment.
    
    Returns:
        Groq client instance ready to call Llama-3.1-8b
    """
    global _groq_client
    
    if _groq_client is None:
        logger.info("Initializing Groq LLM client")
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("✓ Groq client initialized")
    
    return _groq_client


# === FastAPI Dependency Functions ===
# These are used with Depends() in route handlers

def get_embedding_model_dep() -> SentenceTransformer:
    """FastAPI dependency wrapper for embedding model"""
    return get_embedding_model()


def get_qdrant_client_dep() -> QdrantClient:
    """FastAPI dependency wrapper for Qdrant client"""
    return get_qdrant_client()


def get_groq_client_dep() -> Groq:
    """FastAPI dependency wrapper for Groq client"""
    return get_groq_client()


def get_reranker() -> Reranker:
    """
    Get or create the Cross-Encoder reranker instance.

    Loaded lazily on first request to /advanced_query so that the server
    starts fast and the model is only loaded if the advanced endpoint is used.

    Returns:
        Reranker instance backed by BAAI/bge-reranker-base
    """
    global _reranker
    if _reranker is None:
        logger.info(f"Loading reranker model: {settings.RERANKER_MODEL}")
        _reranker = Reranker(model_name=settings.RERANKER_MODEL)
        logger.info("✓ Reranker loaded successfully")
    return _reranker


def get_reranker_dep() -> Reranker:
    """FastAPI dependency wrapper for the Cross-Encoder reranker"""
    return get_reranker()


def check_qdrant_health(client: QdrantClient = Depends(get_qdrant_client_dep)) -> dict:
    """
    Check if Qdrant is reachable and collection exists.
    
    Returns dict with status info for health endpoint.
    """
    try:
        start_time = __import__('time').time()
        collections = client.get_collections()
        latency_ms = (__import__('time').time() - start_time) * 1000
        
        # Check if our collection exists
        collection_exists = any(
            c.name == settings.COLLECTION_NAME 
            for c in collections.collections
        )
        
        return {
            "status": "connected",
            "latency_ms": round(latency_ms, 2),
            "collection_exists": collection_exists
        }
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def check_groq_health(client: Groq = Depends(get_groq_client_dep)) -> dict:
    """
    Check if Groq API is reachable.
    
    Makes a minimal test call to verify API key and connectivity.
    """
    try:
        # Make a tiny test request (1 token) to check connectivity
        start_time = __import__('time').time()
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": "."}],
            max_tokens=1,
            temperature=0
        )
        latency_ms = (__import__('time').time() - start_time) * 1000
        
        return {
            "status": "available",
            "latency_ms": round(latency_ms, 2),
            "model": settings.LLM_MODEL
        }
    except Exception as e:
        logger.error(f"Groq health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }