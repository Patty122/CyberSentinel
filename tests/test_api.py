import math

import pytest

from ml import config


def post(client, url, body):
    return client.post(url, json=body)


def test_health(client):
    r = client.get("/api/health").get_json()
    assert r["status"] == "ok" and r["data"]["models_loaded"] is True
    assert r["data"]["artifacts"]["metrics"] is True


def test_health_without_artifacts_does_not_crash(empty_client):
    r = empty_client.get("/api/health")
    assert r.status_code == 200 and r.get_json()["data"]["models_loaded"] is False
    for url in ["/api/summary", "/api/models", "/api/metrics", "/api/transactions"]:
        resp = empty_client.get(url)
        assert resp.status_code == 404 and resp.get_json()["status"] == "error"
    assert empty_client.post("/api/predict", json={"features": {}}).status_code in (422, 503)


def test_models_and_metrics(client):
    models = client.get("/api/models").get_json()["data"]
    assert models["selected_model"] and any(m["selected"] for m in models["models"])
    m = client.get("/api/metrics").get_json()["data"]
    assert "confusion_matrix" in m["models"]["random_forest"]["test"]


def test_predict_valid(client, valid_features):
    r = post(client, "/api/predict", {"features": valid_features})
    d = r.get_json()["data"]
    assert r.status_code == 200 and d["label"] in (0, 1) and "threshold" in d and "not proof" in d["disclaimer"]


def test_predict_isolation_forest_has_no_probability(client, valid_features):
    d = post(client, "/api/predict", {"features": valid_features, "model": "isolation_forest"}).get_json()["data"]
    assert d["probability"] is None and d["anomaly_score"] is not None


@pytest.mark.parametrize("mutate,field", [
    (lambda f: f.pop("V3"), "V3"),
    (lambda f: f.update(V1="abc"), "V1"),
    (lambda f: f.update(V2=None), "V2"),
    (lambda f: f.update(V4=float("nan")), "V4"),
    (lambda f: f.update(V5=float("inf")), "V5"),
    (lambda f: f.update(Amount=-5.0), "Amount"),
    (lambda f: f.update(Time=-1.0), "Time"),
    (lambda f: f.update(V6=1e9), "V6"),
    (lambda f: f.update(V7=True), "V7"),
    (lambda f: f.update(bogus=1.0), "bogus"),
])
def test_predict_rejects_bad_features(client, valid_features, mutate, field):
    mutate(valid_features)
    r = client.post("/api/predict", data=__import__("json").dumps({"features": valid_features}), content_type="application/json")
    body = r.get_json()
    assert r.status_code == 422 and field in body["error"]["details"]


def test_predict_rejects_bad_bodies(client):
    assert client.post("/api/predict", data="not json", content_type="application/json").status_code == 400
    assert client.post("/api/predict", json=[1, 2]).status_code == 400
    assert client.post("/api/predict", json={"features": {}, "x": 1}).status_code == 400
    assert client.post("/api/predict", json={"features": "abc"}).status_code == 422


def test_unknown_model(client, valid_features):
    assert post(client, "/api/predict", {"features": valid_features, "model": "nope"}).status_code == 400


def test_batch_mixed_validity(client, valid_features):
    bad = dict(valid_features); bad.pop("V1")
    r = post(client, "/api/predict/batch", {"transactions": [valid_features, bad]})
    d = r.get_json()["data"]
    assert r.status_code == 200 and d["valid_count"] == 1 and d["invalid_count"] == 1
    assert d["results"][0]["valid"] and not d["results"][1]["valid"]


def test_batch_limits(client, valid_features):
    assert post(client, "/api/predict/batch", {"transactions": [valid_features] * 6}).status_code == 413
    assert post(client, "/api/predict/batch", {"transactions": []}).status_code == 400


def test_request_size_limit(client):
    client.application.config["MAX_CONTENT_LENGTH"] = 1000
    r = client.post("/api/predict", data="x" * 5000, content_type="application/json")
    assert r.status_code == 413 and r.get_json()["status"] == "error"


def test_transactions_pagination_and_filters(client):
    d = client.get("/api/transactions?page_size=10&class=1").get_json()["data"]
    assert len(d["rows"]) <= 10 and all(r["Class"] == 1 for r in d["rows"])
    assert client.get("/api/transactions?page_size=101").status_code == 400  # bounded
    assert client.get("/api/transactions?page=abc").status_code == 400
    assert client.get("/api/transactions?min_amount=nan").status_code == 400


def test_sample_returns_real_row(client):
    d = client.get("/api/transactions/sample?class=1").get_json()["data"]
    assert d["label"] == 1 and set(d["features"]) == set(config.FEATURES)


def test_errors_do_not_leak_internals(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404 and "Traceback" not in r.get_data(as_text=True)
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_cors_allows_only_configured_origin(client):
    ok = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    bad = client.get("/api/health", headers={"Origin": "http://evil.example"})
    assert ok.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert "Access-Control-Allow-Origin" not in bad.headers
