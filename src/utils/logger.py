# src/utils/logger.py
"""
Logger configuration module.

This module sets up a centralized logging system using loguru.
Loguru is chosen because it's beginner-friendly and doesn't require
complex handler configuration like Python's built-in logging.

Features:
- Logs to both console and file
- Color-coded output for easy reading
- Automatic log rotation (prevents huge log files)
- Includes timing information for performance tracking
"""

import sys
from pathlib import Path
from loguru import logger as loguru_logger


def setup_logger(
    log_level: str = "INFO",
    log_file: str = "./logs/app.log",
    retention_days: int = 7
) -> None:
    """
    Configure the application logger.
    
    This function removes default loguru handlers and adds our custom ones.
    It's called once at application startup.
    
    Args:
        log_level: Minimum level to log ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_file: Path to the log file (will be created if doesn't exist)
        retention_days: How many days to keep old log files
    """
    
    # Remove default loguru handler to avoid duplicate logs
    loguru_logger.remove()
    
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format for console output (colorful and readable)
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}:{function}:{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Format for file output (more detailed, no colors)
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # Add console handler - shows logs in terminal
    loguru_logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,  # Enable colors in terminal
        backtrace=True,  # Show variable values in tracebacks (debugging)
        diagnose=True,   # Show local variables in errors (debugging)
    )
    
    # Add file handler - saves logs to disk
    loguru_logger.add(
        log_file,
        format=file_format,
        level=log_level,
        rotation="10 MB",  # Create new file when current reaches 10MB
        retention=f"{retention_days} days",  # Auto-delete old logs
        compression="zip",  # Compress old logs to save space
        backtrace=True,
        diagnose=True,
    )
    
    # Log that setup is complete
    loguru_logger.info(f"Logger initialized | Level: {log_level} | File: {log_file}")


def get_logger(name: str = None):
    """
    Get a logger instance for a specific module.
    
    Usage example in another file:
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Starting data ingestion...")
    
    Args:
        name: Usually __name__ of the calling module
        
    Returns:
        loguru.logger instance configured for the module
    """
    if name:
        return loguru_logger.bind(module=name)
    return loguru_logger


# Create a default logger instance for direct imports
logger = get_logger()