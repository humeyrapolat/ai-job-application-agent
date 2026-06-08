import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_application_endpoint(client: TestClient) -> None:
    response = client.post(
        "/applications/analyze",
        json={
            "candidate_name": "Ada Lovelace",
            "job_title": "Junior AI Backend Developer",
            "company_name": "Example GmbH",
            "cv_text": "Python, FastAPI, PostgreSQL, Docker, REST APIs, Git, OpenAI API.",
            "job_description": "Looking for Python, FastAPI, PostgreSQL, Docker, Git, and LLM.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["candidate_name"] == "Ada Lovelace"
    assert body["match_score"] >= 70
    assert "python" in body["matched_skills"]
