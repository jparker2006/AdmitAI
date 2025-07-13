"""
Utility helpers: logging, timing decorator, etc.
"""

import logging
import time
from functools import wraps

logger = logging.getLogger("essay_agent")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(name)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def timed(func):
    """Decorator to measure execution time of functions."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.debug(f"{func.__name__} executed in {duration:.3f}s")
        return result

    return wrapper 