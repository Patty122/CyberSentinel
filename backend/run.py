import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))  # exposes the `ml` package

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    import os
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=5000, debug=False)
