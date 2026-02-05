"""
Zentrale Konfiguration
"""
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# LLM Models
# =============================================================================
DEFAULT_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o")
FAST_MODEL = os.getenv("FAST_LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = "text-embedding-3-small"

# LLM Request Timeout (Sekunden)
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

# Chat History / Memory Settings
MAX_RECENT_MESSAGES = 4
MAX_OLDER_MESSAGES = 4


# =============================================================================
# GPT Pricing (USD per 1M tokens)
# =============================================================================
PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
}


# =============================================================================
# Database Configuration
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL")
FAQ_TABLE = os.getenv("FAQ_TABLE", "documents")


# =============================================================================
# API Keys
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# =============================================================================
# Validation
# =============================================================================
def validate_config() -> None:
    """
    Prüft ob alle erforderlichen Umgebungsvariablen gesetzt sind.
    """
    required = ["OPENAI_API_KEY", "DATABASE_URL"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        raise EnvironmentError(
            f"Fehlende Umgebungsvariablen: {', '.join(missing)}\n"
            f"Bitte in .env Datei setzen."
        )


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Hilfsfunktion zum Abrufen von Umgebungsvariablen."""
    value = os.getenv(key, default)
    if required and value is None:
        raise EnvironmentError(f"Erforderliche Umgebungsvariable fehlt: {key}")
    return value
