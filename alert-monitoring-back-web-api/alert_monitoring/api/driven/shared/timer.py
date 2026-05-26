import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def log_timer(label: str, log: logging.Logger | None = None):
    """Context manager that logs elapsed time in ms for a named step."""
    _log = log or logger
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _log.info("[TIMER] %s → %.1f ms", label, elapsed_ms)
