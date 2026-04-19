#!/usr/bin/env python3
"""
Standalone Ingestion Pipeline Script

Purpose:
    Loads all .txt files from the data directory, converts them to embeddings,
    and uploads them to Qdrant. Designed to handle 1000s of files efficiently.

Usage:
    python scripts/ingest_texts.py                          # Uses default settings
    python scripts/ingest_texts.py --data-dir ./my_docs     # Custom directory
    python scripts/ingest_texts.py --dry-run                # Test without uploading

Features:
    ✅ tqdm progress bars for each phase
    ✅ Precise timing for loading, embedding, and uploading
    ✅ Graceful error handling (skips bad files, continues pipeline)
    ✅ Memory-efficient batch processing
    ✅ Detailed summary report at completion
"""

import sys
import time
import argparse
import uuid
from pathlib import Path
from typing import List, Tuple, Dict
from tqdm import tqdm
from qdrant_client.models import PointStruct

# === Project Imports ===
from src.utils.config import settings
from src.utils.logger import setup_logger, get_logger
from src.utils.timer import format_duration
from src.ingestion.text_loader import load_txt_files
from src.ingestion.embedder import TextEmbedder
from src.ingestion.indexer import VectorIndexer

# Initialize logger with project settings
setup_logger(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)
logger = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for customization.
    
    Allows users to override default config without editing .env files.
    """
    parser = argparse.ArgumentParser(
        description="Ingest preprocessed .txt files into Qdrant vector database"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=settings.DATA_DIR,
        help="Path to directory containing .txt files (default: from .env)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Number of files to embed at once (default: 64)"
    )
    parser.add_argument(
        "--upload-batch",
        type=int,
        default=100,
        help="Number of vectors to upload per Qdrant request (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and embed files, but skip uploading to Qdrant"
    )
    return parser.parse_args()


def main() -> None:
    """
    Main ingestion pipeline orchestrator.
    
    Flow:
    1. Parse CLI arguments & validate paths
    2. Initialize components (embedder, indexer)
    3. Phase 1: Load .txt files into memory
    4. Phase 2: Generate embeddings in batches
    5. Phase 3: Upload vectors to Qdrant
    6. Print comprehensive summary report
    """
    args = parse_arguments()
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Laptop Troubleshooting Ingestion Pipeline")
    logger.info(f"   Data Directory: {args.data_dir}")
    logger.info(f"   Embedding Batch Size: {args.batch_size}")
    logger.info(f"   Upload Batch Size: {args.upload_batch}")
    logger.info(f"   Dry Run: {'YES' if args.dry_run else 'NO'}")
    logger.info("=" * 60)
    
    # Track overall pipeline start time
    pipeline_start = time.time()
    
    # Initialize tracking variables
    stats = {
        "total_files_found": 0,
        "successfully_loaded": 0,
        "successfully_embedded": 0,
        "successfully_uploaded": 0,
        "errors": []
    }
    
    try:
        # ==========================================
        # 📦 PHASE 1: Load & Collect .txt Files
        # ==========================================
        logger.info("📖 Phase 1: Loading text files...")
        phase1_start = time.time()
        
        loaded_data: List[Tuple[str, str, Dict]] = []
        
        # Use the generator to load files with progress tracking
        for filename, text, metadata in tqdm(
            load_txt_files(args.data_dir), 
            desc="Loading files", 
            unit="file",
            leave=False
        ):
            stats["successfully_loaded"] += 1
            loaded_data.append((filename, text, metadata))
            
        stats["total_files_found"] = stats["successfully_loaded"]
        phase1_duration = time.time() - phase1_start
        
        if not loaded_data:
            logger.warning("⚠️ No valid .txt files found. Aborting pipeline.")
            return
            
        logger.info(f"✅ Phase 1 Complete: Loaded {stats['total_files_found']} files in {format_duration(phase1_duration)}")
        
        # ==========================================
        # 🔢 PHASE 2: Generate Embeddings
        # ==========================================
        logger.info("🧠 Phase 2: Generating embeddings...")
        phase2_start = time.time()
        
        # Initialize embedder (lazy-loads model on first call)
        embedder = TextEmbedder(batch_size=args.batch_size)
        
        # Extract texts for batch processing
        all_texts = [text for _, text, _ in loaded_data]
        all_filenames = [fn for fn, _, _ in loaded_data]
        all_metadata = [meta for _, _, meta in loaded_data]
        
        # Encode all texts in batches
        embeddings = embedder.encode_texts(all_texts)
        stats["successfully_embedded"] = len(embeddings)
        
        phase2_duration = time.time() - phase2_start
        logger.info(f"✅ Phase 2 Complete: Generated {stats['successfully_embedded']} embeddings in {format_duration(phase2_duration)}")
        
        # ==========================================
        # 🗃️ PHASE 3: Upload to Qdrant
        # ==========================================
        if args.dry_run:
            logger.info("💧 Dry run enabled. Skipping Qdrant upload.")
            phase3_duration = 0.0
            stats["successfully_uploaded"] = 0
        else:
            logger.info("☁️ Phase 3: Uploading to Qdrant...")
            phase3_start = time.time()
            
            # Initialize indexer
            indexer = VectorIndexer()
            
            # Determine vector dimension from first embedding
            vector_dim = len(embeddings[0]) if embeddings else 768
            indexer.ensure_collection(vector_size=vector_dim)
            
            # Build Qdrant PointStruct objects
            points_to_upload = []
            for i in range(len(embeddings)):
                point = PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_DNS, all_filenames[i])),  # Valid UUID from filename
                    vector=embeddings[i],
                    payload={
                        "text": all_texts[i],
                        "source": all_filenames[i],
                        **all_metadata[i]
                    }
                )
                points_to_upload.append(point)
            
            # Upload in batches
            stats["successfully_uploaded"] = indexer.upload_points(
                points=points_to_upload,
                batch_size=args.upload_batch
            )
            
            phase3_duration = time.time() - phase3_start
            logger.info(f"✅ Phase 3 Complete: Uploaded {stats['successfully_uploaded']} vectors in {format_duration(phase3_duration)}")
        
        # ==========================================
        # 📊 FINAL SUMMARY REPORT
        # ==========================================
        total_duration = time.time() - pipeline_start
        
        print("\n" + "=" * 60)
        print("📊 INGESTION PIPELINE SUMMARY")
        print("=" * 60)
        print(f"⏱️  Total Time:          {format_duration(total_duration)}")
        print(f"📁 Files Found:        {stats['total_files_found']}")
        print(f"✅ Successfully Loaded:  {stats['successfully_loaded']}")
        print(f"🧠 Successfully Embedded: {stats['successfully_embedded']}")
        print(f"☁️ Successfully Uploaded: {stats['successfully_uploaded']}")
        print(f"⚠️ Errors:             {len(stats['errors'])}")
        
        if stats['errors']:
            print("\n🔍 Recent Errors (check logs for full details):")
            for err in stats['errors'][-5:]:
                print(f"   • {err}")
                
        print("=" * 60)
        logger.info("🎉 Pipeline execution finished successfully!")
        
    except KeyboardInterrupt:
        logger.warning("⛔ Pipeline interrupted by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Fatal pipeline error: {e}", exc_info=True)
        print(f"\n❌ Fatal Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()