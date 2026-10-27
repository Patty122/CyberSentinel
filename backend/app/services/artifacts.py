"""Read-only access to saved analysis artifacts (JSON) and the trained models."""
import json
import logging
from pathlib import Path

from ml.predict import Predictor

log = logging.getLogger("cybersentinel.api")


class ArtifactStore:
    def __init__(self, models_dir: Path, reports_dir: Path):
        self.models_dir, self.reports_dir = Path(models_dir), Path(reports_dir)
        self._predictor = None
        self._cache = {}

    def _json(self, path: Path):
        if not path.exists():
            return None
        m = path.stat().st_mtime
        hit = self._cache.get(path)
        if hit and hit[0] == m:
            return hit[1]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            log.warning("Could not read artifact %s", path.name)
            return None
        self._cache[path] = (m, data)
        return data

    summary = property(lambda s: s._json(s.reports_dir / "summary.json"))
    metrics = property(lambda s: s._json(s.models_dir / "metrics.json"))
    metadata = property(lambda s: s._json(s.models_dir / "metadata.json"))

    def predictor(self):
        """Load models once; returns None if artifacts are missing/invalid (API stays up)."""
        if self._predictor is None:
            try:
                self._predictor = Predictor(self.models_dir)
            except Exception as exc:  # noqa: BLE001 - never crash the API over bad artifacts
                log.warning("Predictor unavailable: %s", type(exc).__name__)
                return None
        return self._predictor
