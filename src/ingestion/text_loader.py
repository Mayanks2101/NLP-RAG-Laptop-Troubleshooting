# src/ingestion/text_loader.py
"""
Text file loader for the RAG ingestion pipeline.

This module scans a directory for .txt files and yields their content
along with metadata. It uses a Python generator to handle thousands
of files efficiently without loading everything into memory at once.

Key Features:
- tqdm progress bar for visual feedback
- Graceful error handling (skips corrupt/empty files)
- Timing logs for performance tracking
- Beginner-friendly: clear docstrings & comments
"""

from pathlib import Path
from typing import Generator, Tuple, Dict, Optional
from tqdm import tqdm
from src.utils.config import settings
from src.utils.logger import get_logger
from src.utils.timer import timer

# Get a logger specific to this module
logger = get_logger(__name__)


def load_txt_files(source_dir: Optional[Path] = None) -> Generator[Tuple[str, str, Dict], None, None]:
    """
    Generator that yields (filename, text_content, metadata) for each .txt file.
    
    Why a generator? 
    Instead of loading 1000s of files into RAM at once, it processes them
    one-by-one as requested by the calling code. This prevents memory crashes.
    
    Args:
        source_dir: Path to directory containing .txt files. 
                    Defaults to settings.DATA_DIR if not provided.
                    
    Yields:
        Tuple of (filename, text_content, metadata_dict)
    """
    if source_dir is None:
        source_dir = settings.DATA_DIR
    
    # Ensure directory exists
    if not source_dir.is_dir():
        logger.error(f"Data directory not found: {source_dir}")
        return
    
    # Find all .txt files recursively
    txt_files = sorted(list(source_dir.rglob("*.txt")))
    
    if not txt_files:
        logger.warning(f"No .txt files found in {source_dir}")
        return
        
    logger.info(f"🔍 Found {len(txt_files)} .txt files to process")
    
    # Use tqdm to show progress while iterating through files
    for file_path in tqdm(txt_files, desc="Loading .txt files", unit="file"):
        try:
            # Read file content with UTF-8 encoding
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            
            # Skip empty files (common with bad exports)
            if not text:
                logger.debug(f"⏭️ Skipping empty file: {file_path.name}")
                continue
            
            # Prepare metadata to store alongside the vector in Qdrant
            metadata = {
                "source": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "char_count": len(text),
                "loaded_at": __import__('time').time()
            }
            
            # Yield control back to the pipeline with the loaded data
            yield file_path.name, text, metadata
            
        except UnicodeDecodeError as e:
            logger.error(f"❌ Encoding error in {file_path.name}: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to load {file_path.name}: {e}")