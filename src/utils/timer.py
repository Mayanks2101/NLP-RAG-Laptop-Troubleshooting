# src/utils/timer.py
"""
Timing utilities for tracking execution time.

Two main tools:
1. @timing decorator - Wrap any function (sync or async) to auto-log execution time
2. timer context manager - Measure time for specific code blocks manually
"""

import time
import asyncio
from functools import wraps
from contextlib import contextmanager
from typing import Callable, Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


def timing(func: Callable) -> Callable:
    """
    Decorator to log function execution time.
    Works correctly for BOTH regular and async functions.

    The original implementation used a plain `def wrapper`, which broke all
    async FastAPI route handlers decorated with @timing: calling an async
    function without awaiting it returns a bare coroutine object, which
    FastAPI cannot serialize — causing ResponseValidationError on every call.

    Fix: detect whether the wrapped function is a coroutine function and
    return an `async def` wrapper when needed.

    Usage:
        @timing
        async def my_endpoint(): ...   # ← works now

        @timing
        def my_function(): ...         # ← still works
    """
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            # Use loguru placeholder style (not f-strings) to avoid KeyError
            # when log messages contain curly braces from exception reprs.
            logger.info("▶ Starting {}...", func.__name__)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed_time = time.time() - start_time
                logger.info("✓ {} completed in {:.2f}s", func.__name__, elapsed_time)
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            logger.info("▶ Starting {}...", func.__name__)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_time = time.time() - start_time
                logger.info("✓ {} completed in {:.2f}s", func.__name__, elapsed_time)
        return sync_wrapper


@contextmanager
def timer(description: str = "Operation"):
    """
    Context manager to time a block of code.

    Usage:
        with timer("Loading data"):
            data = load_data()
    """
    start_time = time.time()
    logger.info("▶ {}...", description)
    try:
        yield
    finally:
        elapsed_time = time.time() - start_time
        logger.info("✓ {} completed in {:.2f}s", description, elapsed_time)


def format_duration(seconds: float) -> str:
    """
    Convert seconds to human-readable duration string.

    Examples:
        0.5  -> "0.50s"
        65   -> "1m 5s"
        3665 -> "1h 1m 5s"
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"