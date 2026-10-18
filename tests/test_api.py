import math

import pytest

from ml.data_loader import FEATURE_COLUMNS


@pytest.fixture
def client(api_env):
    from app import create_app
    cfg, _ = api_env
    return create_app({**cfg, "TESTING": True, "MAX_BATCH_SIZE": 5}).test_client()


@pytest.fixture
def row(api_env):
    return api_env[1].drop(columns="Class").iloc[0].to_dict()


@pytest.fixture
def empty_client(tmp_path):
    from app import create_app
    return create_app({"MODELS_DIR": tmp_path, "REPORTS_DIR": tmp_path, "DATA_PATH": tmp_path / "x.csv",
                       "TESTING": True}).test_client()


def test_health_ok(client):
    d = client.get("/api/health").get_json()["data"]
    assert d["models_available"] and d["dataset_available"]


def test_health_without_artifacts_does_not_crash(empty_client):
    r = empty_client.get("/api/health")
    assert r.status_code == 200 and r.get_json()["data"]["models_available"] is False
    for ep in ("summary", "models", "metrics", "transactions"):
        assert empty_client.get(f"/api/{ep}").get_json()["status"] == "unavailable"
    assert empty_client.post("/api/predict", json={}).status_code in (422, 400)


def test_metrics_and_models(client):
    m = client.get("/api/metrics").get_json()["data"]
    assert "confusion_matrix" in m["models"]["random_forest"]["test"]
    mods = client.get("/api/models").get_json()["data"]
    assert "curves" not in mods["models"]["random_forest"]["test"]


def test_predict_valid_all_models(client, row):
    for name in ("logistic_regression", "random_forest", "isolation_forest"):
        r = client.post("/api/predict", json={"features": row, "model": name})
        assert r.status_code == 200, r.get_json()
        d = r.get_json()["data"]
        assert d["model"] == name and d["prediction"] in (0, 1)
        if name == "isolation_forest":
            assert d["fraud_probability"] is None and "anomaly_score" in d


@pytest.mark.parametrize("mutate", [
    lambda r: r.pop("V3"),
    lambda r: r.update(V3="abc"),
    lambda r: r.update(V3=None),
    lambda r: r.update(Extra=1),
    lambda r: r.update(Amount=True),
])
def test_predict_invalid_features(client, row, mutate):
    mutate(row)
    r = client.post("/api/predict", json={"features": row})
    assert r.status_code == 422
    assert r.get_json()["error"]["fields"]


def test_predict_rejects_nan_inf(client, row):
    for bad in ("NaN", "Infinity"):
        body = '{"features": {' + ",".join(f'"{k}": {v}' for k, v in {**row, "V1": 0}.items()).replace(
            '"V1": 0', f'"V1": {bad}') + "}}"
        r = client.post("/api/predict", data=body, content_type="application/json")
        assert r.status_code in (400, 422)


def test_predict_bad_body_and_model(client, row):
    assert client.post("/api/predict", data="not json", content_type="application/json").status_code == 400
    assert client.post("/api/predict", json={"features": row, "model": "nope"}).status_code == 400


def test_batch_limits(client, row):
    assert client.post("/api/predict/batch", json={"transactions": [row] * 3}).status_code == 200
    assert client.post("/api/predict/batch", json={"transactions": [row] * 6}).status_code == 413
    assert client.post("/api/predict/batch", json={"transactions": []}).status_code == 422
    bad = {**row}; bad.pop("V1")
    r = client.post("/api/predict/batch", json={"transactions": [row, bad]})
    assert r.status_code == 422 and "1.V1" in r.get_json()["error"]["fields"]


def test_request_size_limit(api_env):
    from app import create_app
    c = create_app({**api_env[0], "MAX_CONTENT_LENGTH": 100, "TESTING": True}).test_client()
    assert c.post("/api/predict", data="x" * 500, content_type="application/json").status_code == 413


def test_transactions_pagination_and_filters(client):
    d = client.get("/api/transactions?page_size=10000&class=1").get_json()["data"]
    assert d["page_size"] == 100 and all(r["Class"] == 1 for r in d["rows"])
    assert client.get("/api/transactions?class=7").status_code == 400
    assert client.get("/api/transactions?page=abc").status_code == 400


def test_unknown_route_and_no_leak(client):
    r = client.get("/api/nothing")
    assert r.status_code == 404 and "Traceback" not in r.get_data(as_text=True)


def test_cors_restricted(client):
    r = client.get("/api/health", headers={"Origin": "http://evil.example"})
    assert "Access-Control-Allow-Origin" not in r.headers
    r = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
