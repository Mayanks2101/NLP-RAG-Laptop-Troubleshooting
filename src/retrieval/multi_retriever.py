# src/retrieval/multi_retriever.py
"""
Multi-Query Parallel Retriever with Union & Deduplication.

Purpose:
    Runs a separate Qdrant vector search for EACH generated query
    simultaneously using asyncio, then merges the results.

    Why async/parallel?
        Each Qdrant search call takes ~20-80ms. Running 3 queries
        sequentially = ~60-240ms extra latency. Running them in
        parallel = almost zero extra latency (bounded by the slowest query).

Deduplication strategy:
    A chunk is identified by its "source" filename (since each .txt file
    is stored as exactly one vector in Qdrant). If the same source appears
    in multiple query results, we keep the version with the highest
    bi-encoder similarity score.

Output:
    A deduplicated list of chunks, sorted by their best bi-encoder score
    descending. This list is then passed to the Reranker.
"""

import asyncio
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from src.retrieval.retriever import Retriever
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.timer import timer

logger = get_logger(__name__)


class MultiQueryRetriever:
    """
    Wraps the existing Retriever to support parallel multi-query retrieval.

    Usage:
        mretriever = MultiQueryRetriever(qdrant_client, embedding_model)
        chunks = mretriever.search_all(
            queries=["query 1", "query 2", "query 3"],
            top_k_per_query=5,
        )
        # Returns deduplicated union, sorted by best bi-encoder score
    """

    def __init__(self, qdrant_client: QdrantClient, embedding_model: SentenceTransformer):
        self._retriever = Retriever(qdrant_client, embedding_model)

    def search_all(
        self,
        queries: List[str],
        top_k_per_query: Optional[int] = None,
    ) -> List[Dict]:
        """
        Run parallel Qdrant searches for all queries and return deduplicated union.

        Args:
            queries:          List of query strings (original + generated).
            top_k_per_query:  Max results per individual query search.

        Returns:
            Deduplicated list of chunk dicts sorted by best bi-encoder score.
        """
        top_k_per_query = top_k_per_query or settings.TOP_K

        logger.info(
            "🔍 Multi-retrieval: {} queries × top-{} each",
            len(queries),
            top_k_per_query,
        )

        with timer("Parallel multi-query retrieval"):
            all_results = self._run_parallel(queries, top_k_per_query)

        merged = self._union_and_deduplicate(all_results)

        logger.info(
            "✅ Multi-retrieval complete: {} raw results → {} unique chunks after dedup",
            sum(len(r) for r in all_results),
            len(merged),
        )

        return merged

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_parallel(
        self,
        queries: List[str],
        top_k: int,
    ) -> List[List[Dict]]:
        """
        Execute all searches concurrently via asyncio.

        Returns a list-of-lists: one inner list per query.
        """
        async def _async_search_all():
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    None,               # default ThreadPoolExecutor
                    self._retriever.search,
                    query,
                    top_k,
                )
                for query in queries
            ]
            return await asyncio.gather(*tasks)

        # If we are already inside an event loop (FastAPI async context),
        # use run_in_executor directly; otherwise spin up a new loop.
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context — run synchronously in threads
            import concurrent.futures
            futures = [
                loop.run_in_executor(None, self._retriever.search, q, top_k)
                for q in queries
            ]
            # This is called from inside an async route via pipeline.process()
            # which is itself a normal sync method, so we use a thread pool trick:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(
                    lambda q: self._retriever.search(q, top_k), queries
                ))
            return results
        except RuntimeError:
            # No running event loop — create one
            return asyncio.run(_async_search_all())

    def _union_and_deduplicate(self, all_results: List[List[Dict]]) -> List[Dict]:
        """
        Merge results from multiple queries, keeping the highest bi-encoder
        score for any chunk that appears in more than one query's results.

        Deduplication key: "source" (filename), since each file = one vector.

        Returns:
            Unique chunks sorted by best score descending.
        """
        best_per_source: Dict[str, Dict] = {}

        for query_results in all_results:
            for chunk in query_results:
                source = chunk.get("source", "unknown")
                existing = best_per_source.get(source)

                if existing is None or chunk["score"] > existing["score"]:
                    best_per_source[source] = chunk

        merged = sorted(
            best_per_source.values(),
            key=lambda c: c["score"],
            reverse=True,
        )

        return merged
