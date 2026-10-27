"""Consistent JSON envelopes: {"status": "ok", "data": ...} or {"status": "error", "error": {...}}."""
from flask import jsonify


def ok(data=None, status=200, **extra):
    return jsonify({"status": "ok", "data": data, **extra}), status


def fail(code: str, message: str, status: int, details=None):
    err = {"code": code, "message": message}
    if details is not None:
        err["details"] = details
    return jsonify({"status": "error", "error": err}), status
