import logging

from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.routes.api import bp
from app.services.store import Store
from app.utils.responses import error


def create_app(overrides: dict | None = None) -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)
    CORS(app, resources={r"/api/*": {"origins": [app.config["FRONTEND_ORIGIN"]]}}, methods=["GET", "POST"])
    app.extensions["store"] = Store(app.config)
    app.register_blueprint(bp)

    @app.errorhandler(404)
    def _404(_):
        return error("not_found", "Resource not found.", 404)

    @app.errorhandler(405)
    def _405(_):
        return error("method_not_allowed", "Method not allowed.", 405)

    @app.errorhandler(413)
    def _413(_):
        return error("payload_too_large", "Request body too large.", 413)

    @app.errorhandler(Exception)
    def _500(exc):
        app.logger.error("Unhandled error: %s", type(exc).__name__)  # no data, no traceback to client
        return error("internal_error", "Internal server error.", 500)

    return app
