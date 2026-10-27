"""Backend configuration, read from environment variables (see .env.example). No secrets are hard-coded."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


class Config:
    MODELS_DIR = Path(os.getenv("CYBERSENTINEL_MODELS_DIR", ROOT / "models"))
    REPORTS_DIR = Path(os.getenv("CYBERSENTINEL_REPORTS_DIR", ROOT / "reports"))
    DATA_PATH = Path(os.getenv("CYBERSENTINEL_DATA_PATH", ROOT / "data" / "raw" / "creditcard.csv"))
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
    MAX_CONTENT_LENGTH = _int("MAX_CONTENT_LENGTH", 1_000_000)  # bytes
    MAX_BATCH_SIZE = _int("MAX_BATCH_SIZE", 100)
    MAX_PAGE_SIZE = _int("MAX_PAGE_SIZE", 100)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    PORT = _int("FLASK_PORT", 5000)
    DEBUG = False  # never enable the Werkzeug debugger on a reachable interface
