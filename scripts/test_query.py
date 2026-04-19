# scripts/test_query.py
#!/usr/bin/env python3
"""
Quick test script for the RAG pipeline.
Run this to verify retrieval + generation works end-to-end.
"""

import sys
from src.utils.config import settings
from src.utils.logger import setup_logger, get_logger
from src.api.dependencies import get_qdrant_client, get_embedding_model, get_groq_client
from src.retrieval.retriever import Retriever
from src.generation.llm_client import GroqLLMClient
from src.generation.qa_chain import QAPipeline

setup_logger(log_level="INFO", log_file="./logs/test_query.log")
logger = get_logger(__name__)

def main():
    logger.info("🧪 Testing RAG Pipeline...")
    
    # Load shared resources
    qdrant = get_qdrant_client()
    embedder = get_embedding_model()
    groq = get_groq_client()
    
    # Build pipeline
    retriever = Retriever(qdrant, embedder)
    llm_client = GroqLLMClient(groq)
    pipeline = QAPipeline(retriever, llm_client)
    
    # Test questions
    test_questions = [
        "My laptop battery is not charging.",
        "Screen is completely black but power LED is on.",
        "Laptop overheats and shuts down randomly."
    ]
    
    for q in test_questions:
        print(f"\n❓ Question: {q}")
        print("-" * 50)
        try:
            result = pipeline.process(q)
            print(f"✅ Answer: {result['answer'][:200]}...")
            print(f"⏱️ Time: {result['processing_time_seconds']}s | Chunks: {result['chunks_used']}")
        except Exception as e:
            print(f"❌ Error: {e}")
        print("=" * 50)

if __name__ == "__main__":
    main()