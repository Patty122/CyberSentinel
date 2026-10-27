"""Start the API:  python run.py   (run from the backend/ directory)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make the `ml` package importable

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    # Local development server bound to localhost. For production use a WSGI server (e.g. waitress/gunicorn).
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=False)
