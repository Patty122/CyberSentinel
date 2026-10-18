import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Config:
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "100"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(1024 * 1024)))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))
    MODELS_DIR = Path(os.getenv("MODELS_DIR", ROOT / "models"))
    REPORTS_DIR = Path(os.getenv("REPORTS_DIR", ROOT / "reports"))
    DATA_PATH = Path(os.getenv("DATA_PATH", ROOT / "data" / "raw" / "creditcard.csv"))
