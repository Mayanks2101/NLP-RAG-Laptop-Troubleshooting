# src/ingestion/indexer.py
"""
Vector database indexer for the RAG ingestion pipeline.

Handles connection to Qdrant, collection creation, and batch uploading
of embedding vectors with metadata.

Key Features:
- Auto-creates collection if it doesn't exist
- Batch uploading with tqdm progress
- Graceful error handling (logs failures, continues pipeline)
- Timing logs for connection & upload
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Optional
from tqdm import tqdm
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.timer import timer

logger = get_logger(__name__)


class VectorIndexer:
    """
    Manages Qdrant connection and vector uploads.
    
    Usage:
        indexer = VectorIndexer()
        indexer.ensure_collection(vector_size=768)
        uploaded = indexer.upload_points(points_list)
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or settings.QDRANT_HOST
        self.port = port or settings.QDRANT_PORT
        self.collection_name = settings.COLLECTION_NAME
        self.client: Optional[QdrantClient] = None
        
    def connect(self) -> QdrantClient:
        """Establish connection to Qdrant (cached after first call)."""
        if self.client is None:
            with timer("Connecting to Qdrant"):
                self.client = QdrantClient(
                    host=self.host, 
                    port=self.port, 
                    prefer_grpc=False  # HTTP is easier for debugging
                )
                # Test connection
                self.client.get_collections()
                logger.info("✓ Connected to Qdrant successfully")
        return self.client
    
    def ensure_collection(self, vector_size: int) -> None:
        """
        Create Qdrant collection if it doesn't already exist.
        
        Args:
            vector_size: Dimension of embeddings (768 for bge-base-en-v1.5)
        """
        client = self.connect()
        collections = client.get_collections()
        exists = any(c.name == self.collection_name for c in collections.collections)
        
        if not exists:
            with timer(f"Creating collection '{self.collection_name}'"):
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE  # Best for normalized embeddings
                    )
                )
                logger.info(f"✅ Created collection: {self.collection_name} (dim={vector_size})")
        else:
            logger.info(f"ℹ️  Collection '{self.collection_name}' already exists")
            
    def upload_points(self, points: List[PointStruct], batch_size: int = 100) -> int:
        """
        Upload points to Qdrant in batches with progress tracking.
        
        Args:
            points: List of Qdrant PointStruct objects
            batch_size: Number of points to send per API call
            
        Returns:
            Number of successfully uploaded points
        """
        if not points:
            logger.warning("No points provided for upload")
            return 0
            
        client = self.connect()
        uploaded_count = 0
        total = len(points)
        
        with tqdm(total=total, desc="Uploading to Qdrant", unit="vector") as pbar:
            for i in range(0, total, batch_size):
                batch = points[i : i + batch_size]
                try:
                    client.upsert(
                        collection_name=self.collection_name,
                        points=batch
                    )
                    uploaded_count += len(batch)
                    pbar.update(len(batch))
                except Exception as e:
                    logger.error(f"❌ Failed to upload batch starting at index {i}: {e}")
                    # Continue processing remaining batches
                    
        logger.info(f"✅ Successfully uploaded {uploaded_count}/{total} vectors")
        return uploaded_count