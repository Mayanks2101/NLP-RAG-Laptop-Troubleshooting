# src/api/routes.py

import time
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from groq import Groq

from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.timer import timing, timer, format_duration
from src.api.models import (
    QueryRequest, QueryResponse, IngestRequest, IngestResponse,
    HealthResponse, StatsResponse, ResetRequest, ResetResponse,
    QueryDebugResponse, ErrorResponse
)
from src.api.dependencies import (
    get_embedding_model_dep, get_qdrant_client_dep, get_groq_client_dep,
    check_qdrant_health, check_groq_health
)

from src.retrieval.retriever import Retriever
from src.generation.llm_client import GroqLLMClient
from src.generation.qa_chain import QAPipeline
from src.generation.prompt_templates import FALLBACK_RESPONSE

from src.ingestion.embedder import TextEmbedder
from src.ingestion.indexer import VectorIndexer

router = APIRouter(prefix="/api/v1")
logger = get_logger(__name__)


@router.post("/ingest", response_model=IngestResponse)
@timing
async def ingest_file(
    file: UploadFile = File(...),
    request: IngestRequest = Depends(),
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dep),
    embedding_model: SentenceTransformer = Depends(get_embedding_model_dep)
):
    start_time = time.time()
    logger.info(f"📥 Starting API ingestion: {file.filename}")

    try:
        content = await file.read()
        text = content.decode("utf-8").strip()

        if not text:
            raise ValueError("Uploaded file is empty")

        with timer("Generating embedding"):
            embedder = TextEmbedder()
            embedder.model = embedding_model
            vector = embedder.encode_texts([text])[0]

        with timer("Uploading to Qdrant"):
            indexer = VectorIndexer()
            indexer.client = qdrant_client

            vector_dim = len(vector)
            indexer.ensure_collection(vector_size=vector_dim)

            # Use deterministic UUID from filename so re-uploading replaces the same vector
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, file.filename))

            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "text": text,
                    "source": file.filename,
                    "ingested_at": time.time(),
                    "char_count": len(text)
                }
            )

            qdrant_client.upsert(
                collection_name=settings.COLLECTION_NAME,
                points=[point]
            )

        elapsed = time.time() - start_time
        logger.info(f"✅ Ingested '{file.filename}' in {elapsed:.2f}s")

        return IngestResponse(
            status="success",
            filename=file.filename,
            chunks_created=1,
            vectors_added=1,
            processing_time_seconds=round(elapsed, 2),
            message="File indexed successfully"
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"❌ Ingestion failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")


@router.post("/query", response_model=QueryResponse)
@timing
async def query_endpoint(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dep),
    embedding_model: SentenceTransformer = Depends(get_embedding_model_dep),
    groq_client: Groq = Depends(get_groq_client_dep)
):
    logger.info(f"🎯 Query received: '{request.question[:60]}...'")

    try:
        retriever = Retriever(qdrant_client, embedding_model)
        llm_client = GroqLLMClient(groq_client)
        pipeline = QAPipeline(retriever, llm_client)

        result = pipeline.process(request.question)

        return QueryResponse(
            question=request.question,
            answer=result["answer"],
            processing_time_seconds=result["processing_time_seconds"],
            chunks_used=result["chunks_used"]
        )

    except Exception as e:
        logger.error(f"❌ Query processing failed: {e}")
        return QueryResponse(
            question=request.question,
            answer="I'm experiencing technical difficulties. Please try again.",
            processing_time_seconds=0.0,
            chunks_used=0
        )


@router.post("/query_debug", response_model=QueryDebugResponse)
@timing
async def query_debug_endpoint(
    request: QueryRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dep),
    embedding_model: SentenceTransformer = Depends(get_embedding_model_dep),
    groq_client: Groq = Depends(get_groq_client_dep)
):
    try:
        retriever = Retriever(qdrant_client, embedding_model)
        llm_client = GroqLLMClient(groq_client)
        pipeline = QAPipeline(retriever, llm_client)

        result = pipeline.process(request.question)

        return QueryDebugResponse(
            question=request.question,
            answer=result["answer"],
            processing_time_seconds=result["processing_time_seconds"],
            chunks_used=result["chunks_used"],
            retrieved_contexts=result["contexts"]
        )

    except Exception as e:
        logger.error(f"❌ Debug query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Debug query error: {str(e)}")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dep),
    groq_client: Groq = Depends(get_groq_client_dep)
):
    logger.debug("🏥 Running health check")

    qdrant_status = check_qdrant_health(qdrant_client)
    groq_status = check_groq_health(groq_client)

    if qdrant_status["status"] == "connected" and groq_status["status"] == "available":
        overall_status = "healthy"
    elif qdrant_status["status"] == "error" or groq_status["status"] == "error":
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        components={
            "qdrant": qdrant_status,
            "groq_api": groq_status,
            "embedding_model": {"status": "loaded", "model": settings.EMBEDDING_MODEL}
        }
    )


@router.get("/stats", response_model=StatsResponse)
@timing
async def get_stats(
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dep)
):
    try:
        collection_info = qdrant_client.get_collection(settings.COLLECTION_NAME)
        total_vectors = collection_info.points_count or 0

        return StatsResponse(
            collection_name=settings.COLLECTION_NAME,
            total_vectors=total_vectors,
            total_files=total_vectors,
            vector_dimension=collection_info.config.params.vectors.size,
            last_updated=None
        )

    except Exception as e:
        logger.error(f"❌ Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Could not retrieve stats: {str(e)}")


@router.delete("/reset", response_model=ResetResponse)
@timing
async def reset_database(
    request: ResetRequest,
    qdrant_client: QdrantClient = Depends(get_qdrant_client_dep)
):
    logger.warning("🗑️ Database reset requested")

    try:
        if not request.confirm:
            raise ValueError("Explicit confirmation required")

        qdrant_client.delete_collection(settings.COLLECTION_NAME)
        logger.info(f"✅ Deleted collection: {settings.COLLECTION_NAME}")

        return ResetResponse(
            status="success",
            message=f"Collection '{settings.COLLECTION_NAME}' deleted successfully",
            vectors_deleted=None
        )

    except Exception as e:
        logger.error(f"❌ Reset failed: {e}")
        raise HTTPException(status_code=400, detail=f"Reset error: {str(e)}")