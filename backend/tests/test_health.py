from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["models"]["crop_recommendation"] == "available"
    assert body["models"]["crop_disease"] == "available"


def test_profile_requires_authentication():
    response = client.get("/api/auth/me")
    assert response.status_code in (401, 403)


def test_crop_model_artifact_exists():
    from app.api.routes import resolve_model_path

    assert resolve_model_path("crop_recommendation.joblib").exists()
