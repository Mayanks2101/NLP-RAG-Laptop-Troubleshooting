# src/retrieval/retriever.py

import time
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.timer import timer

logger = get_logger(__name__)


class Retriever:
    """
    Manages semantic search against the Qdrant knowledge base.

    Usage:
        retriever = Retriever(qdrant_client, embedding_model)
        contexts = retriever.search("My laptop won't turn on")
    """

    def __init__(self, qdrant_client: QdrantClient, embedding_model: SentenceTransformer):
        self.client = qdrant_client
        self.model = embedding_model
        self.collection_name = settings.COLLECTION_NAME

    def _encode_query(self, query: str) -> List[float]:
        """Convert user question to a normalized embedding vector."""
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding.tolist()

    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Execute semantic search and return ranked contexts.

        Args:
            query: User's troubleshooting question
            top_k: Max results to return (defaults to settings.TOP_K)

        Returns:
            List of dicts: [{"text": ..., "source": ..., "score": ...}]
        """
        top_k = top_k or settings.TOP_K
        start_time = time.time()

        try:
            query_vector = self._encode_query(query)

            with timer("Qdrant vector search"):
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    with_payload=True,
                )

            contexts = []
            for r in results:
                contexts.append(
                    {
                        "text": r.payload.get("text", ""),
                        "source": r.payload.get("source", "unknown"),
                        "score": round(r.score, 4),
                    }
                )

            elapsed = time.time() - start_time
            logger.info("🔍 Retrieved {} contexts in {:.2f}s", len(contexts), elapsed)

            return contexts

        except Exception as e:
            logger.exception("❌ Retrieval failed: {}", str(e))
            return []