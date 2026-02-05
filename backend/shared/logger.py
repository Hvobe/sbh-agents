"""
Strukturiertes Logging
"""
import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Erstellt einen konfigurierten Logger."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


# Pre-konfigurierte Logger
api_logger = setup_logger("api", logging.INFO)
agent_logger = setup_logger("agents", logging.INFO)
llm_logger = setup_logger("llm", logging.INFO)
db_logger = setup_logger("database", logging.INFO)


def log_api_error(endpoint: str, error: Exception, extra: Optional[dict] = None):
    """Loggt einen API-Fehler mit Kontext."""
    msg = f"Error in {endpoint}: {error}"
    api_logger.error(msg, exc_info=True, extra=extra or {})
