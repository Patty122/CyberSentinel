"""Global error handlers: clients never receive stack traces or filesystem paths."""
import logging

from werkzeug.exceptions import HTTPException

from .responses import fail

log = logging.getLogger("cybersentinel.api")


class ApiError(Exception):
    def __init__(self, code, message, status=400, details=None):
        self.code, self.message, self.status, self.details = code, message, status, details


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def _api(e):
        return fail(e.code, e.message, e.status, e.details)

    @app.errorhandler(HTTPException)
    def _http(e):
        return fail(e.name.lower().replace(" ", "_"), e.description, e.code)

    @app.errorhandler(Exception)
    def _unhandled(e):
        log.exception("Unhandled error")  # stack trace stays in server logs only
        return fail("internal_error", "An internal error occurred.", 500)
