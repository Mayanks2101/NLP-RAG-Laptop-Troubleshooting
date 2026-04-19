# src/ingestion/embedder.py
"""
Text embedding module for the RAG ingestion pipeline.

Converts raw text into numerical vectors using SentenceTransformers.
Uses batching to process thousands of files efficiently without 
overloading system memory.

Key Features:
- Lazy model loading (only loads when first called)
- Batch processing with tqdm progress
- Automatic vector normalization (required for cosine similarity)
- Timing logs for embedding generation
"""

from sentence_transformers import SentenceTransformer
from typing import List, Optional
from tqdm import tqdm
import numpy as np
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.timer import timer

logger = get_logger(__name__)


class TextEmbedder:
    """
    Wrapper around SentenceTransformer for efficient batch embedding.
    
    Usage:
        embedder = TextEmbedder()
        embeddings = embedder.encode_texts(["text1", "text2", ...])
    """
    
    def __init__(self, model_name: Optional[str] = None, batch_size: int = 64):
        """
        Initialize the embedder.
        
        Args:
            model_name: HuggingFace model to use. Defaults to config setting.
            batch_size: Number of texts to process at once. 
                        Higher = faster, Lower = less memory.
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.batch_size = batch_size
        self.model: Optional[SentenceTransformer] = None
        
    def load_model(self) -> SentenceTransformer:
        """
        Load the embedding model into memory (lazy initialization).
        Only runs once, then caches the model for reuse.
        """
        if self.model is None:
            with timer(f"Loading embedding model ({self.model_name})"):
                # Load model from HuggingFace cache (or download if first run)
                self.model = SentenceTransformer(self.model_name)
                # Explicitly use CPU for stability in ingestion scripts
                self.model.to("cpu")
                logger.info("✓ Embedding model loaded & cached")
        return self.model
    
    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Convert a list of text strings into embedding vectors.
        
        Args:
            texts: List of strings to encode
            
        Returns:
            List of embedding vectors (list of lists of floats)
        """
        if not texts:
            logger.warning("No texts provided for embedding")
            return []
            
        model = self.load_model()
        all_embeddings = []
        
        # Process in batches with progress bar
        with tqdm(total=len(texts), desc="Generating embeddings", unit="chunk") as pbar:
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i : i + self.batch_size]
                
                # Encode batch & normalize for cosine similarity
                # show_progress_bar=False because we have our own tqdm
                embeddings = model.encode(
                    batch, 
                    normalize_embeddings=True, 
                    show_progress_bar=False
                )
                
                # Convert numpy array to Python lists (Qdrant friendly)
                all_embeddings.extend(embeddings.tolist())
                pbar.update(len(batch))
                
        logger.info(f"✓ Generated {len(all_embeddings)} embeddings")
        return all_embeddings