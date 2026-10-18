from flask import jsonify


def ok(data, status=200, **extra):
    return jsonify({"status": "ok", "data": data, **extra}), status


def unavailable(message):
    return jsonify({"status": "unavailable", "data": None, "message": message}), 200


def error(code, message, http=400, fields=None):
    body = {"status": "error", "error": {"code": code, "message": message}}
    if fields:
        body["error"]["fields"] = fields
    return jsonify(body), http
