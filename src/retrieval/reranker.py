# src/retrieval/reranker.py
"""
Cross-Encoder Reranker using BAAI/bge-reranker-base.

Purpose:
    After union of multi-query results, we may have 10-15 chunks.
    The embedding model used for retrieval is a Bi-Encoder — it encodes
    query and document SEPARATELY, which is fast but less accurate.

    A Cross-Encoder reads (query + document) TOGETHER, giving a much
    more accurate relevance score. We use it as a final filter to keep
    only the most relevant RERANKER_TOP_K chunks before sending to the LLM.

Why BAAI/bge-reranker-base?
    - Same family as our embedding model (BAAI/bge-base-en-v1.5) → consistent scoring.
    - Small and fast (110M params), runs comfortably on CPU.
    - State-of-the-art for English reranking on BEIR benchmark.

Scoring against combined query string:
    We concatenate the original question + all generated queries into a
    single string separated by " | ". This forces the reranker to score
    each chunk against the FULL intent of the user, not just one angle.

    Example combined_query:
        "laptop won't turn on | computer not powering up | no boot response laptop"
"""

from typing import List, Dict, Optional

from sentence_transformers import CrossEncoder

from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.timer import timer

logger = get_logger(__name__)


class Reranker:
    """
    Scores and re-orders candidate chunks using a Cross-Encoder model.

    Usage:
        reranker = Reranker()
        top_chunks = reranker.rerank(
            original_query="laptop won't turn on",
            generated_queries=["no power response laptop", ...],
            chunks=[{"text": ..., "source": ..., "score": ...}, ...],
            top_k=4,
        )
    """

    def __init__(self, model_name: Optional[str] = None):
        model_name = model_name or settings.RERANKER_MODEL
        logger.info("Loading Cross-Encoder reranker: {}", model_name)
        self.model = CrossEncoder(model_name)
        logger.info("✓ Reranker loaded: {}", model_name)

    def rerank(
        self,
        original_query: str,
        generated_queries: List[str],
        chunks: List[Dict],
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Score each chunk against the combined query and return top-K.

        Args:
            original_query:    The user's original question.
            generated_queries: List of alternative queries from the generator.
            chunks:            Candidate chunks after union/deduplication.
            top_k:             How many chunks to keep (default: settings.RERANKER_TOP_K).

        Returns:
            List of chunk dicts (same format as Retriever.search), now sorted
            by reranker_score descending, truncated to top_k.
            Each chunk gets an extra "reranker_score" key for transparency.
        """
        top_k = top_k or settings.RERANKER_TOP_K

        if not chunks:
            logger.warning("Reranker received empty chunk list")
            return []

        # Build a rich combined query string:
        #   original question weighted first, then generated queries
        all_queries = [original_query] + generated_queries
        combined_query = " | ".join(q.strip() for q in all_queries if q.strip())

        logger.info(
            "🎯 Reranking {} chunks | combined query: '{}'",
            len(chunks),
            combined_query[:80],
        )

        # CrossEncoder expects list of (query, document) pairs
        pairs = [(combined_query, chunk["text"]) for chunk in chunks]

        with timer("Cross-Encoder reranking"):
            raw_scores: List[float] = self.model.predict(pairs).tolist()

        # Attach reranker scores and sort
        scored_chunks = []
        for chunk, score in zip(chunks, raw_scores):
            enriched = dict(chunk)            # shallow copy to avoid mutating original
            enriched["reranker_score"] = round(float(score), 4)
            scored_chunks.append(enriched)

        scored_chunks.sort(key=lambda c: c["reranker_score"], reverse=True)

        top_chunks = scored_chunks[:top_k]

        logger.info(
            "✅ Reranked: kept {}/{} chunks | top score: {:.4f} | bottom score: {:.4f}",
            len(top_chunks),
            len(chunks),
            top_chunks[0]["reranker_score"] if top_chunks else 0.0,
            top_chunks[-1]["reranker_score"] if top_chunks else 0.0,
        )

        return top_chunks
