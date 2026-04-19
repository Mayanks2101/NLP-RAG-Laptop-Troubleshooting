# src/generation/qa_chain.py
"""
Question-Answer pipeline orchestrator.

Connects retrieval + prompt building + LLM generation into a single flow.
Acts as the bridge between the API `/query` endpoint and the backend modules.

Beginner tip: This is the "conductor" that tells each section when to play.
It keeps the API routes clean and testable.
"""

import time
from typing import Dict, List

from src.retrieval.retriever import Retriever
from src.generation.llm_client import GroqLLMClient
from src.generation.prompt_templates import SYSTEM_PROMPT, FALLBACK_RESPONSE, build_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)


class QAPipeline:
    """
    End-to-end QA pipeline: Question → Retrieval → Prompt → LLM → Answer
    
    Usage:
        pipeline = QAPipeline(retriever, llm_client)
        result = pipeline.process("Why is my screen black?")
        print(result["answer"])
    """
    
    def __init__(self, retriever: Retriever, llm_client: GroqLLMClient):
        self.retriever = retriever
        self.llm_client = llm_client
        
    def process(self, question: str) -> Dict:
        """
        Execute the full RAG pipeline for a single question.
        
        Args:
            question: User's troubleshooting query
            
        Returns:
            Dictionary containing answer, contexts, timing, and metadata
        """
        start_time = time.time()
        logger.info(f"🎯 Processing query: '{question[:60]}...'")
        
        # Step 1: Retrieve relevant contexts
        contexts = self.retriever.search(question)
        
        # Step 2: Handle empty retrieval gracefully
        if not contexts:
            logger.info("ℹ️ No relevant contexts found. Returning fallback response.")
            return {
                "answer": FALLBACK_RESPONSE,
                "contexts": [],
                "chunks_used": 0,
                "processing_time_seconds": round(time.time() - start_time, 2)
            }
        
        # Step 3: Build LLM prompt
        user_prompt = build_prompt(question, contexts)
        
        # Step 4: Generate answer via Groq
        answer = self.llm_client.generate(SYSTEM_PROMPT, user_prompt)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Query processed in {elapsed:.2f}s | Used {len(contexts)} knowledge chunks")
        
        return {
            "answer": answer,
            "contexts": contexts,
            "chunks_used": len(contexts),
            "processing_time_seconds": round(elapsed, 2)
        }