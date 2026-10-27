"""Flask application factory."""
import logging

from flask import Flask
from flask_cors import CORS

from .config import Config
from .routes import analysis, health, predict, transactions
from .services.artifacts import ArtifactStore
from .services.transactions import TransactionStore
from .utils.errors import register_error_handlers


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    logging.basicConfig(level=app.config["LOG_LEVEL"], format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    CORS(app, origins=app.config["CORS_ORIGINS"], methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])
    app.extensions["store"] = ArtifactStore(app.config["MODELS_DIR"], app.config["REPORTS_DIR"])
    app.extensions["transactions"] = TransactionStore(app.config["DATA_PATH"])
    for mod in (health, analysis, predict, transactions):
        app.register_blueprint(mod.bp, url_prefix="/api")
    register_error_handlers(app)

    @app.after_request
    def _headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Content-Security-Policy"] = "default-src 'none'"
        return resp

    return app
