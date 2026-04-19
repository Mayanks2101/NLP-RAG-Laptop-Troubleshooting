# src/ingestion/__init__.py
"""
Ingestion module: Handles loading, embedding, and indexing .txt files.

This package contains three main components:
1. text_loader.py  -> Reads .txt files from disk
2. embedder.py     -> Converts text to vectors
3. indexer.py      -> Uploads vectors to Qdrant

Usage example:
    from src.ingestion import TextLoader, TextEmbedder, VectorIndexer
    loader = TextLoader()
    embedder = TextEmbedder()
    indexer = VectorIndexer()
    # ... pipeline logic ...
"""

from .text_loader import load_txt_files
from .embedder import TextEmbedder
from .indexer import VectorIndexer

__all__ = ["load_txt_files", "TextEmbedder", "VectorIndexer"]