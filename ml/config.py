"""Central configuration for the ML pipeline (paths, schema, seeds, split sizes)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Paths can be overridden with environment variables (see .env.example).
DATA_PATH = Path(os.getenv("CYBERSENTINEL_DATA_PATH", ROOT / "data" / "raw" / "creditcard.csv"))
MODELS_DIR = Path(os.getenv("CYBERSENTINEL_MODELS_DIR", ROOT / "models"))
REPORTS_DIR = Path(os.getenv("CYBERSENTINEL_REPORTS_DIR", ROOT / "reports"))
FIGURES_DIR = REPORTS_DIR / "figures"

# Dataset schema (Kaggle "Credit Card Fraud Detection", ULB MLG).
TARGET = "Class"
FEATURES = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
ALL_COLUMNS = FEATURES + [TARGET]

# Reproducibility and splitting: 60 % train / 20 % validation / 20 % test (stratified).
SEED = 42
VAL_SIZE = 0.20
TEST_SIZE = 0.20

# Threshold selection on validation data: maximise F-beta (beta=2 weights recall twice as much as precision).
THRESHOLD_BETA = 2.0

MODEL_VERSION = "1.0.0"
